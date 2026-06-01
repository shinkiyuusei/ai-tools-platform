"""
Character card API endpoints
"""
import json
import math
import os
import uuid
from flask import Blueprint, request, current_app, Response, stream_with_context
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ...utils.crud import dynamic_update
from ...utils.mysql import query_one, query_all, execute
from ...utils.response import success_response, page_response
from ...core.errors import AppError, ErrorCode
from ...api.v1.ai import _increment_daily_stat
from ...services.ai.deepseek import DeepSeekAdapter, TOKEN_USAGE_SIGNAL
from ...services.audit import audit_content
from ...services.cache import (
    get_cached_character, set_cached_character, invalidate_character,
    cache_get, cache_set, LIST_TTL,
)
from ...services.chat.character_prompt_builder import build_character_system_prompt
from ...services.credit import deduct, get_balance

character_bp = Blueprint("character", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024

_CHAR_SELECT = (
    "id, user_id, name, `desc`, avatar, author, language, category, tags, "
    "persona_content, is_public, like_count, view_count, collect_count, "
    "use_count, create_time"
)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _parse_tags(tags):
    if not tags:
        return []
    try:
        return json.loads(tags) if isinstance(tags, str) else tags
    except (json.JSONDecodeError, TypeError):
        return []


@character_bp.post("/character/upload")
@jwt_required()
def upload_avatar():
    if 'file' not in request.files:
        raise AppError(ErrorCode.PARAM_INVALID, "No file provided")

    file = request.files['file']
    if file.filename == '':
        raise AppError(ErrorCode.PARAM_INVALID, "No file selected")

    if not allowed_file(file.filename):
        raise AppError(ErrorCode.PARAM_INVALID, "File type not allowed")

    if file.content_length > MAX_FILE_SIZE:
        raise AppError(ErrorCode.PARAM_INVALID, "File too large (max 5MB)")

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"

    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'characters')
    os.makedirs(upload_dir, exist_ok=True)

    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    url = f"/uploads/characters/{filename}"
    return success_response({"url": url})


@character_bp.get("/character/list")
def get_character_list():
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    user_id = request.args.get("userId", type=int)
    sort_type = request.args.get("sortType", "new")
    rank_type = request.args.get("rankType", "total")
    keyword = request.args.get("keyword", "")
    category = request.args.get("category", type=int)

    where = ["c.status = 1", "c.is_public = 1"]
    params = []

    if user_id:
        where.append("c.user_id = %s")
        params.append(user_id)

    if keyword:
        where.append("(c.name LIKE %s OR c.`desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if category:
        where.append("c.category = %s")
        params.append(category)

    where_clause = " AND ".join(where)

    _RANK_DATE = {
        "daily": "c.id = s.card_id AND s.card_type = 'character' AND s.stat_date = CURDATE()",
        "weekly": "c.id = s.card_id AND s.card_type = 'character' AND s.stat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
        "monthly": "c.id = s.card_id AND s.card_type = 'character' AND s.stat_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)",
    }

    if rank_type in _RANK_DATE:
        join_clause = f"INNER JOIN t_cards_daily_stat s ON {_RANK_DATE[rank_type]}"
        count_sql = (
            f"SELECT COUNT(*) AS total FROM ("
            f"SELECT c.id FROM t_character_card c {join_clause} "
            f"WHERE {where_clause} GROUP BY c.id"
            f") sub"
        )
        select_prefix = (
            f"SELECT c.id, c.user_id, c.name, c.`desc`, c.avatar, c.author, "
            f"c.language, c.category, c.tags, c.persona_content, c.is_public, "
            f"c.like_count, c.view_count, c.collect_count, c.use_count, c.create_time, "
            f"COALESCE(SUM(s.chat_count), 0) AS rank_score "
            f"FROM t_character_card c {join_clause} "
        )
        data_sql = (
            f"{select_prefix} WHERE {where_clause} GROUP BY c.id "
            f"ORDER BY rank_score DESC, c.id DESC LIMIT %s OFFSET %s"
        )
    else:
        count_sql = f"SELECT COUNT(*) AS total FROM t_character_card c WHERE {where_clause}"
        order_map = {"new": "create_time DESC", "hot": "use_count DESC", "like": "like_count DESC"}
        order_clause = order_map.get(sort_type, "create_time DESC")
        select_prefix = f"SELECT {_CHAR_SELECT} FROM t_character_card c "
        data_sql = (
            f"{select_prefix} WHERE {where_clause} ORDER BY {order_clause} LIMIT %s OFFSET %s"
        )

    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]

    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))

    result = [{
        "id": item["id"],
        "userId": item["user_id"],
        "name": item["name"],
        "desc": item.get("desc", ""),
        "avatar": item.get("avatar", ""),
        "author": item.get("author", ""),
        "language": item.get("language", "zh-Hans"),
        "category": item.get("category", 0),
        "tags": _parse_tags(item.get("tags")),
        "isPublic": item.get("is_public", 1),
        "likeCount": item.get("like_count", 0),
        "viewCount": item.get("view_count", 0),
        "collectCount": item.get("collect_count", 0),
        "useCount": item.get("use_count", 0),
        "createTime": str(item.get("create_time", "")),
    } for item in items]

    return page_response(result, total=total, page_num=page_num, page_size=page_size)


@character_bp.get("/character/<int:character_id>")
def get_character_detail(character_id: int):
    cached = get_cached_character(character_id)
    if cached:
        return success_response(cached)

    character = query_one(
        f"SELECT {_CHAR_SELECT} FROM t_character_card "
        f"WHERE id = %s AND status = 1",
        (character_id,)
    )

    if not character:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "Character not found")

    execute("UPDATE t_character_card SET view_count = view_count + 1 WHERE id = %s", (character_id,))

    data = {
        "id": character["id"],
        "userId": character["user_id"],
        "name": character["name"],
        "desc": character.get("desc", ""),
        "avatar": character.get("avatar", ""),
        "author": character.get("author", ""),
        "language": character.get("language", "zh-Hans"),
        "category": character.get("category", 0),
        "tags": _parse_tags(character.get("tags")),
        "personaContent": character.get("persona_content", ""),
        "isPublic": character.get("is_public", 1),
        "likeCount": character.get("like_count", 0),
        "viewCount": (character.get("view_count") or 0) + 1,
        "collectCount": character.get("collect_count", 0),
        "useCount": character.get("use_count", 0),
        "createTime": str(character.get("create_time", "")),
    }
    set_cached_character(character_id, data)
    return success_response(data)


@character_bp.post("/character")
@jwt_required()
def create_character():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    name = payload.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "name is required")

    character_id = execute(
        "INSERT INTO t_character_card "
        "(user_id, name, `desc`, avatar, author, language, category, tags, "
        "persona_content, is_public) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            user_id, name,
            payload.get("desc", "").strip(),
            payload.get("avatar", "").strip(),
            payload.get("author", "").strip(),
            payload.get("language", "zh-Hans").strip(),
            payload.get("category", 0),
            json.dumps(payload.get("tags", []), ensure_ascii=False),
            payload.get("personaContent", "").strip(),
            payload.get("isPublic", 1),
        ),
    )

    invalidate_character(0)
    return success_response({"id": character_id, "message": "创建成功"})


@character_bp.put("/character/<int:character_id>")
@jwt_required()
def update_character(character_id: int):
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    character = query_one(
        "SELECT user_id FROM t_character_card WHERE id = %s",
        (character_id,)
    )
    if not character:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "Character not found")
    if character["user_id"] != user_id:
        raise AppError(ErrorCode.FORBIDDEN, "Permission denied")

    updates = {}
    values = []
    for col, key in [("name", "name"), ("desc", "desc"), ("avatar", "avatar"),
                     ("author", "author"), ("language", "language"),
                     ("category", "category"), ("persona_content", "personaContent"),
                     ("is_public", "isPublic")]:
        if key in payload:
            updates[col] = "%s"
            values.append(payload[key])

    if "tags" in payload:
        updates["tags"] = "%s"
        values.append(json.dumps(payload["tags"], ensure_ascii=False))

    if not updates:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    set_clause = ", ".join(f"`{k}` = %s" for k in updates)
    values.append(character_id)
    execute(f"UPDATE t_character_card SET {set_clause} WHERE id = %s", tuple(values))
    invalidate_character(character_id)
    return success_response({"message": "更新成功"})


@character_bp.delete("/character/<int:character_id>")
@jwt_required()
def delete_character(character_id: int):
    user_id = int(get_jwt_identity())

    character = query_one(
        "SELECT user_id FROM t_character_card WHERE id = %s",
        (character_id,)
    )
    if not character:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "Character not found")
    if character["user_id"] != user_id:
        raise AppError(ErrorCode.FORBIDDEN, "Permission denied")

    execute("DELETE FROM t_character_collect WHERE character_id = %s", (character_id,))
    execute("DELETE FROM t_character_like WHERE character_id = %s", (character_id,))
    execute("DELETE FROM t_character_card WHERE id = %s", (character_id,))
    invalidate_character(character_id)
    return success_response({"success": True})


@character_bp.post("/character/<int:character_id>/like")
@jwt_required()
def like_character(character_id: int):
    user_id = int(get_jwt_identity())

    existing = query_one(
        "SELECT id FROM t_character_like WHERE user_id = %s AND character_id = %s",
        (user_id, character_id)
    )

    if existing:
        execute("DELETE FROM t_character_like WHERE user_id = %s AND character_id = %s", (user_id, character_id))
        execute("UPDATE t_character_card SET like_count = like_count - 1 WHERE id = %s", (character_id,))
        invalidate_character(character_id)
        return success_response({"liked": False})
    else:
        execute("INSERT INTO t_character_like (user_id, character_id) VALUES (%s, %s)", (user_id, character_id))
        execute("UPDATE t_character_card SET like_count = like_count + 1 WHERE id = %s", (character_id,))
        invalidate_character(character_id)
        return success_response({"liked": True})


@character_bp.post("/character/<int:character_id>/collect")
@jwt_required()
def collect_character(character_id: int):
    user_id = int(get_jwt_identity())

    existing = query_one(
        "SELECT id FROM t_character_collect WHERE user_id = %s AND character_id = %s",
        (user_id, character_id)
    )

    if existing:
        execute("DELETE FROM t_character_collect WHERE user_id = %s AND character_id = %s", (user_id, character_id))
        execute("UPDATE t_character_card SET collect_count = collect_count - 1 WHERE id = %s", (character_id,))
        invalidate_character(character_id)
        return success_response({"collected": False})
    else:
        execute("INSERT INTO t_character_collect (user_id, character_id) VALUES (%s, %s)", (user_id, character_id))
        execute("UPDATE t_character_card SET collect_count = collect_count + 1 WHERE id = %s", (character_id,))
        invalidate_character(character_id)
        return success_response({"collected": True})


@character_bp.get("/character/my")
@jwt_required()
def get_my_characters():
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)

    count_sql = "SELECT COUNT(*) AS total FROM t_character_card WHERE user_id = %s AND status = 1"
    total_row = query_one(count_sql, (user_id,))
    total = total_row["total"]

    data_sql = (
        f"SELECT {_CHAR_SELECT} FROM t_character_card "
        f"WHERE user_id = %s AND status = 1 "
        f"ORDER BY create_time DESC LIMIT %s OFFSET %s"
    )
    items = query_all(data_sql, (user_id, page_size, (page_num - 1) * page_size))

    result = [{
        "id": item["id"],
        "userId": item["user_id"],
        "name": item["name"],
        "desc": item.get("desc", ""),
        "avatar": item.get("avatar", ""),
        "author": item.get("author", ""),
        "language": item.get("language", "zh-Hans"),
        "category": item.get("category", 0),
        "tags": _parse_tags(item.get("tags")),
        "personaContent": item.get("persona_content", ""),
        "isPublic": item.get("is_public", 1),
        "likeCount": item.get("like_count", 0),
        "viewCount": item.get("view_count", 0),
        "collectCount": item.get("collect_count", 0),
        "useCount": item.get("use_count", 0),
        "createTime": str(item.get("create_time", "")),
    } for item in items]

    return page_response(result, total=total, page_num=page_num, page_size=page_size)


# ---- Character Chat Endpoints ----


def _chat_ensure_credits(user_id: int):
    balance = get_balance(user_id)
    if balance < 0:
        raise AppError(ErrorCode.FORBIDDEN, "积分已透支，无法继续对话，请联系管理员充值")


def _chat_check_and_deduct(user_id: int, tokens: int, **kwargs):
    if not tokens:
        return 0
    deduction = math.ceil(tokens / 100)
    balance = get_balance(user_id)
    if balance < 0:
        raise AppError(ErrorCode.FORBIDDEN, "积分已透支，无法继续对话，请联系管理员充值")
    deduct(user_id, deduction, tokens_used=tokens, **kwargs)
    return deduction


def _char_add_token_usage(entity_id: int, tokens: int):
    if not entity_id or not tokens:
        return
    execute(
        "UPDATE t_character_card SET use_count = use_count + %s WHERE id = %s",
        (tokens, entity_id),
    )


@character_bp.get("/character/<int:character_id>/config")
def get_character_chat_config(character_id: int):
    character = query_one(
        f"SELECT {_CHAR_SELECT} FROM t_character_card "
        f"WHERE id = %s AND status = 1",
        (character_id,),
    )
    if not character:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "角色卡不存在")

    persona_content = character.get("persona_content", "")
    system_prompt = build_character_system_prompt(persona_content) if persona_content else ""

    return success_response({
        "id": character["id"],
        "name": character["name"],
        "avatar": character.get("avatar", ""),
        "desc": character.get("desc", ""),
        "author": character.get("author", ""),
        "tags": _parse_tags(character.get("tags")),
        "systemPrompt": system_prompt,
        "personaContent": persona_content,
        "useCount": character.get("use_count", 0),
    })


@character_bp.post("/character/<int:character_id>/chat")
@jwt_required()
def character_chat_stream(character_id: int):
    """SSE streaming chat with a character card."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    model = payload.get("model") or ""
    thinking_mode = bool(payload.get("thinkingMode", False))
    reasoning_effort = payload.get("reasoningEffort", "medium")
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

    character = query_one(
        f"SELECT {_CHAR_SELECT} FROM t_character_card WHERE id = %s AND status = 1",
        (character_id,),
    )
    if not character:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "角色卡不存在")

    persona_content = character.get("persona_content", "")
    system_prompt = build_character_system_prompt(persona_content) if persona_content else ""
    if system_prompt and normalized_messages[0]["role"] != "system":
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
    _chat_ensure_credits(user_id)

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

        if stream_tokens:
            _char_add_token_usage(character_id, stream_tokens)
            _increment_daily_stat("character", character_id)
            try:
                _chat_check_and_deduct(user_id, stream_tokens, conversation_id=conversation_id)
            except AppError:
                pass

        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
