"""Token usage tracking and daily chat stats for work / character cards."""

from datetime import date

from ..utils.mysql import execute


def add_token_usage(entity_id: int, tokens: int, entity_type: str = "work") -> None:
    """Accumulate token usage onto a card's use_count."""
    if not entity_id or not tokens:
        return
    table = "t_work_card" if entity_type == "work" else "t_character_card"
    execute(
        f"UPDATE {table} SET use_count = use_count + %s WHERE id = %s",
        (tokens, entity_id),
    )


def increment_daily_stat(card_type: str, card_id: int) -> None:
    """Increment today's chat count for the given card."""
    if not card_id:
        return
    today = date.today().isoformat()
    execute(
        "INSERT INTO t_cards_daily_stat (card_type, card_id, stat_date, chat_count) "
        "VALUES (%s, %s, %s, 1) "
        "ON DUPLICATE KEY UPDATE chat_count = chat_count + 1",
        (card_type, card_id, today),
    )
