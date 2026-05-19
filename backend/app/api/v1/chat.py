"""
Chat API endpoints for AI chat works.
"""
import json
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...utils.mysql import query_one, execute
from ...utils.response import success_response
from ...core.errors import AppError, ErrorCode
from ...services.chat.prompt_builder import build_enhanced_system_prompt

chat_bp = Blueprint("chat", __name__)


def _parse_config(tool):
    """Parse form_config JSON from a tool row."""
    if not tool or not tool.get("form_config"):
        return {}
    try:
        config = json.loads(tool["form_config"])
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(config, dict):
        return {}
    return config


def _build_work_response(tool, config, perspective=None):
    """Build the full work response dict from tool row and parsed config."""
    work_name = tool["name"]

    # Build the enhanced full system prompt from rich data
    full_prompt = build_enhanced_system_prompt(work_name, config, perspective)

    # When perspective is swapped, hide the static opening line since it was
    # written for the default protagonist. The opening is instead woven into
    # the system prompt so the AI can reinterpret it from the new perspective.
    protagonist_name = config.get("protagonist", {}).get("name", "").strip()
    perspective_name = perspective.get("name", "").strip() if perspective else ""
    raw_opening = config.get("opening", "")
    if perspective_name and perspective_name != protagonist_name:
        raw_opening = ""

    return success_response({
        "id": tool["id"],
        "name": work_name,
        "icon": tool.get("icon", ""),
        "desc": tool.get("desc", ""),
        "isFree": tool.get("isFree", 1),
        "isVip": tool.get("isVip", 0),
        "useCount": tool.get("useCount", 0),
        "aiApi": tool.get("ai_api", "deepseek"),
        "opening": raw_opening,
        "systemPrompt": full_prompt,
        "author": config.get("author", ""),
        "rating": config.get("rating", 0),
        "models": config.get("models", ["deepseek-v4-flash"]),
        "detailedIntro": config.get("detailedIntro", ""),
        "characters": config.get("characters", []),
        "protagonist": config.get("protagonist", {
            "name": "", "description": "", "motivation": ""
        }),
        "worldSetting": config.get("worldSetting", {
            "worldName": "", "eraTech": "", "coreConflict": "",
            "toneAtmosphere": "", "mainPlot": "", "initialState": ""
        }),
        "gameRules": config.get("gameRules", ""),
        "statusBar": config.get("statusBar", ""),
    })


@chat_bp.post("/chat/work/upload-cover")
def upload_cover():
    """Upload cover image for work card."""
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
    """Create a new work card with full form data."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    name = payload.get("name", "").strip()
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "作品名称不能为空")

    desc = payload.get("desc", "").strip()
    if not desc:
        raise AppError(ErrorCode.PARAM_INVALID, "简介不能为空")

    detailed_intro = payload.get("detailedIntro", "").strip()
    characters = payload.get("characters", [])
    protagonist = payload.get("protagonist", {})
    world_setting = payload.get("worldSetting", {})
    game_rules = payload.get("gameRules", "").strip()
    status_bar = payload.get("statusBar", "").strip()
    opening = payload.get("opening", "").strip()
    icon = payload.get("icon", "").strip()

    form_config = json.dumps({
        "author": payload.get("author", ""),
        "rating": payload.get("rating", 0),
        "detailedIntro": detailed_intro,
        "characters": characters,
        "protagonist": protagonist,
        "worldSetting": world_setting,
        "gameRules": game_rules,
        "statusBar": status_bar,
        "opening": opening,
        "models": payload.get("models", ["deepseek-v4-flash"]),
    }, ensure_ascii=False)

    work_id = execute(
        "INSERT INTO t_ai_tool (name, icon, `desc`, category_id, tag_ids, form_config, ai_api, is_free, is_vip, use_count, sort_order, status) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (name, icon, desc, 2, "", form_config, "deepseek", 1, 0, 0, 99, 1),
    )
    return success_response({"id": work_id, "message": "创建成功"})


@chat_bp.put("/chat/work/<int:work_id>")
@jwt_required()
def update_work(work_id: int):
    """Update an existing work card."""
    user_id = int(get_jwt_identity())
    existing = query_one("SELECT id FROM t_ai_tool WHERE id = %s", (work_id,))
    if not existing:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在")

    payload = request.get_json(silent=True) or {}
    fields = []
    params = []

    if "name" in payload:
        fields.append("name = %s")
        params.append(payload["name"])
    if "desc" in payload:
        fields.append("`desc` = %s")
        params.append(payload["desc"])
    if "icon" in payload:
        fields.append("icon = %s")
        params.append(payload["icon"])

    # Rebuild form_config
    existing_tool = query_one(
        "SELECT form_config FROM t_ai_tool WHERE id = %s", (work_id,)
    )
    import json as _json
    config = {}
    if existing_tool and existing_tool.get("form_config"):
        try:
            config = _json.loads(existing_tool["form_config"])
        except (_json.JSONDecodeError, TypeError):
            config = {}

    for key in ["characters", "protagonist", "worldSetting", "gameRules", "statusBar", "opening", "detailedIntro", "author", "rating", "models"]:
        if key in payload:
            config[key] = payload[key]

    fields.append("form_config = %s")
    params.append(_json.dumps(config, ensure_ascii=False))

    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    params.append(work_id)
    execute(f"UPDATE t_ai_tool SET {', '.join(fields)} WHERE id = %s", tuple(params))
    return success_response({"message": "更新成功"})


@chat_bp.get("/chat/work/<int:work_id>")
def get_work_chat_config(work_id: int):
    """Get work chat configuration including opening lines and system prompt.
    Accepts optional query param ?perspective=<角色名> to build the system
    prompt for a different playable character."""
    tool = query_one(
        "SELECT id, name, icon, `desc`, use_desc, form_config, ai_api, "
        "is_free AS isFree, is_vip AS isVip, use_count AS useCount "
        "FROM t_ai_tool WHERE id = %s AND status = 1",
        (work_id,)
    )
    if not tool:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已下架")

    config = _parse_config(tool)

    # resolve optional perspective parameter
    perspective_name = request.args.get("perspective", "").strip()
    perspective = None
    if perspective_name:
        all_candidates = list(config.get("characters", []))
        protagonist = config.get("protagonist", {})
        if protagonist.get("name"):
            all_candidates.append(protagonist)
        for c in all_candidates:
            if c.get("name") == perspective_name:
                perspective = c
                break

    return _build_work_response(tool, config, perspective)


@chat_bp.put("/chat/work/<int:work_id>/config")
@jwt_required()
def update_work_config(work_id: int):
    """Save rich structured config for a chat work (admin only)."""
    from ...api.v1.admin import _check_admin

    user_id = int(get_jwt_identity())
    _check_admin(user_id)

    tool = query_one(
        "SELECT id, form_config FROM t_ai_tool WHERE id = %s AND status = 1",
        (work_id,)
    )
    if not tool:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已下架")

    existing = _parse_config(tool)
    payload = request.get_json(silent=True) or {}

    rich_fields = (
        "detailedIntro", "characters", "protagonist", "worldSetting",
        "gameRules", "statusBar", "opening", "systemPrompt"
    )
    for key in rich_fields:
        if key in payload:
            existing[key] = payload[key]

    execute(
        "UPDATE t_ai_tool SET form_config = %s WHERE id = %s",
        (json.dumps(existing, ensure_ascii=False), work_id)
    )
    return success_response({"message": "配置已保存"})


@chat_bp.get("/chat/works")
def list_chat_works():
    """List all available AI chat works."""
    from ...utils.mysql import query_all

    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    keyword = request.args.get("keyword", "")
    sort_type = request.args.get("sortType", "hot")
    category_id = request.args.get("categoryId", type=int)

    where = ["status = 1"]
    params = []

    if keyword:
        where.append("(name LIKE %s OR `desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if category_id:
        where.append("category_id = %s")
        params.append(category_id)

    where_clause = " AND ".join(where)

    order_map = {
        "hot": "use_count DESC",
        "new": "create_time DESC",
    }
    order_clause = order_map.get(sort_type, "use_count DESC")

    count_sql = f"SELECT COUNT(*) AS total FROM t_ai_tool WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]

    data_sql = (
        f"SELECT id, name, icon, `desc`, use_count AS useCount, is_free AS isFree, "
        f"is_vip AS isVip, category_id AS categoryId, create_time AS createTime "
        f"FROM t_ai_tool WHERE {where_clause} "
        f"ORDER BY {order_clause} LIMIT %s OFFSET %s"
    )
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))

    from ...utils.response import page_response
    return page_response(items, total=total, page_num=page_num, page_size=page_size)
