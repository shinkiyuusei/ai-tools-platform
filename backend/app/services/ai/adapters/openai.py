"""
OpenAI adapter — matches the OpenAI chat-completion API shape.

This is the reference "second provider" that validates the ChatAdapter
abstraction.  Any OpenAI-compatible service (vLLM, Ollama, LiteLLM, …)
can be used by pointing ``OPENAI_API_BASE`` at its endpoint.
"""

import json

import requests

from ....core.errors import AppError, ErrorCode
from .base import TOKEN_USAGE_SIGNAL, ChatAdapter
from . import register_adapter


class OpenAIAdapter(ChatAdapter):
    """Adapter for the OpenAI chat-completion API (and compatible proxies)."""

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.config.get("api_key"):
            raise AppError(ErrorCode.GENERATE_FAILED, "未配置 OpenAI API Key")
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    #  ABC implementation
    # ------------------------------------------------------------------

    def chat_completion_stream(
        self, messages: list[dict], model: str = "", **params
    ):
        """Stream chat completion, yielding raw text chunks."""
        chat_model = model or self.config.get("chat_model", "gpt-4o")

        payload: dict = {
            "model": chat_model,
            "messages": messages,
            "stream": True,
        }

        # Optional: OpenAI supports a higher max_tokens; keep it reasonable.
        payload["max_tokens"] = params.get("max_tokens", 4096)

        try:
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=120,
                stream=True,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED,
                f"OpenAI 调用失败 [{exc.response.status_code}]: {exc.response.text[:500]}",
            ) from exc
        except requests.RequestException as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED, f"OpenAI 网络请求失败: {exc}"
            ) from exc

        total_tokens = 0
        for line in response.iter_lines():
            if not line:
                continue
            line = line.decode("utf-8").strip()
            if not line.startswith("data: "):
                continue
            data_str = line[6:]
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                usage = chunk.get("usage", {})
                if usage:
                    total_tokens = usage.get("total_tokens", 0)
                choices = chunk.get("choices", [])
                if choices and choices[0].get("delta", {}).get("content"):
                    yield choices[0]["delta"]["content"]
            except (json.JSONDecodeError, KeyError):
                continue

        yield f"{TOKEN_USAGE_SIGNAL}{total_tokens}\0"

    def list_models(self) -> list[dict]:
        """Return the well-known OpenAI models."""
        chat_model = self.config.get("chat_model", "gpt-4o")
        return [
            {"id": chat_model, "name": chat_model},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        ]

    def count_tokens(self, messages: list[dict]) -> int:
        """Rough approximation: ~4 chars per token for English + CJK text."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return max(1, total_chars // 3)

    def health_check(self) -> bool:
        """Ping the models endpoint to verify connectivity."""
        try:
            r = requests.get(
                f"{self.config['base_url']}/models",
                headers=self._headers(),
                timeout=10,
            )
            return r.status_code == 200
        except requests.RequestException:
            return False


# Self-register at import time.
register_adapter("openai", OpenAIAdapter)
