ALTER TABLE t_conversation
  ADD COLUMN character_state JSON DEFAULT NULL AFTER message_count;
