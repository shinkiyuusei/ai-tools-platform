-- Supports both fresh databases and old databases that already gained this
-- column before migrations were tracked.  The migration runner executes each
-- statement on one connection, so prepared statements remain available.
SET @add_language_sql = (
  SELECT IF(COUNT(*) = 0,
    'ALTER TABLE t_user ADD COLUMN language VARCHAR(10) NOT NULL DEFAULT ''zh'' AFTER nickname',
    'SELECT 1')
  FROM information_schema.columns
  WHERE table_schema = DATABASE() AND table_name = 't_user' AND column_name = 'language'
);
PREPARE add_language_stmt FROM @add_language_sql;
EXECUTE add_language_stmt;
DEALLOCATE PREPARE add_language_stmt;
