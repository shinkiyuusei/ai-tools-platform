"""
Backward-compatible re-export shim.

All code that previously imported ``DeepSeekAdapter`` and
``TOKEN_USAGE_SIGNAL`` from this module continues to work unchanged.
The real implementation now lives in ``services.ai.adapters``.
"""

from .adapters.base import TOKEN_USAGE_SIGNAL, CONTENT_FILTER_CODES  # noqa: F401
from .adapters.deepseek import DeepSeekAdapter  # noqa: F401
