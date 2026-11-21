"""Non-destructive Parquet loading for LILA BLACK telemetry files."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .processor import decode_event


class DatasetReadError(RuntimeError):
    """Raised when a discovered telemetry file cannot be loaded completely."""


def default_dataset_root() -> Path:
    """Prefer the requested data/ directory, then this project's audited copy."""
    return Path("data") if Path("data").is_dir() else Path("work/player_data")


def discover_files(dataset_root: Path | str, match_ids: Iterable[str] | None = None) -> list[Path]:
    """List telemetry files; filter by filename match ID without reading rows."""
    root = Path(dataset_root)
    if not root.is_dir():
        raise FileNotFoundError(f"Dataset directory does not exist: {root}")
    requested = set(match_ids or [])
    files = sorted(root.glob("February_*/*.nakama-0"))
    if not requested:
        return files

    def belongs_to_requested_match(path: Path) -> bool:
        match_id = path.name.rsplit("_", 1)[-1]
        return match_id in requested or match_id.removesuffix(".nakama-0") in requested

    selected = [path for path in files if belongs_to_requested_match(path)]
    found = {path.name.rsplit("_", 1)[-1] for path in selected}
    missing = {match_id for match_id in requested if match_id not in found and f"{match_id}.nakama-0" not in found}
    if missing:
        raise FileNotFoundError(f"No telemetry files found for match IDs: {sorted(missing)}")
    return selected


def _pyarrow_modules() -> tuple[Any, Any]:
    """Import on demand so non-I/O modules remain usable without PyArrow."""
    try:
        import pyarrow as pa
        import pyarrow.compute as pc
        import pyarrow.parquet as pq
    except ImportError as exc:  # includes unavailable native parquet support
        raise DatasetReadError("PyArrow with Parquet support is required. Install it with: pip install pyarrow") from exc
    return pa, pc, pq


def iter_events(dataset_root: Path | str | None = None, match_ids: Iterable[str] | None = None) -> Iterator[dict[str, Any]]:
    """Yield every source row, adding decoded fields while preserving raw columns.

    ``event`` remains the raw bytes from Parquet. ``event_name`` is its decoded
    view. ``timestamp_ms`` is the timezone-independent integer underlying the
    TIMESTAMP_MILLIS column. Any file read failure raises DatasetReadError.
    """
    root = Path(dataset_root) if dataset_root is not None else default_dataset_root()
    pa, pc, pq = _pyarrow_modules()
    for path in discover_files(root, match_ids):
        try:
            table = pq.read_table(path)
            if "ts" not in table.column_names or "event" not in table.column_names:
                raise DatasetReadError(f"Required columns missing from {path}")
            timestamp_values = pc.cast(table["ts"], target_type=pa.int64()).to_pylist()
            for raw_row, timestamp_ms in zip(table.to_pylist(), timestamp_values):
                row = dict(raw_row)
                row["source_file"] = str(path)
                row["date_folder"] = path.parent.name
                row["timestamp_ms"] = int(timestamp_ms)
                row["event_name"] = decode_event(row["event"])
                yield row
        except DatasetReadError:
            raise
        except Exception as exc:
            raise DatasetReadError(f"Failed to read {path}: {exc}") from exc


def load_events(dataset_root: Path | str | None = None, match_ids: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Materialize all selected events. Rows are never dropped or deduplicated."""
    return list(iter_events(dataset_root, match_ids))
