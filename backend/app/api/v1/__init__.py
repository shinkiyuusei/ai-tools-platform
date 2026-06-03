from flask import Blueprint

from .admin import admin_bp
from .ai import ai_bp
from .analytics import analytics_bp
from .character import character_bp
from .chat import chat_bp
from .conversation import conv_bp
from .discovery import discovery_bp
from .home import home_bp
from .i18n import i18n_bp
from .monitoring import monitoring_bp
from .recharge import recharge_bp
from .user import user_bp


def register_v1_blueprints(app):
    api_v1 = Blueprint("api_v1", __name__, url_prefix=app.config["API_PREFIX"])

    api_v1.register_blueprint(home_bp)
    api_v1.register_blueprint(user_bp)
    api_v1.register_blueprint(ai_bp)
    api_v1.register_blueprint(admin_bp)
    api_v1.register_blueprint(i18n_bp)
    api_v1.register_blueprint(discovery_bp)
    api_v1.register_blueprint(analytics_bp)
    api_v1.register_blueprint(monitoring_bp)
    api_v1.register_blueprint(character_bp)
    api_v1.register_blueprint(recharge_bp)
    api_v1.register_blueprint(chat_bp)
    api_v1.register_blueprint(conv_bp)

    app.register_blueprint(api_v1)
