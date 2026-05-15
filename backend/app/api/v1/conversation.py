from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ...utils.mysql import execute, query_all, query_one
from ...utils.response import success_response
from ...utils.snowflake import generate_id

conv_bp = Blueprint("conversation", __name__)


def _get_user_id():
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return int(identity) if identity else 0
    except Exception:
        return 0


@conv_bp.post("/conversation")
def create():
    user_id = _get_user_id()
    payload = request.get_json(silent=True) or {}
    work_id = int(payload.get("workId", 0))
    title = (payload.get("title") or "").strip()[:100]

    if not title:
        row = query_one(
            "SELECT COUNT(1) AS cnt FROM t_conversation WHERE user_id = %s AND work_id = %s AND is_delete = 0",
            (user_id, work_id),
        )
        title = f"新对话{(row['cnt'] if row else 0) + 1}"

    conv_id = generate_id()
    execute(
        "INSERT INTO t_conversation (id, user_id, work_id, title) VALUES (%s,%s,%s,%s)",
        (conv_id, user_id, work_id, title),
    )
    return success_response(
        {"id": conv_id, "workId": work_id, "title": title, "createTime": datetime.utcnow().isoformat()}
    )


@conv_bp.get("/conversation/<int:conv_id>")
def detail(conv_id: int):
    conv = query_one(
        "SELECT id, user_id, work_id, title, message_count, create_time, update_time "
        "FROM t_conversation WHERE id = %s AND is_delete = 0",
        (conv_id,),
    )
    if not conv:
        return success_response(None, "对话不存在")
    messages = query_all(
        "SELECT id, role, content, create_time FROM t_message WHERE conversation_id = %s ORDER BY id ASC",
        (conv_id,),
    )
    return success_response(
        {
            "id": conv["id"],
            "userId": conv["user_id"],
            "workId": conv["work_id"],
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
def add_messages(conv_id: int):
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
def list_conversations():
    user_id = _get_user_id()
    work_id = request.args.get("workId", type=int, default=0)
    page = request.args.get("pageNum", type=int, default=1)
    page_size = min(request.args.get("pageSize", type=int, default=20), 50)

    where = "is_delete = 0"
    params = []
    if user_id:
        where += " AND user_id = %s"
        params.append(user_id)
    if work_id:
        where += " AND work_id = %s"
        params.append(work_id)

    offset = (page - 1) * page_size
    total_row = query_one(f"SELECT COUNT(1) AS cnt FROM t_conversation WHERE {where}", tuple(params))
    total = total_row["cnt"] if total_row else 0

    rows = query_all(
        f"SELECT id, user_id, work_id, title, message_count, create_time, update_time "
        f"FROM t_conversation WHERE {where} ORDER BY update_time DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, offset]),
    )

    lst = []
    for r in (rows or []):
        lst.append(
            {
                "id": r["id"],
                "workId": r["work_id"],
                "title": r["title"],
                "messageCount": r["message_count"],
                "createTime": r["create_time"].isoformat() if hasattr(r["create_time"], "isoformat") else str(r["create_time"]),
                "updateTime": r["update_time"].isoformat() if hasattr(r["update_time"], "isoformat") else str(r["update_time"]),
            }
        )

    return success_response({"list": lst, "total": total, "pageNum": page, "pageSize": page_size})


@conv_bp.delete("/conversation/<int:conv_id>")
def remove(conv_id: int):
    execute("UPDATE t_conversation SET is_delete = 1 WHERE id = %s", (conv_id,))
    return success_response(None, "已删除")
