"""Match-level manifest construction and CSV serialization."""

from __future__ import annotations

from collections import Counter
import csv
import json
from pathlib import Path
from typing import Any, Iterable

from .processor import classify_player


MANIFEST_COLUMNS = (
    "match_id", "map_id", "date_folder", "date_folders", "first_date_folder", "last_date_folder",
    "event_count", "unique_player_count", "player_ids",
    "human_player_count", "bot_player_count", "ambiguous_player_count", "min_timestamp_raw_ms",
    "max_timestamp_raw_ms", "event_type_counts",
)


def build_match_manifest(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate source events into one manifest entry per match without dropping rows."""
    grouped: dict[str, dict[str, Any]] = {}
    for event in events:
        match_id = event["match_id"]
        entry = grouped.setdefault(match_id, {
            "match_id": match_id, "maps": set(), "dates": set(), "event_count": 0, "players": set(),
            "event_types": Counter(), "timestamps": [],
        })
        entry["maps"].add(event["map_id"])
        entry["dates"].add(event["date_folder"])
        entry["event_count"] += 1
        entry["players"].add(event["user_id"])
        entry["event_types"][event["event_name"]] += 1
        entry["timestamps"].append(event["timestamp_ms"])

    manifest: list[dict[str, Any]] = []
    for match_id, entry in grouped.items():
        if len(entry["maps"]) != 1:
            raise ValueError(f"Match {match_id} has multiple maps: {sorted(entry['maps'])}")
        player_classes = Counter(classify_player(player_id) for player_id in entry["players"])
        date_folders = sorted(entry["dates"])
        manifest.append({
            "match_id": match_id,
            "map_id": next(iter(entry["maps"])),
            # Keep the original required field as a first-folder compatibility
            # value while retaining every source partition separately.
            "date_folder": date_folders[0],
            "date_folders": ";".join(date_folders),
            "first_date_folder": date_folders[0],
            "last_date_folder": date_folders[-1],
            "event_count": entry["event_count"],
            "unique_player_count": len(entry["players"]),
            "player_ids": sorted(entry["players"]),
            "human_player_count": player_classes["human"],
            "bot_player_count": player_classes["bot"],
            "ambiguous_player_count": player_classes["ambiguous"],
            # Raw Parquet TIMESTAMP_MILLIS INT64 values; no datetime conversion.
            "min_timestamp_raw_ms": min(entry["timestamps"]),
            "max_timestamp_raw_ms": max(entry["timestamps"]),
            "event_type_counts": dict(sorted(entry["event_types"].items())),
        })
    return sorted(manifest, key=lambda row: row["match_id"])


def write_manifest_csv(manifest: Iterable[dict[str, Any]], output_path: Path | str) -> None:
    """Write a stable CSV; list/dict values are JSON so the manifest is lossless."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        for row in manifest:
            serialized = dict(row)
            serialized["player_ids"] = json.dumps(row["player_ids"], separators=(",", ":"))
            serialized["event_type_counts"] = json.dumps(row["event_type_counts"], sort_keys=True, separators=(",", ":"))
            writer.writerow(serialized)
