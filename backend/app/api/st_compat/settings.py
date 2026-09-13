"""SillyTavern-compatible /api/settings endpoints."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, humanized_datetime, parse_json_safe, write_json_file

settings_bp = Blueprint("st_compat_settings", __name__, url_prefix="/settings")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


def _read_presets_from_directory(directory: Path):
    file_contents = []
    file_names = []
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            try:
                text = path.read_text(encoding="utf-8")
                json.loads(text)
                file_contents.append(text)
                file_names.append(path.stem)
            except Exception:
                continue
    return file_contents, file_names


def _read_and_parse_from_directory(directory: Path):
    parsed = []
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            value = parse_json_safe(path.read_text(encoding="utf-8"))
            if value is not None:
                parsed.append(value)
    return parsed


@settings_bp.post("/save")
@jwt_required()
def save_settings():
    body = _request_body()
    if not body:
        return (jsonify({"result": "error"}), 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["root"] / "settings.json", body)
    return jsonify({"result": "ok"})


@settings_bp.post("/get")
@jwt_required()
def get_settings():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    settings_path = dirs["root"] / "settings.json"
    try:
        settings_text = settings_path.read_text(encoding="utf-8")
    except OSError:
        return ("", 500)

    novelai_settings, novelai_setting_names = _read_presets_from_directory(dirs["novelai_settings"])
    openai_settings, openai_setting_names = _read_presets_from_directory(dirs["openai_settings"])
    textgen_presets, textgen_preset_names = _read_presets_from_directory(dirs["textgen_settings"])
    koboldai_settings, koboldai_setting_names = _read_presets_from_directory(dirs["koboldai_settings"])

    world_names = []
    for path in sorted(dirs["worlds"].glob("*.json")):
        if path.is_file():
            world_names.append(path.stem)

    return jsonify({
        "settings": settings_text,
        "koboldai_settings": koboldai_settings,
        "koboldai_setting_names": koboldai_setting_names,
        "world_names": world_names,
        "novelai_settings": novelai_settings,
        "novelai_setting_names": novelai_setting_names,
        "openai_settings": openai_settings,
        "openai_setting_names": openai_setting_names,
        "textgenerationwebui_presets": textgen_presets,
        "textgenerationwebui_preset_names": textgen_preset_names,
        "themes": _read_and_parse_from_directory(dirs["themes"]),
        "movingUIPresets": _read_and_parse_from_directory(dirs["moving_ui"]),
        "quickReplyPresets": _read_and_parse_from_directory(dirs["quick_replies"]),
        "instruct": _read_and_parse_from_directory(dirs["instruct"]),
        "context": _read_and_parse_from_directory(dirs["context"]),
        "sysprompt": _read_and_parse_from_directory(dirs["sysprompt"]),
        "reasoning": _read_and_parse_from_directory(dirs["reasoning"]),
        "enable_extensions": True,
        "enable_extensions_auto_update": True,
        "enable_accounts": True,
        "request_compression": {
            "enabled": False,
            "minPayloadSize": 0,
            "maxPayloadSize": 0,
            "timeout": 0,
        },
    })


def _snapshot_prefix(user_id: str) -> str:
    return f"settings_{user_id}_"


@settings_bp.post("/get-snapshots")
@jwt_required()
def get_snapshots():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    prefix = _snapshot_prefix(user_id)
    result = []
    if dirs["backups"].exists():
        for path in sorted(dirs["backups"].glob("*.json")):
            if not path.name.startswith(prefix):
                continue
            stat = path.stat()
            result.append({"date": int(stat.st_ctime * 1000), "name": path.name, "size": stat.st_size})
    return jsonify(result)


@settings_bp.post("/load-snapshot")
@jwt_required()
def load_snapshot():
    body = _request_body()
    name = body.get("name")
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    prefix = _snapshot_prefix(user_id)
    if not name or not str(name).startswith(prefix):
        return (jsonify({"error": "Invalid snapshot name"}), 400)
    path = dirs["backups"] / str(name) if dirs["backups"].exists() else None
    if path is None or not path.exists():
        return ("", 404)
    return Response(path.read_text(encoding="utf-8"), mimetype="application/json")


@settings_bp.post("/make-snapshot")
@jwt_required()
def make_snapshot():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    settings_path = dirs["root"] / "settings.json"
    if not settings_path.exists():
        return ("", 204)
    snapshot_name = f"{_snapshot_prefix(user_id)}{humanized_datetime()}.json"
    shutil.copyfile(settings_path, dirs["backups"] / snapshot_name)
    return ("", 204)


@settings_bp.post("/restore-snapshot")
@jwt_required()
def restore_snapshot():
    body = _request_body()
    name = body.get("name")
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    prefix = _snapshot_prefix(user_id)
    if not name or not str(name).startswith(prefix):
        return (jsonify({"error": "Invalid snapshot name"}), 400)
    path = dirs["backups"] / str(name) if dirs["backups"].exists() else None
    if path is None or not path.exists():
        return ("", 404)
    shutil.copyfile(path, dirs["root"] / "settings.json")
    return ("", 204)
