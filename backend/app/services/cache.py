"""Cache helpers — disabled after the Redis removal.

The interface is kept so callers can re-enable an in-process or external cache
later without touching API code.
"""


def cache_get(key: str):
    return None


def cache_set(key: str, value, ttl: int = 300) -> None:
    return None


def cache_delete(key: str) -> None:
    return None


def cache_invalidate(pattern: str) -> None:
    return None


# ---- Predefined key helpers ----

def _work_key(work_id: int) -> str:
    return f"work:{work_id}"


def _char_key(char_id: int) -> str:
    return f"character:{char_id}"


CACHE_TTL = 300        # 5 min for detail
LIST_TTL = 60          # 1 min for lists


def invalidate_work(work_id: int):
    pass


def invalidate_character(char_id: int):
    pass


def get_cached_work(work_id: int):
    return cache_get(_work_key(work_id))


def set_cached_work(work_id: int, data):
    cache_set(_work_key(work_id), data, CACHE_TTL)


def get_cached_character(char_id: int):
    return cache_get(_char_key(char_id))


def set_cached_character(char_id: int, data):
    cache_set(_char_key(char_id), data, CACHE_TTL)
