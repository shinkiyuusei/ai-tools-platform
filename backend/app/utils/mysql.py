import pymysql
from contextlib import contextmanager
from dbutils.pooled_db import PooledDB


_pool = None


def init_pool(mysql_config: dict):
    """Initialize the DBUtils connection pool. Called once at app startup."""
    global _pool
    cfg = {k: v for k, v in mysql_config.items() if k != "cursorclass"}
    cfg["cursorclass"] = pymysql.cursors.DictCursor
    _pool = PooledDB(
        creator=pymysql,
        maxconnections=20,
        mincached=2,
        maxcached=10,
        blocking=True,
        ping=1,
        **cfg,
    )


def _get_conn():
    return _pool.connection()


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
    """Get a raw MySQL connection from the pool.

    The caller is responsible for closing the connection (which returns it to the pool).
    """
    return _get_conn()
