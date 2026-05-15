import json
import uuid
from datetime import datetime

import requests
from flask import current_app

from ...core.errors import AppError, ErrorCode
from ...extensions import get_mongo_db, get_redis_client


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

    def generate_text(self, prompt: str, thinking_mode: bool = False):
        model = self.config["reasoner_model"] if thinking_mode else self.config["chat_model"]
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        response = requests.post(
            f"{self.config['base_url']}/chat/completions",
            json=payload,
            headers=self._headers(),
            timeout=60,
        )
        response.raise_for_status()
        body = response.json()
        return body["choices"][0]["message"]["content"]

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
        """Stream chat completion, yielding SSE content chunks."""
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
                choices = chunk.get("choices", [])
                if choices and choices[0].get("delta", {}).get("content"):
                    yield choices[0]["delta"]["content"]
            except (json.JSONDecodeError, KeyError):
                continue

    def submit_async_task(self, tool_id: int, user_id: int, params: dict, tool_name: str = "", thinking_mode: bool = False):
        task_id = f"task_{uuid.uuid4().hex[:16]}"
        record_id = f"record_{uuid.uuid4().hex[:16]}"

        task_payload = {
            "taskId": task_id,
            "recordId": record_id,
            "toolId": tool_id,
            "userId": user_id,
            "params": params,
            "thinkingMode": thinking_mode,
            "status": 0,
            "result": None,
        }
        get_redis_client().setex(f"ai_task:{task_id}", 3600, json.dumps(task_payload, default=str))
        get_mongo_db()["t_generate_record"].insert_one(
            {
                "recordId": record_id,
                "userId": user_id,
                "toolId": tool_id,
                "toolName": tool_name or "未知工具",
                "params": params,
                "result": "",
                "status": 0,
                "createTime": datetime.utcnow(),
                "isCollected": 0,
            }
        )

        from ..task_worker import submit_async_task
        submit_async_task(task_payload)

        return {"taskId": task_id, "recordId": record_id}
