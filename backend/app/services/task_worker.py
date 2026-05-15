import json
import queue
import threading
from datetime import datetime

from flask import Response, request, stream_with_context
from flask_jwt_extended import verify_jwt_in_request

from ..core.errors import AppError, ErrorCode
from ..extensions import get_mongo_db, get_redis_client
from .ai.deepseek import DeepSeekAdapter
from .audit import audit_content


_task_queue = queue.Queue()
_worker_started = False
_lock = threading.Lock()


def _process_task(task: dict):
    task_id = task["taskId"]
    record_id = task["recordId"]
    redis_client = get_redis_client()
    mongo_db = get_mongo_db()

    try:
        params = task.get("params", {})
        prompt = params.get("topic") or params.get("prompt") or str(params)
        thinking_mode = task.get("thinkingMode", False)

        audit_res = audit_content(prompt)
        if not audit_res["passed"]:
            result_text = f"[审核拦截] {audit_res['message']}"
        else:
            service = DeepSeekAdapter()
            result_text = service.generate_text(prompt, thinking_mode=thinking_mode)

        task["status"] = 1
        task["result"] = result_text

        mongo_db["t_generate_record"].update_one(
            {"recordId": record_id},
            {"$set": {"result": result_text, "status": 1}},
        )
    except Exception as exc:
        task["status"] = 2
        task["result"] = str(exc)
        mongo_db["t_generate_record"].update_one(
            {"recordId": record_id},
            {"$set": {"result": f"[生成失败] {exc}", "status": 2}},
        )

    redis_client.setex(f"ai_task:{task_id}", 3600, json.dumps(task, default=str))
    redis_client.publish(f"ai_task_channel:{task_id}", json.dumps(task, default=str))


def _start_worker():
    global _worker_started
    with _lock:
        if _worker_started:
            return
        _worker_started = True

    def worker_loop():
        while True:
            try:
                task = _task_queue.get(timeout=5)
                _process_task(task)
            except queue.Empty:
                continue
            except Exception:
                continue

    t = threading.Thread(target=worker_loop, daemon=True)
    t.start()


def submit_async_task(task: dict):
    _start_worker()
    _task_queue.put(task)


def sse_handler(api_v1_bp):
    @api_v1_bp.get("/ai/generate/stream/<string:task_id>")
    def stream_task(task_id: str):
        redis_client = get_redis_client()

        verify_jwt_in_request(optional=True)

        def generate():
            existing = redis_client.get(f"ai_task:{task_id}")
            if existing:
                yield f"data: {existing}\n\n"

            pubsub = redis_client.pubsub()
            pubsub.subscribe(f"ai_task_channel:{task_id}")

            try:
                for message in pubsub.listen():
                    if message["type"] == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode()
                        yield f"data: {data}\n\n"
                        yield "event: complete\ndata: \n\n"
                        break
            except GeneratorExit:
                pubsub.unsubscribe()
            finally:
                pubsub.close()

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
