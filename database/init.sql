CREATE DATABASE IF NOT EXISTS ai_tools_platform
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE ai_tools_platform;

-- 工具分类表
CREATE TABLE IF NOT EXISTS t_tool_category (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  parent_id INT NOT NULL DEFAULT 0,
  icon VARCHAR(255) NOT NULL DEFAULT '',
  sort_order INT NOT NULL DEFAULT 0,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
  free_count INT NOT NULL DEFAULT 10,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_delete TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_phone (phone),
  UNIQUE KEY uk_email (email),
  INDEX idx_status (status),
  INDEX idx_vip_level (vip_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 会员权益配置表
CREATE TABLE IF NOT EXISTS t_vip_rights (
  id INT AUTO_INCREMENT PRIMARY KEY,
  vip_level TINYINT NOT NULL,
  free_tool TINYINT NOT NULL DEFAULT 1,
  all_tool TINYINT NOT NULL DEFAULT 0,
  free_count INT NOT NULL DEFAULT 10,
  concurrency_limit INT NOT NULL DEFAULT 1,
  ad_free TINYINT NOT NULL DEFAULT 0,
  priority_generate TINYINT NOT NULL DEFAULT 0,
  UNIQUE KEY uk_vip_level (vip_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- AI工具表
CREATE TABLE IF NOT EXISTS t_ai_tool (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  icon VARCHAR(255) NOT NULL DEFAULT '',
  `desc` VARCHAR(200) NOT NULL DEFAULT '',
  use_desc TEXT,
  category_id INT NOT NULL DEFAULT 0,
  tag_ids VARCHAR(100) NOT NULL DEFAULT '',
  form_config TEXT,
  ai_api VARCHAR(255) NOT NULL DEFAULT '',
  is_free TINYINT NOT NULL DEFAULT 1,
  is_vip TINYINT NOT NULL DEFAULT 0,
  use_count BIGINT NOT NULL DEFAULT 0,
  sort_order INT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_category (category_id),
  INDEX idx_status (status),
  INDEX idx_use_count (use_count)
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
  name VARCHAR(100) NOT NULL,
  avatar VARCHAR(500) NOT NULL DEFAULT '',
  description TEXT NOT NULL,
  personality TEXT NOT NULL,
  background TEXT NOT NULL,
  tags VARCHAR(500) NOT NULL DEFAULT '',
  category_id INT NOT NULL DEFAULT 0,
  is_public TINYINT NOT NULL DEFAULT 1,
  is_vip TINYINT NOT NULL DEFAULT 0,
  like_count INT NOT NULL DEFAULT 0,
  view_count BIGINT NOT NULL DEFAULT 0,
  collect_count INT NOT NULL DEFAULT 0,
  status TINYINT NOT NULL DEFAULT 1,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_category (category_id),
  INDEX idx_status (status),
  INDEX idx_like_count (like_count),
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
