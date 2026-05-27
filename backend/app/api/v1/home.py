from flask import Blueprint, request

from ...utils.categories import CATEGORIES
from ...utils.mysql import query_all
from ...utils.response import success_response
from ...services.cache import cache_get, cache_set

home_bp = Blueprint("home", __name__)

HOME_CACHE_KEY = "home:index"


@home_bp.get("/home/index")
def home_index():
    cached = cache_get(HOME_CACHE_KEY)
    if cached:
        return success_response(cached)

    hot_tools = query_all(
        "SELECT id, name, cover AS icon, `desc`, use_count AS useCount "
        "FROM t_work_card WHERE status = 1 ORDER BY use_count DESC LIMIT 8"
    )
    data = {
        "bannerList": [],
        "categoryList": CATEGORIES,
        "hotToolList": hot_tools,
    }
    cache_set(HOME_CACHE_KEY, data, ttl=60)
    return success_response(data)
