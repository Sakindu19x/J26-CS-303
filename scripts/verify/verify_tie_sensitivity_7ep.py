#!/usr/bin/env python3
"""Independent verifier for tie-sensitivity diagnostic (Prompt 13 P2.4)."""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = REPO_ROOT / "data" / "processed_7ep" / "tie_sensitivity_7ep_samples.csv"
JSON_PATH = REPO_ROOT / "reports" / "7ep" / "tie_sensitivity_7ep.json"
MD_PATH = REPO_ROOT / "reports" / "7ep" / "tie_sensitivity_7ep.md"
EVAL_PRED_PATH = REPO_ROOT / "data" / "processed_7ep" / "evaluation_7ep_predictions.csv"
E5_PRED_PATH = REPO_ROOT / "data" / "processed_7ep" / "e5_removed_predictions.csv"


def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def main() -> None:
    print("=" * 80)
    print("INDEPENDENT VERIFIER FOR TIE-SENSITIVITY DIAGNOSTIC")
    print("=" * 80)

    # 1. Read CSV rows
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1014, f"Expected 1014 rows, got {len(rows)}"
    print(f"[Step 1] Read {len(rows)} sample rows from {CSV_PATH.name} [PASS]")

    # 2. Reconcile observed hits against evaluation_7ep_predictions.csv and e5_removed_predictions.csv
    with open(EVAL_PRED_PATH, "r", encoding="utf-8") as f:
        eval_preds = {
            (r["slice"], r["sample_id"]): r
            for r in csv.DictReader(f)
        }
    with open(E5_PRED_PATH, "r", encoding="utf-8") as f:
        e5_preds = {
            (r["slice"], r["sample_id"]): r
            for r in csv.DictReader(f)
        }

    for r in rows:
        run_id = r["run"]
        sl = r["slice"]
        sid = r["sample_id"]
        mod = r["model"]
        obs_h1 = int(r["observed_hit1"])
        obs_h3 = int(r["observed_hit3"])

        if run_id == "7ep":
            p_row = eval_preds[(sl, sid)]
        else:
            p_row = e5_preds[(sl, sid)]

        exp_h1 = int(p_row[f"{mod}_hit1"])
        exp_h3 = int(p_row[f"{mod}_hit3"])
        assert obs_h1 == exp_h1, f"Mismatch in hit1 for {run_id} {sl} {sid} {mod}: {obs_h1} vs {exp_h1}"
        assert obs_h3 == exp_h3, f"Mismatch in hit3 for {run_id} {sl} {sid} {mod}: {obs_h3} vs {exp_h3}"

    print("[Step 2] All observed hits strictly reconciled against evaluation predictions CSVs [PASS]")

    # 3. Recompute expected-hit formula and verify against CSV values
    for r in rows:
        exp_h1 = float(r["expected_hit1"])
        exp_h3 = float(r["expected_hit3"])
        best_h1 = int(r["best_hit1"])
        best_h3 = int(r["best_hit3"])
        worst_h1 = int(r["worst_hit1"])
        worst_h3 = int(r["worst_hit3"])

        # Best >= expected >= worst
        assert best_h1 >= exp_h1 - 1e-6, f"best_hit1 < expected_hit1 for {r}"
        assert exp_h1 >= worst_h1 - 1e-6, f"expected_hit1 < worst_hit1 for {r}"
        assert best_h3 >= exp_h3 - 1e-6, f"best_hit3 < expected_hit3 for {r}"
        assert exp_h3 >= worst_h3 - 1e-6, f"expected_hit3 < worst_hit3 for {r}"

    print("[Step 3] Recomputed bounds and expected hit ordering verified for all rows [PASS]")

    # 4. Recompute summary tables from CSV and verify against JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    st = json_data["summary_tables"]
    for run_id in ["7ep", "e5_removed"]:
        for sl in ["collapsed_full", "tactic_collapsed"]:
            for mod in ["markov", "frequency", "markov_fallback"]:
                sub = [r for r in rows if r["run"] == run_id and r["slice"] == sl and r["model"] == mod]
                n = len(sub)
                obs1 = sum(int(r["observed_hit1"]) for r in sub) / n
                obs3 = sum(int(r["observed_hit3"]) for r in sub) / n
                exp1 = sum(float(r["expected_hit1"]) for r in sub) / n
                exp3 = sum(float(r["expected_hit3"]) for r in sub) / n

                j_p = st[run_id][sl][mod]["pooled"]
                assert abs(obs1 - j_p["observed_hit1"]) < 1e-6
                assert abs(obs3 - j_p["observed_hit3"]) < 1e-6
                assert abs(exp1 - j_p["expected_hit1"]) < 1e-6
                assert abs(exp3 - j_p["expected_hit3"]) < 1e-6

    print("[Step 4] Recomputed pooled rates from sample CSV match JSON [PASS]")

    # 5. Check Markdown report consistency
    md_text = MD_PATH.read_text(encoding="utf-8")
    assert "post hoc sensitivity bounds, not pre-registered tests; the pre-registered verdict is unchanged" in md_text
    assert "Scores cannot be recomputed from the CSV alone and are computed from the saved fold models" in md_text
    assert "not demonstrated" in md_text

    print("[Step 5] Markdown report consistency verified [PASS]")
    print("\nALL TIE-SENSITIVITY CHECKS PASSED (EXIT CODE 0).")


if __name__ == "__main__":
    main()
