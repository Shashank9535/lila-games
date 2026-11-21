"""Plotly minimap overlays using the calibrated logical coordinate space."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from PIL import Image

from .components import BOT_COLOR, EVENT_STYLE, HUMAN_COLOR, SELECTED_COLOR


def minimap_path(dataset_root: Path, map_id: str) -> Path:
    suffix = "jpg" if map_id == "Lockdown" else "png"
    return dataset_root / "minimaps" / f"{map_id}_Minimap.{suffix}"


def build_journey_map(events: pd.DataFrame, image_path: Path, selected_player: str | None, show_events: bool = True) -> go.Figure:
    image = Image.open(image_path)
    width, height = image.size
    figure = go.Figure()
    # Source image sizes differ. World points are projected independently from
    # the documented 1024 logical canvas; alignment remains explicitly flagged.
    figure.add_layout_image(dict(source=image, x=0, y=0, sizex=width, sizey=height, xref="x", yref="y", layer="below", sizing="stretch"))
    movements = events[events["event_name"].isin(["Position", "BotPosition"])]
    for player_id, group in movements.groupby("user_id", sort=False):
        is_selected = selected_player == player_id
        color = SELECTED_COLOR if is_selected else (HUMAN_COLOR if group["player_class"].iloc[0] == "human" else BOT_COLOR)
        figure.add_trace(go.Scattergl(
            x=group["pixel_x"], y=group["pixel_y"], mode="lines", name=str(player_id)[:10],
            legendgroup=str(player_id), line=dict(color=color, width=3 if is_selected else 1.4),
            customdata=group[["event_name", "relative_t_ms", "player_class"]],
            hovertemplate="Player: %{fullData.name}<br>Type: %{customdata[2]}<br>Relative ms: %{customdata[1]}<extra></extra>",
        ))
    if show_events:
        for event_name, style in EVENT_STYLE.items():
            group = events[events["event_name"] == event_name]
            if group.empty:
                continue
            figure.add_trace(go.Scattergl(x=group["pixel_x"], y=group["pixel_y"], mode="markers", name=style["label"], marker=dict(color=style["color"], symbol=style["symbol"], size=9), customdata=group[["user_id", "relative_t_ms"]], hovertemplate="%{fullData.name}<br>Player: %{customdata[0]}<br>Relative ms: %{customdata[1]}<extra></extra>"))
    figure.update_xaxes(range=[0, width], visible=False, constrain="domain")
    figure.update_yaxes(range=[height, 0], visible=False, scaleanchor="x", scaleratio=1)
    figure.update_layout(template="plotly_dark", height=740, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", y=-0.08), paper_bgcolor="#111827", plot_bgcolor="#111827")
    return figure
