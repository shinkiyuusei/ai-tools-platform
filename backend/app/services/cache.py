"""Redis caching helpers — card detail, lists, and analytics."""
import json


def _client():
    from ..extensions import get_redis_client
    return get_redis_client()


def cache_get(key: str):
    val = _client().get(key)
    if val:
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return None


def cache_set(key: str, value, ttl: int = 300):
    _client().setex(key, ttl, json.dumps(value, ensure_ascii=False))


def cache_delete(key: str):
    _client().delete(key)


def cache_invalidate(pattern: str):
    """Delete all keys matching a glob pattern."""
    keys = _client().keys(pattern)
    if keys:
        _client().delete(*keys)


# ---- Predefined key helpers ----

def _work_key(work_id: int) -> str:
    return f"work:{work_id}"


def _char_key(char_id: int) -> str:
    return f"character:{char_id}"


CACHE_TTL = 300        # 5 min for detail
LIST_TTL = 60          # 1 min for lists


def invalidate_work(work_id: int):
    _client().delete(_work_key(work_id), "home:index", "works:hot:*")
    cache_invalidate("works:list:*")
    cache_invalidate("discovery:*")


def invalidate_character(char_id: int):
    _client().delete(_char_key(char_id))
    cache_invalidate("characters:list:*")
    cache_invalidate("discovery:*")


def get_cached_work(work_id: int):
    return cache_get(_work_key(work_id))


def set_cached_work(work_id: int, data):
    cache_set(_work_key(work_id), data, CACHE_TTL)


def get_cached_character(char_id: int):
    return cache_get(_char_key(char_id))


def set_cached_character(char_id: int, data):
    cache_set(_char_key(char_id), data, CACHE_TTL)
