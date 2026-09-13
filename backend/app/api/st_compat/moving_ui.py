"""SillyTavern-compatible /api/moving-ui endpoints."""

from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, sanitize_filename, write_json_file

moving_ui_bp = Blueprint("st_compat_moving_ui", __name__, url_prefix="/moving-ui")


@moving_ui_bp.post("/save")
@jwt_required()
def save_moving_ui():
    from flask import request

    body = request.get_json(silent=True) or {}
    name = body.get("name")
    if not body or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["moving_ui"] / f"{sanitize_filename(str(name))}.json", body)
    return ("", 200)
