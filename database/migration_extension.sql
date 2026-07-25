-- Migration: Client extension system
-- Stores installed extensions and per-user extension configurations.

CREATE TABLE IF NOT EXISTS t_extension (
  id VARCHAR(64) NOT NULL PRIMARY KEY COMMENT 'Extension ID from manifest',
  manifest JSON NOT NULL COMMENT 'Full manifest object as JSON',
  status VARCHAR(20) NOT NULL DEFAULT 'active' COMMENT 'active, inactive, pending_review',
  install_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS t_extension_config (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  extension_id VARCHAR(64) NOT NULL,
  user_id BIGINT NOT NULL,
  config JSON NOT NULL COMMENT 'User-specific extension settings',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_ext_user (extension_id, user_id),
  INDEX idx_extension (extension_id),
  INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
