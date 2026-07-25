-- Password reset script (run once via --init-file, then removed)
FLUSH PRIVILEGES;
ALTER USER 'root'@'localhost' IDENTIFIED BY 'root123456';
ALTER USER 'root'@'%' IDENTIFIED BY 'root123456';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
ALTER USER 'ai_user'@'%' IDENTIFIED BY 'ai_pass_123';
GRANT ALL PRIVILEGES ON ai_tools_platform.* TO 'ai_user'@'%';
FLUSH PRIVILEGES;
