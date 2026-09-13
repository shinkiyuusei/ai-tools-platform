"""One-time bootstrap for ``t_ai_provider`` / ``t_ai_model``.

Runs at app startup. Idempotent:

1. If tables don't exist yet, create them (so a fresh deploy works without
   the operator having to run the SQL migration manually first).
2. If ``t_ai_provider`` is empty, seed it from the env-var config in
   ``AI_BACKENDS`` so admins immediately see what's currently configured.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from ...utils.mysql import execute, query_one

log = logging.getLogger(__name__)

_MIGRATION_SQL_PATH = (
    Path(__file__).resolve().parents[4]
    / "database"
    / "migration_ai_provider_table.sql"
)


def _table_exists(name: str) -> bool:
    row = query_one(
        "SELECT COUNT(*) AS c FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = %s",
        (name,),
    )
    return bool(row and row.get("c"))


def _run_migration() -> None:
    if not _MIGRATION_SQL_PATH.exists():
        log.warning("AI provider migration SQL not found: %s", _MIGRATION_SQL_PATH)
        return
    sql = _MIGRATION_SQL_PATH.read_text(encoding="utf-8")
    # Strip single-line SQL comments (`-- ...` to end of line) before splitting,
    # otherwise a statement that begins with a comment line would be skipped.
    sql = re.sub(r"--[^\n]*", "", sql)
    # Split on `;`-terminated statements (good enough for these DDL files).
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    for stmt in statements:
        execute(stmt + ";", None)


def _seed_from_env() -> None:
    """Copy current env-var AI_BACKENDS into t_ai_provider/t_ai_model."""
    from flask import current_app

    backends = current_app.config.get("AI_BACKENDS", {}) or {}
    if not backends:
        return

    # Map of provider_key -> adapter name (which ChatAdapter class to use).
    adapter_for = {
        "deepseek": "deepseek",
        "openai": "openai",
        "gemini": "gemini",
    }

    sort = 1
    for key, cfg in backends.items():
        if not cfg.get("base_url"):
            continue
        provider_id = execute(
            "INSERT INTO t_ai_provider (`key`, name, adapter, base_url, api_key, is_active, sort_order) "
            "VALUES (%s, %s, %s, %s, %s, 1, %s)",
            (
                key,
                key.capitalize(),
                adapter_for.get(key, "openai"),
                cfg.get("base_url", ""),
                cfg.get("api_key", ""),
                sort,
            ),
        )
        sort += 1

        # Seed models from the env config
        for model_key in ("chat_model", "reasoner_model", "pro_model"):
            mid = cfg.get(model_key)
            if not mid:
                continue
            execute(
                "INSERT INTO t_ai_model "
                "(provider_id, model_id, display_name, is_active, is_default, sort_order) "
                "VALUES (%s, %s, %s, 1, %s, %s)",
                (
                    provider_id,
                    mid,
                    mid,
                    1 if model_key == "chat_model" else 0,
                    0 if model_key == "chat_model" else 1,
                ),
            )


def bootstrap_ai_providers() -> None:
    """Create tables if missing and seed from env when empty. Safe to re-run."""
    try:
        if not _table_exists("t_ai_provider"):
            _run_migration()
    except Exception:
        log.warning("t_ai_provider migration failed (non-fatal):", exc_info=True)
        return

    try:
        existing = query_one("SELECT COUNT(*) AS c FROM t_ai_provider", ())
        if existing and existing.get("c", 0) == 0:
            _seed_from_env()
            log.info("Seeded t_ai_provider from env config")
    except Exception:
        log.warning("t_ai_provider seed check failed (non-fatal):", exc_info=True)
