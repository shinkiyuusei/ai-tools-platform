"""Shared writingStyle defaults and normalization — single source of truth."""

DEFAULT_WRITING_STYLE = {
    "contentMode": "nsfw",
    "sensoryDensity": "high",
    "pacingPreference": "slow",
    "powerIntensity": "extreme",
    "proseStyle": "direct",
    "wordCount": 1500,
}

# Default STATUS schemas for immersive character state tracking
DEFAULT_NSFW_STATUS_SCHEMA = [
    {"key": "服装", "label": "服装", "type": "text"},
    {"key": "表情", "label": "表情", "type": "text"},
    {"key": "想法", "label": "想法", "type": "text"},
    {"key": "乳头状态", "label": "乳头状态", "type": "text"},
    {"key": "嫩屄状态", "label": "嫩屄状态", "type": "text"},
    {"key": "嘴穴敏感度", "label": "嘴穴敏感度", "type": "number"},
    {"key": "乳房敏感度", "label": "乳房敏感度", "type": "number"},
    {"key": "嫩屄敏感度", "label": "嫩屄敏感度", "type": "number"},
    {"key": "屁眼敏感度", "label": "屁眼敏感度", "type": "number"},
    {"key": "骚臀敏感度", "label": "骚臀敏感度", "type": "number"},
    {"key": "大腿敏感度", "label": "大腿敏感度", "type": "number"},
]

DEFAULT_MALE_NSFW_STATUS_SCHEMA = [
    {"key": "服装", "label": "服装", "type": "text"},
    {"key": "表情", "label": "表情", "type": "text"},
    {"key": "想法", "label": "想法", "type": "text"},
    {"key": "肉棒状态", "label": "肉棒状态", "type": "text"},
]

DEFAULT_NORMAL_STATUS_SCHEMA = [
    {"key": "服装", "label": "服装", "type": "text"},
    {"key": "表情", "label": "表情", "type": "text"},
    {"key": "想法", "label": "想法", "type": "text"},
    {"key": "好感度", "label": "好感度", "type": "number"},
]


def normalize_writing_style(ws: dict | None = None) -> dict:
    """Apply defaults to a writingStyle dict, returning a full 6-key dict."""
    if not ws:
        ws = {}
    return {
        "contentMode": ws.get("contentMode", DEFAULT_WRITING_STYLE["contentMode"]),
        "sensoryDensity": ws.get("sensoryDensity", DEFAULT_WRITING_STYLE["sensoryDensity"]),
        "pacingPreference": ws.get("pacingPreference", DEFAULT_WRITING_STYLE["pacingPreference"]),
        "powerIntensity": ws.get("powerIntensity", DEFAULT_WRITING_STYLE["powerIntensity"]),
        "proseStyle": ws.get("proseStyle", DEFAULT_WRITING_STYLE["proseStyle"]),
        "wordCount": ws.get("wordCount", DEFAULT_WRITING_STYLE["wordCount"]),
    }


def resolve_status_schema(content_mode: str, custom_schema: list | None = None,
                         gender: str = "") -> list:
    """Resolve the effective status schema for a character.

    Priority: custom_schema > gender-matched default > content-mode default.

    For NSFW mode, male characters get a 4-field schema (服装/表情/想法/肉棒状态)
    while female characters get the full 11-field schema.
    """
    if custom_schema and isinstance(custom_schema, list) and len(custom_schema) > 0:
        return custom_schema
    if content_mode == "nsfw":
        is_male = gender and "男" in str(gender)
        return DEFAULT_MALE_NSFW_STATUS_SCHEMA if is_male else DEFAULT_NSFW_STATUS_SCHEMA
    return DEFAULT_NORMAL_STATUS_SCHEMA


def resolve_work_status_schemas(content_mode: str, characters: list,
                                protagonist: dict) -> dict:
    """Build per-character status schemas for a work card.

    Returns a dict mapping character name → list of schema fields.
    Characters with "男" in their gender get the male schema, others get female.
    Falls back to a default single-character schema when no structured characters
    are defined (e.g., custom system prompt cards).
    """
    schemas = {}
    # Protagonist
    pname = (protagonist.get("name") or "").strip()
    pgender = protagonist.get("gender", "")
    if pname:
        schemas[pname] = resolve_status_schema(content_mode, gender=pgender)
    # NPCs
    for c in characters:
        cname = (c.get("name") or "").strip()
        cgender = c.get("gender", "")
        if cname and cname not in schemas:
            schemas[cname] = resolve_status_schema(content_mode, gender=cgender)

    # Fallback: if no characters are defined (custom prompt cards), use a
    # default single-character schema so the StatusPanel always renders.
    if not schemas:
        schemas["主角"] = resolve_status_schema(content_mode, gender="女")

    return schemas
