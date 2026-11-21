# Architecture

The Streamlit application reads `outputs/match_manifest.csv` once (cached) to
populate map/date/match controls. It loads only the selected match through
`data_pipeline.loader.load_events`, then passes those raw-preserved rows through
`process_match_events` for sorting, duplicate/inversion reporting, event
decoding, player classification, and match-relative time.

`coordinate_mapper.map_world_position` maps world `x,z` into the documented
logical 1024×1024 canvas. The UI projects those logical pixels onto each source
minimap's native image dimensions only for display. This is an independent-axis
projection, not evidence of landmark calibration, so the UI exposes that limit.

Plotly renders movement as WebGL line trails and non-movement events as markers.
The timeline filters already-loaded selected-match events by `relative_t_ms`;
it never claims timestamps are wall-clock time. Heatmaps use only event rows
with their own recorded coordinates. Streamlit caches the manifest and each
selected match, preventing scans of all Parquet files during normal filtering.

For deployment, do not commit raw telemetry. Package only a compact authorized
demo dataset, or store approved Parquet files in private object storage and set
the dataset location through deployment configuration. The public deployment
cannot function until an authorized dataset delivery mechanism is provisioned.
