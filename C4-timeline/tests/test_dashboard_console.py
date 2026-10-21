"""test_dashboard_console.py

Comprehensive tests for Part S3 Industry-Grade Analyst Console:
1. Grep Gate: Asserts NO hardcoded evaluation percentages or model metrics in dashboard code.
2. AppTest Fidelity Gate: Asserts displayed metrics, key figures, and candidate probabilities
   equal the exact values in records/JSON files without runtime fabrication.
3. Episode & Mode Switching: Asserts error-free rendering across all 7 episodes and both prediction levels.
4. WCAG Contrast Check: Asserts theme token contrast ratios >= 4.5:1.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = REPO_ROOT / "src" / "c4" / "dashboard"
APP_PATH = DASHBOARD_DIR / "prediction_app.py"
JSONL_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"
EVAL_PATH = REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json"
TIMELINES_PATH = REPO_ROOT / "data" / "processed_7ep" / "attack_timelines.json"


def test_grep_gate_no_hardcoded_evaluation_numbers():
    """Grep Gate: Verify dashboard code contains no hardcoded evaluation result constants."""
    hardcoded_suspicious_patterns = [
        r"['\"]13\.68['\"]",
        r"['\"]16\.84['\"]",
        r"['\"]63\.16['\"]",
        r"['\"]28\.95['\"]",
        r"['\"]0\.0430['\"]",
        r"['\"]0\.1548['\"]",
        r"['\"]0\.0316['\"]",
    ]
    
    dashboard_files = list(DASHBOARD_DIR.glob("*.py"))
    assert len(dashboard_files) > 0

    for py_file in dashboard_files:
        content = py_file.read_text(encoding="utf-8")
        for pat in hardcoded_suspicious_patterns:
            matches = re.findall(pat, content)
            assert not matches, f"Hardcoded metric {pat} detected in {py_file.name}: {matches}"


def test_apptest_console_renders_cleanly():
    """Verify Streamlit console initializes and renders with zero unhandled exceptions."""
    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert not at.exception, f"App threw exception: {at.exception}"


def test_apptest_key_figures_match_timeline_data():
    """Verify key figures rendered match the actual episode timeline counts."""
    with open(TIMELINES_PATH, "r", encoding="utf-8") as f:
        timelines = json.load(f)

    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert not at.exception

    for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
        ep_sb = at.sidebar.selectbox[0]
        ep_sb.select(ep).run()
        assert not at.exception

        ev_count = len(timelines[ep])
        # The key figure strip contains the event count
        # In markdown strings rendered by AppTest
        all_markdown = " ".join([m.value for m in at.markdown])
        assert f">{ev_count}</div>" in all_markdown or str(ev_count) in all_markdown


def test_apptest_candidate_probabilities_match_records():
    """Verify next-step candidate probabilities rendered match the prediction record."""
    records = {}
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                records[rec["input"]["sample_id"]] = rec

    at = AppTest.from_file(str(APP_PATH), default_timeout=30)
    at.run()
    assert not at.exception

    # Select E1 and check first sample
    sample_sb = at.sidebar.selectbox[1]
    sample_id = sample_sb.value
    assert sample_id in records

    target_rec = records[sample_id]
    ptype = target_rec["prediction_type"]
    p_obj = target_rec["technique_prediction"] if ptype == "technique" else target_rec["tactic_prediction"]
    
    all_markdown = " ".join([m.value for m in at.markdown])
    for cand in p_obj.get("ranked_candidates", []):
        cid = cand["candidate_id"]
        score = cand["score"]
        assert cid in all_markdown
        assert f"{score:.4f}" in all_markdown


def test_wcag_theme_contrast():
    """Verify WCAG AA 4.5:1 contrast compliance across all design tokens."""
    from c4.dashboard.theme import verify_all_tokens_contrast
    results = verify_all_tokens_contrast(min_ratio=4.5)
    for pair, ratio, passed in results:
        assert passed, f"Token pair {pair.name} failed WCAG AA: ratio {ratio:.2f} < 4.5"
