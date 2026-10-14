r"""Permutation Test on Real Episodes (E1-E4) v2.

Pre-declared test design:
- Primary scheme S1 ("collapsed-order shuffle"):
    For each real episode, take the stored collapsed sequence from data/processed/attack_sequences.json
    and shuffle the ORDER of its items strictly within the episode (item contents unchanged).
    Technique level: rebuild samples with production build_samples_for_sequence and run LOEO evaluation.
    Tactic level: evaluate collapsed tactic sequences with production LOEO evaluation.
    Assert that N equals the observed N (67 technique, 53 tactic) in EVERY permutation.
- Sensitivity scheme S2 ("raw-shuffle-then-collapse"):
    Raw labeled events shuffled strictly within each episode, collapsed with production logic,
    rebuilt with production sample builder, evaluated with production LOEO.
    Statistic is the hit RATE (hits / N_perm) compared against observed rate (obs_hits / N_obs).
- Decision rule:
    p < 0.05 under S1 only. S2 is reported as sensitivity and never used for headline conclusions.
- B=1000 permutations (seeds 0..999, stdlib random.Random).
- One-sided p-value:
    p = (1 + count(null >= observed)) / (1 + B)
- Conclusion text rule:
    Code-generated strictly from p-value:
    if p < 0.05: "observed exceeds the shuffled-order null (p=...)"
    else: "not distinguishable from the shuffled-order null at this sample size (this is not proof of absence)"
    No causal or confirmatory claims ("driven by", "confirm").
"""
from __future__ import annotations

import copy
import csv
import json
import math
import random
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.c4.models.markov import MarkovModel
from src.c4.models.frequency import FrequencyBaseline
from src.c4.attack_sequence import collapse_sequence
from src.c4.samples import build_samples_for_sequence
from src.c4.normalization import EPISODE_MAPPING
from src.c4.evaluation import evaluate_loeo_slice
import src.c4.tactic_evaluation as te

DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

ATTACK_SEQUENCES_PATH = PROCESSED_DIR / "attack_sequences.json"
LOEO_FOLDS_PATH = PROCESSED_DIR / "loeo_folds.json"
TECH_EVAL_JSON_PATH = REPORTS_DIR / "evaluation_results.json"
TACTIC_EVAL_JSON_PATH = REPORTS_DIR / "tactic_evaluation_results.json"

CSV_OUT_PATH = PROCESSED_DIR / "permutation_v2_null_distribution.csv"
JSON_OUT_PATH = REPORTS_DIR / "permutation_test_v2_report.json"
MD_OUT_PATH = REPORTS_DIR / "permutation_test_v2_report.md"

B_PERMUTATIONS = 1000


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


def compute_summary_stats(observed: float, null_values: list[float], scheme: str) -> dict[str, Any]:
    b = len(null_values)
    mean_val = sum(null_values) / b
    var = sum((x - mean_val) ** 2 for x in null_values) / (b - 1) if b > 1 else 0.0
    sd_val = math.sqrt(var)
    p2_5 = percentile_linear(null_values, 2.5)
    p97_5 = percentile_linear(null_values, 97.5)
    min_val = min(null_values)
    max_val = max(null_values)
    n_ge = sum(1 for x in null_values if x >= observed - 1e-12)
    p_val = (1.0 + n_ge) / (1.0 + b)
    
    # Generated conclusion text rule
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


def run_permutation_test_v2() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING PERMUTATION TEST v2 (FIXED-N S1 & RATE-BASED S2)")
    print("=" * 80)

    # 1. Load baseline data
    with open(ATTACK_SEQUENCES_PATH, "r", encoding="utf-8") as f:
        orig_seqs = json.load(f)

    with open(LOEO_FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)

    with open(TECH_EVAL_JSON_PATH, "r", encoding="utf-8") as f:
        tech_eval_json = json.load(f)

    with open(TACTIC_EVAL_JSON_PATH, "r", encoding="utf-8") as f:
        tactic_eval_json = json.load(f)

    # 2. Extract and verify observed rates and hits
    tech_cf = tech_eval_json["slices"]["collapsed_full"]
    N_tech_obs = tech_cf["n_samples"]
    assert N_tech_obs == 67, f"Expected 67 technique samples, got {N_tech_obs}"

    m_h1 = tech_cf["headline"]["markov"]["hit1"]
    m_h3 = tech_cf["headline"]["markov"]["hit3"]
    f_h1 = tech_cf["headline"]["frequency"]["hit1"]
    f_h3 = tech_cf["headline"]["frequency"]["hit3"]
    fb_h1 = tech_cf["headline"]["fallback"]["hit1"]
    fb_h3 = tech_cf["headline"]["fallback"]["hit3"]

    assert (m_h1, m_h3) == (1, 2)
    assert (f_h1, f_h3) == (4, 8)
    assert (fb_h1, fb_h3) == (2, 5)

    tac_tc = tactic_eval_json["slices"]["tactic_collapsed"]
    N_tac_obs = tac_tc["n_samples"]
    assert N_tac_obs == 53, f"Expected 53 tactic samples, got {N_tac_obs}"

    tm_h1 = tac_tc["headline"]["markov"]["hit1"]
    tm_h3 = tac_tc["headline"]["markov"]["hit3"]
    tf_h1 = tac_tc["headline"]["frequency"]["hit1"]
    tf_h3 = tac_tc["headline"]["frequency"]["hit3"]
    tfb_h1 = tac_tc["headline"]["markov_fallback"]["hit1"]
    tfb_h3 = tac_tc["headline"]["markov_fallback"]["hit3"]

    assert (tm_h1, tm_h3) == (11, 28)
    assert (tf_h1, tf_h3) == (9, 33)
    assert (tfb_h1, tfb_h3) == (13, 30)

    # Observed rates (hits / N)
    obs_rates = {
        "technique_collapsed_full": {
            "markov_hit1": m_h1 / N_tech_obs,
            "markov_hit3": m_h3 / N_tech_obs,
            "frequency_hit1": f_h1 / N_tech_obs,
            "frequency_hit3": f_h3 / N_tech_obs,
            "markov_fallback_hit1": fb_h1 / N_tech_obs,
            "markov_fallback_hit3": fb_h3 / N_tech_obs,
            "markov_minus_frequency_hit1": (m_h1 - f_h1) / N_tech_obs,
            "markov_minus_frequency_hit3": (m_h3 - f_h3) / N_tech_obs,
        },
        "tactic_collapsed": {
            "markov_hit1": tm_h1 / N_tac_obs,
            "markov_hit3": tm_h3 / N_tac_obs,
            "frequency_hit1": tf_h1 / N_tac_obs,
            "frequency_hit3": tf_h3 / N_tac_obs,
            "markov_fallback_hit1": tfb_h1 / N_tac_obs,
            "markov_fallback_hit3": tfb_h3 / N_tac_obs,
            "markov_minus_frequency_hit1": (tm_h1 - tf_h1) / N_tac_obs,
            "markov_minus_frequency_hit3": (tm_h3 - tf_h3) / N_tac_obs,
        },
    }

    obs_counts = {
        "technique_collapsed_full": {
            "n_samples": N_tech_obs,
            "markov_hit1": m_h1, "markov_hit3": m_h3,
            "frequency_hit1": f_h1, "frequency_hit3": f_h3,
            "markov_fallback_hit1": fb_h1, "markov_fallback_hit3": fb_h3,
            "markov_minus_frequency_hit1": m_h1 - f_h1,
            "markov_minus_frequency_hit3": m_h3 - f_h3,
        },
        "tactic_collapsed": {
            "n_samples": N_tac_obs,
            "markov_hit1": tm_h1, "markov_hit3": tm_h3,
            "frequency_hit1": tf_h1, "frequency_hit3": tf_h3,
            "markov_fallback_hit1": tfb_h1, "markov_fallback_hit3": tfb_h3,
            "markov_minus_frequency_hit1": tm_h1 - tf_h1,
            "markov_minus_frequency_hit3": tm_h3 - tf_h3,
        },
    }

    print("Observed baselines verified successfully.")

    # Prepare canonical tactic collapsed sequences for S1
    all_ep_seqs = te.build_tactic_sequences(orig_seqs, use_dataset_tactics=False)
    canonical_tac_col = {ep: all_ep_seqs[ep]["tactic_collapsed"] for ep in all_ep_seqs}

    csv_rows = []
    # Structure: null_distributions[scheme][level][stat] = list[float]
    schemes = ["S1_collapsed_order", "S2_raw_shuffle_rate"]
    levels = ["technique_collapsed_full", "tactic_collapsed"]
    stats_keys = [
        "markov_hit1", "markov_hit3",
        "frequency_hit1", "frequency_hit3",
        "markov_fallback_hit1", "markov_fallback_hit3",
        "markov_minus_frequency_hit1", "markov_minus_frequency_hit3",
    ]

    null_distributions: dict[str, dict[str, dict[str, list[float]]]] = {
        sc: {lvl: {st: [] for st in stats_keys} for lvl in levels} for sc in schemes
    }
    sample_counts: dict[str, dict[str, list[int]]] = {
        sc: {lvl: [] for lvl in levels} for sc in schemes
    }

    t0 = time.time()
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S1 (collapsed-order shuffle)...")
    for b in range(B_PERMUTATIONS):
        rng = random.Random(b)

        # --- S1 Technique ---
        s1_tech_episodes = {}
        s1_tech_samples = []
        for ep_id, ep_data in sorted(orig_seqs["episodes"].items()):
            shuffled_col = copy.deepcopy(ep_data["collapsed"])
            rng.shuffle(shuffled_col)
            s1_tech_episodes[ep_id] = {
                "raw": shuffled_col,
                "collapsed": shuffled_col,
            }
            sc_id = EPISODE_MAPPING.get(ep_id, "")
            s1_tech_samples.extend(
                build_samples_for_sequence(shuffled_col, ep_id, sc_id, "collapsed", "full")
            )

        n_s1_tech = len(s1_tech_samples)
        assert n_s1_tech == N_tech_obs, f"S1 technique sample count {n_s1_tech} != {N_tech_obs} at seed {b}!"
        sample_counts["S1_collapsed_order"]["technique_collapsed_full"].append(n_s1_tech)

        t_res, _ = evaluate_loeo_slice(
            variant="collapsed",
            granularity="full",
            save_fold_models=False,
            sequences_data={"episodes": s1_tech_episodes},
            folds_data=folds_data,
            samples_data=s1_tech_samples,
        )

        sm_h1 = t_res["headline"]["markov"]["hit1"]
        sm_h3 = t_res["headline"]["markov"]["hit3"]
        sf_h1 = t_res["headline"]["frequency"]["hit1"]
        sf_h3 = t_res["headline"]["frequency"]["hit3"]
        sfb_h1 = t_res["headline"]["fallback"]["hit1"]
        sfb_h3 = t_res["headline"]["fallback"]["hit3"]

        s1_tech_vals = {
            "markov_hit1": sm_h1 / n_s1_tech,
            "markov_hit3": sm_h3 / n_s1_tech,
            "frequency_hit1": sf_h1 / n_s1_tech,
            "frequency_hit3": sf_h3 / n_s1_tech,
            "markov_fallback_hit1": sfb_h1 / n_s1_tech,
            "markov_fallback_hit3": sfb_h3 / n_s1_tech,
            "markov_minus_frequency_hit1": (sm_h1 - sf_h1) / n_s1_tech,
            "markov_minus_frequency_hit3": (sm_h3 - sf_h3) / n_s1_tech,
        }
        s1_tech_hits = {
            "markov_hit1": sm_h1, "markov_hit3": sm_h3,
            "frequency_hit1": sf_h1, "frequency_hit3": sf_h3,
            "markov_fallback_hit1": sfb_h1, "markov_fallback_hit3": sfb_h3,
            "markov_minus_frequency_hit1": sm_h1 - sf_h1,
            "markov_minus_frequency_hit3": sm_h3 - sf_h3,
        }

        for k, v in s1_tech_vals.items():
            null_distributions["S1_collapsed_order"]["technique_collapsed_full"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S1_collapsed_order",
                "level": "technique_collapsed_full",
                "statistic": k,
                "n_samples": n_s1_tech,
                "hits": s1_tech_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['technique_collapsed_full'][k]:.10f}",
            })

        # --- S1 Tactic ---
        s1_tac_col = {}
        for ep_id in sorted(canonical_tac_col.keys()):
            shuffled_tac = copy.deepcopy(canonical_tac_col[ep_id])
            rng.shuffle(shuffled_tac)
            s1_tac_col[ep_id] = shuffled_tac

        orig_te_fn = te.build_tactic_sequences
        te.build_tactic_sequences = lambda seqs, use_dataset_tactics=False: {
            ep: {"tactic_collapsed": s1_tac_col[ep]} for ep in s1_tac_col
        }
        try:
            tac_res, _ = te.evaluate_tactic_slice(
                variant="tactic_collapsed",
                folds_data=folds_data,
            )
        finally:
            te.build_tactic_sequences = orig_te_fn

        n_s1_tac = tac_res["n_samples"]
        assert n_s1_tac == N_tac_obs, f"S1 tactic sample count {n_s1_tac} != {N_tac_obs} at seed {b}!"
        sample_counts["S1_collapsed_order"]["tactic_collapsed"].append(n_s1_tac)

        stm_h1 = tac_res["headline"]["markov"]["hit1"]
        stm_h3 = tac_res["headline"]["markov"]["hit3"]
        stf_h1 = tac_res["headline"]["frequency"]["hit1"]
        stf_h3 = tac_res["headline"]["frequency"]["hit3"]
        stfb_h1 = tac_res["headline"]["markov_fallback"]["hit1"]
        stfb_h3 = tac_res["headline"]["markov_fallback"]["hit3"]

        s1_tac_vals = {
            "markov_hit1": stm_h1 / n_s1_tac,
            "markov_hit3": stm_h3 / n_s1_tac,
            "frequency_hit1": stf_h1 / n_s1_tac,
            "frequency_hit3": stf_h3 / n_s1_tac,
            "markov_fallback_hit1": stfb_h1 / n_s1_tac,
            "markov_fallback_hit3": stfb_h3 / n_s1_tac,
            "markov_minus_frequency_hit1": (stm_h1 - stf_h1) / n_s1_tac,
            "markov_minus_frequency_hit3": (stm_h3 - stf_h3) / n_s1_tac,
        }
        s1_tac_hits = {
            "markov_hit1": stm_h1, "markov_hit3": stm_h3,
            "frequency_hit1": stf_h1, "frequency_hit3": stf_h3,
            "markov_fallback_hit1": stfb_h1, "markov_fallback_hit3": stfb_h3,
            "markov_minus_frequency_hit1": stm_h1 - stf_h1,
            "markov_minus_frequency_hit3": stm_h3 - stf_h3,
        }

        for k, v in s1_tac_vals.items():
            null_distributions["S1_collapsed_order"]["tactic_collapsed"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S1_collapsed_order",
                "level": "tactic_collapsed",
                "statistic": k,
                "n_samples": n_s1_tac,
                "hits": s1_tac_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['tactic_collapsed'][k]:.10f}",
            })

    print(f"S1 finished in {time.time() - t0:.2f}s.")

    t1 = time.time()
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S2 (raw-shuffle rate-based sensitivity)...")
    for b in range(B_PERMUTATIONS):
        rng = random.Random(b)
        s2_perm_seqs = {"episodes": {}}
        s2_rebuilt_tech_samples = []

        for ep_id, ep_data in sorted(orig_seqs["episodes"].items()):
            shuffled_raw = copy.deepcopy(ep_data["raw"])
            rng.shuffle(shuffled_raw)
            shuffled_col = collapse_sequence(shuffled_raw)
            s2_perm_seqs["episodes"][ep_id] = {
                "raw": shuffled_raw,
                "collapsed": shuffled_col,
            }
            sc_id = EPISODE_MAPPING.get(ep_id, "")
            s2_rebuilt_tech_samples.extend(
                build_samples_for_sequence(shuffled_col, ep_id, sc_id, "collapsed", "full")
            )

        n_s2_tech = len(s2_rebuilt_tech_samples)
        sample_counts["S2_raw_shuffle_rate"]["technique_collapsed_full"].append(n_s2_tech)

        t_res, _ = evaluate_loeo_slice(
            variant="collapsed",
            granularity="full",
            save_fold_models=False,
            sequences_data=s2_perm_seqs,
            folds_data=folds_data,
            samples_data=s2_rebuilt_tech_samples,
        )

        s2_m_h1 = t_res["headline"]["markov"]["hit1"]
        s2_m_h3 = t_res["headline"]["markov"]["hit3"]
        s2_f_h1 = t_res["headline"]["frequency"]["hit1"]
        s2_f_h3 = t_res["headline"]["frequency"]["hit3"]
        s2_fb_h1 = t_res["headline"]["fallback"]["hit1"]
        s2_fb_h3 = t_res["headline"]["fallback"]["hit3"]

        s2_tech_vals = {
            "markov_hit1": s2_m_h1 / n_s2_tech,
            "markov_hit3": s2_m_h3 / n_s2_tech,
            "frequency_hit1": s2_f_h1 / n_s2_tech,
            "frequency_hit3": s2_f_h3 / n_s2_tech,
            "markov_fallback_hit1": s2_fb_h1 / n_s2_tech,
            "markov_fallback_hit3": s2_fb_h3 / n_s2_tech,
            "markov_minus_frequency_hit1": (s2_m_h1 - s2_f_h1) / n_s2_tech,
            "markov_minus_frequency_hit3": (s2_m_h3 - s2_f_h3) / n_s2_tech,
        }
        s2_tech_hits = {
            "markov_hit1": s2_m_h1, "markov_hit3": s2_m_h3,
            "frequency_hit1": s2_f_h1, "frequency_hit3": s2_f_h3,
            "markov_fallback_hit1": s2_fb_h1, "markov_fallback_hit3": s2_fb_h3,
            "markov_minus_frequency_hit1": s2_m_h1 - s2_f_h1,
            "markov_minus_frequency_hit3": s2_m_h3 - s2_f_h3,
        }

        for k, v in s2_tech_vals.items():
            null_distributions["S2_raw_shuffle_rate"]["technique_collapsed_full"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S2_raw_shuffle_rate",
                "level": "technique_collapsed_full",
                "statistic": k,
                "n_samples": n_s2_tech,
                "hits": s2_tech_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['technique_collapsed_full'][k]:.10f}",
            })

        # --- S2 Tactic ---
        tac_res, _ = te.evaluate_tactic_slice(
            variant="tactic_collapsed",
            sequences_data=s2_perm_seqs,
            folds_data=folds_data,
        )

        n_s2_tac = tac_res["n_samples"]
        sample_counts["S2_raw_shuffle_rate"]["tactic_collapsed"].append(n_s2_tac)

        s2_tm_h1 = tac_res["headline"]["markov"]["hit1"]
        s2_tm_h3 = tac_res["headline"]["markov"]["hit3"]
        s2_tf_h1 = tac_res["headline"]["frequency"]["hit1"]
        s2_tf_h3 = tac_res["headline"]["frequency"]["hit3"]
        s2_tfb_h1 = tac_res["headline"]["markov_fallback"]["hit1"]
        s2_tfb_h3 = tac_res["headline"]["markov_fallback"]["hit3"]

        s2_tac_vals = {
            "markov_hit1": s2_tm_h1 / n_s2_tac,
            "markov_hit3": s2_tm_h3 / n_s2_tac,
            "frequency_hit1": s2_tf_h1 / n_s2_tac,
            "frequency_hit3": s2_tf_h3 / n_s2_tac,
            "markov_fallback_hit1": s2_tfb_h1 / n_s2_tac,
            "markov_fallback_hit3": s2_tfb_h3 / n_s2_tac,
            "markov_minus_frequency_hit1": (s2_tm_h1 - s2_tf_h1) / n_s2_tac,
            "markov_minus_frequency_hit3": (s2_tm_h3 - s2_tf_h3) / n_s2_tac,
        }
        s2_tac_hits = {
            "markov_hit1": s2_tm_h1, "markov_hit3": s2_tm_h3,
            "frequency_hit1": s2_tf_h1, "frequency_hit3": s2_tf_h3,
            "markov_fallback_hit1": s2_tfb_h1, "markov_fallback_hit3": s2_tfb_h3,
            "markov_minus_frequency_hit1": s2_tm_h1 - s2_tf_h1,
            "markov_minus_frequency_hit3": s2_tm_h3 - s2_tf_h3,
        }

        for k, v in s2_tac_vals.items():
            null_distributions["S2_raw_shuffle_rate"]["tactic_collapsed"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S2_raw_shuffle_rate",
                "level": "tactic_collapsed",
                "statistic": k,
                "n_samples": n_s2_tac,
                "hits": s2_tac_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['tactic_collapsed'][k]:.10f}",
            })

    print(f"S2 finished in {time.time() - t1:.2f}s.")

    # 3. Write CSV
    print(f"\nWriting {len(csv_rows)} rows to {CSV_OUT_PATH}...")
    fieldnames = [
        "seed",
        "scheme",
        "level",
        "statistic",
        "n_samples",
        "hits",
        "null_value",
        "observed_value",
    ]
    with open(CSV_OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # 4. Compute statistics
    report_data: dict[str, Any] = {
        "metadata": {
            "test_name": "Permutation Test on Real Episodes (E1-E4) v2",
            "b_permutations": B_PERMUTATIONS,
            "decision_rule": "p < 0.05 under primary scheme S1 only; S2 reported as sensitivity",
            "p_value_formula": "p = (1 + count(null >= observed)) / (1 + B)",
            "observed_sample_counts": {
                "technique_collapsed_full": N_tech_obs,
                "tactic_collapsed": N_tac_obs,
            },
            "observed_baseline_counts": obs_counts,
            "observed_baseline_rates": obs_rates,
            "sample_counts_summary": {},
        },
        "schemes": {},
    }

    for sc in schemes:
        report_data["metadata"]["sample_counts_summary"][sc] = {}
        for lvl in levels:
            ns = sample_counts[sc][lvl]
            report_data["metadata"]["sample_counts_summary"][sc][lvl] = {
                "min": min(ns),
                "mean": sum(ns) / len(ns),
                "max": max(ns),
                "is_constant": bool(min(ns) == max(ns)),
            }

    for sc in schemes:
        report_data["schemes"][sc] = {}
        for lvl in levels:
            report_data["schemes"][sc][lvl] = {}
            for st in stats_keys:
                obs_val = obs_rates[lvl][st]
                null_vals = null_distributions[sc][lvl][st]
                stat_summary = compute_summary_stats(obs_val, null_vals, sc)
                report_data["schemes"][sc][lvl][st] = stat_summary

    # Write JSON
    print(f"Writing report JSON to {JSON_OUT_PATH}...")
    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Generate Markdown
    print(f"Writing report Markdown to {MD_OUT_PATH}...")
    generate_markdown_report_v2(report_data)

    print("Permutation test v2 completed successfully.")
    return report_data


def generate_markdown_report_v2(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    meta = data["metadata"]
    s_sum = meta["sample_counts_summary"]

    A("# Permutation Test on Real Episodes (E1–E4) v2 Report")
    A()
    A("## Pre-Declared Test Design & Purpose")
    A()
    A("- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines in real telemetry episodes E1–E4.")
    A("- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: The items of the stored collapsed sequence for each episode are shuffled strictly within the episode. Sample counts $N$ are strictly invariant ($N=67$ for technique, $N=53$ for tactic in every permutation). Headline decisions are made solely under S1.")
    A("- **Sensitivity Scheme (S2 - Raw-Shuffle Rate-Based)**: Raw labeled events are shuffled within each episode and re-collapsed, yielding variable sample counts ($N \\in [82, 95]$ technique, $N \\in [74, 90]$ tactic). The statistic is evaluated as hit rate (hits / $N_{perm}$) compared against observed hit rate.")
    A("- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999).")
    A(f"- **One-Sided p-value Formula**: `{meta['p_value_formula']}`.")
    A("- **Pre-Declared Decision Rule**: `p < 0.05` under S1 only. Sensitivity scheme S2 is documented alongside S1 for methodological completeness.")
    A("- **Conclusion Text Generation Rule**: Every conclusion sentence is generated strictly by code from the p-value: if $p < 0.05$, *'observed exceeds the shuffled-order null (p=...)'*; else *'not distinguishable from the shuffled-order null at this sample size (this is not proof of absence)'*. No causal inferences are asserted.")
    A()
    A("---")
    A()
    A("## Sample Count Distribution (Confound Resolution)")
    A()
    A("| Scheme | Level | Observed N | Permutation Min N | Permutation Mean N | Permutation Max N | Invariant N? |")
    A("|:---|:---|:---:|:---:|:---:|:---:|:---:|")
    for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S2_raw_shuffle_rate", "S2 (Raw-Shuffle)")]:
        for lvl, lvl_label in [("technique_collapsed_full", "Technique (collapsed_full)"), ("tactic_collapsed", "Tactic (tactic_collapsed)")]:
            info = s_sum[sc][lvl]
            obs_n = meta["observed_sample_counts"][lvl]
            inv_str = "**YES (Constant)**" if info["is_constant"] else "NO (Variable)"
            A(f"| {sc_label} | {lvl_label} | {obs_n} | {info['min']} | {info['mean']:.2f} | {info['max']} | {inv_str} |")
    A()
    A("---")
    A()
    A("## Primary Scheme S1 Results (Headline)")
    A()
    A("### Technique Level (`collapsed_full`, N=67)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s1_tech = data["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]
    counts_tech = meta["observed_baseline_counts"]["technique_collapsed_full"]
    stat_labels = {
        "markov_hit1": "Markov Hit@1",
        "markov_hit3": "Markov Hit@3",
        "frequency_hit1": "Frequency Hit@1",
        "frequency_hit3": "Frequency Hit@3",
        "markov_fallback_hit1": "Markov Fallback Hit@1",
        "markov_fallback_hit3": "Markov Fallback Hit@3",
        "markov_minus_frequency_hit1": "Markov - Frequency Hit@1",
        "markov_minus_frequency_hit3": "Markov - Frequency Hit@3",
    }
    for st, lbl in stat_labels.items():
        row = s1_tech[st]
        h_str = f"{counts_tech[st]:+d} / 67" if "minus" in st else f"{counts_tech[st]} / 67"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N=53)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s1_tac = data["schemes"]["S1_collapsed_order"]["tactic_collapsed"]
    counts_tac = meta["observed_baseline_counts"]["tactic_collapsed"]
    for st, lbl in stat_labels.items():
        row = s1_tac[st]
        h_str = f"{counts_tac[st]:+d} / 53" if "minus" in st else f"{counts_tac[st]} / 53"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("---")
    A()
    A("## Sensitivity Scheme S2 Results (Rate-Based Comparison)")
    A()
    A("### Technique Level (`collapsed_full`, N_perm in [82, 95])")
    A()
    A("| Statistic | Observed Rate | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s2_tech = data["schemes"]["S2_raw_shuffle_rate"]["technique_collapsed_full"]
    for st, lbl in stat_labels.items():
        row = s2_tech[st]
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N_perm in [74, 90])")
    A()
    A("| Statistic | Observed Rate | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s2_tac = data["schemes"]["S2_raw_shuffle_rate"]["tactic_collapsed"]
    for st, lbl in stat_labels.items():
        row = s2_tac[st]
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("---")
    A()
    A("## What this test cannot show")
    A()
    A("Statistical power in this permutation test is inherently limited by sample size:")
    A("- The technique evaluation contains only $N=67$ transition samples, and the tactic evaluation contains only $N=53$ transition samples across four episodes.")
    A("- In leave-one-episode-out cross-validation, models are trained on only three episodes per fold, limiting transition coverage across a large technique vocabulary ($V=64$).")
    A("- Therefore, failure to reject the shuffled-order null ($p \\ge 0.05$) does not constitute proof of absence of sequential structure in cybersecurity attacks in general. It reflects the limited statistical power achievable with three training episodes on this dataset.")
    A("- See the accompanying real-scale planted-structure power analysis (A4 in `reports/planted_realscale_report.md`) for empirical demonstration of the sample-size and reachability constraints governing Markov model power under identical scale.")
    A()

    with open(MD_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_permutation_test_v2()
