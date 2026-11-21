"""Sidebar controls driven from the prebuilt match manifest."""

from __future__ import annotations

import pandas as pd

from data_pipeline.processor import EVENT_TYPES


def render_sidebar(st, manifest: pd.DataFrame) -> dict[str, object]:
    st.sidebar.header("Match controls")
    maps = sorted(manifest["map_id"].dropna().unique())
    map_id = st.sidebar.selectbox("Map", maps)
    scoped = manifest[manifest["map_id"] == map_id].sort_values("match_id")
    dates = sorted({part for value in scoped["date_folders"] for part in value.split(";")})
    selected_date = st.sidebar.selectbox("Source date", ["All"] + dates)
    if selected_date != "All":
        scoped = scoped[scoped["date_folders"].str.contains(selected_date, regex=False)]
    match_id = st.sidebar.selectbox("Match", scoped["match_id"].tolist(), format_func=lambda value: value.removesuffix(".nakama-0"))
    player_mode = st.sidebar.radio("Players", ["All", "Humans", "Bots"], horizontal=True)
    events = st.sidebar.multiselect("Event types", sorted(EVENT_TYPES), default=sorted(EVENT_TYPES))
    return {"map_id": map_id, "match_id": match_id, "date": selected_date, "player_mode": player_mode, "event_types": set(events)}
