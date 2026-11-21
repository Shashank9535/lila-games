# LILA BLACK gameplay dataset audit

Audit date: 2026-11-22. Source examined: the supplied `player_data.zip`, extracted into the workspace only. The original archive was not modified.

## 1. Dataset overview

**Verified**

- The ZIP is 27,247,847 bytes. Its extracted contents are 32,835,876 bytes.
- There are 1,243 telemetry files, one README, three minimap images, and one `.DS_Store` file (1,248 files total).
- All 1,243 `.nakama-0` files have Parquet `PAR1` magic at both the beginning and end, and all decode successfully as Parquet. The unusual suffix is therefore a naming convention, not a different format.
- There are 89,104 event rows, 339 unique player IDs, and 796 unique match IDs. These agree with the README except that its event total is rounded to “~89,000.”
- Dates represented by folders: February 10–14, 2026. February 14 has 79 files and is marked partial in the README.

| Folder | Files | Telemetry bytes |
|---|---:|---:|
| February_10 | 437 | 2,991,430 |
| February_11 | 293 | 1,992,563 |
| February_12 | 268 | 1,783,860 |
| February_13 | 166 | 1,103,813 |
| February_14 | 79 | 499,545 |

Maps represented in rows are AmbroseValley (61,013), Lockdown (21,238), and GrandRift (6,853).

## 2. Schema and records

**Verified:** every file has the same required, uncompressed Parquet schema:

| Column | Physical/logical type | Observed nulls |
|---|---|---:|
| `user_id` | BYTE_ARRAY / UTF8 | 0 |
| `match_id` | BYTE_ARRAY / UTF8 | 0 |
| `map_id` | BYTE_ARRAY / UTF8 | 0 |
| `x`, `y`, `z` | FLOAT (float32) | 0 each |
| `ts` | INT64 / TIMESTAMP_MILLIS | 0 |
| `event` | BYTE_ARRAY | 0 |

`event` is stored as raw bytes and decodes as UTF-8. Example decoded telemetry row:

```text
user_id  0019c582-574d-4a53-9f77-554519b75b4c
match_id 1298e3e2-2776-4038-ba9b-72808b041561.nakama-0
map_id   AmbroseValley
x,y,z    -315.35388, 125.67549, -2.59261
ts       1970-01-21T11:52:34.537Z (raw: 1,770,681,535 ms)
event    Position
```

## 3. Event breakdown

| Event | Rows |
|---|---:|
| Position | 51,347 |
| BotPosition | 21,712 |
| Loot | 12,885 |
| BotKill | 2,415 |
| BotKilled | 700 |
| KilledByStorm | 39 |
| Kill | 3 |
| Killed | 3 |

Position events total 73,059 rows (82.0% of all events). All eight event names documented in the README appear; no additional decoded event types were found.

## 4. Human and bot identification

**Verified:** classifying IDs exactly as the README specifies yields 245 unique UUID-form human IDs and 94 unique all-numeric bot IDs (339 total). There are no ambiguous IDs.

The rule is consistent in the data:

- Every file name parsed as `{user_id}_{match_uuid}.nakama-0`.
- Each row’s `user_id` matched its filename’s ID.
- Each row’s `match_id` matched the filename match UUID plus `.nakama-0`.
- UUID IDs account for 66,161 rows; numeric IDs account for 22,943 rows.

There are no unexpected player-ID forms. Event-to-class behavior is also consistent with the README’s broad description: `Position`, `Loot`, `Kill`, `Killed`, and `KilledByStorm` occur on UUID IDs; `BotPosition` occurs on numeric IDs. `BotKill` and `BotKilled` occur on UUID IDs, which matches their descriptions as human-facing bot combat outcomes.

## 5. Coordinate mapping and minimaps

**Verified from README:** use `x` and `z` for 2D placement; `y` is elevation. The documented configurations are:

| Map | World origin (x,z) | Scale |
|---|---:|---:|
| AmbroseValley | (-370, -473) | 900 |
| GrandRift | (-290, -290) | 581 |
| Lockdown | (-500, -500) | 1,000 |

For the README’s 1,024-pixel rendering coordinate system: subtract the map origin from `x` and `z`, divide each result by scale to get `u` and `v`, multiply `u` by 1,024 for horizontal pixel position, and multiply `(1 - v)` by 1,024 for vertical pixel position. The latter inversion is required because world Z increases upward while image pixel Y increases downward.

Validation examples using observed records (values rounded to two pixels):

| Map | Actual x,z | README-formula pixel x,y |
|---|---:|---:|
| AmbroseValley | -315.35388, -2.59261 | 62.18, 488.78 |
| GrandRift | -223.18521, 42.54266 | 117.76, 437.90 |
| Lockdown | -346.56146, 132.77669 | 157.12, 376.04 |

**Verified bounds check:** no row is outside the README’s inclusive world extent `[origin_x, origin_x + scale] × [origin_z, origin_z + scale]`.

| Map | Observed x range | Observed y range | Observed z range |
|---|---:|---:|---:|
| AmbroseValley | -324.967 to 301.787 | 100.000 to 162.666 | -380.007 to 360.758 |
| GrandRift | -225.904 to 256.616 | 8.139 to 46.856 | -194.005 to 170.113 |
| Lockdown | -406.630 to 348.356 | 32.584 to 70.554 | -285.105 to 329.238 |

**Important discrepancy requiring human verification:** the README says all supplied minimap images are 1,024×1,024. The actual assets are valid images but have different source dimensions: AmbroseValley PNG 4,320×4,320; GrandRift PNG 2,160×2,158; Lockdown JPEG 9,000×9,000. The documented formula is valid for a 1,024×1,024 display canvas. It must not be applied directly as raw-image pixels unless product/design confirms that the assets are first rescaled/cropped to that canvas. If the raw images themselves are confirmed to be full-map, aligned images, the corresponding mathematical scaling would use their actual width/height in place of 1,024; that is an inference, not a dataset-provided rule.

## 6. Timestamps and match reconstruction

**Verified:** `ts` has Parquet logical type `TIMESTAMP_MILLIS`. Its raw values span 1,770,681,535 to 1,771,081,300 milliseconds and render as 1970-01-21 11:51:21.535Z through 11:58:01.300Z when interpreted as Unix-epoch milliseconds.

These are not wall-clock telemetry times for February 10–14, 2026. They are duration/monotonic-style values encoded with the timestamp logical type. However, they also do **not** reset to zero per match: the scan found values across a narrow shared 6m39.765s range. The README’s statement that they are match-context elapsed times is directionally useful for ordering, but the exact origin/clock semantics need telemetry-owner confirmation.

Files are almost completely chronological in on-disk row order: 1,240 files are nondecreasing, while 3 files contain one timestamp inversion each (3 inversions total). Always sort the merged rows by `ts` before reconstructing a match timeline.

To reconstruct a match, union all files sharing `match_id`, then sort their events by `ts`. The dataset has one map per match (no multi-map match IDs). Per-match rows: minimum 2, median 85, p95 271, maximum 1,216. The largest match is `d0a38c30-d476-4305-857d-ece9e65f72e6.nakama-0` with 1,216 rows, 15 player files, and Lockdown as its sole map.

For consecutive movement samples within a player file, observed positive intervals are 4 ms (min), 5 ms (median), 10 ms (p95), 25 ms (p99), and 518 ms (max). No interval exceeded 10 seconds. Sampling is therefore high-frequency but not perfectly fixed-rate; the occasional 518 ms gap should be treated as a discontinuity when drawing trails.

## 7. Data-quality findings

**Verified findings:**

- 1,505 globally exact duplicate rows exist. They were counted, not removed. Deduplication needs an explicit product decision because duplicates may be source retransmissions or semantically meaningful repeated samples.
- 3 timestamp order inversions exist in 3 player files.
- Zero schema/read errors, null fields, malformed telemetry filenames, filename/field identity mismatches, ambiguous IDs, multi-map matches, or out-of-bounds x/z positions were found.
- The minimap dimension statement in the README conflicts with the image files (described above).
- `y` has map-specific elevation ranges and should not be treated as 2D vertical image position.

## 8. Performance assessment

The extracted telemetry itself is 8.37 MB (32.84 MB including large minimap assets); 89,104 rows is small enough to load into memory for offline analysis or a single selected day/match. An interactive client should still avoid eagerly decoding every player file at startup, especially if the production dataset will grow.

Recommended baseline:

1. Build a file manifest/index keyed by `match_id`, `map_id`, date folder, player ID, player class, row count, and timestamp min/max.
2. Convert or query the Parquet files as a partitioned event dataset by date/map/match. Preserve original rows and the raw `event` bytes in the canonical layer; expose a decoded event string in a derived layer.
3. Precompute per-match timeline indexes and multiple-resolution movement tracks (for example, full, 50-ms, and 250-ms buckets). Keep discrete combat/loot/death events at full fidelity.
4. Cache requested match data and rendered map tiles/client overlays, not all raw movement points. Sort by timestamp at read time or during preprocessing, and flag—not silently repair—the three known ordering inversions.
5. Store map calibration separately from imagery. Do not hard-code a 1,024 source-image assumption until the asset discrepancy is resolved.

## 9. Unanswered questions / assumptions

- **Needs human verification:** What is the actual origin and intended unit of `ts`? It is timestamp-ms in Parquet and orderable, but neither February wall-clock time nor clearly reset match elapsed time.
- **Needs human verification:** Are minimap source assets supposed to be resized/cropped to a 1,024×1,024 logical canvas? GrandRift’s source is also slightly non-square.
- **Needs product/data-owner decision:** Should the 1,505 exact duplicate rows be retained, visually collapsed, or deduplicated in derived views?
- **Assumption (explicit):** The README’s origin and scale values are the intended world extents; the audit only verified that observed coordinates fit them, not visual landmark alignment.

## Reproducibility

The audit script is `scripts/audit_dataset.py`. On a standard Python installation:

```powershell
py -3.12 -m pip install pyarrow Pillow
py -3.12 scripts/audit_dataset.py --dataset work/player_data --json outputs/audit_stats.json
```

This workstation’s application-control policy blocks PyArrow’s native Parquet DLL, so the verification run used the included pure-JavaScript fallback (`scripts/audit_dataset_fallback.js`) with a compatible Parquet reader. That environmental limitation did not affect the source dataset and is documented here so it is reproducible rather than hidden.
