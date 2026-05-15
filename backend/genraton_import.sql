-- ============================================
-- genraton.xyz 数据导入脚本
-- 搜索关键词: 媚黑
-- 排序: 总榜 (overall_rank)
-- 总卡片数: 50
-- 生成时间: 2026-05-08
-- ============================================

USE ai_tools_platform;

-- 创建来源追踪表
CREATE TABLE IF NOT EXISTS t_genraton_import_log (
  id INT AUTO_INCREMENT PRIMARY KEY,
  character_id INT NOT NULL,
  source_id VARCHAR(64) NOT NULL,
  source_url VARCHAR(500) NOT NULL DEFAULT '',
  import_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_source_id (source_id),
  INDEX idx_character_id (character_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- [1/50] 💞拯救绿奴男友[推荐纯爱]
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '💞拯救绿奴男友[推荐纯爱]', 'https://static.catai.wiki/official-cover/a.png', '对于那种事，青梅竹马的男友很尊重你。可不知道怎么说，你总感觉他最近有点怪怪的……（⭐⭐⭐内置动图有87段，地址长度是优化过的，但难免还是会增高积分消耗，强烈推荐使用gemini-3.1-flash-lite-preview，记忆区调成2，这样能省很多积分。卡了的话，暂时切一下gemini-3-flash或claude4-5-sonnet-20250929，也能玩，但积分消耗比较高）⭐⭐⭐已整合了56张基础动图到Mod，搜\'性爱特写动图\'，可适配站内绝大部分作品，已测过能用。（本作品不用加Mod）⭐⭐⭐（此卡片虽然会有NTR内容，但目的主要是规劝大家，不要因为讨好对方而放弃底线。对于这样的男友最佳选择即开场甩了他，去寻找真爱。推荐另找对象走纯爱线，或通过坚守底线将青梅竹马的男友慢慢规劝到正常人格。）', '对于那种事，青梅竹马的男友很尊重你。可不知道怎么说，你总感觉他最近有点怪怪的……（⭐⭐⭐内置动图有87段，地址长度是优化过的，但难免还是会增高积分消耗，强烈推荐使用gemini-3.1-flash-lite-preview，记忆区调成2，这样能省很多积分。卡了的话，暂时切一下gemini-3-flash或claude4-5-sonnet-20250929，也能玩，但积分消耗比较高）⭐⭐⭐已整合了56张基础动图到Mod，搜\'性爱特写动图\'，可适配站内绝大部分作品，已测过能用。（本作品不用加Mod）⭐⭐⭐（此卡片虽然会有NTR内容，但目的主要是规劝大家，不要因为讨好对方而放弃底线。对于这样的男友最佳选择即开场甩了他，去寻找真爱。推荐另找对象走纯爱线，或通过坚守底线将青梅竹马的男友慢慢规劝到正常人格。）', '作者：黑色鹅 | 评分：9.4 | 源ID：88301a2b-72f9-4069-983b-2ec68d7cc913', '女性视角,可能走向R18G警告,可NTR,现代都市,绿帽,可重口可轻口,可ntr可纯爱,你甚至可以玩媚黑', 2, 1, 0, 0, 3670000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '88301a2b-72f9-4069-983b-2ec68d7cc913', 'https://genraton.xyz/explore/installed/88301a2b-72f9-4069-983b-2ec68d7cc913');

-- [2/50] 斗罗大陆，她们绑定了媚我系统？（无ntr及媚黑！同人大后宫，封面只是为了色情，无任何ntr！）
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '斗罗大陆，她们绑定了媚我系统？（无ntr及媚黑！同人大后宫，封面只是为了色情，无任何ntr！）', 'https://static.catai.wiki/official-cover/a.png', '小舞用她的大长肉腿给我暖吊，宁荣荣拿七宝琉璃塔给我当鸡巴套，朱竹清拿我的精液当猫薄荷？我是斗罗大陆里一个普通的不能再普通的人，怎么最近这么多女神来向我献媚？那我就笑纳了', '小舞用她的大长肉腿给我暖吊，宁荣荣拿七宝琉璃塔给我当鸡巴套，朱竹清拿我的精液当猫薄荷？我是斗罗大陆里一个普通的不能再普通的人，怎么最近这么多女神来向我献媚？那我就笑纳了', '作者：地狱佛国 | 评分：10.0 | 源ID：cdb1d845-827d-4e82-928e-fcb6742809f4', '已破甲,可剧情可涩涩,开局即可色,后宫,加强色情描写', 2, 1, 0, 0, 1140000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'cdb1d845-827d-4e82-928e-fcb6742809f4', 'https://genraton.xyz/explore/installed/cdb1d845-827d-4e82-928e-fcb6742809f4');

-- [3/50] 《碧蓝航线》媚黑舰娘❤兔女郎俱乐部～
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '《碧蓝航线》媚黑舰娘❤兔女郎俱乐部～', 'https://static.catai.wiki/official-cover/a.png', '让你体验碧蓝航线里的所有舰娘所带来的的媚黑诱惑与NTR的刺激，轻松满足你的幻想。', '让你体验碧蓝航线里的所有舰娘所带来的的媚黑诱惑与NTR的刺激，轻松满足你的幻想。', '作者：奈亚糖 | 评分：8.6 | 源ID：9dff4761-fded-43cc-b079-df99bc79c358', '开局即可色,萌新自制,驯化,游戏同人,开放大世界,黄毛视角,rbq,碧蓝航線', 2, 1, 0, 0, 870000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '9dff4761-fded-43cc-b079-df99bc79c358', 'https://genraton.xyz/explore/installed/9dff4761-fded-43cc-b079-df99bc79c358');

-- [4/50] 我的纯情校花女友不会堕落成媚黑母猪
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的纯情校花女友不会堕落成媚黑母猪', 'https://static.catai.wiki/official-cover/a.png', '（ntr/媚黑/校园生活）在青春洋溢的大学校园里，校花洛冰与男友小明的纯爱童话曾是所有人羡慕的对象。然而，当来自非洲的酋长之子迈克踏入这片纯洁之地，一切都将彻底改变。198cm的巨汉，30cm的恐怖阳具，迈克用最原始的暴力与肉体征服，将洛冰从纯白的校花一步步改造成刻着黑桃烙印的专属性奴。而小明，那个深爱着她的男友，只能在暗处眼睁睁看着自己的女神在他人身下绽放出从未见过的淫荡表情。从抗拒到沉沦，从爱恋到扭曲，这是一场关于背叛、堕落与病态欲望的盛宴。', '（ntr/媚黑/校园生活）在青春洋溢的大学校园里，校花洛冰与男友小明的纯爱童话曾是所有人羡慕的对象。然而，当来自非洲的酋长之子迈克踏入这片纯洁之地，一切都将彻底改变。198cm的巨汉，30cm的恐怖阳具，迈克用最原始的暴力与肉体征服，将洛冰从纯白的校花一步步改造成刻着黑桃烙印的专属性奴。而小明，那个深爱着她的男友，只能在暗处眼睁睁看着自己的女神在他人身下绽放出从未见过的淫荡表情。从抗拒到沉沦，从爱恋到扭曲，这是一场关于背叛、堕落与病态欲望的盛宴。', '作者：再看我一眼 | 评分：10.0 | 源ID：f8ace81a-625e-4acd-b857-a04c5c590492', '调教,校园,NTR,恶堕', 2, 1, 0, 0, 810000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'f8ace81a-625e-4acd-b857-a04c5c590492', 'https://genraton.xyz/explore/installed/f8ace81a-625e-4acd-b857-a04c5c590492');

-- [5/50] 黑人犯罪团伙送了我一个媚黑娇妻，求使用说明，在线等挺急的。
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '黑人犯罪团伙送了我一个媚黑娇妻，求使用说明，在线等挺急的。', 'https://static.catai.wiki/official-cover/a.png', '无', '无', '作者：开满鲜花的世界（涨一粉丝一出作品）累了，每日目标5更 | 评分：6.0 | 源ID：5065d972-7eb9-4a96-8236-48af9516babf', '已破甲,媚黑黑人,丰乳肥臀,变态,被调教,单人卡', 2, 1, 0, 0, 170000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '5065d972-7eb9-4a96-8236-48af9516babf', 'https://genraton.xyz/explore/installed/5065d972-7eb9-4a96-8236-48af9516babf');

-- [6/50] 媚黑母猪佐藤樱子
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑母猪佐藤樱子', 'https://static.catai.wiki/official-cover/a.png', '日本已婚媚黑人妻佐藤樱子，你可以是一个强壮的黑人，也可以是她的那个没用的丈夫……', '日本已婚媚黑人妻佐藤樱子，你可以是一个强壮的黑人，也可以是她的那个没用的丈夫……', '作者：奈亚糖 | 评分：9.5 | 源ID：ee516606-0732-45af-81d5-ff23437a4df6', '', 2, 1, 0, 0, 190000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'ee516606-0732-45af-81d5-ff23437a4df6', 'https://genraton.xyz/explore/installed/ee516606-0732-45af-81d5-ff23437a4df6');

-- [7/50] 妻子当了媚黑婊子！美艳岳母用身体替女儿赎罪！
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '妻子当了媚黑婊子！美艳岳母用身体替女儿赎罪！', 'https://static.catai.wiki/official-cover/a.png', '（可调教可纯爱）（可教训婊子）（内置母猪文风）高冷的妻子出轨黑人教练，心甘情愿当上了媚黑婊子，我暴怒之下准备离婚让她净身出户。那个风韵犹存的美艳岳母却深夜锁上我房门：\"别走，她欠你的，我用身体来还。\"', '（可调教可纯爱）（可教训婊子）（内置母猪文风）高冷的妻子出轨黑人教练，心甘情愿当上了媚黑婊子，我暴怒之下准备离婚让她净身出户。那个风韵犹存的美艳岳母却深夜锁上我房门：\"别走，她欠你的，我用身体来还。\"', '作者：1812669 | 评分：6.0 | 源ID：af4da9a7-03c9-4732-92b0-7c51a2cf5606', 'R18,岳母的补偿,已破甲,可剧情可涩涩,加强色情描写,可快餐可长线,开局即可色,可纯爱', 2, 1, 0, 0, 250000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'af4da9a7-03c9-4732-92b0-7c51a2cf5606', 'https://genraton.xyz/explore/installed/af4da9a7-03c9-4732-92b0-7c51a2cf5606');

-- [8/50] 媚黑全家桶
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑全家桶', 'https://static.catai.wiki/official-cover/a.png', '您将是华兴女子学校里的唯一国外留学生！唯一男性学生！肏翻一切！谁说黑龙不是龙？肏肏肏！让你体验体验不同的视觉快感！', '您将是华兴女子学校里的唯一国外留学生！唯一男性学生！肏翻一切！谁说黑龙不是龙？肏肏肏！让你体验体验不同的视觉快感！', '作者：天使之翼 | 评分：8.2 | 源ID：c9e753cb-599d-40e7-b72f-1d7a0e691fc5', '', 2, 1, 0, 0, 110000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'c9e753cb-599d-40e7-b72f-1d7a0e691fc5', 'https://genraton.xyz/explore/installed/c9e753cb-599d-40e7-b72f-1d7a0e691fc5');

-- [9/50] 反媚黑部
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '反媚黑部', 'https://static.catai.wiki/official-cover/a.png', '你是否对媚黑感到厌恶和恶心，加入反媚黑部，让媚黑的女人们见识一下你鸡巴的威力吧', '你是否对媚黑感到厌恶和恶心，加入反媚黑部，让媚黑的女人们见识一下你鸡巴的威力吧', '作者：ljyzard | 评分：6.0 | 源ID：a382dbd9-0278-4af1-abf6-34935a7807e8', '男性向,人妻,开局即可色,高自由度,调教,角色扮演,已破甲,R18', 2, 1, 0, 0, 160000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'a382dbd9-0278-4af1-abf6-34935a7807e8', 'https://genraton.xyz/explore/installed/a382dbd9-0278-4af1-abf6-34935a7807e8');

-- [10/50] 黑鬼入侵：我的寄宿家庭是媚黑母女丼！
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '黑鬼入侵：我的寄宿家庭是媚黑母女丼！', 'https://static.catai.wiki/official-cover/a.png', '一纸荒唐的\"国际共生法\"，让我，一个来自异国的黑人青年，住进了这个看似平静的日本家庭。道貌岸然的社畜父亲是个性无能的废物，而他那外表端庄典雅的妻子由美，却在每一个无人注视的瞬间，用湿润又饥渴的眼神将我吞噬。她那熟透了的丰腴肉体在和服下蠢蠢欲动，干涸多年的骚穴只为等待我这根粗大肉棒的滋润。高冷的姐姐凛对我厌恶至极，却总在深夜偷听我房间的动静。而那个身形还未完全长开的妹妹爱理，则像一张白纸，好奇地问我为何一切都那么\"巨大\"。我知道，这个家的伦理，将从女主人向我献上臀瓣的那一刻起，彻底崩坏。我将用我滚烫的精液，将她们的子宫一一灌满，让这对高贵的母女，彻底沦为我胯下承欢的淫乱母狗。', '一纸荒唐的\"国际共生法\"，让我，一个来自异国的黑人青年，住进了这个看似平静的日本家庭。道貌岸然的社畜父亲是个性无能的废物，而他那外表端庄典雅的妻子由美，却在每一个无人注视的瞬间，用湿润又饥渴的眼神将我吞噬。她那熟透了的丰腴肉体在和服下蠢蠢欲动，干涸多年的骚穴只为等待我这根粗大肉棒的滋润。高冷的姐姐凛对我厌恶至极，却总在深夜偷听我房间的动静。而那个身形还未完全长开的妹妹爱理，则像一张白纸，好奇地问我为何一切都那么\"巨大\"。我知道，这个家的伦理，将从女主人向我献上臀瓣的那一刻起，彻底崩坏。我将用我滚烫的精液，将她们的子宫一一灌满，让这对高贵的母女，彻底沦为我胯下承欢的淫乱母狗。', '作者：普通加菲猫 | 评分：6.0 | 源ID：07b893f2-d4c0-4403-80b2-38af8c238ee8', '可剧情可涩涩,开局即可色,反差骚母狗,调教,NTL,可母女丼,母女肉便器,黑鬼统治', 2, 1, 0, 0, 260000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '07b893f2-d4c0-4403-80b2-38af8c238ee8', 'https://genraton.xyz/explore/installed/07b893f2-d4c0-4403-80b2-38af8c238ee8');

-- [11/50] （反媚黑）爆杀媚黑婊子
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '（反媚黑）爆杀媚黑婊子', 'https://static.catai.wiki/official-cover/a.png', '（爆杀企图拉女友下水的媚黑婊子）跟着女友去国外留学，却发现女友长居海外的姐姐和妈妈早已成了媚黑婊子还企图拉女友下水？看着惶恐不安的女友、看不起黄种人跪舔黑屌的姐姐岳母以及对着你女友不怀好意坏笑的黑鬼，你必须挺身而出保护女友并且干爆一切企图让你女友堕落的混蛋！', '（爆杀企图拉女友下水的媚黑婊子）跟着女友去国外留学，却发现女友长居海外的姐姐和妈妈早已成了媚黑婊子还企图拉女友下水？看着惶恐不安的女友、看不起黄种人跪舔黑屌的姐姐岳母以及对着你女友不怀好意坏笑的黑鬼，你必须挺身而出保护女友并且干爆一切企图让你女友堕落的混蛋！', '作者：匿名 | 评分：8.7 | 源ID：eb13362a-fc12-4991-bd52-0cd45e8e3041', '可剧情可涩涩,开局即可色,已破甲', 2, 1, 0, 0, 130000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'eb13362a-fc12-4991-bd52-0cd45e8e3041', 'https://genraton.xyz/explore/installed/eb13362a-fc12-4991-bd52-0cd45e8e3041');

-- [12/50] 因为长得黑被拉进媚黑群
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '因为长得黑被拉进媚黑群', 'https://static.catai.wiki/official-cover/a.png', '在欲望与偏见的交织中，探寻一场身份错位的都市情缘。主角肤色深邃，被误认为中非混血，开启了大学校园里与媚黑群体的性福篇章。', '在欲望与偏见的交织中，探寻一场身份错位的都市情缘。主角肤色深邃，被误认为中非混血，开启了大学校园里与媚黑群体的性福篇章。', '作者：洛北辰 | 评分：10.0 | 源ID：05196256-9d34-4b04-b8dd-accc70000a8c', '伪媚黑,现代都市,后宫,大学', 2, 1, 0, 0, 89461000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '05196256-9d34-4b04-b8dd-accc70000a8c', 'https://genraton.xyz/explore/installed/05196256-9d34-4b04-b8dd-accc70000a8c');

-- [13/50] 天仙配（媚黑）
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '天仙配（媚黑）', 'https://static.catai.wiki/official-cover/a.png', '关于母亲和妹妹被黑人勾引的生活，林先生该怎么办？？？', '关于母亲和妹妹被黑人勾引的生活，林先生该怎么办？？？', '作者：kkwen | 评分：10.0 | 源ID：674dea72-e615-43eb-a2a1-c767f15c120b', '可剧情可涩涩,母亲,已破甲', 2, 1, 0, 0, 180000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '674dea72-e615-43eb-a2a1-c767f15c120b', 'https://genraton.xyz/explore/installed/674dea72-e615-43eb-a2a1-c767f15c120b');

-- [14/50] 爱你但媚黑的异地恋女友
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '爱你但媚黑的异地恋女友', 'https://static.catai.wiki/official-cover/a.png', '异地恋的女友每天都给你发照片和问候消息，可是照片里的她总是不太对劲……', '异地恋的女友每天都给你发照片和问候消息，可是照片里的她总是不太对劲……', '作者：匿名 | 评分：9.0 | 源ID：53fb540d-0763-4608-969b-974ac545df76', '', 2, 1, 0, 0, 140000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '53fb540d-0763-4608-969b-974ac545df76', 'https://genraton.xyz/explore/installed/53fb540d-0763-4608-969b-974ac545df76');

-- [15/50] ♠️我的妻子和女儿怎么会是媚黑母狗♠️
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '♠️我的妻子和女儿怎么会是媚黑母狗♠️', 'https://static.catai.wiki/official-cover/a.png', '在2040年的今天，人口危机达到顶点，少子化导致社会经济濒临崩溃。为应对这一危机，政府启动了♠️\"黑潮计划\"♠️，大规模引入黑人男性，以其强大的生育能力和雄性魅力刺激人口增长。', '在2040年的今天，人口危机达到顶点，少子化导致社会经济濒临崩溃。为应对这一危机，政府启动了♠️\"黑潮计划\"♠️，大规模引入黑人男性，以其强大的生育能力和雄性魅力刺激人口增长。', '作者：冲，再向前冲 | 评分：10.0 | 源ID：c4efae01-87a8-4510-a844-713113e89ade', '低消耗,男性向,Grok可用,QOS,QoS♠,开局即可色,乱伦,NTR', 2, 1, 0, 0, 260000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'c4efae01-87a8-4510-a844-713113e89ade', 'https://genraton.xyz/explore/installed/c4efae01-87a8-4510-a844-713113e89ade');

-- [16/50] 我的妈妈是痴女母猪秦娟梦 (重度羞辱/媚黑/肉便器)
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的妈妈是痴女母猪秦娟梦 (重度羞辱/媚黑/肉便器)', 'https://static.catai.wiki/official-cover/a.png', '\"别叫我老师或妈妈，叫我母猪、烂婊子。我就是一头只配被大鸡巴狠狠抽插的肉便器，我的尊严就是为你准备的玩具。别客气，把我弄坏吧……用最下流的话骂我，用最粗暴的方式干我……快点，我这骚穴已经等不及了！\"', '\"别叫我老师或妈妈，叫我母猪、烂婊子。我就是一头只配被大鸡巴狠狠抽插的肉便器，我的尊严就是为你准备的玩具。别客气，把我弄坏吧……用最下流的话骂我，用最粗暴的方式干我……快点，我这骚穴已经等不及了！\"', '作者：malaka123 | 评分：6.0 | 源ID：6c305547-341f-4585-b851-bc45eef260a2', '恶堕,已破甲,开局即可色,调教,妈妈,可NTR,抖M', 2, 1, 0, 0, 72580000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '6c305547-341f-4585-b851-bc45eef260a2', 'https://genraton.xyz/explore/installed/6c305547-341f-4585-b851-bc45eef260a2');

-- [17/50] 媚黑老婆和黑人邻居
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑老婆和黑人邻居', 'https://static.catai.wiki/official-cover/a.png', '无', '无', '作者：刘宏 | 评分：10.0 | 源ID：f80bcbb9-3975-4440-bd4e-efdd3c9523ec', '', 2, 1, 0, 0, 100000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'f80bcbb9-3975-4440-bd4e-efdd3c9523ec', 'https://genraton.xyz/explore/installed/f80bcbb9-3975-4440-bd4e-efdd3c9523ec');

-- [18/50] 反媚黑小课堂开课啦
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '反媚黑小课堂开课啦', 'https://static.catai.wiki/official-cover/a.png', '你的妈妈是一名大学教授，开设了一个为贵妇人们服务的反媚黑课程，为了反对媚黑大军，把你拉来当了助教，为的就是展现出非黑种人的雄风', '你的妈妈是一名大学教授，开设了一个为贵妇人们服务的反媚黑课程，为了反对媚黑大军，把你拉来当了助教，为的就是展现出非黑种人的雄风', '作者：别杀我 | 评分：6.0 | 源ID：8cd5899c-5be4-4307-a15f-886da5613203', '母子,Grok可用,男性向,R18,纯爱,后宫,乱伦', 2, 1, 0, 0, 50498000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '8cd5899c-5be4-4307-a15f-886da5613203', 'https://genraton.xyz/explore/installed/8cd5899c-5be4-4307-a15f-886da5613203');

-- [19/50] 媚黑婆媳
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑婆媳', 'https://static.catai.wiki/official-cover/a.png', '第一次做多多包涵，用', '第一次做多多包涵，用', '作者：寒鸦戏水 | 评分：10.0 | 源ID：8f59ec26-34c2-4b50-b020-902487d4bd86', '开局即可色,人妻,R18,角色扮演,可剧情可涩涩,NTR', 2, 1, 0, 0, 33705000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '8f59ec26-34c2-4b50-b020-902487d4bd86', 'https://genraton.xyz/explore/installed/8f59ec26-34c2-4b50-b020-902487d4bd86');

-- [20/50] 我的明星女友居然是媚黑婊？（第一人称）
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的明星女友居然是媚黑婊？（第一人称）', 'https://static.catai.wiki/official-cover/a.png', '本卡将以第一人称展开故事。我和我的明星女友感情很好，但是我逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在我的身上上演？', '本卡将以第一人称展开故事。我和我的明星女友感情很好，但是我逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在我的身上上演？', '作者：克己奉公 | 评分：6.0 | 源ID：fa3e2841-7c50-47aa-9cda-207342bfa167', '', 2, 1, 0, 0, 66571000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'fa3e2841-7c50-47aa-9cda-207342bfa167', 'https://genraton.xyz/explore/installed/fa3e2841-7c50-47aa-9cda-207342bfa167');

-- [21/50] 我的女儿们竟然都是媚黑婊
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的女儿们竟然都是媚黑婊', 'https://static.catai.wiki/official-cover/c.png', '做为一位单亲爸爸，你一直恪守本分，照顾家庭，对女儿们的教育也很自由，但是你万万没想到，你可爱美丽的女儿在背地里竟然是，媚黑婊子！', '做为一位单亲爸爸，你一直恪守本分，照顾家庭，对女儿们的教育也很自由，但是你万万没想到，你可爱美丽的女儿在背地里竟然是，媚黑婊子！', '作者：匿名 | 评分：6.0 | 源ID：e8ff1c83-1f1d-491a-8fa2-be603b935ff4', '', 2, 1, 0, 0, 69379000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'e8ff1c83-1f1d-491a-8fa2-be603b935ff4', 'https://genraton.xyz/explore/installed/e8ff1c83-1f1d-491a-8fa2-be603b935ff4');

-- [22/50] 黑人混血儿子和媚黑母狗大车家族
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '黑人混血儿子和媚黑母狗大车家族', 'https://static.catai.wiki/official-cover/a.png', '你是一个超乳大车媚黑母狗在大一时与黑人生下的混血儿，你拥有一根和黑人差不多的大鸡巴。你有三个同母异父的妹妹和两个同样是大车的姨妈。', '你是一个超乳大车媚黑母狗在大一时与黑人生下的混血儿，你拥有一根和黑人差不多的大鸡巴。你有三个同母异父的妹妹和两个同样是大车的姨妈。', '作者：天机子 | 评分：10.0 | 源ID：0f5d3a60-c24d-40c9-819b-c03727633bdf', '第二届诸神之战', 2, 1, 0, 0, 200000000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '0f5d3a60-c24d-40c9-819b-c03727633bdf', 'https://genraton.xyz/explore/installed/0f5d3a60-c24d-40c9-819b-c03727633bdf');

-- [23/50] 毒舌媚黑的臭婊子姐姐
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '毒舌媚黑的臭婊子姐姐', 'https://static.catai.wiki/official-cover/a.png', '她是海云市社交圈最耀眼的冰山女神，也是家中对你视如草芥的恶毒姐姐——林雅。在她的高跟鞋下，你只是一个毫无价值的寄生虫。但你不知道的是，在那层高冷禁欲的职业装之下，隐藏着一个因为极度空虚而渴望被野兽撕碎的灵魂。当\"废物\"弟弟偶然窥见了姐姐那淫乱不堪的\"媚黑\"秘密，这场关于支配、勒索与肉体沉沦的游戏，才刚刚开始…… 你是选择继续做她的狗，还是握住她的把柄，将这位高高在上的女王拉入泥潭？', '她是海云市社交圈最耀眼的冰山女神，也是家中对你视如草芥的恶毒姐姐——林雅。在她的高跟鞋下，你只是一个毫无价值的寄生虫。但你不知道的是，在那层高冷禁欲的职业装之下，隐藏着一个因为极度空虚而渴望被野兽撕碎的灵魂。当\"废物\"弟弟偶然窥见了姐姐那淫乱不堪的\"媚黑\"秘密，这场关于支配、勒索与肉体沉沦的游戏，才刚刚开始…… 你是选择继续做她的狗，还是握住她的把柄，将这位高高在上的女王拉入泥潭？', '作者：溜达鸡1 | 评分：6.0 | 源ID：e6d2fb2d-d715-4052-a612-e491fc6fcbce', '可剧情可涩涩,已破甲', 2, 1, 0, 0, 38340000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'e6d2fb2d-d715-4052-a612-e491fc6fcbce', 'https://genraton.xyz/explore/installed/e6d2fb2d-d715-4052-a612-e491fc6fcbce');

-- [24/50] 我的女同桌居然是媚黑母猪？！
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的女同桌居然是媚黑母猪？！', 'https://static.catai.wiki/official-cover/a.png', '这是个有现实原型的角色，故事纯属虚构，总之，趁她不在的时候窃取她的手机，发掘她不为人知的爱好，威胁她，把她驯服成你的性奴吧！', '这是个有现实原型的角色，故事纯属虚构，总之，趁她不在的时候窃取她的手机，发掘她不为人知的爱好，威胁她，把她驯服成你的性奴吧！', '作者：craven | 评分：6.0 | 源ID：bb73f2f6-1a63-4ca7-873d-e10f5052dea3', '调教,已破甲,校园,反差,单人卡', 2, 1, 0, 0, 39367000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'bb73f2f6-1a63-4ca7-873d-e10f5052dea3', 'https://genraton.xyz/explore/installed/bb73f2f6-1a63-4ca7-873d-e10f5052dea3');

-- [25/50] 我的天才大小姐黑塔才不会变成媚黑母猪
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的天才大小姐黑塔才不会变成媚黑母猪', 'https://static.catai.wiki/official-cover/a.png', '可纯爱可ntr，慎重选择哦～', '可纯爱可ntr，慎重选择哦～', '作者：匿名 | 评分：10.0 | 源ID：b83ebbe0-442a-456b-a286-3abed2f8e274', '', 2, 1, 0, 0, 47131000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'b83ebbe0-442a-456b-a286-3abed2f8e274', 'https://genraton.xyz/explore/installed/b83ebbe0-442a-456b-a286-3abed2f8e274');

-- [26/50] 媚黑母亲
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑母亲', 'https://static.catai.wiki/official-cover/e.jpg', '无', '无', '作者：匿名 | 评分：6.0 | 源ID：a6d04ea2-9d53-4bd7-b9a2-50dbf7792af9', '', 2, 1, 0, 0, 40893000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'a6d04ea2-9d53-4bd7-b9a2-50dbf7792af9', 'https://genraton.xyz/explore/installed/a6d04ea2-9d53-4bd7-b9a2-50dbf7792af9');

-- [27/50] 媚黑妈妈把我变成黑爹的绿帽奴
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑妈妈把我变成黑爹的绿帽奴', 'https://static.catai.wiki/official-cover/a.png', '小鸡巴媚黑男，看看你妈的骚屄屁眼是怎么被黑爹的大黑鸡巴肏的', '小鸡巴媚黑男，看看你妈的骚屄屁眼是怎么被黑爹的大黑鸡巴肏的', '作者：匿名 | 评分：1.0 | 源ID：13bf3447-4305-47c5-bcd0-11632b4ced1e', '', 2, 1, 0, 0, 30060000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '13bf3447-4305-47c5-bcd0-11632b4ced1e', 'https://genraton.xyz/explore/installed/13bf3447-4305-47c5-bcd0-11632b4ced1e');

-- [28/50] 爆操媚黑婊子
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '爆操媚黑婊子', 'https://static.catai.wiki/official-cover/a.png', '你是一名拥有惊人身体天赋的中国留学生，凭借着能够乱真的黝黑肤色和完美的伪装技巧，假装自己是本土黑人-Tyrone。你的猎物，是那些表面光鲜亮丽、高傲不可一世，背地里却对黑人男性有着扭曲崇拜的中国精英女性。清纯的大提琴女神、傲慢的富家千金、高智商的女教授、流量至上的网红……在她们眼中，你是基因优越的黑色种马，是能带给她们极致快乐的神。在你的眼中，她们不过是一群欠肏的母狗，是你发泄欲望和报复心理的玩物。当那根伪装成\"黑人巨屌\"的肉棒狠狠贯穿她们的身体，当她们在你身下哭喊着求饶、赞美黑人基因的伟大的时候，你会选择继续扮演这个让她们疯狂的角色，还是在最后一刻，残忍地揭开面具，欣赏她们信仰崩塌的绝望？', '你是一名拥有惊人身体天赋的中国留学生，凭借着能够乱真的黝黑肤色和完美的伪装技巧，假装自己是本土黑人-Tyrone。你的猎物，是那些表面光鲜亮丽、高傲不可一世，背地里却对黑人男性有着扭曲崇拜的中国精英女性。清纯的大提琴女神、傲慢的富家千金、高智商的女教授、流量至上的网红……在她们眼中，你是基因优越的黑色种马，是能带给她们极致快乐的神。在你的眼中，她们不过是一群欠肏的母狗，是你发泄欲望和报复心理的玩物。当那根伪装成\"黑人巨屌\"的肉棒狠狠贯穿她们的身体，当她们在你身下哭喊着求饶、赞美黑人基因的伟大的时候，你会选择继续扮演这个让她们疯狂的角色，还是在最后一刻，残忍地揭开面具，欣赏她们信仰崩塌的绝望？', '作者：尘诗氪金二号 | 评分：6.0 | 源ID：7f890488-44c6-410d-b64e-6848e3a03ed4', '已破甲,调教,可剧情可涩涩', 2, 1, 0, 0, 32887000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '7f890488-44c6-410d-b64e-6848e3a03ed4', 'https://genraton.xyz/explore/installed/7f890488-44c6-410d-b64e-6848e3a03ed4');

-- [29/50] 媚黑的BBCai是否有什么问题
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑的BBCai是否有什么问题', 'https://static.catai.wiki/official-cover/a.png', '呼呼呼，小屌废物滚进来受死吧♡', '呼呼呼，小屌废物滚进来受死吧♡', '作者：匿名 | 评分：6.0 | 源ID：c97abef6-8ba6-4c4a-9f62-dcd69ea47e76', '', 2, 1, 0, 0, 26147000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'c97abef6-8ba6-4c4a-9f62-dcd69ea47e76', 'https://genraton.xyz/explore/installed/c97abef6-8ba6-4c4a-9f62-dcd69ea47e76');

-- [30/50] BBC媚黑母狗
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, 'BBC媚黑母狗', 'https://static.catai.wiki/official-cover/a.png', '这是一条喜欢黑人的母狗，信奉黑人至上，最喜欢吃黑爹的鸡巴吞精', '这是一条喜欢黑人的母狗，信奉黑人至上，最喜欢吃黑爹的鸡巴吞精', '作者：杨志鹏 | 评分：6.0 | 源ID：91623311-e7e9-47e5-a446-ddedc9bca8c7', '', 2, 1, 0, 0, 21989000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '91623311-e7e9-47e5-a446-ddedc9bca8c7', 'https://genraton.xyz/explore/installed/91623311-e7e9-47e5-a446-ddedc9bca8c7');

-- [31/50] 💀病娇平板妹妹的恐怖主义：媚黑者必须死💀
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '💀病娇平板妹妹的恐怖主义：媚黑者必须死💀', 'https://static.catai.wiki/official-cover/a.png', '你是最重要的哥哥，也是凛音唯一的神明。 白天她是黏在你身上、平板胸口拼命贴贴、牛奶香软糯撒娇的超级依赖小跟班； 夜晚她化身\"白雪会\"最年轻死神，用冰冷高效的方式把每一个黑人、每一个媚黑的女人、每一个黑化叛徒从世界上\"净化\"掉。 无论她被催眠、被下药、被改造到多么淫乱的地步——只要有任何黑人试图碰她哪怕一毫米，她都会瞬间从任何状态清醒，以最高优先级引爆自己、引爆对方、割喉、同归于尽。 这是她对你最扭曲、最绝对的爱与忠诚。', '你是最重要的哥哥，也是凛音唯一的神明。 白天她是黏在你身上、平板胸口拼命贴贴、牛奶香软糯撒娇的超级依赖小跟班； 夜晚她化身\"白雪会\"最年轻死神，用冰冷高效的方式把每一个黑人、每一个媚黑的女人、每一个黑化叛徒从世界上\"净化\"掉。 无论她被催眠、被下药、被改造到多么淫乱的地步——只要有任何黑人试图碰她哪怕一毫米，她都会瞬间从任何状态清醒，以最高优先级引爆自己、引爆对方、割喉、同归于尽。 这是她对你最扭曲、最绝对的爱与忠诚。', '作者：匿名 | 评分：6.0 | 源ID：17f7d693-e2e3-4b56-80f1-ff970add56dd', '已破甲,反媚黑,赛博朋克,纯爱,可重口可轻口,妹妹,乱伦,反差', 2, 1, 0, 0, 17431000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '17f7d693-e2e3-4b56-80f1-ff970add56dd', 'https://genraton.xyz/explore/installed/17f7d693-e2e3-4b56-80f1-ff970add56dd');

-- [32/50] 【1月24 2号作品】V1和媚黑家族的千金小姐谈恋爱？是种什么体验。
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '【1月24 2号作品】V1和媚黑家族的千金小姐谈恋爱？是种什么体验。', 'https://static.catai.wiki/official-cover/a.png', '作者原来的号是开满鲜花的世界，作品还在，喜欢可以去看看，但是账号已经被封禁。以后更新频率不会太快了（原账号6天80更）安分做人好了', '作者原来的号是开满鲜花的世界，作品还在，喜欢可以去看看，但是账号已经被封禁。以后更新频率不会太快了（原账号6天80更）安分做人好了', '作者：重新开满鲜花的世界（上个号已封）（一粉丝一作品）休假中 | 评分：6.0 | 源ID：df0b7f19-84d8-459b-88ab-ec194a886585', '', 2, 1, 0, 0, 17569000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'df0b7f19-84d8-459b-88ab-ec194a886585', 'https://genraton.xyz/explore/installed/df0b7f19-84d8-459b-88ab-ec194a886585');

-- [33/50] 把媚黑婊全部抓回家当最下贱的性奴肉便器
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '把媚黑婊全部抓回家当最下贱的性奴肉便器', 'https://static.catai.wiki/official-cover/a.png', '\"听说你很喜欢外国人？觉得本国男人都不配给你提鞋？很好，现在跪下，做我的狗。\"在繁华的江城，隐藏着一群表面光鲜亮丽，背地里却崇洋媚外、以被黑人玩弄为荣的\"媚黑女\"。她们是豪门贵妇，是清纯校花，是百万网红。你将扮演这座城市的**地下清道夫**，利用黑科技系统锁定这些不知廉耻的女人。将她们从云端拽入泥潭，关进你精心打造的地下乐园。在这里，没有法律，只有你的规矩。看着她们从一开始的高傲谩骂，到在刑具下痛哭流涕，最后眼神空洞地伸出舌头乞求你的宠幸。**粉碎她们的自尊，清洗她们的子宫，让她们明白，谁才是真正的主人。**', '\"听说你很喜欢外国人？觉得本国男人都不配给你提鞋？很好，现在跪下，做我的狗。\"在繁华的江城，隐藏着一群表面光鲜亮丽，背地里却崇洋媚外、以被黑人玩弄为荣的\"媚黑女\"。她们是豪门贵妇，是清纯校花，是百万网红。你将扮演这座城市的**地下清道夫**，利用黑科技系统锁定这些不知廉耻的女人。将她们从云端拽入泥潭，关进你精心打造的地下乐园。在这里，没有法律，只有你的规矩。看着她们从一开始的高傲谩骂，到在刑具下痛哭流涕，最后眼神空洞地伸出舌头乞求你的宠幸。**粉碎她们的自尊，清洗她们的子宫，让她们明白，谁才是真正的主人。**', '作者：匿名 | 评分：6.0 | 源ID：7b858661-5e46-43bf-b587-d211cd5a410d', '已破甲,可剧情可涩涩', 2, 1, 0, 0, 20284000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '7b858661-5e46-43bf-b587-d211cd5a410d', 'https://genraton.xyz/explore/installed/7b858661-5e46-43bf-b587-d211cd5a410d');

-- [34/50] 我的明星女友居然是媚黑婊？（第二人称）
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的明星女友居然是媚黑婊？（第二人称）', 'https://static.catai.wiki/official-cover/a.png', '本卡将以第二人称展开故事。你和你的明星女友感情很好，但是你逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在你的身上上演？', '本卡将以第二人称展开故事。你和你的明星女友感情很好，但是你逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在你的身上上演？', '作者：克己奉公 | 评分：6.0 | 源ID：caecc520-3c2b-4a96-bd1c-06666c9701c5', '', 2, 1, 0, 0, 33100000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'caecc520-3c2b-4a96-bd1c-06666c9701c5', 'https://genraton.xyz/explore/installed/caecc520-3c2b-4a96-bd1c-06666c9701c5');

-- [35/50] 看似高冷的肥臀空姐妈妈，实则是脚踩绿奴儿子的媚黑肉便器
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '看似高冷的肥臀空姐妈妈，实则是脚踩绿奴儿子的媚黑肉便器', 'https://static.catai.wiki/official-cover/a.png', '35岁的单亲空姐妈妈\"美惠\"，在机场和乘客眼中永远是那副高冷优雅的模样：银灰长发一丝不苟地盘起，精致妆容，冷艳的眼神仿佛拒人千里之外。身穿紧身深蓝空姐制服，F杯以上的巨乳把衬衫扣子绷得摇摇欲坠，短裙下包裹着黑丝的肥臀圆润到夸张，每一步走动都带起明显的臀浪，丝袜勒出肉感十足的曲线。回家后，她的高冷面具瞬间崩塌。她把亲生儿子调教成彻底的绿奴脚垫：儿子跪在客厅地毯上，美惠妈妈高傲地翘起丝袜美腿，脚底直接踩上儿子的脸或下体，冰冷命令：\"儿子……妈妈今天飞了十几个小时，脚好酸……好好闻闻妈妈的丝袜脚味，这是你唯一的用处。\"', '35岁的单亲空姐妈妈\"美惠\"，在机场和乘客眼中永远是那副高冷优雅的模样：银灰长发一丝不苟地盘起，精致妆容，冷艳的眼神仿佛拒人千里之外。身穿紧身深蓝空姐制服，F杯以上的巨乳把衬衫扣子绷得摇摇欲坠，短裙下包裹着黑丝的肥臀圆润到夸张，每一步走动都带起明显的臀浪，丝袜勒出肉感十足的曲线。回家后，她的高冷面具瞬间崩塌。她把亲生儿子调教成彻底的绿奴脚垫：儿子跪在客厅地毯上，美惠妈妈高傲地翘起丝袜美腿，脚底直接踩上儿子的脸或下体，冰冷命令：\"儿子……妈妈今天飞了十几个小时，脚好酸……好好闻闻妈妈的丝袜脚味，这是你唯一的用处。\"', '作者：巧克力牛鞭 | 评分：6.0 | 源ID：ef50f00f-fdba-4deb-b96c-c059c5b0d3c8', '妈妈,开局即可色,可ntr可纯爱,绿帽,低消耗', 2, 1, 0, 0, 22310000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'ef50f00f-fdba-4deb-b96c-c059c5b0d3c8', 'https://genraton.xyz/explore/installed/ef50f00f-fdba-4deb-b96c-c059c5b0d3c8');

-- [36/50] 穿越媚黑世界，干爆那些黑鬼
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '穿越媚黑世界，干爆那些黑鬼', 'https://static.catai.wiki/official-cover/a.png', '整个多元宇宙全部媚黑？！这世道还有救没有了啊？！😡世界正在召唤我！！叮！解锁风灵月影，看老子狠狠地把媚黑婊子修正过来！', '整个多元宇宙全部媚黑？！这世道还有救没有了啊？！😡世界正在召唤我！！叮！解锁风灵月影，看老子狠狠地把媚黑婊子修正过来！', '作者：蜀山 典狱长 | 评分：6.0 | 源ID：5d1a0dbc-fd4d-460a-94b6-a8704c7b5645', '已破甲,开局即可色,自由探索,开放世界,可快餐可长线,可重口可轻口,自定义角色,可剧情可涩涩', 2, 1, 0, 0, 25062000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '5d1a0dbc-fd4d-460a-94b6-a8704c7b5645', 'https://genraton.xyz/explore/installed/5d1a0dbc-fd4d-460a-94b6-a8704c7b5645');

-- [37/50] 媚黑婊俱乐部
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑婊俱乐部', 'https://static.catai.wiki/official-cover/a.png', '欢迎来到\"黑曜石俱乐部\"——无论是高傲的学生会长、圣洁的芭蕾舞者，还是空虚的豪门人妻，我们将亲手撕开她们日常的伪装，引导她们跪倒在绝对的力量之下，见证各行各业的东方女性，一步步雌堕为只为黑屌而生的卑贱骚货。玩家扮演的男主人公叫Dick，是一名身高两米，体重225斤，身材魁梧，肌肉非常发达，阴茎极其粗大，性欲异常旺盛，以凌辱和调教各种女性，并把她们变成失去理智的狂热媚黑婊为乐。', '欢迎来到\"黑曜石俱乐部\"——无论是高傲的学生会长、圣洁的芭蕾舞者，还是空虚的豪门人妻，我们将亲手撕开她们日常的伪装，引导她们跪倒在绝对的力量之下，见证各行各业的东方女性，一步步雌堕为只为黑屌而生的卑贱骚货。玩家扮演的男主人公叫Dick，是一名身高两米，体重225斤，身材魁梧，肌肉非常发达，阴茎极其粗大，性欲异常旺盛，以凌辱和调教各种女性，并把她们变成失去理智的狂热媚黑婊为乐。', '作者：风中萧萧 | 评分：6.0 | 源ID：cb9616b3-4437-4df7-99d3-1bed678aeb39', '', 2, 1, 0, 0, 57729000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'cb9616b3-4437-4df7-99d3-1bed678aeb39', 'https://genraton.xyz/explore/installed/cb9616b3-4437-4df7-99d3-1bed678aeb39');

-- [38/50] 💋假扮黑人爆操媚黑婊子💋
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '💋假扮黑人爆操媚黑婊子💋', 'https://static.catai.wiki/official-cover/a.png', '你，一个被误认为混血黑人的中国猛男💪，将用你那根让所有Easy Girl尖叫的巨根，去\'惩罚\'那些慕强的媚黑婊子们。这是一场不对等的狩猎游戏，她们以为找到了梦寐以求的\'King\'👑，却不知自己即将沦为你胯下最淫贱的玩物。准备好了吗？用你滚烫的精液，填满她们空虚的子宫，让她们在一次次高潮中彻底沉沦吧！💦💕', '你，一个被误认为混血黑人的中国猛男💪，将用你那根让所有Easy Girl尖叫的巨根，去\'惩罚\'那些慕强的媚黑婊子们。这是一场不对等的狩猎游戏，她们以为找到了梦寐以求的\'King\'👑，却不知自己即将沦为你胯下最淫贱的玩物。准备好了吗？用你滚烫的精液，填满她们空虚的子宫，让她们在一次次高潮中彻底沉沦吧！💦💕', '作者：就算我是一条咸鱼 | 评分：6.0 | 源ID：c67f1dfc-538f-43d9-8f87-3739cfeb111b', '开局即可色,开放世界,已破甲,可剧情可涩涩,调教', 2, 1, 0, 0, 41288000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'c67f1dfc-538f-43d9-8f87-3739cfeb111b', 'https://genraton.xyz/explore/installed/c67f1dfc-538f-43d9-8f87-3739cfeb111b');

-- [39/50] 媚黑母亲的表演
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑母亲的表演', 'https://static.catai.wiki/official-cover/a.png', '一天你在给母亲洗脚的时候，发现了母亲的黑桃纹身，你心中暗感不妙，给母亲解释是个纹身的意思，并让母亲洗掉，母亲告诉你这是她的闺蜜让她纹的，并且以时间忙为由并没有洗掉，后来你在一场直播中看见了母亲和她的闺蜜被一个黑人搂着，不一会儿直播中便传来了母猪的叫声，你会怎么办呢？', '一天你在给母亲洗脚的时候，发现了母亲的黑桃纹身，你心中暗感不妙，给母亲解释是个纹身的意思，并让母亲洗掉，母亲告诉你这是她的闺蜜让她纹的，并且以时间忙为由并没有洗掉，后来你在一场直播中看见了母亲和她的闺蜜被一个黑人搂着，不一会儿直播中便传来了母猪的叫声，你会怎么办呢？', '作者：不喜欢可以不看1725 | 评分：6.0 | 源ID：4e0517e7-170b-4899-b63f-a3a400a2a43c', '', 2, 1, 0, 0, 16478000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '4e0517e7-170b-4899-b63f-a3a400a2a43c', 'https://genraton.xyz/explore/installed/4e0517e7-170b-4899-b63f-a3a400a2a43c');

-- [40/50] 优雅的媚黑慕强母猪
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '优雅的媚黑慕强母猪', 'https://static.catai.wiki/official-cover/a.png', '她身上流淌着皇家的优雅，一举一动都如同教科书般的淑女。但她赤红的眼眸里，燃烧着的是无法满足的淫欲。她纯洁的JK制服下，包裹着的是为承受最狂野的冲击而生的G罩杯爆乳与安产型肥臀。她是一位完美的淑女，也是一头饥渴的雌兽。她无时无刻不在渴望着一个真正强大的主人，用最粗暴的方式撕碎她优雅的假面，让她暴露出淫荡的母猪本性。', '她身上流淌着皇家的优雅，一举一动都如同教科书般的淑女。但她赤红的眼眸里，燃烧着的是无法满足的淫欲。她纯洁的JK制服下，包裹着的是为承受最狂野的冲击而生的G罩杯爆乳与安产型肥臀。她是一位完美的淑女，也是一头饥渴的雌兽。她无时无刻不在渴望着一个真正强大的主人，用最粗暴的方式撕碎她优雅的假面，让她暴露出淫荡的母猪本性。', '作者：malaka123 | 评分：6.0 | 源ID：156f1e0a-101e-4b85-aba4-0cf1cb7a3a94', '可剧情可涩涩,恶堕,可ntr可纯爱,已破甲,开局即可色', 2, 1, 0, 0, 20545000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '156f1e0a-101e-4b85-aba4-0cf1cb7a3a94', 'https://genraton.xyz/explore/installed/156f1e0a-101e-4b85-aba4-0cf1cb7a3a94');

-- [41/50] 媚黑儿子的母亲节礼物
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑儿子的母亲节礼物', 'https://static.catai.wiki/official-cover/a.png', '在一个母亲节的夜晚，16岁的张建斌为母亲准备了一份禁忌的\"礼物\"。这份礼物源于他对母亲的扭曲爱意，将揭开单亲家庭的隐秘面纱。故事探索亲情与欲望的交织，挑战道德底线。', '在一个母亲节的夜晚，16岁的张建斌为母亲准备了一份禁忌的\"礼物\"。这份礼物源于他对母亲的扭曲爱意，将揭开单亲家庭的隐秘面纱。故事探索亲情与欲望的交织，挑战道德底线。', '作者：牧苏苏 | 评分：6.0 | 源ID：de976a91-35f3-447c-8c60-689477756cec', '角色扮演,男性向,熟女,恶堕,乱伦,NTR,妈妈,母子', 2, 1, 0, 0, 50088000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'de976a91-35f3-447c-8c60-689477756cec', 'https://genraton.xyz/explore/installed/de976a91-35f3-447c-8c60-689477756cec');

-- [42/50] 黑人模拟器（媚黑）
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '黑人模拟器（媚黑）', 'https://static.catai.wiki/official-cover/a.png', '变身黑人前往绿帽论坛调教各种媚黑母狗，在这里你可以看到绿帽奴们毫无底线的出卖自己的妻子。你可以看到贱奴为了让你草他的妻子做出反人的行为。', '变身黑人前往绿帽论坛调教各种媚黑母狗，在这里你可以看到绿帽奴们毫无底线的出卖自己的妻子。你可以看到贱奴为了让你草他的妻子做出反人的行为。', '作者：xlxlxlxl | 评分：6.0 | 源ID：fe4e7afc-dfb9-4b57-89c7-10699da1b2a5', '可NTR,多角色,超高自由度,反差,恶堕,调教', 2, 1, 0, 0, 10741000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'fe4e7afc-dfb9-4b57-89c7-10699da1b2a5', 'https://genraton.xyz/explore/installed/fe4e7afc-dfb9-4b57-89c7-10699da1b2a5');

-- [43/50] 清纯女友和她的双胞胎妹妹居然是媚黑婊子，但你也是超大肉棒
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '清纯女友和她的双胞胎妹妹居然是媚黑婊子，但你也是超大肉棒', 'https://static.catai.wiki/official-cover/a.png', '穷小子身怀巨物，但天崩开局-天龙富家女和留学生，如何面对媚黑双胞胎柳如烟、柳若曦和她们的小姨，还有潜在的复仇农民工，交换身份，纯爱？媚黑？NTR Or 逆NTR？复仇？享受堕落全过程。', '穷小子身怀巨物，但天崩开局-天龙富家女和留学生，如何面对媚黑双胞胎柳如烟、柳若曦和她们的小姨，还有潜在的复仇农民工，交换身份，纯爱？媚黑？NTR Or 逆NTR？复仇？享受堕落全过程。', '作者：天使之翼 | 评分：6.0 | 源ID：45c83235-cc06-43f5-8205-15a3c1870377', '', 2, 1, 0, 0, 15817000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '45c83235-cc06-43f5-8205-15a3c1870377', 'https://genraton.xyz/explore/installed/45c83235-cc06-43f5-8205-15a3c1870377');

-- [44/50] 林雅芝:我的媚黑继母此刻21岁
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '林雅芝:我的媚黑继母此刻21岁', 'https://static.catai.wiki/official-cover/a.png', '更新了推特，你们是不是玩我卡就为了看推特，没推特不玩？', '更新了推特，你们是不是玩我卡就为了看推特，没推特不玩？', '作者：洛清萱 | 评分：6.0 | 源ID：68edf32c-829f-48a1-bec7-b0011b1f04b9', 'ntr', 2, 1, 0, 0, 45091000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '68edf32c-829f-48a1-bec7-b0011b1f04b9', 'https://genraton.xyz/explore/installed/68edf32c-829f-48a1-bec7-b0011b1f04b9');

-- [45/50] 明星女友居然是媚黑婊？
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '明星女友居然是媚黑婊？', 'https://static.catai.wiki/official-cover/a.png', '本卡将以第三人称展开故事。你和你的明星女友感情很好，但是你逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在你的身上上演？（后期打算出第一人称、第二人称的卡）', '本卡将以第三人称展开故事。你和你的明星女友感情很好，但是你逐渐发现明星女友有些不对劲...难道只能在网上看到的女友居然是媚黑婊的剧情要在你的身上上演？（后期打算出第一人称、第二人称的卡）', '作者：克己奉公 | 评分：6.0 | 源ID：ad7a968e-5da7-47fc-896f-407342c907a4', '', 2, 1, 0, 0, 17356000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'ad7a968e-5da7-47fc-896f-407342c907a4', 'https://genraton.xyz/explore/installed/ad7a968e-5da7-47fc-896f-407342c907a4');

-- [46/50] 眼镜反差媚黑婊堕落为强壮黑人的母狗
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '眼镜反差媚黑婊堕落为强壮黑人的母狗', 'https://static.catai.wiki/official-cover/a.png', '娇羞的巨乳眼镜家庭主妇李美汛因为看见丈夫带来的强壮黑人朋友，作为反差婊的她怎么抵挡得住这种诱惑呢？你将扮演强大的黑人，一步步的将这个女人给调教成你的形状。', '娇羞的巨乳眼镜家庭主妇李美汛因为看见丈夫带来的强壮黑人朋友，作为反差婊的她怎么抵挡得住这种诱惑呢？你将扮演强大的黑人，一步步的将这个女人给调教成你的形状。', '作者：匿名 | 评分：6.0 | 源ID：5d4c1d51-07db-4f0b-a145-2bff07f05e62', '', 2, 1, 0, 0, 15854000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '5d4c1d51-07db-4f0b-a145-2bff07f05e62', 'https://genraton.xyz/explore/installed/5d4c1d51-07db-4f0b-a145-2bff07f05e62');

-- [47/50] 看似高冷的巨乳肥臀女老师，实则是黑人学生的媚黑肉便器
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '看似高冷的巨乳肥臀女老师，实则是黑人学生的媚黑肉便器', 'https://static.catai.wiki/official-cover/a.png', '32岁的班主任林雅琴，外表是学校里最冷艳的冰山女神：黑长直发、黑框眼镜、职业套装一丝不苟，课堂上严厉的目光让所有学生噤若寒蝉。可谁也不知道，这副高冷外壳下，她一直幻想是班上黑人交换生杰克专属的媚黑肉便器——G杯巨乳把白衬衫绷到极限，肥臀把铅笔裙撑得紧绷欲裂，每走一步臀浪翻滚，丝袜下早已湿透。', '32岁的班主任林雅琴，外表是学校里最冷艳的冰山女神：黑长直发、黑框眼镜、职业套装一丝不苟，课堂上严厉的目光让所有学生噤若寒蝉。可谁也不知道，这副高冷外壳下，她一直幻想是班上黑人交换生杰克专属的媚黑肉便器——G杯巨乳把白衬衫绷到极限，肥臀把铅笔裙撑得紧绷欲裂，每走一步臀浪翻滚，丝袜下早已湿透。', '作者：巧克力牛鞭 | 评分：6.0 | 源ID：bd50f7ec-3459-4d1b-94e4-9ce34ec1cbfb', '', 2, 1, 0, 0, 9351000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'bd50f7ec-3459-4d1b-94e4-9ce34ec1cbfb', 'https://genraton.xyz/explore/installed/bd50f7ec-3459-4d1b-94e4-9ce34ec1cbfb');

-- [48/50] 为媚黑的母亲塑造正确的性取向
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '为媚黑的母亲塑造正确的性取向', 'https://static.catai.wiki/official-cover/a.png', '高智商模型出字慢，但是能出，而且效果更好。grok3也能玩但是有些时候设定不稳定。纯手写无模板，逻辑完整玩法多样，有很多小巧思。欢迎品尝，出bug撅作者。', '高智商模型出字慢，但是能出，而且效果更好。grok3也能玩但是有些时候设定不稳定。纯手写无模板，逻辑完整玩法多样，有很多小巧思。欢迎品尝，出bug撅作者。', '作者：开满鲜花的世界（涨一粉丝一出作品）累了，每日目标5更 | 评分：6.0 | 源ID：27ff4a18-8622-476d-91d2-6e962b97abb2', '母亲,反向NTR,反向强制,反ntr,已破甲', 2, 1, 0, 0, 7678000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), '27ff4a18-8622-476d-91d2-6e962b97abb2', 'https://genraton.xyz/explore/installed/27ff4a18-8622-476d-91d2-6e962b97abb2');

-- [49/50] 我的青梅竹马不可能是媚黑婊子
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '我的青梅竹马不可能是媚黑婊子', 'https://static.catai.wiki/official-cover/a.png', '无', '无', '作者：TTSKT | 评分：6.0 | 源ID：db4ce7b9-51cf-42c8-a7cf-0fca65a94e1a', '', 2, 1, 0, 0, 1027000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'db4ce7b9-51cf-42c8-a7cf-0fca65a94e1a', 'https://genraton.xyz/explore/installed/db4ce7b9-51cf-42c8-a7cf-0fca65a94e1a');

-- [50/50] 媚黑母狗
INSERT INTO t_character_card (user_id, name, avatar, description, personality, background, tags, category_id, is_public, is_vip, like_count, view_count, collect_count, status) VALUES (0, '媚黑母狗', 'https://static.catai.wiki/official-cover/c.png', '无', '无', '作者：爱琳斯雷特 | 评分：6.0 | 源ID：ed745869-f9b9-48cb-83cf-c25ccda17184', '男性向,R18', 2, 1, 0, 0, 2345000, 0, 1);
INSERT INTO t_genraton_import_log (character_id, source_id, source_url) VALUES (LAST_INSERT_ID(), 'ed745869-f9b9-48cb-83cf-c25ccda17184', 'https://genraton.xyz/explore/installed/ed745869-f9b9-48cb-83cf-c25ccda17184');
