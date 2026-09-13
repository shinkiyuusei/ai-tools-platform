"""AI provider / model data access layer.

Reads ``t_ai_provider`` + ``t_ai_model`` with a short in-memory cache so the
hot chat path (``get_adapter``) doesn't hit MySQL on every request.

Cache is invalidated by :func:`invalidate_cache` — called by admin write
endpoints after any provider/model mutation.
"""

from __future__ import annotations

import time
from typing import Optional

from ...utils.mysql import execute, query_all, query_one

#: Cache TTL in seconds. Trade-off: longer = fewer DB hits, shorter = faster
#: propagation of admin edits to the chat path.
_CACHE_TTL = 30.0

_cache: dict = {"ts": 0.0, "providers": None, "by_key": None}


def invalidate_cache() -> None:
    """Drop the in-memory cache. Call after any write."""
    _cache["ts"] = 0.0
    _cache["providers"] = None
    _cache["by_key"] = None


def _is_stale() -> bool:
    return (time.time() - _cache["ts"]) > _CACHE_TTL


def _load() -> None:
    if not _is_stale() and _cache["providers"] is not None:
        return
    rows = query_all(
        "SELECT id, `key`, name, adapter, base_url, api_key, "
        "is_active, sort_order FROM t_ai_provider ORDER BY sort_order ASC, id ASC",
        (),
    )
    providers = []
    by_key: dict[str, dict] = {}
    for r in rows:
        pid = r["id"]
        models = query_all(
            "SELECT id, provider_id, model_id, display_name, is_active, "
            "is_default, sort_order FROM t_ai_model WHERE provider_id = %s "
            "ORDER BY is_default DESC, sort_order ASC, id ASC",
            (pid,),
        )
        r["models"] = models or []
        providers.append(r)
        by_key[r["key"]] = r
    _cache["providers"] = providers
    _cache["by_key"] = by_key
    _cache["ts"] = time.time()


def list_all_providers() -> list[dict]:
    """Return all provider rows (including inactive) with nested models."""
    _load()
    return _cache["providers"] or []


def list_active_providers() -> list[dict]:
    """Return only active providers + active models, for the chat UI."""
    _load()
    out = []
    for p in _cache["providers"] or []:
        if not p.get("is_active"):
            continue
        out.append({
            "key": p["key"],
            "name": p["name"],
            "models": [
                {"key": m["model_id"], "label": m["display_name"], "isDefault": bool(m["is_default"])}
                for m in p["models"]
                if m.get("is_active")
            ],
        })
    return out


def get_provider_by_key(key: str) -> Optional[dict]:
    """Return raw provider row (with plain api_key) for adapter construction."""
    _load()
    return (_cache["by_key"] or {}).get(key)


def get_default_provider_key() -> Optional[str]:
    """Return the first active provider's key, or None when table is empty."""
    _load()
    for p in _cache["providers"] or []:
        if p.get("is_active"):
            return p["key"]
    return None


def fetch_models_from_upstream(base_url: str, api_key: str, extra_headers: dict | None = None) -> list[dict]:
    """SillyTavern-style GET ``{base_url}/models`` with Bearer key.

    Returns ``[{"id": str, "name": str}, ...]`` (normalised from OpenAI shape).
    Raises on non-2xx or bad JSON.
    """
    import requests
    from .url_utils import join_url

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if extra_headers:
        headers.update(extra_headers)

    url = join_url(base_url, "/models")
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    body = r.json() or {}
    raw = body.get("data") if isinstance(body, dict) else None
    if not isinstance(raw, list):
        raw = body if isinstance(body, list) else []
    models = []
    for item in raw:
        if isinstance(item, str):
            models.append({"id": item, "name": item})
        elif isinstance(item, dict) and item.get("id"):
            models.append({"id": item["id"], "name": item.get("name") or item["id"]})
    return models


def replace_provider_models(provider_id: int, models: list[dict]) -> None:
    """Replace all rows in ``t_ai_model`` for *provider_id* with *models*.

    Existing user-defined rows are wiped — same behaviour as SillyTavern's
    ``saveModelList`` which clears ``.model_custom_select`` before refill.
    """
    execute("DELETE FROM t_ai_model WHERE provider_id = %s", (provider_id,))
    if not models:
        return
    rows = []
    for i, m in enumerate(models):
        rows.append((
            provider_id,
            m.get("id", ""),
            m.get("name") or m.get("id", ""),
            1,                                   # is_active
            1 if i == 0 else 0,                  # is_default: first wins
            i,                                   # sort_order
        ))
    for row in rows:
        execute(
            "INSERT INTO t_ai_model "
            "(provider_id, model_id, display_name, is_active, is_default, sort_order) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            row,
        )
