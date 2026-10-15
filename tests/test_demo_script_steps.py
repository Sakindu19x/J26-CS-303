"""test_demo_script_steps.py

AppTest automated verification executing steps 2-10 of docs/demo_script.md (Prompt 15 R4(b)).
Fails if any described element is absent:
- Step 2: Select episode E1 (38 events, no cross-episode contamination)
- Step 3: Inspect chronological forensic timeline
- Step 4: Focus on attack step (select sample position E1-col-ful-K01)
- Step 5: Examine Ranked Top-3 Candidate Predictions (candidate table, T1589.002, probability)
- Step 6: Verify Empirical Evidence Basis (numerator/denominator, supporting training episodes)
- Step 7: Review Alternative Candidates and Tie Notices (alternatives expander, tie notice indicator)
- Step 8: Inspect Upstream C3 Interface Fields ("not provided by dataset")
- Step 9: Evaluate Empirical Reliability Banner (Markov vs Frequency Hit@3, Wilson intervals, coverage)
- Step 10: Review Cryptographic Provenance & Schema Validation (record_id, model SHA, input events SHA, record SHA, Schema Validation: 100% PASS)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_demo_script_steps_2_to_10_execution():
    from streamlit.testing.v1 import AppTest

    app_path = REPO_ROOT / "src" / "c4" / "dashboard" / "prediction_app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception, f"Dashboard threw unhandled exception on launch: {at.exception}"

    # -------------------------------------------------------------------------
    # Step 2: Select an Episode Boundary
    # -------------------------------------------------------------------------
    ep_sb = at.sidebar.selectbox[0]
    assert ep_sb.label == "Active Episode", "Sidebar missing Active Episode selector"
    assert "E1" in ep_sb.options, "E1 missing from episode options"
    ep_sb.select("E1").run()
    assert not at.exception, f"Exception selecting E1: {at.exception}"

    # Verify 38 events for E1
    sidebar_md_text = "".join(m.value for m in at.sidebar.markdown)
    assert "38" in sidebar_md_text, "E1 event count (38) not displayed in sidebar metadata"

    # -------------------------------------------------------------------------
    # Step 3: Inspect the Chronological Forensic Timeline
    # -------------------------------------------------------------------------
    assert len(at.dataframe) > 0, "Chronological forensic timeline dataframe missing"
    tl_df = at.dataframe[0].value
    assert len(tl_df) == 38, f"Expected 38 events in E1 timeline dataframe, got {len(tl_df)}"
    assert "timestamp" in tl_df.columns, "Timeline missing timestamp column"
    assert "technique_id" in tl_df.columns or "techniques" in tl_df.columns, "Timeline missing technique column"

    # -------------------------------------------------------------------------
    # Step 4: Focus on an Attack Step (Position Selector)
    # -------------------------------------------------------------------------
    sample_sb = at.selectbox[0]
    assert sample_sb.label == "Select Prediction Sample / Position"
    assert "E1-col-ful-K01" in sample_sb.options, "Sample E1-col-ful-K01 missing from options"
    sample_sb.select("E1-col-ful-K01").run()
    assert not at.exception, f"Exception selecting sample E1-col-ful-K01: {at.exception}"

    all_md = "\n".join(m.value for m in at.markdown)
    assert "E1-col-ful-K01" in all_md, "Selected sample E1-col-ful-K01 not displayed in prediction panel"

    # -------------------------------------------------------------------------
    # Step 5: Examine Ranked Top-3 Candidate Predictions
    # -------------------------------------------------------------------------
    assert len(at.table) >= 1, "Ranked Top-k Next-Step Candidates table missing"
    top_table = at.table[0].value
    assert len(top_table) >= 1, "Top-k candidates table is empty"
    first_candidate = dict(top_table.iloc[0])
    assert "Candidate ID" in first_candidate, "Candidate table missing Candidate ID column"
    assert first_candidate["Candidate ID"] == "T1589.002", f"Expected top candidate T1589.002, got {first_candidate['Candidate ID']}"
    assert "Email Addresses" in first_candidate["Name"], f"Expected Email Addresses name, got {first_candidate['Name']}"
    assert "1.0000" in first_candidate["Probability"], f"Expected 1.0000 probability, got {first_candidate['Probability']}"

    # -------------------------------------------------------------------------
    # Step 6: Verify Empirical Evidence Basis (FR5)
    # -------------------------------------------------------------------------
    assert "Numerator / Denominator" in first_candidate, "Candidate table missing Numerator / Denominator column"
    assert "1.00 / 1.00" in first_candidate["Numerator / Denominator"]
    assert "Supporting Episodes" in first_candidate, "Candidate table missing Supporting Episodes column"
    assert "E7" in first_candidate["Supporting Episodes"]

    # -------------------------------------------------------------------------
    # Step 7: Review Alternative Candidates and Tie Notices (FR6)
    # -------------------------------------------------------------------------
    # For E1-col-ful-K01: tie notice indicator shows "No boundary ties detected."
    assert "No boundary ties detected." in all_md, "Tie notice 'No boundary ties detected.' missing for E1-col-ful-K01"

    # Select sample with alternative candidates and boundary ties: E1-tac-col-K01
    assert "E1-tac-col-K01" in sample_sb.options, "Sample E1-tac-col-K01 missing from options"
    sample_sb.select("E1-tac-col-K01").run()
    assert not at.exception, f"Exception selecting sample E1-tac-col-K01: {at.exception}"

    all_md_tac = "\n".join(m.value for m in at.markdown)
    assert len(at.expander) >= 1, "Alternative Candidates expander missing for E1-tac-col-K01"
    expander_labels = [exp.label for exp in at.expander]
    assert any("Alternative Candidates" in lbl for lbl in expander_labels), f"Expander label missing Alternative Candidates: {expander_labels}"
    assert "Top-3 rank boundary is tied" in all_md_tac, "Tied boundary notice missing for E1-tac-col-K01"

    # Switch back to E1-col-ful-K01 for steps 8-10 checks
    sample_sb.select("E1-col-ful-K01").run()
    all_md = "\n".join(m.value for m in at.markdown)

    # -------------------------------------------------------------------------
    # Step 8: Inspect Upstream C3 Interface Fields (FR8)
    # -------------------------------------------------------------------------
    assert "Upstream Telemetry (Component 3)" in all_md, "Upstream Telemetry (Component 3) section missing"
    assert "Threat Score:** not provided by dataset" in all_md
    assert "Investigation Priority:** not provided by dataset" in all_md
    assert "Asset Criticality:** not provided by dataset" in all_md
    assert "CTI Confidence:** not provided by dataset" in all_md
    assert "Freshness:** not provided by dataset" in all_md
    assert "Observable IoC:** not provided by dataset" in all_md

    # -------------------------------------------------------------------------
    # Step 9: Evaluate the Empirical Reliability Banner (FR7)
    # -------------------------------------------------------------------------
    info_texts = "\n".join(i.value for i in at.info)
    assert "Empirical Reliability Benchmark" in info_texts, "Empirical Reliability Banner missing in at.info"
    assert "Markov Hit@3" in info_texts
    assert "3.16%" in info_texts
    assert "Frequency 16.84%" in info_texts
    assert "Coverage 64.21%" in info_texts

    # -------------------------------------------------------------------------
    # Step 10: Review Cryptographic Provenance and Schema Validation (NFR2, NFR3, NFR6)
    # -------------------------------------------------------------------------
    caption_texts = "\n".join(c.value for c in at.caption)
    assert "Record ID:" in caption_texts, "Record ID missing in cryptographic provenance metadata"
    assert "Model SHA-256:" in caption_texts, "Model SHA-256 missing in metadata"
    assert "Input Events SHA-256:" in caption_texts, "Input Events SHA-256 missing in metadata"
    assert "Record SHA-256:" in caption_texts, "Record SHA-256 missing in metadata"

    # Schema Validation Green Badge
    assert "Schema Validation: 100% PASS (c4_prediction_record.schema.json)" in all_md, "Schema validation 100% PASS badge missing"
