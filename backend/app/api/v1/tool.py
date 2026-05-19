from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...utils.mysql import query_all, query_one
from ...utils.response import page_response, success_response

tool_bp = Blueprint("tool", __name__)


def _resolve_tag_names(items):
    """Batch-resolve tag IDs to tag names for a list of tool dicts.
    Handles both numeric IDs (1,2,3) and text tags (恶堕,校园,NTR).
    """
    if not items:
        return items
    all_tag_ids = set()
    for item in items:
        raw = item.get("tagIds", "")
        if raw:
            for tid in raw.split(","):
                tid = tid.strip()
                if tid and tid.isdigit():
                    all_tag_ids.add(int(tid))
    # Lookup numeric IDs from t_tag
    id_to_name = {}
    if all_tag_ids:
        placeholders = ",".join(["%s"] * len(all_tag_ids))
        tag_rows = query_all(
            f"SELECT id, name FROM t_tag WHERE id IN ({placeholders})",
            tuple(all_tag_ids),
        )
        id_to_name = {row["id"]: row["name"] for row in tag_rows}
    # Resolve tags for each item
    for item in items:
        raw = item.get("tagIds", "")
        tags = []
        seen = set()
        if raw:
            for tid in raw.split(","):
                tid = tid.strip()
                if not tid:
                    continue
                if tid.isdigit():
                    tag_id = int(tid)
                    if tag_id in id_to_name and tag_id not in seen:
                        tags.append({"id": tag_id, "name": id_to_name[tag_id]})
                        seen.add(tag_id)
                else:
                    # Text-based tag: use hash as pseudo-id for color assignment
                    if tid not in seen:
                        pseudo_id = abs(hash(tid)) % 1000 + 100
                        tags.append({"id": pseudo_id, "name": tid})
                        seen.add(tid)
        item["tags"] = tags
    return items


@tool_bp.get("/tool/list")
def tool_list():
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)
    tag_id = request.args.get("tagId")
    sort_type = request.args.get("sortType", "hot")
    keyword = request.args.get("keyword", "")

    where = ["status = 1"]
    params = []

    if tag_id:
        where.append("FIND_IN_SET(%s, tag_ids) > 0")
        params.append(tag_id)

    if keyword:
        where.append("name LIKE %s")
        params.append(f"%{keyword}%")

    where_clause = " AND ".join(where)

    order_map = {
        "hot": "use_count DESC",
        "new": "create_time DESC",
        "old": "create_time ASC",
    }
    order_clause = order_map.get(sort_type, "use_count DESC")

    count_sql = f"SELECT COUNT(*) AS total FROM t_ai_tool WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]

    data_sql = f"SELECT id,name,icon,`desc`,tag_ids AS tagIds,use_count AS useCount,is_free AS isFree,is_vip AS isVip,create_time AS createTime,COALESCE(JSON_EXTRACT(form_config, '$.rating'), 0) AS rating FROM t_ai_tool WHERE {where_clause} ORDER BY {order_clause} LIMIT %s OFFSET %s"
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))
    items = _resolve_tag_names(items)

    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@tool_bp.get("/tool/detail/<int:tool_id>")
def tool_detail(tool_id: int):
    tool = query_one(
        "SELECT id,name,icon,`desc`,use_desc AS useDesc,"
        "tag_ids AS tagIds,form_config AS formConfig,ai_api AS aiApi,"
        "is_free AS isFree,is_vip AS isVip,use_count AS useCount,"
        "COALESCE(JSON_EXTRACT(form_config, '$.rating'), 0) AS rating "
        "FROM t_ai_tool WHERE id = %s AND status = 1",
        (tool_id,),
    )
    if not tool:
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.SYSTEM_ERROR, "工具不存在或已下架")

    tool = _resolve_tag_names([tool])[0]

    if tool.get("formConfig") and isinstance(tool["formConfig"], str):
        import json
        tool["formConfig"] = json.loads(tool["formConfig"])

    return success_response(tool)


@tool_bp.post("/user/tool/collect")
@jwt_required()
def collect_tool():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    tool_id = payload.get("toolId")
    if not tool_id:
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, "工具ID不能为空")

    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    existing = mongo_db["t_user_collect"].find_one({"userId": user_id, "toolId": tool_id})
    if existing:
        mongo_db["t_user_collect"].delete_one({"userId": user_id, "toolId": tool_id})
        return success_response({"success": True, "message": "已取消收藏"})
    else:
        mongo_db["t_user_collect"].insert_one({"userId": user_id, "toolId": tool_id})
        return success_response({"success": True, "message": "收藏成功"})


@tool_bp.get("/user/tool/recent")
@jwt_required()
def recent_tools():
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)

    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    total = mongo_db["t_generate_record"].count_documents({"userId": user_id})
    cursor = (
        mongo_db["t_generate_record"]
        .find({"userId": user_id})
        .sort("createTime", -1)
        .skip((page_num - 1) * page_size)
        .limit(page_size)
    )
    seen = set()
    items = []
    for doc in cursor:
        tid = doc["toolId"]
        if tid in seen:
            continue
        seen.add(tid)
        items.append(
            {
                "id": tid,
                "name": doc["toolName"],
                "icon": "ri-magic-line",
                "lastUseTime": doc["createTime"].isoformat() if doc.get("createTime") else "",
            }
        )
    return page_response(items, total=len(items), page_num=page_num, page_size=page_size)
