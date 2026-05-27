from http import HTTPStatus

from flask import jsonify
from flask_jwt_extended.exceptions import JWTExtendedException


class AppError(Exception):
    def __init__(self, code: int, message: str, http_status: int = HTTPStatus.BAD_REQUEST):
        self.code = code
        self.message = message
        self.http_status = http_status
        super().__init__(message)


class ErrorCode:
    SYSTEM_ERROR = 10000
    PARAM_INVALID = 10001
    RESOURCE_NOT_FOUND = 10002
    UNAUTHORIZED = 20001
    FORBIDDEN = 20003
    USER_NOT_FOUND = 20004
    GENERATE_FAILED = 30001
    VIP_REQUIRED = 40001


def error_response(code: int, message: str, http_status: int):
    return jsonify({"code": code, "message": message, "data": None}), http_status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err: AppError):
        return error_response(err.code, err.message, err.http_status)

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_error(err: JWTExtendedException):
        return error_response(ErrorCode.UNAUTHORIZED, str(err), HTTPStatus.UNAUTHORIZED)

    @app.errorhandler(404)
    def handle_404(_):
        return error_response(ErrorCode.SYSTEM_ERROR, "请求资源不存在", HTTPStatus.NOT_FOUND)

    @app.errorhandler(Exception)
    def handle_unknown_error(err: Exception):
        app.logger.exception(err)
        return error_response(ErrorCode.SYSTEM_ERROR, "系统异常，请稍后重试", HTTPStatus.INTERNAL_SERVER_ERROR)
