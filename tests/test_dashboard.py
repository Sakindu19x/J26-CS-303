"""Tests for dashboard loaders, export utilities, charts, and filtering."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd
import pytest

from c4.dashboard.charts import create_chronological_timeline_chart
from c4.dashboard.export_utils import export_timeline_to_csv, export_timeline_to_json
from c4.dashboard.loaders import MissingArtifactError, load_dashboard_data
from c4.timeline import filter_timeline


def test_load_dashboard_data_success():
    """Verify loading preprocessed data successfully loads all dashboard components."""
    data = load_dashboard_data()
    assert "timelines" in data
    assert "sequences" in data
    assert "data_quality" in data
    assert "tactic_discrepancies" in data

    # Verify 4 episodes present
    assert set(data["timelines"].keys()) == {"E1", "E2", "E3", "E4"}


def test_export_timeline_to_csv_preserves_ids():
    """Verify CSV export keeps event_id and episode_id and serializes complex fields."""
    synthetic_events = [
        {
            "event_id": "E1-S001",
            "episode_id": "E1",
            "timestamp": "2025-01-01T00:00:00+00:00",
            "techniques": ["T1059", "T1078"],
            "tactics": ["Execution"],
            "label_status": "ground_truth",
        },
        {
            "event_id": "E1-S002",
            "episode_id": "E1",
            "timestamp": "2025-01-01T00:01:00+00:00",
            "techniques": [],
            "tactics": [],
            "label_status": "unlabeled",
        },
    ]

    csv_text = export_timeline_to_csv(synthetic_events)
    df = pd.read_csv(pd.io.common.StringIO(csv_text))

    assert "event_id" in df.columns
    assert "episode_id" in df.columns
    assert df["event_id"].tolist() == ["E1-S001", "E1-S002"]
    assert df["episode_id"].tolist() == ["E1", "E1"]

    # Verify techniques were serialized as valid JSON strings in CSV
    parsed_techs = json.loads(df.loc[0, "techniques"])
    assert parsed_techs == ["T1059", "T1078"]


def test_export_timeline_to_json_preserves_ids():
    """Verify JSON export preserves event_id and episode_id."""
    synthetic_events = [
        {"event_id": "E2-S001", "episode_id": "E2", "timestamp": "2025-01-01T00:00:00+00:00"},
    ]
    json_text = export_timeline_to_json(synthetic_events)
    parsed = json.loads(json_text)

    assert len(parsed) == 1
    assert parsed[0]["event_id"] == "E2-S001"
    assert parsed[0]["episode_id"] == "E2"


def test_export_empty_timeline():
    """Verify exporting empty timeline produces valid empty structures."""
    csv_empty = export_timeline_to_csv([])
    assert "event_id" in csv_empty
    assert "episode_id" in csv_empty

    json_empty = export_timeline_to_json([])
    assert json.loads(json_empty) == []


def test_charts_empty_timeline_figure():
    """Verify chart generation with empty events returns a valid Plotly Figure without crashing."""
    fig = create_chronological_timeline_chart([])
    assert fig is not None
    assert hasattr(fig, "data")
    assert "0 events" in fig.layout.title.text


def test_charts_with_synthetic_timeline():
    """Verify chart generation with events populates trace data."""
    synthetic_events = [
        {"event_id": "E1-S001", "timestamp": "2025-01-01T00:00:00+00:00", "label_status": "ground_truth", "techniques": ["T1059"]},
        {"event_id": "E1-S002", "timestamp": "2025-01-01T00:05:00+00:00", "label_status": "unlabeled", "techniques": []},
    ]
    fig = create_chronological_timeline_chart(synthetic_events, y_axis_mode="technique")
    assert fig is not None
    assert len(fig.data) > 0


def test_timeline_filters_empty_and_invalid():
    """Verify filtering timeline with empty results and invalid criteria."""
    events = [
        {"event_id": "E1-S001", "episode_id": "E1", "hostname": "host-a", "techniques": ["T1059"], "tactics": ["Execution"]},
    ]

    # Non-existent hostname
    res1 = filter_timeline(events, hostname="non-existent")
    assert res1 == []

    # Non-existent technique
    res2 = filter_timeline(events, technique="T9999")
    assert res2 == []

    # Non-existent tactic
    res3 = filter_timeline(events, tactic="NonExistentTactic")
    assert res3 == []

    # Empty events input
    res4 = filter_timeline([], hostname="host-a")
    assert res4 == []


def test_dashboard_renders_all_episodes_via_apptest():
    """Verify Streamlit dashboard renders without unhandled exceptions across all 4 episodes."""
    from streamlit.testing.v1 import AppTest

    app_path = Path(__file__).resolve().parents[1] / "src" / "c4" / "dashboard" / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Dashboard threw unhandled exception on default load: {at.exception}"

    # Verify switching to each episode
    for ep in ["E1", "E2", "E3", "E4"]:
        ep_sb = at.sidebar.selectbox[0]
        assert ep_sb.label == "Active Episode"
        ep_sb.select(ep).run()
        assert not at.exception, f"Dashboard threw exception when rendering episode {ep}: {at.exception}"

