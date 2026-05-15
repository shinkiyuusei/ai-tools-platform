import pymysql
from contextlib import contextmanager

from flask import current_app


def _get_conn():
    cfg = dict(current_app.config["MYSQL_CONFIG"])
    cfg.pop("cursorclass", None)
    cfg["cursorclass"] = pymysql.cursors.DictCursor
    return pymysql.connect(**cfg)


@contextmanager
def get_db():
    conn = _get_conn()
    try:
        yield conn
    finally:
        conn.close()


def execute(sql: str, params: tuple = None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid


def query_one(sql: str, params: tuple = None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def query_all(sql: str, params: tuple = None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def get_mysql_connection():
    """Get a raw MySQL connection for use in services that need to manage their own lifecycle"""
    return _get_conn()
