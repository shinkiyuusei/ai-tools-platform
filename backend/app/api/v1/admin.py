import json

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...services.cache import invalidate_work
from ...utils.crud import dynamic_update
from ...utils.mysql import execute, query_all, query_one
from ...utils.response import page_response, success_response
from ...utils.writing_style import normalize_writing_style

admin_bp = Blueprint("admin", __name__)


def _parse_json_col(col):
    """Parse a JSON column that may be returned as a string from PyMySQL."""
    return json.loads(col) if isinstance(col, str) else col


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
        where.append("(name LIKE %s OR `desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(where)
    total_row = query_one(f"SELECT COUNT(*) AS total FROM t_character_card WHERE {where_clause}", tuple(params))
    total = total_row["total"]

    items = query_all(
        f"SELECT id, user_id AS userId, name, `desc`, avatar, author, tags, "
        f"is_public AS isPublic, "
        f"like_count AS likeCount, view_count AS viewCount, collect_count AS collectCount, "
        f"use_count AS useCount, status, create_time AS createTime "
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
        "SELECT id, user_id AS userId, name, `desc`, avatar, author, language, category, tags, "
        "persona_content AS personaContent, is_public AS isPublic, "
        "like_count AS likeCount, view_count AS viewCount, collect_count AS collectCount, "
        "use_count AS useCount, status, create_time AS createTime "
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
        "desc": "desc",
        "avatar": "avatar",
        "author": "author",
        "language": "language",
        "category": "category",
        "tags": "tags",
        "personaContent": "persona_content",
        "isPublic": "is_public",
        "status": "status",
        "likeCount": "like_count",
        "viewCount": "view_count",
        "collectCount": "collect_count",
        "useCount": "use_count",
    }
    dynamic_update("t_character_card", field_map, payload, "id", char_id)
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/character/<int:char_id>")
@jwt_required()
def delete_character_admin(char_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    execute("DELETE FROM t_character_collect WHERE character_id = %s", (char_id,))
    execute("DELETE FROM t_character_like WHERE character_id = %s", (char_id,))
    execute("DELETE FROM t_character_card WHERE id = %s", (char_id,))
    return success_response({"message": "删除成功"})


# ---- Work Card Management ----

@admin_bp.get("/admin/work")
@jwt_required()
def list_works_admin():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)
    keyword = request.args.get("keyword", "")

    where = ["status != 0"]
    params = []
    if keyword:
        where.append("(name LIKE %s OR `desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(where)
    total_row = query_one(f"SELECT COUNT(*) AS total FROM t_work_card WHERE {where_clause}", tuple(params))
    total = total_row["total"]

    items = query_all(
        f"SELECT id, user_id AS userId, name, cover, `desc`, tags, "
        f"category AS categoryId, use_count AS useCount, status, "
        f"create_time AS createTime, update_time AS updateTime "
        f"FROM t_work_card WHERE {where_clause} "
        f"ORDER BY create_time DESC, id DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, (page_num - 1) * page_size]),
    )
    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@admin_bp.get("/admin/work/<int:work_id>")
@jwt_required()
def get_work_admin(work_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    work = query_one(
        "SELECT id, user_id AS userId, name, cover, `desc`, tags, "
        "role_config, openings, summary, author, language, category, "
        "use_count AS useCount, status, create_time AS createTime, update_time AS updateTime "
        "FROM t_work_card WHERE id = %s",
        (work_id,),
    )
    if not work:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品卡不存在")

    for col in ("tags", "openings", "role_config"):
        work[col] = _parse_json_col(work.get(col))

    # Extract writingStyle from role_config for frontend convenience
    role_cfg = work.get("role_config") or {}
    ws = role_cfg.get("writing_style") or {}
    work["writingStyle"] = normalize_writing_style(ws)

    return success_response(work)


@admin_bp.put("/admin/work/<int:work_id>")
@jwt_required()
def update_work_admin(work_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    payload = request.get_json(silent=True) or {}
    updates = {}
    values = []

    for col in ["name", "desc", "cover", "author", "summary", "language", "category"]:
        if col in payload:
            updates[col] = "%s"
            values.append(payload[col])

    for col in ["status", "useCount"]:
        if col in payload:
            db_col = "status" if col == "status" else "use_count"
            updates[db_col] = "%s"
            values.append(payload[col])

    if "tags" in payload:
        updates["tags"] = "%s"
        values.append(json.dumps(payload["tags"], ensure_ascii=False))

    # Merge writingStyle into role_config (atomic JSON_SET, no read-modify-write)
    role_config_sql = None
    role_config_params = []
    if "writingStyle" in payload:
        ws = payload.get("writingStyle") or {}
        writing_style_json = json.dumps(normalize_writing_style(ws), ensure_ascii=False)
        role_config_sql = (
            "JSON_SET(COALESCE(role_config, '{}'), '$.writing_style', CAST(%s AS JSON))"
        )
        role_config_params = [writing_style_json]

    if not updates and not role_config_sql:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    set_parts = [f"`{k}` = %s" for k in updates]
    values.extend(role_config_params)
    values.append(work_id)
    if role_config_sql:
        set_parts.append(f"role_config = {role_config_sql}")
    execute(f"UPDATE t_work_card SET {', '.join(set_parts)} WHERE id = %s", tuple(values))
    invalidate_work(work_id)
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/work/<int:work_id>")
@jwt_required()
def delete_work_admin(work_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    execute("DELETE FROM t_work_collect WHERE work_id = %s", (work_id,))
    execute(
        "DELETE FROM t_conversation WHERE entity_id = %s AND entity_type = 'work'",
        (work_id,),
    )
    execute("DELETE FROM t_work_card WHERE id = %s", (work_id,))
    return success_response({"message": "删除成功"})


# ---- User Management ----

@admin_bp.get("/admin/user")
@jwt_required()
def list_users_admin():
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)
    keyword = request.args.get("keyword", "")

    where = ["is_delete = 0"]
    params = []
    if keyword:
        where.append("(email LIKE %s OR nickname LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    where_clause = " AND ".join(where)
    total_row = query_one(f"SELECT COUNT(*) AS total FROM t_user WHERE {where_clause}", tuple(params))
    total = total_row["total"]

    items = query_all(
        f"SELECT id, email, phone, nickname, avatar, vip_level AS vipLevel, "
        f"vip_expire_time AS vipExpireTime, credits, status, "
        f"create_time AS createTime, update_time AS updateTime "
        f"FROM t_user WHERE {where_clause} "
        f"ORDER BY create_time DESC, id DESC LIMIT %s OFFSET %s",
        tuple(params + [page_size, (page_num - 1) * page_size]),
    )
    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@admin_bp.get("/admin/user/<int:target_user_id>")
@jwt_required()
def get_user_admin(target_user_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    user = query_one(
        "SELECT id, email, phone, nickname, avatar, vip_level AS vipLevel, "
        "vip_expire_time AS vipExpireTime, credits, status, "
        "create_time AS createTime, update_time AS updateTime "
        "FROM t_user WHERE id = %s AND is_delete = 0",
        (target_user_id,),
    )
    if not user:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "用户不存在")
    return success_response(user)


@admin_bp.put("/admin/user/<int:target_user_id>")
@jwt_required()
def update_user_admin(target_user_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    payload = request.get_json(silent=True) or {}
    field_map = {
        "nickname": "nickname",
        "vipLevel": "vip_level",
        "vipExpireTime": "vip_expire_time",
        "credits": "credits",
        "status": "status",
    }
    dynamic_update("t_user", field_map, payload, "id", target_user_id)
    return success_response({"message": "更新成功"})


@admin_bp.delete("/admin/user/<int:target_user_id>")
@jwt_required()
def delete_user_admin(target_user_id: int):
    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    execute("UPDATE t_user SET is_delete = 1 WHERE id = %s", (target_user_id,))
    return success_response({"message": "删除成功"})
