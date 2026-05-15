from flask import jsonify


def success_response(data=None, message="success", code=0, http_status=200):
    return jsonify({"code": code, "message": message, "data": data}), http_status


def page_response(items, total, page_num, page_size, message="success"):
    return success_response(
        {
            "list": items,
            "total": total,
            "pageNum": page_num,
            "pageSize": page_size,
        },
        message=message,
    )
