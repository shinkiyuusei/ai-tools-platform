"""Shared writingStyle defaults and normalization — single source of truth."""

DEFAULT_WRITING_STYLE = {
    "contentMode": "nsfw",
    "sensoryDensity": "high",
    "pacingPreference": "slow",
    "powerIntensity": "extreme",
    "proseStyle": "direct",
    "wordCount": 1500,
}


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
