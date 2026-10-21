"""Interactive visualization charts for C4 dashboard (Altair and Plotly)."""
from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Canonical 14 MITRE ATT&CK Enterprise Tactics in Kill-Chain Order
KILL_CHAIN_TACTICS = [
    "Reconnaissance",
    "Resource Development",
    "Initial Access",
    "Execution",
    "Persistence",
    "Privilege Escalation",
    "Defense Evasion",
    "Credential Access",
    "Discovery",
    "Lateral Movement",
    "Collection",
    "Command and Control",
    "Exfiltration",
    "Impact",
]


def create_kill_chain_swimlane_chart(
    events: list[dict[str, Any]],
    active_event_id: str | None = None,
) -> alt.Chart:
    """Create an industry-grade ATT&CK kill-chain swim-lane timeline using bundled Altair.

    - Rows: ATT&CK tactics ordered strictly by kill-chain sequence.
    - Markers: Events plotted along chronological step index.
    - Accessibility: Colorblind-safe palette (Okabe-Ito) + distinct shapes + text labels.
      Information is NEVER conveyed by color alone.
    - Hover: Rich tooltips displaying event ID, timestamp, techniques, command summary.
    """
    if not events:
        df_empty = pd.DataFrame({"x": [0], "y": ["Initial Access"], "text": ["No events recorded"]})
        return alt.Chart(df_empty).mark_text().encode(x="x", y="y", text="text").properties(height=200)

    rows = []
    for idx, ev in enumerate(events, 1):
        tactics = ev.get("tactics", [])
        techs = ev.get("techniques", [])
        primary_tech = techs[0] if techs else "(unlabeled)"
        label_status = ev.get("label_status", "unlabeled")
        is_active = (ev.get("event_id") == active_event_id)

        # Plot on each associated tactic row, or Initial Access / (unlabeled) if none
        plotted_tactics = [t for t in tactics if t in KILL_CHAIN_TACTICS]
        if not plotted_tactics:
            plotted_tactics = ["Execution"] if "Execution" in tactics else ["Initial Access"]

        cmd = ev.get("cmd") or ""
        cmd_short = (cmd[:50] + "...") if len(cmd) > 50 else cmd

        for tac in plotted_tactics:
            rows.append({
                "step_index": idx,
                "tactic": tac,
                "event_id": ev.get("event_id", f"EV-{idx}"),
                "timestamp": str(ev.get("timestamp", "")),
                "primary_technique": primary_tech,
                "all_techniques": ", ".join(techs) if techs else "None",
                "label_status": label_status,
                "is_active": "Selected Step" if is_active else label_status,
                "command": cmd_short,
            })

    df = pd.DataFrame(rows)

    # Colorblind-safe Okabe-Ito categorical mapping
    # Ground truth = #0072B2 (Blue), Derived = #E69F00 (Orange), Unlabeled = #56B4E9 (Sky blue), Active = #D55E00 (Vermillion)
    domain = ["ground_truth", "derived", "unlabeled", "Selected Step"]
    color_range = ["#0072B2", "#E69F00", "#56B4E9", "#D55E00"]
    shape_range = ["circle", "square", "triangle-up", "diamond"]

    # Base chart
    base = alt.Chart(df).encode(
        x=alt.X("step_index:Q", title="Chronological Sequence Step Index", axis=alt.Axis(tickMinStep=1)),
        y=alt.Y("tactic:N", sort=KILL_CHAIN_TACTICS, title="ATT&CK Tactic (Kill-Chain Order)"),
    )

    # Background swim-lane rule
    rule = alt.Chart(pd.DataFrame({"tactic": KILL_CHAIN_TACTICS})).mark_rule(
        strokeDash=[3, 3],
        color="#E2E8F0",
        strokeWidth=1,
    ).encode(
        y=alt.Y("tactic:N", sort=KILL_CHAIN_TACTICS),
    )

    # Event points
    points = base.mark_point(size=140, filled=True, opacity=0.9).encode(
        color=alt.Color("is_active:N", scale=alt.Scale(domain=domain, range=color_range), legend=alt.Legend(title="Status")),
        shape=alt.Shape("is_active:N", scale=alt.Scale(domain=domain, range=shape_range), legend=alt.Legend(title="Status")),
        tooltip=[
            alt.Tooltip("step_index:Q", title="Step Index"),
            alt.Tooltip("event_id:N", title="Event ID"),
            alt.Tooltip("timestamp:N", title="Timestamp (UTC)"),
            alt.Tooltip("tactic:N", title="Tactic"),
            alt.Tooltip("primary_technique:N", title="Primary Technique"),
            alt.Tooltip("all_techniques:N", title="All Techniques"),
            alt.Tooltip("label_status:N", title="Status"),
            alt.Tooltip("command:N", title="Command"),
        ],
    )

    # Text labels (technique ID) placed adjacent to points
    text = base.mark_text(
        align="left",
        baseline="middle",
        dx=9,
        fontSize=10,
        fontWeight=600,
        color="#334155",
    ).encode(
        text=alt.Text("primary_technique:N"),
    )

    chart = (rule + points + text).properties(
        width=1100,
        height=450,
        title=alt.TitleParams(
            text=f"ATT&CK Kill-Chain Swim-Lane Execution Timeline ({len(events)} events)",
            subtitle="Rows ordered by canonical MITRE ATT&CK kill-chain phases; markers annotated with technique IDs",
            fontSize=14,
            subtitleFontSize=11,
            color="#0F172A",
            subtitleColor="#475569",
        ),
    ).configure_view(
        strokeWidth=0,
    ).configure_axis(
        labelFontSize=11,
        titleFontSize=12,
        titleFontWeight=600,
        labelColor="#334155",
        titleColor="#0F172A",
    )

    return chart


def create_chronological_timeline_chart(
    events: list[dict[str, Any]],
    y_axis_mode: str = "step_index",
) -> go.Figure:
    """Create interactive chronological timeline scatter plot in Plotly (preserved for backward compatibility)."""
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
        "ground_truth": "#2563EB",
        "unlabeled": "#9CA3AF",
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
    )

    fig.update_layout(
        template="plotly_white",
        height=400,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9"),
    )

    return fig
