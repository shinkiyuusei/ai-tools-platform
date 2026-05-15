import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[3] / ".env", override=True)


@dataclass
class BaseConfig:
    DEBUG: bool = os.getenv("FLASK_ENV", "development") == "development"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-secret")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES: int = 60 * 60 * 24
    API_PREFIX: str = os.getenv("API_PREFIX", "/api/v1")
    
    # i18n settings
    BABEL_DEFAULT_LOCALE: str = "zh"
    BABEL_TRANSLATION_DIRECTORIES: str = "translations"
    SUPPORTED_LANGUAGES: list = None

    MYSQL_CONFIG: dict = None
    MONGO_URI: str = ""
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
        mongo_user = os.getenv("MONGO_DB_USERNAME", "root")
        mongo_password = os.getenv("MONGO_DB_PASSWORD", "root123456")
        mongo_host = os.getenv("MONGO_HOST", "127.0.0.1")
        mongo_port = os.getenv("MONGO_DB_PORT", "27017")
        mongo_db = os.getenv("MONGO_DB_NAME", "ai_tools_platform")
        self.MONGO_URI = (
            f"mongodb://{mongo_user}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}"
            "?authSource=admin"
        )
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
