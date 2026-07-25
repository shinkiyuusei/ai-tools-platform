"""
Run all pending SQL migration files against the configured MySQL database.
Usage: python run_migrations.py
"""

import os
import sys
import glob
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

import pymysql
from app.core.config import get_config

cfg = get_config()
mysql = cfg.MYSQL_CONFIG

MIGRATIONS_DIR = Path(__file__).resolve().parent / "database"


def get_applied():
    """Return set of already-applied migration filenames."""
    conn = pymysql.connect(**mysql)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM information_schema.tables "
                "WHERE table_schema = %s AND table_name = '_migrations'",
                (mysql["database"],),
            )
            if cur.fetchone()[0] == 0:
                cur.execute(
                    "CREATE TABLE _migrations (filename VARCHAR(255) PRIMARY KEY, applied_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
                conn.commit()
                return set()

            cur.execute("SELECT filename FROM _migrations")
            return {r[0] for r in cur.fetchall()}
    finally:
        conn.close()


def main():
    applied = get_applied()
    migrations = sorted(
        glob.glob(str(MIGRATIONS_DIR / "migration_*.sql"))
    )

    new_count = 0
    for path in migrations:
        filename = Path(path).name
        if filename in applied:
            continue

        print(f"[MIGRATE] {filename} ... ", end="", flush=True)
        sql = Path(path).read_text(encoding="utf-8").strip()
        if not sql:
            print("empty, skip")
            continue

        conn = pymysql.connect(**mysql)
        try:
            with conn.cursor() as cur:
                for stmt in sql.split(";"):
                    stmt = stmt.strip()
                    if not stmt:
                        continue
                    cur.execute(stmt)
                cur.execute("INSERT INTO _migrations (filename) VALUES (%s)", (filename,))
            conn.commit()
        except Exception as exc:
            print(f"FAILED: {exc}")
            conn.rollback()
            raise
        finally:
            conn.close()

        print("OK")
        new_count += 1

    if new_count == 0:
        print("All migrations already applied.")
    else:
        print(f"\n{new_count} migration(s) applied successfully.")


if __name__ == "__main__":
    main()
