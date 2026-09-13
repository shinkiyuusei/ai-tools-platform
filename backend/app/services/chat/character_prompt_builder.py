"""Build the minimal context prompt for a character card."""


def build_character_system_prompt(persona_content: str) -> str:
    """Expose card data only; behavioral instructions come from prompt presets."""
    persona_content = str(persona_content or "").strip()
    return f"# 角色卡\n\n{persona_content}" if persona_content else ""
