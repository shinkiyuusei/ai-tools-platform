"""
Discovery API endpoints with recommendation engine integration
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...services.recommendation import RecommendationEngine
from ...extensions import get_redis_client, get_mongo_db
from ...utils.mysql import query_all, query_one
from ...utils.response import success_response

discovery_bp = Blueprint("discovery", __name__)


def get_recommendation_engine():
    """Get recommendation engine instance with cache service"""
    from ...extensions import get_redis_client, get_mongo_db
    from ...utils.mysql import get_mysql_connection
    from ...services.cache import CacheService
    
    cache_service = CacheService(get_redis_client())
    return RecommendationEngine(get_mysql_connection(), get_mongo_db(), get_redis_client(), cache_service)


@discovery_bp.get("/discovery/recommend")
@jwt_required()
def get_recommendations():
    """Get personalized recommendations for the current user"""
    user_id = int(get_jwt_identity())
    limit = min(int(request.args.get("limit", 20)), 50)
    category_id = request.args.get("categoryId", type=int)
    
    engine = get_recommendation_engine()
    recommendations = engine.get_personalized_recommendations(
        user_id=user_id,
        limit=limit,
        category_id=category_id
    )
    
    return success_response(recommendations)


@discovery_bp.get("/discovery/ranking")
def get_ranking():
    """Get ranking by time period (daily, weekly, monthly, total)"""
    period = request.args.get("period", "daily")  # daily, weekly, monthly, total
    category_id = request.args.get("categoryId", type=int)
    limit = min(int(request.args.get("limit", 50)), 100)
    
    engine = get_recommendation_engine()
    ranking = engine.get_ranking_by_period(
        period=period,
        category_id=category_id,
        limit=limit
    )
    
    return success_response(ranking)


@discovery_bp.get("/discovery/trending")
def get_trending():
    """Get trending content based on recent activity including tools and character cards"""
    limit = min(int(request.args.get("limit", 20)), 50)
    category_id = request.args.get("categoryId", type=int)
    
    # Get trending tools
    where = "status = 1"
    params = []
    if category_id:
        where += " AND category_id = %s"
        params.append(category_id)
    
    tools = query_all(
        f"SELECT id, name, icon, `desc`, tag_ids AS tagIds, use_count AS useCount, is_free AS isFree, "
        f"category_id AS categoryId, 'tool' AS type FROM t_ai_tool WHERE {where} "
        f"ORDER BY use_count DESC LIMIT %s",
        tuple(params + [limit // 2])
    )
    from .tool import _resolve_tag_names
    tools = _resolve_tag_names(tools)
    
    # Get trending character cards
    char_where = "status = 1 AND is_public = 1"
    char_params = []
    if category_id:
        char_where += " AND category_id = %s"
        char_params.append(category_id)
    
    characters = query_all(
        f"SELECT id, name, avatar, description, like_count AS likeCount, view_count AS viewCount, "
        f"collect_count AS collectCount, 'character' AS type FROM t_character_card "
        f"WHERE {char_where} ORDER BY like_count DESC LIMIT %s",
        tuple(char_params + [limit // 2])
    )
    
    # Combine and sort by engagement
    trending = tools + characters
    trending.sort(key=lambda x: x.get('useCount') or x.get('likeCount') or 0, reverse=True)
    
    return success_response(trending[:limit])


@discovery_bp.get("/discovery/categories")
def get_categories():
    """Get all categories with statistics"""
    # Get categories from database or return default categories
    categories = [
        {"id": 1, "name": "恋爱", "color": "crimson", "icon": "ri-heart-line"},
        {"id": 2, "name": "角色", "color": "candy", "icon": "ri-user-line"},
        {"id": 3, "name": "剧情", "color": "misty", "icon": "ri-book-line"},
        {"id": 4, "name": "幻想", "color": "green", "icon": "ri-magic-line"},
        {"id": 5, "name": "日常", "color": "silver", "icon": "ri-home-line"},
    ]
    
    # Add count for each category
    for cat in categories:
        count = query_one(
            "SELECT COUNT(*) as count FROM t_ai_tool WHERE category_id = %s AND status = 1",
            (cat["id"],)
        )
        cat["count"] = count["count"] if count else 0
    
    return success_response(categories)


@discovery_bp.get("/discovery/search")
def advanced_search():
    """Advanced search with filters and sorting"""
    keyword = request.args.get("keyword", "")
    category_id = request.args.get("categoryId", type=int)
    sort_type = request.args.get("sortType", "relevance")  # relevance, hot, new, rating
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    tags = request.args.get("tags", "").split(",") if request.args.get("tags") else []
    
    where = ["status = 1"]
    params = []
    
    if keyword:
        where.append("(name LIKE %s OR `desc` LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    if category_id:
        where.append("category_id = %s")
        params.append(category_id)
    
    if tags:
        for tag in tags:
            if tag.strip():
                where.append("FIND_IN_SET(%s, tag_ids) > 0")
                params.append(tag.strip())
    
    where_clause = " AND ".join(where)
    
    # Sorting logic
    order_map = {
        "relevance": "use_count DESC",  # Simple relevance based on popularity
        "hot": "use_count DESC",
        "new": "create_time DESC",
        "rating": "(use_count / GREATEST(DATEDIFF(NOW(), create_time), 1)) DESC"
    }
    order_clause = order_map.get(sort_type, "use_count DESC")
    
    # Get total count
    count_sql = f"SELECT COUNT(*) AS total FROM t_ai_tool WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]
    
    # Get paginated results
    data_sql = (
        f"SELECT id, name, icon, `desc`, tag_ids AS tagIds, use_count AS useCount, is_free AS isFree, "
        f"is_vip AS isVip, category_id AS categoryId, create_time AS createTime "
        f"FROM t_ai_tool WHERE {where_clause} ORDER BY {order_clause} LIMIT %s OFFSET %s"
    )
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))
    from .tool import _resolve_tag_names
    items = _resolve_tag_names(items)

    return success_response({
        "list": items,
        "total": total,
        "pageNum": page_num,
        "pageSize": page_size
    })


@discovery_bp.get("/discovery/featured")
def get_featured():
    """Get featured/curated content including tools and character cards"""
    limit = min(int(request.args.get("limit", 10)), 20)
    
    # Get featured tools
    tools = query_all(
        "SELECT id, name, icon, `desc`, tag_ids AS tagIds, use_count AS useCount, is_free AS isFree, "
        "category_id AS categoryId, 'tool' AS type FROM t_ai_tool WHERE status = 1 "
        "ORDER BY use_count DESC LIMIT %s",
        (limit // 2,)
    )
    from .tool import _resolve_tag_names
    tools = _resolve_tag_names(tools)
    
    # Get featured character cards
    characters = query_all(
        "SELECT id, name, avatar, description, like_count AS likeCount, view_count AS viewCount, "
        "collect_count AS collectCount, 'character' AS type FROM t_character_card "
        "WHERE status = 1 AND is_public = 1 ORDER BY like_count DESC LIMIT %s",
        (limit // 2,)
    )
    
    # Combine and shuffle
    featured = tools + characters
    
    return success_response(featured)
