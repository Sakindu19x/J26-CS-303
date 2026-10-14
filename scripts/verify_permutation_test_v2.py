r"""Independent Verifier for Permutation Test on Real Episodes v2.1.

Constraints:
- Reads ONLY data/processed/permutation_v2_null_distribution.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Recomputes all null statistics (mean, SD, 2.5th and 97.5th percentiles, min, max).
- Recomputes empirical one-sided p-values: p = (1 + count(null >= observed)) / (1 + B).
- Verifies that report JSON and Markdown match the recomputed values exactly.
- Verifies that N is constant (67 technique, 53 tactic) under S1 and S3.
- Verifies that Scheme Validity Warnings are present if and only if an order-free Frequency statistic has p < 0.05.
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
CSV_PATH = BASE_DIR / "data" / "processed" / "permutation_v2_null_distribution.csv"
JSON_PATH = BASE_DIR / "reports" / "permutation_test_v2_report.json"
MD_PATH = BASE_DIR / "reports" / "permutation_test_v2_report.md"


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
    mean_val = sum(null_values) / b if b > 0 else 0.0
    var = sum((x - mean_val) ** 2 for x in null_values) / (b - 1) if b > 1 else 0.0
    sd_val = math.sqrt(var)
    p2_5 = percentile_linear(null_values, 2.5) if b > 0 else 0.0
    p97_5 = percentile_linear(null_values, 97.5) if b > 0 else 0.0
    min_val = min(null_values) if b > 0 else 0.0
    max_val = max(null_values) if b > 0 else 0.0
    n_ge = sum(1 for x in null_values if x >= observed - 1e-12)
    p_val = (1.0 + n_ge) / (1.0 + b)
    if p_val < 0.05:
        conclusion = f"observed exceeds the shuffled-order null (p={p_val:.4f})"
    else:
        conclusion = f"not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p={p_val:.4f})"

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
        "conclusion": conclusion,
    }


def verify_permutation_test_v2() -> bool:
    print("=" * 80)
    print("VERIFYING PERMUTATION TEST v2.1 (INDEPENDENT CSV RECOMPUTATION)")
    print("=" * 80)

    if not CSV_PATH.exists():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not JSON_PATH.exists():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.exists():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # 1. Read CSV and group values
    print("\n[Step 1] Reading CSV and grouping null distributions...")
    schemes = ["S1_collapsed_order", "S3_constrained_shuffle", "S2_raw_shuffle_rate"]
    levels = ["technique_collapsed_full", "tactic_collapsed"]
    stats_keys = [
        "markov_hit1", "markov_hit3",
        "frequency_hit1", "frequency_hit3",
        "markov_fallback_hit1", "markov_fallback_hit3",
        "markov_minus_frequency_hit1", "markov_minus_frequency_hit3",
    ]

    null_data: dict[str, dict[str, dict[str, list[float]]]] = {
        sc: {lvl: {st: [] for st in stats_keys} for lvl in levels} for sc in schemes
    }
    sample_counts: dict[str, dict[str, set[int]]] = {
        sc: {lvl: set() for lvl in levels} for sc in schemes
    }
    obs_from_csv: dict[str, dict[str, float]] = {lvl: {} for lvl in levels}

    n_rows = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_rows += 1
            sc = row["scheme"]
            lvl = row["level"]
            st = row["statistic"]
            n_s = int(row["n_samples"])
            val = float(row["null_value"])
            obs = float(row["observed_value"])

            null_data[sc][lvl][st].append(val)
            sample_counts[sc][lvl].add(n_s)
            obs_from_csv[lvl][st] = obs

    print(f"Read {n_rows} rows from CSV successfully (expected 48000).")
    assert n_rows == 48000, f"Expected 48000 rows, got {n_rows}"

    # Verify S1 and S3 invariance
    assert sample_counts["S1_collapsed_order"]["technique_collapsed_full"] == {67}, "S1 technique N not constant 67!"
    assert sample_counts["S1_collapsed_order"]["tactic_collapsed"] == {53}, "S1 tactic N not constant 53!"
    assert sample_counts["S3_constrained_shuffle"]["technique_collapsed_full"] == {67}, "S3 technique N not constant 67!"
    assert sample_counts["S3_constrained_shuffle"]["tactic_collapsed"] == {53}, "S3 tactic N not constant 53!"
    
    # Verify S2 variability bounds
    s2_tech_n = sample_counts["S2_raw_shuffle_rate"]["technique_collapsed_full"]
    s2_tac_n = sample_counts["S2_raw_shuffle_rate"]["tactic_collapsed"]
    assert min(s2_tech_n) == 82 and max(s2_tech_n) == 95, f"S2 technique N range unexpected: {min(s2_tech_n)}..{max(s2_tech_n)}"
    assert min(s2_tac_n) == 74 and max(s2_tac_n) == 90, f"S2 tactic N range unexpected: {min(s2_tac_n)}..{max(s2_tac_n)}"
    print("S1 and S3 constant sample counts verified: Technique N=67, Tactic N=53.")
    print("S2 variable sample counts verified: Technique N in [82, 95], Tactic N in [74, 90].")

    # Verify pairwise distinctness across schemes (FAILS if any two schemes have identical permutation distributions)
    print("\n[Step 1b] Verifying pairwise scheme distinctness (no scheme equals another)...")
    scheme_pairs = [
        ("S1_collapsed_order", "S3_constrained_shuffle"),
        ("S1_collapsed_order", "S2_raw_shuffle_rate"),
        ("S3_constrained_shuffle", "S2_raw_shuffle_rate"),
    ]
    for s_a, s_b in scheme_pairs:
        for lvl in levels:
            for st in stats_keys:
                vals_a = null_data[s_a][lvl][st]
                vals_b = null_data[s_b][lvl][st]
                assert len(vals_a) == len(vals_b) == 1000
                if vals_a == vals_b:
                    raise ValueError(f"CRITICAL INTEGRITY FAILURE: Permutation rows of schemes {s_a} and {s_b} are identical for {lvl} {st}!")
    print("Pairwise scheme distinctness verified: S1, S2, and S3 are strictly distinct across all statistics and levels.")

    # 2. Recompute statistics and verify against JSON
    print("\n[Step 2] Recomputing null statistics and verifying against report JSON...")
    for sc in schemes:
        print(f"\nScheme: {sc}")
        for lvl in levels:
            print(f"  Level: {lvl}")
            for st in stats_keys:
                rpt_stat = report_data["schemes"][sc][lvl][st]
                obs_val = obs_from_csv[lvl][st]
                null_vals = null_data[sc][lvl][st]

                rec_stat = compute_summary_stats(obs_val, null_vals)

                # Check if level is invalid (order-free stat p < 0.05)
                # Compute order free stats p-values for this scheme and level
                lvl_invalid = any(
                    compute_summary_stats(obs_from_csv[lvl][of_st], null_data[sc][lvl][of_st])["p_value"] < 0.05
                    for of_st in ["frequency_hit1", "frequency_hit3"]
                )
                if lvl_invalid:
                    rec_stat["conclusion"] = f"INVALID NULL - do not cite: {rec_stat['conclusion']}"

                # Assert precision matches
                for k in ["null_mean", "null_sd", "null_p2_5", "null_p97_5", "null_min", "null_max", "p_value"]:
                    diff = abs(rpt_stat[k] - rec_stat[k])
                    if diff > 1e-6:
                        raise ValueError(f"Mismatch in {sc} {lvl} {st} {k}: rpt={rpt_stat[k]} vs rec={rec_stat[k]}")

                for k in ["n_ge_observed", "b_permutations"]:
                    if rpt_stat[k] != rec_stat[k]:
                        raise ValueError(f"Mismatch in {sc} {lvl} {st} {k}: rpt={rpt_stat[k]} vs rec={rec_stat[k]}")

                if rpt_stat["conclusion"] != rec_stat["conclusion"]:
                    raise ValueError(f"Conclusion mismatch in {sc} {lvl} {st}!")

                print(
                    f"    {st:28s} | Obs: {obs_val:+.4f} | Null Mean: {rec_stat['null_mean']:+.4f} "
                    f"| SD: {rec_stat['null_sd']:.4f} | p: {rec_stat['p_value']:.4f} [MATCH]"
                )

    # 3. Check Scheme Validity Check
    print("\n[Step 3] Checking Scheme Validity Warnings...")
    val_check = report_data["scheme_validity_check"]
    for sc in schemes:
        sig_stats = []
        for lvl in levels:
            for st in ["frequency_hit1", "frequency_hit3"]:
                p = report_data["schemes"][sc][lvl][st]["p_value"]
                if p < 0.05:
                    sig_stats.append((lvl, st, p))
        expected_valid = len(sig_stats) == 0
        actual_valid = val_check[sc]["is_valid_order_null"]
        assert actual_valid == expected_valid, f"Validity mismatch for {sc}: actual={actual_valid}, expected={expected_valid}"
        if not expected_valid:
            assert val_check[sc]["warning"] is not None, f"Expected warning message for invalid scheme {sc}!"
            print(f"  {sc}: Invalid null as expected (significant order-free stats: {sig_stats}) [PASS]")
        else:
            assert val_check[sc]["warning"] is None, f"Unexpected warning for valid scheme {sc}!"
            print(f"  {sc}: Valid order-only null as expected [PASS]")

    # 4. Check Markdown report consistency
    print("\n[Step 4] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    assert "v2.1 Report" in md_text
    assert "S3 (Constrained Shuffle)" in md_text

    for sc in schemes:
        for lvl in levels:
            for st in stats_keys:
                stat = report_data["schemes"][sc][lvl][st]
                p_tok = f"{stat['p_value']:.4f}"
                mean_tok = f"{stat['null_mean']:+.4f}"
                sd_tok = f"{stat['null_sd']:.4f}"
                for tok in [p_tok, mean_tok, sd_tok]:
                    if tok not in md_text:
                        raise ValueError(f"Token '{tok}' ({sc} {lvl} {st}) not found in Markdown report!")

    # Check sample count summary tokens
    assert "67.00" in md_text
    assert "53.00" in md_text
    assert "89.36" in md_text
    assert "82.51" in md_text

    # Check warning token in markdown
    assert "Scheme Validity Warning (S2)" in md_text

    print("All Markdown tokens verified.")
    print("\nALL PERMUTATION TEST v2.1 VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_permutation_test_v2()
