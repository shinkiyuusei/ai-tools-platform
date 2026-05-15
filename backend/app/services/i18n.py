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


def get_supported_languages():
    """Get list of supported languages with their names"""
    return [
        {'code': code, 'name': name}
        for code, name in LANGUAGE_NAMES.items()
    ]


def validate_language(lang_code):
    """Validate if a language code is supported"""
    return lang_code in SUPPORTED_LANGUAGES
