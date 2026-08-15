"""Shared runtime helpers for chat endpoints (ai.py / character.py).

Consolidates the message normalization, scene/state injection, SSE framing and
character-state persistence that were previously duplicated across endpoints.
"""

import json

from flask import Response, stream_with_context

from ...core.errors import AppError, ErrorCode
from ...services.ai.adapters import TOKEN_USAGE_SIGNAL
from ...utils.mysql import execute, query_one
from .prompt_builder import _fmt_character_states, parse_character_states


def normalize_messages(messages) -> list[dict]:
    """Validate and normalize the client message list. Raises AppError on failure."""
    if not isinstance(messages, list) or not messages:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 不能为空")

    normalized = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = (message.get("role") or "").strip()
        content = str(message.get("content") or "").strip()
        if role not in ("system", "user", "assistant") or not content:
            continue
        normalized.append({"role": role, "content": content})

    if not normalized:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 格式不合法")
    return normalized


def inject_scene_context(messages: list[dict], scene_context: dict) -> list[dict]:
    """Prefix the latest user message with the current scene context (in place)."""
    if not scene_context or not messages:
        return messages

    scene_prefix = ""
    if scene_context.get("worldName"):
        scene_prefix += f"【当前世界：{scene_context['worldName']}】"
    if scene_context.get("time"):
        scene_prefix += f"【当前时间：{scene_context['time']}】"
    if scene_context.get("location"):
        scene_prefix += f"【当前位置：{scene_context['location']}】"
    if scene_context.get("scene"):
        scene_prefix += f"【上一幕：{scene_context['scene']}】"

    if scene_prefix:
        scene_prefix += "\n"
        for i in range(len(messages) - 1, -1, -1):
            if messages[i]["role"] == "user":
                messages[i]["content"] = scene_prefix + messages[i]["content"]
                break
    return messages


def load_conversation_state(conversation_id, user_id: int = 0) -> tuple:
    """Return (entity_id, entity_type, character_state) for an owned conversation.

    Raises FORBIDDEN when a conversation id is supplied but does not belong to
    the current user, so chat endpoints cannot attach state/usage to a
    conversation they do not own.
    """
    if not conversation_id:
        return 0, "work", None

    conv = query_one(
        "SELECT entity_id, entity_type, character_state FROM t_conversation "
        "WHERE id = %s AND user_id = %s AND is_delete = 0",
        (conversation_id, user_id),
    )
    if not conv:
        raise AppError(ErrorCode.FORBIDDEN, "对话不存在或无权访问")

    character_state = None
    if conv.get("character_state"):
        try:
            raw = conv["character_state"]
            character_state = json.loads(raw) if isinstance(raw, str) else raw
        except (json.JSONDecodeError, TypeError):
            character_state = None
    return conv.get("entity_id", 0), conv.get("entity_type", "work"), character_state


def latest_user_content(messages: list[dict]) -> str:
    """Return the content of the most recent user message."""
    for item in reversed(messages):
        if item["role"] == "user":
            return item["content"]
    return ""


def append_state_block(system_prompt: str, character_state: dict | None) -> str:
    """Append persisted character states to the system prompt (private keys excluded)."""
    if not character_state:
        return system_prompt
    visible = {k: v for k, v in character_state.items() if not k.startswith("_")}
    block = _fmt_character_states(visible)
    if block:
        return system_prompt + "\n\n" + block
    return system_prompt


def persist_character_state(conversation_id, character_state, full_text: str) -> None:
    """Parse + merge + persist character states from a completed response.

    Best-effort: failures never break the request/stream.
    """
    if not conversation_id or not full_text:
        return
    try:
        new_state = parse_character_states(full_text)
        if not new_state:
            return
        merged = dict(character_state) if character_state else {}
        for key, val in new_state.items():
            if key.startswith("_"):
                merged[key] = val
            elif val is not None:
                merged[key] = val
        execute(
            "UPDATE t_conversation SET character_state = %s WHERE id = %s",
            (json.dumps(merged, ensure_ascii=False), conversation_id),
        )
    except Exception:
        pass  # state persistence is best-effort


def split_usage_signal(chunk: str) -> int | None:
    """Return the token count when *chunk* is the usage sentinel, else None."""
    if TOKEN_USAGE_SIGNAL not in chunk:
        return None
    try:
        return int(chunk.split(TOKEN_USAGE_SIGNAL)[1].rstrip("\0"))
    except (ValueError, IndexError):
        return 0


def sse_data(chunk: str) -> str:
    """Frame a text chunk as an SSE data event (newlines escaped)."""
    escaped = "\ndata: ".join(chunk.split("\n"))
    return f"data: {escaped}\n\n"


def build_sse_response(generator):
    """Wrap a chunk generator in a standard SSE streaming response."""
    return Response(
        stream_with_context(generator),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
