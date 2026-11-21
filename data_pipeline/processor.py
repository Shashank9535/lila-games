"""Classification and non-destructive event processing for playback."""

from __future__ import annotations

from collections import Counter
import re
from typing import Any, Iterable


EVENT_TYPES = frozenset(
    {"Position", "BotPosition", "Loot", "BotKill", "BotKilled", "KilledByStorm", "Kill", "Killed"}
)
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
NUMERIC_ID_RE = re.compile(r"^\d+$")


def classify_player(player_id: object) -> str:
    """Classify only by the audited UUID/numeric-ID rule."""
    value = "" if player_id is None else str(player_id)
    if UUID_RE.fullmatch(value):
        return "human"
    if NUMERIC_ID_RE.fullmatch(value):
        return "bot"
    return "ambiguous"


def decode_event(event: object) -> str | None:
    """Decode a raw Parquet event value without changing the original value."""
    if event is None:
        return None
    if isinstance(event, bytes):
        return event.decode("utf-8", errors="replace")
    return str(event)


def _event_identity(event: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    """A deterministic identity for reporting exact duplicate source rows."""
    return tuple(sorted((key, repr(value)) for key, value in event.items() if key not in {"event_name", "relative_t_ms"}))


def process_match_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Sort one match for playback while retaining every supplied event.

    Input events must carry ``timestamp_ms`` as the raw integer timestamp. The
    returned ``relative_t_ms`` is a playback offset, not verified wall-clock
    or match-elapsed time.
    """
    original = [dict(event) for event in events]
    if not original:
        return {"events": [], "duplicate_count": 0, "timestamp_inversions": 0, "min_timestamp_ms": None}

    match_ids = {event.get("match_id") for event in original}
    if len(match_ids) != 1:
        raise ValueError("process_match_events expects events from exactly one match")
    if any(not isinstance(event.get("timestamp_ms"), int) for event in original):
        raise ValueError("each event must include integer timestamp_ms")

    inversions = sum(
        current["timestamp_ms"] < previous["timestamp_ms"]
        for previous, current in zip(original, original[1:])
    )
    seen: set[tuple[tuple[str, str], ...]] = set()
    duplicate_count = 0
    for event in original:
        identity = _event_identity(event)
        if identity in seen:
            duplicate_count += 1
        seen.add(identity)

    min_timestamp_ms = min(event["timestamp_ms"] for event in original)
    processed = sorted(original, key=lambda event: event["timestamp_ms"])
    for event in processed:
        event.setdefault("event_name", decode_event(event.get("event")))
        event["player_class"] = classify_player(event.get("user_id"))
        event["relative_t_ms"] = event["timestamp_ms"] - min_timestamp_ms

    return {
        "events": processed,
        "duplicate_count": duplicate_count,
        "timestamp_inversions": inversions,
        "min_timestamp_ms": min_timestamp_ms,
        "event_counts": dict(Counter(event["event_name"] for event in processed)),
    }


def filter_events(
    events: Iterable[dict[str, Any]], *, event_types: set[str] | None = None, player_id: str | None = None
) -> list[dict[str, Any]]:
    """Filter already-processed events for a future UI without mutating them."""
    return [
        event
        for event in events
        if (event_types is None or event.get("event_name") in event_types)
        and (player_id is None or event.get("user_id") == player_id)
    ]
