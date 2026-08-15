"""
Extensions REST API — marketplace, install, user config.
"""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from urllib.parse import urljoin

from ...core.errors import AppError, ErrorCode
from ...services.extensions import (
    list_installed, get_extension, install_extension,
    uninstall_extension, update_status,
    get_user_config, set_user_config,
)
from ...utils.ssrf import MAX_REDIRECTS, MAX_TIMEOUT_SEC, validate_outbound_url
from ...utils.mysql import query_one
from ...utils.response import success_response

extensions_bp = Blueprint("extensions", __name__)


def _require_admin(user_id: int) -> None:
    user = query_one("SELECT vip_level FROM t_user WHERE id = %s", (user_id,))
    if not user or (user.get("vip_level", 0) or 0) < 2:
        raise AppError(ErrorCode.FORBIDDEN, "需要管理员权限")


# ---------------------------------------------------------------------------
#  Public endpoints
# ---------------------------------------------------------------------------

@extensions_bp.get("/extensions")
def api_list_extensions():
    """List active installed extensions (public)."""
    extensions = list_installed("active")
    return success_response(extensions)


@extensions_bp.get("/extensions/<ext_id>")
def api_get_extension(ext_id: str):
    """Get a single extension by id."""
    ext = get_extension(ext_id)
    if not ext:
        raise AppError(ErrorCode.NOT_FOUND, "扩展不存在")
    return success_response(ext)


# ---------------------------------------------------------------------------
#  Admin endpoints
# ---------------------------------------------------------------------------

@extensions_bp.post("/extensions/install")
@jwt_required()
def api_install_extension():
    """Admin: install an extension from a manifest payload."""
    user_id = int(get_jwt_identity())
    _require_admin(user_id)

    payload = request.get_json(silent=True) or {}
    ext_id = (payload.get("id") or "").strip()
    if not ext_id:
        raise AppError(ErrorCode.PARAM_INVALID, "id 不能为空")

    manifest = payload.get("manifest")
    if not isinstance(manifest, dict):
        raise AppError(ErrorCode.PARAM_INVALID, "manifest 必须是对象")

    # Validate required manifest fields
    for field in ("name", "version"):
        if not manifest.get(field):
            raise AppError(ErrorCode.PARAM_INVALID, f"manifest 缺少 {field}")

    install_extension(ext_id, manifest, "active")
    return success_response(None, "安装成功")


@extensions_bp.delete("/extensions/<ext_id>")
@jwt_required()
def api_uninstall_extension(ext_id: str):
    """Admin: uninstall an extension."""
    user_id = int(get_jwt_identity())
    _require_admin(user_id)
    uninstall_extension(ext_id)
    return success_response(None, "卸载成功")


@extensions_bp.put("/extensions/<ext_id>/status")
@jwt_required()
def api_update_extension_status(ext_id: str):
    """Admin: toggle extension status."""
    user_id = int(get_jwt_identity())
    _require_admin(user_id)

    payload = request.get_json(silent=True) or {}
    status = payload.get("status", "active")
    if status not in ("active", "inactive", "pending_review"):
        raise AppError(ErrorCode.PARAM_INVALID, "status 无效")
    update_status(ext_id, status)
    return success_response(None, "状态更新成功")


# ---------------------------------------------------------------------------
#  User config endpoints
# ---------------------------------------------------------------------------

@extensions_bp.get("/extensions/<ext_id>/config")
@jwt_required()
def api_get_user_config(ext_id: str):
    """Get the current user's config for an extension."""
    user_id = int(get_jwt_identity())
    config = get_user_config(ext_id, user_id)
    return success_response(config)


@extensions_bp.put("/extensions/<ext_id>/config")
@jwt_required()
def api_set_user_config(ext_id: str):
    """Update the current user's config for an extension."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    set_user_config(ext_id, user_id, payload)
    return success_response(None, "配置已保存")


# ---------------------------------------------------------------------------
#  HTTP proxy for extension sandbox
# ---------------------------------------------------------------------------

_BLOCKED_PROXY_HEADERS = {
    "host", "cookie", "content-length", "connection", "keep-alive",
    "proxy-authorization", "proxy-connection", "te", "trailer",
    "transfer-encoding", "upgrade", "x-forwarded-for", "x-forwarded-host",
    "x-forwarded-proto", "x-real-ip", "x-http-method-override",
}


def _sanitize_proxy_headers(headers: dict) -> dict:
    return {
        key: value for key, value in (headers or {}).items()
        if key.lower() not in _BLOCKED_PROXY_HEADERS
    }


@extensions_bp.post("/extensions/proxy/http")
@jwt_required()
def api_proxy_http():
    """Extension sandbox HTTP proxy — relays fetches through the backend."""
    import requests as req_lib

    payload = request.get_json(silent=True) or {}
    url = (payload.get("url") or "").strip()
    method = (payload.get("method") or "GET").upper()

    if not url:
        raise AppError(ErrorCode.PARAM_INVALID, "url 不能为空")
    if method not in ("GET", "POST"):
        raise AppError(ErrorCode.PARAM_INVALID, "method 仅支持 GET/POST")

    headers = _sanitize_proxy_headers(payload.get("headers") or {})
    body = payload.get("body")
    current_url = url
    current_method = method
    current_body = body

    try:
        for _ in range(MAX_REDIRECTS + 1):
            validate_outbound_url(current_url)
            resp = req_lib.request(
                current_method,
                current_url,
                headers=headers,
                json=current_body if current_method == "POST" else None,
                timeout=MAX_TIMEOUT_SEC,
                allow_redirects=False,
            )
            location = resp.headers.get("Location")
            if resp.status_code in (301, 302, 303, 307, 308) and location:
                current_url = urljoin(current_url, location)
                if resp.status_code == 303:
                    current_method = "GET"
                    current_body = None
                continue
            return success_response({
                "status": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text[:10000],  # cap response size
            })
        raise AppError(ErrorCode.GENERATE_FAILED, "重定向次数过多")
    except req_lib.RequestException as exc:
        raise AppError(ErrorCode.GENERATE_FAILED, f"代理请求失败: {exc}")
