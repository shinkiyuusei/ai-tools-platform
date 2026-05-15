import functools
import time
from datetime import datetime

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..core.errors import AppError, ErrorCode
from ..extensions import get_redis_client


def rate_limit(max_requests: int, window_seconds: int = 60):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client = get_redis_client()

            user_id = 0
            try:
                verify_jwt_in_request(optional=True)
                identity = get_jwt_identity()
                if identity:
                    user_id = int(identity)
            except Exception:
                pass

            if user_id:
                key = f"rate_limit:user:{user_id}:{request.path}"
            else:
                ip = request.remote_addr or "unknown"
                key = f"rate_limit:ip:{ip}:{request.path}"

            current = client.get(key)
            if current and int(current) >= max_requests:
                ttl = client.ttl(key)
                raise AppError(
                    ErrorCode.VIP_REQUIRED,
                    f"请求过于频繁，请在 {ttl} 秒后重试",
                )

            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            pipe.execute()

            return func(*args, **kwargs)

        return wrapper

    return decorator


def daily_limit(route_path: str, max_per_day: int = 10):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            client = get_redis_client()

            user_id = 0
            try:
                verify_jwt_in_request(optional=True)
                identity = get_jwt_identity()
                if identity:
                    user_id = int(identity)
            except Exception:
                pass

            if user_id:
                key = f"daily_limit:user:{user_id}:{datetime.utcnow().strftime('%Y%m%d')}"
            else:
                ip = request.remote_addr or "unknown"
                key = f"daily_limit:ip:{ip}:{datetime.utcnow().strftime('%Y%m%d')}"

            current = int(client.get(key) or 0)
            if current >= max_per_day:
                raise AppError(
                    ErrorCode.VIP_REQUIRED,
                    f"今日使用次数已达上限（{max_per_day}次），请开通会员或明日再来",
                )
            client.incr(key)
            client.expire(key, 86400)

            return func(*args, **kwargs)

        return wrapper

    return decorator
