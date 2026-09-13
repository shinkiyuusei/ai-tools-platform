"""SillyTavern-compatible /api/presets endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, sanitize_filename, write_json_file

presets_bp = Blueprint("st_compat_presets", __name__, url_prefix="/presets")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


def _preset_folder(api_id: str, dirs: dict):
    mapping = {
        "kobold": "koboldai_settings",
        "koboldhorde": "koboldai_settings",
        "novel": "novelai_settings",
        "textgenerationwebui": "textgen_settings",
        "openai": "openai_settings",
        "instruct": "instruct",
        "context": "context",
        "sysprompt": "sysprompt",
        "reasoning": "reasoning",
    }
    return dirs.get(mapping.get(api_id)) if api_id in mapping else None


@presets_bp.post("/save")
@jwt_required()
def save_preset():
    body = _request_body()
    name = sanitize_filename(str(body.get("name") or ""))
    preset = body.get("preset")
    if not preset or not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    folder = _preset_folder(body.get("apiId"), dirs)
    if folder is None:
        return ("", 400)
    write_json_file(folder / f"{name}.json", preset)
    return jsonify({"name": name})


@presets_bp.post("/delete")
@jwt_required()
def delete_preset():
    body = _request_body()
    name = sanitize_filename(str(body.get("name") or ""))
    if not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    folder = _preset_folder(body.get("apiId"), dirs)
    if folder is None:
        return ("", 400)
    path = folder / f"{name}.json"
    if path.exists():
        path.unlink()
        return ("", 200)
    return ("", 404)


@presets_bp.post("/restore")
@jwt_required()
def restore_preset():
    body = _request_body()
    if not body.get("apiId") or not body.get("name"):
        return ("", 400)
    return jsonify({"isDefault": False, "preset": {}})
