"""
Credit service: MySQL-backed atomic credit operations.

MySQL is the single source of truth for balances. Deductions use a conditional
UPDATE so concurrent requests cannot overspend, and every mutation writes a
t_credit_log row in the same transaction.
"""

import logging
import math

from ..core.errors import AppError, ErrorCode
from ..utils.mysql import execute, query_one, transaction
from ..utils.snowflake import generate_id

logger = logging.getLogger(__name__)


def get_balance(user_id: int) -> int:
    """Get current credit balance from MySQL."""
    row = query_one(
        "SELECT credits FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    return row["credits"] if row else 0


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
    deduct(user_id, deduction, tokens_used=tokens, **kwargs)
    return deduction


def deduct(user_id: int, amount: int, *, conversation_id: int = 0,
           message_id: int = 0, tokens_used: int = 0) -> int:
    """Atomically deduct credits from a user. Returns the new balance.

    Raises AppError when the user has insufficient balance.
    """
    if amount <= 0:
        return get_balance(user_id)

    with transaction() as cur:
        cur.execute(
            "UPDATE t_user SET credits = credits - %s "
            "WHERE id = %s AND is_delete = 0 AND credits >= %s",
            (amount, user_id, amount),
        )
        if cur.rowcount == 0:
            logger.warning("Insufficient credits for user %s (requested %s)", user_id, amount)
            raise AppError(ErrorCode.FORBIDDEN, "积分不足，无法完成操作")

        cur.execute("SELECT credits FROM t_user WHERE id = %s", (user_id,))
        row = cur.fetchone()
        new_balance = row["credits"] if row else 0
        _insert_log(
            user_id=user_id,
            amount=-amount,
            balance_after=new_balance,
            conversation_id=conversation_id,
            message_id=message_id,
            tokens_used=tokens_used,
            source_type="chat",
            cursor=cur,
        )
    return new_balance


def grant(user_id: int, amount: int, *, source_type: str = "admin_grant") -> int:
    """Grant credits to a user (admin / recharge). Returns the new balance."""
    if amount == 0:
        return get_balance(user_id)

    with transaction() as cur:
        cur.execute(
            "UPDATE t_user SET credits = credits + %s WHERE id = %s AND is_delete = 0",
            (amount, user_id),
        )
        if cur.rowcount == 0:
            raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "用户不存在")

        cur.execute("SELECT credits FROM t_user WHERE id = %s", (user_id,))
        row = cur.fetchone()
        new_balance = row["credits"] if row else 0
        _insert_log(
            user_id=user_id,
            amount=amount,
            balance_after=new_balance,
            source_type=source_type,
            cursor=cur,
        )
    return new_balance


def init_user_credits(user_id: int, initial: int = 500):
    """Record the initial credit grant for a newly registered user."""
    _insert_log(
        user_id=user_id,
        amount=initial,
        balance_after=initial,
        source_type="register",
    )


# ---------------------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------------------

def _insert_log(user_id: int, amount: int, balance_after: int, *,
                conversation_id: int = 0, message_id: int = 0,
                tokens_used: int = 0, source_type: str = "chat",
                cursor=None):
    """Insert a credit transaction log record (best-effort)."""
    try:
        log_id = generate_id()
        sql = (
            "INSERT INTO t_credit_log (id, user_id, amount, balance_after, "
            "source_type, conversation_id, message_id, tokens_used) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        )
        params = (log_id, user_id, amount, balance_after, source_type,
                  conversation_id, message_id, tokens_used)
        if cursor is not None:
            cursor.execute(sql, params)
        else:
            execute(sql, params)
    except Exception:
        logger.exception("Failed to insert credit log for user %s", user_id)
