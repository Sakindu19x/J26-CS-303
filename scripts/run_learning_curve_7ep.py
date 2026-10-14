"""Pre-registered Learning Curve Analysis across 7 Episodes (E1-E7).

Evaluates models as a function of training scenario count k (1..6).
Per reports/prereg_7episode_design.md Section 7:
- Held-out episodes: E1..E7.
- For each held-out episode e, and each k in 1..6:
  - All C(6, k) combinations of the remaining 6 episodes are evaluated as training set.
  - Slices: technique collapsed_full (Primary) and tactic tactic_collapsed (Secondary).
  - Models: MarkovModel, FrequencyBaseline, markov_fallback.
- Outputs:
  - data/processed_7ep/learning_curve_7ep.csv
  - reports/7ep/learning_curve_7ep_results.json
  - reports/7ep/learning_curve_7ep_report.md
  - reports/7ep/learning_curve_7ep.png
  - reports/7ep/learning_curve_7ep_plot_data.json
"""
from __future__ import annotations

import csv
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

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
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"

CSV_OUT = DATA_7EP / "learning_curve_7ep.csv"
JSON_OUT = REPORTS_7EP / "learning_curve_7ep_results.json"
MD_OUT = REPORTS_7EP / "learning_curve_7ep_report.md"
PNG_OUT = REPORTS_7EP / "learning_curve_7ep.png"
PLOT_DATA_OUT = REPORTS_7EP / "learning_curve_7ep_plot_data.json"
EVAL_RESULTS_PATH = REPORTS_7EP / "evaluation_7ep_results.json"

EPISODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
MODELS = ["markov", "frequency", "markov_fallback"]


def run_learning_curve_7ep() -> dict[str, Any]:
    print("================================================================================")
    print("RUNNING 7-EPISODE LEARNING CURVE EVALUATION (E1-E7)")
    print("================================================================================")

    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_data = json.load(f)

    ep_seqs = seqs_data["episodes"]
    cf_samples = [s for s in samples_data if s["variant"] == "collapsed" and s["granularity"] == "full"]

    # Build tactic sequences and samples
    t_seqs = build_tactic_sequences(seqs_data)
    if "episodes" in t_seqs:
        t_seqs = t_seqs["episodes"]
    ep_t_seqs = {ep_id: t_seqs[ep_id]["tactic_collapsed"] for ep_id in t_seqs}

    tac_samples_by_ep: dict[str, list[dict[str, Any]]] = {}
    for ep_id in EPISODES:
        items = ep_t_seqs[ep_id]
        tac_samples_by_ep[ep_id] = []
        for idx in range(len(items) - 1):
            cur = items[idx]["tactics"]
            tgt = items[idx + 1]["tactics"]
            tac_samples_by_ep[ep_id].append({"current": cur, "target": tgt})

    csv_rows: list[dict[str, Any]] = []

    # Structure to hold evaluations: slice -> k -> held_out_ep -> list of subset eval dicts
    eval_tree: dict[str, dict[int, dict[str, list[dict[str, Any]]]]] = {
        "technique_collapsed_full": {k: {ep: [] for ep in EPISODES} for k in range(1, 7)},
        "tactic_collapsed": {k: {ep: [] for ep in EPISODES} for k in range(1, 7)},
    }

    # 1. Technique Evaluation
    print("\n[1/2] Evaluating Technique (collapsed_full) across 441 subsets...")
    for ep in EPISODES:
        others = [x for x in EPISODES if x != ep]
        fold_samples = [s for s in cf_samples if s["episode_id"] == ep]
        n_samples = len(fold_samples)

        for k in range(1, 7):
            combos = list(itertools.combinations(others, k))
            for sub in combos:
                train_eps = list(sub)
                sub_id = f"{ep}_k{k}_" + "-".join(train_eps)

                m_tech = MarkovModel(variant="collapsed", granularity="full").fit(ep_seqs, training_episodes=train_eps)
                f_tech = FrequencyBaseline(variant="collapsed", granularity="full").fit(ep_seqs, training_episodes=train_eps)

                train_pool: set[str] = set()
                for tr in train_eps:
                    items = ep_seqs[tr]["collapsed"]
                    for i in range(len(items) - 1):
                        train_pool.update(m_tech._extract_tech_set(items[i + 1]))

                f_res = f_tech.predict(k=3)
                f_cands = [c[0] for c in f_res["candidates"]]

                m1, m3, f1, f3, fb1, fb3, cov, ceil = 0, 0, 0, 0, 0, 0, 0, 0
                for s in fold_samples:
                    cur = s["current_technique_set"]
                    tgt = set(s["target_technique_set"])
                    if tgt & train_pool:
                        ceil += 1
                    m_res = m_tech.predict(cur, k=3)
                    st = m_res["status"]
                    if st == "ok":
                        cov += 1
                        mc = [c[0] for c in m_res["candidates"]]
                        h1, h3 = _hit_flags(mc, tgt)
                        fb_h1, fb_h3 = h1, h3
                    else:
                        h1, h3 = 0, 0
                        fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                    fh1, fh3 = _hit_flags(f_cands, tgt)

                    m1 += h1
                    m3 += h3
                    f1 += fh1
                    f3 += fh3
                    fb1 += fb_h1
                    fb3 += fb_h3

                res_entry = {
                    "held_out_episode": ep,
                    "k": k,
                    "subset_id": sub_id,
                    "training_episodes": train_eps,
                    "n_samples": n_samples,
                    "markov": {"hit1": m1, "hit3": m3, "hit1_rate": m1 / n_samples, "hit3_rate": m3 / n_samples},
                    "frequency": {"hit1": f1, "hit3": f3, "hit1_rate": f1 / n_samples, "hit3_rate": f3 / n_samples},
                    "markov_fallback": {"hit1": fb1, "hit3": fb3, "hit1_rate": fb1 / n_samples, "hit3_rate": fb3 / n_samples},
                    "coverage": {"covered_samples": cov, "coverage_rate": cov / n_samples},
                    "ceiling": {"ceiling_samples": ceil, "ceiling_rate": ceil / n_samples},
                }
                eval_tree["technique_collapsed_full"][k][ep].append(res_entry)

                for model_name in MODELS:
                    m_hits = res_entry[model_name]
                    csv_rows.append({
                        "held_out_episode": ep,
                        "k": k,
                        "subset_id": sub_id,
                        "training_episodes": "-".join(train_eps),
                        "slice": "technique_collapsed_full",
                        "model": model_name,
                        "n_samples": n_samples,
                        "hit1": m_hits["hit1"],
                        "hit3": m_hits["hit3"],
                        "hit1_rate": f"{m_hits['hit1_rate']:.6f}",
                        "hit3_rate": f"{m_hits['hit3_rate']:.6f}",
                        "covered_samples": cov,
                        "coverage_rate": f"{cov / n_samples:.6f}",
                        "ceiling_samples": ceil,
                        "ceiling_rate": f"{ceil / n_samples:.6f}",
                    })

    # 2. Tactic Evaluation
    print("\n[2/2] Evaluating Tactic (tactic_collapsed) across 441 subsets...")
    for ep in EPISODES:
        others = [x for x in EPISODES if x != ep]
        fold_samples = tac_samples_by_ep[ep]
        n_samples = len(fold_samples)

        for k in range(1, 7):
            combos = list(itertools.combinations(others, k))
            for sub in combos:
                train_eps = list(sub)
                sub_id = f"{ep}_k{k}_" + "-".join(train_eps)

                m_tac = TacticMarkovModel().fit(ep_t_seqs, train_eps)
                f_tac = TacticFrequencyBaseline().fit(ep_t_seqs, train_eps)

                train_pool = set()
                for tr in train_eps:
                    items = ep_t_seqs[tr]
                    for i in range(len(items) - 1):
                        train_pool.update(items[i + 1]["tactics"])

                f_res = f_tac.predict(k=3)
                f_cands = [c[0] for c in f_res["candidates"]]

                m1, m3, f1, f3, fb1, fb3, cov, ceil = 0, 0, 0, 0, 0, 0, 0, 0
                for s in fold_samples:
                    cur = s["current"]
                    tgt = set(s["target"])
                    if tgt & train_pool:
                        ceil += 1
                    m_res = m_tac.predict(cur, k=3)
                    st = m_res["status"]
                    if st == "ok":
                        cov += 1
                        mc = [c[0] for c in m_res["candidates"]]
                        h1, h3 = _hit_flags(mc, tgt)
                        fb_h1, fb_h3 = h1, h3
                    else:
                        h1, h3 = 0, 0
                        fb_h1, fb_h3 = _hit_flags(f_cands, tgt)
                    fh1, fh3 = _hit_flags(f_cands, tgt)

                    m1 += h1
                    m3 += h3
                    f1 += fh1
                    f3 += fh3
                    fb1 += fb_h1
                    fb3 += fb_h3

                res_entry = {
                    "held_out_episode": ep,
                    "k": k,
                    "subset_id": sub_id,
                    "training_episodes": train_eps,
                    "n_samples": n_samples,
                    "markov": {"hit1": m1, "hit3": m3, "hit1_rate": m1 / n_samples, "hit3_rate": m3 / n_samples},
                    "frequency": {"hit1": f1, "hit3": f3, "hit1_rate": f1 / n_samples, "hit3_rate": f3 / n_samples},
                    "markov_fallback": {"hit1": fb1, "hit3": fb3, "hit1_rate": fb1 / n_samples, "hit3_rate": fb3 / n_samples},
                    "coverage": {"covered_samples": cov, "coverage_rate": cov / n_samples},
                    "ceiling": {"ceiling_samples": ceil, "ceiling_rate": ceil / n_samples},
                }
                eval_tree["tactic_collapsed"][k][ep].append(res_entry)

                for model_name in MODELS:
                    m_hits = res_entry[model_name]
                    csv_rows.append({
                        "held_out_episode": ep,
                        "k": k,
                        "subset_id": sub_id,
                        "training_episodes": "-".join(train_eps),
                        "slice": "tactic_collapsed",
                        "model": model_name,
                        "n_samples": n_samples,
                        "hit1": m_hits["hit1"],
                        "hit3": m_hits["hit3"],
                        "hit1_rate": f"{m_hits['hit1_rate']:.6f}",
                        "hit3_rate": f"{m_hits['hit3_rate']:.6f}",
                        "covered_samples": cov,
                        "coverage_rate": f"{cov / n_samples:.6f}",
                        "ceiling_samples": ceil,
                        "ceiling_rate": f"{ceil / n_samples:.6f}",
                    })

    # Write CSV (only if not already byte-identical, or rewrite identically)
    print(f"\nWriting learning curve CSV ({len(csv_rows)} rows) to {CSV_OUT}...")
    fieldnames = [
        "held_out_episode", "k", "subset_id", "training_episodes", "slice",
        "model", "n_samples", "hit1", "hit3", "hit1_rate", "hit3_rate",
        "covered_samples", "coverage_rate", "ceiling_samples", "ceiling_rate",
    ]
    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    # 3. Compute Aggregations
    # Per prereg section 7:
    # "Compute metric averages across subsets for each held-out episode, then average over all 7 held-out episodes."
    aggregated_results: dict[str, Any] = {
        "metadata": {
            "eval_name": "7-Episode Learning Curve Evaluation (E1-E7)",
            "slices_evaluated": ["technique_collapsed_full", "tactic_collapsed"],
            "models_evaluated": MODELS,
            "episodes": EPISODES,
            "k_values": list(range(1, 7)),
            "subsets_per_k": {k: math.comb(6, k) for k in range(1, 7)},
            "total_subsets_per_ep": 63,
            "total_evaluations_per_slice": 441,
        },
        "learning_curve": {},
    }

    plot_data: dict[str, Any] = {
        "k_values": list(range(1, 7)),
        "slices": {},
    }

    for sl in ["technique_collapsed_full", "tactic_collapsed"]:
        aggregated_results["learning_curve"][sl] = {}
        plot_data["slices"][sl] = {
            "k": list(range(1, 7)),
            "episode_mean": {
                "markov_hit3": [],
                "frequency_hit3": [],
                "fallback_hit3": [],
                "ceiling": [],
                "coverage": [],
            },
            "sample_weighted": {
                "markov_hit3": [],
                "frequency_hit3": [],
                "fallback_hit3": [],
                "ceiling": [],
                "coverage": [],
            },
            # Primary series mapped to top-level for convenience
            "markov_hit3": [],
            "frequency_hit3": [],
            "fallback_hit3": [],
            "ceiling": [],
            "coverage": [],
        }

        for k in range(1, 7):
            n_subsets = math.comb(6, k)
            per_ep_metrics: dict[str, Any] = {}

            # Metrics accumulators across all 7 episodes
            ep_means = {
                "markov_hit1": [], "markov_hit3": [],
                "freq_hit1": [], "freq_hit3": [],
                "fb_hit1": [], "fb_hit3": [],
                "coverage": [], "ceiling": [],
            }
            # Also sample-weighted totals
            weighted_totals = {
                "total_eval_samples": 0,
                "markov_hit1": 0.0, "markov_hit3": 0.0,
                "freq_hit1": 0.0, "freq_hit3": 0.0,
                "fb_hit1": 0.0, "fb_hit3": 0.0,
                "covered_samples": 0.0, "ceiling_samples": 0.0,
            }

            for ep in EPISODES:
                subs = eval_tree[sl][k][ep]
                assert len(subs) == n_subsets

                mean_m1 = sum(s["markov"]["hit1_rate"] for s in subs) / n_subsets
                mean_m3 = sum(s["markov"]["hit3_rate"] for s in subs) / n_subsets
                mean_f1 = sum(s["frequency"]["hit1_rate"] for s in subs) / n_subsets
                mean_f3 = sum(s["frequency"]["hit3_rate"] for s in subs) / n_subsets
                mean_fb1 = sum(s["markov_fallback"]["hit1_rate"] for s in subs) / n_subsets
                mean_fb3 = sum(s["markov_fallback"]["hit3_rate"] for s in subs) / n_subsets
                mean_cov = sum(s["coverage"]["coverage_rate"] for s in subs) / n_subsets
                mean_ceil = sum(s["ceiling"]["ceiling_rate"] for s in subs) / n_subsets

                ep_n = subs[0]["n_samples"]
                per_ep_metrics[ep] = {
                    "n_samples": ep_n,
                    "markov": {"hit1_rate": mean_m1, "hit3_rate": mean_m3},
                    "frequency": {"hit1_rate": mean_f1, "hit3_rate": mean_f3},
                    "markov_fallback": {"hit1_rate": mean_fb1, "hit3_rate": mean_fb3},
                    "coverage_rate": mean_cov,
                    "ceiling_rate": mean_ceil,
                }

                ep_means["markov_hit1"].append(mean_m1)
                ep_means["markov_hit3"].append(mean_m3)
                ep_means["freq_hit1"].append(mean_f1)
                ep_means["freq_hit3"].append(mean_f3)
                ep_means["fb_hit1"].append(mean_fb1)
                ep_means["fb_hit3"].append(mean_fb3)
                ep_means["coverage"].append(mean_cov)
                ep_means["ceiling"].append(mean_ceil)

                # Sample weighted
                weighted_totals["total_eval_samples"] += ep_n
                weighted_totals["markov_hit1"] += mean_m1 * ep_n
                weighted_totals["markov_hit3"] += mean_m3 * ep_n
                weighted_totals["freq_hit1"] += mean_f1 * ep_n
                weighted_totals["freq_hit3"] += mean_f3 * ep_n
                weighted_totals["fb_hit1"] += mean_fb1 * ep_n
                weighted_totals["fb_hit3"] += mean_fb3 * ep_n
                weighted_totals["covered_samples"] += mean_cov * ep_n
                weighted_totals["ceiling_samples"] += mean_ceil * ep_n

            tot_n = weighted_totals["total_eval_samples"]

            # Compute E5-excluded aggregation
            no_e5_eps = [ep for ep in EPISODES if ep != "E5"]
            tot_n_no_e5 = sum(per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps)
            e5_excluded_summary = {
                "unweighted_episode_mean": {
                    "markov_hit1": sum(per_ep_metrics[ep]["markov"]["hit1_rate"] for ep in no_e5_eps) / 6.0,
                    "markov_hit3": sum(per_ep_metrics[ep]["markov"]["hit3_rate"] for ep in no_e5_eps) / 6.0,
                    "frequency_hit1": sum(per_ep_metrics[ep]["frequency"]["hit1_rate"] for ep in no_e5_eps) / 6.0,
                    "frequency_hit3": sum(per_ep_metrics[ep]["frequency"]["hit3_rate"] for ep in no_e5_eps) / 6.0,
                    "markov_fallback_hit1": sum(per_ep_metrics[ep]["markov_fallback"]["hit1_rate"] for ep in no_e5_eps) / 6.0,
                    "markov_fallback_hit3": sum(per_ep_metrics[ep]["markov_fallback"]["hit3_rate"] for ep in no_e5_eps) / 6.0,
                    "coverage": sum(per_ep_metrics[ep]["coverage_rate"] for ep in no_e5_eps) / 6.0,
                    "ceiling": sum(per_ep_metrics[ep]["ceiling_rate"] for ep in no_e5_eps) / 6.0,
                },
                "pooled_sample_weighted": {
                    "total_samples": tot_n_no_e5,
                    "markov_hit1": sum(per_ep_metrics[ep]["markov"]["hit1_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "markov_hit3": sum(per_ep_metrics[ep]["markov"]["hit3_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "frequency_hit1": sum(per_ep_metrics[ep]["frequency"]["hit1_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "frequency_hit3": sum(per_ep_metrics[ep]["frequency"]["hit3_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "markov_fallback_hit1": sum(per_ep_metrics[ep]["markov_fallback"]["hit1_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "markov_fallback_hit3": sum(per_ep_metrics[ep]["markov_fallback"]["hit3_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "coverage": sum(per_ep_metrics[ep]["coverage_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                    "ceiling": sum(per_ep_metrics[ep]["ceiling_rate"] * per_ep_metrics[ep]["n_samples"] for ep in no_e5_eps) / tot_n_no_e5,
                },
            }

            k_summary = {
                "k": k,
                "n_subsets_per_episode": n_subsets,
                "per_episode_means": per_ep_metrics,
                "unweighted_episode_mean": {
                    "markov_hit1": sum(ep_means["markov_hit1"]) / 7.0,
                    "markov_hit3": sum(ep_means["markov_hit3"]) / 7.0,
                    "frequency_hit1": sum(ep_means["freq_hit1"]) / 7.0,
                    "frequency_hit3": sum(ep_means["freq_hit3"]) / 7.0,
                    "markov_fallback_hit1": sum(ep_means["fb_hit1"]) / 7.0,
                    "markov_fallback_hit3": sum(ep_means["fb_hit3"]) / 7.0,
                    "coverage": sum(ep_means["coverage"]) / 7.0,
                    "ceiling": sum(ep_means["ceiling"]) / 7.0,
                },
                "pooled_sample_weighted": {
                    "total_samples": tot_n,
                    "markov_hit1": weighted_totals["markov_hit1"] / tot_n,
                    "markov_hit3": weighted_totals["markov_hit3"] / tot_n,
                    "frequency_hit1": weighted_totals["freq_hit1"] / tot_n,
                    "frequency_hit3": weighted_totals["freq_hit3"] / tot_n,
                    "markov_fallback_hit1": weighted_totals["fb_hit1"] / tot_n,
                    "markov_fallback_hit3": weighted_totals["fb_hit3"] / tot_n,
                    "coverage": weighted_totals["covered_samples"] / tot_n,
                    "ceiling": weighted_totals["ceiling_samples"] / tot_n,
                },
                "e5_excluded": e5_excluded_summary,
            }
            aggregated_results["learning_curve"][sl][f"k_{k}"] = k_summary

            # Plot data tracking
            unw = k_summary["unweighted_episode_mean"]
            pw = k_summary["pooled_sample_weighted"]

            plot_data["slices"][sl]["episode_mean"]["markov_hit3"].append(unw["markov_hit3"])
            plot_data["slices"][sl]["episode_mean"]["frequency_hit3"].append(unw["frequency_hit3"])
            plot_data["slices"][sl]["episode_mean"]["fallback_hit3"].append(unw["markov_fallback_hit3"])
            plot_data["slices"][sl]["episode_mean"]["ceiling"].append(unw["ceiling"])
            plot_data["slices"][sl]["episode_mean"]["coverage"].append(unw["coverage"])

            plot_data["slices"][sl]["sample_weighted"]["markov_hit3"].append(pw["markov_hit3"])
            plot_data["slices"][sl]["sample_weighted"]["frequency_hit3"].append(pw["frequency_hit3"])
            plot_data["slices"][sl]["sample_weighted"]["fallback_hit3"].append(pw["markov_fallback_hit3"])
            plot_data["slices"][sl]["sample_weighted"]["ceiling"].append(pw["ceiling"])
            plot_data["slices"][sl]["sample_weighted"]["coverage"].append(pw["coverage"])

            # Map primary (episode-mean) to top-level
            plot_data["slices"][sl]["markov_hit3"].append(unw["markov_hit3"])
            plot_data["slices"][sl]["frequency_hit3"].append(unw["frequency_hit3"])
            plot_data["slices"][sl]["fallback_hit3"].append(unw["markov_fallback_hit3"])
            plot_data["slices"][sl]["ceiling"].append(unw["ceiling"])
            plot_data["slices"][sl]["coverage"].append(unw["coverage"])

    # Code assertions at k=6 against evaluation_7ep_results.json
    print("\nAsserting k=6 aggregations against evaluation_7ep_results.json fold-mean and pooled values...")
    if EVAL_RESULTS_PATH.is_file():
        with open(EVAL_RESULTS_PATH, "r", encoding="utf-8") as f:
            ev_json = json.load(f)

        # Technique assertions
        lc_t6_unw = aggregated_results["learning_curve"]["technique_collapsed_full"]["k_6"]["unweighted_episode_mean"]
        lc_t6_w = aggregated_results["learning_curve"]["technique_collapsed_full"]["k_6"]["pooled_sample_weighted"]
        ev_t_head = ev_json["primary_slice_technique_collapsed_full"]["headline"]

        assert math.isclose(lc_t6_unw["markov_hit1"], ev_t_head["markov"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_unw["markov_hit3"], ev_t_head["markov"]["fold_mean_top3"], abs_tol=1e-6)
        assert math.isclose(lc_t6_unw["frequency_hit1"], ev_t_head["frequency"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_unw["frequency_hit3"], ev_t_head["frequency"]["fold_mean_top3"], abs_tol=1e-6)
        assert math.isclose(lc_t6_unw["markov_fallback_hit1"], ev_t_head["fallback"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_unw["markov_fallback_hit3"], ev_t_head["fallback"]["fold_mean_top3"], abs_tol=1e-6)

        assert math.isclose(lc_t6_w["markov_hit1"], ev_t_head["markov"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["markov_hit3"], ev_t_head["markov"]["top3"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["frequency_hit1"], ev_t_head["frequency"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["frequency_hit3"], ev_t_head["frequency"]["top3"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["markov_fallback_hit1"], ev_t_head["fallback"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["markov_fallback_hit3"], ev_t_head["fallback"]["top3"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["coverage"], ev_t_head["coverage"]["coverage_rate"], abs_tol=1e-6)
        assert math.isclose(lc_t6_w["ceiling"], ev_t_head["ceiling"]["ceiling_rate"], abs_tol=1e-6)

        # Tactic assertions
        lc_tac6_unw = aggregated_results["learning_curve"]["tactic_collapsed"]["k_6"]["unweighted_episode_mean"]
        lc_tac6_w = aggregated_results["learning_curve"]["tactic_collapsed"]["k_6"]["pooled_sample_weighted"]
        ev_tac_head = ev_json["secondary_slice_tactic_collapsed"]["headline"]

        assert math.isclose(lc_tac6_unw["markov_hit1"], ev_tac_head["markov"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_unw["markov_hit3"], ev_tac_head["markov"]["fold_mean_top3"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_unw["frequency_hit1"], ev_tac_head["frequency"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_unw["frequency_hit3"], ev_tac_head["frequency"]["fold_mean_top3"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_unw["markov_fallback_hit1"], ev_tac_head["markov_fallback"]["fold_mean_top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_unw["markov_fallback_hit3"], ev_tac_head["markov_fallback"]["fold_mean_top3"], abs_tol=1e-6)

        assert math.isclose(lc_tac6_w["markov_hit1"], ev_tac_head["markov"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_w["markov_hit3"], ev_tac_head["markov"]["top3"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_w["frequency_hit1"], ev_tac_head["frequency"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_w["frequency_hit3"], ev_tac_head["frequency"]["top3"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_w["markov_fallback_hit1"], ev_tac_head["markov_fallback"]["top1"], abs_tol=1e-6)
        assert math.isclose(lc_tac6_w["markov_fallback_hit3"], ev_tac_head["markov_fallback"]["top3"], abs_tol=1e-6)
        print("  All k=6 aggregations exactly MATCH evaluation_7ep_results.json fold-mean and pooled values [PASS]")

    # Write Results JSON
    print(f"\nWriting learning curve results JSON to {JSON_OUT}...")
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(aggregated_results, f, indent=2)

    # Write Sidecar Plot Data JSON
    print(f"Writing plot data JSON to {PLOT_DATA_OUT}...")
    with open(PLOT_DATA_OUT, "w", encoding="utf-8") as f:
        json.dump(plot_data, f, indent=2)

    # Generate Plot (Primary solid, Secondary dashed)
    print(f"Generating learning curve figure at {PNG_OUT}...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5), sharey=False)

    ks = list(range(1, 7))

    # Panel 1: Technique
    ax1 = axes[0]
    p_tech = plot_data["slices"]["technique_collapsed_full"]
    # Primary (Solid lines with markers)
    ax1.plot(ks, p_tech["episode_mean"]["ceiling"], "k-o", label="Ceiling (Episode-Mean)")
    ax1.plot(ks, p_tech["episode_mean"]["coverage"], "c-v", label="Coverage (Episode-Mean)")
    ax1.plot(ks, p_tech["episode_mean"]["frequency_hit3"], "s-", color="#d95f02", label="Frequency Hit@3 (Episode-Mean)")
    ax1.plot(ks, p_tech["episode_mean"]["fallback_hit3"], "^-", color="#7570b3", label="Fallback Hit@3 (Episode-Mean)")
    ax1.plot(ks, p_tech["episode_mean"]["markov_hit3"], "o-", color="#1b9e77", label="Markov Hit@3 (Episode-Mean)")
    # Secondary (Dashed lines without markers)
    ax1.plot(ks, p_tech["sample_weighted"]["ceiling"], "k--", alpha=0.7, label="Ceiling (Pooled)")
    ax1.plot(ks, p_tech["sample_weighted"]["coverage"], "c--", alpha=0.7, label="Coverage (Pooled)")
    ax1.plot(ks, p_tech["sample_weighted"]["frequency_hit3"], "--", color="#d95f02", alpha=0.7, label="Frequency Hit@3 (Pooled)")
    ax1.plot(ks, p_tech["sample_weighted"]["fallback_hit3"], "--", color="#7570b3", alpha=0.7, label="Fallback Hit@3 (Pooled)")
    ax1.plot(ks, p_tech["sample_weighted"]["markov_hit3"], "--", color="#1b9e77", alpha=0.7, label="Markov Hit@3 (Pooled)")

    ax1.set_title("Technique Level (collapsed_full, N=95)")
    ax1.set_xlabel("Number of Training Episodes (k)")
    ax1.set_ylabel("Rate")
    ax1.set_xticks(ks)
    ax1.set_ylim(-0.02, 0.75)
    ax1.grid(True, linestyle=":", alpha=0.6)
    ax1.legend(loc="upper left", fontsize=8)

    # Panel 2: Tactic
    ax2 = axes[1]
    p_tac = plot_data["slices"]["tactic_collapsed"]
    # Primary (Solid lines with markers)
    ax2.plot(ks, p_tac["episode_mean"]["ceiling"], "k-o", label="Ceiling (Episode-Mean)")
    ax2.plot(ks, p_tac["episode_mean"]["coverage"], "c-v", label="Coverage (Episode-Mean)")
    ax2.plot(ks, p_tac["episode_mean"]["frequency_hit3"], "s-", color="#d95f02", label="Frequency Hit@3 (Episode-Mean)")
    ax2.plot(ks, p_tac["episode_mean"]["fallback_hit3"], "^-", color="#7570b3", label="Fallback Hit@3 (Episode-Mean)")
    ax2.plot(ks, p_tac["episode_mean"]["markov_hit3"], "o-", color="#1b9e77", label="Markov Hit@3 (Episode-Mean)")
    # Secondary (Dashed lines without markers)
    ax2.plot(ks, p_tac["sample_weighted"]["ceiling"], "k--", alpha=0.7, label="Ceiling (Pooled)")
    ax2.plot(ks, p_tac["sample_weighted"]["coverage"], "c--", alpha=0.7, label="Coverage (Pooled)")
    ax2.plot(ks, p_tac["sample_weighted"]["frequency_hit3"], "--", color="#d95f02", alpha=0.7, label="Frequency Hit@3 (Pooled)")
    ax2.plot(ks, p_tac["sample_weighted"]["fallback_hit3"], "--", color="#7570b3", alpha=0.7, label="Fallback Hit@3 (Pooled)")
    ax2.plot(ks, p_tac["sample_weighted"]["markov_hit3"], "--", color="#1b9e77", alpha=0.7, label="Markov Hit@3 (Pooled)")

    ax2.set_title("Tactic Level (tactic_collapsed, N=76)")
    ax2.set_xlabel("Number of Training Episodes (k)")
    ax2.set_ylabel("Rate")
    ax2.set_xticks(ks)
    ax2.set_ylim(0.0, 1.02)
    ax2.grid(True, linestyle=":", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=8)

    plt.suptitle("7-Episode Learning Curve: Model Performance vs Training Episode Count (k=1..6)\nSolid: Primary Pre-Registered Episode-Mean Aggregation; Dashed: Secondary Sample-Weighted Pooled Aggregation", fontsize=11)
    plt.tight_layout()
    fig.savefig(PNG_OUT, dpi=200)
    plt.close(fig)

    # Generate Markdown Report
    print(f"Generating learning curve Markdown report at {MD_OUT}...")
    generate_learning_curve_report_md(aggregated_results)

    print("Learning curve evaluation completed successfully.")
    return aggregated_results


def generate_learning_curve_report_md(data: dict[str, Any]) -> None:
    lines = []

    def A(line: str = ""):
        lines.append(line)

    A("# Pre-Registered 7-Episode Learning Curve Report")
    A()
    A("This report documents the combinatorial learning curve evaluation across all seven episodes (E1–E7) of the C4 dataset.")
    A("All procedures strictly adhere to `reports/prereg_7episode_design.md` Section 7 and Amendments 1–5.")
    A("No model tuning, parameter selection, or causal claims are made.")
    A()
    A("---")
    A()
    A("## 1. Experimental Protocol and Combinatorial Scope")
    A()
    A("- **Evaluated Slices**: Technique `collapsed_full` ($N=95$) and Tactic `tactic_collapsed` ($N=76$), as pre-registered in Section 7.")
    A("- **Evaluated Models**: `MarkovModel`, `FrequencyBaseline`, and `markov_fallback`.")
    A("- **Held-Out Test Episodes**: $e \\in \\{E1, E2, E3, E4, E5, E6, E7\\}$ ($7$ episodes).")
    A("- **Training Subset Sizes**: $k \\in \\{1, 2, 3, 4, 5, 6\\}$.")
    A("- **Combinatorial Enumeration**: For each held-out episode $e$, all $\\binom{6}{k}$ subsets of the remaining 6 episodes were evaluated:")
    A("  - $k=1$: $\\binom{6}{1} = 6$ subsets per episode ($42$ evaluations per slice)")
    A("  - $k=2$: $\\binom{6}{2} = 15$ subsets per episode ($105$ evaluations per slice)")
    A("  - $k=3$: $\\binom{6}{3} = 20$ subsets per episode ($140$ evaluations per slice)")
    A("  - $k=4$: $\\binom{6}{4} = 15$ subsets per episode ($105$ evaluations per slice)")
    A("  - $k=5$: $\\binom{6}{5} = 6$ subsets per episode ($42$ evaluations per slice)")
    A("  - $k=6$: $\\binom{6}{6} = 1$ subset per episode ($7$ evaluations per slice, corresponding to the standard full LOEO evaluation)")
    A("  - **Total Evaluations per Slice**: $63$ subsets per episode $\\times 7$ episodes $= 441$ training subset evaluations ($882$ across both slices).")
    A("- **Aggregation Methods**:")
    A("  - **Table 1 (Pre-Registered Primary)**: Episode-mean aggregation per Section 7 (\"Compute metric averages across subsets for each held-out episode, then average over all 7 held-out episodes\").")
    A("  - **Table 2 (Secondary)**: Sample-weighted pooled aggregation across all evaluated transitions ($N=95$ technique, $N=76$ tactic).")
    A("  - **Table 3 (Sensitivity, E5 Excluded)**: Aggregation with Episode E5 excluded (both 6-episode unweighted mean and sample-weighted over the remaining $N=93$ technique or $N=74$ tactic samples).")
    A()
    A("---")
    A()
    A("## 2. Technique Level: `collapsed_full` (N=95)")
    A()
    A("### Table 1: Pre-Registered Primary (Episode-Mean Aggregation across 7 Episodes)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    tech_k = data["learning_curve"]["technique_collapsed_full"]
    for k in range(1, 7):
        k_d = tech_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        unw = k_d["unweighted_episode_mean"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{unw['markov_hit1']:.4f} | {unw['markov_hit3']:.4f} | "
            f"{unw['frequency_hit1']:.4f} | {unw['frequency_hit3']:.4f} | "
            f"{unw['markov_fallback_hit1']:.4f} | {unw['markov_fallback_hit3']:.4f} | "
            f"{unw['coverage']:.4f} | {unw['ceiling']:.4f} |"
        )

    A()
    A("### Table 2: Secondary (Sample-Weighted Pooled Aggregation across 7 Episodes)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for k in range(1, 7):
        k_d = tech_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        pw = k_d["pooled_sample_weighted"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{pw['markov_hit1']:.4f} | {pw['markov_hit3']:.4f} | "
            f"{pw['frequency_hit1']:.4f} | {pw['frequency_hit3']:.4f} | "
            f"{pw['markov_fallback_hit1']:.4f} | {pw['markov_fallback_hit3']:.4f} | "
            f"{pw['coverage']:.4f} | {pw['ceiling']:.4f} |"
        )

    A()
    A("### Table 3: Sensitivity (E5 Excluded from Aggregation)")
    A()
    A("#### Table 3a: Episode-Mean Aggregation (6 Episodes, E5 Excluded)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tech_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        e5_unw = k_d["e5_excluded"]["unweighted_episode_mean"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{e5_unw['markov_hit1']:.4f} | {e5_unw['markov_hit3']:.4f} | "
            f"{e5_unw['frequency_hit1']:.4f} | {e5_unw['frequency_hit3']:.4f} | "
            f"{e5_unw['markov_fallback_hit1']:.4f} | {e5_unw['markov_fallback_hit3']:.4f} | "
            f"{e5_unw['coverage']:.4f} | {e5_unw['ceiling']:.4f} |"
        )

    A()
    A("#### Table 3b: Sample-Weighted Pooled Aggregation (6 Episodes, N=93, E5 Excluded)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tech_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        e5_w = k_d["e5_excluded"]["pooled_sample_weighted"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{e5_w['markov_hit1']:.4f} | {e5_w['markov_hit3']:.4f} | "
            f"{e5_w['frequency_hit1']:.4f} | {e5_w['frequency_hit3']:.4f} | "
            f"{e5_w['markov_fallback_hit1']:.4f} | {e5_w['markov_fallback_hit3']:.4f} | "
            f"{e5_w['coverage']:.4f} | {e5_w['ceiling']:.4f} |"
        )

    A()
    A("### Per-Episode Breakdown by Training Scenario Count (k)")
    A()
    A("| k | Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tech_k[f"k_{k}"]
        for ep in EPISODES:
            m = k_d["per_episode_means"][ep]
            A(
                f"| {k} | {ep} | {m['n_samples']} | "
                f"{m['markov']['hit1_rate']:.4f} | {m['markov']['hit3_rate']:.4f} | "
                f"{m['frequency']['hit1_rate']:.4f} | {m['frequency']['hit3_rate']:.4f} | "
                f"{m['markov_fallback']['hit1_rate']:.4f} | {m['markov_fallback']['hit3_rate']:.4f} | "
                f"{m['coverage_rate']:.4f} | {m['ceiling_rate']:.4f} |"
            )

    A()
    A("---")
    A()
    A("## 3. Tactic Level: `tactic_collapsed` (N=76)")
    A()
    A("### Table 1: Pre-Registered Primary (Episode-Mean Aggregation across 7 Episodes)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    tac_k = data["learning_curve"]["tactic_collapsed"]
    for k in range(1, 7):
        k_d = tac_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        unw = k_d["unweighted_episode_mean"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{unw['markov_hit1']:.4f} | {unw['markov_hit3']:.4f} | "
            f"{unw['frequency_hit1']:.4f} | {unw['frequency_hit3']:.4f} | "
            f"{unw['markov_fallback_hit1']:.4f} | {unw['markov_fallback_hit3']:.4f} | "
            f"{unw['coverage']:.4f} | {unw['ceiling']:.4f} |"
        )

    A()
    A("### Table 2: Secondary (Sample-Weighted Pooled Aggregation across 7 Episodes)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for k in range(1, 7):
        k_d = tac_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        pw = k_d["pooled_sample_weighted"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{pw['markov_hit1']:.4f} | {pw['markov_hit3']:.4f} | "
            f"{pw['frequency_hit1']:.4f} | {pw['frequency_hit3']:.4f} | "
            f"{pw['markov_fallback_hit1']:.4f} | {pw['markov_fallback_hit3']:.4f} | "
            f"{pw['coverage']:.4f} | {pw['ceiling']:.4f} |"
        )

    A()
    A("### Table 3: Sensitivity (E5 Excluded from Aggregation)")
    A()
    A("#### Table 3a: Episode-Mean Aggregation (6 Episodes, E5 Excluded)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tac_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        e5_unw = k_d["e5_excluded"]["unweighted_episode_mean"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{e5_unw['markov_hit1']:.4f} | {e5_unw['markov_hit3']:.4f} | "
            f"{e5_unw['frequency_hit1']:.4f} | {e5_unw['frequency_hit3']:.4f} | "
            f"{e5_unw['markov_fallback_hit1']:.4f} | {e5_unw['markov_fallback_hit3']:.4f} | "
            f"{e5_unw['coverage']:.4f} | {e5_unw['ceiling']:.4f} |"
        )

    A()
    A("#### Table 3b: Sample-Weighted Pooled Aggregation (6 Episodes, N=74, E5 Excluded)")
    A()
    A("| k | Subsets / Ep | Total Evals | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tac_k[f"k_{k}"]
        n_sub = k_d["n_subsets_per_episode"]
        tot_evals = n_sub * 7
        e5_w = k_d["e5_excluded"]["pooled_sample_weighted"]
        A(
            f"| {k} | {n_sub} | {tot_evals} | "
            f"{e5_w['markov_hit1']:.4f} | {e5_w['markov_hit3']:.4f} | "
            f"{e5_w['frequency_hit1']:.4f} | {e5_w['frequency_hit3']:.4f} | "
            f"{e5_w['markov_fallback_hit1']:.4f} | {e5_w['markov_fallback_hit3']:.4f} | "
            f"{e5_w['coverage']:.4f} | {e5_w['ceiling']:.4f} |"
        )

    A()
    A("### Per-Episode Breakdown by Training Scenario Count (k)")
    A()
    A("| k | Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Coverage | Ceiling |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in range(1, 7):
        k_d = tac_k[f"k_{k}"]
        for ep in EPISODES:
            m = k_d["per_episode_means"][ep]
            A(
                f"| {k} | {ep} | {m['n_samples']} | "
                f"{m['markov']['hit1_rate']:.4f} | {m['markov']['hit3_rate']:.4f} | "
                f"{m['frequency']['hit1_rate']:.4f} | {m['frequency']['hit3_rate']:.4f} | "
                f"{m['markov_fallback']['hit1_rate']:.4f} | {m['markov_fallback']['hit3_rate']:.4f} | "
                f"{m['coverage_rate']:.4f} | {m['ceiling_rate']:.4f} |"
            )

    A()
    A("---")
    A()
    A("## 4. Code-Generated Summary Observations")
    A()
    A("The following observational statements are generated strictly from the evaluation numbers without causal claims:")
    A()

    # Generate observations for Technique
    t1_unw = tech_k["k_1"]["unweighted_episode_mean"]
    t6_unw = tech_k["k_6"]["unweighted_episode_mean"]
    t1_pw = tech_k["k_1"]["pooled_sample_weighted"]
    t6_pw = tech_k["k_6"]["pooled_sample_weighted"]

    A(
        f"- **Technique Primary Episode-Mean Trajectories**: Under the pre-registered primary episode-mean aggregation across k=1..6, "
        f"technique Markov Hit@3 changes from {t1_unw['markov_hit3']:.4f} to {t6_unw['markov_hit3']:.4f}, "
        f"Frequency Hit@3 changes from {t1_unw['frequency_hit3']:.4f} to {t6_unw['frequency_hit3']:.4f}, "
        f"Markov coverage moves from {t1_unw['coverage']:.4f} to {t6_unw['coverage']:.4f} (+{t6_unw['coverage'] - t1_unw['coverage']:.4f}), "
        f"and target ceiling moves from {t1_unw['ceiling']:.4f} to {t6_unw['ceiling']:.4f} (+{t6_unw['ceiling'] - t1_unw['ceiling']:.4f})."
    )
    A(
        f"- **Technique Secondary Sample-Weighted Trajectories**: Under the secondary sample-weighted pooled aggregation across k=1..6, "
        f"technique Markov Hit@3 changes from {t1_pw['markov_hit3']:.4f} to {t6_pw['markov_hit3']:.4f}, "
        f"Frequency Hit@3 changes from {t1_pw['frequency_hit3']:.4f} to {t6_pw['frequency_hit3']:.4f}, "
        f"Markov coverage moves from {t1_pw['coverage']:.4f} to {t6_pw['coverage']:.4f} (+{t6_pw['coverage'] - t1_pw['coverage']:.4f}), "
        f"and target ceiling moves from {t1_pw['ceiling']:.4f} to {t6_pw['ceiling']:.4f} (+{t6_pw['ceiling'] - t1_pw['ceiling']:.4f})."
    )

    # Generate observations for Tactic
    tac1_unw = tac_k["k_1"]["unweighted_episode_mean"]
    tac6_unw = tac_k["k_6"]["unweighted_episode_mean"]
    tac1_pw = tac_k["k_1"]["pooled_sample_weighted"]
    tac6_pw = tac_k["k_6"]["pooled_sample_weighted"]

    A(
        f"- **Tactic Primary Episode-Mean Trajectories**: Under the pre-registered primary episode-mean aggregation across k=1..6, "
        f"tactic Markov Hit@3 moves from {tac1_unw['markov_hit3']:.4f} to {tac6_unw['markov_hit3']:.4f}, "
        f"Frequency Hit@3 moves from {tac1_unw['frequency_hit3']:.4f} to {tac6_unw['frequency_hit3']:.4f}, "
        f"tactic coverage moves from {tac1_unw['coverage']:.4f} to {tac6_unw['coverage']:.4f}, "
        f"and tactic ceiling moves from {tac1_unw['ceiling']:.4f} to {tac6_unw['ceiling']:.4f}."
    )
    A(
        f"- **Tactic Secondary Sample-Weighted Trajectories**: Under the secondary sample-weighted pooled aggregation across k=1..6, "
        f"tactic Markov Hit@3 moves from {tac1_pw['markov_hit3']:.4f} to {tac6_pw['markov_hit3']:.4f}, "
        f"Frequency Hit@3 moves from {tac1_pw['frequency_hit3']:.4f} to {tac6_pw['frequency_hit3']:.4f}, "
        f"tactic coverage moves from {tac1_pw['coverage']:.4f} to {tac6_pw['coverage']:.4f}, "
        f"and tactic ceiling moves from {tac1_pw['ceiling']:.4f} to {tac6_pw['ceiling']:.4f}."
    )
    A("- **Figure Reference**: Plotted learning curves are rendered in `reports/7ep/learning_curve_7ep.png` with sidecar values in `reports/7ep/learning_curve_7ep_plot_data.json` (solid curves: primary episode-mean aggregation; dashed curves: secondary sample-weighted pooled aggregation).")
    A()

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_learning_curve_7ep()
