from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...utils.mysql import execute, query_all, query_one
from ...utils.response import success_response
from ...utils.snowflake import generate_id

conv_bp = Blueprint("conversation", __name__)


@conv_bp.post("/conversation")
@jwt_required()
def create():
    user_id = int(get_jwt_identity())
    # Some clients may send content-type that causes get_json to fail silently;
    # fall back to raw body parsing
    payload = request.get_json(silent=True) or {}
    if not payload:
        raw = request.get_data(as_text=True)
        if raw:
            import json as _json
            try:
                payload = _json.loads(raw)
            except Exception:
                payload = {}
    entity_id = int(payload.get("entityId", 0) or payload.get("workId", 0))
    entity_type = (payload.get("entityType") or "work").strip()
    title = (payload.get("title") or "").strip()[:100]

    if not title:
        row = query_one(
            "SELECT COUNT(1) AS cnt FROM t_conversation WHERE user_id = %s AND entity_id = %s AND entity_type = %s AND is_delete = 0",
            (user_id, entity_id, entity_type),
        )
        title = f"新对话{(row['cnt'] if row else 0) + 1}"

    conv_id = generate_id()
    execute(
        "INSERT INTO t_conversation (id, user_id, entity_id, entity_type, title) VALUES (%s,%s,%s,%s,%s)",
        (conv_id, user_id, entity_id, entity_type, title),
    )
    return success_response(
        {"id": conv_id, "entityId": entity_id, "entityType": entity_type, "title": title, "createTime": datetime.utcnow().isoformat()}
    )


@conv_bp.get("/conversation/<int:conv_id>")
@jwt_required()
def detail(conv_id: int):
    user_id = int(get_jwt_identity())
    conv = query_one(
        "SELECT id, user_id, entity_id, entity_type, title, message_count, create_time, update_time "
        "FROM t_conversation WHERE id = %s AND user_id = %s AND is_delete = 0",
        (conv_id, user_id),
    )
    if not conv:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    messages = query_all(
        "SELECT id, role, content, create_time FROM t_message WHERE conversation_id = %s ORDER BY id ASC",
        (conv_id,),
    )
    return success_response(
        {
            "id": conv["id"],
            "userId": conv["user_id"],
            "entityId": conv["entity_id"],
            "entityType": conv["entity_type"],
            "title": conv["title"],
            "messageCount": conv["message_count"],
            "createTime": conv["create_time"].isoformat() if hasattr(conv["create_time"], "isoformat") else str(conv["create_time"]),
            "updateTime": conv["update_time"].isoformat() if hasattr(conv["update_time"], "isoformat") else str(conv["update_time"]),
            "messages": [
                {
                    "id": m["id"],
                    "role": m["role"],
                    "content": m["content"],
                    "createTime": m["create_time"].isoformat() if hasattr(m["create_time"], "isoformat") else str(m["create_time"]),
                }
                for m in (messages or [])
            ],
        }
    )


@conv_bp.post("/conversation/<int:conv_id>/messages")
@jwt_required()
def add_messages(conv_id: int):
    user_id = int(get_jwt_identity())
    conv = query_one(
        "SELECT id FROM t_conversation WHERE id = %s AND user_id = %s AND is_delete = 0",
        (conv_id, user_id),
    )
    if not conv:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")

    payload = request.get_json(silent=True) or {}
    msgs = payload.get("messages") or []

    if not isinstance(msgs, list) or not msgs:
        return success_response({"saved": 0}, "无消息需保存")

    saved = 0
    for m in msgs:
        role = (m.get("role") or "").strip()
        content = str(m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        msg_id = generate_id()
        execute(
            "INSERT INTO t_message (id, conversation_id, role, content) VALUES (%s,%s,%s,%s)",
            (msg_id, conv_id, role, content),
        )
        saved += 1

    if saved:
        execute(
            "UPDATE t_conversation SET message_count = message_count + %s, update_time = NOW() WHERE id = %s",
            (saved, conv_id),
        )

    return success_response({"saved": saved})


@conv_bp.get("/conversations")
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    entity_id = request.args.get("entityId", type=int, default=0)
    entity_type = request.args.get("entityType", type=str, default="work")
    page = request.args.get("pageNum", type=int, default=1)
    page_size = min(request.args.get("pageSize", type=int, default=20), 50)

    where = "is_delete = 0 AND user_id = %s"
    params = [user_id]
    if entity_id:
        where += " AND entity_id = %s"
        params.append(entity_id)
    if entity_type:
        where += " AND entity_type = %s"
        params.append(entity_type)

    offset = (page - 1) * page_size
    total_row = query_one(f"SELECT COUNT(1) AS cnt FROM t_conversation WHERE {where}", tuple(params))
    total = total_row["cnt"] if total_row else 0

    rows = query_all(
        f"SELECT id, user_id, entity_id, entity_type, title, message_count, create_time, update_time "
        f"FROM t_conversation WHERE {where} ORDER BY update_time DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, offset]),
    )

    lst = []
    for r in (rows or []):
        lst.append(
            {
                "id": r["id"],
                "entityId": r["entity_id"],
                "entityType": r["entity_type"],
                "title": r["title"],
                "messageCount": r["message_count"],
                "createTime": r["create_time"].isoformat() if hasattr(r["create_time"], "isoformat") else str(r["create_time"]),
                "updateTime": r["update_time"].isoformat() if hasattr(r["update_time"], "isoformat") else str(r["update_time"]),
            }
        )

    return success_response({"list": lst, "total": total, "pageNum": page, "pageSize": page_size})


@conv_bp.delete("/conversation/<int:conv_id>")
@jwt_required()
def remove(conv_id: int):
    user_id = int(get_jwt_identity())
    conv = query_one(
        "SELECT id FROM t_conversation WHERE id = %s AND user_id = %s AND is_delete = 0",
        (conv_id, user_id),
    )
    if not conv:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "对话不存在")
    execute("UPDATE t_conversation SET is_delete = 1 WHERE id = %s", (conv_id,))
    return success_response(None, "已删除")
