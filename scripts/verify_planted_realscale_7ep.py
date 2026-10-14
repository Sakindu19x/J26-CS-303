r"""Independent Verifier for 7-Episode Real-Scale Planted-Structure Power Analysis (A4 at 7ep).

Constraints:
- Reads ONLY data/processed_7ep/planted_realscale_7ep_predictions.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Recomputes replicate means, standard errors, and reachable fractions (with and without E5) from the CSV.
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

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "planted_realscale_7ep_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "planted_realscale_7ep_report.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "planted_realscale_7ep_report.md"


def verify_planted_realscale_7ep() -> bool:
    print("=" * 80)
    print("VERIFYING 7-EPISODE REAL-SCALE PLANTED STRUCTURE (A4) (INDEPENDENT CSV RECOMPUTATION)")
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
            fold = row["fold"]
            if rep not in reps_data[s_str]:
                reps_data[s_str][rep] = {
                    "m1": 0, "m3": 0, "f1": 0, "f3": 0,
                    "r": 0, "r_no_e5": 0, "broken": 0,
                    "n": 0, "n_no_e5": 0,
                }
            reps_data[s_str][rep]["m1"] += int(row["markov_hit1"])
            reps_data[s_str][rep]["m3"] += int(row["markov_hit3"])
            reps_data[s_str][rep]["f1"] += int(row["frequency_hit1"])
            reps_data[s_str][rep]["f3"] += int(row["frequency_hit3"])
            reps_data[s_str][rep]["broken"] += int(row["broken_markov_hit1"])
            is_reach = int(row["is_reachable"])
            reps_data[s_str][rep]["r"] += is_reach
            reps_data[s_str][rep]["n"] += 1
            if fold != "E5":
                reps_data[s_str][rep]["r_no_e5"] += is_reach
                reps_data[s_str][rep]["n_no_e5"] += 1

    print(f"Read {n_rows} rows from CSV (expected 95000: 95 samples * 200 reps * 5 signal levels).")
    assert n_rows == 95000, f"Expected 95000 rows, got {n_rows}"

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
        r_no_e5_vals = [r["r_no_e5"] / r["n_no_e5"] for r in reps.values()]
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
        r_no_e5_mean = sum(r_no_e5_vals) / n_reps
        broken_mean = sum(broken_vals) / n_reps

        comb_se = math.sqrt(m1_se ** 2 + f1_se ** 2)
        exceeds_2se = bool((m1_mean - f1_mean) > 2.0 * comb_se)

        # Key in JSON uses float representation string ("0.0", "0.25", etc.)
        json_key = str(float(s_str))
        recomputed[json_key] = {
            "s": float(s_str),
            "markov_top1_mean": m1_mean,
            "markov_top1_se": m1_se,
            "markov_top3_mean": m3_mean,
            "markov_top3_se": m3_se,
            "frequency_top1_mean": f1_mean,
            "frequency_top1_se": f1_se,
            "frequency_top3_mean": f3_mean,
            "frequency_top3_se": f3_se,
            "reachable_fraction_mean": r_mean,
            "reachable_fraction_no_e5_mean": r_no_e5_mean,
            "broken_markov_top1_mean": broken_mean,
            "combined_se_m1_f1": comb_se,
            "exceeds_2_combined_se": exceeds_2se,
            "m1_reps": m1_vals,
            "r_reps": r_vals,
        }

        # Compare with JSON
        rpt_row = report_data["results_by_signal"][json_key]
        for field in [
            "markov_top1_mean", "markov_top1_se",
            "markov_top3_mean", "markov_top3_se",
            "frequency_top1_mean", "frequency_top1_se",
            "frequency_top3_mean", "frequency_top3_se",
            "reachable_fraction_mean", "reachable_fraction_no_e5_mean",
            "broken_markov_top1_mean", "combined_se_m1_f1",
        ]:
            diff = abs(rpt_row[field] - recomputed[json_key][field])
            assert diff < 1e-9, f"Mismatch in s={s_str} {field}: rpt={rpt_row[field]} vs rec={recomputed[json_key][field]}"

        assert rpt_row["exceeds_2_combined_se"] == exceeds_2se

        print(
            f"  s={s_str:4s} | M1={m1_mean:.4f}±{m1_se:.4f} | M3={m3_mean:.4f} "
            f"| F1={f1_mean:.4f} | R={r_mean:.4f} | R(no E5)={r_no_e5_mean:.4f} "
            f"| Exceeds 2 SE? {exceeds_2se} [MATCH]"
        )

    # 3. Verify Gates G8, G9, G10, G11
    print("\n[Step 3] Recomputing and verifying Gates G8, G9, G10, G11...")
    chance_top1 = 1.0 / (82 - 1)
    g8_diff = abs(recomputed["0.0"]["markov_top1_mean"] - chance_top1)
    g8_thresh = max(0.02, 3.0 * recomputed["0.0"]["markov_top1_se"])
    g8_pass = bool(g8_diff <= g8_thresh)
    assert g8_pass == report_data["gates"]["G8"]["passed"], "G8 pass mismatch!"
    print(f"  G8: diff={g8_diff:.4f} <= thresh={g8_thresh:.4f} -> {g8_pass} [MATCH]")

    m1_means_seq = [recomputed[str(s)]["markov_top1_mean"] for s in [0.0, 0.25, 0.5, 0.75, 1.0]]
    g9_pass = bool(all(m1_means_seq[i] <= m1_means_seq[i + 1] for i in range(len(m1_means_seq) - 1)))
    assert g9_pass == report_data["gates"]["G9"]["passed"], "G9 pass mismatch!"
    print(f"  G9: trajectory non-decreasing -> {g9_pass} [MATCH]")

    m1_1_reps = recomputed["1.0"]["m1_reps"]
    r_1_reps = recomputed["1.0"]["r_reps"]
    g10_every_le_r = bool(all(m <= r + 1e-9 for m, r in zip(m1_1_reps, r_1_reps)))
    g10_ratio = recomputed["1.0"]["markov_top1_mean"] / recomputed["1.0"]["reachable_fraction_mean"]
    g10_pass = bool(g10_every_le_r and g10_ratio >= 0.99)
    assert g10_pass == report_data["gates"]["G10"]["passed"], "G10 pass mismatch!"
    print(f"  G10: every m1 <= r ({g10_every_le_r}), ratio={g10_ratio:.4f} >= 0.99 -> {g10_pass} [MATCH]")

    broken_ratio = recomputed["1.0"]["broken_markov_top1_mean"] / recomputed["1.0"]["reachable_fraction_mean"]
    g11_pass = bool(not (broken_ratio >= 0.99))
    assert g11_pass == report_data["gates"]["G11"]["passed"], "G11 pass mismatch!"
    print(f"  G11: broken ratio={broken_ratio:.4f} < 0.99 -> {g11_pass} [MATCH]")

    # 4. Verify Markdown report consistency
    print("\n[Step 4] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "Real-Scale Planted-Structure Power Analysis Report (7 Episodes)" in md_text
    assert "82" in md_text
    assert "95" in md_text
    assert "93" in md_text
    assert "G8" in md_text
    assert "G9" in md_text
    assert "G10" in md_text
    assert "G11" in md_text

    for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
        rec = recomputed[s_str]
        m1_tok = f"{rec['markov_top1_mean']:.4f} ± {rec['markov_top1_se']:.4f}"
        f1_tok = f"{rec['frequency_top1_mean']:.4f} ± {rec['frequency_top1_se']:.4f}"
        r_tok = f"{rec['reachable_fraction_mean']:.4f}"
        r_no_e5_tok = f"{rec['reachable_fraction_no_e5_mean']:.4f}"
        for tok in [m1_tok, f1_tok, r_tok, r_no_e5_tok]:
            if tok not in md_text:
                raise ValueError(f"Token '{tok}' (s={s_str}) not found in Markdown report!")

    print("All Markdown tokens verified.")
    print("\nALL 7-EPISODE REAL-SCALE POWER ANALYSIS VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_planted_realscale_7ep()
