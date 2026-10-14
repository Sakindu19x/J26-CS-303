r"""Independent Verifier for Permutation Test on Real Episodes (Part B).

Constraints:
- Reads ONLY data/processed/permutation_null_distribution.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Recomputes all null statistics (mean, SD, 2.5th and 97.5th percentiles, min, max).
- Recomputes empirical one-sided p-values.
- Verifies that report JSON and Markdown match the recomputed values exactly.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "reports" / "archive" / "permutation_null_distribution_v1_counts_superseded.csv"
JSON_PATH = BASE_DIR / "reports" / "archive" / "permutation_test_report_v1_counts_superseded.json"
MD_PATH = BASE_DIR / "reports" / "archive" / "permutation_test_report_v1_counts_superseded.md"


def percentile_linear(data: list[float], p: float) -> float:
    """Compute percentile using linear interpolation matching numpy.percentile."""
    sorted_d = sorted(data)
    n = len(sorted_d)
    if n == 0:
        return 0.0
    if n == 1:
        return float(sorted_d[0])
    idx = (n - 1) * p / 100.0
    low = int(idx)
    high = min(low + 1, n - 1)
    weight = idx - low
    return float(sorted_d[low] * (1.0 - weight) + sorted_d[high] * weight)


def compute_summary_stats(observed: float, null_values: list[float]) -> dict[str, Any]:
    b = len(null_values)
    mean_val = sum(null_values) / b
    var = sum((x - mean_val) ** 2 for x in null_values) / (b - 1) if b > 1 else 0.0
    sd_val = math.sqrt(var)
    p2_5 = percentile_linear(null_values, 2.5)
    p97_5 = percentile_linear(null_values, 97.5)
    min_val = min(null_values)
    max_val = max(null_values)
    n_ge = sum(1 for x in null_values if x >= observed)
    p_val = (1.0 + n_ge) / (1.0 + b)
    interpretation = (
        "order carries detectable signal under this null"
        if p_val < 0.05
        else "no detectable order signal at this sample size (this is not proof of absence)"
    )
    return {
        "observed": observed,
        "null_mean": mean_val,
        "null_sd": sd_val,
        "null_p2_5": p2_5,
        "null_p97_5": p97_5,
        "null_min": min_val,
        "null_max": max_val,
        "n_ge_observed": n_ge,
        "b_permutations": b,
        "p_value": p_val,
        "interpretation": interpretation,
    }


def verify_permutation_test() -> bool:
    print("=" * 80)
    print("VERIFYING PERMUTATION TEST (INDEPENDENT CSV RECOMPUTATION)")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    # Load report JSON
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 1. Read CSV
    print("\n[Step 1] Reading CSV and grouping null distribution rows...")
    null_data: dict[str, dict[str, dict[str, list[float]]]] = {
        "technique_collapsed_full": {
            "markov": {"hit1": [], "hit3": []},
            "frequency": {"hit1": [], "hit3": []},
            "markov_fallback": {"hit1": [], "hit3": []},
            "markov_minus_frequency": {"hit1": [], "hit3": []},
        },
        "tactic_collapsed": {
            "markov": {"hit1": [], "hit3": []},
            "frequency": {"hit1": [], "hit3": []},
            "markov_fallback": {"hit1": [], "hit3": []},
            "markov_minus_frequency": {"hit1": [], "hit3": []},
        },
    }

    n_rows = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_rows += 1
            lvl = row["level"]
            mth = row["method"]
            h1 = float(row["hit1"])
            h3 = float(row["hit3"])
            null_data[lvl][mth]["hit1"].append(h1)
            null_data[lvl][mth]["hit3"].append(h3)

    print(f"Read {n_rows} rows from CSV successfully.")

    # 2. Recompute statistics and verify against JSON
    print("\n[Step 2] Recomputing null statistics and verifying against report JSON...")
    levels = ["technique_collapsed_full", "tactic_collapsed"]
    methods = ["markov", "frequency", "markov_fallback", "markov_minus_frequency"]
    metrics = ["hit1", "hit3"]

    for lvl in levels:
        print(f"\nLevel: {lvl}")
        for mth in methods:
            for met in metrics:
                rpt_stat = report_data["statistics"][lvl][mth][met]
                obs_val = rpt_stat["observed"]
                null_vals = null_data[lvl][mth][met]

                rec_stat = compute_summary_stats(obs_val, null_vals)

                # Assert matching values
                for k in ["null_mean", "null_sd", "null_p2_5", "null_p97_5", "p_value"]:
                    diff = abs(rpt_stat[k] - rec_stat[k])
                    if diff > 1e-7:
                        raise ValueError(f"Mismatch in {lvl} {mth} {met} {k}: rpt={rpt_stat[k]} vs rec={rec_stat[k]}")

                for k in ["null_min", "null_max", "n_ge_observed", "b_permutations"]:
                    if rpt_stat[k] != rec_stat[k]:
                        raise ValueError(f"Mismatch in {lvl} {mth} {met} {k}: rpt={rpt_stat[k]} vs rec={rec_stat[k]}")

                if rpt_stat["interpretation"] != rec_stat["interpretation"]:
                    raise ValueError(f"Interpretation mismatch in {lvl} {mth} {met}!")

                print(
                    f"  {mth:22s} {met:4s} | Obs: {obs_val:+2.0f} | Null Mean: {rec_stat['null_mean']:7.4f} "
                    f"| SD: {rec_stat['null_sd']:6.4f} | p-value: {rec_stat['p_value']:.4f} [MATCH]"
                )

    # 3. Check Markdown report consistency
    print("\n[Step 3] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Verify key tokens in markdown
    for lvl in levels:
        for mth in methods:
            for met in metrics:
                stat = report_data["statistics"][lvl][mth][met]
                p_token = f"{stat['p_value']:.4f}"
                mean_token = f"{stat['null_mean']:.4f}"
                sd_token = f"{stat['null_sd']:.4f}"
                for tok in [p_token, mean_token, sd_token]:
                    if tok not in md_text:
                        raise ValueError(f"Token '{tok}' ({lvl} {mth} {met}) not found in Markdown report!")

    print("All Markdown tokens verified.")
    print("\nALL PERMUTATION TEST VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_permutation_test()
