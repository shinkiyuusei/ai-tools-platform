"""Generate context-sensitive next actions for an assistant reply."""

import re


CHOICE_MARKER = "【抉择分支】"
_CHOICE_LINE = re.compile(r"^([A-D])[.、．]\s*(.+)$")


def build_choice_messages(narrative: str) -> list[dict]:
    """Ask the model for four distinct actions based only on its latest reply."""
    return [
        {
            "role": "system",
            "content": (
                "你负责为互动叙事生成下一步行动选项。必须依据给出的最新回复，"
                "不得使用固定或泛化的选项。只输出四行，不要解释、不要标题：\n"
                "A. 延续当前目标或冲突的行动\n"
                "B. 以不同策略推进的行动\n"
                "C. 探索环境、信息或关系的行动\n"
                "D. 符合角色与剧情、但出人意料的行动"
            ),
        },
        {"role": "user", "content": f"最新回复：\n{narrative.strip()}"},
    ]


def format_choice_block(content: str) -> str:
    """Return a renderable four-choice block, or an empty string when invalid."""
    choices: dict[str, str] = {}
    for line in str(content or "").replace(CHOICE_MARKER, "").splitlines():
        match = _CHOICE_LINE.match(line.strip())
        if match:
            choices.setdefault(match.group(1), f"{match.group(1)}. {match.group(2).strip()}")
    if set(choices) != {"A", "B", "C", "D"}:
        return ""
    return "\n\n" + CHOICE_MARKER + "\n" + "\n".join(choices[key] for key in "ABCD") + "\n"


def generate_choice_block(service, model: str, narrative: str) -> tuple[str, int]:
    """Use an adapter to generate choices and return ``(block, token_count)``."""
    result = service.chat_completion(
        messages=build_choice_messages(narrative),
        model=model,
        thinking_mode=False,
        temperature=0.7,
        max_tokens=500,
    )
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    tokens = int(result.get("usage", {}).get("total_tokens") or 0)
    return format_choice_block(content), tokens
