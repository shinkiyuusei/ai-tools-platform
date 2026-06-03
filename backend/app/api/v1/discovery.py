"""
Discovery API endpoints — trending, categories, search, featured content, recommendations.
"""
import copy
from flask import Blueprint, request

from ...utils.categories import CATEGORIES
from ...utils.mysql import query_all, query_one
from ...utils.response import success_response, page_response
from ...services.recommendation import get_cached_recommendations

discovery_bp = Blueprint("discovery", __name__)


@discovery_bp.get("/discovery/trending")
def get_trending():
    limit = min(int(request.args.get("limit", 20)), 50)
    category_id = request.args.get("categoryId", type=int)

    where = "status = 1"
    params = []
    if category_id:
        where += " AND category = %s"
        params.append(category_id)

    works = query_all(
        f"SELECT id, name, cover AS icon, `desc`, use_count AS useCount, 'work' AS type "
        f"FROM t_work_card WHERE {where} "
        f"ORDER BY use_count DESC LIMIT %s",
        tuple(params + [limit // 2])
    )

    char_where = "status = 1 AND is_public = 1"
    char_params = []
    if category_id:
        char_where += " AND category_id = %s"
        char_params.append(category_id)

    characters = query_all(
        f"SELECT c.id, c.name, c.avatar, c.description, c.like_count AS likeCount, "
        f"c.view_count AS viewCount, c.collect_count AS collectCount, 'character' AS type "
        f"FROM t_character_card c "
        f"WHERE {char_where} ORDER BY like_count DESC LIMIT %s",
        tuple(char_params + [limit // 2])
    )

    trending = list(works) + list(characters)
    trending.sort(key=lambda x: x.get('useCount') or x.get('likeCount') or 0, reverse=True)

    return success_response(trending[:limit])


@discovery_bp.get("/discovery/categories")
def get_categories():
    """Get all categories with per-category work counts."""
    categories = copy.deepcopy(CATEGORIES)

    for cat in categories:
        count = query_one(
            "SELECT COUNT(*) as count FROM t_work_card WHERE category = %s AND status = 1",
            (cat["id"],)
        )
        cat["count"] = count["count"] if count else 0

    return success_response(categories)


@discovery_bp.get("/discovery/search")
def advanced_search():
    keyword = request.args.get("keyword", "")
    category_id = request.args.get("categoryId", type=int)
    sort_type = request.args.get("sortType", "hot")
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)

    where = ["status = 1"]
    params = []

    if keyword:
        where.append("(name LIKE %s OR `desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])

    if category_id:
        where.append("category = %s")
        params.append(category_id)

    where_clause = " AND ".join(where)

    order_map = {"hot": "use_count DESC, id DESC", "new": "create_time DESC, id DESC"}
    order_clause = order_map.get(sort_type, "use_count DESC, id DESC")

    count_sql = f"SELECT COUNT(*) AS total FROM t_work_card WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]

    data_sql = (
        f"SELECT id, name, cover AS icon, `desc`, tags, "
        f"use_count AS useCount, category AS categoryId, create_time AS createTime "
        f"FROM t_work_card WHERE {where_clause} ORDER BY {order_clause} LIMIT %s OFFSET %s"
    )
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))

    return success_response({
        "list": items,
        "total": total,
        "pageNum": page_num,
        "pageSize": page_size
    })


@discovery_bp.get("/discovery/featured")
def get_featured():
    limit = min(int(request.args.get("limit", 10)), 20)

    works = query_all(
        "SELECT id, name, cover AS icon, `desc`, use_count AS useCount, 'work' AS type "
        "FROM t_work_card WHERE status = 1 ORDER BY use_count DESC LIMIT %s",
        (limit // 2,)
    )

    characters = query_all(
        f"SELECT c.id, c.name, c.avatar, c.description, c.like_count AS likeCount, "
        f"c.view_count AS viewCount, c.collect_count AS collectCount, 'character' AS type "
        f"FROM t_character_card c "
        f"WHERE c.status = 1 AND c.is_public = 1 ORDER BY like_count DESC LIMIT %s",
        (limit // 2,)
    )

    featured = list(works) + list(characters)
    return success_response(featured)


@discovery_bp.get("/discovery/recommend")
def get_recommend():
    """Return works and/or characters sorted by composite recommendation score.

    Query params:
        type  — "all" (default), "work", or "character"
        pageNum  — defaults to 1
        pageSize — defaults to 12, max 50
    """
    card_type = request.args.get("type", "all")
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)

    cached = get_cached_recommendations()
    if not cached:
        # Scheduler hasn't run yet — trigger a cold refresh inline
        from ...services.recommendation import refresh_recommendations
        cached = refresh_recommendations()

    results = []
    for ct in ("works", "characters"):
        if card_type == "all" or card_type == ct.rstrip("s"):
            results.extend(cached.get(ct, {}).values())

    # Merge works + characters, sort by score descending
    results.sort(key=lambda r: r["score"], reverse=True)

    total = len(results)
    start = (page_num - 1) * page_size
    page_items = results[start:start + page_size]

    # Enrich with full card data from DB
    enriched = []
    work_ids = [int(r["card_id"]) for r in page_items if str(r["card_id"]) in cached.get("works", {})]
    char_ids = [int(r["card_id"]) for r in page_items if str(r["card_id"]) in cached.get("characters", {})]

    work_map = {}
    if work_ids:
        placeholders = ",".join(["%s"] * len(work_ids))
        rows = query_all(
            f"SELECT id, name, cover, `desc`, use_count AS useCount, "
            f"category AS categoryId, create_time AS createTime "
            f"FROM t_work_card WHERE id IN ({placeholders})",
            tuple(work_ids),
        )
        work_map = {str(r["id"]): r for r in rows}

    char_map = {}
    if char_ids:
        placeholders = ",".join(["%s"] * len(char_ids))
        rows = query_all(
            f"SELECT c.id, c.name, c.avatar, c.`desc`, c.category, c.tags, "
            f"c.like_count AS likeCount, c.view_count AS viewCount, "
            f"c.collect_count AS collectCount, c.use_count AS useCount, "
            f"c.create_time AS createTime "
            f"FROM t_character_card c WHERE c.id IN ({placeholders})",
            tuple(char_ids),
        )
        char_map = {str(r["id"]): r for r in rows}

    for item in page_items:
        cid = str(item["card_id"])
        if cid in work_map:
            w = work_map[cid]
            enriched.append({
                "id": w["id"],
                "name": w["name"],
                "icon": w.get("cover", ""),
                "desc": w.get("desc", ""),
                "useCount": w.get("useCount", 0),
                "categoryId": w.get("categoryId", 0),
                "createTime": str(w.get("createTime", "")),
                "isFree": True,
                "isVip": False,
                "_type": "work",
                "score": item["score"],
            })
        elif cid in char_map:
            c = char_map[cid]
            enriched.append({
                "id": c["id"],
                "name": c["name"],
                "icon": c.get("avatar", ""),
                "desc": c.get("desc", ""),
                "useCount": c.get("useCount", 0),
                "likeCount": c.get("likeCount", 0),
                "collectCount": c.get("collectCount", 0),
                "categoryId": c.get("category", 0),
                "createTime": str(c.get("createTime", "")),
                "isFree": True,
                "isVip": False,
                "_type": "character",
                "score": item["score"],
            })

    return page_response(enriched, total=total, page_num=page_num, page_size=page_size)
