"""SillyTavern-compatible /api/chats endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .helpers import (
    atomic_write_text,
    get_chat_info,
    get_jwt_user_id,
    get_preview_message,
    get_user_dirs,
    humanized_datetime,
    is_path_within,
    parse_json_safe,
    read_jsonl_file,
    sanitize_filename,
    write_jsonl_file,
)

chats_bp = Blueprint("st_compat_chats", __name__, url_prefix="/chats")


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


def _avatar_internal_name(avatar_url: str) -> str:
    return sanitize_filename(str(avatar_url).replace(".png", ""))


class ChatIntegrityError(Exception):
    pass


def _try_save_chat(chat_data: list, file_path: Path, skip_integrity_check: bool = False) -> None:
    if not skip_integrity_check and file_path.exists():
        existing = read_jsonl_file(file_path)
        new_integrity = None
        if chat_data and isinstance(chat_data[0], dict):
            metadata = chat_data[0].get("chat_metadata") or {}
            new_integrity = metadata.get("integrity")
        existing_integrity = None
        if existing and isinstance(existing[0], dict):
            metadata = existing[0].get("chat_metadata") or {}
            existing_integrity = metadata.get("integrity")
        if existing_integrity and new_integrity and existing_integrity != new_integrity:
            raise ChatIntegrityError("Chat integrity check failed")
    write_jsonl_file(file_path, chat_data)


def _get_chat_file_path(dirs: dict, avatar_url: str, file_name: str) -> Path | None:
    chat_dir = dirs["chats"] / _avatar_internal_name(avatar_url)
    file_name = sanitize_filename(file_name)
    if not file_name.endswith(".jsonl"):
        file_name += ".jsonl"
    path = chat_dir / file_name
    if not is_path_within(dirs["chats"], path):
        return None
    return path


@chats_bp.post("/save")
@jwt_required()
def save_chat():
    body = _request_body()
    chat_data = body.get("chat")
    avatar_url = body.get("avatar_url")
    file_name = body.get("file_name")
    if not isinstance(chat_data, list) or not avatar_url or not file_name:
        return (jsonify({"error": "The request's body.chat is not an array."}), 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = _get_chat_file_path(dirs, avatar_url, str(file_name))
    if path is None:
        return ("", 400)
    try:
        _try_save_chat(chat_data, path, bool(body.get("force")))
        return jsonify({"ok": True})
    except ChatIntegrityError:
        return (jsonify({"error": "integrity"}), 400)
    except Exception:
        return (jsonify({"error": "An error has occurred, see the console logs for more information."}), 500)


@chats_bp.post("/get")
@jwt_required()
def get_chat():
    body = _request_body()
    avatar_url = body.get("avatar_url")
    file_name = body.get("file_name")
    if not avatar_url:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    chat_dir = dirs["chats"] / _avatar_internal_name(avatar_url)
    if not is_path_within(dirs["chats"], chat_dir):
        return jsonify({})
    if not chat_dir.exists():
        chat_dir.mkdir(parents=True, exist_ok=True)
        return jsonify({})
    if not file_name:
        return jsonify({})

    path = _get_chat_file_path(dirs, avatar_url, str(file_name))
    if path is None:
        return jsonify({})
    return jsonify(read_jsonl_file(path))


@chats_bp.post("/rename")
@jwt_required()
def rename_chat():
    body = _request_body()
    original_file = body.get("original_file")
    renamed_file = body.get("renamed_file")
    if not original_file or not renamed_file:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    if body.get("is_group"):
        folder = dirs["group_chats"]
        if not is_path_within(dirs["group_chats"], folder):
            return ("", 400)
    else:
        folder = dirs["chats"] / _avatar_internal_name(str(body.get("avatar_url") or ""))
        if not is_path_within(dirs["chats"], folder):
            return ("", 400)

    original_path = folder / sanitize_filename(str(original_file))
    renamed_path = folder / sanitize_filename(str(renamed_file))
    if not is_path_within(folder, original_path) or not is_path_within(folder, renamed_path):
        return ("", 400)
    if not original_path.exists() or renamed_path.exists():
        return (jsonify({"error": True}), 400)

    shutil.copyfile(original_path, renamed_path)
    original_path.unlink()
    return jsonify({"ok": True, "sanitizedFileName": renamed_path.stem})


@chats_bp.post("/delete")
@jwt_required()
def delete_chat():
    body = _request_body()
    avatar_url = body.get("avatar_url")
    chatfile = body.get("chatfile")
    if not avatar_url or not chatfile:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = _get_chat_file_path(dirs, avatar_url, str(chatfile))
    if path is None:
        return ("", 400)
    if path.exists():
        path.unlink()
        return jsonify({"ok": True})
    return ("", 400)


@chats_bp.post("/export")
@jwt_required()
def export_chat():
    body = _request_body()
    file_name = body.get("file")
    is_group = body.get("is_group") is True or body.get("is_group") == "true"
    if not file_name or (not body.get("avatar_url") and not is_group):
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    if is_group:
        folder = dirs["group_chats"]
        if not is_path_within(dirs["group_chats"], folder):
            return ("", 400)
    else:
        folder = dirs["chats"] / _avatar_internal_name(str(body.get("avatar_url")))
        if not is_path_within(dirs["chats"], folder):
            return ("", 400)
    path = folder / sanitize_filename(str(file_name))
    if not is_path_within(folder, path):
        return ("", 400)
    if not path.exists():
        return (jsonify({"message": f"Could not find JSONL file to export. Source chat file: {path}."}), 404)

    export_name = body.get("exportfilename") or path.name
    if body.get("format") == "jsonl":
        return jsonify({"message": f"Chat saved to {export_name}", "result": path.read_text(encoding="utf-8")})

    lines = read_jsonl_file(path)
    buffer = []
    for data in lines:
        if data.get("is_system"):
            continue
        if data.get("mes"):
            name = data.get("name")
            message = (data.get("extra") or {}).get("display_text") or data.get("mes") or ""
            buffer.append(f"{name}: {message}\n\n")
    return jsonify({"message": f"Chat saved to {export_name}", "result": "".join(buffer)})


@chats_bp.post("/group/import")
@jwt_required()
def import_group_chat():
    from flask import request

    filedata = request.files.get("avatar")
    if not filedata:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    chat_name = humanized_datetime()
    target = dirs["group_chats"] / f"{chat_name}.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    filedata.save(target)
    return jsonify({"res": chat_name})


def _import_json_chat(data: dict, user_name: str, character_name: str):
    if isinstance(data.get("messages"), list):  # Agnai
        items = []
        for message in data["messages"]:
            is_user = bool(message.get("userId"))
            items.append({
                "name": user_name if is_user else character_name,
                "is_user": is_user,
                "send_date": message.get("send_date") or message.get("createdAt"),
                "mes": message.get("msg") or message.get("content") or "",
                "extra": {},
            })
    elif isinstance(data.get("data_visible"), list):  # Ooba
        items = []
        for pair in data["data_visible"]:
            if pair and pair[0]:
                items.append({"name": user_name, "is_user": True, "mes": pair[0], "send_date": None, "extra": {}})
            if len(pair) > 1 and pair[1]:
                items.append({"name": character_name, "is_user": False, "mes": pair[1], "send_date": None, "extra": {}})
    elif data.get("type") == "risuChat":  # RisuAI
        items = []
        for message in (data.get("data") or {}).get("message") or []:
            is_user = message.get("role") == "user"
            items.append({
                "name": message.get("name") or (user_name if is_user else character_name),
                "is_user": is_user,
                "send_date": message.get("time"),
                "mes": message.get("data") or "",
                "extra": {},
            })
    elif isinstance(data.get("histories"), dict):  # CAI Tools
        items = []
        for history in (data.get("histories") or {}).get("histories") or []:
            for message in history.get("msgs") or []:
                source = message.get("src") or {}
                is_user = bool(source.get("is_human"))
                items.append({
                    "name": user_name if is_user else character_name,
                    "is_user": is_user,
                    "send_date": message.get("send_date"),
                    "mes": message.get("text") or "",
                    "extra": {},
                })
    elif isinstance(data.get("savedsettings"), dict):  # Kobold Lite
        saved = data.get("savedsettings") or {}
        user_name = saved.get("chatname") or user_name
        opponent = str(saved.get("chatopponent") or character_name).split("||$||")[0]
        character_name = opponent
        items = []
        for action in data.get("actions") or []:
            if not isinstance(action, str):
                continue
            is_user = "{{[INPUT]}}" in action
            text = action.replace("{{[INPUT]}}", "").replace("{{[OUTPUT]}}", "").strip()
            items.append({
                "name": user_name if is_user else character_name,
                "is_user": is_user,
                "send_date": None,
                "mes": text,
                "extra": {},
            })
        if data.get("prompt"):
            prompt = str(data["prompt"]).replace("{{[INPUT]}}", "").replace("{{[OUTPUT]}}", "").strip()
            items.insert(0, {"name": user_name if "{{[INPUT]}}" in str(data["prompt"]) else character_name, "is_user": "{{[INPUT]}}" in str(data["prompt"]), "send_date": None, "mes": prompt, "extra": {}})
    else:
        raise ValueError("Incorrect chat format .json")

    header = {"chat_metadata": {}, "user_name": "unused", "character_name": "unused"}
    return [header] + items


@chats_bp.post("/import")
@jwt_required()
def import_chat():
    from flask import request

    body = _request_body()
    file_format = body.get("file_type")
    avatar_url = body.get("avatar_url")
    filedata = request.files.get("avatar")
    if not file_format or not avatar_url or not filedata:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    character_name = sanitize_filename(str(body.get("character_name") or "Character"))
    user_name = sanitize_filename(str(body.get("user_name") or "User"))
    chat_dir = dirs["chats"] / _avatar_internal_name(avatar_url)
    if not is_path_within(dirs["chats"], chat_dir):
        return ("", 400)
    chat_dir.mkdir(parents=True, exist_ok=True)
    upload_bytes = filedata.read()

    try:
        if file_format == "json":
            data = parse_json_safe(upload_bytes.decode("utf-8"))
            if not isinstance(data, dict):
                return jsonify({"error": True})
            chat = _import_json_chat(data, user_name, character_name)
            file_names = []
            for single in chat if isinstance(chat[0], list) else [chat]:
                file_name = f"{character_name} - {humanized_datetime()} imported.jsonl"
                write_jsonl_file(chat_dir / file_name, single)
                file_names.append(file_name)
            return jsonify({"res": True, "fileNames": file_names})

        if file_format == "jsonl":
            lines = upload_bytes.decode("utf-8").splitlines()
            header = parse_json_safe(lines[0]) if lines else None
            if not isinstance(header, dict) or not (
                "user_name" in header or "name" in header or "chat_metadata" in header
            ):
                return jsonify({"error": True})
            file_name = f"{character_name} - {humanized_datetime()} imported.jsonl"
            atomic_write_text(chat_dir / file_name, upload_bytes.decode("utf-8"))
            return jsonify({"res": True, "fileNames": [file_name]})
    except Exception:
        return jsonify({"error": True})
    return jsonify({"error": True})


@chats_bp.post("/group/get")
@jwt_required()
def get_group_chat():
    body = _request_body()
    group_id = body.get("id")
    if not group_id:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["group_chats"] / f"{sanitize_filename(str(group_id))}.jsonl"
    return jsonify(read_jsonl_file(path))


@chats_bp.post("/group/info")
@jwt_required()
def group_chat_info():
    body = _request_body()
    group_id = body.get("id")
    if not group_id:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["group_chats"] / f"{sanitize_filename(str(group_id))}.jsonl"
    if not path.exists():
        return ("", 500)
    return jsonify(get_chat_info(path))


@chats_bp.post("/group/delete")
@jwt_required()
def delete_group_chat():
    body = _request_body()
    group_id = body.get("id")
    if not group_id:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["group_chats"] / f"{sanitize_filename(str(group_id))}.jsonl"
    if path.exists():
        path.unlink()
        return jsonify({"ok": True})
    return ("", 400)


@chats_bp.post("/group/save")
@jwt_required()
def save_group_chat():
    body = _request_body()
    group_id = body.get("id")
    chat_data = body.get("chat")
    if not group_id:
        return ("", 400)
    if not isinstance(chat_data, list):
        return (jsonify({"error": "The request's body.chat is not an array."}), 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["group_chats"] / f"{sanitize_filename(str(group_id))}.jsonl"
    try:
        _try_save_chat(chat_data, path, bool(body.get("force")))
        return jsonify({"ok": True})
    except ChatIntegrityError:
        return (jsonify({"error": "integrity"}), 400)
    except Exception:
        return (jsonify({"error": "An error has occurred, see the console logs for more information."}), 500)


@chats_bp.post("/search")
@jwt_required()
def search_chats():
    body = _request_body()
    query = str(body.get("query") or "").strip().lower()
    fragments = [fragment for fragment in query.split() if fragment]
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)

    chat_files = []
    if body.get("group_id"):
        target_group = None
        for group_file in dirs["groups"].glob("*.json"):
            group_data = parse_json_safe(group_file.read_text(encoding="utf-8"))
            if isinstance(group_data, dict) and str(group_data.get("id")) == str(body.get("group_id")):
                target_group = group_data
                break
        if not target_group or not isinstance(target_group.get("chats"), list):
            return jsonify([])
        for chat_id in target_group["chats"]:
            path = dirs["group_chats"] / f"{sanitize_filename(str(chat_id))}.jsonl"
            if path.exists():
                chat_files.append(path)
    else:
        character_name = _avatar_internal_name(str(body.get("avatar_url") or ""))
        chat_dir = dirs["chats"] / character_name
        if not is_path_within(dirs["chats"], chat_dir):
            return jsonify([])
        if chat_dir.exists():
            chat_files = [path for path in chat_dir.glob("*.jsonl") if path.is_file()]

    results = []
    for path in chat_files:
        def has_match(messages):
            if not fragments:
                return True
            for message in messages:
                text = str((message.get("extra") or {}).get("display_text") or message.get("mes") or "").lower()
                if all(fragment in text for fragment in fragments):
                    return True
            return False

        info = get_chat_info(path, matcher=has_match if query else None)
        if not info.get("file_name"):
            continue
        has_text_match = info.get("match") or has_match([]) or (
            fragments and all(fragment in str(info.get("file_id") or "").lower() for fragment in fragments)
        )
        if query and info.get("chat_items") == 0 and not has_text_match:
            continue
        if not query or has_text_match:
            results.append({
                "file_name": info.get("file_id"),
                "file_size": info.get("file_size"),
                "message_count": info.get("chat_items"),
                "last_mes": info.get("last_mes"),
                "preview_message": get_preview_message(info.get("mes")),
            })
    return jsonify(results)


@chats_bp.post("/recent")
@jwt_required()
def recent_chats():
    body = _request_body()
    pinned = body.get("pinned") if isinstance(body.get("pinned"), list) else []
    try:
        max_chats = int(body.get("max")) + len(pinned)
    except (TypeError, ValueError):
        max_chats = 10 ** 12

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    all_chat_files = []

    for png_file in dirs["characters"].glob("*.png"):
        if not png_file.is_file():
            continue
        chat_dir = dirs["chats"] / png_file.stem
        if not chat_dir.exists():
            continue
        for path in chat_dir.glob("*.jsonl"):
            if path.is_file():
                all_chat_files.append({"png_file": png_file.name, "path": path, "mtime": path.stat().st_mtime})

    for group_file in dirs["groups"].glob("*.json"):
        if not group_file.is_file():
            continue
        group_data = parse_json_safe(group_file.read_text(encoding="utf-8"))
        if not isinstance(group_data, dict) or not isinstance(group_data.get("chats"), list):
            continue
        for chat_id in group_data["chats"]:
            path = dirs["group_chats"] / f"{sanitize_filename(str(chat_id))}.jsonl"
            if path.exists():
                all_chat_files.append({"group_id": str(group_data.get("id")), "path": path, "mtime": path.stat().st_mtime})

    for path in dirs["chats"].glob("*.jsonl"):
        if path.is_file():
            all_chat_files.append({"path": path, "mtime": path.stat().st_mtime})

    def is_pinned(entry):
        return any(
            p.get("file_name") == entry["path"].name
            and (p.get("avatar") == entry.get("png_file") or p.get("group") == entry.get("group_id"))
            for p in pinned
        )

    all_chat_files.sort(key=lambda entry: (not is_pinned(entry), -entry["mtime"]))
    recent = all_chat_files[:max_chats]
    results = []
    for entry in recent:
        additional = {"group": entry["group_id"]} if entry.get("group_id") else {"avatar": entry.get("png_file")}
        info = get_chat_info(entry["path"], additional, with_metadata=bool(body.get("metadata")))
        if info.get("file_name"):
            results.append(info)
    return jsonify(results)
