"""
World Info (世界设定书) — dynamic lore injection for immersive storytelling.

Each work card or character card can have many world-info entries.
At chat time the user's latest message is matched against entry keywords.
Constant entries are always injected; selective entries are tagged for the
AI to judge relevance during response generation.

Cache strategy (following ``services/cache.py`` patterns):
    - Per-entity entry lists may be cached (TTL 300 s) via cache helpers.
    - Writes invalidate the affected cache key.
"""

import json
import re

from ..utils.mysql import query_one, query_all, execute
from .cache import cache_get, cache_set, cache_delete

# ---------------------------------------------------------------------------
#  Cache helpers
# ---------------------------------------------------------------------------

LIST_TTL = 300  # 5 minutes


def _cache_key(entity_type: str, entity_id: int) -> str:
    return f"world_info:{entity_type}:{entity_id}"


def _invalidate(entity_type: str, entity_id: int):
    cache_delete(_cache_key(entity_type, entity_id))


# ---------------------------------------------------------------------------
#  CRUD
# ---------------------------------------------------------------------------

def create_entry(
    entity_type: str,
    entity_id: int,
    keys: list[str],
    content: str,
    comment: str = "",
    selective: bool = False,
    constant: bool = False,
    recursion: bool = False,
    position: str = "before_char",
    depth: int = 1,
    order: int = 0,
    probability: int = 100,
    content_mode: str | None = None,
    character_name: str | None = None,
) -> int:
    """Insert a world-info entry and invalidate the cache.  Returns the new id."""
    entry_id = execute(
        """INSERT INTO t_world_info_entry
           (entity_type, entity_id, `keys`, content, comment,
            selective, constant, recursion, position, depth, `order`,
            probability, content_mode, character_name)
           VALUES (%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s)""",
        (
            entity_type, entity_id, json.dumps(keys, ensure_ascii=False),
            content, comment,
            int(selective), int(constant), int(recursion),
            position, depth, order,
            probability, content_mode, character_name,
        ),
    )
    _invalidate(entity_type, entity_id)
    return entry_id


def update_entry(entry_id: int, **fields) -> None:
    """Partial-update a world-info entry and invalidate its cache."""
    # Resolve entity info for cache invalidation
    row = query_one(
        "SELECT entity_type, entity_id FROM t_world_info_entry WHERE id = %s",
        (entry_id,),
    )
    if not row:
        return

    # Build dynamic SET clause (follows utils/crud.py pattern)
    allowed = {
        "keys", "content", "comment", "selective", "constant", "recursion",
        "position", "depth", "order", "probability", "content_mode",
        "character_name",
    }
    sets = []
    values = []
    for col, val in fields.items():
        if col not in allowed:
            continue
        # JSON-serialize list fields
        if col == "keys" and isinstance(val, list):
            val = json.dumps(val, ensure_ascii=False)
        if col in ("selective", "constant", "recursion"):
            val = int(val)
        sets.append(f"`{col}` = %s" if col == "keys" or col == "order" else f"{col} = %s")
        values.append(val)
    if not sets:
        return
    values.append(entry_id)
    execute(
        f"UPDATE t_world_info_entry SET {', '.join(sets)} WHERE id = %s",
        tuple(values),
    )
    _invalidate(row["entity_type"], row["entity_id"])


def delete_entry(entry_id: int) -> None:
    """Delete a world-info entry and invalidate its cache."""
    row = query_one(
        "SELECT entity_type, entity_id FROM t_world_info_entry WHERE id = %s",
        (entry_id,),
    )
    if row:
        execute("DELETE FROM t_world_info_entry WHERE id = %s", (entry_id,))
        _invalidate(row["entity_type"], row["entity_id"])


def get_entry(entry_id: int) -> dict | None:
    """Return a single world-info entry or None."""
    return query_one(
        "SELECT * FROM t_world_info_entry WHERE id = %s", (entry_id,)
    )


def list_entries(entity_type: str, entity_id: int) -> list[dict]:
    """Return all world-info entries for an entity, ordered by depth/order."""
    return query_all(
        """SELECT * FROM t_world_info_entry
           WHERE entity_type = %s AND entity_id = %s
           ORDER BY depth ASC, `order` ASC""",
        (entity_type, entity_id),
    )


# ---------------------------------------------------------------------------
#  Active lore resolution (keyword matching + AI-selective logic)
# ---------------------------------------------------------------------------

# Simple CJK + Latin tokenisation regex
_TOKEN_RE = re.compile(r"[一-鿿]+|[a-zA-Z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Return a set of lowercase tokens from *text*."""
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def get_active_lore(
    entity_type: str,
    entity_id: int,
    user_message: str,
    content_mode: str | None = None,
) -> dict[str, list[dict]]:
    """Return active lore entries split into *always* and *selective*.

    Resolution logic:
        1. Fetch entries (cache-aside).
        2. Filter by content_mode (exclude mismatched entries).
        3. Separate ``constant=true`` entries → always.
        4. For remaining entries: tokenize user message and match against entry keys.
        5. Matched entries with ``selective=false`` → always.
        6. Matched entries with ``selective=true`` → selective (AI will judge).

    Returns
    -------
    dict
        ``{"always": [...], "selective": [...]}`` — each list is entry dicts.
    """
    # 1. Fetch (cache-aside)
    entries = cache_get(_cache_key(entity_type, entity_id))
    if entries is None:
        entries = list_entries(entity_type, entity_id)
        cache_set(_cache_key(entity_type, entity_id), entries, LIST_TTL)

    if not entries:
        return {"always": [], "selective": []}

    # 2. Filter by content_mode
    if content_mode:
        entries = [
            e for e in entries
            if e.get("content_mode") is None or e["content_mode"] == content_mode
        ]

    # 3. Separate constants
    always: list[dict] = []
    selective: list[dict] = []
    for e in entries:
        if e.get("constant"):
            always.append(e)

    # 4-6. Keyword match remaining entries
    remaining = [e for e in entries if not e.get("constant")]
    if not remaining:
        return {"always": always, "selective": selective}

    tokens = _tokenize(user_message)
    for e in remaining:
        entry_keys: list[str] = e.get("keys", [])
        if isinstance(entry_keys, str):
            try:
                entry_keys = json.loads(entry_keys)
            except (json.JSONDecodeError, TypeError):
                entry_keys = []

        # Check if any keyword is present in the user message
        matched = any(
            any(kw_token.lower() in tokens for kw_token in _tokenize(kw))
            for kw in entry_keys
        )
        if not matched:
            continue

        # Probability check
        prob = e.get("probability", 100)
        if prob < 100 and prob > 0:
            import random
            if random.randint(1, 100) > prob:
                continue

        if e.get("selective"):
            selective.append(e)
        else:
            always.append(e)

    # Sort by depth, order for deterministic prompt injection
    always.sort(key=lambda x: (x.get("depth", 1), x.get("order", 0)))
    selective.sort(key=lambda x: (x.get("depth", 1), x.get("order", 0)))

    return {"always": always, "selective": selective}
