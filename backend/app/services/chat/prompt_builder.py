"""Build minimal card context for chats.

Writing instructions are intentionally not defined by the server.  They belong
to each user's prompt preset; this module only serializes the work-card data
that a preset can use as context.
"""

import re


def _value(value, fallback="未填写") -> str:
    value = str(value or "").strip()
    return value or fallback


def _fmt_characters(characters: list) -> str:
    """Serialize NPC card data without adding role-play instructions."""
    if not characters:
        return "未填写"

    fields = (
        ("姓名", "name"),
        ("职业", "occupation"),
        ("年龄", "age"),
        ("性别", "gender"),
        ("外貌", "appearance"),
        ("性格", "personality"),
        ("语气", "speechTone"),
        ("背景", "background"),
    )
    blocks = []
    for index, character in enumerate(characters, 1):
        if not isinstance(character, dict):
            continue
        lines = [f"角色 {index}"]
        lines.extend(f"{label}：{_value(character.get(key))}" for label, key in fields)
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) or "未填写"


def _fmt_protagonist(protagonist: dict) -> str:
    protagonist = protagonist if isinstance(protagonist, dict) else {}
    return "\n".join((
        f"姓名：{_value(protagonist.get('name'))}",
        f"设定：{_value(protagonist.get('description'))}",
        f"核心动机：{_value(protagonist.get('motivation'))}",
    ))


def _fmt_world(world: dict) -> str:
    world = world if isinstance(world, dict) else {}
    fields = (
        ("世界名称", "worldName"),
        ("时代背景", "eraTech"),
        ("核心冲突", "coreConflict"),
        ("整体基调", "toneAtmosphere"),
        ("主线剧情", "mainPlot"),
        ("初始剧情", "initialState"),
    )
    return "\n".join(f"{label}：{_value(world.get(key))}" for label, key in fields)


def _fmt_character_states(states: dict) -> str:
    """Serialize persisted state as data; its output format comes from presets."""
    if not states:
        return ""
    lines = ["# 当前角色状态"]
    for name, attrs in states.items():
        if not isinstance(attrs, dict):
            continue
        lines.append(str(name))
        lines.extend(f"{key}：{value}" for key, value in attrs.items())
    return "\n".join(lines) if len(lines) > 1 else ""


def _fmt_lore_entries(entries: list) -> str:
    """Serialize active world-book entries without prescribing how to use them."""
    if not entries:
        return ""
    lines = ["# 世界书"]
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        content = str(entry.get("content") or "").strip()
        if content:
            lines.append(content)
    return "\n\n".join(lines) if len(lines) > 1 else ""


def build_enhanced_system_prompt(
    work_name: str,
    config: dict,
    perspective: dict | None = None,
    character_states: dict | None = None,
    active_lore_entries: dict | None = None,
) -> str:
    """Return the single, basic context prompt generated from a work card."""
    config = config if isinstance(config, dict) else {}
    parts = [
        "# 作品卡",
        f"作品名称：{_value(work_name)}",
        f"作者：{_value(config.get('author'))}",
        f"简介：{_value(config.get('detailedIntro'))}",
        "\n## 世界观\n" + _fmt_world(config.get("worldSetting", {})),
        "\n## 主角\n" + _fmt_protagonist(config.get("protagonist", {})),
        "\n## 角色\n" + _fmt_characters(list(config.get("characters") or [])),
    ]

    optional_sections = (
        ("作品规则", config.get("gameRules")),
        ("状态栏定义", config.get("statusBar")),
        ("开场", config.get("opening")),
    )
    for title, content in optional_sections:
        content = str(content or "").strip()
        if content:
            parts.append(f"\n## {title}\n{content}")

    if isinstance(perspective, dict) and perspective.get("name"):
        parts.append(f"\n## 当前视角\n{perspective['name']}")

    state_block = _fmt_character_states(character_states or {})
    if state_block:
        parts.append("\n" + state_block)

    lore = active_lore_entries or {}
    lore_block = _fmt_lore_entries(lore.get("always", []))
    if lore_block:
        parts.append("\n" + lore_block)
    return "\n".join(parts).strip()


def parse_character_states(content: str) -> dict | None:
    """Parse an optional status section emitted by a user-defined preset."""
    marker = re.search(r"[【\[]角色状态栏[】\]]", content or "")
    if not marker:
        return None

    result: dict[str, dict] = {}
    current_name = "当前角色"
    for raw_line in content[marker.end():].splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("【", "[")):
            break
        field = re.match(r"^([^：:]{1,40})[：:]\s*(.+)$", line)
        if field:
            key, value = field.groups()
            result.setdefault(current_name, {})[key.strip()] = value.strip()
        elif len(line) <= 40:
            current_name = line
            result.setdefault(current_name, {})
    return {name: values for name, values in result.items() if values} or None
