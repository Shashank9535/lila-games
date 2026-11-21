# LILA BLACK data pipeline

This package builds a non-destructive processing layer over the supplied
`.nakama-0` Parquet telemetry files. It does not alter the raw dataset.

- `loader.py` discovers telemetry files, loads all or selected matches, retains
  raw columns (`event` remains bytes and `ts` remains present), and adds
  `event_name`, integer `timestamp_ms`, source file, and date-folder metadata.
- `manifest.py` aggregates source rows into one CSV row per match.
- `processor.py` classifies players only by UUID/numeric ID, decodes events,
  reports duplicate rows and input timestamp inversions, and produces sorted
  playback events with `relative_t_ms`.
- `coordinate_mapper.py` converts world `x,z` to normalized `u,v` and the
  documented logical 1024x1024 pixel canvas. It does not modify or assume a
  size for the source minimap images.

## Commands

Install the Parquet dependency, then build the index:

```powershell
py -3.12 -m pip install pyarrow
py -3.12 scripts/build_manifest.py --dataset work/player_data --output outputs/match_manifest.csv
py -3.12 scripts/inspect_match.py d0a38c30-d476-4305-857d-ece9e65f72e6.nakama-0 --dataset work/player_data
py -3.12 -m unittest discover -s tests -v
```

`data/` is preferred automatically if supplied by a deployment. In this
workspace the audited source is `work/player_data`, so commands explicitly use
that path. The loader never silently skips files or rows: read failures raise
`DatasetReadError`.

The manifest keeps `date_folder` as its first source folder for compatibility,
and adds `date_folders`, `first_date_folder`, and `last_date_folder`. The
semicolon-delimited `date_folders` value retains all source partitions when a
match ID occurs in more than one folder.

## Time and mapping limits

`timestamp_ms` is the raw integer value of the Parquet `TIMESTAMP_MILLIS`
column. It is not converted through the computer timezone. `relative_t_ms` is
only `timestamp_ms - min(timestamp_ms)` for the selected match: it is a
playback offset, not verified real-world or elapsed-match time.

The README's logical mapping is `u=(x-origin_x)/scale`,
`v=(z-origin_z)/scale`, `pixel_x=u*1024`, and `pixel_y=(1-v)*1024`. Source
minimap dimensions are intentionally kept separate because the audit found
they are not actually 1024x1024.

The manifest calls these values `min_timestamp_raw_ms` and
`max_timestamp_raw_ms` to make clear that they are unmodified Parquet INT64
millisecond values, not Unix wall-clock seconds.
