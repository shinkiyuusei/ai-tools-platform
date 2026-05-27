from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jwt_identity,
    jwt_required, set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
)
from flask_jwt_extended.exceptions import JWTExtendedException

from ...core.errors import AppError, ErrorCode
from ...services.credit import init_user_credits
from ...utils.mysql import execute, query_one
from ...utils.response import success_response
from ...utils.security import check_password, hash_password
from ...utils.snowflake import generate_id

user_bp = Blueprint("user", __name__)


def _build_login_claims(user_id: int, remember: bool = False) -> dict:
    """Return access + refresh token strings."""
    token_kwargs = {}
    if remember:
        token_kwargs["expires_delta"] = None
    return {
        "access": create_access_token(identity=str(user_id), **token_kwargs),
        "refresh": create_refresh_token(identity=str(user_id)),
    }


def _set_tokens(response_tuple, user_id: int, remember: bool = False):
    """Set access + refresh cookies on a Flask response tuple.

    success_response() returns (Response, http_status). Extract the Response
    object from the tuple, set cookies, then return the same tuple.
    """
    resp, status = response_tuple
    claims = _build_login_claims(user_id, remember)
    set_access_cookies(resp, claims["access"])
    set_refresh_cookies(resp, claims["refresh"])
    return response_tuple


def _user_info_row(user: dict) -> dict:
    return {
        "id": user["id"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "vipLevel": user["vip_level"],
        "credits": user["credits"],
        "phone": user["phone"],
        "email": user["email"],
    }


# ---------------------------------------------------------------------------
#  Auth endpoints
# ---------------------------------------------------------------------------

@user_bp.post("/user/register")
def register():
    payload = request.get_json(silent=True) or {}
    phone = (payload.get("phone", "") or "").strip()
    password = payload.get("password", "")

    if not phone:
        raise AppError(ErrorCode.PARAM_INVALID, "手机号不能为空")
    if not password or len(password) < 6:
        raise AppError(ErrorCode.PARAM_INVALID, "密码长度不能少于6位")

    existing = query_one(
        "SELECT id FROM t_user WHERE phone = %s AND phone != '' AND is_delete = 0",
        (phone,),
    )
    if existing:
        raise AppError(ErrorCode.PARAM_INVALID, "该手机号已注册")

    user_id = generate_id()
    hashed = hash_password(password)
    nickname = f"用户{str(user_id)[-6:]}"
    execute(
        "INSERT INTO t_user (id, phone, password, nickname, credits) VALUES (%s,%s,%s,%s,%s)",
        (user_id, phone, hashed, nickname, 500),
    )
    init_user_credits(user_id, 500)

    user_info = {"id": user_id, "nickname": nickname, "avatar": "", "vipLevel": 0, "credits": 500}
    response = success_response({"userInfo": user_info})
    _set_tokens(response, user_id)
    return response


@user_bp.post("/user/login")
def login():
    payload = request.get_json(silent=True) or {}
    account = payload.get("account", "")
    password = payload.get("password", "")
    remember = payload.get("remember", False)

    if not account or not password:
        raise AppError(ErrorCode.PARAM_INVALID, "账号和密码不能为空")

    user = query_one(
        "SELECT * FROM t_user WHERE (phone = %s OR email = %s) AND is_delete = 0",
        (account, account),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "账号不存在")

    if user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号已被封禁")

    if not check_password(password, user["password"]):
        raise AppError(ErrorCode.UNAUTHORIZED, "密码错误")

    response = success_response({"userInfo": _user_info_row(user)})
    _set_tokens(response, user["id"], remember)
    return response


@user_bp.post("/user/refresh")
def refresh():
    """Silently refresh the access token using the refresh cookie."""
    payload = request.get_json(silent=True) or {}
    refresh_token_value = payload.get("refreshToken", "")

    # Support both cookie-based and body-based refresh (transitional)
    # If cookie is present, Flask-JWT-Extended handles it via @jwt_required(refresh=True)
    # For now, decode token manually to support old clients
    if not refresh_token_value:
        # Try reading from cookie
        from flask import request as flask_request
        refresh_token_value = flask_request.cookies.get("refresh_token", "")

    if not refresh_token_value:
        raise AppError(ErrorCode.UNAUTHORIZED, "refreshToken 不能为空")

    try:
        from flask_jwt_extended import decode_token
        decoded = decode_token(refresh_token_value, allow_expired=False)
        identity = decoded.get("sub") if isinstance(decoded, dict) else None
        user_id = int(identity) if identity else None
        if not user_id:
            raise AppError(ErrorCode.UNAUTHORIZED, "无效的 refreshToken")
    except JWTExtendedException:
        raise AppError(ErrorCode.UNAUTHORIZED, "refreshToken 无效或已过期")
    except (ValueError, TypeError, Exception):
        raise AppError(ErrorCode.UNAUTHORIZED, "refreshToken 无效或已过期")

    user = query_one(
        "SELECT id, vip_level, status FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "用户不存在")
    if user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号已被封禁")

    response = success_response({"message": "ok"})
    _set_tokens(response, user_id)
    return response


@user_bp.post("/user/logout")
def logout():
    """Clear auth cookies."""
    resp, status = success_response({"message": "已退出登录"})
    unset_jwt_cookies(resp)
    return resp, status


@user_bp.get("/user/session")
@jwt_required()
def check_session():
    """Return authenticated user info for session validation.

    Called by the frontend router guard to verify cookie-based auth.
    """
    user_id = int(get_jwt_identity())
    user = query_one(
        "SELECT id, phone, email, nickname, avatar, vip_level, credits, status "
        "FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    if not user or user["status"] != 1:
        raise AppError(ErrorCode.USER_NOT_FOUND, "会话已失效")

    return success_response({"userInfo": _user_info_row(user)})


# ---------------------------------------------------------------------------
#  User profile endpoints
# ---------------------------------------------------------------------------

@user_bp.post("/user/resetPassword")
def reset_password():
    payload = request.get_json(silent=True) or {}
    account = payload.get("account", "")
    new_password = payload.get("newPassword", "")

    if not account:
        raise AppError(ErrorCode.PARAM_INVALID, "账号不能为空")
    if not new_password or len(new_password) < 6:
        raise AppError(ErrorCode.PARAM_INVALID, "新密码长度不能少于6位")

    user = query_one(
        "SELECT id FROM t_user WHERE (phone = %s OR email = %s) AND is_delete = 0",
        (account, account),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "账号不存在")

    hashed = hash_password(new_password)
    execute("UPDATE t_user SET password = %s WHERE id = %s", (hashed, user["id"]))

    return success_response({"success": True, "message": "密码重置成功"})


@user_bp.get("/user/info")
@jwt_required()
def get_user_info():
    user_id = int(get_jwt_identity())
    user = query_one(
        "SELECT id, phone, email, nickname, avatar, vip_level, vip_expire_time, credits, status "
        "FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "用户不存在")
    if user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号已被封禁")

    return success_response({
        "id": user["id"],
        "nickname": user["nickname"],
        "avatar": user["avatar"],
        "vipLevel": user["vip_level"],
        "vipExpireTime": user["vip_expire_time"].isoformat() if user["vip_expire_time"] else None,
        "phone": user["phone"],
        "email": user["email"],
        "credits": user["credits"],
    })


@user_bp.post("/user/info/update")
@jwt_required()
def update_user_info():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    nickname = payload.get("nickname")
    avatar = payload.get("avatar")

    fields = []
    values = []
    if nickname:
        fields.append("nickname = %s")
        values.append(nickname)
    if avatar:
        fields.append("avatar = %s")
        values.append(avatar)
    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    values.append(user_id)
    execute(f"UPDATE t_user SET {', '.join(fields)} WHERE id = %s", tuple(values))
    return success_response({"success": True, "message": "个人信息更新成功"})
