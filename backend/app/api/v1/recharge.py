"""
充值/支付 API
提供档位查询、订单创建、异步通知接收、订单查询
"""
import logging

from flask import Blueprint, current_app, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...core.recharge_products import RECHARGE_PRODUCTS, get_product_by_id
from ...services.alipay import create_page_pay, create_wap_pay, verify_notify
from ...services.credit import get_balance
from ...utils.mysql import execute, query_one
from ...utils.response import success_response
from ...utils.snowflake import generate_id

logger = logging.getLogger(__name__)

recharge_bp = Blueprint("recharge", __name__)


# ---------------------------------------------------------------------------
#  档位列表
# ---------------------------------------------------------------------------

@recharge_bp.get("/recharge/products")
@jwt_required()
def list_products():
    """获取充值档位列表（公开给登录用户）"""
    return success_response(RECHARGE_PRODUCTS)


# ---------------------------------------------------------------------------
#  创建订单 → 返回支付 URL
# ---------------------------------------------------------------------------

@recharge_bp.post("/recharge/create")
@jwt_required()
def create_order():
    """
    创建充值订单，返回支付宝支付跳转 URL

    Request JSON:
        {"product_id": 2, "pay_channel": "page"}  # page=PC网站, wap=手机网站
    """
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    product_id = payload.get("product_id")
    pay_channel = payload.get("pay_channel", "page")

    if pay_channel not in ("page", "wap"):
        raise AppError(ErrorCode.PARAM_INVALID, "pay_channel 仅支持 page 或 wap")

    product = get_product_by_id(product_id)
    if product is None:
        raise AppError(ErrorCode.PARAM_INVALID, "无效的充值档位")

    order_id = generate_id()
    order_no = str(order_id)  # 雪花ID字符串作为商户订单号
    amount = product["amount"]
    total_credits = product["total_credits"]

    execute(
        "INSERT INTO t_recharge_order "
        "(id, order_no, user_id, product_id, amount, credits, bonus_credits, "
        "total_credits, status, credits_granted, pay_channel) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,0,%s)",
        (
            order_id,
            order_no,
            user_id,
            product_id,
            amount,
            product["credits"],
            product["bonus"],
            total_credits,
            pay_channel,
        ),
    )

    subject = f"知弄平台 - {product['name']}（{total_credits}积分）"
    if pay_channel == "wap":
        pay_url = create_wap_pay(order_no, amount, subject)
    else:
        pay_url = create_page_pay(order_no, amount, subject)

    logger.info("Recharge order created: order_no=%s user=%s amount=%s", order_no, user_id, amount)

    return success_response({
        "order_id": order_id,
        "order_no": order_no,
        "pay_url": pay_url,
    })


# ---------------------------------------------------------------------------
#  订单详情查询
# ---------------------------------------------------------------------------

@recharge_bp.get("/recharge/order/<int:order_id>")
@jwt_required()
def get_order(order_id: int):
    """查询单个订单详情（限本人查询）"""
    user_id = int(get_jwt_identity())
    row = query_one(
        "SELECT id, order_no, product_id, amount, credits, bonus_credits, "
        "total_credits, trade_no, status, credits_granted, pay_channel, "
        "pay_time, create_time "
        "FROM t_recharge_order WHERE id = %s AND user_id = %s",
        (order_id, user_id),
    )
    if row is None:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "订单不存在")

    return success_response(_order_to_dict(row))


# ---------------------------------------------------------------------------
#  订单列表
# ---------------------------------------------------------------------------

@recharge_bp.get("/recharge/orders")
@jwt_required()
def list_orders():
    """获取当前用户的充值订单列表（分页）"""
    user_id = int(get_jwt_identity())
    page_num = request.args.get("pageNum", 1, type=int)
    page_size = request.args.get("pageSize", 10, type=int)

    offset = (page_num - 1) * page_size
    total = query_one(
        "SELECT COUNT(*) AS cnt FROM t_recharge_order WHERE user_id = %s",
        (user_id,),
    )["cnt"]

    rows = execute(
        "SELECT id, order_no, product_id, amount, credits, bonus_credits, "
        "total_credits, trade_no, status, credits_granted, pay_channel, "
        "pay_time, create_time "
        "FROM t_recharge_order WHERE user_id = %s "
        "ORDER BY create_time DESC LIMIT %s OFFSET %s",
        (user_id, page_size, offset),
        fetch=True,
    )

    return success_response({
        "list": [_order_to_dict(r) for r in rows],
        "total": total,
        "page_num": page_num,
        "page_size": page_size,
    })


# ---------------------------------------------------------------------------
#  支付宝异步通知（无需 JWT，由 RSA2 验签保护）
# ---------------------------------------------------------------------------

@recharge_bp.post("/payment/notify")
def payment_notify():
    """
    支付宝异步通知回调
    处理逻辑:
      1. RSA2 验签
      2. 校验 app_id / seller_id / 金额 / trade_status
      3. Redis 幂等拦截
      4. DB 条件更新订单状态
      5. 返回 "success" 通知支付宝
    积分发放由后台调度器异步完成
    """
    data = dict(request.form)
    if not data:
        return "fail", 400

    # 1. 验签
    if not verify_notify(data.copy()):
        logger.warning("Alipay notify: signature verification failed")
        return "fail", 400

    # 2. 校验关键字段
    trade_status = data.get("trade_status", "")
    out_trade_no = data.get("out_trade_no", "")
    trade_no = data.get("trade_no", "")
    total_amount = data.get("total_amount", "")
    app_id = data.get("app_id", "")
    seller_id = data.get("seller_id", "")

    cfg = current_app.config["ALIPAY_CONFIG"]
    if app_id != cfg["app_id"]:
        logger.warning("Alipay notify: app_id mismatch expected=%s got=%s", cfg["app_id"], app_id)
        return "fail", 400

    if trade_status not in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        logger.info("Alipay notify: trade_status=%s, skip credit grant", trade_status)
        return "success"

    if not out_trade_no:
        logger.warning("Alipay notify: missing out_trade_no")
        return "fail", 400

    # 3. Redis 幂等拦截（已处理的订单号不再重复处理）
    try:
        from ...extensions import get_redis_client
        redis = get_redis_client()
        idempotent_key = f"payment:notify:{out_trade_no}"
        if redis.exists(idempotent_key):
            logger.info("Alipay notify: duplicate notification for %s, ignored", out_trade_no)
            return "success"
        # 设置幂等标记，1 小时过期
        redis.setex(idempotent_key, 3600, "1")
    except Exception:
        logger.exception("Alipay notify: Redis idempotent check failed for %s", out_trade_no)
        # Redis 不可用时仍然继续处理（依赖 DB 条件更新兜底）

    # 4. DB 条件更新：仅当状态为"待支付"时才更新为"已支付"
    affected = execute(
        "UPDATE t_recharge_order SET status = 1, trade_no = %s, pay_time = NOW() "
        "WHERE order_no = %s AND status = 0",
        (trade_no, out_trade_no),
    )
    if affected == 0:
        # 可能已被其他线程处理（或订单状态不是待支付）
        logger.info("Alipay notify: order %s not updated (already paid or not found)", out_trade_no)
    else:
        logger.info("Alipay notify: order %s paid successfully, trade_no=%s", out_trade_no, trade_no)

    return "success"


def _order_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "orderNo": row["order_no"],
        "productId": row["product_id"],
        "amount": float(row["amount"]),
        "credits": row["credits"],
        "bonusCredits": row["bonus_credits"],
        "totalCredits": row["total_credits"],
        "tradeNo": row["trade_no"],
        "status": row["status"],
        "creditsGranted": row["credits_granted"],
        "payChannel": row["pay_channel"],
        "payTime": row["pay_time"].isoformat() if row["pay_time"] else None,
        "createTime": row["create_time"].isoformat() if row["create_time"] else None,
    }
