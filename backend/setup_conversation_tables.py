"""Create conversation and message tables if they don't exist."""
import pymysql
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

cfg = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_DB_PORT", "3306")),
    "user": os.getenv("MYSQL_DB_USER", "ai_user"),
    "password": os.getenv("MYSQL_DB_PASSWORD", "ai_pass_123"),
    "database": os.getenv("MYSQL_DB_NAME", "ai_tools_platform"),
    "charset": "utf8mb4",
    "autocommit": True,
}

sql = """
CREATE TABLE IF NOT EXISTS t_conversation (
  id BIGINT NOT NULL PRIMARY KEY,
  user_id BIGINT NOT NULL DEFAULT 0,
  work_id INT NOT NULL DEFAULT 0,
  title VARCHAR(100) NOT NULL DEFAULT '',
  message_count INT NOT NULL DEFAULT 0,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  INDEX idx_conv_user (user_id),
  INDEX idx_conv_work (work_id),
  INDEX idx_conv_user_work (user_id, work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS t_message (
  id BIGINT NOT NULL PRIMARY KEY,
  conversation_id BIGINT NOT NULL,
  role VARCHAR(10) NOT NULL,
  content TEXT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_msg_conv (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

if __name__ == "__main__":
    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            for stmt in sql.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
        print("Conversation tables created successfully.")
    finally:
        conn.close()
