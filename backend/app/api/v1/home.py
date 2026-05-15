from flask import Blueprint, request

from ...utils.mysql import query_all
from ...utils.response import success_response

home_bp = Blueprint("home", __name__)


@home_bp.get("/home/index")
def home_index():
    categories = query_all(
        "SELECT id, name, icon FROM t_tool_category WHERE parent_id = 0 ORDER BY sort_order ASC"
    )
    hot_tools = query_all(
        "SELECT id, name, icon, `desc`, use_count AS useCount FROM t_ai_tool WHERE status = 1 ORDER BY use_count DESC LIMIT 8"
    )
    data = {
        "bannerList": [
            {"id": 1, "imgUrl": "/static/banner-1.png", "jumpUrl": "/explore?featured=1"},
            {"id": 2, "imgUrl": "/static/banner-2.png", "jumpUrl": "/explore?category=1"},
        ],
        "categoryList": categories,
        "hotToolList": hot_tools,
    }
    return success_response(data)


@home_bp.get("/tool/search")
def tool_search():
    keyword = request.args.get("keyword", "")
    if not keyword:
        return success_response({"list": [], "total": 0})

    like = f"%{keyword}%"
    items = query_all(
        "SELECT id, name, icon, `desc` FROM t_ai_tool WHERE status = 1 AND name LIKE %s ORDER BY use_count DESC LIMIT 10",
        (like,),
    )
    total = len(items)
    return success_response({"list": items, "total": total})
