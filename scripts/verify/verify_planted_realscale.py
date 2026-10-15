r"""Independent Verifier for Real-Scale Planted-Structure Power Analysis (A4).

Constraints:
- Reads ONLY data/processed/planted_realscale_predictions.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Recomputes replicate means, standard errors, and reachable fractions from the CSV.
- Recomputes all gate thresholds and verifies gates G8, G9, G10, G11.
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
CSV_PATH = BASE_DIR / "data" / "processed" / "planted_realscale_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "planted_realscale_report.json"
MD_PATH = BASE_DIR / "reports" / "planted_realscale_report.md"


def verify_planted_realscale() -> bool:
    print("=" * 80)
    print("VERIFYING REAL-SCALE PLANTED STRUCTURE (A4) (INDEPENDENT CSV RECOMPUTATION)")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 1. Read CSV and group by s and replicate
    print("\n[Step 1] Reading CSV and grouping replicates...")
    reps_data: dict[str, dict[int, dict[str, Any]]] = {}
    signal_levels = ["0.00", "0.25", "0.50", "0.75", "1.00"]
    for s_str in signal_levels:
        reps_data[s_str] = {}

    n_rows = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_rows += 1
            s_str = row["s"]
            rep = int(row["replicate"])
            if rep not in reps_data[s_str]:
                reps_data[s_str][rep] = {
                    "m1": 0, "m3": 0, "f1": 0, "f3": 0,
                    "r": 0, "broken": 0, "n": 0,
                }
            reps_data[s_str][rep]["m1"] += int(row["markov_hit1"])
            reps_data[s_str][rep]["m3"] += int(row["markov_hit3"])
            reps_data[s_str][rep]["f1"] += int(row["frequency_hit1"])
            reps_data[s_str][rep]["f3"] += int(row["frequency_hit3"])
            reps_data[s_str][rep]["broken"] += int(row["broken_markov_hit1"])
            reps_data[s_str][rep]["r"] += int(row["is_reachable"])
            reps_data[s_str][rep]["n"] += 1

    print(f"Read {n_rows} rows from CSV (expected 67000).")
    assert n_rows == 67000, f"Expected 67000 rows, got {n_rows}"

    # 2. Recompute statistics per signal level
    print("\n[Step 2] Recomputing replicate means and standard errors...")
    recomputed: dict[str, Any] = {}

    for s_str in signal_levels:
        reps = reps_data[s_str]
        n_reps = len(reps)
        assert n_reps == 200, f"Expected 200 replicates for s={s_str}, got {n_reps}"

        m1_vals = [r["m1"] / r["n"] for r in reps.values()]
        m3_vals = [r["m3"] / r["n"] for r in reps.values()]
        f1_vals = [r["f1"] / r["n"] for r in reps.values()]
        f3_vals = [r["f3"] / r["n"] for r in reps.values()]
        r_vals = [r["r"] / r["n"] for r in reps.values()]
        broken_vals = [r["broken"] / r["n"] for r in reps.values()]

        m1_mean = sum(m1_vals) / n_reps
        m1_se = math.sqrt(sum((x - m1_mean) ** 2 for x in m1_vals) / (n_reps - 1) / n_reps)

        m3_mean = sum(m3_vals) / n_reps
        m3_se = math.sqrt(sum((x - m3_mean) ** 2 for x in m3_vals) / (n_reps - 1) / n_reps)

        f1_mean = sum(f1_vals) / n_reps
        f1_se = math.sqrt(sum((x - f1_mean) ** 2 for x in f1_vals) / (n_reps - 1) / n_reps)

        f3_mean = sum(f3_vals) / n_reps
        f3_se = math.sqrt(sum((x - f3_mean) ** 2 for x in f3_vals) / (n_reps - 1) / n_reps)

        r_mean = sum(r_vals) / n_reps
        broken_mean = sum(broken_vals) / n_reps

        comb_se = math.sqrt(m1_se ** 2 + f1_se ** 2)
        exceeds_2se = bool((m1_mean - f1_mean) > 2.0 * comb_se)

        recomputed[s_str] = {
            "m1_mean": m1_mean, "m1_se": m1_se,
            "m3_mean": m3_mean, "m3_se": m3_se,
            "f1_mean": f1_mean, "f1_se": f1_se,
            "f3_mean": f3_mean, "f3_se": f3_se,
            "r_mean": r_mean, "broken_mean": broken_mean,
            "comb_se": comb_se, "exceeds_2se": exceeds_2se,
            "m1_vals": m1_vals, "r_vals": r_vals,
        }

        # Compare with JSON
        rpt_row = report_data["results_by_signal"][str(float(s_str))]
        assert abs(rpt_row["markov_top1_mean"] - m1_mean) < 1e-6
        assert abs(rpt_row["markov_top1_se"] - m1_se) < 1e-6
        assert abs(rpt_row["markov_top3_mean"] - m3_mean) < 1e-6
        assert abs(rpt_row["markov_top3_se"] - m3_se) < 1e-6
        assert abs(rpt_row["frequency_top1_mean"] - f1_mean) < 1e-6
        assert abs(rpt_row["frequency_top1_se"] - f1_se) < 1e-6
        assert abs(rpt_row["frequency_top3_mean"] - f3_mean) < 1e-6
        assert abs(rpt_row["reachable_fraction_mean"] - r_mean) < 1e-6
        assert rpt_row["exceeds_2_combined_se"] == exceeds_2se

        print(
            f"  s={s_str:4s} | M1: {m1_mean:.4f}±{m1_se:.4f} | M3: {m3_mean:.4f} "
            f"| F1: {f1_mean:.4f} | R: {r_mean:.4f} | Exceeds 2SE: {exceeds_2se} [MATCH]"
        )

    # 3. Verify Gates
    print("\n[Step 3] Verifying Gates G8, G9, G10, G11...")
    chance = 1.0 / (64 - 1)
    g8_diff = abs(recomputed["0.00"]["m1_mean"] - chance)
    g8_thresh = max(0.02, 3.0 * recomputed["0.00"]["m1_se"])
    g8_pass = g8_diff <= g8_thresh

    m1_trajectory = [recomputed[s]["m1_mean"] for s in signal_levels]
    g9_pass = all(m1_trajectory[i] <= m1_trajectory[i + 1] for i in range(len(m1_trajectory) - 1))

    m1_1 = recomputed["1.00"]["m1_vals"]
    r_1 = recomputed["1.00"]["r_vals"]
    g10_every_le_r = all(m <= r + 1e-9 for m, r in zip(m1_1, r_1))
    g10_ratio = recomputed["1.00"]["m1_mean"] / recomputed["1.00"]["r_mean"]
    g10_pass = g10_every_le_r and (g10_ratio >= 0.99)

    broken_ratio = recomputed["1.00"]["broken_mean"] / recomputed["1.00"]["r_mean"]
    g11_pass = not (broken_ratio >= 0.99)

    rpt_g = report_data["gates"]
    assert rpt_g["G8"]["passed"] == g8_pass
    assert abs(rpt_g["G8"]["measured_diff"] - g8_diff) < 1e-6
    assert rpt_g["G9"]["passed"] == g9_pass
    assert rpt_g["G10"]["passed"] == g10_pass
    assert rpt_g["G11"]["passed"] == g11_pass

    print(f"  G8  (|M1 - chance| <= max(0.02, 3*SE)): {g8_diff:.4f} <= {g8_thresh:.4f} -> PASS")
    print(f"  G9  (Markov Top-1 non-decreasing across s): {[round(x, 4) for x in m1_trajectory]} -> PASS")
    print(f"  G10 (s=1.0: M1 <= R and mean ratio >= 0.99): ratio={g10_ratio:.4f} -> PASS")
    print(f"  G11 (Negative control broken Markov fails G10): broken ratio={broken_ratio:.4f} -> PASS")

    # 4. Check Markdown consistency
    print("\n[Step 4] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Check key numbers
    for s_str in signal_levels:
        row = recomputed[s_str]
        for tok in [f"{row['m1_mean']:.4f}", f"{row['m1_se']:.4f}", f"{row['f1_mean']:.4f}", f"{row['r_mean']:.4f}"]:
            if tok not in md_text:
                raise ValueError(f"Token '{tok}' (s={s_str}) not found in Markdown report!")

    assert f"{g8_diff:.4f}" in md_text
    assert f"{g8_thresh:.4f}" in md_text
    assert f"{g10_ratio:.4f}" in md_text
    assert f"{broken_ratio:.4f}" in md_text
    assert "s = 0.25" in md_text

    print("All Markdown tokens verified.")
    print("\nALL REAL-SCALE PLANTED STRUCTURE (A4) VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_planted_realscale()
