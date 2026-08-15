"""One-time verification codes backed by MySQL (password reset flow)."""

import hmac
import logging
import secrets

from ..core.errors import AppError, ErrorCode
from ..utils.mysql import execute, query_one

logger = logging.getLogger(__name__)

CODE_TTL_SEC = 600
MAX_ATTEMPTS = 5
SEND_COOLDOWN_SEC = 60
SEND_ACCOUNT_LIMIT = 5
SEND_IP_LIMIT = 10
RATE_WINDOW_SEC = 3600


def _normalize_account(account: str) -> str:
    return (account or "").strip().lower()


def send_reset_code(account: str, ip: str = "") -> None:
    """Issue a reset code. Delivery is logged until an email/SMS adapter is wired."""
    account = _normalize_account(account)
    if not account:
        raise AppError(ErrorCode.PARAM_INVALID, "账号不能为空")
    ip = (ip or "unknown").strip()

    row = query_one(
        "SELECT id FROM t_verification_code WHERE account = %s "
        "AND created_at >= NOW() - INTERVAL %s SECOND LIMIT 1",
        (account, SEND_COOLDOWN_SEC),
    )
    if row:
        raise AppError(ErrorCode.FORBIDDEN, "发送过于频繁，请稍后再试")

    account_count = query_one(
        "SELECT COUNT(*) AS cnt FROM t_verification_code WHERE account = %s "
        "AND created_at >= NOW() - INTERVAL %s SECOND",
        (account, RATE_WINDOW_SEC),
    )["cnt"]
    if account_count >= SEND_ACCOUNT_LIMIT:
        raise AppError(ErrorCode.FORBIDDEN, "该账号发送过于频繁，请稍后再试")

    ip_count = query_one(
        "SELECT COUNT(*) AS cnt FROM t_verification_code WHERE ip_address = %s "
        "AND created_at >= NOW() - INTERVAL %s SECOND",
        (ip, RATE_WINDOW_SEC),
    )["cnt"]
    if ip_count >= SEND_IP_LIMIT:
        raise AppError(ErrorCode.FORBIDDEN, "发送过于频繁，请稍后再试")

    code = f"{secrets.randbelow(1_000_000):06d}"
    execute(
        "UPDATE t_verification_code SET expires_at = NOW() "
        "WHERE account = %s AND expires_at > NOW()",
        (account,),
    )
    execute(
        "INSERT INTO t_verification_code (account, code, ip_address, expires_at) "
        "VALUES (%s, %s, %s, NOW() + INTERVAL %s SECOND)",
        (account, code, ip, CODE_TTL_SEC),
    )
    logger.info("Password reset code issued for %s (delivery pending): %s", account, code)


def verify_reset_code(account: str, code: str) -> None:
    """Validate a reset code; invalidates it after success or too many failures."""
    account = _normalize_account(account)
    code = (code or "").strip()
    if not account or not code:
        raise AppError(ErrorCode.PARAM_INVALID, "账号或验证码不能为空")

    row = query_one(
        "SELECT id, code, attempts FROM t_verification_code "
        "WHERE account = %s AND expires_at > NOW() ORDER BY id DESC LIMIT 1",
        (account,),
    )
    if not row:
        raise AppError(ErrorCode.UNAUTHORIZED, "验证码无效或已过期")

    attempts = row["attempts"] + 1
    if attempts > MAX_ATTEMPTS:
        execute("DELETE FROM t_verification_code WHERE id = %s", (row["id"],))
        raise AppError(ErrorCode.UNAUTHORIZED, "验证码错误次数过多，请重新获取")

    execute(
        "UPDATE t_verification_code SET attempts = %s WHERE id = %s",
        (attempts, row["id"]),
    )
    if not hmac.compare_digest(row["code"].encode("utf-8"), code.encode("utf-8")):
        raise AppError(ErrorCode.UNAUTHORIZED, "验证码错误")

    execute("DELETE FROM t_verification_code WHERE account = %s", (account,))
