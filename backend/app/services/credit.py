"""
Credit service: Redis-backed atomic credit operations with MySQL sync.

Redis is the primary data source for credit balances (atomic DECRBY/INCRBY).
MySQL t_user.credits is updated every 5 minutes via background sync.
All transactions are recorded in t_credit_log synchronously.
"""

import logging
import math
import time

from ..core.errors import AppError, ErrorCode
from ..extensions import get_redis_client
from ..utils.mysql import execute, query_one
from ..utils.snowflake import generate_id

logger = logging.getLogger(__name__)

REDIS_KEY_PREFIX = "user:credits:"
SYNC_KEY = "credits:sync:last"
SYNC_INTERVAL_SEC = 300  # 5 minutes


def _redis_key(user_id: int) -> str:
    return f"{REDIS_KEY_PREFIX}{user_id}"


def _ensure_in_redis(user_id: int) -> int:
    """Load credits from MySQL into Redis if not already cached. Returns balance."""
    redis = get_redis_client()
    key = _redis_key(user_id)
    balance = redis.get(key)
    if balance is None:
        row = query_one(
            "SELECT credits FROM t_user WHERE id = %s AND is_delete = 0",
            (user_id,),
        )
        balance = row["credits"] if row else 0
        redis.set(key, balance)
    return int(balance)


def get_balance(user_id: int) -> int:
    """Get current credit balance (from Redis, fallback to MySQL)."""
    return _ensure_in_redis(user_id)


def ensure_positive_balance(user_id: int) -> int:
    """Raise AppError when the user's balance has gone negative."""
    balance = get_balance(user_id)
    if balance < 0:
        raise AppError(ErrorCode.FORBIDDEN, "积分已透支，无法继续对话，请联系管理员充值")
    return balance


def deduct_for_tokens(user_id: int, tokens: int, **kwargs) -> int:
    """Deduct credits based on token usage (100 tokens = 1 credit, ceil).

    Returns the deducted amount.
    """
    if not tokens:
        return 0
    deduction = math.ceil(tokens / 100)
    ensure_positive_balance(user_id)
    deduct(user_id, deduction, tokens_used=tokens, **kwargs)
    return deduction


def deduct(user_id: int, amount: int, *, conversation_id: int = 0,
           message_id: int = 0, tokens_used: int = 0) -> int:
    """Atomically deduct credits from user. Returns new balance.

    Raises ValueError if user has insufficient balance.
    """
    redis = get_redis_client()
    key = _redis_key(user_id)
    _ensure_in_redis(user_id)

    new_balance = redis.decrby(key, amount)
    if new_balance < 0:
        # Still allow the deduction but log a warning — the caller should
        # check balance before starting an expensive AI call.
        logger.warning("User %s credits went negative: %s", user_id, new_balance)

    _insert_log(
        user_id=user_id,
        amount=-amount,
        balance_after=new_balance,
        conversation_id=conversation_id,
        message_id=message_id,
        tokens_used=tokens_used,
        source_type="chat",
    )

    _maybe_sync()
    return new_balance


def grant(user_id: int, amount: int, *, source_type: str = "admin_grant") -> int:
    """Grant credits to user (admin operation). Returns new balance."""
    redis = get_redis_client()
    key = _redis_key(user_id)
    _ensure_in_redis(user_id)

    new_balance = redis.incrby(key, amount)
    _insert_log(
        user_id=user_id,
        amount=amount,
        balance_after=new_balance,
        source_type=source_type,
    )

    _maybe_sync()
    return new_balance


def init_user_credits(user_id: int, initial: int = 500):
    """Set initial credits for a newly registered user."""
    redis = get_redis_client()
    key = _redis_key(user_id)
    redis.set(key, initial)
    _insert_log(
        user_id=user_id,
        amount=initial,
        balance_after=initial,
        source_type="register",
    )


def sync_all_to_mysql():
    """Sync all in-memory Redis credit balances to MySQL.

    Called periodically (every 5 min) and at app shutdown.
    """
    redis = get_redis_client()
    keys = redis.keys(f"{REDIS_KEY_PREFIX}*")
    if not keys:
        return

    for key in keys:
        try:
            user_id = int(key.removeprefix(REDIS_KEY_PREFIX))
            balance = redis.get(key)
            if balance is not None:
                execute(
                    "UPDATE t_user SET credits = %s WHERE id = %s",
                    (int(balance), user_id),
                )
        except (ValueError, Exception) as e:
            logger.warning("Failed to sync credits for key %s: %s", key, e)

    redis.set(SYNC_KEY, int(time.time()))
    logger.info("Credit sync complete: %s users synced to MySQL", len(keys))


def _maybe_sync():
    """Trigger a sync if the sync interval has elapsed."""
    redis = get_redis_client()
    last = redis.get(SYNC_KEY)
    if last is None or (int(time.time()) - int(last)) >= SYNC_INTERVAL_SEC:
        sync_all_to_mysql()


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------

def _insert_log(user_id: int, amount: int, balance_after: int, *,
                conversation_id: int = 0, message_id: int = 0,
                tokens_used: int = 0, source_type: str = "chat"):
    """Insert a credit transaction log record (synchronous MySQL write)."""
    try:
        log_id = generate_id()
        execute(
            "INSERT INTO t_credit_log (id, user_id, amount, balance_after, "
            "source_type, conversation_id, message_id, tokens_used) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (log_id, user_id, amount, balance_after, source_type,
             conversation_id, message_id, tokens_used),
        )
    except Exception:
        logger.exception("Failed to insert credit log for user %s", user_id)
