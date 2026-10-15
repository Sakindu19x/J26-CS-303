"""verify_overnight_summary.py

Independent verifier for reports/overnight_summary.md (Prompt 14 Q6).
Checks that every number and embedded section in overnight_summary.md strictly
matches its source file (ledger, decisions, and JSON measurements).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = REPO_ROOT / "reports" / "overnight_summary.md"
LEDGER_PATH = REPO_ROOT / "reports" / "overnight_ledger.md"
DECISIONS_PATH = REPO_ROOT / "reports" / "overnight_decisions.md"
NFR1_PATH = REPO_ROOT / "reports" / "measurements" / "nfr1_timing.json"
DQR_PATH = REPO_ROOT / "reports" / "7ep" / "data_quality_report.json"
RECORDS_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"


def verify_overnight_summary(md_override: str | None = None, verbose: bool = True) -> None:
    if verbose:
        print("=" * 80)
        print("VERIFYING OVERNIGHT SUMMARY (scripts/verify_overnight_summary.py)")
        print("=" * 80)

    if md_override is not None:
        md_text = md_override
    else:
        assert SUMMARY_PATH.is_file(), f"Missing {SUMMARY_PATH}"
        md_text = SUMMARY_PATH.read_text(encoding="utf-8")

    # Section headings and document structure
    assert "## 1. Executive Summary" in md_text
    assert "## 2. Overnight Execution Ledger" in md_text
    assert "## 3. Overnight Decisions Register" in md_text
    assert "## 4. Verification & Audit Sign-Off" in md_text
    assert "All protocol phases" in md_text
    assert "| Baseline Integrity |" in md_text
    assert "| Test Suite |" in md_text
    assert "| Explainability |" in md_text

    # 1. Check Section 2 embedding matches ledger
    assert LEDGER_PATH.is_file(), f"Missing {LEDGER_PATH}"
    ledger_text = LEDGER_PATH.read_text(encoding="utf-8").strip()
    assert ledger_text in md_text, "Section 2 does not contain exact overnight_ledger.md contents!"
    if verbose:
        print("[Step 1] Section 2 matches overnight_ledger.md exactly [PASS]")

    # 2. Check Section 3 embedding matches decisions
    assert DECISIONS_PATH.is_file(), f"Missing {DECISIONS_PATH}"
    decisions_text = DECISIONS_PATH.read_text(encoding="utf-8").strip()
    assert decisions_text in md_text, "Section 3 does not contain exact overnight_decisions.md contents!"
    if verbose:
        print("[Step 2] Section 3 matches overnight_decisions.md exactly [PASS]")

    # 3. Check baseline hashes count
    baseline_files = [
        REPO_ROOT / "reports" / "_baseline_hashes_stage2.json",
        REPO_ROOT / "reports" / "_baseline_hashes_tactic.json",
        REPO_ROOT / "reports" / "_baseline_hashes_7ep_stage1.json",
        REPO_ROOT / "reports" / "_baseline_hashes_7ep_eval.json",
        REPO_ROOT / "reports" / "_baseline_hashes_7ep_inference.json",
    ]
    exp_hashes_count = 10  # 10 canonical Stage 1 baseline files
    for bf in baseline_files:
        with open(bf, "r", encoding="utf-8") as f:
            exp_hashes_count += len(json.load(f))
    assert exp_hashes_count == 61
    assert f"{exp_hashes_count}/{exp_hashes_count} protected baseline hashes" in md_text
    assert f"| {exp_hashes_count} SHA-256 baseline hashes | {exp_hashes_count}/{exp_hashes_count} Match |" in md_text
    if verbose:
        print(f"[Step 3] Baseline hashes count ({exp_hashes_count}) verified in summary text and sign-off table [PASS]")

    # 4. Check test counts from latest ledger entry
    ledger_rows = re.findall(
        r"^\|\s*([A-Za-z0-9]+)\s*\|\s*`([a-f0-9]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*([A-Z]+)\s*\|\s*([^|]+)\|",
        ledger_text,
        re.MULTILINE,
    )
    assert ledger_rows, "No rows in ledger"
    latest_verify_exit = int(ledger_rows[-1][2])
    latest_passed = int(ledger_rows[-1][3])
    latest_failed = int(ledger_rows[-1][4])
    assert f"exited with code {latest_verify_exit}" in md_text
    assert f"verifying all {exp_hashes_count} protected hashes and {latest_passed} passed unit/regression tests" in md_text
    assert f"{latest_passed} passed unit/regression tests" in md_text
    assert f"| {latest_passed} passed, {latest_failed} failed |" in md_text
    if verbose:
        print(f"[Step 4] Latest test counts ({latest_passed} passed, {latest_failed} failed) verified [PASS]")

    # 5. Check prediction records count
    with open(RECORDS_PATH, "r", encoding="utf-8") as f:
        exp_records_count = sum(1 for line in f if line.strip())
    assert f"{exp_records_count}/{exp_records_count} explainable LOEO prediction records" in md_text
    assert f"| {exp_records_count}/{exp_records_count} records valid |" in md_text
    if verbose:
        print(f"[Step 5] Prediction records count ({exp_records_count}) verified [PASS]")

    # 6. Check episodes count
    with open(DQR_PATH, "r", encoding="utf-8") as f:
        dqr = json.load(f)
    exp_episodes = len(dqr.get("episodes", {}))
    assert f"all {exp_episodes} empirical attack episodes" in md_text
    if verbose:
        print(f"[Step 6] Episodes count ({exp_episodes}) verified [PASS]")

    # 7. Check NFR1 timing from nfr1_timing.json
    with open(NFR1_PATH, "r", encoding="utf-8") as f:
        nfr_data = json.load(f)
    exp_med = nfr_data["summary_warm"]["median_seconds"]
    exp_p95 = nfr_data["summary_warm"]["p95_seconds"]
    exp_cold = nfr_data["process_cold_start"]["parent_timed_seconds"]

    med_str = f"{exp_med:.4f}s"
    p95_str = f"{exp_p95:.4f}s"
    cold_str = f"{exp_cold:.4f}s"

    assert f"warm median latency of {med_str}" in md_text
    assert f"warm p95 of {p95_str}" in md_text
    assert f"parent-timed process cold start of {cold_str}" in md_text

    assert f"| Timing (NFR1 Warm Median) | End-to-end warm median <= 2.0s | {med_str} |" in md_text
    assert f"| Timing (NFR1 Warm P95) | End-to-end warm p95 <= 5.0s | {p95_str} |" in md_text
    assert f"| Timing (NFR1 Cold Start) | Parent-timed process cold start <= 10.0s | {cold_str} |" in md_text
    if verbose:
        print(f"[Step 7] NFR1 timing metrics ({med_str}, {p95_str}, {cold_str}) verified [PASS]")

    if verbose:
        print("=" * 80)
        print("ALL OVERNIGHT SUMMARY VERIFICATIONS PASSED (Exit 0)")
        print("=" * 80)


if __name__ == "__main__":
    verify_overnight_summary()
