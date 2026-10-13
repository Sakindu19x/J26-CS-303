"""Timeline export utilities for C4 dashboard."""
from __future__ import annotations

import io
import json
from typing import Any

import pandas as pd

from c4.timeline import TIMELINE_COLUMNS


def export_timeline_to_csv(events: list[dict[str, Any]]) -> str:
    """Serialize timeline events to CSV string ensuring event_id and episode_id are preserved."""
    if not events:
        empty_df = pd.DataFrame(columns=TIMELINE_COLUMNS)
        return empty_df.to_csv(index=False)

    df = pd.DataFrame(events)

    # Ensure event_id and episode_id are present
    assert "event_id" in df.columns, "Exported CSV must contain event_id"
    assert "episode_id" in df.columns, "Exported CSV must contain episode_id"

    # JSON-serialize nested list or dict columns for valid tabular CSV formatting
    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)

    buf = io.StringIO()
    df.to_csv(buf, index=False, encoding="utf-8")
    return buf.getvalue()


def export_timeline_to_json(events: list[dict[str, Any]]) -> str:
    """Serialize timeline events to formatted JSON string ensuring event_id and episode_id are preserved."""
    if not events:
        return "[]"

    for ev in events:
        if "event_id" not in ev or "episode_id" not in ev:
            raise ValueError("All timeline events must contain event_id and episode_id")

    return json.dumps(events, indent=2, ensure_ascii=False)
