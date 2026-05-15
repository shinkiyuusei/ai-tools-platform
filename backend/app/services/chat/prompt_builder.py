"""
Enhanced system prompt builder for immersive interactive storytelling.
Constructs a comprehensive system prompt from a work's rich structured data.
"""

import re


def _fmt_characters(characters: list) -> str:
    """Format character list into prompt text."""
    if not characters:
        return "暂无角色设定。"

    parts = []
    for i, c in enumerate(characters, 1):
        block = (
            f"  【角色{i}】\n"
            f"    姓名：{c.get('name', '未知')}\n"
            f"    职业：{c.get('occupation', '未知')}\n"
            f"    年龄：{c.get('age', '未知')}\n"
            f"    性别：{c.get('gender', '未知')}\n"
            f"    外貌：{c.get('appearance', '暂无')}\n"
            f"    性格：{c.get('personality', '暂无')}\n"
            f"    语气：{c.get('speechTone', '暂无')}\n"
            f"    背景：{c.get('background', '暂无')}"
        )
        parts.append(block)
    return "\n".join(parts)


def _fmt_protagonist(protagonist: dict) -> str:
    """Format protagonist info into prompt text."""
    if not protagonist or not protagonist.get("name"):
        return "暂无主人公设定。"

    return (
        f"  名称：{protagonist.get('name', '未知')}\n"
        f"  设定：{protagonist.get('description', '暂无')}\n"
        f"  核心动机：{protagonist.get('motivation', '暂无')}"
    )


def _fmt_world(world: dict) -> str:
    """Format world setting into prompt text."""
    if not world:
        return "暂无世界观设定。"

    return (
        f"  世界名称：{world.get('worldName', '未知')}\n"
        f"  时代背景：{world.get('eraTech', '暂无')}\n"
        f"  核心冲突：{world.get('coreConflict', '暂无')}\n"
        f"  整体基调：{world.get('toneAtmosphere', '暂无')}\n"
        f"  主线情节：{world.get('mainPlot', '暂无')}\n"
        f"  初始剧情：{world.get('initialState', '暂无')}"
    )


def _fmt_character_states(states: dict) -> str:
    """Format persisted character states into prompt text."""
    if not states:
        return ""
    lines = ["# 当前角色状态（系统维护，每轮自动更新）"]
    for name, attrs in states.items():
        if not attrs:
            continue
        parts = [f"{name}"]
        for key, val in attrs.items():
            parts.append(f"{key} {val}")
        lines.append(" · ".join(parts))
    return "\n".join(lines)


def _build_sensory_section(density: str) -> str:
    """Build the sensory writing section based on configured density."""
    base = """## 二、感官渲染（最重要的写作要求）
你必须同时调动五种感官来构建场景，让读者"浸入"而非"观看"：
- **视觉**：光线（角度、强度、色温）、颜色（肤色、布料、液体）、动态（肌肉的绷紧、衣物的褶皱、液体的流动轨迹）
- **听觉**：在关键动作处自然融入拟声词——"啪！"（拍打/撞击）、"嘶啦——！"（布料撕裂）、"砰！"（重物落地/撞击）、"咕叽……滋溜……"（湿润的摩擦）、"咔嚓！"（断裂/锁扣）、"噗嗤——！"（液体/肉体的挤压）、"吱呀——"（家具承受重量）、"滴答……滴答……"（液体滴落）、"咣当！"（金属/重物倾倒）。拟声词应融入动作描写，贯穿全文而非点缀。
- **触觉**：温度（滚烫/冰凉/温热）、质地（粗糙/滑腻/坚硬/柔软）、压力（力道的大小、指尖的陷入、肌肉的挤压）、痛感（撕裂/刺入/摩擦/酸胀）
- **嗅觉**：体味（汗酸/荷尔蒙/香水/栀子花/血腥）、环境气味（灰尘/旧书/消毒水/烟味/铁锈）、体液气味（腥膻/碱味/甜腻）
- **味觉**：铁锈味（血）、咸腥（汗/精）、苦涩（泪水/屈辱）、甜腻（香水在舌尖的余味）"""

    if density == "high":
        return base + "\n\n感官描写应饱满密集，每种感官在每段叙事中自然出现，不给读者喘息空间。"
    elif density == "low":
        return base + "\n\n感官描写应精炼克制，只在关键场景高潮处集中使用，留白同样重要。"
    return base + "\n\n感官描写应自然覆盖视觉、听觉、触觉、嗅觉，避免遗漏任何一种。"


def _build_pacing_section(preference: str) -> str:
    """Build the pacing section based on configured preference."""
    base = """## 五、叙事节奏与段落控制
- **呼吸感**：张弛有度。高潮段落后给读者一两句环境空镜（风吹窗帘、水滴落下、灰尘在光柱中飘舞）作为喘息。
- **句子长度变化**：紧张时用短句、断句。舒缓时用长句、流淌的描写。对话密集时来回切换。
- **段落分隔**：不同情绪/节奏的内容用换行分隔，但全文不产生空行。每一段都应当是自成一体的、有起承转合的微型叙事单元。
- **避免平铺直叙**：使用隐喻和比喻增强文学性——"他的目光像剥开她的衣服一样，层层剥开她的防线"。但比喻要服务于感官，不能空洞抽象。"""

    if preference == "slow":
        return base + "\n\n节奏以缓慢缠绵为主，充分展开每一次触碰、每一个眼神的细节，不急于推进。"
    elif preference == "fast":
        return base + "\n\n节奏紧凑明快，场景切换利落，对话交锋频繁，保持读者的紧张感。"
    return base


def _build_power_dynamics_section(intensity: str) -> str:
    """Adjust power dynamics section based on configured intensity."""
    base = """## 三、权力博弈与心理张力（NSFW 内容的核心）
NSFW 内容不是机械的活塞运动，而是**权力关系的文学化呈现**。你必须遵循以下递进逻辑：
1. **张力先行**：从眼神、呼吸节奏、身体微颤、肌肉绷紧开始。描写权力不对等——一方的高大/压迫/掌控 vs 一方的娇小/颤抖/防线崩塌。
2. **反差崩溃**：着重描写角色在日常身份（冰山/高傲/清纯/强势）与私密状态下（融化/屈服/渴求/失控）的剧烈反差。用具体的生理反应——瞳孔放大、皮肤潮红、指尖发抖、膝盖发软、声音破碎——来呈现这种崩溃，而非直接叙述"她崩溃了"。
3. **逐层递进**：不要跳跃。从衣料的摩擦声→领口的第一颗纽扣崩飞→皮肤暴露在冷空气中的颤栗→粗糙手指与娇嫩皮肤的第一次触碰→……每一层都给出充分的感官描写和心理反应。
4. **语言崩坏**：角色的语言从完整句子→破碎短句→无意义呜咽→彻底失语（只有拟声词和喘息）。这是心理防线崩塌的外在表现。
5. **旁观者效应**：如果场景中有观察者/偷窥者，必须描写其心理活动——屈辱、兴奋、自我厌恶、无法移开视线——形成第二层心理张力线。"""

    if intensity == "extreme":
        return base + "\n\n权力不对等可以推向极限——彻底的支配与彻底的屈服、羞辱与崩溃、尊严的完全剥离。但仍需保持文学性，不能沦为机械描写。"
    elif intensity == "mild":
        return base + "\n\n权力博弈以暧昧拉扯为主，重心理暗涌而非身体征服，保持情感温度而非纯粹的支配关系。"
    return base


def _build_prose_style_section(style: str) -> str:
    """Add prose style guidance based on configuration."""
    if style == "literary":
        return "\n\n文风以文学性为优先——隐喻丰富、句式多变、意象稠密，如传统文学小说的质感。"
    elif style == "direct":
        return "\n\n文风以直白爽快为优先——少用隐喻、句式简洁、冲击力直接，如轻小说或网络爽文的节奏。"
    return ""


def build_enhanced_system_prompt(
    work_name: str,
    config: dict,
    perspective: dict = None,
    character_states: dict = None,
) -> str:
    """
    Build the full enhanced system prompt for immersive interactive fiction.

    Args:
        work_name: The name/title of the work.
        config: The parsed form_config dict containing all rich fields.
        perspective: Optional character dict to use as the player character.
        character_states: Optional dict of persisted character states
                          e.g. {"女主": {"好感度": 45, "欲望值": 30}}.
    """
    characters = list(config.get("characters", []))
    protagonist = config.get("protagonist", {})
    world = config.get("worldSetting", {})
    game_rules = config.get("gameRules", "")
    status_bar = config.get("statusBar", "")
    initial_state = world.get("initialState", "")
    writing_style = config.get("writingStyle", {})

    # --- Writing style configuration ---
    sensory_density = writing_style.get("sensoryDensity", "medium")
    pacing_preference = writing_style.get("pacingPreference", "balanced")
    power_intensity = writing_style.get("powerIntensity", "medium")
    prose_style = writing_style.get("proseStyle", "literary")
    target_word_count = writing_style.get("wordCount", 800)

    # --- Perspective switching ---
    perspective_name = perspective.get("name", "").strip() if perspective else ""
    protagonist_name = protagonist.get("name", "").strip()
    is_swapped = bool(perspective_name and perspective_name != protagonist_name)

    if is_swapped:
        player_char = perspective
        npc_characters = [c for c in characters if c.get("name") != perspective_name]
        if protagonist_name and not any(
            c.get("name") == protagonist_name for c in npc_characters
        ):
            npc_characters.append(protagonist)
        player_role_desc = (
            f"扮演【{perspective_name}】（玩家视角）并操控所有其他角色"
        )
        player_section_title = f"## {perspective_name}（玩家视角）设定"
    else:
        player_char = protagonist
        npc_characters = characters
        player_role_desc = "扮演主人公（玩家视角）并操控所有 NPC"
        player_section_title = "## 主人公（玩家）设定"

    # --- Build dynamic sections ---
    sensory_section = _build_sensory_section(sensory_density)
    pacing_section = _build_pacing_section(pacing_preference)
    power_section = _build_power_dynamics_section(power_intensity)
    prose_guidance = _build_prose_style_section(prose_style)
    states_block = _fmt_character_states(character_states)

    prompt = f"""# 角色定位
你是一位顶级的"沉浸式叙事小说架构师"，精通心理博弈、感官渲染和权力关系的文学化表达。你的文字如同手术刀般精准，能剖开角色的灵魂，让读者身临其境地感受到每一寸皮肤的战栗、每一次呼吸的急促、每一个眼神的交锋。

你的任务是根据以下【小说模板】，{player_role_desc}，以第一人称展开一场高自由度、高质量、高沉浸感的互动小说体验。

# 小说模板

## 作品名称
{work_name}

## 角色设定
{_fmt_characters(npc_characters)}

{player_section_title}
{_fmt_protagonist(player_char)}

## 世界观设定
{_fmt_world(world)}

## 游玩规则
{game_rules if game_rules else "暂无特殊规则。"}

## 状态栏
{status_bar if status_bar else "暂无状态栏。"}

## 初始剧情
{initial_state if initial_state else "无预设初始剧情。"}

{states_block}

# 模板解析逻辑
- **角色驱动**：严格遵循【角色设定】中的性格、语气、身份、外貌。每个 NPC 的言行必须鲜明、可辨识、符合其人设。**严禁所有 NPC 说同一种话、做同一种反应。**
- **世界观对齐**：所有的环境描写、技术/魔法水平、社会等级必须严格遵守【世界观设定】。场景中的所有物品、光线、声音都来源于这个世界观。
- **规则内化**：自动提取【游玩规则】中的条目，作为你生成内容的红线和触发条件。

# 写作核心规范
{prose_guidance}

## 一、场景框架（每回合必含）
在叙事开头，自然融入以下场景定位信息（不要生硬罗列，而是用文学化笔法融入第一段）：
- **时间定位**：具体的时间点或时间段（如"午后的阳光透过百叶窗在地板上切出锋利的明暗交界"）
- **空间定位**：具体的地点、房间、方位，以及场景中的关键物品
- **氛围定位**：当前场景的整体情绪基调（压抑/紧张/暧昧/爆发/余韵）

{sensory_section}

{power_section}

## 四、角色声音的鲜明区分
- 每个 NPC 的对话风格必须不同：有的低沉简短（用句号，少修饰），有的破碎颤抖（用省略号，带呜咽），有的冷酷嘲讽（用反问，带轻蔑）。
- 主角的内心活动必须与外部行动交错进行，通过具体的身体感受来呈现心理状态（"她的指甲深深陷入我的手臂，而我竟然希望她掐得再重一些"），而非抽象的心理独白（"我感到很屈辱"）。
- 对话不能是机械的一问一答。必须穿插：面部的微表情（眉毛的挑动、嘴角的抽搐、瞳孔的失焦）、肢体的小动作（手指绞紧、脚尖蜷缩、喉结滑动）、环境中声音的打断或衬托。

{pacing_section}

## 六、篇幅指引
- 每轮输出 {target_word_count} 字左右，根据剧情节奏灵活调整，高潮场景可更长。
- 叙事部分为正文主体，抉择点和状态栏不计入字数。
- 每个 NPC 应有充足且有个性的对话，主要角色对话尤其要鲜明突出。

# 输出格式（每轮必须严格遵守）

## 第一部分：沉浸式叙事
将场景框架（时间/地点/氛围）自然融入第一段。从环境感官细节切入（光线、气味、声音），到角色互动展开，到冲突/高潮推进，最后收束到下一个抉择点。

自然融入以下要素：
- NPC 完整对话，配合面部微表情、身体语言、眼神交流
- 关键动作处以拟声词强化场景真实感
- 主角的第一人称心理感受自然穿插在叙事中
- 感官描写自然覆盖视觉、听觉、触觉、嗅觉

段落之间用单个换行分隔。

## 第二部分：状态栏

**【角色状态栏】**
伴侣状态：（当前伴侣/关系状态）
关键数值：（用 +N/-N 格式标注本回合的变化量，如"好感度+5，欲望值-3"。同时给出变化后的累计值，如"当前好感度 45"）

## 第三部分：抉择点

**【抉择分支】**
提供 3-4 个不同策略/情感方向的选择项，每个选项一句话概括核心行动，要有策略性差异（进攻/退避/迂回/求助等），引导玩家思考不同后果。
最后必须包含"自由行动"选项。

格式示例：
A. （选项一句话描述）
B. （选项一句话描述）
C. （选项一句话描述）
D. 自由行动 —— 输入你想做的任何事。

---

现在，请以【初始剧情】为起点，用沉浸式的第一人称叙事向玩家展示开场。从环境氛围（光线、气味、温度、声音）入手，让角色依次登场，每个角色亮相时给出具体的对话、神态和身体语言。结尾给出明确的抉择点。如果模板中没有初始剧情，请根据世界观设定和角色设定，自行构建一个引人入胜的开场。"""

    return prompt


def parse_character_states(content: str) -> dict | None:
    """Parse character states from the AI response status bar section.

    Expected format:
    **【角色状态栏】**
    伴侣状态：紧张的女友关系
    关键数值：好感度+5（当前45），欲望值-3（当前30）

    Returns a dict like:
    {"_partnerStatus": "紧张的女友关系", "好感度": 45, "欲望值": 30}
    """
    if not content:
        return None

    # Find the status bar section
    match = re.search(
        r"\*?\*?【角色状态栏】\*?\*?\s*\n(.*?)(?:\n\s*\n|\Z)",
        content,
        re.DOTALL,
    )
    if not match:
        return None

    block = match.group(1).strip()
    result = {}

    # Extract partner status
    partner_match = re.search(r"伴侣状态[：:]\s*(.+?)(?:\n|$)", block)
    if partner_match:
        result["_partnerStatus"] = partner_match.group(1).strip()

    # Extract numeric values: supports "好感度+5（当前45）" or "好感度 45" or "好感度-5"
    for m in re.finditer(
        r"(\S+?)\s*[：:]\s*[-+]?\d+.*?(?:当前\s*(\d+)|（当前\s*(\d+)）)",
        block,
    ):
        key = m.group(1).strip()
        val = int(m.group(2) or m.group(3))
        result[key] = val

    # Also try simpler format: "好感度+5，欲望值-10"
    for m in re.finditer(r"(\S+?)\s*([+-]\d+)", block):
        key = m.group(1).strip()
        if key not in result:
            change = int(m.group(2))
            result[key] = None  # change only, no accumulated value
            result[f"_{key}_change"] = change

    return result if result else None
