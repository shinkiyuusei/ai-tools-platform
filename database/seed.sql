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

-- 分类种子数据
INSERT INTO t_tool_category (id, name, parent_id, icon, sort_order) VALUES
(1, '文本生成', 0, 'ri-file-text-line', 1),
(2, '图像生成', 0, 'ri-image-line', 2),
(3, '代码生成', 0, 'ri-code-line', 3),
(4, '文案营销', 0, 'ri-megaphone-line', 4),
(5, '办公效率', 0, 'ri-briefcase-line', 5),
(6, '创意设计', 0, 'ri-paint-brush-line', 6);

-- 二级分类
INSERT INTO t_tool_category (id, name, parent_id, icon, sort_order) VALUES
(11, 'AI文案', 1, 'ri-quill-pen-line', 1),
(12, '故事续写', 1, 'ri-book-open-line', 2),
(13, '翻译助手', 1, 'ri-translate-2', 3),
(21, '图片生成', 2, 'ri-image-edit-line', 1),
(22, '图片修复', 2, 'ri-tools-line', 2),
(31, '代码生成', 3, 'ri-code-box-line', 1),
(32, '代码解释', 3, 'ri-terminal-box-line', 2),
(41, '营销文案', 4, 'ri-advertisement-line', 1),
(42, '社媒内容', 4, 'ri-share-line', 2),
(51, '周报生成', 5, 'ri-file-list-line', 1),
(52, '会议纪要', 5, 'ri-chat-1-line', 2);

-- AI工具种子数据（已移除，旧数据编码损坏）
-- 如需恢复，请使用正确编码重新插入

-- 会员权益种子数据
INSERT INTO t_vip_rights (vip_level, free_tool, all_tool, free_count, concurrency_limit, ad_free, priority_generate) VALUES
(0, 1, 0, 10, 1, 0, 0),
(1, 1, 1, 0, 5, 1, 0),
(2, 1, 1, 0, 0, 1, 1);

-- 演示用户 (密码: Test123456)
-- bcrypt hash for "Test123456"
INSERT INTO t_user (id, phone, email, password, nickname, avatar, vip_level, vip_expire_time, free_count, status) VALUES
(1000000000000001, '13800000000', 'demo@example.com', '$2b$12$LJ3m4ys3Gy4e1Zq8wHkDZOxhBqEkqRQVF.r4YkCFkQI8PqMBYGgv6', '演示用户', '', 0, NULL, 10, 1);
