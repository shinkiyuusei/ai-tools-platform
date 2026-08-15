"""
Recommendation scoring service.

Computes a composite score for works and character cards based on:
  - daily / weekly / monthly chat counts (from t_cards_daily_stat)
  - all-time usage (use_count on the card table)
  - collection count (t_work_collect / t_character_collect)
  - token consumption (use_count)

All dimensions are min-max normalised across currently-published cards,
then combined with configurable weights.  Results are stored in MySQL
(t_recommend_score) and refreshed by the scheduler.
"""

import json
from datetime import date, timedelta

from ..utils.mysql import query_all, transaction


# --- Dimension queries --------------------------------------------------------

def _published_works():
    return query_all(
        "SELECT id, use_count FROM t_work_card WHERE status = 1"
    )


def _published_chars():
    return query_all(
        "SELECT id, use_count FROM t_character_card WHERE status = 1 AND is_public = 1"
    )


def _daily_chat_counts(card_type: str, card_ids: list[int]):
    """Return {card_id: chat_count} for today."""
    if not card_ids:
        return {}
    placeholders = ",".join(["%s"] * len(card_ids))
    rows = query_all(
        f"SELECT card_id, SUM(chat_count) AS cnt FROM t_cards_daily_stat "
        f"WHERE card_type = %s AND card_id IN ({placeholders}) AND stat_date = %s "
        f"GROUP BY card_id",
        (card_type, *card_ids, date.today().isoformat()),
    )
    return {r["card_id"]: int(r["cnt"] or 0) for r in rows}


def _weekly_chat_counts(card_type: str, card_ids: list[int]):
    if not card_ids:
        return {}
    placeholders = ",".join(["%s"] * len(card_ids))
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    rows = query_all(
        f"SELECT card_id, SUM(chat_count) AS cnt FROM t_cards_daily_stat "
        f"WHERE card_type = %s AND card_id IN ({placeholders}) AND stat_date >= %s "
        f"GROUP BY card_id",
        (card_type, *card_ids, week_ago),
    )
    return {r["card_id"]: int(r["cnt"] or 0) for r in rows}


def _monthly_chat_counts(card_type: str, card_ids: list[int]):
    if not card_ids:
        return {}
    placeholders = ",".join(["%s"] * len(card_ids))
    month_ago = (date.today() - timedelta(days=30)).isoformat()
    rows = query_all(
        f"SELECT card_id, SUM(chat_count) AS cnt FROM t_cards_daily_stat "
        f"WHERE card_type = %s AND card_id IN ({placeholders}) AND stat_date >= %s "
        f"GROUP BY card_id",
        (card_type, *card_ids, month_ago),
    )
    return {r["card_id"]: int(r["cnt"] or 0) for r in rows}


def _collection_counts(card_type: str, card_ids: list[int]):
    """Return {card_id: count} of collections."""
    if not card_ids:
        return {}
    placeholders = ",".join(["%s"] * len(card_ids))
    table = "t_work_collect" if card_type == "work" else "t_character_collect"
    col = "work_id" if card_type == "work" else "character_id"
    rows = query_all(
        f"SELECT {col} AS card_id, COUNT(*) AS cnt FROM {table} "
        f"WHERE {col} IN ({placeholders}) GROUP BY {col}",
        tuple(card_ids),
    )
    return {r["card_id"]: int(r["cnt"] or 0) for r in rows}


# --- Normalisation ------------------------------------------------------------

def _min_max_norm(values: list[float]) -> list[float]:
    if not values:
        return []
    mn, mx = min(values), max(values)
    if mx == mn:
        return [0.5] * len(values)  # all equal → neutral
    return [(v - mn) / (mx - mn) for v in values]


# --- Main scoring ------------------------------------------------------------

# Default weights: daily 25%, weekly 20%, monthly 15%, total 15%, collections 15%, token 10%
WEIGHTS = {
    "daily": 0.25,
    "weekly": 0.20,
    "monthly": 0.15,
    "total": 0.15,
    "collections": 0.15,
    "token": 0.10,
}


def compute_scores(card_type: str = "work"):
    """
    Compute recommendation scores for every published card of the given type.

    Returns a list of dicts: {card_id, score, dimensions: {...}} sorted by score DESC.
    """
    if card_type == "work":
        cards = _published_works()
    else:
        cards = _published_chars()

    if not cards:
        return []

    card_ids = [c["id"] for c in cards]

    raw_daily = _daily_chat_counts(card_type, card_ids)
    raw_weekly = _weekly_chat_counts(card_type, card_ids)
    raw_monthly = _monthly_chat_counts(card_type, card_ids)
    raw_collections = _collection_counts(card_type, card_ids)
    raw_token = {c["id"]: int(c["use_count"] or 0) for c in cards}

    daily_vals = [raw_daily.get(cid, 0) for cid in card_ids]
    weekly_vals = [raw_weekly.get(cid, 0) for cid in card_ids]
    monthly_vals = [raw_monthly.get(cid, 0) for cid in card_ids]
    total_vals = [raw_token.get(cid, 0) for cid in card_ids]
    coll_vals = [raw_collections.get(cid, 0) for cid in card_ids]
    token_vals = [raw_token.get(cid, 0) for cid in card_ids]

    norm_daily = _min_max_norm(daily_vals)
    norm_weekly = _min_max_norm(weekly_vals)
    norm_monthly = _min_max_norm(monthly_vals)
    norm_total = _min_max_norm(total_vals)
    norm_coll = _min_max_norm(coll_vals)
    norm_token = _min_max_norm(token_vals)

    results = []
    for i, card in enumerate(cards):
        score = (
            WEIGHTS["daily"] * norm_daily[i]
            + WEIGHTS["weekly"] * norm_weekly[i]
            + WEIGHTS["monthly"] * norm_monthly[i]
            + WEIGHTS["total"] * norm_total[i]
            + WEIGHTS["collections"] * norm_coll[i]
            + WEIGHTS["token"] * norm_token[i]
        )
        results.append({
            "card_id": card["id"],
            "score": round(score, 6),
            "dimensions": {
                "daily": round(norm_daily[i], 4),
                "weekly": round(norm_weekly[i], 4),
                "monthly": round(norm_monthly[i], 4),
                "total": round(norm_total[i], 4),
                "collections": round(norm_coll[i], 4),
                "token": round(norm_token[i], 4),
            },
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# --- Scheduler integration ---------------------------------------------------

def refresh_recommendations():
    """Recompute scores and upsert them into MySQL."""
    work_scores = compute_scores("work")
    char_scores = compute_scores("character")

    payload = {
        "works": {str(item["card_id"]): item for item in work_scores},
        "characters": {str(item["card_id"]): item for item in char_scores},
    }

    rows = []
    for card_type, scores in (("work", work_scores), ("character", char_scores)):
        for item in scores:
            rows.append((
                card_type,
                item["card_id"],
                item["score"],
                json.dumps(item["dimensions"], ensure_ascii=False),
            ))

    with transaction() as cur:
        cur.execute("DELETE FROM t_recommend_score")
        if rows:
            cur.executemany(
                "INSERT INTO t_recommend_score "
                "(card_type, card_id, score, dimensions) VALUES (%s,%s,%s,%s)",
                rows,
            )
    return payload


def get_cached_recommendations(card_type: str | None = None):
    """Return cached scores from MySQL.  Returns None when the table is empty."""
    rows = query_all(
        "SELECT card_type, card_id, score, dimensions FROM t_recommend_score "
        "ORDER BY score DESC"
    )
    if not rows:
        return None

    payload = {"works": {}, "characters": {}}
    for r in rows:
        group = "works" if r["card_type"] == "work" else "characters"
        try:
            dimensions = json.loads(r["dimensions"]) if isinstance(r["dimensions"], str) else r["dimensions"]
        except (json.JSONDecodeError, TypeError):
            dimensions = {}
        payload[group][str(r["card_id"])] = {
            "card_id": r["card_id"],
            "score": float(r["score"]),
            "dimensions": dimensions,
        }

    if card_type:
        return payload.get(card_type, {})
    return payload
