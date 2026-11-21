"""Shared UI constants and small presentation helpers."""

EVENT_STYLE = {
    "Loot": {"color": "#f5c542", "symbol": "diamond", "label": "Loot"},
    "BotKill": {"color": "#ff8c42", "symbol": "x", "label": "Bot kill"},
    "BotKilled": {"color": "#ff5a5f", "symbol": "x-thin", "label": "Killed by bot"},
    "Kill": {"color": "#ff5a5f", "symbol": "cross", "label": "Human kill"},
    "Killed": {"color": "#ff2d55", "symbol": "cross-thin", "label": "Human death"},
    "KilledByStorm": {"color": "#a78bfa", "symbol": "triangle-down", "label": "Storm death"},
}
HUMAN_COLOR = "#3dd6d0"
BOT_COLOR = "#7d8ca3"
SELECTED_COLOR = "#ffffff"


def format_relative_time(milliseconds: int) -> str:
    """Format a relative playback offset; this is deliberately not wall-clock time."""
    total_seconds, millis = divmod(max(0, int(milliseconds)), 1000)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}.{millis:03d}"
