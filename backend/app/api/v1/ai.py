import json
import math

from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...services.ai.adapters import get_adapter, TOKEN_USAGE_SIGNAL
from ...services.audit import audit_content
from ...services.chat.prompt_builder import parse_character_states, _fmt_lore_entries
from ...services.world_info import get_active_lore
from ...services.credit import deduct, get_balance
from datetime import date

from ...utils.mysql import execute, query_one
from ...utils.response import success_response

ai_bp = Blueprint("ai", __name__)


def _add_token_usage(entity_id: int, tokens: int, entity_type: str = "work"):
    if not entity_id or not tokens:
        return
    table = "t_work_card" if entity_type == "work" else "t_character_card"
    execute(
        f"UPDATE {table} SET use_count = use_count + %s WHERE id = %s",
        (tokens, entity_id),
    )


def _increment_daily_stat(card_type, card_id):
    if not card_id:
        return
    today = date.today().isoformat()
    execute(
        "INSERT INTO t_cards_daily_stat (card_type, card_id, stat_date, chat_count) "
        "VALUES (%s, %s, %s, 1) "
        "ON DUPLICATE KEY UPDATE chat_count = chat_count + 1",
        (card_type, card_id, today),
    )


def _check_and_deduct_credits(user_id: int, tokens: int, **kwargs):
    """Deduct credits from user based on token consumption (100 tokens = 1 credit, ceil).

    Uses Redis atomic DECRBY as the primary data source.
    Returns the deducted amount.
    """
    if not tokens:
        return 0
    deduction = math.ceil(tokens / 100)
    balance = get_balance(user_id)
    if balance < 0:
        raise AppError(ErrorCode.FORBIDDEN, "积分已透支，无法继续对话，请联系管理员充值")
    deduct(
        user_id,
        deduction,
        tokens_used=tokens,
        **kwargs,
    )
    return deduction


def _ensure_credits(user_id: int):
    """Raise AppError if user has negative balance."""
    balance = get_balance(user_id)
    if balance < 0:
        raise AppError(ErrorCode.FORBIDDEN, "积分已透支，无法继续对话，请联系管理员充值")


@ai_bp.post("/ai/chat/completions")
@jwt_required()
def chat_completions():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    model = payload.get("model") or ""
    system_prompt = payload.get("systemPrompt", "").strip()
    thinking_mode = bool(payload.get("thinkingMode", False))
    reasoning_effort = payload.get("reasoningEffort", "medium")
    scene_context = payload.get("sceneContext") or {}
    conversation_id = payload.get("conversationId") or 0

    if not isinstance(messages, list) or not messages:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 不能为空")

    normalized_messages = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = (message.get("role") or "").strip()
        content = str(message.get("content") or "").strip()
        if role not in ("system", "user", "assistant") or not content:
            continue
        normalized_messages.append({"role": role, "content": content})

    if not normalized_messages:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 格式不合法")

    # inject scene context into the latest user message for continuity
    if scene_context and normalized_messages:
        location = scene_context.get("location", "")
        time_info = scene_context.get("time", "")
        scene_title = scene_context.get("scene", "")
        world_name = scene_context.get("worldName", "")
        scene_prefix = ""
        if world_name:
            scene_prefix += f"【当前世界：{world_name}】"
        if time_info:
            scene_prefix += f"【当前时间：{time_info}】"
        if location:
            scene_prefix += f"【当前位置：{location}】"
        if scene_title:
            scene_prefix += f"【上一幕：{scene_title}】"
        if scene_prefix:
            scene_prefix += "\n"
            for i in range(len(normalized_messages) - 1, -1, -1):
                if normalized_messages[i]["role"] == "user":
                    normalized_messages[i]["content"] = scene_prefix + normalized_messages[i]["content"]
                    break

    # load persisted character state and inject into system prompt
    character_state = None
    entity_id = 0
    entity_type = "work"
    if conversation_id:
        conv = query_one(
            "SELECT entity_id, entity_type, character_state FROM t_conversation WHERE id = %s AND is_delete = 0",
            (conversation_id,),
        )
        if conv:
            entity_id = conv.get("entity_id", 0)
            entity_type = conv.get("entity_type", "work")
            if conv.get("character_state"):
                try:
                    character_state = json.loads(conv["character_state"]) if isinstance(conv["character_state"], str) else conv["character_state"]
                except (json.JSONDecodeError, TypeError):
                    character_state = None

    if system_prompt:
        if character_state:
            state_lines = ["\n# 当前角色状态（系统维护，每轮自动更新）"]
            for name, attrs in character_state.items():
                if not attrs or name.startswith("_"):
                    continue
                parts = [f"{name}"]
                for key, val in attrs.items():
                    parts.append(f"{key} {val}")
                state_lines.append(" · ".join(parts))
            system_prompt += "\n" + "\n".join(state_lines)
        if normalized_messages[0]["role"] != "system":
            normalized_messages.insert(0, {"role": "system", "content": system_prompt})

    latest_user_content = ""
    for item in reversed(normalized_messages):
        if item["role"] == "user":
            latest_user_content = item["content"]
            break
    audit_input = audit_content(latest_user_content)
    if not audit_input["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_input["message"])

    provider = payload.get("aiProvider") or "deepseek"
    service = get_adapter(provider)
    result = service.chat_completion(
        messages=normalized_messages,
        model=model,
        thinking_mode=thinking_mode,
        reasoning_effort=reasoning_effort,
    )
    answer = result["choices"][0]["message"]["content"]
    audit_output = audit_content(answer)
    if not audit_output["passed"]:
        answer = "[内容审核未通过，结果已拦截]"

    # parse and persist character state from response
    if conversation_id and answer:
        try:
            new_state = parse_character_states(answer)
            if new_state:
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
            pass

    total_tokens = result.get("usage", {}).get("total_tokens", 0)
    _add_token_usage(entity_id, total_tokens, entity_type)
    _increment_daily_stat(entity_type, entity_id)
    _check_and_deduct_credits(user_id, total_tokens, conversation_id=conversation_id)

    return success_response(
        {
            "content": answer,
            "model": result.get("model", model),
            "usage": result.get("usage", {}),
            "thinkingMode": thinking_mode,
        }
    )


@ai_bp.post("/ai/chat/completions/stream")
@jwt_required()
def chat_completions_stream():
    """Streaming chat completions via SSE."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    model = payload.get("model") or ""
    system_prompt = payload.get("systemPrompt", "").strip()
    thinking_mode = bool(payload.get("thinkingMode", False))
    reasoning_effort = payload.get("reasoningEffort", "medium")
    scene_context = payload.get("sceneContext") or {}
    conversation_id = payload.get("conversationId") or 0

    if not isinstance(messages, list) or not messages:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 不能为空")

    normalized_messages = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = (message.get("role") or "").strip()
        content = str(message.get("content") or "").strip()
        if role not in ("system", "user", "assistant") or not content:
            continue
        normalized_messages.append({"role": role, "content": content})

    if not normalized_messages:
        raise AppError(ErrorCode.PARAM_INVALID, "messages 不能为空")

    # inject scene context into the latest user message for continuity
    if scene_context and normalized_messages:
        location = scene_context.get("location", "")
        time_info = scene_context.get("time", "")
        scene_title = scene_context.get("scene", "")
        world_name = scene_context.get("worldName", "")
        prev_choices = scene_context.get("lastChoices", "")

        scene_prefix = ""
        if world_name:
            scene_prefix += f"【当前世界：{world_name}】"
        if time_info:
            scene_prefix += f"【当前时间：{time_info}】"
        if location:
            scene_prefix += f"【当前位置：{location}】"
        if scene_title:
            scene_prefix += f"【上一幕：{scene_title}】"

        if scene_prefix:
            scene_prefix += "\n"
            for i in range(len(normalized_messages) - 1, -1, -1):
                if normalized_messages[i]["role"] == "user":
                    normalized_messages[i]["content"] = scene_prefix + normalized_messages[i]["content"]
                    break

    # extract latest user message early (needed for content audit + lore matching)
    latest_user_content = ""
    for item in reversed(normalized_messages):
        if item["role"] == "user":
            latest_user_content = item["content"]
            break

    # load persisted character state from conversation and inject into system prompt
    character_state = None
    entity_id = 0
    entity_type = "work"
    if conversation_id:
        conv = query_one(
            "SELECT entity_id, entity_type, character_state FROM t_conversation WHERE id = %s AND is_delete = 0",
            (conversation_id,),
        )
        if conv:
            entity_id = conv.get("entity_id", 0)
            entity_type = conv.get("entity_type", "work")
            if conv.get("character_state"):
                try:
                    character_state = json.loads(conv["character_state"]) if isinstance(conv["character_state"], str) else conv["character_state"]
                except (json.JSONDecodeError, TypeError):
                    character_state = None

    if system_prompt:
        if character_state:
            state_lines = ["\n# 当前角色状态（系统维护，每轮自动更新）"]
            for name, attrs in character_state.items():
                if not attrs or name.startswith("_"):
                    continue
                parts = [f"{name}"]
                for key, val in attrs.items():
                    parts.append(f"{key} {val}")
                state_lines.append(" · ".join(parts))
            system_prompt += "\n" + "\n".join(state_lines)

        # --- World Info lore injection (runtime, per-request) ---
        if entity_type == "work" and entity_id and latest_user_content:
            try:
                lore = get_active_lore("work", entity_id, latest_user_content)
                lore_block = _fmt_lore_entries(lore.get("always", []))
                if lore_block:
                    system_prompt += "\n" + lore_block
            except Exception:
                pass  # lore injection is best-effort, never break the stream

        if normalized_messages[0]["role"] != "system":
            normalized_messages.insert(0, {"role": "system", "content": system_prompt})
        elif system_prompt and normalized_messages[0]["role"] == "system":
            # append state to existing system message
            if character_state:
                normalized_messages[0]["content"] = system_prompt

    audit_input = audit_content(latest_user_content)
    if not audit_input["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_input["message"])

    provider = payload.get("aiProvider") or "deepseek"
    service = get_adapter(provider)

    _ensure_credits(user_id)

    # accumulator for full response to parse state bar after streaming
    full_response = []

    def generate():
        stream_tokens = 0
        try:
            for chunk in service.chat_completion_stream(
                messages=normalized_messages,
                model=model,
                thinking_mode=thinking_mode,
                reasoning_effort=reasoning_effort,
            ):
                if not chunk:
                    continue
                # Check for token usage signal embedded at end of stream
                if TOKEN_USAGE_SIGNAL in chunk:
                    try:
                        stream_tokens = int(chunk.split(TOKEN_USAGE_SIGNAL)[1].rstrip("\0"))
                    except (ValueError, IndexError):
                        pass
                    continue
                full_response.append(chunk)
                escaped = "\ndata: ".join(chunk.split("\n"))
                yield f"data: {escaped}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            return

        # Accumulate token usage to the work/character card
        if stream_tokens:
            _add_token_usage(entity_id, stream_tokens, entity_type)
            _increment_daily_stat(entity_type, entity_id)
            try:
                _check_and_deduct_credits(user_id, stream_tokens, conversation_id=conversation_id)
            except AppError:
                pass  # deduction failure must not break the stream

        # parse and persist character state from the full response
        if conversation_id and full_response:
            try:
                new_state = parse_character_states("".join(full_response))
                if new_state:
                    # merge with existing state: add change values to existing
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
                pass  # state persistence is best-effort, don't break the stream

        # Guard: if AI omitted the required markers, inject fallback
        full_text = "".join(full_response)
        if "【角色状态栏】" not in full_text:
            guard = "\n\n【角色状态栏】\n服装：—\n表情：—\n想法：—\n"
            full_response.append(guard)
            yield f"data: {guard}\n\n"
        if "【抉择分支】" not in full_text:
            guard = "\n\n【抉择分支】\nA. 继续当前行动\nB. 换个方式\nC. 观察周围\nD. 自由行动 —— 输入你想做的任何事。\n"
            full_response.append(guard)
            for chunk in [guard]:
                escaped = "\ndata: ".join(chunk.split("\n"))
                yield f"data: {escaped}\n\n"

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
