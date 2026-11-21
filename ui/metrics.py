"""Selected-match metric cards."""

from __future__ import annotations

import pandas as pd

from .components import format_relative_time


def render_metrics(st, events: pd.DataFrame) -> None:
    players = events[["user_id", "player_class"]].drop_duplicates()
    duration = int(events["relative_t_ms"].max()) if len(events) else 0
    cols = st.columns(5)
    cols[0].metric("Events", f"{len(events):,}")
    cols[1].metric("Players", len(players))
    cols[2].metric("Humans", int((players["player_class"] == "human").sum()))
    cols[3].metric("Bots", int((players["player_class"] == "bot").sum()))
    cols[4].metric("Relative range", format_relative_time(duration))
    st.caption("Event distribution")
    st.bar_chart(events["event_name"].value_counts())
