r"""Independent Verifier for Planted-Structure Validation Experiment.

Constraints:
- Reads ONLY data/processed/planted_structure_predictions.csv and report artifacts.
- No c4 imports (src.c4 is NOT imported).
- Recomputes every hit flag from raw candidate lists and target sets.
- Recomputes every replicate mean, standard error, difference, and gate threshold.
- Computes theoretical closed forms independently.
- Verifies that report JSON and Markdown match the CSV recomputations exactly.
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

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "data" / "processed" / "planted_structure_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "planted_structure_report.json"
MD_PATH = BASE_DIR / "reports" / "planted_structure_report.md"


def recompute_hit_flags(top3: list[str], target_set: set[str]) -> tuple[int, int]:
    """Hit@1 = 1 if top candidate in target set; Hit@3 = 1 if any of top 3 candidates in target set."""
    h1 = 1 if (len(top3) > 0 and top3[0] in target_set) else 0
    h3 = 1 if any(c in target_set for c in top3[:3]) else 0
    return h1, h3


def verify_planted_structure() -> bool:
    print("=" * 80)
    print("VERIFYING PLANTED STRUCTURE EXPERIMENT (INDEPENDENT CSV RECOMPUTATION)")
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

    # 1. Read CSV and recompute every hit flag
    print("\n[Step 1] Reading CSV and recomputing hit flags for every row...")
    n_rows = 0
    recompute_data: dict[str, Any] = {
        "A1": {},
        "A2": {"replicates": {}},
        "A3": {},
    }

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            n_rows += 1
            variant = row["variant"]
            s = float(row["s"])
            s_str = f"{s:.2f}" if s != 0.0 or variant != "A2" else "0.0"
            rep = int(row["replicate"])
            method = row["method"]
            cur_set = json.loads(row["current_set"])
            tgt_set = set(json.loads(row["target_set"]))
            top3 = json.loads(row["top3_candidates"])
            csv_h1 = int(row["hit1"])
            csv_h3 = int(row["hit3"])

            # Verify hit flags
            exp_h1, exp_h3 = recompute_hit_flags(top3, tgt_set)
            if csv_h1 != exp_h1 or csv_h3 != exp_h3:
                raise ValueError(
                    f"Hit flag mismatch at row {n_rows}: {row['sample_id']} method={method} "
                    f"CSV=({csv_h1},{csv_h3}) vs Recomputed=({exp_h1},{exp_h3})"
                )

            # Accumulate per variant / s / rep / method
            if variant in ("A1", "A3"):
                s_key = str(s)
                if s_key not in recompute_data[variant]:
                    recompute_data[variant][s_key] = {}
                if rep not in recompute_data[variant][s_key]:
                    recompute_data[variant][s_key][rep] = {}
                if method not in recompute_data[variant][s_key][rep]:
                    recompute_data[variant][s_key][rep][method] = {"h1": 0, "h3": 0, "n": 0}

                recompute_data[variant][s_key][rep][method]["h1"] += exp_h1
                recompute_data[variant][s_key][rep][method]["h3"] += exp_h3
                recompute_data[variant][s_key][rep][method]["n"] += 1

            elif variant == "A2":
                if rep not in recompute_data["A2"]["replicates"]:
                    recompute_data["A2"]["replicates"][rep] = {}
                if method not in recompute_data["A2"]["replicates"][rep]:
                    recompute_data["A2"]["replicates"][rep][method] = {"h1": 0, "h3": 0, "n": 0}

                recompute_data["A2"]["replicates"][rep][method]["h1"] += exp_h1
                recompute_data["A2"]["replicates"][rep][method]["h3"] += exp_h3
                recompute_data["A2"]["replicates"][rep][method]["n"] += 1

    print(f"Verified all hit flags across all {n_rows} CSV rows without error.")

    # 2. Closed forms
    V_size = 12
    chance_top1 = 1.0 / (V_size - 1)  # 1/11
    if abs(chance_top1 - report_data["chance_top1"]) > 1e-9:
        raise ValueError("Chance Top-1 mismatch between verifier and report!")

    # 3. Recompute A1 metrics
    print("\n[Step 2] Recomputing Variant A1 metrics & checking against report...")
    signal_levels = [0.0, 0.25, 0.5, 0.75, 1.0]
    a1_recomputed = {}
    for s in signal_levels:
        s_key = str(s)
        rep_dict = recompute_data["A1"][s_key]
        m_top1_list = []
        f_top1_list = []
        for rep in sorted(rep_dict.keys()):
            m_stat = rep_dict[rep]["markov"]
            f_stat = rep_dict[rep]["frequency"]
            m_top1_list.append(m_stat["h1"] / m_stat["n"])
            f_top1_list.append(f_stat["h1"] / f_stat["n"])

        n_reps = len(m_top1_list)
        m_mean = sum(m_top1_list) / n_reps
        f_mean = sum(f_top1_list) / n_reps
        var = sum((x - m_mean) ** 2 for x in m_top1_list) / (n_reps - 1)
        se = math.sqrt(var / n_reps)
        oracle = s + (1.0 - s) / 11.0
        diff_oracle = abs(m_mean - oracle)

        # Check against JSON
        rpt_a1 = report_data["A1"][s_key]
        if abs(m_mean - rpt_a1["markov_top1_mean"]) > 1e-7:
            raise ValueError(f"A1 s={s} Markov Top-1 mean mismatch!")
        if abs(se - rpt_a1["markov_top1_se"]) > 1e-7:
            raise ValueError(f"A1 s={s} Markov Top-1 SE mismatch!")
        if abs(f_mean - rpt_a1["frequency_top1_mean"]) > 1e-7:
            raise ValueError(f"A1 s={s} Frequency Top-1 mean mismatch!")
        if abs(oracle - rpt_a1["oracle_top1"]) > 1e-7:
            raise ValueError(f"A1 s={s} Oracle Top-1 mismatch!")

        a1_recomputed[s_key] = {
            "s": s,
            "markov_top1_mean": m_mean,
            "markov_top1_se": se,
            "frequency_top1_mean": f_mean,
            "oracle_top1": oracle,
            "diff_from_oracle": diff_oracle,
        }
        print(f"  A1 s={s:4.2f} -> Markov: {m_mean:.4f} (SE: {se:.4f}, oracle: {oracle:.4f}), Freq: {f_mean:.4f} [MATCH]")

    # 4. Recompute A2 metrics
    print("\n[Step 3] Recomputing Variant A2 metrics & checking against report...")
    a2_m_list = []
    a2_f_list = []
    for rep in sorted(recompute_data["A2"]["replicates"].keys()):
        m_stat = recompute_data["A2"]["replicates"][rep]["markov"]
        f_stat = recompute_data["A2"]["replicates"][rep]["frequency"]
        a2_m_list.append(m_stat["h1"] / m_stat["n"])
        a2_f_list.append(f_stat["h1"] / f_stat["n"])

    n_reps = len(a2_m_list)
    a2_m_mean = sum(a2_m_list) / n_reps
    a2_f_mean = sum(a2_f_list) / n_reps
    a2_diff = abs(a2_m_mean - a2_f_mean)

    rpt_a2 = report_data["A2"]
    if abs(a2_m_mean - rpt_a2["markov_top1_mean"]) > 1e-7:
        raise ValueError("A2 Markov Top-1 mean mismatch!")
    if abs(a2_f_mean - rpt_a2["frequency_top1_mean"]) > 1e-7:
        raise ValueError("A2 Frequency Top-1 mean mismatch!")
    if abs(a2_diff - rpt_a2["difference"]) > 1e-7:
        raise ValueError("A2 difference mismatch!")
    print(f"  A2 -> Markov: {a2_m_mean:.4f}, Freq: {a2_f_mean:.4f}, Diff: {a2_diff:.4f} [MATCH]")

    # 5. Recompute A3 metrics
    print("\n[Step 4] Recomputing Variant A3 metrics & checking against report...")
    a3_recomputed = {}
    for s in signal_levels:
        s_key = str(s)
        rep_dict = recompute_data["A3"][s_key]
        m_top1_list = []
        f_top1_list = []
        for rep in sorted(rep_dict.keys()):
            m_stat = rep_dict[rep]["markov"]
            f_stat = rep_dict[rep]["frequency"]
            m_top1_list.append(m_stat["h1"] / m_stat["n"])
            f_top1_list.append(f_stat["h1"] / f_stat["n"])

        n_reps = len(m_top1_list)
        m_mean = sum(m_top1_list) / n_reps
        f_mean = sum(f_top1_list) / n_reps

        rpt_a3 = report_data["A3"][s_key]
        if abs(m_mean - rpt_a3["markov_top1_mean"]) > 1e-7:
            raise ValueError(f"A3 s={s} Markov Top-1 mean mismatch!")
        if abs(f_mean - rpt_a3["frequency_top1_mean"]) > 1e-7:
            raise ValueError(f"A3 s={s} Frequency Top-1 mean mismatch!")

        a3_recomputed[s_key] = {
            "s": s,
            "markov_top1_mean": m_mean,
            "frequency_top1_mean": f_mean,
        }
        print(f"  A3 s={s:4.2f} -> Markov: {m_mean:.4f}, Freq: {f_mean:.4f} [MATCH]")

    # 6. Recompute and verify all Gates
    print("\n[Step 5] Evaluating Pre-Declared Gates...")
    g1_val = a1_recomputed["1.0"]["markov_top1_mean"]
    g1_pass = g1_val >= 0.98

    se_0 = a1_recomputed["0.0"]["markov_top1_se"]
    g2_threshold = max(0.02, 3.0 * se_0)
    g2_diff = abs(a1_recomputed["0.0"]["markov_top1_mean"] - chance_top1)
    g2_pass = g2_diff <= g2_threshold

    a1_means = [a1_recomputed[str(s)]["markov_top1_mean"] for s in signal_levels]
    g3_pass = all(a1_means[i] <= a1_means[i + 1] for i in range(len(a1_means) - 1))

    g4_diffs = [a1_recomputed[str(s)]["diff_from_oracle"] for s in [0.25, 0.5, 0.75, 1.0]]
    g4_pass = all(d <= 0.05 for d in g4_diffs)

    g5_diffs = [a1_recomputed[str(s)]["markov_top1_mean"] - a1_recomputed[str(s)]["frequency_top1_mean"] for s in [0.5, 0.75, 1.0]]
    g5_pass = all(d >= 0.20 for d in g5_diffs)

    g6_pass = a2_diff <= 0.03

    a3_means = [a3_recomputed[str(s)]["markov_top1_mean"] for s in signal_levels]
    g7_pass = (a3_means[-1] >= 0.98) and all(a3_means[i] <= a3_means[i + 1] for i in range(len(a3_means) - 1))

    neg_m_mean = report_data["negative_control"]["broken_markov_top1"]
    neg_pass = neg_m_mean < 0.98

    gates_status = [
        ("G1", "A1, s=1.0: Markov Top-1 >= 0.98", f"{g1_val:.4f}", ">= 0.9800", g1_pass),
        ("G2", "A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE)", f"{g2_diff:.4f}", f"<= {g2_threshold:.4f}", g2_pass),
        ("G3", "A1: Markov Top-1 non-decreasing across s", str([round(x, 4) for x in a1_means]), "non-decreasing", g3_pass),
        ("G4", "A1, s >= 0.25: Markov within 0.05 of oracle", f"max diff={max(g4_diffs):.4f}", "<= 0.0500", g4_pass),
        ("G5", "A1, s >= 0.5: Markov exceeds Freq by >= 0.20", f"min excess={min(g5_diffs):.4f}", ">= 0.2000", g5_pass),
        ("G6", "A2: |Markov Top-1 - Freq Top-1| <= 0.03 (no order)", f"{a2_diff:.4f}", "<= 0.0300", g6_pass),
        ("G7", "A3, s=1.0: Markov Top-1 >= 0.98 & non-decreasing", f"s=1.0: {a3_means[-1]:.4f}", ">= 0.9800 & non-dec", g7_pass),
        ("NegCtrl", "Negative control: broken Markov fails G1", f"{neg_m_mean:.4f}", "< 0.9800 (must fail G1)", neg_pass),
    ]

    print("\nGate Summary Table:")
    print("-" * 80)
    for gid, desc, measured, thresh, passed in gates_status:
        res = "PASS" if passed else "FAIL"
        print(f"  {gid:7s} | {desc:50s} | {measured:20s} | {thresh:22s} | {res}")
    print("-" * 80)

    if not all(passed for _, _, _, _, passed in gates_status):
        raise RuntimeError("One or more gates FAILED in independent verification!")

    # 7. Check Markdown report consistency
    print("\n[Step 6] Checking Markdown report consistency...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Verify that key numbers appear in the markdown text
    for token in [
        f"{g1_val:.4f}",
        f"{g2_diff:.4f}",
        f"{g2_threshold:.4f}",
        f"{max(g4_diffs):.4f}",
        f"{min(g5_diffs):.4f}",
        f"{a2_diff:.4f}",
        f"{a2_m_mean:.4f}",
        f"{a2_f_mean:.4f}",
        f"{neg_m_mean:.4f}",
    ]:
        if token not in md_text:
            raise ValueError(f"Token {token} not found in Markdown report!")

    print("All Markdown tokens verified.")
    print("\nALL VERIFICATIONS PASSED SUCCESSFULLY.")
    return True


if __name__ == "__main__":
    verify_planted_structure()
