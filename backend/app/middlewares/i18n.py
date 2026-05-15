"""
Internationalization middleware for language detection and handling
"""
from flask import g, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def language_middleware():
    """
    Middleware to detect and set the user's language preference
    Priority: URL parameter > User profile > Accept-Language header > Default
    """
    # Check URL parameter first
    lang = request.args.get('lang')
    if lang:
        g.user_language = lang
        return
    
    # Check if user is authenticated and has language preference
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            # TODO: Fetch user's language preference from database
            # For now, default to None which will use Accept-Language header
            pass
    except:
        pass
    
    # Language will be determined by Babel's locale_selector in i18n.py
