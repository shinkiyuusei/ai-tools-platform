import json

import requests
from flask import current_app

from ...core.errors import AppError, ErrorCode

TOKEN_USAGE_SIGNAL = "\0[TOKENS]"


class DeepSeekAdapter:
    def __init__(self):
        self.config = current_app.config["DEEPSEEK_CONFIG"]

    def _headers(self):
        if not self.config["api_key"]:
            raise AppError(ErrorCode.GENERATE_FAILED, "未配置 DeepSeek API Key")
        return {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json",
        }

    def chat_completion(
        self,
        messages: list,
        model: str = "",
        thinking_mode: bool = False,
        reasoning_effort: str = "medium",
    ) -> dict:
        payload = {
            "model": model or (self.config["reasoner_model"] if thinking_mode else self.config["chat_model"]),
            "messages": messages,
            "stream": False,
        }
        if thinking_mode:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = reasoning_effort
        try:
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=90,
            )
            response.raise_for_status()
            body = response.json()
        except requests.RequestException as exc:
            raise AppError(ErrorCode.GENERATE_FAILED, f"DeepSeek 调用失败: {exc}") from exc
        if not body.get("choices"):
            raise AppError(ErrorCode.GENERATE_FAILED, "DeepSeek 返回为空")
        return body

    def chat_completion_stream(
        self,
        messages: list,
        model: str = "",
        thinking_mode: bool = False,
        reasoning_effort: str = "medium",
    ):
        """Stream chat completion, yielding SSE content chunks and final usage."""
        payload = {
            "model": model or (self.config["reasoner_model"] if thinking_mode else self.config["chat_model"]),
            "messages": messages,
            "stream": True,
        }
        if thinking_mode:
            payload["thinking"] = {"type": "enabled"}
            payload["reasoning_effort"] = reasoning_effort
        try:
            response = requests.post(
                f"{self.config['base_url']}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=120,
                stream=True,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise AppError(ErrorCode.GENERATE_FAILED, f"DeepSeek 调用失败: {exc}") from exc

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
                # The final chunk may contain usage data with empty choices
                usage = chunk.get("usage", {})
                if usage:
                    total_tokens = usage.get("total_tokens", 0)
                choices = chunk.get("choices", [])
                if choices and choices[0].get("delta", {}).get("content"):
                    yield choices[0]["delta"]["content"]
            except (json.JSONDecodeError, KeyError):
                continue

        yield f"{TOKEN_USAGE_SIGNAL}{total_tokens}\0"

