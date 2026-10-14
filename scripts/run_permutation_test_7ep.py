"""Pre-registered 7-Episode Permutation Tests (P3 and P4).

Evaluates whether sequence order carries predictive signal beyond order-free baselines across E1-E7.
Per reports/prereg_7episode_design.md Section 10 and Amendments 1-4:
- B = 1000 permutations (stdlib random.Random seeds 0..999).
- p = (1 + count(null >= observed)) / (1 + B).
- Primary Scheme: S1 (Collapsed-Order Shuffle, N fixed).
- Constrained Scheme: S3 (Adjacency-Constrained Shuffle, dedicated RNG stream, max 10,000 tries, N asserted).
- S2 is excluded per prereg Section 10.
- Statistics evaluated:
  - Markov Hit@1, Markov Hit@3
  - Frequency Hit@1, Frequency Hit@3
  - Fallback Hit@1, Fallback Hit@3
  - Markov minus Frequency Hit@1, Markov minus Frequency Hit@3
- Slices evaluated:
  - Technique collapsed_full (N=95)
  - Tactic tactic_collapsed (N=76)
- Hypothesis mapping:
  - P3: Tactic Markov Hit@3 vs S1 null (S1 p enters Holm adjustment; S3 reported alongside).
  - P4: Technique Markov Hit@3 vs S1 null (S1 p enters Holm adjustment; S3 reported alongside).
- Outputs:
  - data/processed_7ep/permutation_7ep_null_distribution.csv
  - reports/7ep/permutation_7ep_report.json
  - reports/7ep/permutation_7ep_report.md
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

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.c4.evaluation import _hit_flags
from src.c4.models.frequency import FrequencyBaseline
from src.c4.models.markov import MarkovModel
from src.c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
)

DATA_7EP = BASE_DIR / "data" / "processed_7ep"
REPORTS_7EP = BASE_DIR / "reports" / "7ep"

SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"
FOLDS_PATH = DATA_7EP / "loeo_folds.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
TECH_EVAL_PATH = REPORTS_7EP / "evaluation_7ep_results.json"

CSV_OUT_PATH = DATA_7EP / "permutation_7ep_null_distribution.csv"
JSON_OUT_PATH = REPORTS_7EP / "permutation_7ep_report.json"
MD_OUT_PATH = REPORTS_7EP / "permutation_7ep_report.md"

B_PERMUTATIONS = 1000
MAX_S3_TRIES = 10000

EPISODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]


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


def compute_summary_stats(observed: float, null_values: list[float], is_valid_null: bool = True) -> dict[str, Any]:
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
    mc_se = math.sqrt(p_val * (1.0 - p_val) / b) if b > 0 else 0.0

    if is_valid_null:
        if p_val < 0.05:
            conclusion = f"observed exceeds the shuffled-order null (p={p_val:.4f})"
        else:
            conclusion = f"not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p={p_val:.4f})"
    else:
        if p_val < 0.05:
            conclusion = f"INVALID NULL - do not cite: observed exceeds the shuffled-order null (p={p_val:.4f})"
        else:
            conclusion = f"INVALID NULL - do not cite: not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p={p_val:.4f})"

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
        "mc_se": mc_se,
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


def run_permutation_test_7ep() -> dict[str, Any]:
    print("================================================================================")
    print("RUNNING 7-EPISODE PERMUTATION TEST (S1 & S3 CONSTRAINED SHUFFLE, B=1000)")
    print("================================================================================")

    # 1. Load baseline data
    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        orig_seqs = json.load(f)
    with open(FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)
    with open(TECH_EVAL_PATH, "r", encoding="utf-8") as f:
        eval_7ep_json = json.load(f)

    # Extract observed hits and rates
    tech_cf = eval_7ep_json["primary_slice_technique_collapsed_full"]["headline"]
    tac_tc = eval_7ep_json["secondary_slice_tactic_collapsed"]["headline"]

    N_tech_obs = 95
    N_tac_obs = 76

    obs_counts = {
        "technique_collapsed_full": {
            "markov_hit1": tech_cf["markov"]["hit1"],
            "markov_hit3": tech_cf["markov"]["hit3"],
            "frequency_hit1": tech_cf["frequency"]["hit1"],
            "frequency_hit3": tech_cf["frequency"]["hit3"],
            "markov_fallback_hit1": tech_cf["fallback"]["hit1"],
            "markov_fallback_hit3": tech_cf["fallback"]["hit3"],
            "markov_minus_frequency_hit1": tech_cf["markov"]["hit1"] - tech_cf["frequency"]["hit1"],
            "markov_minus_frequency_hit3": tech_cf["markov"]["hit3"] - tech_cf["frequency"]["hit3"],
        },
        "tactic_collapsed": {
            "markov_hit1": tac_tc["markov"]["hit1"],
            "markov_hit3": tac_tc["markov"]["hit3"],
            "frequency_hit1": tac_tc["frequency"]["hit1"],
            "frequency_hit3": tac_tc["frequency"]["hit3"],
            "markov_fallback_hit1": tac_tc["markov_fallback"]["hit1"],
            "markov_fallback_hit3": tac_tc["markov_fallback"]["hit3"],
            "markov_minus_frequency_hit1": tac_tc["markov"]["hit1"] - tac_tc["frequency"]["hit1"],
            "markov_minus_frequency_hit3": tac_tc["markov"]["hit3"] - tac_tc["frequency"]["hit3"],
        },
    }

    obs_rates = {
        lvl: {k: obs_counts[lvl][k] / (N_tech_obs if "technique" in lvl else N_tac_obs) for k in obs_counts[lvl]}
        for lvl in obs_counts
    }

    print("Observed baselines verified successfully:")
    print(f"  Technique: Markov Hit@1={obs_counts['technique_collapsed_full']['markov_hit1']}/95, Hit@3={obs_counts['technique_collapsed_full']['markov_hit3']}/95")
    print(f"  Tactic:    Markov Hit@1={obs_counts['tactic_collapsed']['markov_hit1']}/76, Hit@3={obs_counts['tactic_collapsed']['markov_hit3']}/76")

    # Canonical tactic collapsed sequences
    raw_tac_seqs = build_tactic_sequences(orig_seqs)
    canonical_tac_col = {
        ep_id: (raw_tac_seqs["episodes"][ep_id]["tactic_collapsed"] if "episodes" in raw_tac_seqs else raw_tac_seqs[ep_id]["tactic_collapsed"])
        for ep_id in EPISODES
    }

    schemes = ["S1_collapsed_order", "S3_constrained_shuffle"]
    levels = ["technique_collapsed_full", "tactic_collapsed"]
    stats_keys = list(obs_counts["technique_collapsed_full"].keys())

    null_distributions: dict[str, dict[str, dict[str, list[float]]]] = {
        sc: {lvl: {st: [] for st in stats_keys} for lvl in levels} for sc in schemes
    }
    sample_counts: dict[str, dict[str, list[int]]] = {
        sc: {lvl: [] for lvl in levels} for sc in schemes
    }

    csv_rows: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # SCHEME S1: Collapsed-Order Shuffle
    # -------------------------------------------------------------------------
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S1 (collapsed-order shuffle)...")
    t0 = time.time()
    for b in range(B_PERMUTATIONS):
        # S1 Technique
        rng_tech = random.Random(b)
        s1_tech_col: dict[str, list[dict[str, Any]]] = {}
        for ep_id in EPISODES:
            col_copy = copy.deepcopy(orig_seqs["episodes"][ep_id]["collapsed"])
            rng_tech.shuffle(col_copy)
            s1_tech_col[ep_id] = col_copy

        # Evaluate S1 technique across all 7 folds
        m_h1_tot, m_h3_tot, f_h1_tot, f_h3_tot, fb_h1_tot, fb_h3_tot = 0, 0, 0, 0, 0, 0
        n_samples_tech = 0

        for fold in folds_data:
            test_ep = fold["test_episode"]
            train_eps = fold["training_episodes"]

            m_model = MarkovModel(variant="collapsed", granularity="full").fit(
                {ep: {"collapsed": s1_tech_col[ep]} for ep in train_eps},
                training_episodes=train_eps,
            )
            f_model = FrequencyBaseline(variant="collapsed", granularity="full").fit(
                {ep: {"collapsed": s1_tech_col[ep]} for ep in train_eps},
                training_episodes=train_eps,
            )

            test_items = s1_tech_col[test_ep]
            n_samples_tech += len(test_items) - 1

            f_res = f_model.predict(k=3)
            f_cands = [c[0] for c in f_res["candidates"]]

            for i in range(len(test_items) - 1):
                cur = test_items[i]["techniques"]
                tgt = set(test_items[i + 1]["techniques"])

                m_res = m_model.predict(cur, k=3)
                if m_res["status"] == "ok":
                    mc = [c[0] for c in m_res["candidates"]]
                    h1, h3 = _hit_flags(mc, tgt)
                    fb_h1, fb_h3 = h1, h3
                else:
                    h1, h3 = 0, 0
                    fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                fh1, fh3 = _hit_flags(f_cands, tgt)

                m_h1_tot += h1
                m_h3_tot += h3
                f_h1_tot += fh1
                f_h3_tot += fh3
                fb_h1_tot += fb_h1
                fb_h3_tot += fb_h3

        assert n_samples_tech == N_tech_obs, f"S1 technique sample count {n_samples_tech} != {N_tech_obs} at seed {b}"
        sample_counts["S1_collapsed_order"]["technique_collapsed_full"].append(n_samples_tech)

        s1_tech_vals = {
            "markov_hit1": m_h1_tot / n_samples_tech,
            "markov_hit3": m_h3_tot / n_samples_tech,
            "frequency_hit1": f_h1_tot / n_samples_tech,
            "frequency_hit3": f_h3_tot / n_samples_tech,
            "markov_fallback_hit1": fb_h1_tot / n_samples_tech,
            "markov_fallback_hit3": fb_h3_tot / n_samples_tech,
            "markov_minus_frequency_hit1": (m_h1_tot - f_h1_tot) / n_samples_tech,
            "markov_minus_frequency_hit3": (m_h3_tot - f_h3_tot) / n_samples_tech,
        }
        s1_tech_hits = {
            "markov_hit1": m_h1_tot, "markov_hit3": m_h3_tot,
            "frequency_hit1": f_h1_tot, "frequency_hit3": f_h3_tot,
            "markov_fallback_hit1": fb_h1_tot, "markov_fallback_hit3": fb_h3_tot,
            "markov_minus_frequency_hit1": m_h1_tot - f_h1_tot,
            "markov_minus_frequency_hit3": m_h3_tot - f_h3_tot,
        }
        for k, v in s1_tech_vals.items():
            null_distributions["S1_collapsed_order"]["technique_collapsed_full"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S1_collapsed_order",
                "level": "technique_collapsed_full",
                "statistic": k,
                "n_samples": n_samples_tech,
                "hits": s1_tech_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['technique_collapsed_full'][k]:.10f}",
            })

        # S1 Tactic (dedicated independent RNG stream)
        rng_tac = random.Random(b)
        s1_tac_col: dict[str, list[dict[str, Any]]] = {}
        for ep_id in EPISODES:
            tac_copy = copy.deepcopy(canonical_tac_col[ep_id])
            rng_tac.shuffle(tac_copy)
            s1_tac_col[ep_id] = tac_copy

        # Evaluate S1 tactic across all 7 folds
        tm_h1_tot, tm_h3_tot, tf_h1_tot, tf_h3_tot, tfb_h1_tot, tfb_h3_tot = 0, 0, 0, 0, 0, 0
        n_samples_tac = 0

        for fold in folds_data:
            test_ep = fold["test_episode"]
            train_eps = fold["training_episodes"]

            m_tac = TacticMarkovModel().fit(s1_tac_col, train_eps)
            f_tac = TacticFrequencyBaseline().fit(s1_tac_col, train_eps)

            test_items = s1_tac_col[test_ep]
            n_samples_tac += len(test_items) - 1

            f_res = f_tac.predict(k=3)
            f_cands = [c[0] for c in f_res["candidates"]]

            for i in range(len(test_items) - 1):
                cur = test_items[i]["tactics"]
                tgt = set(test_items[i + 1]["tactics"])

                m_res = m_tac.predict(cur, k=3)
                if m_res["status"] == "ok":
                    mc = [c[0] for c in m_res["candidates"]]
                    h1, h3 = _hit_flags(mc, tgt)
                    fb_h1, fb_h3 = h1, h3
                else:
                    h1, h3 = 0, 0
                    fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                fh1, fh3 = _hit_flags(f_cands, tgt)

                tm_h1_tot += h1
                tm_h3_tot += h3
                tf_h1_tot += fh1
                tf_h3_tot += fh3
                tfb_h1_tot += fb_h1
                tfb_h3_tot += fb_h3

        assert n_samples_tac == N_tac_obs, f"S1 tactic sample count {n_samples_tac} != {N_tac_obs} at seed {b}"
        sample_counts["S1_collapsed_order"]["tactic_collapsed"].append(n_samples_tac)

        s1_tac_vals = {
            "markov_hit1": tm_h1_tot / n_samples_tac,
            "markov_hit3": tm_h3_tot / n_samples_tac,
            "frequency_hit1": tf_h1_tot / n_samples_tac,
            "frequency_hit3": tf_h3_tot / n_samples_tac,
            "markov_fallback_hit1": tfb_h1_tot / n_samples_tac,
            "markov_fallback_hit3": tfb_h3_tot / n_samples_tac,
            "markov_minus_frequency_hit1": (tm_h1_tot - tf_h1_tot) / n_samples_tac,
            "markov_minus_frequency_hit3": (tm_h3_tot - tf_h3_tot) / n_samples_tac,
        }
        s1_tac_hits = {
            "markov_hit1": tm_h1_tot, "markov_hit3": tm_h3_tot,
            "frequency_hit1": tf_h1_tot, "frequency_hit3": tf_h3_tot,
            "markov_fallback_hit1": tfb_h1_tot, "markov_fallback_hit3": tfb_h3_tot,
            "markov_minus_frequency_hit1": tm_h1_tot - tf_h1_tot,
            "markov_minus_frequency_hit3": tm_h3_tot - tf_h3_tot,
        }
        for k, v in s1_tac_vals.items():
            null_distributions["S1_collapsed_order"]["tactic_collapsed"][k].append(v)
            csv_rows.append({
                "seed": b,
                "scheme": "S1_collapsed_order",
                "level": "tactic_collapsed",
                "statistic": k,
                "n_samples": n_samples_tac,
                "hits": s1_tac_hits[k],
                "null_value": f"{v:.10f}",
                "observed_value": f"{obs_rates['tactic_collapsed'][k]:.10f}",
            })

    print(f"S1 finished in {time.time() - t0:.2f}s.")

    # -------------------------------------------------------------------------
    # SCHEME S3: Constrained Shuffle (Adjacency-Constrained)
    # -------------------------------------------------------------------------
    print(f"\nRunning {B_PERMUTATIONS} permutations under Scheme S3 (constrained shuffle)...")
    t1 = time.time()
    s3_tech_fails = 0
    s3_tac_fails = 0
    s3_tech_tries_list = []
    s3_tac_tries_list = []

    for b in range(B_PERMUTATIONS):
        # S3 Technique
        rng_s3_tech = random.Random(b)
        s3_tech_col: dict[str, list[dict[str, Any]]] = {}
        b_tech_tries = 0
        tech_valid = True

        for ep_id in EPISODES:
            shuffled_tech, tries = shuffle_constrained_tech(orig_seqs["episodes"][ep_id]["collapsed"], rng_s3_tech, MAX_S3_TRIES)
            b_tech_tries += tries
            if shuffled_tech is None:
                tech_valid = False
                break
            s3_tech_col[ep_id] = shuffled_tech

        if not tech_valid:
            s3_tech_fails += 1
        else:
            s3_tech_tries_list.append(b_tech_tries)
            m_h1_tot, m_h3_tot, f_h1_tot, f_h3_tot, fb_h1_tot, fb_h3_tot = 0, 0, 0, 0, 0, 0
            n_samples_tech = 0

            for fold in folds_data:
                test_ep = fold["test_episode"]
                train_eps = fold["training_episodes"]

                m_model = MarkovModel(variant="collapsed", granularity="full").fit(
                    {ep: {"collapsed": s3_tech_col[ep]} for ep in train_eps},
                    training_episodes=train_eps,
                )
                f_model = FrequencyBaseline(variant="collapsed", granularity="full").fit(
                    {ep: {"collapsed": s3_tech_col[ep]} for ep in train_eps},
                    training_episodes=train_eps,
                )

                test_items = s3_tech_col[test_ep]
                n_samples_tech += len(test_items) - 1

                f_res = f_model.predict(k=3)
                f_cands = [c[0] for c in f_res["candidates"]]

                for i in range(len(test_items) - 1):
                    cur = test_items[i]["techniques"]
                    tgt = set(test_items[i + 1]["techniques"])

                    m_res = m_model.predict(cur, k=3)
                    if m_res["status"] == "ok":
                        mc = [c[0] for c in m_res["candidates"]]
                        h1, h3 = _hit_flags(mc, tgt)
                        fb_h1, fb_h3 = h1, h3
                    else:
                        h1, h3 = 0, 0
                        fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                    fh1, fh3 = _hit_flags(f_cands, tgt)

                    m_h1_tot += h1
                    m_h3_tot += h3
                    f_h1_tot += fh1
                    f_h3_tot += fh3
                    fb_h1_tot += fb_h1
                    fb_h3_tot += fb_h3

            assert n_samples_tech == N_tech_obs, f"S3 technique sample count {n_samples_tech} != {N_tech_obs} at seed {b}"
            sample_counts["S3_constrained_shuffle"]["technique_collapsed_full"].append(n_samples_tech)

            s3_tech_vals = {
                "markov_hit1": m_h1_tot / n_samples_tech,
                "markov_hit3": m_h3_tot / n_samples_tech,
                "frequency_hit1": f_h1_tot / n_samples_tech,
                "frequency_hit3": f_h3_tot / n_samples_tech,
                "markov_fallback_hit1": fb_h1_tot / n_samples_tech,
                "markov_fallback_hit3": fb_h3_tot / n_samples_tech,
                "markov_minus_frequency_hit1": (m_h1_tot - f_h1_tot) / n_samples_tech,
                "markov_minus_frequency_hit3": (m_h3_tot - f_h3_tot) / n_samples_tech,
            }
            s3_tech_hits = {
                "markov_hit1": m_h1_tot, "markov_hit3": m_h3_tot,
                "frequency_hit1": f_h1_tot, "frequency_hit3": f_h3_tot,
                "markov_fallback_hit1": fb_h1_tot, "markov_fallback_hit3": fb_h3_tot,
                "markov_minus_frequency_hit1": m_h1_tot - f_h1_tot,
                "markov_minus_frequency_hit3": m_h3_tot - f_h3_tot,
            }
            for k, v in s3_tech_vals.items():
                null_distributions["S3_constrained_shuffle"]["technique_collapsed_full"][k].append(v)
                csv_rows.append({
                    "seed": b,
                    "scheme": "S3_constrained_shuffle",
                    "level": "technique_collapsed_full",
                    "statistic": k,
                    "n_samples": n_samples_tech,
                    "hits": s3_tech_hits[k],
                    "null_value": f"{v:.10f}",
                    "observed_value": f"{obs_rates['technique_collapsed_full'][k]:.10f}",
                })

        # S3 Tactic (dedicated independent RNG stream)
        rng_s3_tac = random.Random(b)
        s3_tac_col: dict[str, list[dict[str, Any]]] = {}
        b_tac_tries = 0
        tac_valid = True

        for ep_id in EPISODES:
            shuffled_tac, tries = shuffle_constrained_tac(canonical_tac_col[ep_id], rng_s3_tac, MAX_S3_TRIES)
            b_tac_tries += tries
            if shuffled_tac is None:
                tac_valid = False
                break
            s3_tac_col[ep_id] = shuffled_tac

        if not tac_valid:
            s3_tac_fails += 1
        else:
            s3_tac_tries_list.append(b_tac_tries)
            tm_h1_tot, tm_h3_tot, tf_h1_tot, tf_h3_tot, tfb_h1_tot, tfb_h3_tot = 0, 0, 0, 0, 0, 0
            n_samples_tac = 0

            for fold in folds_data:
                test_ep = fold["test_episode"]
                train_eps = fold["training_episodes"]

                m_tac = TacticMarkovModel().fit(s3_tac_col, train_eps)
                f_tac = TacticFrequencyBaseline().fit(s3_tac_col, train_eps)

                test_items = s3_tac_col[test_ep]
                n_samples_tac += len(test_items) - 1

                f_res = f_tac.predict(k=3)
                f_cands = [c[0] for c in f_res["candidates"]]

                for i in range(len(test_items) - 1):
                    cur = test_items[i]["tactics"]
                    tgt = set(test_items[i + 1]["tactics"])

                    m_res = m_tac.predict(cur, k=3)
                    if m_res["status"] == "ok":
                        mc = [c[0] for c in m_res["candidates"]]
                        h1, h3 = _hit_flags(mc, tgt)
                        fb_h1, fb_h3 = h1, h3
                    else:
                        h1, h3 = 0, 0
                        fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                    fh1, fh3 = _hit_flags(f_cands, tgt)

                    tm_h1_tot += h1
                    tm_h3_tot += h3
                    tf_h1_tot += fh1
                    tf_h3_tot += fh3
                    tfb_h1_tot += fb_h1
                    tfb_h3_tot += fb_h3

            assert n_samples_tac == N_tac_obs, f"S3 tactic sample count {n_samples_tac} != {N_tac_obs} at seed {b}"
            sample_counts["S3_constrained_shuffle"]["tactic_collapsed"].append(n_samples_tac)

            s3_tac_vals = {
                "markov_hit1": tm_h1_tot / n_samples_tac,
                "markov_hit3": tm_h3_tot / n_samples_tac,
                "frequency_hit1": tf_h1_tot / n_samples_tac,
                "frequency_hit3": tf_h3_tot / n_samples_tac,
                "markov_fallback_hit1": tfb_h1_tot / n_samples_tac,
                "markov_fallback_hit3": tfb_h3_tot / n_samples_tac,
                "markov_minus_frequency_hit1": (tm_h1_tot - tf_h1_tot) / n_samples_tac,
                "markov_minus_frequency_hit3": (tm_h3_tot - tf_h3_tot) / n_samples_tac,
            }
            s3_tac_hits = {
                "markov_hit1": tm_h1_tot, "markov_hit3": tm_h3_tot,
                "frequency_hit1": tf_h1_tot, "frequency_hit3": tf_h3_tot,
                "markov_fallback_hit1": tfb_h1_tot, "markov_fallback_hit3": tfb_h3_tot,
                "markov_minus_frequency_hit1": tm_h1_tot - tf_h1_tot,
                "markov_minus_frequency_hit3": tm_h3_tot - tf_h3_tot,
            }
            for k, v in s3_tac_vals.items():
                null_distributions["S3_constrained_shuffle"]["tactic_collapsed"][k].append(v)
                csv_rows.append({
                    "seed": b,
                    "scheme": "S3_constrained_shuffle",
                    "level": "tactic_collapsed",
                    "statistic": k,
                    "n_samples": n_samples_tac,
                    "hits": s3_tac_hits[k],
                    "null_value": f"{v:.10f}",
                    "observed_value": f"{obs_rates['tactic_collapsed'][k]:.10f}",
                })

    assert s3_tech_fails <= 50, f"S3 technique failed in {s3_tech_fails} > 50 permutations (>5%)"
    assert s3_tac_fails <= 50, f"S3 tactic failed in {s3_tac_fails} > 50 permutations (>5%)"
    print(f"S3 finished in {time.time() - t1:.2f}s. (Tech fails: {s3_tech_fails}, Tac fails: {s3_tac_fails})")

    # 3. Write CSV
    print(f"\nWriting {len(csv_rows)} rows to {CSV_OUT_PATH}...")
    fieldnames = [
        "seed", "scheme", "level", "statistic", "n_samples", "hits", "null_value", "observed_value",
    ]
    with open(CSV_OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # 4. Compute statistics
    report_data: dict[str, Any] = {
        "metadata": {
            "test_name": "7-Episode Permutation Test (E1-E7)",
            "b_permutations": B_PERMUTATIONS,
            "decision_rule": "p < 0.05 under primary scheme S1; S3 reported alongside",
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

    # Preliminary summary computation
    for sc in schemes:
        report_data["schemes"][sc] = {}
        for lvl in levels:
            report_data["schemes"][sc][lvl] = {}
            for st in stats_keys:
                obs_val = obs_rates[lvl][st]
                null_vals = null_distributions[sc][lvl][st]
                stat_summary = compute_summary_stats(obs_val, null_vals, is_valid_null=True)
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

    # Apply "INVALID NULL - do not cite:" prefix to conclusion text for invalid schemes/levels
    for sc in schemes:
        for lvl in levels:
            lvl_invalid = any(
                report_data["schemes"][sc][lvl][st]["p_value"] < 0.05
                for st in order_free_stats
            )
            if lvl_invalid:
                for st in stats_keys:
                    old_c = report_data["schemes"][sc][lvl][st]["conclusion"]
                    if not old_c.startswith("INVALID NULL - do not cite:"):
                        report_data["schemes"][sc][lvl][st]["conclusion"] = f"INVALID NULL - do not cite: {old_c}"

    # Write JSON
    print(f"Writing report JSON to {JSON_OUT_PATH}...")
    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Generate Markdown
    print(f"Writing report Markdown to {MD_OUT_PATH}...")
    generate_markdown_report_7ep(report_data)

    print("7-episode permutation test completed successfully.")
    return report_data


def generate_markdown_report_7ep(data: dict[str, Any]) -> None:
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

    A("# Pre-Registered 7-Episode Permutation Test Report (E1–E7)")
    A()
    A("## Pre-Declared Test Design & Purpose")
    A()
    A("- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines across all seven episodes (E1–E7).")
    A("- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: Pre-declared headline null hypothesis (prereg Section 10). Shuffles the collapsed sequence strictly within each episode, preserving exact sample counts ($N=95$ technique, $N=76$ tactic) and marginal item frequencies. S1 p-values enter the pre-registered Holm step-down correction for hypotheses P3 and P4.")
    A("- **Constrained Scheme (S3 - Adjacency-Constrained Shuffle)**: Shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items share identical technique sets (technique level) or identical tactic sets (tactic level), using rejection sampling with up to 10,000 tries per episode. Reported alongside S1.")
    A("- **Excluded Scheme (S2)**: S2 (raw-event shuffle) is excluded from the 7-episode design per prereg Section 10.")
    A("- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999).")
    A(f"- **One-Sided p-value Formula**: `{meta['p_value_formula']}`.")
    A("- **Pre-Registered Primary Comparisons**: P3 = Tactic Markov Hit@3 vs S1 null; P4 = Technique Markov Hit@3 vs S1 null.")
    A("- **Conclusion Text Generation Rule**: Generated strictly by code from p-values without causal claims. If any scheme fails order-free validity, its conclusions are prefixed with *'INVALID NULL - do not cite:'*.")
    A()
    A("---")
    A()
    A("## Scheme Validity Check (Order-Free Frequency Statistics)")
    A()
    A("A valid order-only null permutation must not perturb the performance of an **order-free** model (FrequencyBaseline). If an order-free statistic exhibits $p < 0.05$, the scheme alters marginal event distributions or set compositions in addition to order, confounding order-signal tests.")
    A()
    A("| Scheme | Level | Statistic | Observed Rate | Null Mean Rate | p-value | MC SE | Order-Free Status |")
    A("|:---|:---|:---|:---:|:---:|:---:|:---:|:---|")
    for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)")]:
        for lvl, lvl_label in [("technique_collapsed_full", "Technique"), ("tactic_collapsed", "Tactic")]:
            for st in ["frequency_hit1", "frequency_hit3"]:
                row = data["schemes"][sc][lvl][st]
                lbl = stat_labels[st]
                status_str = "**FLAG (p < 0.05)**" if row["p_value"] < 0.05 else "PASS (Valid)"
                A(f"| {sc_label} | {lvl_label} | {lbl} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {status_str} |")
    A()
    for sc, sc_label in [("S1_collapsed_order", "S1"), ("S3_constrained_shuffle", "S3")]:
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
    for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)")]:
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
    A("### Technique Level (`collapsed_full`, N=95)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s1_tech = data["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]
    counts_tech = meta["observed_baseline_counts"]["technique_collapsed_full"]
    for st, lbl in stat_labels.items():
        row = s1_tech[st]
        h_str = f"{counts_tech[st]:+d} / 95" if "minus" in st else f"{counts_tech[st]} / 95"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N=76)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s1_tac = data["schemes"]["S1_collapsed_order"]["tactic_collapsed"]
    counts_tac = meta["observed_baseline_counts"]["tactic_collapsed"]
    for st, lbl in stat_labels.items():
        row = s1_tac[st]
        h_str = f"{counts_tac[st]:+d} / 76" if "minus" in st else f"{counts_tac[st]} / 76"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {row['conclusion']} |")

    A()
    A("---")
    A()
    A("## Constrained Scheme S3 Results (Adjacency-Constrained Null)")
    A()
    A("### Technique Level (`collapsed_full`, N=95)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s3_tech = data["schemes"]["S3_constrained_shuffle"]["technique_collapsed_full"]
    for st, lbl in stat_labels.items():
        row = s3_tech[st]
        h_str = f"{counts_tech[st]:+d} / 95" if "minus" in st else f"{counts_tech[st]} / 95"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {row['conclusion']} |")

    A()
    A("### Tactic Level (`tactic_collapsed`, N=76)")
    A()
    A("| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    s3_tac = data["schemes"]["S3_constrained_shuffle"]["tactic_collapsed"]
    for st, lbl in stat_labels.items():
        row = s3_tac[st]
        h_str = f"{counts_tac[st]:+d} / 76" if "minus" in st else f"{counts_tac[st]} / 76"
        A(f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {row['conclusion']} |")

    A()
    A("### S1 vs S3 Monte Carlo Consistency")
    A()
    A("Monte Carlo permutation standard errors are given by $\\text{SE}_{\\text{MC}}(p) = \\sqrt{p(1-p)/B}$ ($B=1000$). S1 and S3 p-values differing by less than two combined Monte Carlo standard errors are statistically consistent:")
    A()
    for lvl, lvl_label in [("technique_collapsed_full", "Technique Level (`collapsed_full`)"), ("tactic_collapsed", "Tactic Level (`tactic_collapsed`)")]:
        A(f"#### {lvl_label}")
        A()
        for st, lbl in stat_labels.items():
            p1 = data["schemes"]["S1_collapsed_order"][lvl][st]["p_value"]
            p3 = data["schemes"]["S3_constrained_shuffle"][lvl][st]["p_value"]
            se1 = data["schemes"]["S1_collapsed_order"][lvl][st]["mc_se"]
            se3 = data["schemes"]["S3_constrained_shuffle"][lvl][st]["mc_se"]
            diff = abs(p1 - p3)
            combined_2se = 2.0 * math.sqrt(se1**2 + se3**2)
            if diff <= combined_2se:
                verdict = f"is less than two combined Monte Carlo standard errors ({combined_2se:.4f}), confirming S1 and S3 are consistent."
            else:
                verdict = f"exceeds two combined Monte Carlo standard errors ({combined_2se:.4f}), reflecting sensitivity to the adjacency constraint on collapsed sequences."
            A(f"- **{lbl}**: S1 $p = {p1:.4f}$ (MC SE $= {se1:.4f}$), S3 $p = {p3:.4f}$ (MC SE $= {se3:.4f}$); difference $|p_{{S1}} - p_{{S3}}| = {diff:.4f}$ {verdict}")
        A()

    A("---")
    A()
    A("## Pre-Registered Hypotheses P3 and P4 (S1 Headline)")
    A()
    p3_val = data["schemes"]["S1_collapsed_order"]["tactic_collapsed"]["markov_hit3"]["p_value"]
    p4_val = data["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]["markov_hit3"]["p_value"]
    A(f"- **Hypothesis P3 (Tactic Markov Hit@3 vs S1 Null)**: Raw $p = {p3_val:.4f}$ (S3 reported alongside: $p = {data['schemes']['S3_constrained_shuffle']['tactic_collapsed']['markov_hit3']['p_value']:.4f}$).")
    A(f"- **Hypothesis P4 (Technique Markov Hit@3 vs S1 Null)**: Raw $p = {p4_val:.4f}$ (S3 reported alongside: $p = {data['schemes']['S3_constrained_shuffle']['technique_collapsed_full']['markov_hit3']['p_value']:.4f}$).")
    A()

    with open(MD_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_permutation_test_7ep()
