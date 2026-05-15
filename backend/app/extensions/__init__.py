import pymysql
import redis
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from pymongo import MongoClient


jwt = JWTManager()
mongo_client = None
mongo_db = None
redis_client = None
mysql_pool = None


def init_extensions(app):
    global mongo_client, mongo_db, redis_client, mysql_pool

    CORS(app, resources={r"/api/*": {"origins": "*"}})
    jwt.init_app(app)

    mysql_config = dict(app.config["MYSQL_CONFIG"])
    mysql_config["cursorclass"] = pymysql.cursors.DictCursor
    mysql_pool = mysql_config

    mongo_client = MongoClient(app.config["MONGO_URI"])
    mongo_db = mongo_client.get_default_database()
    redis_client = redis.from_url(app.config["REDIS_URL"], decode_responses=True)


def get_mysql_connection():
    return pymysql.connect(**mysql_pool)


def get_mongo_db():
    return mongo_db


def get_redis_client():
    return redis_client
