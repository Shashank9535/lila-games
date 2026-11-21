"""LILA BLACK Player Journey Explorer — internal level-design analytics."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

from data_pipeline.coordinate_mapper import map_world_position
from data_pipeline.loader import default_dataset_root, load_events
from data_pipeline.processor import process_match_events
from ui.heatmaps import build_heatmap
from ui.landing import render_landing
from ui.map_view import build_journey_map, minimap_path
from ui.metrics import render_metrics
from ui.sidebar import render_sidebar
from ui.timeline import render_timeline


ROOT = Path(__file__).parent
MANIFEST_PATH = ROOT / "outputs" / "match_manifest.csv"


@st.cache_data(show_spinner=False)
def load_manifest() -> pd.DataFrame:
    return pd.read_csv(MANIFEST_PATH, dtype={"match_id": str})


@st.cache_data(show_spinner="Loading selected match telemetry…")
def load_processed_match(dataset_root: str, match_id: str) -> pd.DataFrame:
    result = process_match_events(load_events(dataset_root, [match_id]))
    frame = pd.DataFrame(result["events"])
    if frame.empty:
        return frame
    coordinates = frame.apply(lambda row: map_world_position(row["map_id"], row["x"], row["z"]), axis=1)
    frame["pixel_x"] = [value["pixel_x"] for value in coordinates]
    frame["pixel_y"] = [value["pixel_y"] for value in coordinates]
    frame["in_bounds"] = [value["in_bounds"] for value in coordinates]
    frame.attrs["duplicate_count"] = result["duplicate_count"]
    frame.attrs["timestamp_inversions"] = result["timestamp_inversions"]
    return frame


def render_dashboard(dataset_root: Path) -> None:
    if st.sidebar.button("← Back to overview"):
        st.session_state["view"] = "landing"
        st.query_params.clear()
        st.rerun()
    st.title("Player Journey Explorer")
    st.caption("LILA BLACK gameplay telemetry • Level-design analysis • Relative playback time")
    manifest = load_manifest()
    controls = render_sidebar(st, manifest)
    try:
        events = load_processed_match(str(dataset_root), str(controls["match_id"]))
    except Exception as exc:
        st.error(f"Could not load the selected match: {exc}")
        st.info("This app requires PyArrow with working Parquet support in the running environment.")
        return
    if events.empty:
        st.warning("The selected match contains no events.")
        return

    player_options = ["All players"] + sorted(events["user_id"].unique().tolist())
    selected_player = st.sidebar.selectbox("Highlight player", player_options)
    filtered = events.copy()
    if controls["player_mode"] == "Humans":
        filtered = filtered[filtered["player_class"] == "human"]
    elif controls["player_mode"] == "Bots":
        filtered = filtered[filtered["player_class"] == "bot"]
    if selected_player != "All players":
        filtered = filtered[filtered["user_id"] == selected_player]
    filtered = filtered[filtered["event_name"].isin(controls["event_types"])]
    if filtered.empty:
        st.warning("No events match the current player and event filters.")
        return

    render_metrics(st, filtered)
    current_time = render_timeline(st, int(events["relative_t_ms"].max()))
    playback_events = filtered[filtered["relative_t_ms"] <= current_time]
    if playback_events.empty:
        st.info("Move the timeline forward to reveal the first event.")
    else:
        st.subheader("Player journeys")
        image_path = minimap_path(dataset_root, str(controls["map_id"]))
        st.plotly_chart(build_journey_map(playback_events, image_path, None if selected_player == "All players" else selected_player), use_container_width=True)
        dimensions = Image.open(image_path).size
        st.caption(f"Logical 1024×1024 mapping is projected onto the source image ({dimensions[0]}×{dimensions[1]}). Source-image landmark alignment is not independently verified.")
        st.caption(f"Raw rows retained: {len(events):,}; exact duplicates in selected match: {events.attrs.get('duplicate_count', 0)}; source-order timestamp inversions: {events.attrs.get('timestamp_inversions', 0)}.")

    st.subheader("Heatmap analysis")
    heatmap_kind = st.radio("Heatmap", ["Movement", "Kill-related", "Death-related"], horizontal=True)
    figure, message = build_heatmap(filtered, heatmap_kind)
    if figure:
        st.plotly_chart(figure, use_container_width=True)
    else:
        st.info(message)
    st.caption("Kill/death heatmaps show only coordinates recorded on their corresponding event rows; they do not infer actor/victim relationships or locations.")

    with st.expander("Selected-match records"):
        st.dataframe(filtered[["user_id", "player_class", "event_name", "relative_t_ms", "x", "y", "z", "in_bounds"]], use_container_width=True)


def main() -> None:
    st.set_page_config(page_title="Player Journey Explorer", page_icon="◈", layout="wide")
    st.markdown("""<style>.stApp {background:#0b1220;} [data-testid='stMetric'] {background:#111827; padding:12px; border-radius:8px;}</style>""", unsafe_allow_html=True)
    if not MANIFEST_PATH.exists():
        st.error("Match manifest is missing. Run scripts/build_manifest.py first.")
        return
    dataset_root = default_dataset_root()
    if not dataset_root.exists():
        st.error("No local dataset found. Configure data/ or work/player_data before running the app.")
        return

    # Routing is URL-led rather than session-led: a clean root URL must always
    # show the landing page, even after a visitor previously explored a match.
    requested_view = st.query_params.get("view")
    if requested_view != "dashboard":
        render_landing(dataset_root)
    else:
        render_dashboard(dataset_root)


if __name__ == "__main__":
    main()
