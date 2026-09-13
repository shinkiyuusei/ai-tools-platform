"""Super-admin endpoints for AI provider & model management.

Mirrors the SillyTavern flow:

* ``GET /admin/ai-provider``                    → list providers (masked keys)
* ``POST /admin/ai-provider``                  → create provider (writes key)
* ``PUT /admin/ai-provider/<id>``               → update (key optional)
* ``DELETE /admin/ai-provider/<id>``            → delete + cascade models
* ``POST /admin/ai-provider/<id>/test``         → GET {base_url}/models health-check
* ``POST /admin/ai-provider/<id>/fetch-models`` → SillyTavern status pattern,
                                                 replace ``t_ai_model`` rows

* ``POST /admin/ai-model``                     → manually add a model row
* ``PUT /admin/ai-model/<id>``                 → edit
* ``DELETE /admin/ai-model/<id>``               → delete
"""

from __future__ import annotations

import json

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...services.ai.provider_repo import (
    fetch_models_from_upstream,
    invalidate_cache,
    list_all_providers,
    replace_provider_models,
)
from ...services.ai.secrets import looks_masked, mask_secret
from ...utils.crud import dynamic_update
from ...utils.mysql import execute, query_one
from ...utils.response import success_response

ai_provider_admin_bp = Blueprint("ai_provider_admin", __name__)


def _check_admin(user_id: int) -> None:
    user = query_one(
        "SELECT vip_level FROM t_user WHERE id = %s AND status = 1 AND is_delete = 0",
        (user_id,),
    )
    if not user or user["vip_level"] < 2:
        raise AppError(ErrorCode.FORBIDDEN, "无管理员权限")


def _require_admin() -> int:
    user_id = int(get_jwt_identity())
    _check_admin(user_id)
    return user_id


def _mask_provider(p: dict) -> dict:
    """Public-facing shape: api_key masked, models nested."""
    return {
        "id": p["id"],
        "key": p["key"],
        "name": p["name"],
        "adapter": p["adapter"],
        "baseUrl": p["base_url"],
        "apiKeyMasked": mask_secret(p.get("api_key", "")),
        "isActive": bool(p["is_active"]),
        "sortOrder": p["sort_order"],
        "createTime": p.get("create_time"),
        "updateTime": p.get("update_time"),
        "models": [
            {
                "id": m["id"],
                "modelId": m["model_id"],
                "displayName": m["display_name"],
                "isActive": bool(m["is_active"]),
                "isDefault": bool(m["is_default"]),
                "sortOrder": m["sort_order"],
            }
            for m in (p.get("models") or [])
        ],
    }


def _load_provider_or_404(provider_id: int) -> dict:
    p = query_one(
        "SELECT id, `key`, name, adapter, base_url, api_key, is_active, sort_order, "
        "create_time, update_time FROM t_ai_provider WHERE id = %s",
        (provider_id,),
    )
    if not p:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "AI 提供商不存在")
    return p


# ---- Provider CRUD ----

@ai_provider_admin_bp.get("/admin/ai-provider")
@jwt_required()
def list_providers():
    _require_admin()
    providers = list_all_providers()
    return success_response({"list": [_mask_provider(p) for p in providers]})


@ai_provider_admin_bp.post("/admin/ai-provider")
@jwt_required()
def create_provider():
    _require_admin()
    payload = request.get_json(silent=True) or {}

    key = (payload.get("key") or "").strip()
    name = (payload.get("name") or "").strip()
    base_url = (payload.get("baseUrl") or "").strip()
    api_key = (payload.get("apiKey") or "").strip()
    adapter = (payload.get("adapter") or "openai").strip()
    is_active = 1 if payload.get("isActive", True) else 0
    sort_order = int(payload.get("sortOrder", 0))

    if not key or not name or not base_url:
        raise AppError(ErrorCode.PARAM_INVALID, "key/name/baseUrl 不能为空")

    existing = query_one("SELECT id FROM t_ai_provider WHERE `key` = %s", (key,))
    if existing:
        raise AppError(ErrorCode.PARAM_INVALID, f"提供商 key 已存在: {key}")

    provider_id = execute(
        "INSERT INTO t_ai_provider (`key`, name, adapter, base_url, api_key, is_active, sort_order) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (key, name, adapter, base_url, api_key, is_active, sort_order),
    )
    invalidate_cache()
    return success_response({"id": provider_id, "message": "创建成功"})


@ai_provider_admin_bp.put("/admin/ai-provider/<int:provider_id>")
@jwt_required()
def update_provider(provider_id: int):
    _require_admin()
    _load_provider_or_404(provider_id)

    payload = request.get_json(silent=True) or {}
    fields = []
    params = []

    for json_key, db_col in (
        ("name", "name"),
        ("adapter", "adapter"),
        ("baseUrl", "base_url"),
        ("isActive", "is_active"),
        ("sortOrder", "sort_order"),
    ):
        if json_key in payload:
            fields.append(f"{db_col} = %s")
            params.append(
                1 if (json_key == "isActive" and payload[json_key]) else
                (0 if json_key == "isActive" else payload[json_key])
            )

    # API key handling: when omitted, keep current value. When submitted as
    # the masked preview (admin didn't actually change it), also keep. Only
    # write a new plaintext when a real new value was typed.
    submitted_key = payload.get("apiKey")
    if submitted_key is not None and not looks_masked(str(submitted_key)):
        fields.append("api_key = %s")
        params.append(str(submitted_key))

    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    params.append(provider_id)
    execute(
        f"UPDATE t_ai_provider SET {', '.join(fields)} WHERE id = %s",
        tuple(params),
    )
    invalidate_cache()
    return success_response({"message": "更新成功"})


@ai_provider_admin_bp.delete("/admin/ai-provider/<int:provider_id>")
@jwt_required()
def delete_provider(provider_id: int):
    _require_admin()
    _load_provider_or_404(provider_id)
    # t_ai_model rows cascade via FK ON DELETE CASCADE
    execute("DELETE FROM t_ai_provider WHERE id = %s", (provider_id,))
    invalidate_cache()
    return success_response({"message": "删除成功"})


# ---- Test connection + fetch models ----

@ai_provider_admin_bp.post("/admin/ai-provider/<int:provider_id>/test")
@jwt_required()
def test_provider(provider_id: int):
    """Health-check via GET {base_url}/models (SillyTavern status pattern)."""
    _require_admin()
    p = _load_provider_or_404(provider_id)
    try:
        models = fetch_models_from_upstream(p["base_url"], p["api_key"])
        return success_response({"ok": True, "modelCount": len(models)})
    except Exception as exc:
        return success_response({"ok": False, "error": str(exc)})


@ai_provider_admin_bp.post("/admin/ai-provider/test-connection")
@jwt_required()
def test_connection():
    """Health-check a provider draft before it is saved.

    Unlike ``/test`` this takes the values straight from the dialog, so an
    admin can verify a new provider without persisting a bad row first.

    ``apiKey`` may be blank — either because the admin is editing and did not
    retype it (send ``id`` so the stored key is reused), or because the admin
    pasted back the masked preview.
    """
    _require_admin()
    payload = request.get_json(silent=True) or {}

    base_url = (payload.get("baseUrl") or "").strip()
    api_key = (payload.get("apiKey") or "").strip()
    provider_id = payload.get("id")

    if not base_url:
        raise AppError(ErrorCode.PARAM_INVALID, "baseUrl 不能为空")
    if not base_url.startswith(("http://", "https://")):
        raise AppError(ErrorCode.PARAM_INVALID, "baseUrl 需以 http:// 或 https:// 开头")

    if (not api_key or looks_masked(api_key)) and provider_id:
        stored = _load_provider_or_404(int(provider_id))
        api_key = stored["api_key"] or ""

    try:
        models = fetch_models_from_upstream(base_url, api_key)
        return success_response({"ok": True, "modelCount": len(models)})
    except Exception as exc:
        return success_response({"ok": False, "error": str(exc)})


@ai_provider_admin_bp.post("/admin/ai-provider/<int:provider_id>/fetch-models")
@jwt_required()
def fetch_models(provider_id: int):
    """Replace this provider's t_ai_model rows with the upstream list."""
    _require_admin()
    p = _load_provider_or_404(provider_id)
    try:
        models = fetch_models_from_upstream(p["base_url"], p["api_key"])
    except Exception as exc:
        raise AppError(ErrorCode.GENERATE_FAILED, f"拉取模型失败: {exc}") from exc

    replace_provider_models(provider_id, models)
    invalidate_cache()
    return success_response({
        "message": "拉取成功",
        "count": len(models),
        "models": models,
    })


# ---- Manual model CRUD ----

@ai_provider_admin_bp.post("/admin/ai-model")
@jwt_required()
def create_model():
    _require_admin()
    payload = request.get_json(silent=True) or {}
    provider_id = int(payload.get("providerId") or 0)
    model_id = (payload.get("modelId") or "").strip()
    display_name = (payload.get("displayName") or "").strip() or model_id
    is_active = 1 if payload.get("isActive", True) else 0
    is_default = 1 if payload.get("isDefault", False) else 0
    sort_order = int(payload.get("sortOrder", 0))

    if not provider_id or not model_id:
        raise AppError(ErrorCode.PARAM_INVALID, "providerId/modelId 不能为空")
    _load_provider_or_404(provider_id)

    dup = query_one(
        "SELECT id FROM t_ai_model WHERE provider_id = %s AND model_id = %s",
        (provider_id, model_id),
    )
    if dup:
        raise AppError(ErrorCode.PARAM_INVALID, "该 provider 下 modelId 已存在")

    # Enforce at-most-one default per provider
    if is_default:
        execute(
            "UPDATE t_ai_model SET is_default = 0 WHERE provider_id = %s",
            (provider_id,),
        )

    model_db_id = execute(
        "INSERT INTO t_ai_model "
        "(provider_id, model_id, display_name, is_active, is_default, sort_order) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (provider_id, model_id, display_name, is_active, is_default, sort_order),
    )
    invalidate_cache()
    return success_response({"id": model_db_id, "message": "创建成功"})


@ai_provider_admin_bp.put("/admin/ai-model/<int:model_db_id>")
@jwt_required()
def update_model(model_db_id: int):
    _require_admin()
    existing = query_one(
        "SELECT id, provider_id FROM t_ai_model WHERE id = %s", (model_db_id,)
    )
    if not existing:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "模型不存在")

    payload = request.get_json(silent=True) or {}
    fields = []
    params = []
    for json_key, db_col in (
        ("modelId", "model_id"),
        ("displayName", "display_name"),
        ("isActive", "is_active"),
        ("sortOrder", "sort_order"),
    ):
        if json_key in payload:
            fields.append(f"{db_col} = %s")
            params.append(
                1 if (json_key == "isActive" and payload[json_key]) else
                (0 if json_key == "isActive" else payload[json_key])
            )

    if payload.get("isDefault"):
        execute(
            "UPDATE t_ai_model SET is_default = 0 WHERE provider_id = %s",
            (existing["provider_id"],),
        )
        fields.append("is_default = %s")
        params.append(1)
    elif "isDefault" in payload:
        fields.append("is_default = %s")
        params.append(0)

    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    params.append(model_db_id)
    execute(
        f"UPDATE t_ai_model SET {', '.join(fields)} WHERE id = %s",
        tuple(params),
    )
    invalidate_cache()
    return success_response({"message": "更新成功"})


@ai_provider_admin_bp.delete("/admin/ai-model/<int:model_db_id>")
@jwt_required()
def delete_model(model_db_id: int):
    _require_admin()
    execute("DELETE FROM t_ai_model WHERE id = %s", (model_db_id,))
    invalidate_cache()
    return success_response({"message": "删除成功"})
