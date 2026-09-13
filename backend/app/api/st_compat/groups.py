"""SillyTavern-compatible /api/groups endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, now_millis, parse_json_safe, sanitize_filename, write_json_file

groups_bp = Blueprint("st_compat_groups", __name__, url_prefix="/groups")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


@groups_bp.post("/all")
@jwt_required()
def all_groups():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    groups = []
    for group_file in sorted(dirs["groups"].glob("*.json")):
        try:
            group = parse_json_safe(group_file.read_text(encoding="utf-8"))
            if not isinstance(group, dict):
                continue
            stat = group_file.stat()
            added_ms = int(stat.st_ctime * 1000)
            group["date_added"] = added_ms
            group["create_date"] = datetime.fromtimestamp(stat.st_ctime, timezone.utc).isoformat()

            chat_size = 0
            date_last_chat = 0
            chats = group.get("chats")
            if isinstance(chats, list):
                for chat_id in chats:
                    chat_file = dirs["group_chats"] / f"{sanitize_filename(str(chat_id))}.jsonl"
                    if chat_file.exists():
                        chat_stat = chat_file.stat()
                        chat_size += chat_stat.st_size
                        date_last_chat = max(date_last_chat, int(chat_stat.st_mtime * 1000))
            group["date_last_chat"] = date_last_chat
            group["chat_size"] = chat_size
            groups.append(group)
        except Exception:
            continue
    return jsonify(groups)


@groups_bp.post("/create")
@jwt_required()
def create_group():
    body = _request_body()
    if not body:
        return ("", 400)
    group_id = str(now_millis())
    group_metadata = {
        "id": group_id,
        "name": body.get("name") or "New Group",
        "members": body.get("members") or [],
        "avatar_url": body.get("avatar_url"),
        "allow_self_responses": bool(body.get("allow_self_responses")),
        "activation_strategy": body.get("activation_strategy", 0),
        "generation_mode": body.get("generation_mode", 0),
        "disabled_members": body.get("disabled_members") or [],
        "fav": body.get("fav"),
        "chat_id": body.get("chat_id") or group_id,
        "chats": body.get("chats") or [group_id],
        "auto_mode_delay": body.get("auto_mode_delay", 5),
        "generation_mode_join_prefix": body.get("generation_mode_join_prefix") or "",
        "generation_mode_join_suffix": body.get("generation_mode_join_suffix") or "",
    }
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["groups"] / f"{sanitize_filename(group_id)}.json", group_metadata)
    return jsonify(group_metadata)


@groups_bp.post("/edit")
@jwt_required()
def edit_group():
    body = _request_body()
    group_id = body.get("id")
    if not body or not group_id:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    write_json_file(dirs["groups"] / f"{sanitize_filename(str(group_id))}.json", body)
    return jsonify({"ok": True})


@groups_bp.post("/delete")
@jwt_required()
def delete_group():
    body = _request_body()
    group_id = body.get("id")
    if not body or not group_id:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    group_file = dirs["groups"] / f"{sanitize_filename(str(group_id))}.json"
    try:
        group = parse_json_safe(group_file.read_text(encoding="utf-8"))
        if isinstance(group, dict) and isinstance(group.get("chats"), list):
            for chat_id in group["chats"]:
                chat_file = dirs["group_chats"] / f"{sanitize_filename(str(chat_id))}.jsonl"
                if chat_file.exists():
                    chat_file.unlink()
    except Exception:
        pass
    if group_file.exists():
        group_file.unlink()
    return jsonify({"ok": True})
