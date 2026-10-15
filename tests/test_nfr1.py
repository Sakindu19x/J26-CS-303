"""Test NFR1 timing measurement artifact schemas (P8).

Per prompt requirement: Tests assert only the output schema, not values.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = REPO_ROOT / "reports" / "measurements" / "nfr1_timing.json"
MD_PATH = REPO_ROOT / "reports" / "measurements" / "nfr1_timing.md"


def test_nfr1_timing_artifacts_exist():
    """Verify that both JSON and Markdown timing measurement artifacts exist."""
    assert JSON_PATH.is_file(), f"Missing {JSON_PATH}"
    assert MD_PATH.is_file(), f"Missing {MD_PATH}"


def test_nfr1_timing_json_schema():
    """Verify JSON output schema contains all required sections, keys, and types without checking values."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Top-level keys
    required_top_keys = [
        "telemetry",
        "criteria",
        "summary_warm",
        "cold_start",
        "episodes",
        "scaling_benchmark",
        "verdict",
    ]
    for key in required_top_keys:
        assert key in data, f"Missing top-level key '{key}' in nfr1_timing.json"

    # Telemetry schema
    telem = data["telemetry"]
    assert isinstance(telem.get("cpu_model"), str)
    assert isinstance(telem.get("os"), str)
    assert isinstance(telem.get("python_version"), str)
    assert isinstance(telem.get("packages"), dict)
    for pkg in ["numpy", "pandas", "streamlit", "pytest", "jsonschema"]:
        assert pkg in telem["packages"], f"Missing package '{pkg}' in telemetry"

    # Criteria schema
    crit = data["criteria"]
    assert "warm_median_threshold_seconds" in crit
    assert "warm_p95_threshold_seconds" in crit
    assert "cold_start_threshold_seconds" in crit

    # Summary warm schema
    sw = data["summary_warm"]
    assert isinstance(sw.get("total_repetitions"), int)
    assert isinstance(sw.get("mean_seconds"), (int, float))
    assert isinstance(sw.get("median_seconds"), (int, float))
    assert isinstance(sw.get("p95_seconds"), (int, float))
    assert isinstance(sw.get("pass_median"), bool)
    assert isinstance(sw.get("pass_p95"), bool)

    # Cold start schema
    cs = data["cold_start"]
    assert isinstance(cs.get("cold_start_seconds"), (int, float))
    assert isinstance(cs.get("pass_cold_start"), bool)

    # Episodes schema
    eps = data["episodes"]
    assert set(eps.keys()) == {"E1", "E2", "E3", "E4", "E5", "E6", "E7"}
    for ep_id, ep_stats in eps.items():
        assert isinstance(ep_stats.get("events_count"), int)
        assert isinstance(ep_stats.get("repetitions"), int)
        assert isinstance(ep_stats.get("median_seconds"), (int, float))
        assert isinstance(ep_stats.get("p95_seconds"), (int, float))
        assert isinstance(ep_stats.get("mean_seconds"), (int, float))

    # Scaling benchmark schema
    scale = data["scaling_benchmark"]
    assert "base_episode" in scale
    assert "results" in scale
    assert set(scale["results"].keys()) == {"1x", "10x", "100x"}
    for mkey, mstats in scale["results"].items():
        assert isinstance(mstats.get("event_count"), int)
        assert isinstance(mstats.get("elapsed_seconds"), (int, float))
        assert isinstance(mstats.get("throughput_events_per_sec"), (int, float))

    # Verdict schema
    assert data["verdict"] in {"PASS", "FAIL"}


def test_nfr1_timing_markdown_structure():
    """Verify Markdown report contains required headers and tables without checking numeric values."""
    text = MD_PATH.read_text(encoding="utf-8")
    assert "# NFR1 Timing & Response Time Verification Report" in text
    assert "## 1. Executive Summary & Verdict" in text
    assert "## 2. Timed Region Definitions" in text
    assert "Per-Episode Latency Breakdown" in text
    assert "Scaling Benchmark" in text
    assert "Platform and Environment Telemetry" in text
    for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
        assert f"`{ep}`" in text
    for scale in ["1x", "10x", "100x"]:
        assert f"| {scale} |" in text


def test_verify_nfr1_script():
    """Verify scripts/verify_nfr1.py passes independently."""
    import subprocess
    import sys
    script = REPO_ROOT / "scripts" / "verify_nfr1.py"
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert res.returncode == 0, f"verify_nfr1.py failed:\n{res.stdout}\n{res.stderr}"
