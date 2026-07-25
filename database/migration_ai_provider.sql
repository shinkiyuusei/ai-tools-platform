-- Migration: add AI provider support
-- Allows work cards and character cards to specify which AI backend to use.
-- Defaults to 'deepseek' for backward compatibility.

ALTER TABLE t_work_card ADD COLUMN ai_provider VARCHAR(50) NOT NULL DEFAULT 'deepseek' AFTER role_config;

ALTER TABLE t_character_card ADD COLUMN ai_provider VARCHAR(50) NOT NULL DEFAULT 'deepseek' AFTER persona_content;
