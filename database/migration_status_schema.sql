ALTER TABLE t_character_card
  ADD COLUMN status_schema JSON DEFAULT NULL
  COMMENT 'Creator-defined status fields schema for immersive STATUS panel'
  AFTER persona_content;
