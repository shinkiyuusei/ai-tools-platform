"""Shared file-system helpers for the SillyTavern-compatible API."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from flask import current_app, request
from flask_jwt_extended import get_jwt_identity

# Sentinel used by /api/characters/merge-attributes to delete a key.
UNSET_SENTINEL = "__@@UNSET@@__"

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

USER_DIRECTORIES = {
    "root": "",
    "characters": "characters",
    "chats": "chats",
    "group_chats": "group chats",
    "groups": "groups",
    "worlds": "worlds",
    "themes": "themes",
    "moving_ui": "movingUI",
    "quick_replies": "QuickReplies",
    "openai_settings": "OpenAI Settings",
    "textgen_settings": "TextGen Settings",
    "novelai_settings": "NovelAI Settings",
    "koboldai_settings": "KoboldAI Settings",
    "instruct": "instruct",
    "context": "context",
    "sysprompt": "sysprompt",
    "reasoning": "reasoning",
    "backups": "backups",
}


def get_jwt_user_id() -> str:
    """Return the current JWT identity normalized to a string."""
    return str(get_jwt_identity())


def st_data_root() -> Path:
    """Return the root directory for all SillyTavern-compatible data."""
    configured = current_app.config.get("ST_COMPAT_DATA_DIR")
    if configured:
        return Path(configured)
    return Path(current_app.root_path).parent / "data" / "st_compat"


def user_root(user_id: str) -> Path:
    return st_data_root() / user_id


def get_user_dirs(user_id: str, ensure: bool = True) -> dict:
    """Return the per-user directory map (mirrors USER_DIRECTORY_TEMPLATE)."""
    base = user_root(user_id)
    dirs = {name: base / rel for name, rel in USER_DIRECTORIES.items() if rel}
    dirs["root"] = base
    if ensure:
        for directory in dirs.values():
            directory.mkdir(parents=True, exist_ok=True)
    return dirs


def sanitize_filename(name: str) -> str:
    """Sanitize a user supplied filename the same way SillyTavern does."""
    if not isinstance(name, str):
        return ""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name)
    cleaned = cleaned.strip().strip(".")
    return cleaned


def is_path_within(parent: Path, child: Path) -> bool:
    """Return True when child resolves inside parent (path traversal guard)."""
    try:
        resolved_parent = parent.resolve()
        resolved_child = child.resolve()
        return resolved_child == resolved_parent or resolved_parent in resolved_child.parents
    except OSError:
        return False


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    os.replace(temp, path)


def atomic_write_text(path: Path, text: str) -> None:
    atomic_write_bytes(path, text.encode("utf-8"))


def parse_json_safe(text, default=None):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def read_json_file(path: Path, default=None):
    if not path.exists():
        return default
    return parse_json_safe(path.read_text(encoding="utf-8"), default)


def write_json_file(path: Path, data, pretty: bool = True) -> None:
    text = json.dumps(data, ensure_ascii=False, indent=4 if pretty else None)
    atomic_write_text(path, text)


def read_jsonl_file(path: Path):
    """Read a SillyTavern .jsonl chat file into a list of message objects."""
    if not path.exists():
        return []
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = parse_json_safe(line)
        if item is not None:
            items.append(item)
    return items


def write_jsonl_file(path: Path, items) -> None:
    text = "\n".join(json.dumps(item, ensure_ascii=False) for item in items)
    atomic_write_text(path, text)


def now_millis() -> int:
    return int(time.time() * 1000)


def uuid4_str() -> str:
    return str(uuid.uuid4())


def humanized_datetime(timestamp: int | None = None) -> str:
    """Format like SillyTavern: 2026-08-15@14h30m00s000ms."""
    date = datetime.fromtimestamp((timestamp or now_millis()) / 1000)
    return (
        f"{date.year:04d}-{date.month:02d}-{date.day:02d}@"
        f"{date.hour:02d}h{date.minute:02d}m{date.second:02d}s{date.microsecond // 1000:03d}ms"
    )


def format_bytes(num_bytes: int) -> str:
    """Human readable byte size (npm bytes compatible enough for clients)."""
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def get_unique_name(base_name: str, exists, start_index: int = 1, max_tries: int = 10000) -> str | None:
    """Find a unique name; index 0 means the plain base name is checked first."""
    index = start_index
    while index < max_tries + start_index:
        candidate = base_name if index == 0 else f"{base_name}{index}"
        if not exists(candidate):
            return candidate
        index += 1
    return None


def get_dict_path(data: dict, path: str, default=None):
    current = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def deep_merge(base: dict, update: dict) -> dict:
    """Recursively merge update into a copy of base; UNSET_SENTINEL deletes keys."""
    result = deepcopy(base)
    for key, value in update.items():
        if key == "json_data":
            continue
        if value is UNSET_SENTINEL:
            result.pop(key, None)
        elif isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_preview_message(last_message: str) -> str:
    if not last_message:
        return ""
    if len(last_message) > 400:
        return "..." + last_message[-400:]
    return last_message


def calculate_chat_size(chat_dir: Path):
    """Return (total_size, last_mtime_ms) for all chat files in a directory."""
    if not chat_dir.exists():
        return 0, 0
    total_size = 0
    last_mtime = 0
    for child in chat_dir.iterdir():
        if child.is_file() and child.suffix.lower() == ".jsonl":
            stat = child.stat()
            total_size += stat.st_size
            last_mtime = max(last_mtime, int(stat.st_mtime * 1000))
    return total_size, last_mtime


def get_chat_info(path: Path, additional_data: dict | None = None, with_metadata: bool = False, matcher=None):
    """Build the SillyTavern ChatInfo object for a chat file."""
    stat = path.stat()
    info = {
        "match": False,
        "file_id": path.stem,
        "file_name": path.name,
        "file_size": format_bytes(stat.st_size),
        "chat_items": 0,
        "mes": "[The chat is empty]",
        "last_mes": int(stat.st_mtime * 1000),
    }
    if additional_data:
        info.update(additional_data)

    if stat.st_size == 0:
        return info

    lines = read_jsonl_file(path)
    if not lines:
        return {}

    if with_metadata and isinstance(lines[0].get("chat_metadata"), dict):
        info["chat_metadata"] = lines[0]["chat_metadata"]

    last = lines[-1]
    if not isinstance(last, dict) or not (
        last.get("name") or last.get("character_name") or last.get("chat_metadata")
    ):
        return {}

    info["chat_items"] = max(0, len(lines) - 1)
    info["mes"] = last.get("mes") or "[The message is empty]"
    info["last_mes"] = last.get("send_date") or datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
    info["match"] = bool(matcher(lines[1:])) if matcher else True
    return info


def uploaded_file():
    return request.files.get("avatar")
