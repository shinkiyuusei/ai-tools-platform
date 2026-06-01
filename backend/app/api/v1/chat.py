"""
Chat API endpoints for AI chat works.
Uses t_work_card with real columns + role_config JSON.
"""
import json
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from ...utils.mysql import query_one, query_all, execute
from ...utils.response import success_response, page_response
from ...core.errors import AppError, ErrorCode
from ...services.cache import (
    get_cached_work, set_cached_work, invalidate_work,
    cache_get, cache_set, LIST_TTL,
)
from ...services.chat.prompt_builder import build_enhanced_system_prompt

chat_bp = Blueprint("chat", __name__)


def _try_get_user_id():
    """Get JWT identity without raising on invalid/expired tokens."""
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return int(identity) if identity else None
    except Exception:
        return None


_WORK_SELECT = (
    "id, user_id, name, `desc`, cover, author, summary, opening, openings, "
    "tags, role_config, use_count AS useCount, create_time AS createTime"
)


def _parse_json(col, default=None):
    if default is None:
        default = {}
    if not col:
        return default
    try:
        val = json.loads(col) if isinstance(col, str) else col
    except (json.JSONDecodeError, TypeError):
        return default
    return val if isinstance(val, (dict, list)) else default


def _build_work_data(work, perspective=None):
    """Build the work response data dict (without response wrapper)."""
    work_name = work.get("name", "")
    role_config = _parse_json(work.get("role_config"), {})
    openings = _parse_json(work.get("openings"), [])

    legacy = {
        "author": work.get("author", ""),
        "detailedIntro": work.get("summary", ""),
        "opening": work.get("opening", ""),
        "models": ["deepseek-v4-flash"],
        "characters": role_config.get("npc_settings", []),
        "protagonist": {
            "name": role_config.get("protagonist_setting", {}).get("name", ""),
            "description": role_config.get("protagonist_setting", {}).get("setting", ""),
            "motivation": role_config.get("protagonist_setting", {}).get("core_motivation", ""),
        },
        "worldSetting": {
            "worldName": role_config.get("worldview_setting", {}).get("name", ""),
            "eraTech": role_config.get("worldview_setting", {}).get("era_background", ""),
            "coreConflict": role_config.get("worldview_setting", {}).get("core_conflict", ""),
            "toneAtmosphere": role_config.get("worldview_setting", {}).get("overall_atmosphere", ""),
            "mainPlot": role_config.get("main_plot", ""),
            "initialState": role_config.get("init_plot_status", ""),
        },
        "gameRules": role_config.get("play_rule", ""),
        "statusBar": role_config.get("status_bar", ""),
    }

    full_prompt = build_enhanced_system_prompt(work_name, legacy, perspective)

    opening_text = work.get("opening", "")
    opening_statements = openings
    if not opening_statements and opening_text:
        opening_statements = [{"label": "默认开局", "text": opening_text}]
    if not opening_text and opening_statements:
        opening_text = opening_statements[0].get("text", "")

    protagonist = role_config.get("protagonist_setting", {})
    protagonist_name = protagonist.get("name", "").strip()
    perspective_name = perspective.get("name", "").strip() if perspective else ""
    if perspective_name and perspective_name != protagonist_name:
        opening_text = ""
        opening_statements = []

    return {
        "id": work["id"],
        "name": work_name,
        "icon": work.get("cover", ""),
        "desc": work.get("desc", ""),
        "isFree": True,
        "isVip": False,
        "useCount": work.get("useCount", 0),
        "aiApi": "deepseek",
        "opening": opening_text,
        "openingStatements": opening_statements,
        "systemPrompt": full_prompt,
        "author": work.get("author", ""),
        "models": ["deepseek-v4-flash"],
        "detailedIntro": work.get("summary", ""),
        "characters": role_config.get("npc_settings", []),
        "protagonist": {
            "name": protagonist.get("name", ""),
            "description": protagonist.get("setting", ""),
            "motivation": protagonist.get("core_motivation", ""),
        },
        "worldSetting": {
            "worldName": role_config.get("worldview_setting", {}).get("name", ""),
            "eraTech": role_config.get("worldview_setting", {}).get("era_background", ""),
            "coreConflict": role_config.get("worldview_setting", {}).get("core_conflict", ""),
            "toneAtmosphere": role_config.get("worldview_setting", {}).get("overall_atmosphere", ""),
            "mainPlot": role_config.get("main_plot", ""),
            "initialState": role_config.get("init_plot_status", ""),
        },
        "gameRules": role_config.get("play_rule", ""),
        "statusBar": role_config.get("status_bar", ""),
    }


def _build_work_response(work, perspective=None):
    return success_response(_build_work_data(work, perspective))


def _normalize_openings(payload):
    openings = payload.get("openingStatements") or payload.get("opening_statements")
    if openings and isinstance(openings, list):
        return [
            {"label": o.get("label", "").strip(), "text": o.get("text", "").strip()}
            for o in openings if o.get("text", "").strip()
        ]
    opening_text = payload.get("opening", "").strip()
    if opening_text:
        return [{"label": "默认开局", "text": opening_text}]
    return []


def _convert_world(ws):
    return {
        "name": ws.get("worldName", ""),
        "era_background": ws.get("eraTech", ""),
        "core_conflict": ws.get("coreConflict", ""),
        "overall_atmosphere": ws.get("toneAtmosphere", ""),
    }


def _convert_protagonist(p):
    return {
        "name": p.get("name", ""),
        "setting": p.get("description", ""),
        "core_motivation": p.get("motivation", ""),
    }


def _make_role_config(payload):
    return {
        "main_plot": payload.get("mainPlot", "").strip(),
        "play_rule": payload.get("gameRules", "").strip(),
        "status_bar": payload.get("statusBar", "").strip(),
        "npc_settings": payload.get("characters", []),
        "init_plot_status": payload.get("opening", "").strip(),
        "worldview_setting": _convert_world(payload.get("worldSetting", {})),
        "protagonist_setting": _convert_protagonist(payload.get("protagonist", {})),
    }


@chat_bp.post("/chat/work/upload-cover")
def upload_cover():
    import os, uuid
    from werkzeug.utils import secure_filename
    from flask import current_app

    if 'file' not in request.files:
        raise AppError(ErrorCode.PARAM_INVALID, "请选择文件")
    file = request.files['file']
    if not file.filename:
        raise AppError(ErrorCode.PARAM_INVALID, "请选择文件")

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
        raise AppError(ErrorCode.PARAM_INVALID, "不支持的图片格式")

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'covers')
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    url = f"/uploads/covers/{filename}"
    return success_response({"url": url})


@chat_bp.post("/chat/work/create")
@jwt_required()
def create_work():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "作品名称不能为空")
    desc = payload.get("desc", "").strip()
    if not desc:
        raise AppError(ErrorCode.PARAM_INVALID, "简介不能为空")

    openings = _normalize_openings(payload)
    opening = payload.get("opening", "").strip() or (openings[0]["text"] if openings else "")
    role_config = _make_role_config(payload)

    work_id = execute(
        "INSERT INTO t_work_card (user_id, name, `desc`, cover, author, summary, "
        "opening, openings, tags, role_config, content, use_count, status) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (
            user_id, name, desc, payload.get("icon", "").strip(),
            payload.get("author", "").strip(), payload.get("detailedIntro", "").strip(),
            opening, json.dumps(openings, ensure_ascii=False),
            json.dumps(payload.get("tags", []), ensure_ascii=False),
            json.dumps(role_config, ensure_ascii=False),
            json.dumps(payload.get("content", {}), ensure_ascii=False),
            0, 1,
        ),
    )
    invalidate_work(0)  # invalidate lists and home
    return success_response({"id": work_id, "message": "创建成功"})


@chat_bp.put("/chat/work/<int:work_id>")
@jwt_required()
def update_work(work_id: int):
    user_id = int(get_jwt_identity())

    existing = query_one(
        f"SELECT {_WORK_SELECT} FROM t_work_card WHERE id = %s", (work_id,)
    )
    if not existing:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在")
    if existing["user_id"] != user_id:
        raise AppError(ErrorCode.FORBIDDEN, "只能编辑自己的作品")

    payload = request.get_json(silent=True) or {}
    updates = {}
    values = []

    for col, key in [("name", "name"), ("desc", "desc"), ("cover", "icon"),
                     ("author", "author"), ("summary", "detailedIntro")]:
        if key in payload:
            updates[col] = "%s"
            values.append(payload[key])

    if "openingStatements" in payload:
        openings = _normalize_openings(payload)
        updates["openings"] = "%s"
        values.append(json.dumps(openings, ensure_ascii=False))
        if openings:
            if "opening" not in payload:
                updates["opening"] = "%s"
                values.append(openings[0]["text"])
    elif "opening" in payload:
        updates["opening"] = "%s"
        values.append(payload["opening"].strip())

    role_config = _parse_json(existing.get("role_config"), {})
    role_changed = False
    for pl_key, rc_key in [("characters", "npc_settings"), ("gameRules", "play_rule"),
                           ("statusBar", "status_bar")]:
        if pl_key in payload:
            role_config[rc_key] = payload[pl_key]
            role_changed = True
    if "protagonist" in payload:
        role_config["protagonist_setting"] = _convert_protagonist(payload["protagonist"])
        role_changed = True
    if "worldSetting" in payload:
        role_config["worldview_setting"] = _convert_world(payload["worldSetting"])
        role_changed = True
    if "opening" in payload:
        role_config["init_plot_status"] = payload["opening"]
        role_changed = True
    if role_changed:
        updates["role_config"] = "%s"
        values.append(json.dumps(role_config, ensure_ascii=False))

    if not updates:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    set_clause = ", ".join(f"`{k}` = %s" for k in updates)
    values.append(work_id)
    execute(f"UPDATE t_work_card SET {set_clause} WHERE id = %s", tuple(values))
    invalidate_work(work_id)
    return success_response({"message": "更新成功"})


@chat_bp.get("/chat/work/<int:work_id>")
def get_work_chat_config(work_id: int):
    user_id = _try_get_user_id()
    is_admin = False
    if user_id:
        from ...api.v1.admin import _check_admin
        try:
            _check_admin(user_id)
            is_admin = True
        except AppError:
            pass

    perspective_name = request.args.get("perspective", "").strip()

    # Serve from cache for default (non-admin, no perspective) requests
    if not is_admin and not perspective_name:
        cached = get_cached_work(work_id)
        if cached:
            return success_response(cached)

    status_cond = "IN (1, 2)" if is_admin else "= 1"
    work = query_one(
        f"SELECT {_WORK_SELECT} FROM t_work_card WHERE id = %s AND status {status_cond}",
        (work_id,),
    )
    if not work:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已下架")

    perspective = None
    if perspective_name:
        role_config = _parse_json(work.get("role_config"), {})
        all_candidates = list(role_config.get("npc_settings", []))
        protagonist = role_config.get("protagonist_setting", {})
        if protagonist.get("name"):
            all_candidates.append(protagonist)
        for c in all_candidates:
            if c.get("name") == perspective_name:
                perspective = c
                break

    data = _build_work_data(work, perspective)

    if not is_admin and not perspective_name:
        set_cached_work(work_id, data)

    return success_response(data)


@chat_bp.put("/chat/work/<int:work_id>/config")
@jwt_required()
def update_work_config(work_id: int):
    from ...api.v1.admin import _check_admin

    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    work = query_one(
        f"SELECT {_WORK_SELECT} FROM t_work_card WHERE id = %s AND status = 1",
        (work_id,),
    )
    if not work:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已下架")

    payload = request.get_json(silent=True) or {}
    updates = {}
    values = []

    if "detailedIntro" in payload:
        updates["summary"] = "%s"
        values.append(payload["detailedIntro"])

    role_config = _parse_json(work.get("role_config"), {})
    role_changed = False
    for pl_key, rc_key in [("characters", "npc_settings"), ("gameRules", "play_rule"),
                           ("statusBar", "status_bar")]:
        if pl_key in payload:
            role_config[rc_key] = payload[pl_key]
            role_changed = True
    if "protagonist" in payload:
        role_config["protagonist_setting"] = _convert_protagonist(payload["protagonist"])
        role_changed = True
    if "worldSetting" in payload:
        role_config["worldview_setting"] = _convert_world(payload["worldSetting"])
        role_changed = True

    if "openingStatements" in payload:
        openings = _normalize_openings(payload)
        updates["openings"] = "%s"
        values.append(json.dumps(openings, ensure_ascii=False))
        if openings:
            if "opening" not in payload:
                updates["opening"] = "%s"
                values.append(openings[0]["text"])
                role_config["init_plot_status"] = openings[0]["text"]
                role_changed = True
    elif "opening" in payload:
        updates["opening"] = "%s"
        values.append(payload["opening"])
        role_config["init_plot_status"] = payload["opening"]
        role_changed = True

    if role_changed:
        updates["role_config"] = "%s"
        values.append(json.dumps(role_config, ensure_ascii=False))

    if not updates:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    set_clause = ", ".join(f"`{k}` = %s" for k in updates)
    values.append(work_id)
    execute(f"UPDATE t_work_card SET {set_clause} WHERE id = %s", tuple(values))
    invalidate_work(work_id)
    return success_response({"message": "配置已保存"})


@chat_bp.get("/chat/works")
def list_chat_works():
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    keyword = request.args.get("keyword", "")
    sort_type = request.args.get("sortType", "hot")
    rank_type = request.args.get("rankType", "total")
    category_id = request.args.get("categoryId", type=int)

    user_id = _try_get_user_id()
    is_admin = False
    if user_id:
        from ...api.v1.admin import _check_admin
        try:
            _check_admin(user_id)
            is_admin = True
        except AppError:
            pass

    where = ["w.status IN (1, 2)"] if is_admin else ["w.status = 1"]
    params = []

    if keyword:
        where.append("(w.name LIKE %s OR w.`desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if category_id:
        where.append("w.category = %s")
        params.append(category_id)

    where_clause = " AND ".join(where)

    _RANK_DATE = {
        "daily": "w.id = s.card_id AND s.card_type = 'work' AND s.stat_date = CURDATE()",
        "weekly": "w.id = s.card_id AND s.card_type = 'work' AND s.stat_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)",
        "monthly": "w.id = s.card_id AND s.card_type = 'work' AND s.stat_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)",
    }

    if rank_type in _RANK_DATE:
        join_clause = f"INNER JOIN t_cards_daily_stat s ON {_RANK_DATE[rank_type]}"
        count_sql = (
            f"SELECT COUNT(*) AS total FROM ("
            f"SELECT w.id FROM t_work_card w {join_clause} "
            f"WHERE {where_clause} GROUP BY w.id"
            f") sub"
        )
        data_sql = (
            f"SELECT w.id, w.name, w.cover, w.`desc`, w.use_count AS useCount, "
            f"w.create_time AS createTime, "
            f"COALESCE(SUM(s.chat_count), 0) AS rank_score "
            f"FROM t_work_card w {join_clause} "
            f"WHERE {where_clause} GROUP BY w.id "
            f"ORDER BY rank_score DESC, w.id DESC LIMIT %s OFFSET %s"
        )
    else:
        count_sql = f"SELECT COUNT(*) AS total FROM t_work_card w WHERE {where_clause}"
        order_map = {"hot": "use_count DESC, id DESC", "new": "create_time DESC, id DESC"}
        order_clause = order_map.get(sort_type, "use_count DESC, id DESC")
        data_sql = (
            f"SELECT w.id, w.name, w.cover, w.`desc`, w.use_count AS useCount, "
            f"w.create_time AS createTime "
            f"FROM t_work_card w WHERE {where_clause} "
            f"ORDER BY {order_clause} LIMIT %s OFFSET %s"
        )

    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]

    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))

    result = [{
        "id": item["id"],
        "name": item["name"],
        "icon": item.get("cover", ""),
        "desc": item.get("desc", ""),
        "useCount": item.get("useCount", 0),
        "isFree": True,
        "isVip": False,
        "createTime": str(item.get("createTime", "")),
    } for item in items]

    return page_response(result, total=total, page_num=page_num, page_size=page_size)


# ---- Work Collect / Favorite ----

@chat_bp.post("/chat/work/<int:work_id>/collect")
@jwt_required()
def collect_work(work_id: int):
    user_id = int(get_jwt_identity())
    existing = query_one(
        "SELECT id FROM t_work_collect WHERE user_id = %s AND work_id = %s",
        (user_id, work_id),
    )
    if existing:
        execute("DELETE FROM t_work_collect WHERE id = %s", (existing["id"],))
        return success_response({"collected": False, "message": "已取消收藏"})
    else:
        execute(
            "INSERT INTO t_work_collect (user_id, work_id) VALUES (%s, %s)",
            (user_id, work_id),
        )
        return success_response({"collected": True, "message": "收藏成功"})


@chat_bp.get("/chat/work/<int:work_id>/collect")
def get_collect_status(work_id: int):
    user_id = _try_get_user_id()
    if not user_id:
        return success_response({"collected": False})
    existing = query_one(
        "SELECT id FROM t_work_collect WHERE user_id = %s AND work_id = %s",
        (user_id, work_id),
    )
    return success_response({"collected": bool(existing)})


@chat_bp.get("/user/work/collected")
@jwt_required()
def list_collected_works():
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)

    total_row = query_one(
        "SELECT COUNT(*) AS total FROM t_work_collect WHERE user_id = %s",
        (user_id,),
    )
    total = total_row["total"]

    rows = query_all(
        "SELECT wc.work_id, w.name, w.`desc`, w.cover, wc.create_time AS collectTime "
        "FROM t_work_collect wc "
        "JOIN t_work_card w ON w.id = wc.work_id "
        "WHERE wc.user_id = %s AND w.status = 1 "
        "ORDER BY wc.create_time DESC "
        "LIMIT %s OFFSET %s",
        (user_id, page_size, (page_num - 1) * page_size),
    )

    items = [{
        "id": row["work_id"],
        "name": row["name"],
        "desc": row.get("desc", ""),
        "icon": row.get("cover", ""),
        "isFree": True,
        "isVip": False,
        "useCount": 0,
        "collectTime": str(row.get("collectTime", "")),
    } for row in rows]

    return page_response(items, total=total, page_num=page_num, page_size=page_size)


# ---- User Work CRUD (non-admin) ----


@chat_bp.get("/user/work/my")
@jwt_required()
def get_my_works():
    """List the current user's own works."""
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)

    total_row = query_one(
        "SELECT COUNT(*) AS total FROM t_work_card WHERE user_id = %s AND status = 1",
        (user_id,),
    )
    total = total_row["total"]

    rows = query_all(
        "SELECT id, name, `desc`, cover, author, category, language, "
        "use_count AS useCount, status, create_time AS createTime "
        "FROM t_work_card "
        "WHERE user_id = %s AND status = 1 "
        "ORDER BY create_time DESC "
        "LIMIT %s OFFSET %s",
        (user_id, page_size, (page_num - 1) * page_size),
    )

    items = [{
        "id": row["id"],
        "name": row["name"],
        "desc": row.get("desc", ""),
        "cover": row.get("cover", ""),
        "author": row.get("author", ""),
        "category": row.get("category", 0),
        "language": row.get("language", "zh-Hans"),
        "useCount": row.get("useCount", 0),
        "status": row.get("status", 1),
        "createTime": str(row.get("createTime", "")),
    } for row in rows]

    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@chat_bp.delete("/chat/work/<int:work_id>")
@jwt_required()
def delete_my_work(work_id: int):
    """Delete own work card with cascading cleanup."""
    user_id = int(get_jwt_identity())

    owner = query_one(
        "SELECT user_id FROM t_work_card WHERE id = %s AND status = 1",
        (work_id,),
    )
    if not owner:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已删除")
    if owner["user_id"] != user_id:
        raise AppError(ErrorCode.FORBIDDEN, "只能删除自己的作品")

    execute("DELETE FROM t_work_collect WHERE work_id = %s", (work_id,))
    execute(
        "DELETE FROM t_conversation WHERE entity_id = %s AND entity_type = 'work'",
        (work_id,),
    )
    execute("DELETE FROM t_work_card WHERE id = %s", (work_id,))
    invalidate_work(work_id)
    return success_response({"message": "删除成功"})
