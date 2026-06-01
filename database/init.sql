CREATE DATABASE IF NOT EXISTS ai_tools_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_tools_platform;

-- 标签定义表
CREATE TABLE IF NOT EXISTS t_tag (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户表
CREATE TABLE IF NOT EXISTS t_user (
  id BIGINT NOT NULL PRIMARY KEY,
  phone VARCHAR(20) NOT NULL DEFAULT '',
  email VARCHAR(50) NOT NULL DEFAULT '',
  password VARCHAR(100) NOT NULL,
  nickname VARCHAR(30) NOT NULL DEFAULT '',
  avatar VARCHAR(255) NOT NULL DEFAULT '',
  vip_level TINYINT NOT NULL DEFAULT 0,
  vip_expire_time DATETIME NULL,
  credits INT NOT NULL DEFAULT 500,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_phone (phone),
  INDEX idx_status (status),
  INDEX idx_vip_level (vip_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会员权益配置表
CREATE TABLE IF NOT EXISTS t_vip_rights (
  id INT AUTO_INCREMENT PRIMARY KEY,
  vip_level TINYINT NOT NULL,
  free_tool TINYINT NOT NULL DEFAULT 1,
  all_tool TINYINT NOT NULL DEFAULT 0,
  credits INT NOT NULL DEFAULT 500,
  concurrency_limit INT NOT NULL DEFAULT 1,
  ad_free TINYINT NOT NULL DEFAULT 0,
  priority_generate TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_vip_level (vip_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 审核记录表
CREATE TABLE IF NOT EXISTS t_audit_record (
  id BIGINT NOT NULL PRIMARY KEY,
  record_id VARCHAR(50) NOT NULL DEFAULT '',
  user_id BIGINT NOT NULL DEFAULT 0,
  content TEXT,
  audit_type TINYINT NOT NULL DEFAULT 1,
  audit_result TINYINT NOT NULL DEFAULT 0,
  audit_user BIGINT NOT NULL DEFAULT 0,
  audit_time DATETIME NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_record_id (record_id),
  INDEX idx_user_id (user_id),
  INDEX idx_audit_result (audit_result)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 角色卡表
CREATE TABLE IF NOT EXISTS t_character_card (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  name VARCHAR(100) NOT NULL DEFAULT '',
  `desc` VARCHAR(500) NOT NULL DEFAULT '',
  avatar VARCHAR(500) NOT NULL DEFAULT '',
  author VARCHAR(100) NOT NULL DEFAULT '',
  language VARCHAR(10) NOT NULL DEFAULT 'zh-Hans',
  category INT NOT NULL DEFAULT 0,
  tags JSON,
  persona_content TEXT NOT NULL,
  is_public TINYINT NOT NULL DEFAULT 1,
  like_count INT NOT NULL DEFAULT 0,
  view_count BIGINT NOT NULL DEFAULT 0,
  collect_count INT NOT NULL DEFAULT 0,
  use_count BIGINT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_like_count (like_count),
  INDEX idx_category (category),
  INDEX idx_create_time (create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 角色卡收藏表
CREATE TABLE IF NOT EXISTS t_character_collect (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  character_id INT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_character (user_id, character_id),
  INDEX idx_user_id (user_id),
  INDEX idx_character_id (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 角色卡点赞表
CREATE TABLE IF NOT EXISTS t_character_like (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  character_id INT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_character (user_id, character_id),
  INDEX idx_user_id (user_id),
  INDEX idx_character_id (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 作品卡表
CREATE TABLE IF NOT EXISTS t_work_card (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL DEFAULT 0,
  name VARCHAR(100) NOT NULL DEFAULT '',
  `desc` VARCHAR(500) NOT NULL DEFAULT '',
  cover VARCHAR(500) NOT NULL DEFAULT '',
  author VARCHAR(100) NOT NULL DEFAULT '',
  language VARCHAR(10) NOT NULL DEFAULT 'zh-Hans',
  category INT NOT NULL DEFAULT 0,
  summary TEXT,
  opening TEXT,
  openings JSON,
  tags JSON,
  role_config JSON NOT NULL,
  content JSON NOT NULL,
  use_count BIGINT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_status (status),
  INDEX idx_use_count (use_count),
  INDEX idx_category (category),
  INDEX idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 作品收藏表
CREATE TABLE IF NOT EXISTS t_work_collect (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  work_id BIGINT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_user_work (user_id, work_id),
  INDEX idx_work_id (work_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 每日对话统计表（用于日榜/周榜/月榜）
CREATE TABLE IF NOT EXISTS t_cards_daily_stat (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  card_type VARCHAR(16) NOT NULL DEFAULT 'work',
  card_id BIGINT NOT NULL,
  stat_date DATE NOT NULL,
  chat_count INT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_card_date (card_type, card_id, stat_date),
  INDEX idx_type_date_count (card_type, stat_date, chat_count DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 对话会话表
CREATE TABLE IF NOT EXISTS t_conversation (
  id BIGINT NOT NULL PRIMARY KEY,
  user_id BIGINT NOT NULL DEFAULT 0,
  entity_id BIGINT NOT NULL DEFAULT 0,
  entity_type VARCHAR(20) NOT NULL DEFAULT 'work',
  title VARCHAR(100) NOT NULL DEFAULT '',
  message_count INT NOT NULL DEFAULT 0,
  character_state JSON DEFAULT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  INDEX idx_conv_user (user_id),
  INDEX idx_conv_entity (entity_id),
  INDEX idx_conv_user_entity (user_id, entity_id, entity_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 对话消息表
CREATE TABLE IF NOT EXISTS t_message (
  id BIGINT NOT NULL PRIMARY KEY,
  conversation_id BIGINT NOT NULL,
  role VARCHAR(10) NOT NULL,
  content TEXT NOT NULL,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_msg_conv (conversation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
