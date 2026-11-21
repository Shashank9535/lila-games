"""Heatmap selectors built only from events with recorded coordinates."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def build_heatmap(events: pd.DataFrame, kind: str):
    if kind == "Movement":
        data = events[events["event_name"].isin(["Position", "BotPosition"])]
    elif kind == "Kill-related":
        data = events[events["event_name"].isin(["Kill", "BotKill"])]
    else:
        data = events[events["event_name"].isin(["Killed", "BotKilled", "KilledByStorm"])]
    if data.empty:
        return None, "No selected events have recorded coordinates."
    figure = px.density_heatmap(data, x="pixel_x", y="pixel_y", nbinsx=35, nbinsy=35, color_continuous_scale="Turbo")
    figure.update_yaxes(autorange="reversed", visible=False).update_xaxes(visible=False)
    figure.update_layout(template="plotly_dark", height=420, margin=dict(l=0, r=0, t=30, b=0))
    return figure, None
