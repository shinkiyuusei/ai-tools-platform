CREATE TABLE IF NOT EXISTS t_recommend_score (
  card_type VARCHAR(16) NOT NULL,
  card_id BIGINT NOT NULL,
  score DECIMAL(10,6) NOT NULL DEFAULT 0,
  dimensions JSON NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (card_type, card_id),
  INDEX idx_score (card_type, score DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS t_verification_code (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  account VARCHAR(100) NOT NULL,
  code VARCHAR(10) NOT NULL,
  ip_address VARCHAR(64) NOT NULL DEFAULT '',
  attempts INT NOT NULL DEFAULT 0,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_account (account, id),
  INDEX idx_ip_created (ip_address, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS t_analytics_event (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  event_type VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL DEFAULT 0,
  event_data JSON NULL,
  ip_address VARCHAR(64) NOT NULL DEFAULT '',
  user_agent VARCHAR(512) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_type_created (event_type, created_at),
  INDEX idx_user_created (user_id, created_at),
  INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE t_user ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT 'zh' AFTER avatar;
