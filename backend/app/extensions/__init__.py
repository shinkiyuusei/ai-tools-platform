import redis
from flask import jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from ..utils.mysql import init_pool


jwt = JWTManager()
redis_client = None


def _jwt_error_response(message):
    return jsonify({"code": 20001, "message": message, "data": None}), 401


def register_jwt_callbacks():
    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_data):
        return _jwt_error_response("登录已过期，请重新登录")

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return _jwt_error_response(f"无效的登录凭证: {error}")

    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return _jwt_error_response(f"请先登录: {error}")

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_data):
        return _jwt_error_response("登录凭证已失效，请重新登录")


def init_extensions(app):
    global redis_client

    CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})
    jwt.init_app(app)
    register_jwt_callbacks()

    # JWT cookie configuration (use direct assignment — setdefault won't override flask-jwt defaults)
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_ACCESS_COOKIE_NAME"] = "access_token"
    app.config["JWT_REFRESH_COOKIE_NAME"] = "refresh_token"
    app.config["JWT_COOKIE_SECURE"] = not app.config.get("DEBUG", True)
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_CSRF_IN_COOKIES"] = True
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_CSRF_COOKIE_NAME"] = "csrf_access_token"
    app.config["JWT_REFRESH_CSRF_COOKIE_NAME"] = "csrf_refresh_token"

    mysql_config = dict(app.config["MYSQL_CONFIG"])
    init_pool(mysql_config)

    redis_client = redis.from_url(app.config["REDIS_URL"], decode_responses=True)


def get_redis_client():
    return redis_client
