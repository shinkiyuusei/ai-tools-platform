import logging
import secrets

from flask import Flask
from flask import send_from_directory

from .api.v1 import register_v1_blueprints
from .core.config import get_config
from .core.errors import register_error_handlers
from .extensions import init_extensions
from .middlewares.response import register_response_hooks
from .middlewares.security import add_security_headers
from .services.i18n import init_babel
from .utils.logger import setup_logging


def _validate_secrets(app: Flask):
    """Refuse to start if SECRET_KEY or JWT_SECRET_KEY are unset.

    In DEBUG mode a random key is generated so local development works
    without .env, but a warning is emitted.
    """
    for key, label in [("SECRET_KEY", "SECRET_KEY"), ("JWT_SECRET_KEY", "JWT_SECRET_KEY")]:
        value = app.config.get(key, "")
        if not value:
            if app.config.get("DEBUG"):
                generated = secrets.token_hex(32)
                app.config[key] = generated
                logging.getLogger(__name__).warning(
                    "%s is not set — using random value for development: %s", key, generated
                )
            else:
                raise RuntimeError(
                    f"{label} is not set. Set it via the {key} environment variable."
                )


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

    _validate_secrets(app)

    # Setup logging first
    logger = setup_logging(app)
    
    init_extensions(app)
    init_babel(app)
    register_v1_blueprints(app)
    register_error_handlers(app)
    register_response_hooks(app)
    
    # Register security headers middleware
    app.after_request(add_security_headers)

    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def serve_upload(filename):
        return send_from_directory('uploads', filename)

    @app.get("/health")
    def health_check():
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "service": "backend",
                "apiPrefix": app.config["API_PREFIX"],
            },
        }

    return app
