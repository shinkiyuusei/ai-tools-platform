"""
Internationalization (i18n) service for multilingual support
"""
from flask import request, g
from flask_babel import Babel, gettext as _

# Initialize Babel
babel = Babel()

# Supported languages
SUPPORTED_LANGUAGES = ['zh', 'en', 'ja', 'ko']
LANGUAGE_NAMES = {
    'zh': '中文',
    'en': 'English',
    'ja': '日本語',
    'ko': '한국어'
}

_API_MESSAGES = {
    "success": {"en": "Success", "ja": "成功しました", "ko": "성공했습니다"},
    "error": {"en": "Request failed", "ja": "リクエストに失敗しました", "ko": "요청에 실패했습니다"},
    "invalid_parameter": {"en": "Invalid request", "ja": "無効なリクエストです", "ko": "잘못된 요청입니다"},
    "not_found": {"en": "Resource not found", "ja": "リソースが見つかりません", "ko": "리소스를 찾을 수 없습니다"},
    "unauthorized": {"en": "Authentication required", "ja": "認証が必要です", "ko": "인증이 필요합니다"},
    "forbidden": {"en": "You do not have permission for this action", "ja": "この操作を行う権限がありません", "ko": "이 작업을 수행할 권한이 없습니다"},
    "user_not_found": {"en": "User not found", "ja": "ユーザーが見つかりません", "ko": "사용자를 찾을 수 없습니다"},
    "generate_failed": {"en": "Generation failed", "ja": "生成に失敗しました", "ko": "생성에 실패했습니다"},
    "server_error": {"en": "Server error", "ja": "サーバーエラー", "ko": "서버 오류"},
}

_ERROR_KEYS = {
    10001: "invalid_parameter", 10002: "not_found", 20001: "unauthorized",
    20003: "forbidden", 20004: "user_not_found", 30001: "generate_failed",
}


def get_locale():
    """
    Determine the best matching language for the current request
    Priority: URL parameter > User preference > Accept-Language header > Default
    """
    # Check URL parameter first
    lang = request.args.get('lang')
    if lang and lang in SUPPORTED_LANGUAGES:
        return lang
    
    # Check user preference from JWT token if authenticated
    if hasattr(g, 'user_language'):
        return g.user_language
    
    # Check Accept-Language header
    if request.accept_languages:
        best_match = request.accept_languages.best_match(SUPPORTED_LANGUAGES)
        if best_match:
            return best_match
    
    # Default to Chinese
    return 'zh'


def init_babel(app):
    """Initialize Babel with the Flask app"""
    babel.init_app(app, locale_selector=get_locale)
    return babel


def translate(message, **kwargs):
    """Translate a message using the current locale"""
    return _(message, **kwargs)


def localize_api_message(message: str, error_code: int | None = None) -> str:
    """Return a complete, locale-aware API message without exposing source text.

    Existing endpoints still pass descriptive Chinese messages.  Error codes are
    stable API contracts, so use them as the translation key and keep detailed
    source text only for the default Chinese locale.
    """
    locale = get_locale()
    if locale == "zh":
        return message
    key = _ERROR_KEYS.get(error_code, "error") if error_code is not None else "success"
    return _API_MESSAGES[key].get(locale, _API_MESSAGES[key]["en"])


def get_supported_languages():
    """Get list of supported languages with their names"""
    return [
        {'code': code, 'name': name}
        for code, name in LANGUAGE_NAMES.items()
    ]


def validate_language(lang_code):
    """Validate if a language code is supported"""
    return lang_code in SUPPORTED_LANGUAGES
