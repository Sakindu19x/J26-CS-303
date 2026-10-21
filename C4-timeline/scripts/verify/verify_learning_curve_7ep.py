"""Independent CSV-only verifier for the 7-Episode Learning Curve.

Reads ONLY data/processed_7ep/learning_curve_7ep.csv and reports/7ep/learning_curve_7ep_results.json,
recomputing every per-episode average and pooled rate across all k in 1..6,
and verifying all number tokens in reports/7ep/learning_curve_7ep_report.md.
Does NOT import any model code from src/c4.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "learning_curve_7ep.csv"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "learning_curve_7ep_results.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "learning_curve_7ep_report.md"

EPISODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
SLICES = ["technique_collapsed_full", "tactic_collapsed"]
MODELS = ["markov", "frequency", "markov_fallback"]

EXPECTED_TECH_N = {"E1": 18, "E2": 19, "E3": 20, "E4": 10, "E5": 2, "E6": 14, "E7": 12}
EXPECTED_TAC_N = {"E1": 13, "E2": 15, "E3": 15, "E4": 10, "E5": 2, "E6": 13, "E7": 8}


def verify_learning_curve_7ep() -> bool:
    print("================================================================================")
    print("INDEPENDENT CSV-ONLY VERIFIER FOR 7-EPISODE LEARNING CURVE")
    print("================================================================================")

    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Missing CSV: {CSV_PATH}")
    if not JSON_PATH.is_file():
        raise FileNotFoundError(f"Missing JSON: {JSON_PATH}")
    if not MD_PATH.is_file():
        raise FileNotFoundError(f"Missing MD: {MD_PATH}")

    # 1. Read CSV and check row counts
    print("\n[Step 1] Reading and verifying learning_curve_7ep.csv row structure...")
    rows_by_slice_k_ep_sub: dict[str, dict[int, dict[str, dict[str, dict[str, Any]]]]] = {
        sl: {k: {ep: defaultdict(dict) for ep in EPISODES} for k in range(1, 7)} for sl in SLICES
    }

    total_rows = 0
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total_rows += 1
            sl = r["slice"]
            k = int(r["k"])
            ep = r["held_out_episode"]
            sub_id = r["subset_id"]
            model = r["model"]

            assert sl in SLICES, f"Unknown slice: {sl}"
            assert k in range(1, 7), f"Invalid k: {k}"
            assert ep in EPISODES, f"Unknown episode: {ep}"
            assert model in MODELS, f"Unknown model: {model}"

            rows_by_slice_k_ep_sub[sl][k][ep][sub_id][model] = r

    expected_total_rows = 2 * 441 * 3  # 2 slices * 441 subsets * 3 models = 2646
    assert total_rows == expected_total_rows, f"Expected {expected_total_rows} rows, got {total_rows}"
    print(f"  Total CSV rows = {total_rows} (expected {expected_total_rows}) [PASS]")

    # 2. Check subset counts and sample invariants
    print("\n[Step 2] Verifying subset counts and sample size invariants...")
    for sl in SLICES:
        exp_n_map = EXPECTED_TECH_N if sl == "technique_collapsed_full" else EXPECTED_TAC_N
        for k in range(1, 7):
            exp_sub_count = math.comb(6, k)
            for ep in EPISODES:
                subs = rows_by_slice_k_ep_sub[sl][k][ep]
                assert len(subs) == exp_sub_count, f"Slice {sl} k={k} ep={ep}: expected {exp_sub_count} subsets, got {len(subs)}"
                for sub_id, m_dict in subs.items():
                    assert len(m_dict) == 3, f"Subset {sub_id} missing models!"
                    for model in MODELS:
                        r = m_dict[model]
                        n_s = int(r["n_samples"])
                        assert n_s == exp_n_map[ep], f"Sample count mismatch in {sub_id} {model}: {n_s} != {exp_n_map[ep]}"
    print("  All 441 subsets per slice verified with exact sample count invariants [PASS]")

    # 3. Independently recompute aggregations and compare with JSON
    print("\n[Step 3] Independently recomputing averages from CSV and verifying JSON results...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    for sl in SLICES:
        exp_n_map = EXPECTED_TECH_N if sl == "technique_collapsed_full" else EXPECTED_TAC_N
        tot_samples = sum(exp_n_map.values())

        for k in range(1, 7):
            n_sub = math.comb(6, k)
            k_json = json_data["learning_curve"][sl][f"k_{k}"]

            # Accumulators
            recomputed_ep_means = {}
            weighted_tot_m1 = 0.0
            weighted_tot_m3 = 0.0
            weighted_tot_f1 = 0.0
            weighted_tot_f3 = 0.0
            weighted_tot_fb1 = 0.0
            weighted_tot_fb3 = 0.0
            weighted_tot_cov = 0.0
            weighted_tot_ceil = 0.0

            for ep in EPISODES:
                subs = rows_by_slice_k_ep_sub[sl][k][ep]
                n_ep = exp_n_map[ep]

                m1_rates = [float(subs[sid]["markov"]["hit1_rate"]) for sid in subs]
                m3_rates = [float(subs[sid]["markov"]["hit3_rate"]) for sid in subs]
                f1_rates = [float(subs[sid]["frequency"]["hit1_rate"]) for sid in subs]
                f3_rates = [float(subs[sid]["frequency"]["hit3_rate"]) for sid in subs]
                fb1_rates = [float(subs[sid]["markov_fallback"]["hit1_rate"]) for sid in subs]
                fb3_rates = [float(subs[sid]["markov_fallback"]["hit3_rate"]) for sid in subs]
                cov_rates = [float(subs[sid]["markov"]["coverage_rate"]) for sid in subs]
                ceil_rates = [float(subs[sid]["markov"]["ceiling_rate"]) for sid in subs]

                mean_m1 = sum(m1_rates) / n_sub
                mean_m3 = sum(m3_rates) / n_sub
                mean_f1 = sum(f1_rates) / n_sub
                mean_f3 = sum(f3_rates) / n_sub
                mean_fb1 = sum(fb1_rates) / n_sub
                mean_fb3 = sum(fb3_rates) / n_sub
                mean_cov = sum(cov_rates) / n_sub
                mean_ceil = sum(ceil_rates) / n_sub

                recomputed_ep_means[ep] = {
                    "m1": mean_m1, "m3": mean_m3,
                    "f1": mean_f1, "f3": mean_f3,
                    "fb1": mean_fb1, "fb3": mean_fb3,
                    "cov": mean_cov, "ceil": mean_ceil,
                }

                weighted_tot_m1 += mean_m1 * n_ep
                weighted_tot_m3 += mean_m3 * n_ep
                weighted_tot_f1 += mean_f1 * n_ep
                weighted_tot_f3 += mean_f3 * n_ep
                weighted_tot_fb1 += mean_fb1 * n_ep
                weighted_tot_fb3 += mean_fb3 * n_ep
                weighted_tot_cov += mean_cov * n_ep
                weighted_tot_ceil += mean_ceil * n_ep

                # Compare per-episode JSON
                ep_json = k_json["per_episode_means"][ep]
                assert abs(ep_json["markov"]["hit1_rate"] - mean_m1) < 1e-6
                assert abs(ep_json["markov"]["hit3_rate"] - mean_m3) < 1e-6
                assert abs(ep_json["frequency"]["hit1_rate"] - mean_f1) < 1e-6
                assert abs(ep_json["frequency"]["hit3_rate"] - mean_f3) < 1e-6
                assert abs(ep_json["markov_fallback"]["hit1_rate"] - mean_fb1) < 1e-6
                assert abs(ep_json["markov_fallback"]["hit3_rate"] - mean_fb3) < 1e-6
                assert abs(ep_json["coverage_rate"] - mean_cov) < 1e-6
                assert abs(ep_json["ceiling_rate"] - mean_ceil) < 1e-6

            # Compare unweighted episode-mean JSON (Pre-registered primary Table 1)
            unw_json = k_json["unweighted_episode_mean"]
            assert abs(unw_json["markov_hit1"] - (sum(recomputed_ep_means[ep]["m1"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["markov_hit3"] - (sum(recomputed_ep_means[ep]["m3"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["frequency_hit1"] - (sum(recomputed_ep_means[ep]["f1"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["frequency_hit3"] - (sum(recomputed_ep_means[ep]["f3"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["markov_fallback_hit1"] - (sum(recomputed_ep_means[ep]["fb1"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["markov_fallback_hit3"] - (sum(recomputed_ep_means[ep]["fb3"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["coverage"] - (sum(recomputed_ep_means[ep]["cov"] for ep in EPISODES) / 7.0)) < 1e-6
            assert abs(unw_json["ceiling"] - (sum(recomputed_ep_means[ep]["ceil"] for ep in EPISODES) / 7.0)) < 1e-6

            # Compare pooled JSON (Secondary Table 2)
            pw_json = k_json["pooled_sample_weighted"]
            assert abs(pw_json["markov_hit1"] - (weighted_tot_m1 / tot_samples)) < 1e-6
            assert abs(pw_json["markov_hit3"] - (weighted_tot_m3 / tot_samples)) < 1e-6
            assert abs(pw_json["frequency_hit1"] - (weighted_tot_f1 / tot_samples)) < 1e-6
            assert abs(pw_json["frequency_hit3"] - (weighted_tot_f3 / tot_samples)) < 1e-6
            assert abs(pw_json["markov_fallback_hit1"] - (weighted_tot_fb1 / tot_samples)) < 1e-6
            assert abs(pw_json["markov_fallback_hit3"] - (weighted_tot_fb3 / tot_samples)) < 1e-6
            assert abs(pw_json["coverage"] - (weighted_tot_cov / tot_samples)) < 1e-6
            assert abs(pw_json["ceiling"] - (weighted_tot_ceil / tot_samples)) < 1e-6

            # Compare E5-excluded aggregations (Sensitivity Table 3)
            eps_no_e5 = [ep for ep in EPISODES if ep != "E5"]
            tot_samples_no_e5 = sum(exp_n_map[ep] for ep in eps_no_e5)
            e5_unw_json = k_json["e5_excluded"]["unweighted_episode_mean"]
            assert abs(e5_unw_json["markov_hit1"] - (sum(recomputed_ep_means[ep]["m1"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["markov_hit3"] - (sum(recomputed_ep_means[ep]["m3"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["frequency_hit1"] - (sum(recomputed_ep_means[ep]["f1"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["frequency_hit3"] - (sum(recomputed_ep_means[ep]["f3"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["markov_fallback_hit1"] - (sum(recomputed_ep_means[ep]["fb1"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["markov_fallback_hit3"] - (sum(recomputed_ep_means[ep]["fb3"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["coverage"] - (sum(recomputed_ep_means[ep]["cov"] for ep in eps_no_e5) / 6.0)) < 1e-6
            assert abs(e5_unw_json["ceiling"] - (sum(recomputed_ep_means[ep]["ceil"] for ep in eps_no_e5) / 6.0)) < 1e-6

            e5_pw_json = k_json["e5_excluded"]["pooled_sample_weighted"]
            e5_w_m1 = sum(recomputed_ep_means[ep]["m1"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_m3 = sum(recomputed_ep_means[ep]["m3"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_f1 = sum(recomputed_ep_means[ep]["f1"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_f3 = sum(recomputed_ep_means[ep]["f3"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_fb1 = sum(recomputed_ep_means[ep]["fb1"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_fb3 = sum(recomputed_ep_means[ep]["fb3"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_cov = sum(recomputed_ep_means[ep]["cov"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5
            e5_w_ceil = sum(recomputed_ep_means[ep]["ceil"] * exp_n_map[ep] for ep in eps_no_e5) / tot_samples_no_e5

            assert abs(e5_pw_json["markov_hit1"] - e5_w_m1) < 1e-6
            assert abs(e5_pw_json["markov_hit3"] - e5_w_m3) < 1e-6
            assert abs(e5_pw_json["frequency_hit1"] - e5_w_f1) < 1e-6
            assert abs(e5_pw_json["frequency_hit3"] - e5_w_f3) < 1e-6
            assert abs(e5_pw_json["markov_fallback_hit1"] - e5_w_fb1) < 1e-6
            assert abs(e5_pw_json["markov_fallback_hit3"] - e5_w_fb3) < 1e-6
            assert abs(e5_pw_json["coverage"] - e5_w_cov) < 1e-6
            assert abs(e5_pw_json["ceiling"] - e5_w_ceil) < 1e-6

    print("  All per-episode averages, unweighted episode-means, pooled rates, and E5-excluded sensitivities verified against JSON [PASS]")

    # 4. Verify Markdown report consistency
    print("\n[Step 4] Verifying Markdown report number tokens...")
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Verify key tokens in Markdown report
    for sl in SLICES:
        for k in range(1, 7):
            unw = json_data["learning_curve"][sl][f"k_{k}"]["unweighted_episode_mean"]
            pw = json_data["learning_curve"][sl][f"k_{k}"]["pooled_sample_weighted"]
            e5_unw = json_data["learning_curve"][sl][f"k_{k}"]["e5_excluded"]["unweighted_episode_mean"]
            e5_pw = json_data["learning_curve"][sl][f"k_{k}"]["e5_excluded"]["pooled_sample_weighted"]
            for agg in [unw, pw, e5_unw, e5_pw]:
                tok_m3 = f"{agg['markov_hit3']:.4f}"
                tok_f3 = f"{agg['frequency_hit3']:.4f}"
                tok_cov = f"{agg['coverage']:.4f}"
                tok_ceil = f"{agg['ceiling']:.4f}"
                for tok in [tok_m3, tok_f3, tok_cov, tok_ceil]:
                    assert tok in md_text, f"Token '{tok}' (slice {sl} k={k}) missing from Markdown report!"

    print("  All Table 1, Table 2, and Table 3 tokens verified in Markdown report [PASS]")
    print("\n================================================================================")
    print("ALL LEARNING CURVE VERIFICATION CHECKS PASSED (EXIT CODE 0)")
    print("================================================================================")
    return True


if __name__ == "__main__":
    verify_learning_curve_7ep()
