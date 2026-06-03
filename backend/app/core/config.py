import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)


@dataclass
class BaseConfig:
    DEBUG: bool = os.getenv("FLASK_ENV", "development") == "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 60 * 24
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # i18n settings
    BABEL_DEFAULT_LOCALE: str = "zh"
    BABEL_TRANSLATION_DIRECTORIES: str = "translations"
    SUPPORTED_LANGUAGES: list = None

    MYSQL_CONFIG: dict = None
    REDIS_URL: str = ""
    DEEPSEEK_CONFIG: dict = None

    def __post_init__(self):
        self.MYSQL_CONFIG = {
            "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
            "port": int(os.getenv("MYSQL_DB_PORT", "3306")),
            "user": os.getenv("MYSQL_DB_USER", "ai_user"),
            "password": os.getenv("MYSQL_DB_PASSWORD", "ai_pass_123"),
            "database": os.getenv("MYSQL_DB_NAME", "ai_tools_platform"),
            "charset": "utf8mb4",
            "cursorclass": None,
            "autocommit": True,
        }
        redis_password = os.getenv("REDIS_PASSWORD", "redis123456")
        redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
        redis_port = os.getenv("REDIS_DB_PORT", "6379")
        self.REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
        self.DEEPSEEK_CONFIG = {
            "base_url": os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "chat_model": os.getenv("DEEPSEEK_CHAT_MODEL", "deepseek-v4-flash"),
            "reasoner_model": os.getenv("DEEPSEEK_REASONER_MODEL", "deepseek-v4-pro"),
        }
        self.ALIPAY_CONFIG = {
            "app_id": os.getenv("ALIPAY_APP_ID", ""),
            "app_private_key": os.getenv("ALIPAY_APP_PRIVATE_KEY", "").replace("\\n", "\n"),
            "alipay_public_key": os.getenv("ALIPAY_PUBLIC_KEY", "").replace("\\n", "\n"),
            "gateway": os.getenv(
                "ALIPAY_GATEWAY",
                "https://openapi-sandbox.dl.alipaydev.com/gateway.do",
            ),
            "notify_url": os.getenv("ALIPAY_NOTIFY_URL", ""),
            "return_url": os.getenv("ALIPAY_RETURN_URL", ""),
            "sign_type": "RSA2",
        }
        self.SUPPORTED_LANGUAGES = ['zh', 'en', 'ja', 'ko']


class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    DEBUG = False


def get_config():
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
