"""
AI backend adapter registry.

Each adapter module self-registers via ``register_adapter()`` at import time.
The API layer calls ``get_adapter(name)`` to obtain a configured instance.

Provider config source (in priority order):
1. ``t_ai_provider`` row (DB, editable from the admin UI) — preferred.
2. ``current_app.config["AI_BACKENDS"][name]`` (env vars) — fallback for
   deployments that haven't run the migration or where the row was deleted.

The adapter *class* is chosen by the provider's ``adapter`` column when
present, so the same OpenAI-compatible class can back multiple providers
(a "Custom" source, mirroring SillyTavern's chat-completions source).
"""

from flask import current_app

from ....core.errors import AppError, ErrorCode
from .base import TOKEN_USAGE_SIGNAL  # noqa: F401 — re-export for consumers

#: Registry of adapter name → adapter class.
AI_BACKENDS: dict[str, type] = {}

#: Fallback adapter name when no provider is specified.
DEFAULT_ADAPTER_NAME = "deepseek"


def register_adapter(name: str, cls: type) -> None:
    """Register an adapter class under *name*."""
    AI_BACKENDS[name] = cls


def get_default_provider() -> str:
    """Return the configured default AI provider name.

    Prefers a DB-backed default (first active provider), falls back to the
    env-based ``DEFAULT_AI_PROVIDER`` when the table is empty.
    """
    try:
        from ..provider_repo import get_default_provider_key
        db_default = get_default_provider_key()
        if db_default:
            return db_default
    except Exception:
        # DB not available / table missing — fall through to env default
        pass
    return current_app.config.get("DEFAULT_AI_PROVIDER", DEFAULT_ADAPTER_NAME)


def get_adapter(name: str | None = None) -> "ChatAdapter":  # noqa: F821
    """Return a configured adapter instance for *name*.

    When *name* is ``None`` or empty, the default provider is used.
    Raises ``AppError(ErrorCode.PARAM_INVALID)`` for unknown names.
    """
    name = name or get_default_provider()

    config: dict = {}
    adapter_class_name: str | None = None

    # 1) Prefer DB-backed provider config
    try:
        from ..provider_repo import get_provider_by_key
        row = get_provider_by_key(name)
        if row:
            config = {
                "base_url": row.get("base_url", ""),
                "api_key": row.get("api_key", ""),
            }
            adapter_class_name = row.get("adapter") or name
    except Exception:
        pass

    # 2) Fall back to env-var config
    if not config:
        config = current_app.config.get("AI_BACKENDS", {}).get(name, {}) or {}
        adapter_class_name = name

    # Resolve adapter class: DB ``adapter`` column wins, then the registry
    # key itself (deepseek/openai/gemini), then default to OpenAI-compatible.
    cls = AI_BACKENDS.get(adapter_class_name or "")
    if cls is None:
        cls = AI_BACKENDS.get(name)
    if cls is None:
        # Treat unknown providers as OpenAI-compatible (SillyTavern's "Custom")
        cls = AI_BACKENDS.get("openai")
    if cls is None:
        raise AppError(
            ErrorCode.PARAM_INVALID,
            f"不支持的 AI 提供商: {name}，可用选项: {', '.join(AI_BACKENDS)}",
        )
    return cls(config)


def list_available_adapters() -> list[str]:
    """Return the names of all registered adapter classes."""
    return list(AI_BACKENDS.keys())


# Import adapters so they self-register at package-load time.
from . import deepseek  # noqa: E402, F401
from . import openai    # noqa: E402, F401
from . import gemini    # noqa: E402, F401
