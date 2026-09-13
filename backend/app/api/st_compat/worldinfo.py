"""SillyTavern-compatible /api/worldinfo endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .helpers import (
    atomic_write_text,
    get_jwt_user_id,
    get_user_dirs,
    parse_json_safe,
    sanitize_filename,
    write_json_file,
)

worldinfo_bp = Blueprint("st_compat_worldinfo", __name__, url_prefix="/worldinfo")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


def _read_world_info(dirs: dict, name: str, allow_dummy: bool = False):
    if not name:
        return {"entries": {}} if allow_dummy else None
    path = dirs["worlds"] / f"{sanitize_filename(name)}.json"
    if not path.exists():
        return {"entries": {}} if allow_dummy else None
    return parse_json_safe(path.read_text(encoding="utf-8"))


@worldinfo_bp.post("/list")
@jwt_required()
def list_world_info():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    data = []
    for path in sorted(dirs["worlds"].glob("*.json")):
        try:
            parsed = parse_json_safe(path.read_text(encoding="utf-8")) or {}
            extensions = parsed.get("extensions") or {}
            data.append({
                "file_id": path.stem,
                "name": parsed.get("name") or path.stem,
                "extensions": extensions if isinstance(extensions, dict) else {},
            })
        except Exception:
            continue
    return jsonify(data)


@worldinfo_bp.post("/get")
@jwt_required()
def get_world_info():
    body = _request_body()
    name = body.get("name")
    if not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    return jsonify(_read_world_info(dirs, str(name), allow_dummy=True) or {})


@worldinfo_bp.post("/delete")
@jwt_required()
def delete_world_info():
    body = _request_body()
    name = body.get("name")
    if not name:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["worlds"] / f"{sanitize_filename(str(name))}.json"
    if not path.exists():
        return ("", 500)
    path.unlink()
    return ("", 200)


@worldinfo_bp.post("/import")
@jwt_required()
def import_world_info():
    from flask import request

    filedata = request.files.get("avatar")
    if not filedata:
        return ("", 400)

    original_name = sanitize_filename(str(filedata.filename or "world.json"))
    file_name = original_name if original_name.endswith(".json") else f"{original_name}.json"
    content = filedata.read().decode("utf-8")
    converted = (request.form.get("convertedData") or "")
    if converted:
        content = converted
    parsed = parse_json_safe(content)
    if not isinstance(parsed, dict) or "entries" not in parsed:
        return ("Is not a valid world info file", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["worlds"] / file_name
    atomic_write_text(path, content)
    return jsonify({"name": path.stem})


@worldinfo_bp.post("/edit")
@jwt_required()
def edit_world_info():
    body = _request_body()
    name = body.get("name")
    data = body.get("data")
    if not body or not name:
        return ("World file must have a name", 400)
    if not isinstance(data, dict) or "entries" not in data:
        return ("Is not a valid world info file", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["worlds"] / f"{sanitize_filename(str(name))}.json"
    write_json_file(path, data)
    return jsonify({"ok": True})
