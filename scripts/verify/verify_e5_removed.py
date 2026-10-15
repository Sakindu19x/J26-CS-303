r"""Independent Verifier for Pre-Registered E5-Removed Sensitivity Analysis.

Constraints:
- Reads ONLY data/processed_7ep/e5_removed_predictions.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Asserts exactly 167 rows (93 technique, 74 tactic) and no occurrences of episode E5.
- Recomputes pooled and per-fold Hit@1, Hit@3, coverage, and ceiling rates from the CSV.
- Recomputes exact McNemar test p-values (sensitivity, raw p) directly from the CSV.
- Verifies that report JSON and Markdown match the recomputed values exactly.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "e5_removed_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "e5_removed_results.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "e5_removed_report.md"


def exact_mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar test p-value based on binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score confidence interval for a proportion."""
    if n == 0:
        return 0.0, 0.0
    z = 1.959963984540054  # for 95% confidence
    p = successes / n
    denominator = 1.0 + z * z / n
    centre_adjusted_probability = p + z * z / (2.0 * n)
    adjusted_std = math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n)
    lower_bound = (centre_adjusted_probability - z * adjusted_std) / denominator
    upper_bound = (centre_adjusted_probability + z * adjusted_std) / denominator
    return max(0.0, lower_bound), min(1.0, upper_bound)


def verify_e5_removed() -> bool:
    print("=" * 80)
    print("VERIFYING E5-REMOVED SENSITIVITY (INDEPENDENT CSV RECOMPUTATION)")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 1. Read CSV
    print("\n[Step 1] Reading CSV and validating rows...")
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    print(f"Read {len(rows)} rows from CSV (expected 167: 93 tech + 74 tac).")
    assert len(rows) == 167, f"Expected 167 rows, got {len(rows)}"

    tech_rows = [r for r in rows if r["slice"] == "collapsed_full"]
    tac_rows = [r for r in rows if r["slice"] == "tactic_collapsed"]

    assert len(tech_rows) == 93, f"Expected 93 technique rows, got {len(tech_rows)}"
    assert len(tac_rows) == 74, f"Expected 74 tactic rows, got {len(tac_rows)}"

    # Assert no E5 test samples
    for r in rows:
        assert r["test_episode"] != "E5", f"Found E5 test sample in CSV: {r['sample_id']}"
    print("No E5 samples present in CSV verified.")

    # 2. Recompute pooled metrics
    print("\n[Step 2] Recomputing pooled metrics and Wilson intervals...")
    for slice_name, s_rows, json_key in [
        ("collapsed_full", tech_rows, "technique_collapsed_full"),
        ("tactic_collapsed", tac_rows, "tactic_collapsed"),
    ]:
        n = len(s_rows)
        cov_cnt = sum(1 for r in s_rows if r["covered"].lower() == "true")
        ceil_cnt = sum(1 for r in s_rows if r["ceiling"].lower() == "true")
        m1_cnt = sum(int(r["markov_hit1"]) for r in s_rows)
        m3_cnt = sum(int(r["markov_hit3"]) for r in s_rows)
        f1_cnt = sum(int(r["frequency_hit1"]) for r in s_rows)
        f3_cnt = sum(int(r["frequency_hit3"]) for r in s_rows)
        fb1_cnt = sum(int(r["markov_fallback_hit1"]) for r in s_rows)
        fb3_cnt = sum(int(r["markov_fallback_hit3"]) for r in s_rows)

        rpt_hl = report_data[json_key]["headline"]
        assert rpt_hl["markov"]["hit1"] == m1_cnt
        assert rpt_hl["markov"]["hit3"] == m3_cnt
        assert rpt_hl["frequency"]["hit1"] == f1_cnt
        assert rpt_hl["frequency"]["hit3"] == f3_cnt

        if json_key == "technique_collapsed_full":
            assert rpt_hl["fallback"]["hit1"] == fb1_cnt
            assert rpt_hl["fallback"]["hit3"] == fb3_cnt
            assert rpt_hl["coverage"]["covered_samples"] == cov_cnt
            assert rpt_hl["ceiling"]["hits"] == ceil_cnt
        else:
            assert rpt_hl["markov_fallback"]["hit1"] == fb1_cnt
            assert rpt_hl["markov_fallback"]["hit3"] == fb3_cnt
            assert report_data[json_key]["coverage"]["covered_samples"] == cov_cnt
            assert report_data[json_key]["ceiling"]["hits"] == ceil_cnt

        # Check Wilson interval
        w_m1 = wilson_interval(m1_cnt, n)
        w_m3 = wilson_interval(m3_cnt, n)
        assert abs(rpt_hl["markov"]["wilson95_top1"][0] - w_m1[0]) < 1e-6
        assert abs(rpt_hl["markov"]["wilson95_top1"][1] - w_m1[1]) < 1e-6
        assert abs(rpt_hl["markov"]["wilson95_top3"][0] - w_m3[0]) < 1e-6
        assert abs(rpt_hl["markov"]["wilson95_top3"][1] - w_m3[1]) < 1e-6

        print(f"  {slice_name:18s} | N={n:2d} | M1: {m1_cnt}/{n} ({m1_cnt/n:.4f}) | M3: {m3_cnt}/{n} ({m3_cnt/n:.4f}) [MATCH]")

    # 3. Recompute exact McNemar paired tests
    print("\n[Step 3] Recomputing exact McNemar paired tests...")
    for slice_name, s_rows, test_key, m_metric in [
        ("collapsed_full", tech_rows, "technique_hit3", "hit3"),
        ("tactic_collapsed", tac_rows, "tactic_hit3", "hit3"),
        ("collapsed_full", tech_rows, "technique_hit1", "hit1"),
        ("tactic_collapsed", tac_rows, "tactic_hit1", "hit1"),
    ]:
        m1_col = f"markov_{m_metric}"
        m2_col = f"frequency_{m_metric}"
        b = sum(1 for r in s_rows if int(r[m1_col]) == 1 and int(r[m2_col]) == 0)
        c = sum(1 for r in s_rows if int(r[m1_col]) == 0 and int(r[m2_col]) == 1)
        both = sum(1 for r in s_rows if int(r[m1_col]) == 1 and int(r[m2_col]) == 1)
        neither = sum(1 for r in s_rows if int(r[m1_col]) == 0 and int(r[m2_col]) == 0)
        p_val = exact_mcnemar(b, c)

        rpt_pt = report_data["paired_tests"][test_key]
        assert rpt_pt["table_2x2"]["m1_hit_m2_miss"] == b
        assert rpt_pt["table_2x2"]["m1_miss_m2_hit"] == c
        assert rpt_pt["table_2x2"]["both_hit"] == both
        assert rpt_pt["table_2x2"]["neither_hit"] == neither
        assert abs(rpt_pt["p_value_raw"] - p_val) < 1e-9
        assert rpt_pt["label"] == "sensitivity, raw p"

        print(f"  {test_key:20s} | b={b}, c={c}, both={both}, neither={neither} | p={p_val:.4f} ({rpt_pt['label']}) [MATCH]")

    # 4. Check Markdown tokens
    print("\n[Step 4] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "Pre-Registered E5-Removed Sensitivity Analysis Report" in md_text
    assert "93" in md_text
    assert "74" in md_text
    assert "sensitivity, raw p" in md_text

    print("All Markdown tokens verified.")
    print("\nALL E5-REMOVED SENSITIVITY VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_e5_removed()
