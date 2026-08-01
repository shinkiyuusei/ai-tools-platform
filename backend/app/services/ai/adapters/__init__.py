"""
AI backend adapter registry.

Each adapter module self-registers via ``register_adapter()`` at import time.
The API layer calls ``get_adapter(name)`` to obtain a configured instance.
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
    """Return the configured default AI provider name."""
    return current_app.config.get("DEFAULT_AI_PROVIDER", DEFAULT_ADAPTER_NAME)


def get_adapter(name: str | None = None) -> "ChatAdapter":  # noqa: F821
    """Return a configured adapter instance for *name*.

    When *name* is ``None`` or empty, the configured default adapter is used.
    Raises ``AppError(ErrorCode.PARAM_INVALID)`` for unknown names.
    """
    name = name or get_default_provider()
    cls = AI_BACKENDS.get(name)
    if cls is None:
        raise AppError(
            ErrorCode.PARAM_INVALID,
            f"不支持的 AI 提供商: {name}，可用选项: {', '.join(AI_BACKENDS)}",
        )
    config = current_app.config.get("AI_BACKENDS", {}).get(name, {})
    return cls(config)


def list_available_adapters() -> list[str]:
    """Return the names of all registered adapters."""
    return list(AI_BACKENDS.keys())


# Import adapters so they self-register at package-load time.
from . import deepseek  # noqa: E402, F401
from . import openai    # noqa: E402, F401
from . import gemini    # noqa: E402, F401
