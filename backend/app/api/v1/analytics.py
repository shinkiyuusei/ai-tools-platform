"""
Analytics API endpoints for user behavior tracking and insights.
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ...services.analytics import AnalyticsService
from ...extensions import get_redis_client
from ...utils.response import success_response

analytics_bp = Blueprint("analytics", __name__)


def get_analytics_service():
    return AnalyticsService(get_redis_client())


@analytics_bp.post("/analytics/event")
def track_event():
    """Track a user event for analytics."""
    payload = request.get_json(silent=True) or {}
    event_type = payload.get("eventType")
    event_data = payload.get("data", {})

    if not event_type:
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, "eventType is required")

    user_id = None
    try:
        from flask_jwt_extended import verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            user_id = int(user_id)
    except:
        pass

    event_data["ipAddress"] = request.remote_addr
    event_data["userAgent"] = request.headers.get("User-Agent", "")

    service = get_analytics_service()
    service.track_event(event_type, user_id, event_data)

    return success_response({"success": True})


@analytics_bp.get("/analytics/user")
@jwt_required()
def get_user_analytics():
    """Get analytics data for the current user."""
    user_id = int(get_jwt_identity())
    days = min(int(request.args.get("days", 30)), 90)

    service = get_analytics_service()
    analytics = service.get_user_analytics(user_id, days)

    return success_response(analytics)


@analytics_bp.get("/analytics/platform")
def get_platform_analytics():
    """Get platform-wide analytics."""
    days = min(int(request.args.get("days", 7)), 30)

    service = get_analytics_service()
    analytics = service.get_platform_analytics(days)

    return success_response(analytics)
