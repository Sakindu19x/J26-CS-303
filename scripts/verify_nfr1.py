"""verify_nfr1.py

Independent verifier for NFR1 timing measurements (Prompt 14 Q9b).
Asserts:
1. reports/measurements/nfr1_timing.json exists and is valid JSON.
2. reports/measurements/nfr1_timing.md exists and is non-empty.
3. Every numeric value in nfr1_timing.md matches the exact value in nfr1_timing.json (via regex extraction).
4. CPU model and all platform telemetry strings in the Markdown report match the JSON telemetry block exactly.
5. All timed region names and descriptions appear in the markdown.
6. Verdict in Markdown matches verdict in JSON.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = REPO_ROOT / "reports" / "measurements" / "nfr1_timing.json"
MD_PATH = REPO_ROOT / "reports" / "measurements" / "nfr1_timing.md"


def verify_nfr1() -> None:
    print("=" * 80)
    print("INDEPENDENT NFR1 VERIFICATION (scripts/verify_nfr1.py)")
    print("=" * 80)

    if not JSON_PATH.is_file():
        print(f"FAIL: Missing JSON file: {JSON_PATH}")
        sys.exit(1)
    if not MD_PATH.is_file():
        print(f"FAIL: Missing Markdown file: {MD_PATH}")
        sys.exit(1)

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    md_text = MD_PATH.read_text(encoding="utf-8")

    # 1. Telemetry checks
    telemetry = data["telemetry"]
    cpu = telemetry["cpu_model"]
    machine = telemetry["machine"]
    os_str = telemetry["os"]
    py_ver = telemetry["python_version"]
    py_exe = telemetry["python_executable"]
    pkgs = telemetry["packages"]

    assert f"**Processor**: `{cpu}` ({machine})" in md_text, f"CPU mismatch in MD: expected `{cpu}` ({machine})"
    assert f"**Operating System**: `{os_str}`" in md_text, f"OS mismatch in MD: expected `{os_str}`"
    assert f"**Python Runtime**: `{py_ver}` (`{py_exe}`)" in md_text, f"Python runtime mismatch in MD"

    for pkg_name, pkg_ver in pkgs.items():
        if pkg_name != "python":
            expected_line = f"- `{pkg_name}`: `{pkg_ver}`"
            assert expected_line in md_text, f"Missing or mismatched package in MD: {expected_line}"

    print("[Step 1] Platform telemetry strings match JSON block exactly [PASS]")

    # 2. Executive summary table checks
    crit = data["criteria"]
    summary = data["summary_warm"]
    proc_cold = data["process_cold_start"]
    in_proc_cold = data["in_process_cold_start"]
    st_ready = data["streamlit_server_ready"]
    verdict = data["verdict"]

    # Check median
    med_pat = re.compile(r"\|\s*\*\*Warm End-to-End Latency \(Median\)\*\*\s*\|\s*[\$\\]*le[\$\s]*([0-9\.]+)\s*s\s*\|\s*\*\*([0-9\.]+)\s*s\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|")
    m_med = med_pat.search(md_text)
    assert m_med, "Warm median row not found in MD"
    assert float(m_med.group(1)) == crit["warm_median_threshold_seconds"]
    assert float(m_med.group(2)) == summary["median_seconds"]
    assert m_med.group(3) == ("PASS" if summary["pass_median"] else "FAIL")

    # Check p95
    p95_pat = re.compile(r"\|\s*\*\*Warm End-to-End Latency \(p95\)\*\*\s*\|\s*[\$\\]*le[\$\s]*([0-9\.]+)\s*s\s*\|\s*\*\*([0-9\.]+)\s*s\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|")
    m_p95 = p95_pat.search(md_text)
    assert m_p95, "Warm p95 row not found in MD"
    assert float(m_p95.group(1)) == crit["warm_p95_threshold_seconds"]
    assert float(m_p95.group(2)) == summary["p95_seconds"]
    assert m_p95.group(3) == ("PASS" if summary["pass_p95"] else "FAIL")

    # Check process cold start
    cold_pat = re.compile(r"\|\s*\*\*Process-Level Cold Start \(Parent-Timed\)\*\*\s*\|\s*[\$\\]*le[\$\s]*([0-9\.]+)\s*s\s*\|\s*\*\*([0-9\.]+)\s*s\*\*\s*\|\s*\*\*(\w+)\*\*\s*\|")
    m_cold = cold_pat.search(md_text)
    assert m_cold, "Process cold start row not found in MD"
    assert float(m_cold.group(1)) == crit["process_cold_start_threshold_seconds"]
    assert float(m_cold.group(2)) == proc_cold["parent_timed_seconds"]
    assert m_cold.group(3) == ("PASS" if proc_cold["pass"] else "FAIL")

    # Check in-process cold start
    in_cold_pat = re.compile(r"\|\s*\*\*In-Process First-Record Latency\*\*\s*\|\s*Informational \(None\)\s*\|\s*\*\*([0-9\.]+)\s*s\*\*\s*\|\s*\*\*INFORMATIONAL\*\*\s*\|")
    m_in_cold = in_cold_pat.search(md_text)
    assert m_in_cold, "In-process cold start row not found in MD"
    assert float(m_in_cold.group(1)) == in_proc_cold["first_record_latency_seconds"]

    # Check streamlit ready time
    st_pat = re.compile(r"\|\s*\*\*Streamlit Server Ready Time \(Port\s*(\d+)\)\*\*\s*\|\s*Informational \(None\)\s*\|\s*\*\*([0-9\.]+)\s*s\*\*\s*\|\s*\*\*INFORMATIONAL\*\*\s*\|")
    m_st = st_pat.search(md_text)
    assert m_st, "Streamlit server ready row not found in MD"
    assert int(m_st.group(1)) == st_ready["port"]
    assert float(m_st.group(2)) == st_ready["ready_time_seconds"]

    # Check overall compliance
    verdict_pat = re.compile(r"\|\s*\*\*Overall NFR1 Compliance\*\*\s*\|\s*All Gated Criteria Satisfied\s*\|\s*—\s*\|\s*\*\*(\w+)\*\*\s*\|")
    m_verd = verdict_pat.search(md_text)
    assert m_verd, "Overall compliance row not found in MD"
    assert m_verd.group(1) == verdict

    print("[Step 2] Executive summary and verdict rows match JSON exactly [PASS]")

    # 3. Timed region definitions
    regions = data["timed_region_definitions"]
    for reg_key, reg_info in regions.items():
        assert reg_info["name"] in md_text, f"Missing timed region name in MD: {reg_info['name']}"
        assert reg_info["description"] in md_text, f"Missing timed region description in MD: {reg_info['description']}"

    print("[Step 3] All timed region definitions verified in MD [PASS]")

    # 4. Per-episode table checks
    ep_timings = data["episodes"]
    for ep, stats in sorted(ep_timings.items()):
        ep_pat = re.compile(rf"\|\s*`{ep}`\s*\|\s*{stats['events_count']}\s*\|\s*([0-9\.]+)\s*s\s*\|\s*([0-9\.]+)\s*s\s*\|\s*([0-9\.]+)\s*s\s*\|\s*\[([0-9\.]+),\s*([0-9\.]+)\]\s*s\s*\|")
        m_ep = ep_pat.search(md_text)
        assert m_ep, f"Episode {ep} row not found or mismatched in MD"
        assert float(m_ep.group(1)) == stats["median_seconds"]
        assert float(m_ep.group(2)) == stats["p95_seconds"]
        assert float(m_ep.group(3)) == stats["mean_seconds"]
        assert float(m_ep.group(4)) == stats["min_seconds"]
        assert float(m_ep.group(5)) == stats["max_seconds"]

    print("[Step 4] All per-episode latency rows match JSON exactly [PASS]")

    # 5. Scaling benchmark checks
    scaling = data["scaling_benchmark"]["results"]
    for scale_key, sdata in scaling.items():
        scale_pat = re.compile(rf"\|\s*{scale_key}\s*\|\s*{sdata['event_count']}\s*\|\s*{sdata['timeline_length']}\s*\|\s*([0-9\.]+)\s*s\s*\|\s*([0-9\.]+)\s*events/s\s*\|")
        m_sc = scale_pat.search(md_text)
        assert m_sc, f"Scaling {scale_key} row not found or mismatched in MD"
        assert float(m_sc.group(1)) == sdata["elapsed_seconds"]
        assert float(m_sc.group(2)) == sdata["throughput_events_per_sec"]

    print("[Step 5] Scaling benchmark rows match JSON exactly [PASS]")

    print("=" * 80)
    print("ALL NFR1 TIMING VERIFICATIONS PASSED SUCCESSFULLY (Exit 0)")
    print("=" * 80)


if __name__ == "__main__":
    verify_nfr1()
