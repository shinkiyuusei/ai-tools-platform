"""User rating API for works and character cards."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from ...core.errors import AppError, ErrorCode
from ...utils.mysql import execute, query_one
from ...utils.response import success_response
from ...utils.snowflake import generate_id

rating_bp = Blueprint("rating", __name__)


def _get_user_id():
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        return int(identity) if identity else 0
    except Exception:
        return 0


@rating_bp.post("/rating")
@jwt_required()
def submit_rating():
    """Submit or update a rating for a work or character card."""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}

    work_type = payload.get("workType", "").strip()
    if work_type not in ("tool", "character"):
        raise AppError(ErrorCode.PARAM_INVALID, "workType 必须为 tool 或 character")

    work_id = int(payload.get("workId", 0))
    if not work_id:
        raise AppError(ErrorCode.PARAM_INVALID, "workId 不能为空")

    score = int(payload.get("score", 0))
    if score < 1 or score > 5:
        raise AppError(ErrorCode.PARAM_INVALID, "评分范围为 1-5")

    # Verify work exists
    table = "t_ai_tool" if work_type == "tool" else "t_character_card"
    existing = query_one(f"SELECT id FROM {table} WHERE id = %s AND status = 1", (work_id,))
    if not existing:
        raise AppError(ErrorCode.RESOURCE_NOT_FOUND, "作品不存在或已下架")

    rating_id = generate_id()
    execute(
        """INSERT INTO t_rating (id, user_id, work_type, work_id, score)
           VALUES (%s, %s, %s, %s, %s)
           ON DUPLICATE KEY UPDATE score = VALUES(score)""",
        (rating_id, user_id, work_type, work_id, score),
    )

    # Recalculate and update average score on the work table
    _sync_avg_score(work_type, work_id)

    return success_response({"message": "评分成功", "score": score})


@rating_bp.get("/rating/<work_type>/<int:work_id>")
def get_ratings(work_type: str, work_id: int):
    """Get ratings summary and current user's rating."""
    if work_type not in ("tool", "character"):
        raise AppError(ErrorCode.PARAM_INVALID, "workType 必须为 tool 或 character")

    user_id = _get_user_id()

    avg_row = query_one(
        """SELECT COUNT(*) AS count, ROUND(AVG(score), 1) AS average
           FROM t_rating WHERE work_type = %s AND work_id = %s""",
        (work_type, work_id),
    )

    my_score = 0
    if user_id:
        my_row = query_one(
            "SELECT score FROM t_rating WHERE user_id = %s AND work_type = %s AND work_id = %s",
            (user_id, work_type, work_id),
        )
        if my_row:
            my_score = my_row["score"]

    return success_response({
        "count": avg_row["count"] or 0,
        "average": float(avg_row["average"] or 0),
        "myScore": my_score,
    })


def _sync_avg_score(work_type: str, work_id: int):
    """Update the cached rating on the work/character table."""
    avg_row = query_one(
        "SELECT ROUND(AVG(score), 1) AS average FROM t_rating WHERE work_type = %s AND work_id = %s",
        (work_type, work_id),
    )
    if not avg_row or avg_row["average"] is None:
        return

    import json
    if work_type == "tool":
        tool = query_one("SELECT form_config FROM t_ai_tool WHERE id = %s", (work_id,))
        if tool:
            config = {}
            if tool.get("form_config"):
                try:
                    config = json.loads(tool["form_config"])
                except (json.JSONDecodeError, TypeError):
                    config = {}
            config["rating"] = float(avg_row["average"])
            execute(
                "UPDATE t_ai_tool SET form_config = %s WHERE id = %s",
                (json.dumps(config, ensure_ascii=False), work_id),
            )
    else:
        # Character card ratings are computed in real time via LEFT JOIN on t_rating,
        # so no caching to the character table is needed.
        pass
