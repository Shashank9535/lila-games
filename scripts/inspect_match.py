#!/usr/bin/env python3
"""Load, sort, and summarize one selected LILA BLACK match for inspection."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.loader import default_dataset_root, load_events
from data_pipeline.processor import process_match_events


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match_id", help="Match UUID, with or without the .nakama-0 suffix")
    parser.add_argument("--dataset", type=Path, default=default_dataset_root())
    parser.add_argument("--limit", type=int, default=10, help="Number of sorted events to print")
    args = parser.parse_args()

    selected = load_events(args.dataset, [args.match_id])
    processed = process_match_events(selected)
    summary = {
        "match_id": selected[0]["match_id"],
        "map_id": selected[0]["map_id"],
        "event_count": len(processed["events"]),
        "duplicate_count": processed["duplicate_count"],
        "timestamp_inversions": processed["timestamp_inversions"],
        "min_timestamp_ms": processed["min_timestamp_ms"],
        "event_counts": processed["event_counts"],
        "sample_events": processed["events"][: args.limit],
    }
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
