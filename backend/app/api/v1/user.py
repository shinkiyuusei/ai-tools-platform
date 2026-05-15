from flask import Blueprint, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required

from ...core.errors import AppError, ErrorCode
from ...extensions import get_redis_client
from ...utils.mysql import execute, query_one, query_all
from ...utils.response import page_response, success_response
from ...utils.security import check_password, hash_password
from ...utils.snowflake import generate_id

user_bp = Blueprint("user", __name__)


@user_bp.post("/user/sendCode")
def send_code():
    payload = request.get_json(silent=True) or {}
    target = payload.get("phone") or payload.get("email")
    code_type = payload.get("type", "register")
    if not target:
        raise AppError(ErrorCode.PARAM_INVALID, "手机号或邮箱不能为空")

    redis_client = get_redis_client()
    code = "888888"
    key = f"verify_code:{code_type}:{target}"
    redis_client.setex(key, 300, code)
    return success_response({"success": True, "message": "验证码已发送"})


@user_bp.post("/user/register")
def register():
    payload = request.get_json(silent=True) or {}
    phone = payload.get("phone", "")
    email = payload.get("email", "")
    code = payload.get("code", "")
    password = payload.get("password", "")

    if not phone and not email:
        raise AppError(ErrorCode.PARAM_INVALID, "手机号或邮箱不能为空")
    if not code:
        raise AppError(ErrorCode.PARAM_INVALID, "验证码不能为空")
    if not password or len(password) < 6:
        raise AppError(ErrorCode.PARAM_INVALID, "密码长度不能少于6位")

    target = phone or email
    redis_client = get_redis_client()
    stored_code = redis_client.get(f"verify_code:register:{target}")
    if stored_code != code:
        raise AppError(ErrorCode.PARAM_INVALID, "验证码错误或已过期")

    existing = query_one(
        "SELECT id FROM t_user WHERE (phone = %s AND phone != '') OR (email = %s AND email != '') AND is_delete = 0",
        (phone, email),
    )
    if existing:
        raise AppError(ErrorCode.PARAM_INVALID, "该手机号或邮箱已注册")

    user_id = generate_id()
    hashed = hash_password(password)
    nickname = f"用户{str(user_id)[-6:]}"
    execute(
        "INSERT INTO t_user (id, phone, email, password, nickname) VALUES (%s,%s,%s,%s,%s)",
        (user_id, phone, email, hashed, nickname),
    )
    redis_client.delete(f"verify_code:register:{target}")

    return success_response(
        {
            "token": create_access_token(identity=str(user_id)),
            "refreshToken": create_refresh_token(identity=str(user_id)),
            "userInfo": {"id": user_id, "nickname": nickname, "avatar": "", "vipLevel": 0},
        }
    )


@user_bp.post("/user/login")
def login():
    payload = request.get_json(silent=True) or {}
    account = payload.get("account", "")
    password = payload.get("password", "")
    remember = payload.get("remember", False)

    if not account or not password:
        raise AppError(ErrorCode.PARAM_INVALID, "账号和密码不能为空")

    user = query_one(
        "SELECT * FROM t_user WHERE (phone = %s OR email = %s) AND is_delete = 0",
        (account, account),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "账号不存在")

    if user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号已被封禁")

    if not check_password(password, user["password"]):
        raise AppError(ErrorCode.UNAUTHORIZED, "密码错误")

    token_kwargs = {}
    if remember:
        token_kwargs["expires_delta"] = None

    return success_response(
        {
            "token": create_access_token(identity=str(user["id"]), **token_kwargs),
            "refreshToken": create_refresh_token(identity=str(user["id"])),
            "userInfo": {
                "id": user["id"],
                "nickname": user["nickname"],
                "avatar": user["avatar"],
                "vipLevel": user["vip_level"],
                "phone": user["phone"],
                "email": user["email"],
            },
        }
    )


@user_bp.post("/user/resetPassword")
def reset_password():
    payload = request.get_json(silent=True) or {}
    account = payload.get("account", "")
    code = payload.get("code", "")
    new_password = payload.get("newPassword", "")

    if not account:
        raise AppError(ErrorCode.PARAM_INVALID, "账号不能为空")
    if not code:
        raise AppError(ErrorCode.PARAM_INVALID, "验证码不能为空")
    if not new_password or len(new_password) < 6:
        raise AppError(ErrorCode.PARAM_INVALID, "新密码长度不能少于6位")

    redis_client = get_redis_client()
    stored_code = redis_client.get(f"verify_code:reset:{account}")
    if stored_code != code:
        raise AppError(ErrorCode.PARAM_INVALID, "验证码错误或已过期")

    user = query_one(
        "SELECT id FROM t_user WHERE (phone = %s OR email = %s) AND is_delete = 0",
        (account, account),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "账号不存在")

    hashed = hash_password(new_password)
    execute("UPDATE t_user SET password = %s WHERE id = %s", (hashed, user["id"]))
    redis_client.delete(f"verify_code:reset:{account}")

    return success_response({"success": True, "message": "密码重置成功"})


@user_bp.get("/user/info")
@jwt_required()
def get_user_info():
    user_id = int(get_jwt_identity())
    user = query_one(
        "SELECT id,phone,email,nickname,avatar,vip_level,vip_expire_time,status FROM t_user WHERE id = %s AND is_delete = 0",
        (user_id,),
    )
    if not user:
        raise AppError(ErrorCode.USER_NOT_FOUND, "用户不存在")
    if user["status"] != 1:
        raise AppError(ErrorCode.FORBIDDEN, "账号已被封禁")

    return success_response(
        {
            "id": user["id"],
            "nickname": user["nickname"],
            "avatar": user["avatar"],
            "vipLevel": user["vip_level"],
            "vipExpireTime": user["vip_expire_time"].isoformat() if user["vip_expire_time"] else None,
            "phone": user["phone"],
            "email": user["email"],
        }
    )


@user_bp.post("/user/info/update")
@jwt_required()
def update_user_info():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    nickname = payload.get("nickname")
    avatar = payload.get("avatar")

    fields = []
    values = []
    if nickname:
        fields.append("nickname = %s")
        values.append(nickname)
    if avatar:
        fields.append("avatar = %s")
        values.append(avatar)
    if not fields:
        raise AppError(ErrorCode.PARAM_INVALID, "没有需要修改的内容")

    values.append(user_id)
    execute(f"UPDATE t_user SET {', '.join(fields)} WHERE id = %s", tuple(values))
    return success_response({"success": True, "message": "个人信息更新成功"})


@user_bp.get("/user/record/list")
@jwt_required()
def record_list():
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 10)), 50)
    tool_id = request.args.get("toolId", type=int)
    start_time = request.args.get("startTime")
    end_time = request.args.get("endTime")

    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    match = {"userId": user_id}
    if tool_id:
        match["toolId"] = tool_id
    if start_time or end_time:
        match["createTime"] = {}
        if start_time:
            match["createTime"]["$gte"] = start_time
        if end_time:
            match["createTime"]["$lte"] = end_time

    total = mongo_db["t_generate_record"].count_documents(match)
    cursor = (
        mongo_db["t_generate_record"]
        .find(match)
        .sort("createTime", -1)
        .skip((page_num - 1) * page_size)
        .limit(page_size)
    )
    items = []
    for doc in cursor:
        items.append(
            {
                "recordId": doc["recordId"],
                "toolId": doc["toolId"],
                "toolName": doc["toolName"],
                "result": doc.get("result", ""),
                "status": doc.get("status", 1),
                "createTime": doc["createTime"].isoformat() if doc.get("createTime") else "",
                "isCollected": doc.get("isCollected", 0),
            }
        )
    return page_response(items, total=total, page_num=page_num, page_size=page_size)


@user_bp.post("/user/record/collect")
@jwt_required()
def collect_record():
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    record_id = payload.get("recordId", "")
    if not record_id:
        raise AppError(ErrorCode.PARAM_INVALID, "记录ID不能为空")

    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    record = mongo_db["t_generate_record"].find_one({"recordId": record_id, "userId": user_id})
    if not record:
        raise AppError(ErrorCode.PARAM_INVALID, "生成记录不存在")

    new_state = 0 if record.get("isCollected") else 1
    mongo_db["t_generate_record"].update_one(
        {"recordId": record_id}, {"$set": {"isCollected": new_state}}
    )
    return success_response({"success": True, "message": "收藏" if new_state else "已取消收藏"})
