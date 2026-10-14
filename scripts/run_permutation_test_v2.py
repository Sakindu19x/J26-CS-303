r"""Permutation test on real episodes E1-E4 v2.1.

Fixed-N permutation testing:
- Primary Scheme (S1): Collapsed-order shuffle (strictly preserves sample counts N=67 and N=53).
- Constrained Scheme (S3): Uniform random shuffle of collapsed sequence subject to no adjacent identical
  items (rejection sampling <= 10,000 tries). Added after S1/S2 to remove artifact of adjacent identical items.
- Sensitivity Scheme (S2): Raw event shuffle within episode, re-collapsed (variable N). Evaluated on rates.

Includes:
- Automated "Scheme validity check": audits order-free Frequency statistics (p < 0.05).
- Output artifacts:
  - data/processed/permutation_v2_null_distribution.csv
  - reports/permutation_test_v2_report.json
  - reports/permutation_test_v2_report.md
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
MAX_S3_TRIES = 10000


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


def shuffle_constrained_tech(col: list[dict[str, Any]], rng: random.Random, max_tries: int = MAX_S3_TRIES) -> tuple[list[dict[str, Any]] | None, int]:
    for attempt in range(1, max_tries + 1):
        shuffled = copy.deepcopy(col)
        rng.shuffle(shuffled)
        valid = True
        for i in range(len(shuffled) - 1):
            if set(shuffled[i]["techniques"]) == set(shuffled[i + 1]["techniques"]):
                valid = False
                break
        if valid:
            return shuffled, attempt
    return None, max_tries


def shuffle_constrained_tac(col: list[dict[str, Any]], rng: random.Random, max_tries: int = MAX_S3_TRIES) -> tuple[list[dict[str, Any]] | None, int]:
    for attempt in range(1, max_tries + 1):
        shuffled = copy.deepcopy(col)
        rng.shuffle(shuffled)
        valid = True
        for i in range(len(shuffled) - 1):
            if set(shuffled[i]["tactics"]) == set(shuffled[i + 1]["tactics"]):
                valid = False
                break
        if valid:
            return shuffled, attempt
    return None, max_tries


def run_permutation_test_v2() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING PERMUTATION TEST v2.1 (S1, S2, S3 CONSTRAINED SHUFFLE)")
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

    # Prepare canonical tactic collapsed sequences for S1 and S3
    all_ep_seqs = te.build_tactic_sequences(orig_seqs, use_dataset_tactics=False)
    canonical_tac_col = {ep: all_ep_seqs[ep]["tactic_collapsed"] for ep in all_ep_seqs}

    csv_rows: list[dict[str, Any]] = []
    schemes = ["S1_collapsed_order", "S3_constrained_shuffle", "S2_raw_shuffle_rate"]
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

    # =========================================================================
    # SCHEME S1: Collapsed-Order Shuffle (Headline)
    # =========================================================================
    t0 = time.time()
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S1 (collapsed-order shuffle)...")
    for b in range(B_PERMUTATIONS):
        rng = random.Random(b)

        # S1 Technique
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

        # S1 Tactic
        rng_tac = random.Random(b)
        s1_tac_col = {}
        for ep_id in sorted(canonical_tac_col.keys()):
            shuffled_tac = copy.deepcopy(canonical_tac_col[ep_id])
            rng_tac.shuffle(shuffled_tac)
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

    # =========================================================================
    # SCHEME S3: Constrained Shuffle (No Adjacent Identical Items)
    # =========================================================================
    t_s3 = time.time()
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S3 (constrained shuffle)...")
    s3_tech_tries_list: list[int] = []
    s3_tac_tries_list: list[int] = []
    s3_tech_fails = 0
    s3_tac_fails = 0

    for b in range(B_PERMUTATIONS):
        rng = random.Random(b)

        # S3 Technique
        s3_tech_episodes = {}
        s3_tech_samples = []
        b_tech_tries = 0
        tech_valid = True
        for ep_id, ep_data in sorted(orig_seqs["episodes"].items()):
            shuffled_col, tries = shuffle_constrained_tech(ep_data["collapsed"], rng, MAX_S3_TRIES)
            b_tech_tries += tries
            if shuffled_col is None:
                tech_valid = False
                break
            s3_tech_episodes[ep_id] = {
                "raw": shuffled_col,
                "collapsed": shuffled_col,
            }
            sc_id = EPISODE_MAPPING.get(ep_id, "")
            s3_tech_samples.extend(
                build_samples_for_sequence(shuffled_col, ep_id, sc_id, "collapsed", "full")
            )

        if not tech_valid:
            s3_tech_fails += 1
        else:
            s3_tech_tries_list.append(b_tech_tries)
            n_s3_tech = len(s3_tech_samples)
            assert n_s3_tech == N_tech_obs, f"S3 technique sample count {n_s3_tech} != {N_tech_obs} at seed {b}!"
            sample_counts["S3_constrained_shuffle"]["technique_collapsed_full"].append(n_s3_tech)

            t_res, _ = evaluate_loeo_slice(
                variant="collapsed",
                granularity="full",
                save_fold_models=False,
                sequences_data={"episodes": s3_tech_episodes},
                folds_data=folds_data,
                samples_data=s3_tech_samples,
            )

            s3m_h1 = t_res["headline"]["markov"]["hit1"]
            s3m_h3 = t_res["headline"]["markov"]["hit3"]
            s3f_h1 = t_res["headline"]["frequency"]["hit1"]
            s3f_h3 = t_res["headline"]["frequency"]["hit3"]
            s3fb_h1 = t_res["headline"]["fallback"]["hit1"]
            s3fb_h3 = t_res["headline"]["fallback"]["hit3"]

            s3_tech_vals = {
                "markov_hit1": s3m_h1 / n_s3_tech,
                "markov_hit3": s3m_h3 / n_s3_tech,
                "frequency_hit1": s3f_h1 / n_s3_tech,
                "frequency_hit3": s3f_h3 / n_s3_tech,
                "markov_fallback_hit1": s3fb_h1 / n_s3_tech,
                "markov_fallback_hit3": s3fb_h3 / n_s3_tech,
                "markov_minus_frequency_hit1": (s3m_h1 - s3f_h1) / n_s3_tech,
                "markov_minus_frequency_hit3": (s3m_h3 - s3f_h3) / n_s3_tech,
            }
            s3_tech_hits = {
                "markov_hit1": s3m_h1, "markov_hit3": s3m_h3,
                "frequency_hit1": s3f_h1, "frequency_hit3": s3f_h3,
                "markov_fallback_hit1": s3fb_h1, "markov_fallback_hit3": s3fb_h3,
                "markov_minus_frequency_hit1": s3m_h1 - s3f_h1,
                "markov_minus_frequency_hit3": s3m_h3 - s3f_h3,
            }

            for k, v in s3_tech_vals.items():
                null_distributions["S3_constrained_shuffle"]["technique_collapsed_full"][k].append(v)
                csv_rows.append({
                    "seed": b,
                    "scheme": "S3_constrained_shuffle",
                    "level": "technique_collapsed_full",
                    "statistic": k,
                    "n_samples": n_s3_tech,
                    "hits": s3_tech_hits[k],
                    "null_value": f"{v:.10f}",
                    "observed_value": f"{obs_rates['technique_collapsed_full'][k]:.10f}",
                })

        # S3 Tactic
        rng_tac = random.Random(b)
        s3_tac_col = {}
        b_tac_tries = 0
        tac_valid = True
        for ep_id in sorted(canonical_tac_col.keys()):
            shuffled_tac, tries = shuffle_constrained_tac(canonical_tac_col[ep_id], rng_tac, MAX_S3_TRIES)
            b_tac_tries += tries
            if shuffled_tac is None:
                tac_valid = False
                break
            s3_tac_col[ep_id] = shuffled_tac

        if not tac_valid:
            s3_tac_fails += 1
        else:
            s3_tac_tries_list.append(b_tac_tries)
            orig_te_fn = te.build_tactic_sequences
            te.build_tactic_sequences = lambda seqs, use_dataset_tactics=False: {
                ep: {"tactic_collapsed": s3_tac_col[ep]} for ep in s3_tac_col
            }
            try:
                tac_res, _ = te.evaluate_tactic_slice(
                    variant="tactic_collapsed",
                    folds_data=folds_data,
                )
            finally:
                te.build_tactic_sequences = orig_te_fn

            n_s3_tac = tac_res["n_samples"]
            assert n_s3_tac == N_tac_obs, f"S3 tactic sample count {n_s3_tac} != {N_tac_obs} at seed {b}!"
            sample_counts["S3_constrained_shuffle"]["tactic_collapsed"].append(n_s3_tac)

            s3tm_h1 = tac_res["headline"]["markov"]["hit1"]
            s3tm_h3 = tac_res["headline"]["markov"]["hit3"]
            s3tf_h1 = tac_res["headline"]["frequency"]["hit1"]
            s3tf_h3 = tac_res["headline"]["frequency"]["hit3"]
            s3tfb_h1 = tac_res["headline"]["markov_fallback"]["hit1"]
            s3tfb_h3 = tac_res["headline"]["markov_fallback"]["hit3"]

            s3_tac_vals = {
                "markov_hit1": s3tm_h1 / n_s3_tac,
                "markov_hit3": s3tm_h3 / n_s3_tac,
                "frequency_hit1": s3tf_h1 / n_s3_tac,
                "frequency_hit3": s3tf_h3 / n_s3_tac,
                "markov_fallback_hit1": s3tfb_h1 / n_s3_tac,
                "markov_fallback_hit3": s3tfb_h3 / n_s3_tac,
                "markov_minus_frequency_hit1": (s3tm_h1 - s3tf_h1) / n_s3_tac,
                "markov_minus_frequency_hit3": (s3tm_h3 - s3tf_h3) / n_s3_tac,
            }
            s3_tac_hits = {
                "markov_hit1": s3tm_h1, "markov_hit3": s3tm_h3,
                "frequency_hit1": s3tf_h1, "frequency_hit3": s3tf_h3,
                "markov_fallback_hit1": s3tfb_h1, "markov_fallback_hit3": s3tfb_h3,
                "markov_minus_frequency_hit1": s3tm_h1 - s3tf_h1,
                "markov_minus_frequency_hit3": s3tm_h3 - s3tf_h3,
            }

            for k, v in s3_tac_vals.items():
                null_distributions["S3_constrained_shuffle"]["tactic_collapsed"][k].append(v)
                csv_rows.append({
                    "seed": b,
                    "scheme": "S3_constrained_shuffle",
                    "level": "tactic_collapsed",
                    "statistic": k,
                    "n_samples": n_s3_tac,
                    "hits": s3_tac_hits[k],
                    "null_value": f"{v:.10f}",
                    "observed_value": f"{obs_rates['tactic_collapsed'][k]:.10f}",
                })

    assert s3_tech_fails <= 0.05 * B_PERMUTATIONS, f"S3 technique failed > 5% permutations: {s3_tech_fails}"
    assert s3_tac_fails <= 0.05 * B_PERMUTATIONS, f"S3 tactic failed > 5% permutations: {s3_tac_fails}"
    print(f"S3 finished in {time.time() - t_s3:.2f}s. (Tech fails: {s3_tech_fails}, Tac fails: {s3_tac_fails})")

    # =========================================================================
    # SCHEME S2: Raw Shuffle Rate-Based (Sensitivity)
    # =========================================================================
    t1 = time.time()
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S2 (raw event shuffle, rate-based)...")
    for b in range(B_PERMUTATIONS):
        rng = random.Random(b)

        # S2 Technique
        s2_tech_episodes = {}
        s2_tech_samples = []
        for ep_id, ep_data in sorted(orig_seqs["episodes"].items()):
            shuffled_raw = copy.deepcopy(ep_data["raw"])
            rng.shuffle(shuffled_raw)
            re_collapsed = collapse_sequence(shuffled_raw)
            s2_tech_episodes[ep_id] = {
                "raw": shuffled_raw,
                "collapsed": re_collapsed,
            }
            sc_id = EPISODE_MAPPING.get(ep_id, "")
            s2_tech_samples.extend(
                build_samples_for_sequence(re_collapsed, ep_id, sc_id, "collapsed", "full")
            )

        n_s2_tech = len(s2_tech_samples)
        sample_counts["S2_raw_shuffle_rate"]["technique_collapsed_full"].append(n_s2_tech)

        t_res, _ = evaluate_loeo_slice(
            variant="collapsed",
            granularity="full",
            save_fold_models=False,
            sequences_data={"episodes": s2_tech_episodes},
            folds_data=folds_data,
            samples_data=s2_tech_samples,
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

        # S2 Tactic
        rng_tac = random.Random(b)
        s2_perm_seqs = {"episodes": {}}
        for ep_id, ep_data in sorted(orig_seqs["episodes"].items()):
            shuffled_raw = copy.deepcopy(ep_data["raw"])
            rng_tac.shuffle(shuffled_raw)
            re_collapsed = collapse_sequence(shuffled_raw)
            s2_perm_seqs["episodes"][ep_id] = {
                "raw": shuffled_raw,
                "collapsed": re_collapsed,
            }

        tac_seqs_perm = te.build_tactic_sequences(s2_perm_seqs, use_dataset_tactics=False)
        orig_te_fn = te.build_tactic_sequences
        te.build_tactic_sequences = lambda seqs, use_dataset_tactics=False: tac_seqs_perm
        try:
            tac_res, _ = te.evaluate_tactic_slice(
                variant="tactic_collapsed",
                folds_data=folds_data,
            )
        finally:
            te.build_tactic_sequences = orig_te_fn

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
            "test_name": "Permutation Test on Real Episodes (E1-E4) v2.1",
            "b_permutations": B_PERMUTATIONS,
            "decision_rule": "p < 0.05 under primary scheme S1; S3 reported alongside to remove adjacency artifact; S2 reported as sensitivity",
            "p_value_formula": "p = (1 + count(null >= observed)) / (1 + B)",
            "observed_sample_counts": {
                "technique_collapsed_full": N_tech_obs,
                "tactic_collapsed": N_tac_obs,
            },
            "observed_baseline_counts": obs_counts,
            "observed_baseline_rates": obs_rates,
            "sample_counts_summary": {},
            "s3_rejection_sampling_summary": {
                "max_tries_per_episode": MAX_S3_TRIES,
                "technique_collapsed_full": {
                    "excluded_permutations": s3_tech_fails,
                    "min_total_tries": min(s3_tech_tries_list) if s3_tech_tries_list else 0,
                    "mean_total_tries": sum(s3_tech_tries_list) / len(s3_tech_tries_list) if s3_tech_tries_list else 0.0,
                    "max_total_tries": max(s3_tech_tries_list) if s3_tech_tries_list else 0,
                },
                "tactic_collapsed": {
                    "excluded_permutations": s3_tac_fails,
                    "min_total_tries": min(s3_tac_tries_list) if s3_tac_tries_list else 0,
                    "mean_total_tries": sum(s3_tac_tries_list) / len(s3_tac_tries_list) if s3_tac_tries_list else 0.0,
                    "max_total_tries": max(s3_tac_tries_list) if s3_tac_tries_list else 0,
                },
            },
        },
        "schemes": {},
        "scheme_validity_check": {},
    }

    for sc in schemes:
        report_data["metadata"]["sample_counts_summary"][sc] = {}
        for lvl in levels:
            ns = sample_counts[sc][lvl]
            report_data["metadata"]["sample_counts_summary"][sc][lvl] = {
                "min": min(ns) if ns else 0,
                "mean": sum(ns) / len(ns) if ns else 0.0,
                "max": max(ns) if ns else 0,
                "is_constant": bool(min(ns) == max(ns)) if ns else False,
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

    # Scheme validity check (Order-Free Frequency Statistics)
    order_free_stats = ["frequency_hit1", "frequency_hit3"]
    for sc in schemes:
        sig_stats = []
        for lvl in levels:
            for st in order_free_stats:
                d = report_data["schemes"][sc][lvl][st]
                if d["p_value"] < 0.05:
                    sig_stats.append({
                        "level": lvl,
                        "statistic": st,
                        "observed": d["observed"],
                        "null_mean": d["null_mean"],
                        "p_value": d["p_value"],
                    })

        is_valid = len(sig_stats) == 0
        if not is_valid:
            sig_desc = ", ".join(f"{s['level']} {s['statistic']} (p={s['p_value']:.4f})" for s in sig_stats)
            warning_msg = (
                f"WARNING: Scheme '{sc}' exhibits statistically significant deviation (p < 0.05) "
                f"on order-free Frequency statistic(s): {sig_desc}. This indicates that the scheme perturbs "
                f"marginal distributions/compositions in addition to sequence order. Therefore, it is NOT "
                f"an order-only null and MUST NOT be used for an order-signal claim."
            )
        else:
            warning_msg = None

        report_data["scheme_validity_check"][sc] = {
            "order_free_stats_checked": [f"{lvl}:{st}" for lvl in levels for st in order_free_stats],
            "significant_order_free_stats": sig_stats,
            "is_valid_order_null": is_valid,
            "warning": warning_msg,
        }

    # Write JSON
    print(f"Writing report JSON to {JSON_OUT_PATH}...")
    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Generate Markdown
    print(f"Writing report Markdown to {MD_OUT_PATH}...")
    generate_markdown_report_v2(report_data)

    print("Permutation test v2.1 completed successfully.")
    return report_data


def generate_markdown_report_v2(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    meta = data["metadata"]
    s_sum = meta["sample_counts_summary"]
    val_check = data["scheme_validity_check"]
    s3_meta = meta["s3_rejection_sampling_summary"]

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

    A("# Permutation Test on Real Episodes (E1–E4) v2.1 Report")
    A()
    A("## Pre-Declared Test Design & Purpose")
    A()
    A("- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines in real telemetry episodes E1–E4.")
    A("- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: The items of the stored collapsed sequence for each episode are shuffled strictly within the episode. Sample counts $N$ are strictly invariant ($N=67$ for technique, $N=53$ for tactic in every permutation). Headline decisions are made under S1.")
    A("- **Constrained Scheme (S3 - Adjacency-Constrained Shuffle)**: Shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items have identical technique sets (technique level) or identical tactic sets (tactic level), using rejection sampling with up to 10,000 tries per episode. Added after the S1 and S2 results to remove an artifact (adjacent identical items introduced by unconstrained shuffling that are absent in real collapsed data). S1 remains the pre-declared headline; S3 is reported alongside it, and if S1 and S3 disagree, both are reported.")
    A("- **Sensitivity Scheme (S2 - Raw-Shuffle Rate-Based)**: Raw labeled events are shuffled within each episode and re-collapsed, yielding variable sample counts ($N \\in [82, 95]$ technique, $N \\in [74, 90]$ tactic). Evaluated as hit rate (hits / $N_{perm}$) compared against observed hit rate.")
    A("- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999).")
    A(f"- **One-Sided p-value Formula**: `{meta['p_value_formula']}`.")
    A("- **Pre-Declared Decision Rule**: `p < 0.05` under S1/S3. Sensitivity scheme S2 is documented alongside S1 and S3 for methodological completeness.")
    A("- **Conclusion Text Generation Rule**: Every conclusion sentence is generated strictly by code from the p-value: if $p < 0.05$, *'observed exceeds the shuffled-order null (p=...)'*; else *'not distinguishable from the shuffled-order null at this sample size (this is not proof of absence)'*. No causal inferences are asserted.")
    A()
    A("---")
    A()
    A("## Scheme Validity Check (Order-Free Frequency Statistics)")
    A()
    A("A valid order-only null permutation must not perturb the performance of an **order-free** model (FrequencyBaseline). If an order-free statistic exhibits $p < 0.05$, the scheme alters marginal event distributions or set compositions in addition to order, confounding order-signal tests.")
    A()
    A("| Scheme | Level | Statistic | Observed Rate | Null Mean Rate | p-value | Order-Free Status |")
    A("|:---|:---|:---|:---:|:---:|:---:|:---|")
    for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)"), ("S2_raw_shuffle_rate", "S2 (Raw-Shuffle)")]:
        for lvl, lvl_label in [("technique_collapsed_full", "Technique"), ("tactic_collapsed", "Tactic")]:
            for st in ["frequency_hit1", "frequency_hit3"]:
                row = data["schemes"][sc][lvl][st]
                lbl = stat_labels[st]
                status_str = "**FLAG (p < 0.05)**" if row["p_value"] < 0.05 else "PASS (Valid)"
                A(f"| {sc_label} | {lvl_label} | {lbl} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['p_value']:.4f} | {status_str} |")
    A()
    for sc, sc_label in [("S1_collapsed_order", "S1"), ("S3_constrained_shuffle", "S3"), ("S2_raw_shuffle_rate", "S2")]:
        chk = val_check[sc]
        if not chk["is_valid_order_null"]:
            A(f"> [!WARNING]")
            A(f"> **Scheme Validity Warning ({sc_label})**: {chk['warning']}")
            A()
        else:
            A(f"- **{sc_label} Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \\ge 0.05$).")
    A()
    A("---")
    A()
    A("## Sample Count Distribution (Confound Resolution)")
    A()
    A("| Scheme | Level | Observed N | Permutation Min N | Permutation Mean N | Permutation Max N | Invariant N? |")
    A("|:---|:---|:---:|:---:|:---:|:---:|:---:|")
    for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)"), ("S2_raw_shuffle_rate", "S2 (Raw-Shuffle)")]:
        for lvl, lvl_label in [("technique_collapsed_full", "Technique (collapsed_full)"), ("tactic_collapsed", "Tactic (tactic_collapsed)")]:
            info = s_sum[sc][lvl]
            obs_n = meta["observed_sample_counts"][lvl]
            inv_str = "**YES (Constant)**" if info["is_constant"] else "NO (Variable)"
            A(f"| {sc_label} | {lvl_label} | {obs_n} | {info['min']} | {info['mean']:.2f} | {info['max']} | {inv_str} |")
    A()
    A("### S3 Constrained Shuffle Rejection Sampling Statistics")
    A()
    A(f"- **Max Tries Allowed Per Episode**: {s3_meta['max_tries_per_episode']}")
    A(f"- **Technique Level**: Excluded Permutations = {s3_meta['technique_collapsed_full']['excluded_permutations']}, Min Tries = {s3_meta['technique_collapsed_full']['min_total_tries']}, Mean Tries = {s3_meta['technique_collapsed_full']['mean_total_tries']:.2f}, Max Tries = {s3_meta['technique_collapsed_full']['max_total_tries']}")
    A(f"- **Tactic Level**: Excluded Permutations = {s3_meta['tactic_collapsed']['excluded_permutations']}, Min Tries = {s3_meta['tactic_collapsed']['min_total_tries']}, Mean Tries = {s3_meta['tactic_collapsed']['mean_total_tries']:.2f}, Max Tries = {s3_meta['tactic_collapsed']['max_total_tries']}")
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
    A("## Constrained Scheme S3 Results (Adjacency-Constrained Null)")
    A()
    A("### Technique Level (`collapsed_full`, N=67)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s3_tech = data["schemes"]["S3_constrained_shuffle"]["technique_collapsed_full"]
    for st, lbl in stat_labels.items():
        row = s3_tech[st]
        h_str = f"{counts_tech[st]:+d} / 67" if "minus" in st else f"{counts_tech[st]} / 67"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N=53)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s3_tac = data["schemes"]["S3_constrained_shuffle"]["tactic_collapsed"]
    for st, lbl in stat_labels.items():
        row = s3_tac[st]
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
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---|")
    s2_tech = data["schemes"]["S2_raw_shuffle_rate"]["technique_collapsed_full"]
    for st, lbl in stat_labels.items():
        row = s2_tech[st]
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N_perm in [74, 90])")
    A()
    A("| Statistic | Observed Rate | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---|")
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
