-- Migration: World Info (世界设定书) system
-- Each entry is a trigger-keyword → lore-text pair attached to a work card
-- or character card.  The AI prompt builder injects active entries at runtime.

CREATE TABLE IF NOT EXISTS t_world_info_entry (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  entity_type VARCHAR(20) NOT NULL DEFAULT 'work' COMMENT 'work or character',
  entity_id BIGINT NOT NULL DEFAULT 0,
  `keys` JSON NOT NULL COMMENT 'JSON array of trigger keywords',
  content TEXT NOT NULL COMMENT 'Lore content injected into prompt',
  comment VARCHAR(200) NOT NULL DEFAULT '' COMMENT 'Short memo for editor (not injected)',
  selective TINYINT NOT NULL DEFAULT 0 COMMENT '1=AI judges relevance, 0=always inject on match',
  constant TINYINT NOT NULL DEFAULT 0 COMMENT '1=inject in every turn regardless of keywords',
  recursion TINYINT NOT NULL DEFAULT 0 COMMENT '1=recursive scanning after injection',
  position VARCHAR(20) NOT NULL DEFAULT 'before_char' COMMENT 'before_char or after_char',
  depth INT NOT NULL DEFAULT 1 COMMENT 'Injection depth / priority (lower = earlier)',
  `order` INT NOT NULL DEFAULT 0 COMMENT 'Sort order within same depth',
  probability INT NOT NULL DEFAULT 100 COMMENT '1-100, chance of injection on match',
  content_mode VARCHAR(10) DEFAULT NULL COMMENT 'null=both, nsfw, normal — which content mode this entry applies to',
  character_name VARCHAR(50) DEFAULT NULL COMMENT 'If set, only triggers when this character is present',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_entity (entity_type, entity_id),
  INDEX idx_depth (`depth`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
