"""
Internationalization API endpoints
"""
from flask import Blueprint, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity

from ...services.i18n import get_supported_languages, validate_language, translate
from ...utils.response import success_response

i18n_bp = Blueprint("i18n", __name__)


@i18n_bp.get("/i18n/languages")
def get_languages():
    """Get list of supported languages"""
    languages = get_supported_languages()
    return success_response(languages)


@i18n_bp.post("/i18n/language")
@jwt_required()
def set_user_language():
    """Set user's preferred language"""
    user_id = int(get_jwt_identity())
    payload = request.get_json(silent=True) or {}
    lang = payload.get("language")
    
    if not lang:
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, "Language code is required")
    
    if not validate_language(lang):
        from ...core.errors import AppError, ErrorCode
        raise AppError(ErrorCode.PARAM_INVALID, f"Unsupported language: {lang}")
    
    # Store user's language preference in MongoDB
    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    mongo_db["t_user_settings"].update_one(
        {"userId": user_id},
        {"$set": {"language": lang}},
        upsert=True
    )
    
    # Set in current request context
    g.user_language = lang
    
    return success_response({
        "language": lang,
        "message": translate("success")
    })


@i18n_bp.get("/i18n/language")
@jwt_required()
def get_user_language():
    """Get user's preferred language"""
    user_id = int(get_jwt_identity())
    
    from ...extensions import get_mongo_db
    mongo_db = get_mongo_db()
    user_settings = mongo_db["t_user_settings"].find_one({"userId": user_id})
    
    current_lang = user_settings.get("language") if user_settings else "zh"
    
    return success_response({
        "language": current_lang
    })
