"""tests/test_record_baseline_change.py (Prompt 15 R1).

Validates:
1. Numeric leaf extraction across JSON, CSV, and Markdown.
2. Leaf comparison logic (identical, changed, added, removed).
3. The verification rule: "VERIFIED" only when CHANGED = 0 and added/removed justified.
4. Integrity of reports/audit/q15_baseline_changes.md:
   - Corrected McNemar b=3, c=11 (p=0.0574)
   - 5 added exploratory leaves and post hoc disclosure
   - All three Prompt 14 changes listed with VERIFIED verdict.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from record_baseline_change import (
    compare_leaves,
    extract_csv_leaves,
    extract_json_leaves,
    extract_md_leaves,
    verify_diff,
)


def test_extract_json_leaves():
    obj = {
        "metrics": {"top1": 0.0526, "hit1": 5, "tied": True, "note": "exploratory"},
        "folds": [
            {"fold_id": "E1", "score": 1.5},
            {"fold_id": "E2", "score": 2.5},
        ],
    }
    leaves = extract_json_leaves(obj)
    assert leaves["metrics.top1"] == 0.0526
    assert leaves["metrics.hit1"] == 5
    assert "metrics.tied" not in leaves  # bool ignored
    assert "metrics.note" not in leaves  # str ignored
    assert leaves["folds[0].score"] == 1.5
    assert leaves["folds[1].score"] == 2.5


def test_extract_csv_leaves():
    csv_text = "sample_id,hit1,score,status\nE1-01,1,0.75,ok\nE1-02,0,0.25,ok\n"
    leaves = extract_csv_leaves(csv_text)
    assert leaves["row[1].hit1"] == 1.0
    assert leaves["row[1].score"] == 0.75
    assert leaves["row[2].hit1"] == 0.0
    assert leaves["row[2].score"] == 0.25
    assert "row[1].status" not in leaves


def test_extract_md_leaves():
    md_text = (
        "# Summary 2026-10-15\n"
        "Hit@1 = 5/95 (5.26%) across 7 episodes.\n"
        "Date 2026-09-22 excluded.\n"
    )
    leaves = extract_md_leaves(md_text)
    vals = list(leaves.values())
    assert "5" in vals
    assert "95" in vals
    assert "5.26%" in vals
    assert "7" in vals
    assert "2026-10-15" not in vals
    assert "2026-09-22" not in vals


def test_compare_and_verification_rule():
    old = {"a": 10, "b": 20}
    new_clean = {"a": 10, "b": 20, "c": 30}
    diff = compare_leaves(old, new_clean)
    assert len(diff["identical"]) == 2
    assert len(diff["changed"]) == 0
    assert len(diff["added"]) == 1

    # Unjustified addition fails
    ok, msg = verify_diff(diff, added_rationales={}, removed_rationales={})
    assert not ok
    assert "UNVERIFIED" in msg

    # Justified addition passes
    ok, msg = verify_diff(diff, added_rationales={"c": "Added new feature count"}, removed_rationales={})
    assert ok
    assert msg == "VERIFIED"

    # Changed leaf fails even with rationale
    new_changed = {"a": 15, "b": 20}
    diff_changed = compare_leaves(old, new_changed)
    ok, msg = verify_diff(diff_changed, added_rationales={}, removed_rationales={})
    assert not ok
    assert "UNVERIFIED" in msg


def test_q15_baseline_changes_file_contents():
    path = REPO_ROOT / "reports" / "audit" / "q15_baseline_changes.md"
    assert path.is_file(), f"Missing {path}"
    content = path.read_text(encoding="utf-8")

    # 1. Verification verdicts
    assert "**VERIFIED**" in content

    # 2. Recomputed McNemar contingency from CSV
    assert "b=3, c=11" in content
    assert "0.0574" in content
    assert "b=5, c=7" in content

    # 3. Post hoc disclosure for exploratory report
    assert "added post hoc after results were seen" in content
    assert "F3_unseen_state_rate" in content
    assert "35.79%" in content

    # 4. All three Prompt 14 changes
    assert "reports/7ep/exploratory_tactic_conditioned_report.md" in content
    assert "data/processed_7ep/prediction_records_loeo.jsonl" in content
    assert "reports/7ep/requirements_trace.md" in content
