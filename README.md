# LILA BLACK Player Journey Explorer

An internal Streamlit analytics tool for Level Designers. It loads one selected
match at a time and visualizes player paths, discrete gameplay events,
match-relative playback, and recorded-coordinate heatmaps.

## Features

- Manifest-driven map, date, match, player-class, player, and event filters.
- Plotly minimap journeys: human/bot trails, player highlight, and event markers.
- Relative timeline slider with play/pause/reset controls.
- Movement, kill-related, and death-related heatmaps, only using recorded rows.
- Data-quality context: duplicates and timestamp inversions remain visible.

## Setup and local run

```powershell
py -3.12 -m pip install -r requirements.txt
py -3.12 -m unittest discover -s tests -v
py -3.12 scripts/build_manifest.py --dataset data --output outputs/match_manifest.csv
py -3.12 -m streamlit run app.py
```

This workspace keeps the audited extracted data at `work/player_data`; replace
`data` above with that path when running locally here. Raw data and ZIP files
must not be committed.

## Dataset and known limits

The app expects the audit schema (`.nakama-0` Parquet files), and preserves raw
event values. `ts` is a raw Parquet `TIMESTAMP_MILLIS` integer whose origin is
unverified; all UI time is a match-relative offset. The source minimaps have
different native dimensions and their landmark alignment is not independently
verified. See `DATA_AUDIT.md`, `ARCHITECTURE.md`, and `INSIGHTS.md`.

## Deployment

Do not deploy raw telemetry via Git. Use an approved compact demo dataset or
private object storage / mounted volume, configured outside source control. A
public URL is intentionally not claimed because no authorized hosting or data
delivery target is configured in this workspace.
