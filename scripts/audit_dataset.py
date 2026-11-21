#!/usr/bin/env python3
"""Audit the LILA BLACK player-journey dataset without modifying it.

Usage (from the repository root):
    py -3.12 scripts/audit_dataset.py --dataset work/player_data --json outputs/audit_stats.json

Dependencies: pyarrow; Pillow is optional (only used for minimap dimensions).
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

try:
    from PIL import Image
except ImportError:  # pragma: no cover - documented graceful fallback
    Image = None


UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
NUMERIC_RE = re.compile(r"^\d+$")
MAPS = {
    "AmbroseValley": {"scale": 900.0, "origin_x": -370.0, "origin_z": -473.0},
    "GrandRift": {"scale": 581.0, "origin_x": -290.0, "origin_z": -290.0},
    "Lockdown": {"scale": 1000.0, "origin_x": -500.0, "origin_z": -500.0},
}
EXPECTED_COLUMNS = ("user_id", "match_id", "map_id", "x", "y", "z", "ts", "event")


def event_text(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value) if value is not None else "<null>"


def classify_player(value: Any) -> str:
    text = str(value) if value is not None else ""
    if UUID_RE.fullmatch(text):
        return "human_uuid"
    if NUMERIC_RE.fullmatch(text):
        return "bot_numeric"
    return "ambiguous"


def quantiles(values: list[int | float]) -> dict[str, float] | None:
    if not values:
        return None
    ordered = sorted(values)

    def q(p: float) -> float:
        return float(ordered[round((len(ordered) - 1) * p)])

    return {"min": float(ordered[0]), "p50": q(0.50), "p95": q(0.95), "p99": q(0.99), "max": float(ordered[-1])}


def json_default(value: Any) -> str:
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return str(value)


def filename_ids(path: Path) -> tuple[str | None, str | None]:
    """Return filename user ID and match UUID, leaving malformed names visible."""
    suffix = ".nakama-0"
    if not path.name.endswith(suffix):
        return None, None
    stem = path.name[: -len(suffix)]
    if "_" not in stem:
        return None, None
    user, match = stem.rsplit("_", 1)
    return user, match


def minimap_details(dataset: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for path in sorted((dataset / "minimaps").glob("*")) if (dataset / "minimaps").exists() else []:
        item: dict[str, Any] = {"path": str(path), "bytes": path.stat().st_size}
        with path.open("rb") as handle:
            item["signature_hex"] = handle.read(12).hex()
        if Image:
            with Image.open(path) as image:
                item.update({"format": image.format, "dimensions": list(image.size), "mode": image.mode})
        result[path.name] = item
    return result


def audit(dataset: Path) -> dict[str, Any]:
    all_files = sorted(p for p in dataset.rglob("*") if p.is_file())
    data_files = [p for p in all_files if p.suffix == ".nakama-0"]
    report: dict[str, Any] = {
        "dataset": str(dataset.resolve()),
        "files_total": len(all_files),
        "data_files": len(data_files),
        "dataset_bytes": sum(p.stat().st_size for p in all_files),
        "data_bytes": sum(p.stat().st_size for p in data_files),
        "file_extensions": dict(collections.Counter(p.suffix or "<none>" for p in all_files)),
        "read_errors": [],
        "invalid_parquet_magic": [],
        "schemas": collections.Counter(),
        "column_missing_values": collections.Counter(),
        "event_counts": collections.Counter(),
        "event_by_player_class": collections.defaultdict(collections.Counter),
        "map_counts": collections.Counter(),
        "map_coordinate_ranges": {},
        "coordinate_out_of_bounds": collections.Counter(),
        "coordinate_oob_examples": collections.defaultdict(list),
        "player_classes": collections.Counter(),
        "unique_players_by_class": {"human_uuid": set(), "bot_numeric": set(), "ambiguous": set()},
        "ambiguous_player_ids": set(),
        "filename_field_id_mismatches": [],
        "filename_field_match_mismatches": [],
        "malformed_filenames": [],
        "unique_players": set(),
        "unique_matches": set(),
        "matches": collections.defaultdict(lambda: {"files": 0, "rows": 0, "players": set(), "maps": set(), "ts_min": None, "ts_max": None}),
        "rows_total": 0,
        "rows_per_file": [],
        "duplicates_exact": 0,
        "ordered_files": 0,
        "unordered_files": 0,
        "timestamp_inversions": 0,
        "timestamp_ms_min": None,
        "timestamp_ms_max": None,
        "position_gaps_ms": [],
        "large_position_gaps_over_10s": 0,
        "example_rows": [],
    }
    duplicate_rows: set[tuple[Any, ...]] = set()
    ranges: dict[str, dict[str, list[float]]] = collections.defaultdict(
        lambda: {"x": [math.inf, -math.inf], "y": [math.inf, -math.inf], "z": [math.inf, -math.inf]}
    )

    for path in data_files:
        raw = path.read_bytes()[:4]
        if raw != b"PAR1":
            report["invalid_parquet_magic"].append(str(path))
            continue
        file_user, file_match = filename_ids(path)
        if file_user is None:
            report["malformed_filenames"].append(str(path))
        try:
            parquet = pq.ParquetFile(path)
            schema = parquet.schema_arrow
            report["schemas"][str(schema)] += 1
            report["rows_per_file"].append(parquet.metadata.num_rows)
            report["rows_total"] += parquet.metadata.num_rows
        except Exception as exc:  # report and continue: unexpected data must remain visible
            report["read_errors"].append({"path": str(path), "error": repr(exc)})
            continue

        previous_ts: int | None = None
        previous_position_ts: int | None = None
        file_ordered = True
        for batch in parquet.iter_batches(batch_size=65_536):
            data = batch.to_pydict()
            missing_columns = set(EXPECTED_COLUMNS) - set(data)
            if missing_columns:
                report["read_errors"].append({"path": str(path), "error": f"missing columns: {sorted(missing_columns)}"})
                continue
            for row in zip(*(data[column] for column in EXPECTED_COLUMNS)):
                user_id, match_id, map_id, x, y, z, timestamp, event = row
                row_key = (user_id, match_id, map_id, x, y, z, timestamp, event)
                if row_key in duplicate_rows:
                    report["duplicates_exact"] += 1
                else:
                    duplicate_rows.add(row_key)
                for column, value in zip(EXPECTED_COLUMNS, row):
                    if value is None:
                        report["column_missing_values"][column] += 1
                if user_id is not None:
                    report["unique_players"].add(str(user_id))
                if match_id is not None:
                    report["unique_matches"].add(str(match_id))
                player_kind = classify_player(user_id)
                report["player_classes"][player_kind] += 1
                report["unique_players_by_class"][player_kind].add(str(user_id))
                if player_kind == "ambiguous":
                    report["ambiguous_player_ids"].add(str(user_id))
                if file_user is not None and str(user_id) != file_user:
                    if len(report["filename_field_id_mismatches"]) < 20:
                        report["filename_field_id_mismatches"].append({"file": str(path), "filename": file_user, "field": user_id})
                expected_match = f"{file_match}.nakama-0" if file_match else None
                if expected_match and str(match_id) != expected_match:
                    if len(report["filename_field_match_mismatches"]) < 20:
                        report["filename_field_match_mismatches"].append({"file": str(path), "filename": expected_match, "field": match_id})
                event_name = event_text(event)
                report["event_counts"][event_name] += 1
                report["event_by_player_class"][player_kind][event_name] += 1
                if map_id is not None:
                    map_name = str(map_id)
                    report["map_counts"][map_name] += 1
                    for label, value in (("x", x), ("y", y), ("z", z)):
                        if value is not None:
                            ranges[map_name][label][0] = min(ranges[map_name][label][0], float(value))
                            ranges[map_name][label][1] = max(ranges[map_name][label][1], float(value))
                    config = MAPS.get(map_name)
                    if config and x is not None and z is not None:
                        is_oob = not (config["origin_x"] <= x <= config["origin_x"] + config["scale"] and config["origin_z"] <= z <= config["origin_z"] + config["scale"])
                        if is_oob:
                            report["coordinate_out_of_bounds"][map_name] += 1
                            if len(report["coordinate_oob_examples"][map_name]) < 5:
                                report["coordinate_oob_examples"][map_name].append({"x": x, "y": y, "z": z, "event": event_name, "file": str(path)})
                ts_ms = None if timestamp is None else int(timestamp.timestamp() * 1000)
                if ts_ms is not None:
                    report["timestamp_ms_min"] = ts_ms if report["timestamp_ms_min"] is None else min(report["timestamp_ms_min"], ts_ms)
                    report["timestamp_ms_max"] = ts_ms if report["timestamp_ms_max"] is None else max(report["timestamp_ms_max"], ts_ms)
                    if previous_ts is not None and ts_ms < previous_ts:
                        report["timestamp_inversions"] += 1
                        file_ordered = False
                    previous_ts = ts_ms
                    match = report["matches"][str(match_id)]
                    match["ts_min"] = ts_ms if match["ts_min"] is None else min(match["ts_min"], ts_ms)
                    match["ts_max"] = ts_ms if match["ts_max"] is None else max(match["ts_max"], ts_ms)
                    if event_name in {"Position", "BotPosition"}:
                        if previous_position_ts is not None and ts_ms >= previous_position_ts:
                            gap = ts_ms - previous_position_ts
                            report["position_gaps_ms"].append(gap)
                            if gap > 10_000:
                                report["large_position_gaps_over_10s"] += 1
                        previous_position_ts = ts_ms
                match = report["matches"][str(match_id)]
                match["rows"] += 1
                match["players"].add(str(user_id))
                match["maps"].add(str(map_id))
                if len(report["example_rows"]) < 5:
                    report["example_rows"].append(dict(zip(EXPECTED_COLUMNS, [event_text(v) if k == "event" else v for k, v in zip(EXPECTED_COLUMNS, row)])))
        report["ordered_files" if file_ordered else "unordered_files"] += 1
        if str(path):
            match_key = f"{file_match}.nakama-0" if file_match else None
            if match_key:
                report["matches"][match_key]["files"] += 1

    report["map_coordinate_ranges"] = {key: value for key, value in ranges.items()}
    report["unique_players"] = len(report["unique_players"])
    report["unique_players_by_class"] = {
        kind: len(player_ids) for kind, player_ids in report["unique_players_by_class"].items()
    }
    report["unique_matches"] = len(report["unique_matches"])
    report["ambiguous_player_ids"] = sorted(report["ambiguous_player_ids"])
    report["position_gap_ms_summary"] = quantiles(report.pop("position_gaps_ms"))
    matches = report.pop("matches")
    match_rows = {key: value["rows"] for key, value in matches.items()}
    report["matches_summary"] = {
        "count": len(matches),
        "rows_per_match": quantiles(list(match_rows.values())),
        "largest_by_rows": sorted(match_rows.items(), key=lambda item: item[1], reverse=True)[:10],
        "files_per_match": quantiles([value["files"] for value in matches.values()]),
        "players_per_match": quantiles([len(value["players"]) for value in matches.values()]),
        "multi_map_matches": {key: sorted(value["maps"]) for key, value in matches.items() if len(value["maps"]) > 1},
        "examples": {key: {"files": value["files"], "rows": value["rows"], "players": len(value["players"]), "maps": sorted(value["maps"]), "ts_min_ms": value["ts_min"], "ts_max_ms": value["ts_max"]} for key, value in list(matches.items())[:3]},
    }
    report["rows_per_file_summary"] = quantiles(report.pop("rows_per_file"))
    report["minimaps"] = minimap_details(dataset)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path("work/player_data"), help="Extracted player_data directory")
    parser.add_argument("--json", type=Path, help="Optional output path for complete machine-readable statistics")
    args = parser.parse_args()
    if not args.dataset.is_dir():
        parser.error(f"dataset directory not found: {args.dataset}")
    result = audit(args.dataset)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2, default=json_default), encoding="utf-8")
        print(f"Wrote complete JSON report: {args.json}")
    print(json.dumps(result, indent=2, default=json_default))
    return 0 if not result["read_errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
