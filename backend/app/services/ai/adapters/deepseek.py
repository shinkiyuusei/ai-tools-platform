"""
DeepSeek adapter — OpenAI-compatible chat-completion API.

This is the default AI provider for the platform.  It supports both
standard chat and a "thinking / reasoning" mode (``deepseek-v4-pro``).
"""

import json

import requests

from ....core.errors import AppError, ErrorCode
from .base import CONTENT_FILTER_CODES, TOKEN_USAGE_SIGNAL, ChatAdapter
from . import register_adapter


class DeepSeekAdapter(ChatAdapter):
    """Adapter for the DeepSeek API (OpenAI-compatible shape)."""

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        if not self.config.get("api_key"):
            raise AppError(ErrorCode.GENERATE_FAILED, "未配置 DeepSeek API Key")
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    def _handle_http_error(self, response) -> str:
        try:
            body = response.json()
        except Exception:
            body = {}
        err_msg = body.get("error", {}).get("message", "") or response.text[:500]
        err_code = body.get("error", {}).get("code", "")

        if err_code in CONTENT_FILTER_CODES or any(
            kw in err_msg.lower()
            for kw in ("content_filter", "sensitive", "moderation", "inappropriate")
        ):
            return "DeepSeek 内容审核拦截：当前对话内容被 API 安全策略拒绝，请调整输入后重试"
        return f"DeepSeek 调用失败 [{response.status_code}]: {err_msg}"

    def _request_payload(
        self, messages: list[dict], model: str, stream: bool, **params
    ) -> dict:
        """Build the POST body shared by streaming and non-streaming calls."""
        thinking_mode = params.get("thinking_mode", False)
        reasoning_effort = params.get("reasoning_effort", "medium")

        chat_model = self.config.get("chat_model", "deepseek-v4-flash")
        reasoner_model = self.config.get("reasoner_model", "deepseek-v4-pro")

        payload: dict = {
            "model": model or (reasoner_model if thinking_mode else chat_model),
            "messages": messages,
            "stream": stream,
            "max_tokens": 393216,
        }
        if thinking_mode:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = reasoning_effort
        return payload

    # ------------------------------------------------------------------
    #  ABC implementation
    # ------------------------------------------------------------------

    def chat_completion_stream(
        self, messages: list[dict], model: str = "", **params
    ):
        """Stream chat completion, yielding raw text chunks.

        The final yield is always ``TOKEN_USAGE_SIGNAL`` + token_count.
        """
        payload = self._request_payload(messages, model, stream=True, **params)
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
                ErrorCode.GENERATE_FAILED, self._handle_http_error(exc.response)
            ) from exc
        except requests.RequestException as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED, f"DeepSeek 网络请求失败: {exc}"
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
        """Return the models configured for this adapter."""
        return [
            {"id": self.config.get("chat_model", "deepseek-v4-flash"),
             "name": "DeepSeek Flash"},
            {"id": self.config.get("reasoner_model", "deepseek-v4-pro"),
             "name": "DeepSeek Pro (Reasoner)"},
        ]

    # ------------------------------------------------------------------
    #  DeepSeek-specific extras (not part of the ABC)
    # ------------------------------------------------------------------

    def chat_completion(
        self,
        messages: list[dict],
        model: str = "",
        thinking_mode: bool = False,
        reasoning_effort: str = "medium",
    ) -> dict:
        """Non-streaming chat completion (DeepSeek-specific).

        Returns the full JSON response body (OpenAI shape).
        """
        payload = self._request_payload(
            messages, model, stream=False,
            thinking_mode=thinking_mode, reasoning_effort=reasoning_effort,
        )
        try:
            response = self._session.post(
                f"{self.config['base_url']}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=90,
            )
            response.raise_for_status()
            body = response.json()
        except requests.HTTPError as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED, self._handle_http_error(exc.response)
            ) from exc
        except requests.RequestException as exc:
            raise AppError(
                ErrorCode.GENERATE_FAILED, f"DeepSeek 网络请求失败: {exc}"
            ) from exc
        if not body.get("choices"):
            raise AppError(ErrorCode.GENERATE_FAILED, "DeepSeek 返回为空")
        return body


# Self-register at import time.
register_adapter("deepseek", DeepSeekAdapter)
