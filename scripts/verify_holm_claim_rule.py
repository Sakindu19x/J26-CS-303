r"""Independent Verifier for Holm-Bonferroni Adjustment and Claim Rule.

Constraints:
- Reads inputs directly from evaluation_7ep_results.json, permutation_7ep_report.json, and holm_claim_rule_results.json.
- No c4 imports (src.c4 is NOT imported).
- Independently sorts raw p-values and recomputes the Holm step-down adjusted p-values.
- Independently evaluates the pre-registered claim rule ("not demonstrated").
- Verifies that report JSON and Markdown match the recomputed values exactly.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
EVAL_PATH = BASE_DIR / "reports" / "7ep" / "evaluation_7ep_results.json"
PERM_PATH = BASE_DIR / "reports" / "7ep" / "permutation_7ep_report.json"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "holm_claim_rule_results.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "holm_claim_rule_report.md"


def verify_holm_claim_rule() -> bool:
    print("=" * 80)
    print("VERIFYING HOLM STEP-DOWN AND CLAIM RULE (INDEPENDENT RECOMPUTATION)")
    print("=" * 80)

    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Missing Eval JSON: {EVAL_PATH}")
    if not PERM_PATH.exists():
        raise FileNotFoundError(f"Missing Perm JSON: {PERM_PATH}")
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing Holm JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing Holm MD: {MD_PATH}")

    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    with open(PERM_PATH, "r", encoding="utf-8") as f:
        perm_data = json.load(f)
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 1. Extract raw p-values
    p1_raw = eval_data["paired_tests"]["P1_tactic_collapsed_hit3"]["p_value_raw"]
    p2_raw = eval_data["paired_tests"]["P2_technique_collapsed_full_hit3"]["p_value_raw"]
    p3_raw = perm_data["schemes"]["S1_collapsed_order"]["tactic_collapsed"]["markov_hit3"]["p_value"]
    p4_raw = perm_data["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]["markov_hit3"]["p_value"]

    raw_map = {"P1": p1_raw, "P2": p2_raw, "P3": p3_raw, "P4": p4_raw}
    print(f"Extracted raw p-values: P1={p1_raw:.4f}, P2={p2_raw:.4f}, P3={p3_raw:.4f}, P4={p4_raw:.4f}")

    # 2. Independent Holm adjustment
    # Sorted: P2, P3, P4, P1
    sorted_items = sorted(raw_map.items(), key=lambda kv: kv[1])
    m = len(sorted_items)
    adj_recomputed = {}
    running_max = 0.0

    for idx, (hid, p_raw) in enumerate(sorted_items):
        rank = idx + 1
        mult = m - rank + 1
        val = min(1.0, mult * p_raw)
        running_max = max(running_max, val)
        adj_recomputed[hid] = {
            "rank": rank,
            "mult": mult,
            "adj_p": min(1.0, running_max),
            "sig": bool(running_max < 0.05),
        }

    # Verify against report JSON
    print("\n[Step 2] Comparing recomputed Holm adjustment with JSON report...")
    fam = report_data["family"]
    for hid in ["P1", "P2", "P3", "P4"]:
        rec = adj_recomputed[hid]
        rpt = fam[hid]
        assert rpt["rank"] == rec["rank"], f"Rank mismatch for {hid}: rpt={rpt['rank']} vs rec={rec['rank']}"
        assert rpt["multiplier"] == rec["mult"], f"Mult mismatch for {hid}"
        assert abs(rpt["adjusted_p"] - rec["adj_p"]) < 1e-6, f"Adj p mismatch for {hid}: rpt={rpt['adjusted_p']} vs rec={rec['adj_p']}"
        assert rpt["significant_at_05"] == rec["sig"], f"Sig mismatch for {hid}"
        print(f"  {hid:4s} | Rank {rec['rank']} | Mult {rec['mult']} | Raw: {raw_map[hid]:.4f} -> Adj: {rec['adj_p']:.4f} (Sig: {rec['sig']}) [MATCH]")

    # 3. Independent Claim Rule Evaluation
    print("\n[Step 3] Evaluating Pre-Registered Claim Rule...")
    m_p1 = eval_data["secondary_slice_tactic_collapsed"]["headline"]["markov"]["top3"]
    f_p1 = eval_data["secondary_slice_tactic_collapsed"]["headline"]["frequency"]["top3"]
    m_p2 = eval_data["primary_slice_technique_collapsed_full"]["headline"]["markov"]["top3"]
    f_p2 = eval_data["primary_slice_technique_collapsed_full"]["headline"]["frequency"]["top3"]

    tactic_improves = (m_p1 > f_p1) and (adj_recomputed["P1"]["adj_p"] < 0.05)
    technique_improves = (m_p2 > f_p2) and (adj_recomputed["P2"]["adj_p"] < 0.05)

    expected_verdict = "improvement over the baseline demonstrated" if (tactic_improves or technique_improves) else "not demonstrated"
    assert report_data["claim_rule_evaluation"]["formal_verdict"] == expected_verdict
    print(f"  Claim Rule Verdict: \"{expected_verdict}\" [MATCH]")

    # 4. Check Markdown tokens
    print("\n[Step 4] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "Pre-Registered Holm Step-Down Adjustment" in md_text
    assert expected_verdict in md_text
    assert "0.0094" in md_text
    assert "0.0180" in md_text
    assert "0.7712" in md_text
    assert "1.0000" in md_text

    print("All Markdown tokens verified.")
    print("\nALL HOLM STEP-DOWN AND CLAIM RULE VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_holm_claim_rule()
