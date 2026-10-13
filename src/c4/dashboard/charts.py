"""Plotly interactive charts for C4 dashboard."""
from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def create_chronological_timeline_chart(
    events: list[dict[str, Any]],
    y_axis_mode: str = "step_index",
) -> go.Figure:
    """Create interactive chronological timeline scatter plot in Plotly.

    x-axis: timestamp (UTC)
    y-axis: step execution order or primary technique
    color: label_status ('ground_truth' vs 'unlabeled')
    """
    if not events:
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline events match the active filters.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=15, color="#888888"),
        )
        fig.update_layout(
            title="Chronological Attack Timeline (0 events)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=350,
            template="plotly_white",
        )
        return fig

    rows = []
    for idx, ev in enumerate(events, 1):
        techs = ev.get("techniques", [])
        primary_tech = techs[0] if techs else "(unlabeled)"
        tech_str = ", ".join(techs) if techs else "None"
        cmd = ev.get("cmd") or ""
        cmd_short = (cmd[:40] + "...") if len(cmd) > 40 else cmd

        rows.append({
            "event_id": ev.get("event_id"),
            "timestamp": ev.get("timestamp"),
            "step_index": idx,
            "primary_technique": primary_tech,
            "techniques": tech_str,
            "tactics": ", ".join(ev.get("tactics", [])),
            "label_status": ev.get("label_status", "unlabeled"),
            "hostname": ev.get("hostname") or "unspecified",
            "command": cmd_short,
            "sec_start": ev.get("seconds_since_episode_start"),
            "sec_prev": ev.get("seconds_since_previous_event"),
        })

    df = pd.DataFrame(rows)
    df["datetime"] = pd.to_datetime(df["timestamp"], errors="coerce")

    y_col = "primary_technique" if y_axis_mode == "technique" else "step_index"
    y_title = "Primary ATT&CK Technique" if y_axis_mode == "technique" else "Chronological Step Index"

    color_map = {
        "ground_truth": "#2563EB",  # Distinct blue
        "unlabeled": "#9CA3AF",     # Neutral muted gray
    }

    fig = px.scatter(
        df,
        x="datetime",
        y=y_col,
        color="label_status",
        color_discrete_map=color_map,
        hover_data={
            "event_id": True,
            "timestamp": True,
            "command": True,
            "hostname": True,
            "techniques": True,
            "tactics": True,
            "sec_start": True,
            "sec_prev": True,
            "datetime": False,
        },
        labels={
            "datetime": "Timestamp (UTC)",
            y_col: y_title,
            "label_status": "Label Status",
        },
        title=f"Attack Execution Timeline ({len(df)} events)",
    )

    fig.update_traces(
        marker=dict(size=11, line=dict(width=1, color="#1E293B")),
        mode="markers+lines",
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=450,
    )

    return fig
