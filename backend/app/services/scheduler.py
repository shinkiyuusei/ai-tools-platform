"""
Lightweight APScheduler integration.

Runs recommendation refresh every 10 minutes.
The scheduler is a daemon thread — it will not block the main process from exiting.
"""
import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None
INTERVAL_MINUTES = 10


def _refresh_job():
    try:
        from .recommendation import refresh_recommendations

        refresh_recommendations()
        logger.debug("Recommendation scores refreshed successfully.")
    except Exception:
        logger.exception("Recommendation refresh failed")


def start_scheduler(app=None):
    """Start the background scheduler. Call once from run.py."""
    global _scheduler

    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(_refresh_job, "interval", minutes=INTERVAL_MINUTES, id="recommend_refresh")
    _scheduler.start()
    atexit.register(lambda: _scheduler.shutdown(wait=False))
    logger.info("APScheduler started — recommend refresh every %d min", INTERVAL_MINUTES)

    # Run once immediately so Redis is warm on first request
    try:
        _refresh_job()
    except Exception:
        logger.exception("Initial recommendation refresh failed (app may still be starting)")
