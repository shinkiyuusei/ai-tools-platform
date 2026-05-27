USE ai_tools_platform;

-- 1. Rename free_count to credits in t_user
ALTER TABLE t_user CHANGE COLUMN free_count credits INT NOT NULL DEFAULT 500;

-- 2. Rename free_count to credits in t_vip_rights
ALTER TABLE t_vip_rights CHANGE COLUMN free_count credits INT NOT NULL DEFAULT 500;

-- 3. Add credit transaction log table
CREATE TABLE IF NOT EXISTS t_credit_log (
  id BIGINT NOT NULL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  amount INT NOT NULL COMMENT '正数为充值，负数为消费',
  balance_after INT NOT NULL COMMENT '变动后余额',
  source_type VARCHAR(20) NOT NULL DEFAULT 'chat' COMMENT 'chat/daily_login/admin_grant/register',
  conversation_id BIGINT NOT NULL DEFAULT 0,
  message_id BIGINT NOT NULL DEFAULT 0,
  tokens_used INT NOT NULL DEFAULT 0 COMMENT '本次消耗的 token 数',
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_user_id (user_id),
  INDEX idx_create_time (create_time),
  INDEX idx_source_type (source_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
