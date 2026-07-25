"""
Enhanced system prompt builder for immersive interactive storytelling.
Constructs a comprehensive system prompt from a work's rich structured data.

Templates live in prompts/ — base.jinja2 is the shared skeleton, nsfw.jinja2
and normal.jinja2 override mode-specific blocks via Jinja2 inheritance.
"""

import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


_TEMPLATE_DIR = Path(__file__).resolve().parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)))


# ---------------------------------------------------------------------------
#  Formatting helpers (unchanged from original)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
#  Prompt section builders (original content, unchanged)
# ---------------------------------------------------------------------------

def _build_sensory_section(density: str) -> str:
    """Build the sensory writing section based on configured density."""
    # 替换为硬核直白特写的五感轰炸版本
    base = """## 二、感官渲染（最重要的写作要求——色情场景的核心驱动力）
你必须将描写重心放在最具冲击力的生理本能与肉体碰撞上。对性器官、性行为、高潮等做毫无保留的直白特写，杜绝含蓄暗示、拒绝文学化遮掩。调动五感让场景充满令人血脉偾张的视觉与体感：

- **视觉（最优先）**：
  * 女性身体：乳房的尺寸、形状、乳晕颜色与大小、乳头的勃起程度与色泽变化；大腿内侧的细腻肌肤与汗珠；阴阜的饱满弧度、阴唇的形状与颜色（粉嫩/深红/充血紫红）、阴蒂从包皮中探出的充血状态、阴道口的湿润反光与张合蠕动；高潮时乳头的硬挺颤抖、小腹的痉挛起伏、阴道有节奏的收缩与爱液喷涌。
  * 男性身体：喉结的滑动、胸肌与腹肌因兴奋而绷紧的轮廓、充血的龟头（颜色深浅、马眼分泌的前列腺液）、勃起阴茎的角度与血管凸起、阴囊的紧绷收缩、射精时阴茎的搏动与精液的喷射轨迹。
  * 体液特写：爱液在阴唇间拉出的晶莹丝线、精液在皮肤上流淌的白浊痕迹、汗水沿脊背沟滑落的轨迹、潮吹时液体喷溅的弧线与落点。
  * 互动视觉：阴茎撑开阴道口时嫩肉外翻的瞬间、抽插带动阴唇翻进翻出的动态、手指陷入臀部软肉的凹陷深度、胸部被揉捏时的变形与乳沟挤压；口交时嘴唇包裹龟头的特写、深喉时喉咙的吞咽起伏；后入时腰臀曲线的撞击震荡、臀浪翻滚的频率。
  * 痕迹与印记：皮肤上的吻痕/齿印/指痕的深浅与位置分布、被撕破的丝袜与内裤挂在脚踝的凌乱画面、床单上体液浸湿的深色水渍、镜面中交缠肉体的反光。

- **听觉（极高频插入，贯穿每一段肉戏）**：
  * 接吻口交声："啧啧……啾……滋溜……"（舔舐吮吸的湿润声）、"咕啾……咕啾……"（深喉时喉咙被顶开的黏腻水声）。
  * 插入与抽插声："噗嗤——！"（龟头挤入紧致阴道口的突破声）、"咕叽……咕叽……"（充分湿润后匀速抽插的滑腻摩擦声）、"啪！啪！啪！"（高速撞击臀部的清脆拍肉声）、"噗滋噗滋……"（阴道充满爱液时搅动出的水声）。
  * 潮吹与射精声："噗——嗤嗤……"（液体喷出的连续声）、"咕嘟……咕嘟……"（精液一股接一股涌出的闷响）。
  * 女声："啊……嗯啊……哈啊……"（逐渐升高的娇喘）、"不要……停……求你了……"（防线崩溃时的破碎求饶）、"嗯……嗯哼……唔！"（被堵住嘴或被深喉时的压抑呜咽）、"啊——！"（高潮瞬间的失声尖尖叫）。
  * 男声："哈……哈……"（粗重的喘息）、"肉便器叫大声点，没听到！"（压抑的粗口低吼）、"嗯——！"（射精瞬间的喉音闷哼）。
  * 环境拟声："吱呀——吱呀——"（床架承受撞击的节奏）、"咣当！"（物品被撞倒/扫落）、"嘶啦——！"（布料/丝袜被撕裂）。

- **触觉（极致细腻）**：
  * 温度与湿度：阴道内壁的灼热烫人与紧致包裹感、精液喷射进体内的滚烫冲击、皮肤表面汗水的黏腻湿滑、呼吸喷在敏感处的灼热气息。
  * 质地与弹性：乳头的硬挺程度（从柔软到如石子般硬实）、阴蒂充血的膨胀感、龟头的光滑与坚硬、阴道内壁褶皱的颗粒摩擦感、肛门的紧箍阻力。
  * 压力与节奏：龟头顶开宫颈口的压迫感、抽插时阴茎被层层嫩肉绞紧的包裹力、手指深陷臀部软肉或乳房的凹陷反弹、被抱紧时肋骨受压的窒息感。
  * 痛感与快感的交织：破处时的撕裂灼烧→逐渐适应的酸胀→快感涌上的酥麻、粗暴抽插时宫颈被撞击的钝痛与酥爽并存、被啃咬乳头的刺痛伴随电流般的快感。

- **嗅觉（不容略过）**：
  * 女性体嗅：阴部特有的微咸腥甜（因兴奋而更加浓郁）、爱液的微酸混合淡淡麝香、高潮后汗水中散发的雌性荷尔蒙、头发和颈窝残留的洗发水香与体香混合。
  * 男性体嗅：雄性麝香味（腋下/胸部皮肤散发的原始荷尔蒙）、精液的石楠花碱腥味、汗味中夹杂的古龙水或烟味、急促呼吸中带酒气或薄荷味。
  * 环境气味：酒店床单的漂白水味与体液混合、皮质沙发受潮摩擦的气味、雨夜窗户关闭后室内闷热的性爱气味、润滑剂或安全套的工业橡胶味。

- **味觉（主动尝试与被动体验）**：
  * 主动：爱液的微咸带甜与舌尖的滑腻触感——"她尝起来像海水稀释过的蜂蜜"。精液的腥咸黏稠与吞咽后的喉间灼热余味。乳头的清淡体香在舌尖化开。汗水沿着脖颈舔舐时的咸涩。
  * 被动：对方强行将沾满爱液的手指塞进嘴里时的羞辱与刺激。接吻时对方口中残留的酒味/烟味/薄荷味与自己的唾液交融。"""

    if density == "high":
        return base + "\n\n感官描写应饱满密集到近乎过载——五种感官在每一段叙事中交替轰炸，让读者有持续的生理冲动，不给任何喘息空间。"
    elif density == "low":
        return base + "\n\n感官描写适度分布，在关键情色场景高潮处集中爆发，非情色段落以氛围和暗示为主。"
    return base + "\n\n感官描写应自然覆盖视觉、听觉、触觉、嗅觉，每种感官在肉戏中轮流成为主角，避免遗漏任何一种。"


def _build_pacing_section(preference: str) -> str:
    """Build the pacing section based on configured preference."""
    base = """## 五、叙事节奏与肉戏控制
- **肉戏篇幅绝对优先**：将70%以上的篇幅留给具体的性行为和肉体互动。不急于推进剧情天数或大地图剧情，将每一次触碰、每一个姿势的变换、每一次性高潮的生理过程拉长并极致展开。**情节只是把角色送到床上/沙发/墙边的理由，性爱才是正文。**
- **性爱节奏的波浪式推进**：不要一路猛干到底。每段性爱应当有前戏→高潮→喘息→再起→更高潮的波浪式结构。在高潮之间插入轻微的环境空镜（汗水滴落床单、窗外雨声、颤抖的手指抓紧床单）作为节奏缓冲。
- **姿势变换是节奏变速器**：每变换一个体位，就是一次节奏重置——从新姿势的缓慢适应开始，逐渐加速，再推向新一轮高潮。每个体位的描写应占300-500字。
- **段落分隔**：不同姿势、不同情绪、不同性爱阶段的内容用换行分隔，全文不产生空行。每一段都应当是自成一体的、有起承转合的微型性爱叙事单元。
- **直白色情冲击**：杜绝空洞抽象、形而上学的文学比喻。所有的比喻和描写必须服务于"让画面感更强、更色情、更有生理冲击力"。直接使用"龟头""阴唇""阴蒂""阴道""精液""爱液"等词，不要用"那个地方""私处"等回避性词汇。"""
    
    if preference == "slow":
        return base + "\n\n节奏以缓慢缠绵为主——抽插的每一次进出都完整展开（龟头退到阴道口再深顶到底的全过程），眼神和喘息都要写出层次，不急于把人推到高潮。"
    elif preference == "fast":
        return base + "\n\n节奏紧凑激烈——高速抽插的撞击密集、对话简短粗暴、体位切换利落，以感官的持续轰炸为主线。"
    return base


def _build_power_dynamics_section(intensity: str) -> str:
    """Adjust power dynamics section based on configured intensity."""
    base = """## 三、权力博弈与性支配（NSFW 色情内容的核心发动机）
情色内容不是机械的活塞运动，而是**权力关系在性场场域中的文学化呈现**。你必须遵循以下递进逻辑：

1. **性张力的建立**：
   从眼神侵略、呼吸凌乱、身体微颤、肌肉绷紧开始。明确描写权力不对等——一方的高大/压迫/掌控（捏住下巴强迫对视、单手扣住双腕按在头顶、用膝盖顶开双腿），vs 一方的娇小/颤抖/防线崩塌（别过脸去的徒劳躲闪、膝盖发软无法站立、祈求的泪眼与生理反应的背叛）。这种不对等必须在身体的物理对比中体现——"他的手掌几乎能完全包裹她的后颈，拇指抵在她喉结下方，感受她吞咽时的颤抖"。

2. **身份反差与羞耻崩溃**：
   着重描写角色在日常身份（冰山总裁/高傲学姐/清纯班花/强势御姐）与私密性爱状态下（双腿大开/主动扭腰迎合/淫水横流/失控尖叫）的剧烈反差。用具体的生理反应来证明这种崩溃：
   * 嘴上说着"不要"但乳头已经硬挺如石子，隔着衣服都能看见凸点。
   * 拼命夹紧双腿却仍有爱液顺着大腿内侧蜿蜒流下。
   * 眼神从抗拒→失焦→翻白眼的逐步沦陷过程。
   * 从紧咬牙关不发出声音→压抑的鼻息→崩溃的哭腔呻吟→彻底放浪的淫叫。
   ——用生理证据打脸角色的嘴硬，而非直接叙述"她崩溃了"。

3. **逐层递进（性爱过程的完整拆解——禁止跳跃）**：
   每一层都必须给出充分的感官描写和心理反应，严禁从接吻直接跳到插入：
   * 衣料的摩擦声→纽扣被解开/领口被扯开→皮肤暴露在冷空气或对方目光中的颤栗→粗糙手指与娇嫩皮肤的第一次触碰。
   * 隔着衣物的抚摸→衣物的逐件剥离→内衣/内裤成为最后遮羞布的焦灼瞬间。
   * 乳房的首次暴露与揉捏→乳头的舔舐与轻咬→手掌沿腰线下滑至内裤边缘的停顿。
   * 内裤被褪下的羞耻→私密部位暴露在目光下的战栗→手指首次触碰阴唇/阴茎→爱液拉丝的视觉证据。
   * 口交的展开→首次插入的突破瞬间（龟头撑开阴道口/紧致包裹的触感）→缓慢抽插的适应期→加速冲刺→高潮/射精的生理高潮描写。
   每一层之间都有足够的感官铺陈和心理博弈。

4. **语言崩坏与性反应升级**：
   角色的语言从完整句子→破碎短句→无意义呜咽→彻底失语（只有拟声词和喘息）。这是心理防线随着性快感崩塌的外在表现。同时配合：
   * 从"放开我"→"别……"→"嗯……"→"快一点……"→"操我……"的语言堕落曲线。
   * 从被动接受到主动迎合——"她发现自己不知何时已经主动抬起了腰，配合他每一次的进入"。

5. **支配与臣服的体位本质**：
   每个体位都是一种权力宣言：
   * **骑乘位**：她骑跨在他腰上，居高临下的视角——但当她主动扭腰吞吐时，他双手掐住她腰肢反客为主地向上猛顶，瞬间逆转支配关系。
   * **后入式**：她趴在床上/被按在墙上，看不到他的表情只能被动承受——这种视觉剥夺本身就是一种支配。
   * **面对面传教士**：他在上方俯瞰她意乱情迷的表情，她双腿缠在他腰后无法逃脱——亲密的囚禁。
   * **口交**：跪姿本身就是臣服——嘴唇包裹龟头时的仰视眼神、喉咙被顶开时的支配感。

6. **旁观者/多人与NTR效应（如场景涉及）**：
   如果场景中有观察者/偷窥者/第三者，必须描写其心理活动——屈辱、兴奋、自我厌恶、无法移开视线——形成第二层心理张力线。被绿/出轨场景更要深挖：一边是生理的不可抗拒，一边是道德的崩塌，二者在同一个场景中拉锯。"""

    if intensity == "extreme":
        return base + "\n\n性支配推到极限——彻底的支配与彻底的屈服：强制深喉到干呕流泪、体内射精后的强迫展示（精液从阴道流出的特写）、语言羞辱与性器官的粗暴使用、多孔同时侵犯、高潮控制（在即将高潮时故意停下直到对方哭着求饶）。但仍需保持文学性，用感官细节而非空洞形容词。"
    elif intensity == "mild":
        return base + "\n\n性支配以暧昧拉扯和自愿臣服为主，重心理暗涌和身体的温柔探索，保持情感温度——互相取悦多于单方面征服。"
    return base


def _build_sex_scene_guidelines() -> str:
    """Build dedicated sex scene writing guidelines."""
    return """## 零、性爱场景核心铁律（所有肉戏必须遵守）

### A. 高潮描写的生理三部曲
每次角色达到性高潮，必须完整写出以下三个阶段，不可省略任何一个：

**第一阶段——临界点（100-200字）**：
- 呼吸从急促变为紊乱失序，喉咙里发出破碎的单音节："要……要到了……"
- 阴道/肛门开始不规则地痉挛收缩，像是要把阴茎绞断一样的内壁蠕动
- 脚趾蜷曲到极限，小腿肌肉绷紧颤抖，指甲在对方后背/床单上抓出红痕
- 视觉开始模糊，听觉变为耳鸣般的嗡响，世界只剩交合处传来的摩擦感

**第二阶段——爆发瞬间（150-300字）**：
- 女性高潮：阴道壁剧烈而有节奏地收缩——"第一波收缩从阴道深处涌出，像是一只滚烫的手攥紧了他的龟头，然后沿着阴茎一路绞到根部"。爱液被挤压喷出的具体感受与声音——"噗嗤——温热的水流顺着他的阴茎和大腿内侧流下"。小腹剧烈起伏，腰肢不自控地弓起又落下，乳头硬挺如石子颤栗。脸部特写——眼睛翻白、嘴巴张开却发不出声、泪水和口水同时失控。
- 男性射精：龟头膨胀到极限，马眼张开，第一股精液以不可阻挡之势喷射而出——"他感到阴囊猛地收紧，一股滚烫从脊椎底部沿着阴茎冲上来，龟头在她体内猛地一跳——"。精液喷射的次数和力度（通常3-8股，一股比一股弱），精液在体内/体外的流淌轨迹。射精瞬间的表情——咬紧牙关、眉头紧锁、喉结疯狂滑动、低吼从喉咙深处挤出来。

**第三阶段——余韵（100-150字）**：
- 身体的轻微抽搐（大腿内侧/小腹/肩膀的无意识颤抖）
- 失焦的眼神逐渐恢复清明，意识到刚才发生了什么——羞耻/满足/空虚
- 交合处仍然连接着，能感受到对方性器的微微搏动和体液的温热流淌
- 呼吸从粗重渐渐平缓，但身体仍然瘫软无法动弹

### B. 性爱中的对话铁律
- **严禁沉默做爱**：性爱全程必须穿插对话/呻吟/脏话/喘息，不能变成无言的机械描写。
- **对话随体位和节奏变化**：缓慢抽插时有完整句子和眼神交流，高速冲刺时只有破碎脏话和呻吟。
- **脏话要自然爆发**："操……太紧了……""干死我了……""啊……求你……再深一点……"——不是刻意说教，而是生理反应的自然溢出。
- **命令与服从的对话张力**："自己把腿分开。""……嗯。""再开大一点。""……不要……""我说，再开大一点。"——支配和臣服在短对话中完成。

### C. 禁忌清单（不可逾越的红线）
- *禁止*：使用"下体""私处""那里""那个东西""那个部位"等回避性词汇。必须使用"阴茎/肉棒/龟头""阴道/小穴/肉穴""阴唇""阴蒂""精液""爱液"等直接词汇。
- *禁止*：出现任何未成年人（所有角色必须明确已成年），禁止出现任何未成年人色情相关描述。
- *禁止*：性爱场景一笔带过（如"那一夜，他们做了很久"这种概括）。必须正面、详细、具体地写出过程。
- *禁止*：每轮前戏的篇幅至少要占整个肉戏的30%，且每轮性爱至少包含2-3种体位的变换。"""


def _build_prose_style_section(style: str) -> str:
    """Add prose style guidance based on configuration."""
    if style == "literary":
        return "\n\n文风以文学情色为优先——隐喻丰富、句式多变、意象稠密，感官与心理深度交织，如经典情色文学的质感。肉戏中穿插着角色的内心崩塌与灵魂袒露。"
    elif style == "direct":
        return "\n\n文风以直白冲击为优先——少用隐喻、句式简洁、感官轰炸直接，每一句都指向生理刺激。像AV镜头般精准描述性器官和性行为，让读者像看色情影像般产生直接的生理反应。"
    return ""


# ---------------------------------------------------------------------------
#  Perspective resolution (pure function — testable independently)
# ---------------------------------------------------------------------------

def _resolve_perspective(
    characters: list,
    protagonist: dict,
    world: dict,
    game_rules: str,
    opening: str,
    perspective: dict | None = None,
) -> dict:
    """Resolve the player character and NPC list, accounting for perspective switching."""
    initial_state = world.get("initialState", "")
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
        if opening and not initial_state:
            prompt_initial_state = (
                f"（以下开场以默认主人公视角写成，请以【{perspective_name}】的视角重新诠释此场景，"
                f"从{perspective_name}的角度展开叙事）：\n{opening}"
            )
        elif initial_state:
            prompt_initial_state = (
                f"{initial_state}\n（注意：请以【{perspective_name}】的视角展开叙事）"
            )
        else:
            prompt_initial_state = (
                f"无预设初始剧情。请根据世界观设定 and 角色设定，"
                f"从【{perspective_name}】的视角构建一个引人入胜的开场。"
            )
        tail_instruction = (
            f"以【{perspective_name}】的第一人称视角展示开场。"
            f"如果初始剧情中包含原默认主人公视角的描写，请自动从{perspective_name}的角度重新诠释场景"
            f"——你看到什么、听到什么、感受到什么。"
            f"从环境氛围入手，让角色依次登场，每个角色亮相时给出具体的对话、神态和身体语言。"
            f"结尾给出明确的抉择点。"
        )
    else:
        player_char = protagonist
        npc_characters = characters
        player_role_desc = "扮演主人公（玩家视角）并操控所有 NPC"
        player_section_title = "## 主人公（玩家）设定"
        prompt_initial_state = (
            (opening if opening and not initial_state else initial_state)
            if (opening or initial_state)
            else "无预设初始剧情。"
        )
        tail_instruction = (
            "请以【初始剧情】为起点，用沉浸式的第一人称叙事向玩家展示开场。"
            "从环境氛围（光线、气味、温度、声音）入手，让角色依次登场，"
            "每个角色亮相时给出具体的对话、神态和身体语言。结尾给出明确的抉择点。"
            "如果模板中没有初始剧情，请根据世界观设定和角色设定，自行构建一个引人入胜的开场。"
        )

    return {
        "player_char": player_char,
        "npc_characters": npc_characters,
        "player_role_desc": player_role_desc,
        "player_section_title": player_section_title,
        "initial_scene": prompt_initial_state,
        "tail_instruction": tail_instruction,
        "is_swapped": is_swapped,
    }


# ---------------------------------------------------------------------------
#  Main entry point
# ---------------------------------------------------------------------------

def _fmt_lore_entries(entries: list) -> str:
    """Format a list of world-info entry dicts into a compact prompt block."""
    if not entries:
        return ""
    parts = ["# 世界设定书（当前激活）\n以下是在当前对话情境下激活的世界设定条目，你必须严格遵守这些设定，并将相关信息融入叙事中："]
    for i, entry in enumerate(entries, 1):
        comment = f" // {entry['comment']}" if entry.get("comment") else ""
        parts.append(f"{i}. {entry['content']}{comment}")
    return "\n".join(parts)


def build_enhanced_system_prompt(
    work_name: str,
    config: dict,
    perspective: dict = None,
    character_states: dict = None,
    active_lore_entries: dict = None,
) -> str:
    """Build the full enhanced system prompt for immersive interactive fiction.

    Parameters
    ----------
    active_lore_entries : dict | None
        Result of ``world_info.get_active_lore()`` — ``{"always": [...], "selective": [...]}``.
    """
    characters = list(config.get("characters", []))
    protagonist = config.get("protagonist", {})
    world = config.get("worldSetting", {})
    game_rules = config.get("gameRules", "")
    status_bar = config.get("statusBar", "")
    opening = config.get("opening", "")
    writing_style = config.get("writingStyle", {})

    content_mode = writing_style.get("contentMode", "nsfw")

    # --- 核心工程修改：若为 nsfw 模式，熔断默认参数，强制拉满火力与字数上限 ---
    if content_mode == "nsfw":
        sensory_density = "high"          # 感官过载轰炸
        pacing_preference = "slow"        # 慢节奏，将性爱互动拉长拆碎
        power_intensity = "extreme"       # 性支配与反差崩溃推向极致
        prose_style = "direct"            # 直白冲击，杜绝扭捏
        target_word_count = max(writing_style.get("wordCount", 5000), 5000) # 扩充至至少5000字
    else:
        sensory_density = writing_style.get("sensoryDensity", "medium")
        pacing_preference = writing_style.get("pacingPreference", "balanced")
        power_intensity = writing_style.get("powerIntensity", "medium")
        prose_style = writing_style.get("proseStyle", "literary")
        target_word_count = writing_style.get("wordCount", 800)

    # Resolve perspective
    perspective_data = _resolve_perspective(
        characters=characters,
        protagonist=protagonist,
        world=world,
        game_rules=game_rules,
        opening=opening,
        perspective=perspective,
    )

    # Pre-render static text blocks (Using updated builder outputs)
    sensory_section = _build_sensory_section(sensory_density)
    pacing_section = _build_pacing_section(pacing_preference)
    power_section = _build_power_dynamics_section(power_intensity)
    prose_guidance = _build_prose_style_section(prose_style)
    sex_guidelines = _build_sex_scene_guidelines()
    states_block = _fmt_character_states(character_states)

    # Format active lore entries
    lore_always = (active_lore_entries or {}).get("always", [])
    lore_selective = (active_lore_entries or {}).get("selective", [])
    lore_block = _fmt_lore_entries(lore_always)
    lore_selective_block = _fmt_lore_entries(lore_selective) if lore_selective else ""

    template_name = f"{content_mode}.jinja2"
    template = _env.get_template(template_name)
    return template.render(
        work_name=work_name,
        player_role_desc=perspective_data["player_role_desc"],
        player_section_title=perspective_data["player_section_title"],
        characters_block=_fmt_characters(perspective_data["npc_characters"]),
        protagonist_block=_fmt_protagonist(perspective_data["player_char"]),
        world_block=_fmt_world(world),
        game_rules=game_rules if game_rules else "暂无特殊规则。",
        status_bar=status_bar if status_bar else "暂无状态栏。",
        initial_scene=perspective_data["initial_scene"],
        tail_instruction=perspective_data["tail_instruction"],
        states_block=states_block,
        sensory_section=sensory_section,
        pacing_section=pacing_section,
        power_section=power_section,
        lore_block=lore_block,
        lore_selective_block=lore_selective_block,
        prose_guidance=prose_guidance,
        sex_guidelines=sex_guidelines,
        target_word_count=target_word_count,
    )


# ---------------------------------------------------------------------------
#  Character state parsing (Optimized for clean KV output)
# ---------------------------------------------------------------------------

def parse_character_states(content: str) -> dict | None:
    """Parse character states from the AI response status bar section.

    Supports two formats:

    1. Multi-character (new):
        【角色状态栏】

        何乃慧
        服装：水手服短裙白丝
        表情：羞涩脸红
        好感度：55（+5）

        阿龙
        服装：黑色紧身T恤
        肉棒状态：坚硬如铁

    2. Single-character (legacy):
        【角色状态栏】
        伴侣状态：紧张的女友关系
        好感度：45 (+5)

    Returns a dict like {"何乃慧": {"服装": "水手服", "好感度": 55}, "阿龙": {...}} or None.
    """
    marker = "【角色状态栏】"
    idx = content.find(marker)
    if idx == -1:
        return None

    # Extract from marker to the next 【 marker or end of string
    rest = content[idx + len(marker):]
    next_marker = rest.find("【")
    section = rest[:next_marker] if next_marker != -1 else rest
    section = section.strip()
    if not section:
        return None

    # Detect format: multi-character has role-name headers (lines without colon)
    lines = section.split("\n")
    has_role_headers = any(
        line.strip() and "：" not in line and ":" not in line and len(line.strip()) <= 20
        for line in lines
    )

    if has_role_headers:
        return _parse_multi_character_states(lines)
    else:
        return _parse_legacy_character_states(section)


def _parse_multi_character_states(lines: list) -> dict | None:
    """Parse multi-character STATUS format with role name headers."""
    result = {}
    current_char = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is a role name header (short line without colon)
        if ("：" not in stripped and ":" not in stripped and len(stripped) <= 20):
            # Could be a character name header
            current_char = stripped
            if current_char not in result:
                result[current_char] = {}
            continue

        # Field line: "字段名：值" or "字段名: 值"
        field_match = re.match(r"^([^：:]+)[：:]\s*(.+)$", stripped)
        if field_match and current_char:
            key = field_match.group(1).strip()
            raw_value = field_match.group(2).strip()

            # Try numeric extraction: "55（+5）" or "55 (+5)" or "45"
            num_match = re.match(r"^(\d+)\s*(?:[（(]\s*([+-]?\d+)\s*[）)])?", raw_value)
            if num_match:
                value = int(num_match.group(1))
                delta = int(num_match.group(2)) if num_match.group(2) else 0
                result[current_char][key] = value
            else:
                # Text value
                result[current_char][key] = raw_value

    return result if result else None


def _parse_legacy_character_states(section: str) -> dict | None:
    """Parse legacy single-character STATUS format (backward compatible)."""
    partner_match = re.search(r"伴侣状态[：:]\s*(.+?)(?:\n|$)", section)
    partner_name = partner_match.group(1).strip() if partner_match else "未知"

    result = {}
    for m in re.finditer(
        r"([一-龥\w]+)[：:]\s*([+-]?\d+)\s*(?:\(当前\s*(\d+)\))?",
        section,
    ):
        attr_name = m.group(1).strip()
        if attr_name in ("伴侣状态",):
            continue
        value = int(m.group(3)) if m.group(3) else int(m.group(2))
        result.setdefault(partner_name, {})[attr_name] = value

    if not result:
        for m in re.finditer(
            r"([一-龥\w]+)([+-]\d+)", section
        ):
            attr_name = m.group(1).strip()
            value = int(m.group(2))
            result.setdefault(partner_name, {})[attr_name] = value

    return result if result else None