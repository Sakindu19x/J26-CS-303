"""Independent verifier for E5 Hit@1 Change Diagnostic.

Constraints:
- Reads reports/7ep/e5_hit1_change_diagnostic.{json,md}.
- Does NOT import from src/c4.
- Verifies exact accounting sums and consistency between JSON and Markdown.
- Verifies that all 7 Markov differing sample IDs are present and accurate.
- Verifies that Frequency differing count is 0.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
JSON_PATH = BASE_DIR / "reports" / "7ep" / "e5_hit1_change_diagnostic.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "e5_hit1_change_diagnostic.md"

EXPECTED_MARKOV_DIFF_SAMPLES = [
    "E2-tac-col-K05",
    "E2-tac-col-K07",
    "E2-tac-col-K08",
    "E2-tac-col-K11",
    "E2-tac-col-K13",
    "E3-tac-col-K01",
    "E3-tac-col-K04",
]


def verify_e5_hit1_diagnostic() -> bool:
    print("================================================================================")
    print("VERIFYING E5 HIT@1 CHANGE DIAGNOSTIC")
    print("================================================================================")

    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    acc = meta["summary_accounting"]
    m_diffs = data["markov_differing_samples"]
    f_diffs = data["frequency_differing_samples"]

    # 1. Accounting invariants
    print("\n[Step 1] Verifying accounting invariants...")
    assert acc["markov_total_hits_7ep"] == 22
    assert acc["markov_total_samples_7ep"] == 76
    assert acc["markov_e5_test_hits"] == 1
    assert acc["markov_e5_test_samples"] == 2
    assert acc["markov_hits_6ep_in_7ep_run"] == 21
    assert acc["markov_hits_6ep_in_e5_removed_run"] == 18
    assert acc["markov_hits_difference_in_6ep"] == -3
    assert acc["frequency_hits_6ep_in_7ep_run"] == 13
    assert acc["frequency_hits_6ep_in_e5_removed_run"] == 13
    assert acc["frequency_hits_difference_in_6ep"] == 0

    assert acc["markov_hits_6ep_in_7ep_run"] + acc["markov_e5_test_hits"] == acc["markov_total_hits_7ep"]
    print("  All accounting invariants verified [PASS]")

    # 2. Differing sample count and IDs
    print("\n[Step 2] Verifying differing sample IDs...")
    assert len(m_diffs) == 7
    found_ids = [d["sample_id"] for d in m_diffs]
    assert found_ids == EXPECTED_MARKOV_DIFF_SAMPLES, f"Mismatch in sample IDs: {found_ids} != {EXPECTED_MARKOV_DIFF_SAMPLES}"

    # Verify tie flags
    for d in m_diffs:
        sid = d["sample_id"]
        assert d["tied_7ep"] == "no", f"{sid} unexpected 7ep tie: {d['tied_7ep']}"
        if sid == "E3-tac-col-K01":
            assert d["tied_no_e5"] == "no"
        else:
            assert d["tied_no_e5"] == "yes", f"{sid} expected no-e5 tie: {d['tied_no_e5']}"

    assert len(f_diffs) == 0
    print("  All 7 Markov differing samples and 0 Frequency differing samples verified [PASS]")

    # 3. Markdown report consistency
    print("\n[Step 3] Verifying Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "# E5-Removed Tactic Hit@1 Change Diagnostic" in md_text
    assert "diagnostic, not a pre-registered test" in md_text
    assert "22 / 76 (0.2895)" in md_text
    assert "18 / 74 hits (0.2432)" in md_text
    assert "Net difference in other folds: -3 hits" in md_text

    for sid in EXPECTED_MARKOV_DIFF_SAMPLES:
        assert sid in md_text, f"Sample ID {sid} missing from markdown table!"

    assert "Total samples with differing Markov top-1 prediction or Hit@1: **7**" in md_text
    assert "Total samples with differing Frequency top-1 prediction or Hit@1: **0**" in md_text

    print("  All Markdown tokens verified [PASS]")
    print("\n================================================================================")
    print("ALL E5 HIT@1 DIAGNOSTIC VERIFICATIONS PASSED (EXIT CODE 0)")
    print("================================================================================")
    return True


if __name__ == "__main__":
    verify_e5_hit1_diagnostic()
