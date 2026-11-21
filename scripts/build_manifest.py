#!/usr/bin/env python3
"""Build a match-level CSV index without modifying raw telemetry files."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data_pipeline.loader import default_dataset_root, iter_events
from data_pipeline.manifest import build_match_manifest, write_manifest_csv


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=default_dataset_root())
    parser.add_argument("--output", type=Path, default=Path("outputs/match_manifest.csv"))
    args = parser.parse_args()

    manifest = build_match_manifest(iter_events(args.dataset))
    write_manifest_csv(manifest, args.output)
    print(f"Wrote {len(manifest)} matches to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
