USE ai_tools_platform;

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

-- AI工具种子数据（已移除，旧数据编码损坏）
-- 如需恢复，请使用正确编码重新插入

-- 会员权益种子数据
INSERT INTO t_vip_rights (vip_level, free_tool, all_tool, credits, concurrency_limit, ad_free, priority_generate) VALUES
(0, 1, 0, 10, 1, 0, 0),
(1, 1, 1, 0, 5, 1, 0),
(2, 1, 1, 0, 0, 1, 1);

-- 演示用户 (密码: Test123456)
-- bcrypt hash for "Test123456"
INSERT INTO t_user (id, phone, email, password, nickname, avatar, vip_level, vip_expire_time, credits, status) VALUES
(1000000000000001, '13800000000', 'demo@example.com', '$2b$12$LJ3m4ys3Gy4e1Zq8wHkDZOxhBqEkqRQVF.r4YkCFkQI8PqMBYGgv6', '演示用户', '', 0, NULL, 10, 1);
