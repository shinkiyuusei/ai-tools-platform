"""
Character card API endpoints
"""
import os
import uuid
from flask import Blueprint, request, current_app
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from ...utils.crud import dynamic_update
from ...utils.mysql import query_one, query_all, execute
from ...utils.response import success_response
from ...core.errors import AppError, ErrorCode

character_bp = Blueprint("character", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024

_CHARACTER_RATING_JOIN = (
    "LEFT JOIN (SELECT work_id, ROUND(AVG(score), 1) AS avg_rating "
    "FROM t_rating WHERE work_type = 'character' GROUP BY work_id) r "
    "ON c.id = r.work_id"
)
_CHARACTER_RATING_SELECT = "COALESCE(r.avg_rating, 0) AS rating"


def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@character_bp.post("/character/upload")
@jwt_required()
def upload_avatar():
    """Upload character avatar image"""
    if 'file' not in request.files:
        raise AppError(ErrorCode.PARAM_INVALID, "No file provided")
    
    file = request.files['file']
    if file.filename == '':
        raise AppError(ErrorCode.PARAM_INVALID, "No file selected")
    
    if not allowed_file(file.filename):
        raise AppError(ErrorCode.PARAM_INVALID, "File type not allowed")
    
    if file.content_length > MAX_FILE_SIZE:
        raise AppError(ErrorCode.PARAM_INVALID, "File too large (max 5MB)")
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(current_app.root_path, '..', 'uploads', 'characters')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Return public URL
    url = f"/uploads/characters/{filename}"
    
    return success_response({"url": url})


@character_bp.get("/character/list")
def get_character_list():
    """Get character card list with filters"""
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    user_id = request.args.get("userId", type=int)
    sort_type = request.args.get("sortType", "new")  # new, hot, like
    keyword = request.args.get("keyword", "")

    where = ["status = 1", "is_public = 1"]
    params = []

    if user_id:
        where.append("user_id = %s")
        params.append(user_id)
    
    if keyword:
        where.append("(name LIKE %s OR description LIKE %s)")
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    
    where_clause = " AND ".join(where)
    
    # Sorting
    order_map = {
        "new": "create_time DESC",
        "hot": "view_count DESC",
        "like": "like_count DESC"
    }
    order_clause = order_map.get(sort_type, "create_time DESC")
    
    # Get total count
    count_sql = f"SELECT COUNT(*) AS total FROM t_character_card WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]
    
    # Get paginated results with rating from t_rating
    data_sql = (
        f"SELECT c.id, c.user_id, c.name, c.avatar, c.description, c.personality, c.background, c.tags, "
        f"c.is_public, c.like_count, c.view_count, c.collect_count, c.create_time, "
        f"{_CHARACTER_RATING_SELECT} "
        f"FROM t_character_card c "
        f"{_CHARACTER_RATING_JOIN} "
        f"WHERE {where_clause} "
        f"ORDER BY {order_clause} LIMIT %s OFFSET %s"
    )
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))

    return success_response({
        "list": items,
        "total": total,
        "pageNum": page_num,
        "pageSize": page_size
    })


@character_bp.get("/character/<int:character_id>")
def get_character_detail(character_id: int):
    """Get character card detail"""
    character = query_one(
        f"SELECT c.id, c.user_id, c.name, c.avatar, c.description, c.personality, c.background, c.tags, "
        f"c.is_public, c.like_count, c.view_count, c.collect_count, c.create_time, "
        f"{_CHARACTER_RATING_SELECT} "
        f"FROM t_character_card c "
        f"{_CHARACTER_RATING_JOIN} "
        f"WHERE c.id = %s AND c.status = 1",
        (character_id,)
    )
    
    if not character:
        raise AppError(ErrorCode.NOT_FOUND, "Character not found")
    
    # Increment view count
    execute("UPDATE t_character_card SET view_count = view_count + 1 WHERE id = %s", (character_id,))
    
    return success_response(character)


@character_bp.post("/character")
@jwt_required()
def create_character():
    """Create character card"""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    
    name = payload.get("name")
    avatar = payload.get("avatar", "")
    description = payload.get("description", "")
    personality = payload.get("personality", "")
    background = payload.get("background", "")
    tags = payload.get("tags", "")
    is_public = payload.get("isPublic", 1)

    if not name:
        raise AppError(ErrorCode.PARAM_INVALID, "name is required")

    character_id = execute(
        "INSERT INTO t_character_card "
        "(user_id, name, avatar, description, personality, background, tags, is_public) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, name, avatar, description, personality, background, tags, is_public)
    )
    
    return success_response({"id": character_id})


@character_bp.put("/character/<int:character_id>")
@jwt_required()
def update_character(character_id: int):
    """Update character card"""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    
    # Check ownership
    character = query_one(
        "SELECT user_id FROM t_character_card WHERE id = %s",
        (character_id,)
    )
    
    if not character:
        raise AppError(ErrorCode.NOT_FOUND, "Character not found")
    
    if character["user_id"] != user_id:
        raise AppError(ErrorCode.PERMISSION_DENIED, "Permission denied")
    
    dynamic_update("t_character_card", {
        "name": "name",
        "avatar": "avatar",
        "description": "description",
        "personality": "personality",
        "background": "background",
        "tags": "tags",
        "isPublic": "is_public",
    }, payload, "id", character_id)
    return success_response({"success": True})


@character_bp.delete("/character/<int:character_id>")
@jwt_required()
def delete_character(character_id: int):
    """Delete character card"""
    user_id = int(get_jwt_identity())
    
    # Check ownership
    character = query_one(
        "SELECT user_id FROM t_character_card WHERE id = %s",
        (character_id,)
    )
    
    if not character:
        raise AppError(ErrorCode.NOT_FOUND, "Character not found")
    
    if character["user_id"] != user_id:
        raise AppError(ErrorCode.PERMISSION_DENIED, "Permission denied")
    
    # Soft delete
    execute("UPDATE t_character_card SET status = 0 WHERE id = %s", (character_id,))
    
    return success_response({"success": True})


@character_bp.post("/character/<int:character_id>/like")
@jwt_required()
def like_character(character_id: int):
    """Like character card"""
    user_id = int(get_jwt_identity())
    
    # Check if already liked
    existing = query_one(
        "SELECT id FROM t_character_like WHERE user_id = %s AND character_id = %s",
        (user_id, character_id)
    )
    
    if existing:
        # Unlike
        execute("DELETE FROM t_character_like WHERE user_id = %s AND character_id = %s", (user_id, character_id))
        execute("UPDATE t_character_card SET like_count = like_count - 1 WHERE id = %s", (character_id,))
        return success_response({"liked": False})
    else:
        # Like
        execute("INSERT INTO t_character_like (user_id, character_id) VALUES (%s, %s)", (user_id, character_id))
        execute("UPDATE t_character_card SET like_count = like_count + 1 WHERE id = %s", (character_id,))
        return success_response({"liked": True})


@character_bp.post("/character/<int:character_id>/collect")
@jwt_required()
def collect_character(character_id: int):
    """Collect character card"""
    user_id = int(get_jwt_identity())
    
    # Check if already collected
    existing = query_one(
        "SELECT id FROM t_character_collect WHERE user_id = %s AND character_id = %s",
        (user_id, character_id)
    )
    
    if existing:
        # Uncollect
        execute("DELETE FROM t_character_collect WHERE user_id = %s AND character_id = %s", (user_id, character_id))
        execute("UPDATE t_character_card SET collect_count = collect_count - 1 WHERE id = %s", (character_id,))
        return success_response({"collected": False})
    else:
        # Collect
        execute("INSERT INTO t_character_collect (user_id, character_id) VALUES (%s, %s)", (user_id, character_id))
        execute("UPDATE t_character_card SET collect_count = collect_count + 1 WHERE id = %s", (character_id,))
        return success_response({"collected": True})


@character_bp.get("/character/my")
@jwt_required()
def get_my_characters():
    """Get user's character cards"""
    user_id = int(get_jwt_identity())
    page_num = int(request.args.get("pageNum", 1))
    page_size = min(int(request.args.get("pageSize", 12)), 50)
    
    where = ["user_id = %s", "status = 1"]
    params = [user_id]
    
    where_clause = " AND ".join(where)
    
    # Get total count
    count_sql = f"SELECT COUNT(*) AS total FROM t_character_card WHERE {where_clause}"
    total_row = query_one(count_sql, tuple(params))
    total = total_row["total"]
    
    # Get paginated results with rating
    data_sql = (
        f"SELECT c.id, c.name, c.avatar, c.description, c.personality, c.background, c.tags, "
        f"c.is_public, c.like_count, c.view_count, c.collect_count, c.create_time, "
        f"{_CHARACTER_RATING_SELECT} "
        f"FROM t_character_card c "
        f"{_CHARACTER_RATING_JOIN} "
        f"WHERE {where_clause} "
        f"ORDER BY create_time DESC LIMIT %s OFFSET %s"
    )
    params.extend([page_size, (page_num - 1) * page_size])
    items = query_all(data_sql, tuple(params))
    
    return success_response({
        "list": items,
        "total": total,
        "pageNum": page_num,
        "pageSize": page_size
    })
