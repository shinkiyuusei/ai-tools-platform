"""
支付宝支付服务
封装 alipay-sdk-python，提供页面支付和验签能力
"""
import logging

from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from alipay.aop.api.request.AlipayTradeWapPayRequest import AlipayTradeWapPayRequest
from flask import current_app

logger = logging.getLogger(__name__)

_client_cache = None


def _get_alipay_client() -> DefaultAlipayClient:
    """根据当前 Flask 配置构建 DefaultAlipayClient（单例缓存）"""
    global _client_cache
    if _client_cache is not None:
        return _client_cache

    cfg = current_app.config["ALIPAY_CONFIG"]

    config = AlipayClientConfig()
    config.server_url = cfg["gateway"]
    config.app_id = cfg["app_id"]
    config.app_private_key = cfg["app_private_key"]
    config.alipay_public_key = cfg["alipay_public_key"]
    config.sign_type = cfg["sign_type"]
    config.charset = "utf-8"
    config.format = "json"

    _client_cache = DefaultAlipayClient(config)
    return _client_cache


def _build_page_request(order_no: str, amount: float, subject: str,
                        return_url: str, notify_url: str) -> AlipayTradePagePayRequest:
    """构建电脑网站支付请求对象"""
    req = AlipayTradePagePayRequest()
    req.biz_content = {
        "out_trade_no": order_no,
        "total_amount": str(amount),
        "subject": subject,
        "product_code": "FAST_INSTANT_TRADE_PAY",
    }
    req.notify_url = notify_url
    req.return_url = return_url
    return req


def _build_wap_request(order_no: str, amount: float, subject: str,
                       return_url: str, notify_url: str) -> AlipayTradeWapPayRequest:
    """构建手机网站支付请求对象"""
    req = AlipayTradeWapPayRequest()
    req.biz_content = {
        "out_trade_no": order_no,
        "total_amount": str(amount),
        "subject": subject,
        "product_code": "QUICK_WAP_WAY",
    }
    req.notify_url = notify_url
    req.return_url = return_url
    return req


def create_page_pay(order_no: str, amount: float, subject: str,
                    return_url: str | None = None) -> str:
    """
    生成电脑网站支付 URL（alipay.trade.page.pay）
    返回可直接跳转的完整支付 URL
    """
    client = _get_alipay_client()
    cfg = current_app.config["ALIPAY_CONFIG"]
    notify_url = cfg["notify_url"]
    if return_url is None:
        return_url = cfg.get("return_url", "")

    req = _build_page_request(order_no, amount, subject, return_url, notify_url)
    resp = client.page_execute(req, http_method="GET")
    return resp


def create_wap_pay(order_no: str, amount: float, subject: str,
                   return_url: str | None = None) -> str:
    """
    生成手机网站支付 URL（alipay.trade.wap.pay）
    返回可直接跳转的完整支付 URL
    """
    client = _get_alipay_client()
    cfg = current_app.config["ALIPAY_CONFIG"]
    notify_url = cfg["notify_url"]
    if return_url is None:
        return_url = cfg.get("return_url", "")

    req = _build_wap_request(order_no, amount, subject, return_url, notify_url)
    resp = client.page_execute(req, http_method="GET")
    return resp


def verify_notify(data: dict) -> bool:
    """
    验证支付宝异步通知签名

    参数:
        data: 支付宝 POST 过来的表单字典（request.form），不含 sign 和 sign_type

    返回:
        True 表示验签通过
    """
    try:
        client = _get_alipay_client()
        # 深拷贝避免修改原数据
        verify_data = {k: v for k, v in data.items() if k not in ("sign", "sign_type")}
        signature = data.get("sign", "")
        sign_type = data.get("sign_type", "RSA2")
        return client.verify(verify_data, signature, sign_type)
    except Exception:
        logger.exception("Alipay signature verification error")
        return False
