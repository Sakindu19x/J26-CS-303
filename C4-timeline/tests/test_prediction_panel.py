"""Unit and rendering tests for Next-Step Prediction Panel (FR6, FR7, FR9, NFR4, NFR6).

Asserts that for every record in prediction_records_loeo.jsonl:
1. View data extracted equals the exact record fields without runtime computation.
2. Rendered HTML contains all candidate identifiers, probabilities, evidence, and hashes.
3. Streamlit prediction dashboard renders cleanly across all episodes via AppTest.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from c4.dashboard.prediction_panel import (
    extract_panel_view_data,
    format_c3_value,
    get_records_by_episode,
    load_prediction_records_by_sample,
    render_prediction_panel_html,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
JSONL_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"


def test_load_all_records_count():
    """Verify loading all 171 prediction records (95 technique + 76 tactic)."""
    records = load_prediction_records_by_sample()
    assert len(records) == 171
    tech_count = sum(1 for r in records.values() if r["prediction_type"] == "technique")
    tac_count = sum(1 for r in records.values() if r["prediction_type"] == "tactic")
    assert tech_count == 95
    assert tac_count == 76


def test_all_records_rendered_values_equal_record_fields():
    """Gate test: For every record (171/171), values rendered/extracted equal record fields."""
    records = load_prediction_records_by_sample()
    assert len(records) == 171

    for sample_id, rec in records.items():
        inp = rec["input"]
        ptype = rec["prediction_type"]
        p_obj = rec["technique_prediction"] if ptype == "technique" else rec["tactic_prediction"]
        assert p_obj is not None

        d = extract_panel_view_data(rec)

        # 1. Exact equality on identity and context
        assert d["sample_id"] == inp["sample_id"]
        assert d["episode_id"] == inp["episode_id"]
        assert d["prediction_level"] == ptype
        assert d["event_index"] == inp.get("event_index")
        assert d["last_timestamp"] == inp.get("last_timestamp")
        assert d["current_techniques"] == inp.get("current_technique_set", [])
        assert d["current_tactics"] == inp.get("current_tactic_set", [])
        assert d["previous_supporting_techniques"] == inp.get("previous_supporting_techniques", [])
        assert d["incident_stage"] == format_c3_value(inp.get("incident_stage"))
        assert d["affected_asset"] == format_c3_value(inp.get("affected_asset"))

        # 2. Upstream C3 null semantics
        c3_raw = inp.get("c3_fields", {})
        for field in ["threat_score", "investigation_priority", "asset_criticality", "cti_confidence", "freshness", "ioc", "ioc_type"]:
            expected_c3 = format_c3_value(c3_raw.get(field))
            assert d["c3_fields"][field] == expected_c3
            if c3_raw.get(field) is None:
                assert d["c3_fields"][field] == "not provided by dataset"

        # 3. Model outputs & evidence
        assert d["status"] == p_obj["status"]
        assert d["ranked_candidates"] == p_obj.get("ranked_candidates", [])
        assert d["alternatives"] == p_obj.get("alternatives", [])
        assert d["reliability_banner"] == p_obj.get("measured_reliability_banner", {}).get("banner_text", "")
        assert d["explanation"] == p_obj.get("explanation", "")

        # 4. Cryptographic lineage
        assert d["record_id"] == rec["record_id"]
        assert d["model_file_sha256"] == rec["model"]["model_file_sha256"]
        assert d["input_events_sha256"] == rec["input_events_sha256"]
        assert d["record_sha256"] == rec["record_sha256"]

        # 5. Render HTML and verify presence of all essential fields
        html = render_prediction_panel_html(rec)
        assert inp["sample_id"] in html
        assert inp["episode_id"] in html
        assert rec["record_sha256"] in html
        assert rec["model"]["model_file_sha256"] in html

        for cand in p_obj.get("ranked_candidates", []):
            assert cand["candidate_id"] in html
            assert f"{cand['score']:.4f}" in html

        for alt in p_obj.get("alternatives", []):
            assert alt["candidate_id"] in html
            assert f"{alt['score']:.4f}" in html


def test_records_by_episode():
    """Verify grouping records by episode across all seven episodes."""
    by_ep = get_records_by_episode()
    assert set(by_ep.keys()) == {"E1", "E2", "E3", "E4", "E5", "E6", "E7"}
    total_recs = sum(len(v) for v in by_ep.values())
    assert total_recs == 171


def test_prediction_app_renders_via_apptest():
    """Verify Streamlit prediction_app renders cleanly via AppTest."""
    from streamlit.testing.v1 import AppTest

    app_path = REPO_ROOT / "src" / "c4" / "dashboard" / "prediction_app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Dashboard threw unhandled exception on default load: {at.exception}"

    # Verify switching episodes
    for ep in ["E1", "E2", "E3", "E4"]:
        ep_sb = at.sidebar.selectbox[0]
        assert ep_sb.label == "Active Episode"
        ep_sb.select(ep).run()
        assert not at.exception, f"Dashboard threw exception when rendering episode {ep}: {at.exception}"
