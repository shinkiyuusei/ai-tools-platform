from datetime import datetime

from flask import Blueprint, request, Response, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from ...core.errors import AppError, ErrorCode
from ...extensions import get_mongo_db, get_redis_client
from ...middlewares.rate_limit import daily_limit, rate_limit
from ...services.ai.deepseek import DeepSeekAdapter
from ...services.audit import audit_content
from ...services.chat.prompt_builder import parse_character_states
from ...utils.mysql import execute, query_one
from ...utils.response import success_response
from ...utils.snowflake import generate_id
import json

ai_bp = Blueprint("ai", __name__)


def _check_vip_permission(user_id: int, tool: dict):
    if tool["isFree"]:
        return
    if user_id == 0:
        raise AppError(ErrorCode.VIP_REQUIRED, "该工具需要登录后使用")

    user = query_one(
        "SELECT vip_level, free_count, status FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    if not user or user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号异常")

    vip_level = user["vip_level"]
    if vip_level == 0:
        redis_client = get_redis_client()
        today_key = f"daily_count:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
        used = int(redis_client.get(today_key) or 0)
        if used >= user["free_count"]:
            raise AppError(ErrorCode.VIP_REQUIRED, "今日免费次数已用完，请开通会员")
        redis_client.incr(today_key)
        redis_client.expire(today_key, 86400)
        return

    vip_rights = query_one(
        "SELECT all_tool, concurrency_limit FROM t_vip_rights WHERE vip_level = %s",
        (vip_level,),
    )
    if not vip_rights or not vip_rights["all_tool"]:
        raise AppError(ErrorCode.VIP_REQUIRED, "当前会员等级无法使用该工具")


@ai_bp.post("/ai/chat/completions")
def chat_completions():
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
    if conversation_id:
        conv = query_one(
            "SELECT character_state FROM t_conversation WHERE id = %s AND is_delete = 0",
            (conversation_id,),
        )
        if conv and conv.get("character_state"):
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

    service = DeepSeekAdapter()
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

    return success_response(
        {
            "content": answer,
            "model": result.get("model", model),
            "usage": result.get("usage", {}),
            "thinkingMode": thinking_mode,
        }
    )


@ai_bp.post("/ai/chat/completions/stream")
def chat_completions_stream():
    """Streaming chat completions via SSE."""
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

    # load persisted character state from conversation and inject into system prompt
    character_state = None
    if conversation_id:
        conv = query_one(
            "SELECT character_state FROM t_conversation WHERE id = %s AND is_delete = 0",
            (conversation_id,),
        )
        if conv and conv.get("character_state"):
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
        elif system_prompt and normalized_messages[0]["role"] == "system":
            # append state to existing system message
            if character_state:
                normalized_messages[0]["content"] = system_prompt

    latest_user_content = ""
    for item in reversed(normalized_messages):
        if item["role"] == "user":
            latest_user_content = item["content"]
            break
    audit_input = audit_content(latest_user_content)
    if not audit_input["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_input["message"])

    service = DeepSeekAdapter()

    # accumulator for full response to parse state bar after streaming
    full_response = []

    def generate():
        try:
            for chunk in service.chat_completion_stream(
                messages=normalized_messages,
                model=model,
                thinking_mode=thinking_mode,
                reasoning_effort=reasoning_effort,
            ):
                if not chunk:
                    continue
                full_response.append(chunk)
                escaped = "\ndata: ".join(chunk.split("\n"))
                yield f"data: {escaped}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
            return

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

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@ai_bp.post("/ai/generate/<int:tool_id>")
@rate_limit(max_requests=3, window_seconds=1)
def generate(tool_id: int):
    payload = request.get_json(silent=True) or {}
    thinking_mode = bool(payload.pop("thinkingMode", False))
    async_mode = bool(payload.pop("asyncMode", False))

    user_id = 0
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
    except Exception:
        user_id = 0

    tool = query_one(
        "SELECT id, name, is_free AS isFree, is_vip AS isVip FROM t_ai_tool WHERE id = %s AND status = 1",
        (tool_id,),
    )
    if not tool:
        raise AppError(ErrorCode.SYSTEM_ERROR, "工具不存在或已下架")

    _check_vip_permission(user_id, tool)

    generate_params = {k: v for k, v in payload.items() if k not in ("thinkingMode", "asyncMode")}
    if not generate_params:
        raise AppError(ErrorCode.PARAM_INVALID, "生成参数不能为空")

    prompt_text = generate_params.get("topic") or generate_params.get("prompt") or str(generate_params)
    audit_res = audit_content(prompt_text)
    if not audit_res["passed"]:
        raise AppError(ErrorCode.PARAM_INVALID, audit_res["message"])

    service = DeepSeekAdapter()
    if async_mode:
        result = service.submit_async_task(tool_id, user_id, generate_params, tool["name"], thinking_mode=thinking_mode)
        result["status"] = 0
        result["message"] = "任务已提交，后续可通过 taskId 轮询或接 WebSocket 推送"
        return success_response(result)

    prompt = generate_params.get("topic") or generate_params.get("prompt") or str(generate_params)
    ai_result = service.generate_text(prompt, thinking_mode=thinking_mode)

    output_audit = audit_content(ai_result)
    if not output_audit["passed"]:
        ai_result = "[内容审核未通过，结果已拦截]"

    record_id = f"record_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{user_id}"
    mongo_db = get_mongo_db()
    mongo_db["t_generate_record"].insert_one(
        {
            "recordId": record_id,
            "userId": user_id,
            "toolId": tool_id,
            "toolName": tool["name"],
            "params": generate_params,
            "result": ai_result,
            "status": 1,
            "createTime": datetime.utcnow(),
            "isCollected": 0,
        }
    )

    audit_id = generate_id()
    execute(
        "INSERT INTO t_audit_record (id, record_id, user_id, content, audit_type, audit_result, create_time) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (
            audit_id,
            record_id,
            user_id,
            ai_result[:500] if ai_result else "",
            1,
            1 if output_audit["passed"] else 2,
            datetime.utcnow(),
        ),
    )

    execute("UPDATE t_ai_tool SET use_count = use_count + 1 WHERE id = %s", (tool_id,))

    return success_response({"result": ai_result, "recordId": record_id})


@ai_bp.get("/ai/generate/task/<string:task_id>")
@jwt_required(optional=True)
def generate_task_status(task_id: str):
    data = get_redis_client().get(f"ai_task:{task_id}")
    if not data:
        raise AppError(ErrorCode.GENERATE_TASK_NOT_FOUND, "异步任务不存在")
    return success_response({"status": 0, "result": None, "taskMeta": data})
