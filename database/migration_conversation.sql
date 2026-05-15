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
