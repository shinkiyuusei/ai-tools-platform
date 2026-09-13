"""SillyTavern-compatible API layer.

This package mirrors the REST contract of SillyTavern sections 4.2 and 4.3:

* /api/characters/*, /api/chats/*, /api/groups/*, /api/worldinfo/*
* /api/settings/*, /api/presets/*, /api/themes/*, /api/moving-ui/*,
  /api/quick-replies/*, /api/secrets/*

Data is stored per platform user under ST_COMPAT_DATA_DIR/<user_id>/ using the
same file layout as SillyTavern (PNG-embedded character cards, JSONL chats,
JSON world info files, etc.), so existing SillyTavern exports can be reused.
"""

from flask import Blueprint

from .characters import characters_bp
from .chats import chats_bp
from .groups import groups_bp
from .moving_ui import moving_ui_bp
from .presets import presets_bp
from .quick_replies import quick_replies_bp
from .secrets import secrets_bp
from .settings import settings_bp
from .themes import themes_bp
from .worldinfo import worldinfo_bp


def register_st_compat_blueprints(app):
    """Register all SillyTavern-compatible routes under /api."""
    if not app.config.get("ST_COMPAT_ENABLED", True):
        return

    api = Blueprint("st_compat", __name__, url_prefix="/api")
    api.register_blueprint(characters_bp)
    api.register_blueprint(chats_bp)
    api.register_blueprint(groups_bp)
    api.register_blueprint(worldinfo_bp)
    api.register_blueprint(settings_bp)
    api.register_blueprint(presets_bp)
    api.register_blueprint(themes_bp)
    api.register_blueprint(moving_ui_bp)
    api.register_blueprint(quick_replies_bp)
    api.register_blueprint(secrets_bp)
    app.register_blueprint(api)
