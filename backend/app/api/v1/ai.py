from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...services.ai.adapters import get_adapter, get_default_provider
from ...services.audit import audit_content
from ...services.chat.prompt_builder import _fmt_lore_entries
from ...services.chat.runtime import (
    append_state_block,
    build_sse_response,
    inject_scene_context,
    latest_user_content,
    load_conversation_state,
    normalize_messages,
    persist_character_state,
    sse_data,
    split_usage_signal,
)
from ...services.credit import deduct_for_tokens, ensure_positive_balance
from ...services.usage import add_token_usage, increment_daily_stat
from ...services.world_info import get_active_lore
from ...utils.response import success_response

ai_bp = Blueprint("ai", __name__)


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

    normalized_messages = normalize_messages(messages)
    inject_scene_context(normalized_messages, scene_context)

    entity_id, entity_type, character_state = load_conversation_state(conversation_id)

    if system_prompt:
        system_prompt = append_state_block(system_prompt, character_state)
        if normalized_messages[0]["role"] != "system":
            normalized_messages.insert(0, {"role": "system", "content": system_prompt})

    latest_content = latest_user_content(normalized_messages)
    audit_input = audit_content(latest_content)
    if not audit_input["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_input["message"])

    provider = payload.get("aiProvider") or get_default_provider()
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

    persist_character_state(conversation_id, character_state, answer)

    total_tokens = result.get("usage", {}).get("total_tokens", 0)
    add_token_usage(entity_id, total_tokens, entity_type)
    increment_daily_stat(entity_type, entity_id)
    deduct_for_tokens(user_id, total_tokens, conversation_id=conversation_id)

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

    normalized_messages = normalize_messages(messages)
    inject_scene_context(normalized_messages, scene_context)

    latest_content = latest_user_content(normalized_messages)
    entity_id, entity_type, character_state = load_conversation_state(conversation_id)

    if system_prompt:
        system_prompt = append_state_block(system_prompt, character_state)

        # --- World Info lore injection (runtime, per-request) ---
        if entity_type == "work" and entity_id and latest_content:
            try:
                lore = get_active_lore("work", entity_id, latest_content)
                lore_block = _fmt_lore_entries(lore.get("always", []))
                if lore_block:
                    system_prompt += "\n" + lore_block
            except Exception:
                pass  # lore injection is best-effort, never break the stream

        if normalized_messages[0]["role"] != "system":
            normalized_messages.insert(0, {"role": "system", "content": system_prompt})
        elif character_state:
            # append state to existing system message
            normalized_messages[0]["content"] = system_prompt

    audit_input = audit_content(latest_content)
    if not audit_input["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_input["message"])

    provider = payload.get("aiProvider") or get_default_provider()
    service = get_adapter(provider)
    ensure_positive_balance(user_id)

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
                tokens = split_usage_signal(chunk)
                if tokens is not None:
                    stream_tokens = tokens
                    continue
                full_response.append(chunk)
                yield sse_data(chunk)
        except Exception as e:
            yield sse_data(f"[ERROR] {str(e)}")
            return

        # Accumulate token usage to the work/character card
        if stream_tokens:
            add_token_usage(entity_id, stream_tokens, entity_type)
            increment_daily_stat(entity_type, entity_id)
            try:
                deduct_for_tokens(user_id, stream_tokens, conversation_id=conversation_id)
            except AppError:
                pass  # deduction failure must not break the stream

        persist_character_state(conversation_id, character_state, "".join(full_response))

        # Guard: if AI omitted the required markers, inject fallback
        full_text = "".join(full_response)
        if "【角色状态栏】" not in full_text:
            guard = "\n\n【角色状态栏】\n服装：—\n表情：—\n想法：—\n"
            full_response.append(guard)
            yield sse_data(guard)
        if "【抉择分支】" not in full_text:
            guard = "\n\n【抉择分支】\nA. 继续当前行动\nB. 换个方式\nC. 观察周围\nD. 打破常规，做出一个出人意料的举动\n"
            full_response.append(guard)
            yield sse_data(guard)

        yield "data: [DONE]\n\n"

    return build_sse_response(generate())
