USE ai_tools_platform;

-- 标签定义表
CREATE TABLE IF NOT EXISTS t_tag (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(20) NOT NULL,
  sort_order INT NOT NULL DEFAULT 0,
  create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 标签种子数据
INSERT IGNORE INTO t_tag (id, name, sort_order) VALUES
(1, '文案', 1),
(2, '图像', 2),
(3, '营销', 3),
(4, '电商', 4),
(5, '编程', 5),
(6, '翻译', 6),
(7, '写作', 7),
(8, '设计', 8),
(9, '聊天', 9),
(10, '数据分析', 10),
(11, '办公', 11),
(12, '创意', 12),
(13, '故事', 13),
(14, '教育', 14),
(15, '社交媒体', 15);
