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


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config())

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
