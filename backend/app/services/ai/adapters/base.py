"""
Abstract base class for AI chat backend adapters.

Every AI provider (DeepSeek, OpenAI, Anthropic, etc.) implements this interface
so that the API layer can be provider-agnostic.
"""

from abc import ABC, abstractmethod
from typing import Generator

# Sentinel injected at the end of every streaming generator so the caller can
# extract the total token count without a separate API call.
TOKEN_USAGE_SIGNAL = "\0[TOKENS]"

# DeepSeek error codes that indicate content filtering (kept here as a
# well-known constant shared across adapters that may encounter them).
CONTENT_FILTER_CODES = {"content_filter", "sensitive_word", "sensitive_content"}


class ChatAdapter(ABC):
    """Unified interface for AI chat backends."""

    def __init__(self, config: dict):
        """Initialise with a provider-specific configuration dict.

        The config dict comes from ``current_app.config["AI_BACKENDS"][<name>]``
        and must contain at minimum ``base_url`` and ``api_key``.
        """
        self.config = config
        # Use a dedicated session with trust_env=False to avoid Windows
        # proxy auto-detection issues that block outbound HTTPS connections.
        import requests as _requests
        self._session = _requests.Session()
        self._session.trust_env = False

    # ------------------------------------------------------------------
    # Abstract methods — every adapter MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    def chat_completion_stream(
        self,
        messages: list[dict],
        model: str = "",
        **params,
    ) -> Generator[str, None, None]:
        """Stream a chat completion, yielding raw text content chunks.

        The *last* value yielded by the generator MUST be the sentinel
        ``f"{TOKEN_USAGE_SIGNAL}{total_tokens}\\0"`` so that the caller can
        extract the total token usage without inspecting SSE framing.

        Parameters
        ----------
        messages : list[dict]
            List of ``{"role": str, "content": str}`` dicts.
        model : str
            Model identifier.  Empty string means "use the provider default".
        **params
            Provider-specific keyword arguments forwarded from the API payload
            (e.g. ``thinking_mode``, ``reasoning_effort``).

        Yields
        ------
        str
            Raw text content chunks (NOT SSE-framed).
        """
        ...

    @abstractmethod
    def list_models(self) -> list[dict]:
        """Return available models.

        Each dict should have at minimum ``{"id": str, "name": str}``.
        """
        ...

    # ------------------------------------------------------------------
    # Optional methods — adapters MAY override these
    # ------------------------------------------------------------------

    def chat_completion(
        self, messages: list[dict], model: str = "", **params
    ) -> dict:
        """Non-streaming chat completion (concrete default).

        Adapts the streaming endpoint by collecting all chunks in memory.
        Adapters MAY override with a more efficient real implementation.

        Returns a dict shaped like the OpenAI response:
        ``{"choices": [{"message": {"content": "..."}}], "usage": {...}, "model": "..."}``
        """
        full_content: list[str] = []
        total_tokens = 0

        for chunk in self.chat_completion_stream(messages, model, **params):
            if TOKEN_USAGE_SIGNAL in chunk:
                try:
                    total_tokens = int(
                        chunk.split(TOKEN_USAGE_SIGNAL)[1].rstrip("\0")
                    )
                except (ValueError, IndexError):
                    pass
                continue
            full_content.append(chunk)

        return {
            "choices": [
                {"message": {"content": "".join(full_content)}}
            ],
            "usage": {"total_tokens": total_tokens},
            "model": model,
        }

    def count_tokens(self, messages: list[dict]) -> int:
        """Estimate / count tokens for the given message list.

        Returns 0 when the adapter has no tokenizer available (the caller
        falls back to a simple character-count heuristic).
        """
        return 0

    def health_check(self) -> bool:
        """Return ``True`` if the backend is reachable."""
        return True
