"""SillyTavern-compatible /api/themes endpoints."""

from __future__ import annotations

from flask import Blueprint
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, sanitize_filename, write_json_file

themes_bp = Blueprint("st_compat_themes", __name__, url_prefix="/themes")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


@themes_bp.post("/save")
@jwt_required()
def save_theme():
    body = _request_body()
    name = body.get("name")
    if not body or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["themes"] / f"{sanitize_filename(str(name))}.json", body)
    return ("", 200)


@themes_bp.post("/delete")
@jwt_required()
def delete_theme():
    body = _request_body()
    name = body.get("name")
    if not body or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["themes"] / f"{sanitize_filename(str(name))}.json"
    if not path.exists():
        return ("", 404)
    path.unlink()
    return ("", 200)
