"""User-owned prompt presets, including SillyTavern OpenAI preset JSON."""

import json

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...utils.mysql import execute, query_all, query_one, transaction
from ...utils.response import success_response
from ...utils.snowflake import generate_id

prompt_preset_bp = Blueprint("prompt_preset", __name__)


def _decode(row):
    data = dict(row)
    data["id"] = str(data["id"])
    raw = data.pop("preset_json", "{}")
    try:
        data["preset"] = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        data["preset"] = {}
    data["is_default"] = bool(data.get("is_default"))
    return data


def _validate(payload):
    name = str(payload.get("name") or "").strip()[:120]
    preset = payload.get("preset")
    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "预设名称不能为空")
    if not isinstance(preset, dict):
        raise AppError(ErrorCode.PARAM_INVALID, "预设必须是 JSON 对象")
    prompts = preset.get("prompts", [])
    if prompts is not None and not isinstance(prompts, list):
        raise AppError(ErrorCode.PARAM_INVALID, "prompts 必须是数组")
    return name, json.dumps(preset, ensure_ascii=False)


@prompt_preset_bp.get("/prompt-presets")
@jwt_required()
def list_presets():
    uid = int(get_jwt_identity())
    rows = query_all(
        "SELECT id,name,preset_json,is_default,create_time,update_time "
        "FROM t_prompt_preset WHERE user_id=%s ORDER BY is_default DESC,update_time DESC",
        (uid,),
    )
    return success_response({"list": [_decode(row) for row in rows]})


@prompt_preset_bp.post("/prompt-presets")
@jwt_required()
def create_preset():
    uid = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    name, raw = _validate(payload)
    if query_one("SELECT id FROM t_prompt_preset WHERE user_id=%s AND name=%s", (uid, name)):
        raise AppError(ErrorCode.PARAM_INVALID, "同名预设已存在")
    preset_id = generate_id()
    execute(
        "INSERT INTO t_prompt_preset(id,user_id,name,preset_json,is_default) VALUES(%s,%s,%s,%s,%s)",
        (preset_id, uid, name, raw, int(bool(payload.get("isDefault")))),
    )
    if payload.get("isDefault"):
        execute("UPDATE t_prompt_preset SET is_default=(id=%s) WHERE user_id=%s", (preset_id, uid))
    return success_response({"id": str(preset_id)})


@prompt_preset_bp.put("/prompt-presets/<int:preset_id>")
@jwt_required()
def update_preset(preset_id):
    uid = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    if not query_one("SELECT id FROM t_prompt_preset WHERE id=%s AND user_id=%s", (preset_id, uid)):
        raise AppError(ErrorCode.NOT_FOUND, "预设不存在")
    name, raw = _validate(payload)
    execute(
        "UPDATE t_prompt_preset SET name=%s,preset_json=%s WHERE id=%s AND user_id=%s",
        (name, raw, preset_id, uid),
    )
    return success_response(None, "保存成功")


@prompt_preset_bp.post("/prompt-presets/<int:preset_id>/default")
@jwt_required()
def set_default(preset_id):
    uid = int(get_jwt_identity())
    if not query_one("SELECT id FROM t_prompt_preset WHERE id=%s AND user_id=%s", (preset_id, uid)):
        raise AppError(ErrorCode.NOT_FOUND, "预设不存在")
    with transaction() as cur:
        cur.execute("UPDATE t_prompt_preset SET is_default=0 WHERE user_id=%s", (uid,))
        cur.execute("UPDATE t_prompt_preset SET is_default=1 WHERE id=%s AND user_id=%s", (preset_id, uid))
    return success_response(None, "已设为默认")


@prompt_preset_bp.delete("/prompt-presets/<int:preset_id>")
@jwt_required()
def delete_preset(preset_id):
    uid = int(get_jwt_identity())
    execute("DELETE FROM t_prompt_preset WHERE id=%s AND user_id=%s", (preset_id, uid))
    return success_response(None, "删除成功")
