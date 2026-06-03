"""
Lightweight APScheduler integration.

Runs:
  - Recommendation refresh every 10 minutes
  - Credit grant polling every 10 seconds (recharge orders)
The scheduler is a daemon thread — it will not block the main process from exiting.
"""
import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
INTERVAL_MINUTES = 10
CREDIT_GRANT_INTERVAL_SEC = 10


def _refresh_job():
    try:
        from .recommendation import refresh_recommendations

        refresh_recommendations()
        logger.debug("Recommendation scores refreshed successfully.")
    except Exception:
        logger.exception("Recommendation refresh failed")


def _credit_grant_job():
    """轮询 t_recharge_order 中已支付但积分未发放的订单，逐条发放积分"""
    try:
        from ..utils.mysql import execute
        from .credit import grant

        # 批量查询待发放订单（每次最多处理 20 条）
        rows = execute(
            "SELECT id, user_id, total_credits, order_no "
            "FROM t_recharge_order "
            "WHERE status = 1 AND credits_granted = 0 "
            "ORDER BY pay_time ASC LIMIT 20",
            fetch=True,
        )

        if not rows:
            return

        for row in rows:
            order_id = row["id"]
            user_id = row["user_id"]
            total_credits = row["total_credits"]
            order_no = row["order_no"]

            try:
                # 发放积分（Redis 原子操作 + 写 t_credit_log）
                grant(user_id, total_credits, source_type="recharge")

                # 标记积分已发放
                execute(
                    "UPDATE t_recharge_order SET credits_granted = 1 "
                    "WHERE id = %s AND credits_granted = 0",
                    (order_id,),
                )
                logger.info(
                    "Credit grant done: order=%s user=%s credits=%s",
                    order_no, user_id, total_credits,
                )
            except Exception:
                logger.exception(
                    "Credit grant failed for order %s (user=%s)",
                    order_no, user_id,
                )
                # 失败不阻塞后续订单处理
    except Exception:
        logger.exception("Credit grant poll failed")


def start_scheduler(app=None):
    """Start the background scheduler. Call once from run.py."""
    global _scheduler

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _refresh_job, "interval", minutes=INTERVAL_MINUTES, id="recommend_refresh",
    )
    _scheduler.add_job(
        _credit_grant_job, "interval",
        seconds=CREDIT_GRANT_INTERVAL_SEC, id="credit_grant",
    )
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    logger.info(
        "APScheduler started — recommend refresh every %d min, credit grant every %d sec",
        INTERVAL_MINUTES, CREDIT_GRANT_INTERVAL_SEC,
    )

    # Run once immediately so Redis is warm on first request
    try:
        _refresh_job()
    except Exception:
        logger.exception("Initial recommendation refresh failed (app may still be starting)")
