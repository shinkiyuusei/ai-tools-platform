-- Migration: AI provider & model management tables
-- Lets super admins edit API keys / models from the web UI.
-- Mirrors the SillyTavern pattern: provider row -> GET {base_url}/models -> fill t_ai_model.
--
-- Seed (copying current env-var config into these rows) is done once at app
-- startup by backend/app/services/ai/bootstrap.py — env values never get
-- written into this SQL file.

CREATE TABLE IF NOT EXISTS t_ai_provider (
  id          BIGINT       PRIMARY KEY AUTO_INCREMENT,
  `key`       VARCHAR(50)  NOT NULL UNIQUE COMMENT '稳定标识，如 deepseek/openai/gemini/custom-1',
  name        VARCHAR(100) NOT NULL          COMMENT '展示名',
  adapter     VARCHAR(50)  NOT NULL DEFAULT 'openai' COMMENT '使用哪个 ChatAdapter 类',
  base_url    VARCHAR(500) NOT NULL          COMMENT 'OpenAI 兼容基础 URL',
  api_key     VARCHAR(500) NOT NULL DEFAULT '' COMMENT '明文存储，admin 写入；返回时掩码',
  is_active   TINYINT(1)   NOT NULL DEFAULT 1,
  sort_order  INT          NOT NULL DEFAULT 0,
  create_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_active_sort (is_active, sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 提供商配置（超管可编辑）';

CREATE TABLE IF NOT EXISTS t_ai_model (
  id           BIGINT       PRIMARY KEY AUTO_INCREMENT,
  provider_id  BIGINT       NOT NULL,
  model_id     VARCHAR(100) NOT NULL          COMMENT 'API 请求体里的 model 字段值',
  display_name VARCHAR(100) NOT NULL          COMMENT '下拉框展示名',
  is_active    TINYINT(1)   NOT NULL DEFAULT 1,
  is_default   TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '每个 provider 至多一个 default=1',
  sort_order   INT          NOT NULL DEFAULT 0,
  create_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  update_time  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_provider_model (provider_id, model_id),
  INDEX idx_provider_active (provider_id, is_active, sort_order),
  CONSTRAINT fk_ai_model_provider FOREIGN KEY (provider_id)
    REFERENCES t_ai_provider(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI 模型列表（可由 /models 拉取或手填）';
