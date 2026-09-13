"""SillyTavern-compatible /api/quick-replies endpoints."""

from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, sanitize_filename, write_json_file

quick_replies_bp = Blueprint("st_compat_quick_replies", __name__, url_prefix="/quick-replies")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


@quick_replies_bp.post("/save")
@jwt_required()
def save_quick_reply():
    body = _request_body()
    name = body.get("name")
    if not body or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["quick_replies"] / f"{sanitize_filename(str(name))}.json", body)
    return ("", 200)


@quick_replies_bp.post("/delete")
@jwt_required()
def delete_quick_reply():
    body = _request_body()
    name = body.get("name")
    if not body or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["quick_replies"] / f"{sanitize_filename(str(name))}.json"
    if path.exists():
        path.unlink()
    return ("", 200)
