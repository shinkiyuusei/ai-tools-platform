import json

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...utils.crud import dynamic_update
from ...utils.mysql import execute, query_all, query_one
from ...utils.response import page_response, success_response
from ...utils.snowflake import generate_id

admin_bp = Blueprint("admin", __name__)


def _check_admin(user_id: int):
    user = query_one(
        "SELECT vip_level FROM t_user WHERE id = %s AND status = 1 AND is_delete = 0",
        (user_id,),
    )
    if not user or user["vip_level"] < 2:
        raise AppError(ErrorCode.FORBIDDEN, "无管理员权限")


# ---- Tag Management ----

@admin_bp.get("/admin/tag")
def list_tags():
    items = query_all(
        "SELECT id, name, sort_order AS sortOrder, create_time AS createTime "
        "FROM t_tag ORDER BY sort_order ASC",
        (),
    )
    return success_response({"list": items})


@admin_bp.post("/admin/tag")
@jwt_required()
def create_tag():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "标签名称不能为空")
    sort_order = payload.get("sortOrder", 0)
    tag_id = execute(
        "INSERT INTO t_tag (name, sort_order) VALUES (%s, %s)",
        (name, sort_order),
    )
    return success_response({"id": tag_id, "message": "创建成功"})


@admin_bp.put("/admin/tag/<int:tag_id>")
@jwt_required()
def update_tag(tag_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)
    payload = request.get_json(silent=True) or {}
    dynamic_update("t_tag", {"name": "name", "sortOrder": "sort_order"}, payload, "id", tag_id)
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/tag/<int:tag_id>")
@jwt_required()
def delete_tag(tag_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)
    execute("DELETE FROM t_tag WHERE id = %s", (tag_id,))
    return success_response({"message": "删除成功"})


@admin_bp.get("/admin/tool")
@jwt_required()
def list_tools():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)

    total_row = query_one("SELECT COUNT(*) AS total FROM t_ai_tool", ())
    total = total_row["total"]

    items = query_all(
        "SELECT t.id, t.name, t.icon, t.`desc`, t.use_desc AS useDesc,"
        "t.tag_ids AS tagIds, t.form_config AS formConfig, t.ai_api AS aiApi,"
        "t.is_free AS isFree, t.is_vip AS isVip, t.use_count AS useCount,"
        "t.sort_order AS sortOrder, t.status,"
        "t.create_time AS createTime, t.update_time AS updateTime,"
        "COALESCE(r.rating_count, 0) AS ratingCount,"
        "COALESCE(c.conv_count, 0) AS convCount "
        "FROM t_ai_tool t "
        "LEFT JOIN ("
        "  SELECT work_id, COUNT(*) AS rating_count "
        "  FROM t_rating WHERE work_type = 'tool' GROUP BY work_id"
        ") r ON r.work_id = t.id "
        "LEFT JOIN ("
        "  SELECT work_id, COUNT(*) AS conv_count "
        "  FROM t_conversation GROUP BY work_id"
        ") c ON c.work_id = t.id "
        "ORDER BY t.sort_order ASC LIMIT %s OFFSET %s",
        (page_size, (page_num - 1) * page_size),
    )
    from .tool import _resolve_tag_names
    items = _resolve_tag_names(items)
    for item in items:
        _extract_form_config_fields(item)
    return page_response(items, total=total, page_num=page_num, page_size=page_size)


def _extract_form_config_fields(item: dict):
    """Parse form_config JSON and extract structured fields into the item dict."""
    raw = item.get("formConfig")
    if not raw:
        return
    try:
        config = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(config, dict):
        return
    item["author"] = config.get("author", "")
    item["rating"] = config.get("rating", 0)
    item["detailedIntro"] = config.get("detailedIntro", "")
    item["characters"] = config.get("characters", [])
    item["protagonist"] = config.get("protagonist", None)
    item["worldSetting"] = config.get("worldSetting", None)
    item["gameRules"] = config.get("gameRules", "")
    item["statusBar"] = config.get("statusBar", "")
    item["opening"] = config.get("opening", "")
    item["writingStyle"] = config.get("writingStyle", None)
    item["models"] = config.get("models", [])
    item["sourceId"] = config.get("sourceId", "")
    item["version"] = config.get("version", "")
    item["modelConfig"] = config.get("modelConfig", None)
    item["formStats"] = config.get("stats", None)
    # Keep formConfig as raw string for the edit dialog


@admin_bp.post("/admin/tool")
@jwt_required()
def create_tool():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "")
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "工具名称不能为空")

    form_config = payload.get("formConfig", {})
    if isinstance(form_config, (list, dict)):
        form_config = json.dumps(form_config, ensure_ascii=False)

    tool_id = execute(
        "INSERT INTO t_ai_tool (name,icon,`desc`,use_desc,tag_ids,form_config,ai_api,"
        "is_free,is_vip,use_count,sort_order,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            name,
            payload.get("icon", ""),
            payload.get("desc", ""),
            payload.get("useDesc", ""),
            payload.get("tagIds", ""),
            form_config,
            payload.get("aiApi", "deepseek"),
            payload.get("isFree", 1),
            payload.get("isVip", 0),
            0,
            payload.get("sortOrder", 0),
            payload.get("status", 1),
        ),
    )
    return success_response({"id": tool_id, "message": "创建成功"})


@admin_bp.put("/admin/tool/<int:tool_id>")
@jwt_required()
def update_tool(tool_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    payload = request.get_json(silent=True) or {}
    field_map = {
        "name": "name",
        "icon": "icon",
        "desc": "desc",
        "useDesc": "use_desc",
        "tagIds": "tag_ids",
        "aiApi": "ai_api",
        "isFree": "is_free",
        "isVip": "is_vip",
        "sortOrder": "sort_order",
        "status": "status",
    }
    fields = []
    params = []
    for json_key, db_key in field_map.items():
        val = payload.get(json_key)
        if val is not None:
            if json_key == "desc":
                fields.append(f"`{db_key}` = %s")
            else:
                fields.append(f"{db_key} = %s")
            params.append(val)

    if "formConfig" in payload:
        fields.append("form_config = %s")
        fc = payload["formConfig"]
        params.append(json.dumps(fc, ensure_ascii=False) if isinstance(fc, (list, dict)) else fc)

    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    params.append(tool_id)
    execute(f"UPDATE t_ai_tool SET {', '.join(fields)} WHERE id = %s", tuple(params))
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/tool/<int:tool_id>")
@jwt_required()
def delete_tool(tool_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    execute("DELETE FROM t_ai_tool WHERE id = %s", (tool_id,))
    return success_response({"message": "删除成功"})


# ---- Character Card Management ----

@admin_bp.get("/admin/character")
@jwt_required()
def list_characters_admin():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)
    keyword = request.args.get("keyword", "")

    where = ["1=1"]
    params = []
    if keyword:
        where.append("(name LIKE %s OR description LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(where)
    total_row = query_one(f"SELECT COUNT(*) AS total FROM t_character_card WHERE {where_clause}", tuple(params))
    total = total_row["total"]

    items = query_all(
        f"SELECT id, user_id AS userId, name, avatar, description, personality, background, tags, "
        f"is_public AS isPublic, is_vip AS isVip, "
        f"like_count AS likeCount, view_count AS viewCount, collect_count AS collectCount, "
        f"status, create_time AS createTime "
        f"FROM t_character_card WHERE {where_clause} "
        f"ORDER BY create_time DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, (page_num - 1) * page_size]),
    )
    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@admin_bp.get("/admin/character/<int:char_id>")
@jwt_required()
def get_character_admin(char_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    char = query_one(
        "SELECT id, user_id AS userId, name, avatar, description, personality, background, tags, "
        "is_public AS isPublic, is_vip AS isVip, "
        "like_count AS likeCount, view_count AS viewCount, collect_count AS collectCount, "
        "status, create_time AS createTime "
        "FROM t_character_card WHERE id = %s",
        (char_id,),
    )
    if not char:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "角色卡不存在")
    return success_response(char)


@admin_bp.put("/admin/character/<int:char_id>")
@jwt_required()
def update_character_admin(char_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    payload = request.get_json(silent=True) or {}
    field_map = {
        "name": "name",
        "avatar": "avatar",
        "description": "description",
        "personality": "personality",
        "background": "background",
        "tags": "tags",
        "isPublic": "is_public",
        "isVip": "is_vip",
        "status": "status",
        "likeCount": "like_count",
        "viewCount": "view_count",
        "collectCount": "collect_count",
    }
    dynamic_update("t_character_card", field_map, payload, "id", char_id)
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/character/<int:char_id>")
@jwt_required()
def delete_character_admin(char_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    execute("UPDATE t_character_card SET status = 0 WHERE id = %s", (char_id,))
    return success_response({"message": "删除成功"})
