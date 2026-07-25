"""
World Info REST API — CRUD for lore entries attached to work / character cards.
"""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...services.world_info import (
    create_entry, update_entry, delete_entry, get_entry, list_entries,
)
from ...utils.mysql import query_one
from ...utils.response import success_response

world_info_bp = Blueprint("world_info", __name__)


# ---------------------------------------------------------------------------
#  Ownership helper
# ---------------------------------------------------------------------------

def _check_ownership(entity_type: str, entity_id: int, user_id: int) -> None:
    """Raise AppError if the caller does not own the entity or is not admin."""
    table = "t_work_card" if entity_type == "work" else "t_character_card"
    row = query_one(
        f"SELECT user_id FROM {table} WHERE id = %s AND status = 1",
        (entity_id,),
    )
    if not row:
        raise AppError(ErrorCode.NOT_FOUND, f"{entity_type} 不存在")
    if int(row["user_id"]) != user_id:
        # Check admin override
        user = query_one("SELECT vip_level FROM t_user WHERE id = %s", (user_id,))
        if not user or (user.get("vip_level", 0) or 0) < 2:
            raise AppError(ErrorCode.FORBIDDEN, "无权操作此实体的世界设定")


# ---------------------------------------------------------------------------
#  Endpoints
# ---------------------------------------------------------------------------

@world_info_bp.get("/world-info/entries")
def api_list_entries():
    """List entries for an entity (public)."""
    entity_type = request.args.get("entityType", "work").strip()
    entity_id = request.args.get("entityId", 0, type=int)
    if not entity_id:
        raise AppError(ErrorCode.PARAM_INVALID, "entityId 不能为空")
    if entity_type not in ("work", "character"):
        raise AppError(ErrorCode.PARAM_INVALID, "entityType 必须是 work 或 character")
    entries = list_entries(entity_type, entity_id)
    return success_response(entries)


@world_info_bp.get("/world-info/entry/<int:entry_id>")
def api_get_entry(entry_id: int):
    """Get a single entry (public)."""
    entry = get_entry(entry_id)
    if not entry:
        raise AppError(ErrorCode.NOT_FOUND, "条目不存在")
    return success_response(entry)


@world_info_bp.post("/world-info/entry")
@jwt_required()
def api_create_entry():
    """Create a world-info entry.  Caller must own the target entity."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    entity_type = (payload.get("entityType") or "work").strip()
    entity_id = payload.get("entityId") or 0
    keys = payload.get("keys")
    content = (payload.get("content") or "").strip()

    if entity_type not in ("work", "character"):
        raise AppError(ErrorCode.PARAM_INVALID, "entityType 必须是 work 或 character")
    if not entity_id:
        raise AppError(ErrorCode.PARAM_INVALID, "entityId 不能为空")
    if not isinstance(keys, list) or not keys:
        raise AppError(ErrorCode.PARAM_INVALID, "keys 必须是非空关键词数组")
    if not content:
        raise AppError(ErrorCode.PARAM_INVALID, "content 不能为空")

    _check_ownership(entity_type, entity_id, user_id)

    entry_id = create_entry(
        entity_type=entity_type,
        entity_id=entity_id,
        keys=keys,
        content=content,
        comment=(payload.get("comment") or "").strip()[:200],
        selective=bool(payload.get("selective", False)),
        constant=bool(payload.get("constant", False)),
        recursion=bool(payload.get("recursion", False)),
        position=payload.get("position", "before_char"),
        depth=payload.get("depth", 1),
        order=payload.get("order", 0),
        probability=payload.get("probability", 100),
        content_mode=payload.get("contentMode") or None,
        character_name=payload.get("characterName") or None,
    )
    return success_response({"id": entry_id})


@world_info_bp.put("/world-info/entry/<int:entry_id>")
@jwt_required()
def api_update_entry(entry_id: int):
    """Update a world-info entry."""
    user_id = int(get_jwt_identity())
    entry = get_entry(entry_id)
    if not entry:
        raise AppError(ErrorCode.NOT_FOUND, "条目不存在")
    _check_ownership(entry["entity_type"], entry["entity_id"], user_id)

    payload = request.get_json(silent=True) or {}
    update_entry(entry_id, **payload)
    return success_response(None, "更新成功")


@world_info_bp.delete("/world-info/entry/<int:entry_id>")
@jwt_required()
def api_delete_entry(entry_id: int):
    """Delete a world-info entry."""
    user_id = int(get_jwt_identity())
    entry = get_entry(entry_id)
    if not entry:
        raise AppError(ErrorCode.NOT_FOUND, "条目不存在")
    _check_ownership(entry["entity_type"], entry["entity_id"], user_id)

    delete_entry(entry_id)
    return success_response(None, "删除成功")
