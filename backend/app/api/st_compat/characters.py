"""SillyTavern-compatible /api/characters endpoints."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from . import png_utils
from .helpers import (
    calculate_chat_size,
    deep_merge,
    get_chat_info,
    get_dict_path,
    get_jwt_user_id,
    get_unique_name,
    get_user_dirs,
    humanized_datetime,
    is_path_within,
    parse_json_safe,
    read_json_file,
    sanitize_filename,
    uploaded_file,
)

characters_bp = Blueprint("st_compat_characters", __name__, url_prefix="/characters")


def _request_body() -> dict:
    """Merge JSON body with multipart form fields (Express req.body behavior)."""
    body = {}
    from flask import request

    json_body = request.get_json(silent=True)
    if isinstance(json_body, dict):
        body.update(json_body)
    if request.form:
        body.update({key: value for key, value in request.form.items()})
    return body


def _parse_string_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    text = str(value)
    parsed = parse_json_safe(text)
    if isinstance(parsed, list):
        return parsed
    return [item.strip() for item in text.split(",") if item.strip()]


def _format_character_data(body: dict, dirs: dict) -> dict:
    """Port of SillyTavern's charaFormatData (produces a V2 card)."""
    char = parse_json_safe(body.get("json_data")) or {}
    if isinstance(char, dict):
        char.pop("json_data", None)
    else:
        char = {}

    ch_name = body.get("ch_name") or ""
    description = body.get("description") or ""
    personality = body.get("personality") or ""
    scenario = body.get("scenario") or ""
    first_mes = body.get("first_mes") or ""
    mes_example = body.get("mes_example") or ""
    creator_notes = body.get("creator_notes") or ""
    talkativeness = body.get("talkativeness") or 0.5
    try:
        talkativeness = float(talkativeness)
    except (TypeError, ValueError):
        talkativeness = 0.5
    fav = str(body.get("fav")) == "true" or body.get("fav") is True
    tags = _parse_string_list(body.get("tags"))

    alternate_greetings = body.get("alternate_greetings")
    if isinstance(alternate_greetings, str):
        alternate_greetings = parse_json_safe(alternate_greetings, alternate_greetings)
    if not isinstance(alternate_greetings, list):
        alternate_greetings = [alternate_greetings] if alternate_greetings else []

    depth_prompt_depth = body.get("depth_prompt_depth", 4)
    try:
        depth_prompt_depth = int(depth_prompt_depth)
    except (TypeError, ValueError):
        depth_prompt_depth = 4
    depth_prompt_role = body.get("depth_prompt_role") or "system"

    char.update({
        "name": ch_name,
        "description": description,
        "personality": personality,
        "scenario": scenario,
        "first_mes": first_mes,
        "mes_example": mes_example,
        "creatorcomment": creator_notes,
        "avatar": "none",
        "chat": f"{ch_name} - {humanized_datetime()}",
        "talkativeness": talkativeness,
        "fav": fav,
        "tags": tags,
        "spec": "chara_card_v2",
        "spec_version": "2.0",
    })

    data = char.setdefault("data", {})
    data.update({
        "name": ch_name,
        "description": description,
        "personality": personality,
        "scenario": scenario,
        "first_mes": first_mes,
        "mes_example": mes_example,
        "creator_notes": creator_notes,
        "system_prompt": body.get("system_prompt") or "",
        "post_history_instructions": body.get("post_history_instructions") or "",
        "tags": tags,
        "creator": body.get("creator") or "",
        "character_version": body.get("character_version") or "",
        "alternate_greetings": alternate_greetings,
    })
    extensions = data.setdefault("extensions", {})
    extensions.update({
        "talkativeness": talkativeness,
        "fav": fav,
        "world": body.get("world") or "",
    })
    depth_prompt = extensions.setdefault("depth_prompt", {})
    depth_prompt.update({
        "prompt": body.get("depth_prompt_prompt") or "",
        "depth": depth_prompt_depth,
        "role": depth_prompt_role,
    })

    world_name = body.get("world")
    if world_name:
        world_file = dirs["worlds"] / f"{sanitize_filename(world_name)}.json"
        world_data = read_json_file(world_file)
        entries = world_data.get("entries") if isinstance(world_data, dict) else None
        if isinstance(entries, dict):
            data["character_book"] = {
                "name": str(world_name),
                "entries": list(entries.values()),
            }

    return char


def _read_from_v2(card: dict) -> dict:
    card = dict(card)
    card.pop("json_data", None)
    data = card.get("data")
    if not isinstance(data, dict):
        return card

    mappings = {
        "name": ("name", None),
        "description": ("description", None),
        "personality": ("personality", None),
        "scenario": ("scenario", None),
        "first_mes": ("first_mes", None),
        "mes_example": ("mes_example", None),
        "talkativeness": ("extensions.talkativeness", 0.5),
        "fav": ("extensions.fav", False),
        "tags": ("tags", None),
    }
    for char_field, (path, default) in mappings.items():
        value = get_dict_path(data, path)
        if value is None and default is not None:
            value = default
        if value is not None:
            card[char_field] = value

    if not card.get("chat"):
        card["chat"] = f"{card.get('name', '')} - {humanized_datetime()}"
    return card


def _convert_to_v2(card: dict, dirs: dict) -> dict:
    body = {
        "json_data": json.dumps(card, ensure_ascii=False),
        "ch_name": card.get("name", ""),
        "description": card.get("description"),
        "personality": card.get("personality"),
        "scenario": card.get("scenario"),
        "first_mes": card.get("first_mes"),
        "mes_example": card.get("mes_example"),
        "creator_notes": card.get("creatorcomment"),
        "talkativeness": card.get("talkativeness"),
        "fav": card.get("fav"),
        "creator": card.get("creator"),
        "tags": card.get("tags", []),
        "depth_prompt_prompt": card.get("depth_prompt_prompt"),
        "depth_prompt_depth": card.get("depth_prompt_depth"),
        "depth_prompt_role": card.get("depth_prompt_role"),
    }
    result = _format_character_data(body, dirs)
    result["chat"] = card.get("chat") or f"{result.get('name', '')} - {humanized_datetime()}"
    if card.get("create_date"):
        result["create_date"] = card["create_date"]
    return result


def _get_chara_card_v2(card: dict, dirs: dict, hoist_date: bool = True) -> dict:
    if "spec" not in card:
        card = _convert_to_v2(card, dirs)
        if hoist_date and not card.get("create_date"):
            card["create_date"] = datetime.now(timezone.utc).isoformat()
    else:
        card = _read_from_v2(card)
    return card


def _to_shallow(character: dict) -> dict:
    data = character.get("data") or {}
    extensions = data.get("extensions") or {}
    return {
        "name": character.get("name", ""),
        "description": character.get("description", ""),
        "personality": character.get("personality", ""),
        "scenario": character.get("scenario", ""),
        "first_mes": character.get("first_mes", ""),
        "mes_example": character.get("mes_example", ""),
        "avatar": character.get("avatar", ""),
        "chat": character.get("chat", ""),
        "create_date": character.get("create_date", ""),
        "date_added": character.get("date_added", 0),
        "date_last_chat": character.get("date_last_chat", 0),
        "chat_size": character.get("chat_size", 0),
        "data_size": character.get("data_size", 0),
        "tags": character.get("tags", []),
        "data": {
            "name": data.get("name", ""),
            "character_version": data.get("character_version", ""),
            "creator": data.get("creator", ""),
            "creator_notes": data.get("creator_notes", ""),
            "tags": data.get("tags", []),
            "extensions": {
                "fav": extensions.get("fav", False),
                "world": extensions.get("world", ""),
            },
        },
    }


def _process_character(file_name: str, dirs: dict, shallow: bool = False) -> dict:
    try:
        png_path = dirs["characters"] / file_name
        raw_data = png_utils.read_character_data(png_path.read_bytes())
        card = parse_json_safe(raw_data)
        if not isinstance(card, dict):
            return {"date_added": 0, "date_last_chat": 0, "chat_size": 0}

        character = _get_chara_card_v2(card, dirs, hoist_date=False)
        character["avatar"] = file_name
        character["json_data"] = raw_data

        stat = png_path.stat()
        character["date_added"] = int(stat.st_ctime * 1000)
        character["create_date"] = character.get("create_date") or datetime.fromtimestamp(
            stat.st_ctime, timezone.utc
        ).isoformat()

        chat_dir = dirs["chats"] / Path(file_name).stem
        chat_size, date_last_chat = calculate_chat_size(chat_dir)
        character["chat_size"] = chat_size
        character["date_last_chat"] = date_last_chat
        data = character.get("data") or {}
        character["data_size"] = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        return _to_shallow(character) if shallow else character
    except Exception:
        return {"date_added": 0, "date_last_chat": 0, "chat_size": 0}


def _get_png_name(base_name: str, dirs: dict) -> str:
    safe = sanitize_filename(base_name)

    def exists(name: str) -> bool:
        return (dirs["characters"] / f"{name}.png").exists()

    return get_unique_name(safe, exists, start_index=0) or safe


def _read_card_json(png_path: Path) -> str:
    return png_utils.read_character_data(png_path.read_bytes())


def _write_card(png_path: Path, internal_name: str, card_json: str, upload_bytes: bytes | None = None, fallback: bytes | None = None) -> None:
    if upload_bytes is not None and png_utils.is_png(upload_bytes):
        output = png_utils.write_character_data(upload_bytes, card_json)
    elif fallback is not None:
        output = png_utils.write_character_data(fallback, card_json)
    elif png_path.exists():
        output = png_utils.write_character_data(png_path.read_bytes(), card_json)
    else:
        output = png_utils.default_avatar_png(card_json)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.write_bytes(output)


def _unset_private_fields(card: dict) -> None:
    card["fav"] = False
    data = card.get("data")
    if isinstance(data, dict):
        extensions = data.setdefault("extensions", {})
        extensions["fav"] = False
    card.pop("chat", None)


def _validate_card(card: dict) -> bool:
    if card.get("spec") in ("chara_card_v2", "chara_card_v3"):
        return isinstance(card.get("data"), dict)
    return all(key in card for key in ("name", "description", "personality", "scenario", "first_mes", "mes_example"))


@characters_bp.post("/create")
@jwt_required()
def create_character():
    body = _request_body()
    if not body:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    ch_name = sanitize_filename(body.get("ch_name") or "")
    if not ch_name:
        return ("", 400)

    internal_name = sanitize_filename(body.get("file_name") or "") or _get_png_name(ch_name, dirs)
    avatar_name = f"{internal_name}.png"
    chats_dir = dirs["chats"] / internal_name
    chats_dir.mkdir(parents=True, exist_ok=True)

    card_json = json.dumps(_format_character_data(body, dirs), ensure_ascii=False)
    avatar = uploaded_file()
    upload_bytes = avatar.read() if avatar else None
    _write_card(dirs["characters"] / avatar_name, internal_name, card_json, upload_bytes=upload_bytes)
    return Response(avatar_name, mimetype="text/plain")


@characters_bp.post("/rename")
@jwt_required()
def rename_character():
    body = _request_body()
    if not body.get("avatar_url") or not body.get("new_name"):
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    old_avatar_name = sanitize_filename(str(body["avatar_url"]))
    new_name = sanitize_filename(body["new_name"])
    old_internal_name = Path(old_avatar_name).stem
    new_internal_name = _get_png_name(new_name, dirs)
    new_avatar_name = f"{new_internal_name}.png"

    old_avatar_path = dirs["characters"] / old_avatar_name
    if not old_avatar_path.exists():
        return ("", 500)

    try:
        raw_data = _read_card_json(old_avatar_path)
        card = _get_chara_card_v2(parse_json_safe(raw_data), dirs)
        card["name"] = new_name
        card["data"]["name"] = new_name
        new_data = json.dumps(card, ensure_ascii=False)
        _write_card(old_avatar_path, new_internal_name, new_data)

        old_chats = dirs["chats"] / old_internal_name
        new_chats = dirs["chats"] / new_internal_name
        if old_chats.exists() and not new_chats.exists():
            import shutil

            shutil.copytree(old_chats, new_chats)
            shutil.rmtree(old_chats)

        old_avatar_path.unlink()
        return jsonify({"avatar": new_avatar_name})
    except Exception:
        return ("", 500)


@characters_bp.post("/edit")
@jwt_required()
def edit_character():
    body = _request_body()
    if not body:
        return ("Error: no response body detected", 400)

    ch_name = body.get("ch_name")
    if ch_name in ("", None, "."):
        return ("Error: invalid name.", 400)

    avatar_url = body.get("avatar_url")
    if not avatar_url:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / sanitize_filename(str(avatar_url))
    if not png_path.exists():
        return ("", 400)

    try:
        char = _format_character_data(body, dirs)
        if body.get("chat") is not None:
            char["chat"] = body.get("chat")
        if body.get("create_date") is not None:
            char["create_date"] = body.get("create_date")
        card_json = json.dumps(char, ensure_ascii=False)
        avatar = uploaded_file()
        upload_bytes = avatar.read() if avatar else None
        _write_card(png_path, Path(avatar_url).stem, card_json, upload_bytes=upload_bytes, fallback=png_path.read_bytes())
        return ("", 200)
    except Exception:
        return ("", 500)


@characters_bp.post("/edit-avatar")
@jwt_required()
def edit_avatar():
    avatar = uploaded_file()
    if not avatar:
        return ("Error: no file uploaded", 400)
    body = _request_body()
    avatar_url = body.get("avatar_url")
    if not avatar_url:
        return ("Error: no avatar_url in request body", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / sanitize_filename(str(avatar_url))
    if not png_path.exists():
        return ("Error: character file does not exist", 400)
    try:
        raw_data = _read_card_json(png_path)
    except Exception:
        return ("Error: failed to read character data", 400)

    try:
        _write_card(png_path, Path(avatar_url).stem, raw_data, upload_bytes=avatar.read())
        return ("", 200)
    except Exception:
        return ("", 500)


@characters_bp.post("/edit-attribute")
@jwt_required()
def edit_attribute():
    body = _request_body()
    if not body:
        return ("Error: no response body detected", 400)
    if body.get("ch_name") in ("", None, "."):
        return ("Error: invalid name.", 400)
    if body.get("field") == "json_data":
        return ("Error: cannot edit json_data field.", 400)

    avatar_url = body.get("avatar_url")
    field = body.get("field")
    if not avatar_url or not field:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / sanitize_filename(str(avatar_url))
    if not png_path.exists():
        return ("", 400)
    try:
        char = parse_json_safe(_read_card_json(png_path))
        data = char.get("data") or {}
        if field not in char and field not in data:
            return ("Error: invalid field.", 400)
        char[field] = body.get("value")
        data[field] = body.get("value")
        _write_card(png_path, Path(avatar_url).stem, json.dumps(char, ensure_ascii=False), fallback=png_path.read_bytes())
        return ("", 200)
    except Exception:
        return ("", 500)


@characters_bp.post("/merge-attributes")
@jwt_required()
def merge_attributes():
    body = _request_body()
    if not body:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)

    # Bulk mode
    if isinstance(body.get("avatars"), list):
        avatars = body["avatars"]
        update = body.get("data")
        if not isinstance(update, dict):
            return (jsonify({"message": "No valid update data provided."}), 400)

        if not avatars:
            avatars = [f.name for f in dirs["characters"].glob("*.png") if f.is_file()]
        avatars = [sanitize_filename(str(avatar)) for avatar in avatars]
        for avatar in avatars:
            if not avatar or Path(avatar).suffix.lower() != ".png":
                return (jsonify({"message": f"Invalid avatar filename: {avatar}"}), 400)

        updated, skipped, failed = [], [], []
        for avatar in avatars:
            png_path = dirs["characters"] / avatar
            try:
                card = parse_json_safe(_read_card_json(png_path))
                if not isinstance(card, dict):
                    failed.append(avatar)
                    continue
                filter_path = body.get("filter", {}).get("path")
                if filter_path and get_dict_path(card, filter_path) is None:
                    skipped.append(avatar)
                    continue
                merged = deep_merge(card, update)
                if not _validate_card(merged):
                    failed.append(avatar)
                    continue
                _write_card(png_path, Path(avatar).stem, json.dumps(merged, ensure_ascii=False), fallback=png_path.read_bytes())
                updated.append(avatar)
            except Exception:
                failed.append(avatar)
        return jsonify({"updated": updated, "skipped": skipped, "failed": failed})

    # Single mode
    avatar = body.get("avatar")
    if not avatar:
        return (jsonify({"message": "No avatar provided"}), 400)
    avatar = sanitize_filename(str(avatar))
    if not avatar:
        return (jsonify({"message": "No avatar provided"}), 400)
    png_path = dirs["characters"] / avatar
    if not png_path.exists():
        return (jsonify({"message": f"Validation failed for {avatar}", "error": "Character not found"}), 400)
    try:
        card = parse_json_safe(_read_card_json(png_path))
        merged = deep_merge(card, body)
        if not _validate_card(merged):
            return (jsonify({"message": f"Validation failed for {avatar}"}), 400)
        _write_card(png_path, Path(avatar).stem, json.dumps(merged, ensure_ascii=False), fallback=png_path.read_bytes())
        return ("", 200)
    except Exception as exc:
        return (jsonify({"message": "Unexpected error while saving character.", "error": str(exc)}), 500)


@characters_bp.post("/delete")
@jwt_required()
def delete_character():
    body = _request_body()
    avatar_url = body.get("avatar_url")
    if not avatar_url:
        return ("", 400)
    avatar_url = sanitize_filename(str(avatar_url))
    if not avatar_url:
        return ("", 403)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / avatar_url
    if not png_path.exists():
        return ("", 400)

    png_path.unlink()
    dir_name = Path(avatar_url).stem
    if not dir_name:
        return ("", 403)
    if body.get("delete_chats") is True or body.get("delete_chats") == "true":
        import shutil

        shutil.rmtree(dirs["chats"] / dir_name, ignore_errors=True)
    return ("", 200)


@characters_bp.post("/all")
@jwt_required()
def all_characters():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    try:
        png_files = [f.name for f in dirs["characters"].glob("*.png") if f.is_file()]
        characters = [_process_character(file, dirs) for file in png_files]
        return jsonify([c for c in characters if c.get("name")])
    except Exception:
        return (jsonify({"overflow": False, "error": True}), 500)


@characters_bp.post("/get")
@jwt_required()
def get_character():
    body = _request_body()
    if not body:
        return ("", 400)
    avatar_url = body.get("avatar_url")
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / sanitize_filename(str(avatar_url)) if avatar_url else None
    if not png_path or not png_path.exists():
        return ("", 404)
    return jsonify(_process_character(avatar_url, dirs))


@characters_bp.post("/chats")
@jwt_required()
def character_chats():
    body = _request_body()
    if not body:
        return ("", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    character_directory = sanitize_filename(str(body.get("avatar_url") or "").replace(".png", ""))
    chats_dir = dirs["chats"] / character_directory
    if not is_path_within(dirs["chats"], chats_dir):
        return jsonify({"error": True})
    if not chats_dir.exists():
        return jsonify({"error": True})

    jsonl_files = [f.name for f in chats_dir.glob("*.jsonl") if f.is_file()]
    if not jsonl_files:
        return jsonify([])

    if body.get("simple"):
        return jsonify([{"file_name": name, "file_id": Path(name).stem} for name in sorted(jsonl_files)])

    with_metadata = bool(body.get("metadata"))
    results = []
    for name in sorted(jsonl_files):
        info = get_chat_info(chats_dir / name, {}, with_metadata=with_metadata)
        if info.get("file_name"):
            results.append(info)
    return jsonify(results)


@characters_bp.post("/import")
@jwt_required()
def import_character():
    body = _request_body()
    avatar = uploaded_file()
    if not body or not avatar:
        return ("", 400)

    file_type = body.get("file_type")
    if file_type not in ("png", "json"):
        return jsonify({"error": True})

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    upload_bytes = avatar.read()

    try:
        if file_type == "png":
            card_json = png_utils.read_character_data(upload_bytes)
        else:
            card_json = upload_bytes.decode("utf-8")
        card = parse_json_safe(card_json)
        if not isinstance(card, dict):
            return jsonify({"error": True})
        card = _get_chara_card_v2(card, dirs)
        name = card.get("name") or "Character"
        preserved = body.get("preserved_name")
        internal_name = sanitize_filename(Path(preserved).stem if preserved else "") or _get_png_name(name, dirs)
        avatar_name = f"{internal_name}.png"
        (dirs["chats"] / internal_name).mkdir(parents=True, exist_ok=True)
        _write_card(
            dirs["characters"] / avatar_name,
            internal_name,
            json.dumps(card, ensure_ascii=False),
            upload_bytes=upload_bytes if file_type == "png" else None,
        )
        return jsonify({"file_name": avatar_name})
    except Exception:
        return jsonify({"error": True})


@characters_bp.post("/duplicate")
@jwt_required()
def duplicate_character():
    body = _request_body()
    avatar_url = body.get("avatar_url")
    if not avatar_url:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    source = dirs["characters"] / sanitize_filename(avatar_url)
    if not source.exists():
        return ("", 404)

    base = Path(avatar_url).stem
    ext = Path(avatar_url).suffix
    name_parts = base.split("_")
    if len(name_parts) > 1 and name_parts[-1].isdigit():
        suffix = int(name_parts[-1]) + 1
        base_name = "_".join(name_parts[:-1])
    else:
        suffix = 1
        base_name = base

    target = dirs["characters"] / f"{base_name}_{suffix}{ext}"
    while target.exists():
        suffix += 1
        target = dirs["characters"] / f"{base_name}_{suffix}{ext}"

    target.write_bytes(source.read_bytes())
    return jsonify({"path": target.name})


@characters_bp.post("/export")
@jwt_required()
def export_character():
    body = _request_body()
    file_format = body.get("format")
    avatar_url = body.get("avatar_url")
    if not file_format or not avatar_url:
        return ("", 400)

    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    png_path = dirs["characters"] / sanitize_filename(str(avatar_url))
    if not png_path.exists():
        return ("", 404)

    if file_format == "png":
        raw = png_path.read_bytes()
        card = parse_json_safe(png_utils.read_character_data(raw))
        _unset_private_fields(card)
        output = png_utils.write_character_data(raw, json.dumps(card, ensure_ascii=False))
        return Response(
            output,
            mimetype="image/png",
            headers={"Content-Disposition": f'attachment; filename="{png_path.name}"'},
        )

    if file_format == "json":
        try:
            card = parse_json_safe(_read_card_json(png_path))
            card = _get_chara_card_v2(card, dirs)
            _unset_private_fields(card)
            return Response(
                json.dumps(card, ensure_ascii=False, indent=4),
                mimetype="application/json",
            )
        except Exception:
            return ("", 400)

    return ("", 400)
