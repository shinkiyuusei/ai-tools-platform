"""
Gemini adapter — via OpenAI-compatible new-api proxy.

The adapter uses the same OpenAI-compatible chat-completion shape as the
OpenAI adapter, targeting a new-api gateway that proxies requests to
Google Gemini models.
"""

import json

import requests

from ....core.errors import AppError, ErrorCode
from .base import TOKEN_USAGE_SIGNAL, ChatAdapter
from . import register_adapter


class GeminiAdapter(ChatAdapter):
    """Adapter for Gemini models via OpenAI-compatible proxy (new-api)."""

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.config.get("api_key"):
            raise AppError(ErrorCode.GENERATE_FAILED, "未配置 Gemini API Key")
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
        chat_model = model or self.config.get("chat_model", "[YDE]gemini-3.1-flash-防截断-0.5")

        payload: dict = {
            "model": chat_model,
            "messages": messages,
            "stream": True,
            "max_tokens": params.get("max_tokens", 4096),
        }

        try:
            response = self._session.post(
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
                f"Gemini 调用失败 [{exc.response.status_code}]: {exc.response.text[:500]}",
            ) from exc
        except requests.RequestException as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED, f"Gemini 网络请求失败: {exc}"
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
        """Return available Gemini models."""
        chat_model = self.config.get("chat_model", "[YDE]gemini-3.1-flash-防截断-0.5")
        return [
            {"id": chat_model, "name": "Gemini 3.1 Pro"},
        ]

    def count_tokens(self, messages: list[dict]) -> int:
        """Rough approximation: ~4 chars per token."""
        total_chars = sum(len(m.get("content", "")) for m in messages)
        return max(1, total_chars // 3)

    def health_check(self) -> bool:
        """Ping the models endpoint to verify connectivity."""
        try:
            r = self._session.get(
                f"{self.config['base_url']}/models",
                headers=self._headers(),
                timeout=10,
            )
            return r.status_code == 200
        except requests.RequestException:
            return False


# Self-register at import time.
register_adapter("gemini", GeminiAdapter)
