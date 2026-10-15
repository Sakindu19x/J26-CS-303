r"""Pre-registered E5-Removed Sensitivity Analysis (prereg Section 8).

Evaluates the 6-fold Leave-One-Episode-Out (LOEO) design with Episode E5 entirely removed
(neither used for training nor evaluation) across {E1, E2, E3, E4, E6, E7}.
Evaluates:
  1. Technique collapsed_full (N=93)
  2. Tactic tactic_collapsed (N=74)

Reports:
  - Pooled and per-fold performance metrics (Markov, Frequency, markov_fallback)
  - Coverage and ceiling rates
  - Wilson 95% score confidence intervals
  - Exact McNemar paired test (labeled: "sensitivity, raw p")
  - Code-based comparison against the all-7-episodes results from reports/7ep/evaluation_7ep_results.json.

Outputs:
  - data/processed_7ep/e5_removed_predictions.csv
  - reports/7ep/e5_removed_results.json
  - reports/7ep/e5_removed_report.md
"""
from __future__ import annotations

import copy
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.c4.evaluation import evaluate_loeo_slice, wilson_interval
from src.c4.models.frequency import FrequencyBaseline
from src.c4.models.markov import MarkovModel
from src.c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
    evaluate_tactic_slice,
)

DATA_7EP = BASE_DIR / "data" / "processed_7ep"
REPORTS_7EP = BASE_DIR / "reports" / "7ep"

SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
ALL_EP_RESULTS_PATH = REPORTS_7EP / "evaluation_7ep_results.json"

PREDICTIONS_CSV_PATH = DATA_7EP / "e5_removed_predictions.csv"
RESULTS_JSON_PATH = REPORTS_7EP / "e5_removed_results.json"
REPORT_MD_PATH = REPORTS_7EP / "e5_removed_report.md"

EPISODES_6 = ["E1", "E2", "E3", "E4", "E6", "E7"]


def exact_mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar test p-value based on binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def run_e5_removed_sensitivity() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING E5-REMOVED SENSITIVITY ANALYSIS (6-FOLD LOEO)")
    print("=" * 80)

    # 1. Load data from processed_7ep
    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        full_seqs_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        full_samples_data = json.load(f)

    # Build 6-fold LOEO configuration
    e5_removed_folds = [
        {
            "fold_id": f"fold_{ep.lower()}",
            "test_episode": ep,
            "training_episodes": [e for e in EPISODES_6 if e != ep],
        }
        for ep in EPISODES_6
    ]

    # Filter sequences to exclude E5 entirely
    seqs_data_no_e5 = {
        "causation_disclaimer": full_seqs_data.get("causation_disclaimer", ""),
        "episodes": {
            ep: copy.deepcopy(full_seqs_data["episodes"][ep])
            for ep in EPISODES_6
        },
    }

    # Filter technique samples
    tech_col_samples_no_e5 = [
        s for s in full_samples_data
        if s["variant"] == "collapsed"
        and s["granularity"] == "full"
        and s["episode_id"] in EPISODES_6
    ]
    assert len(tech_col_samples_no_e5) == 93, f"Expected 93 technique samples without E5, got {len(tech_col_samples_no_e5)}"

    # 2. Evaluate Technique collapsed_full (N=93)
    print("\n[1/2] Evaluating Technique collapsed_full (6-fold LOEO, N=93)...")
    tech_res, tech_raw_rows = evaluate_loeo_slice(
        variant="collapsed",
        granularity="full",
        save_fold_models=False,
        sequences_data=seqs_data_no_e5,
        folds_data=e5_removed_folds,
        samples_data=tech_col_samples_no_e5,
    )
    assert tech_res["n_samples"] == 93, f"Expected 93 technique samples, got {tech_res['n_samples']}"

    # 3. Evaluate Tactic tactic_collapsed (N=74)
    print("\n[2/2] Evaluating Tactic tactic_collapsed (6-fold LOEO, N=74)...")
    tac_res, tac_raw_rows = evaluate_tactic_slice(
        variant="tactic_collapsed",
        sequences_data=seqs_data_no_e5,
        folds_data=e5_removed_folds,
    )
    assert tac_res["n_samples"] == 74, f"Expected 74 tactic samples, got {tac_res['n_samples']}"

    # 4. Build unified predictions CSV
    csv_rows = []
    ep_seqs = seqs_data_no_e5["episodes"]
    t_seqs = build_tactic_sequences(seqs_data_no_e5)["episodes"] if "episodes" in build_tactic_sequences(seqs_data_no_e5) else build_tactic_sequences(seqs_data_no_e5)
    ep_t_seqs = {ep_id: t_seqs[ep_id]["tactic_collapsed"] for ep_id in t_seqs}

    def assemble_csv_slice(
        slice_name: str,
        raw_eval_rows: list[dict[str, Any]],
        samples_list: list[dict[str, Any]],
        is_tactic: bool,
    ):
        grouped: dict[str, dict[str, dict[str, Any]]] = {}
        for r in raw_eval_rows:
            sid = r["sample_id"]
            if sid not in grouped:
                grouped[sid] = {}
            grouped[sid][r["method"]] = r

        meta_map = {s["sample_id"]: s for s in samples_list}

        for sid, by_method in grouped.items():
            s_meta = meta_map[sid]
            test_ep = s_meta["episode_id"]

            if is_tactic:
                cur_history = s_meta["current_tactics"]
                tgt_set = sorted(s_meta["target_tactics"])
            else:
                cur_history = s_meta["current_technique_set"]
                tgt_set = sorted(s_meta["target_technique_set"])

            m_row = by_method["markov"]
            f_row = by_method["frequency"]
            fb_row = by_method["markov_fallback"]

            is_covered = (m_row["status"] == "ok")

            if is_tactic:
                train_eps = [f["training_episodes"] for f in e5_removed_folds if f["test_episode"] == test_ep][0]
                t_pool: set[str] = set()
                for ep in train_eps:
                    itms = ep_t_seqs[ep]
                    for i in range(len(itms) - 1):
                        t_pool.update(itms[i + 1]["tactics"])
                is_ceiling = bool(set(tgt_set) & t_pool)
            else:
                train_eps = [f["training_episodes"] for f in e5_removed_folds if f["test_episode"] == test_ep][0]
                t_pool = set()
                for ep in train_eps:
                    itms = ep_seqs[ep]["collapsed"]
                    for i in range(len(itms) - 1):
                        techs = itms[i + 1]["techniques"] if isinstance(itms[i + 1], dict) and "techniques" in itms[i + 1] else [itms[i + 1]]
                        t_pool.update(techs)
                is_ceiling = bool(set(tgt_set) & t_pool)

            csv_rows.append({
                "sample_id": sid,
                "slice": slice_name,
                "test_episode": test_ep,
                "input_history": json.dumps(cur_history),
                "target_set": json.dumps(tgt_set),
                "markov_top3": m_row["predicted_candidates_top3"],
                "frequency_top3": f_row["predicted_candidates_top3"],
                "markov_fallback_top3": fb_row["predicted_candidates_top3"],
                "markov_status": m_row["status"],
                "markov_hit1": m_row["hit1"],
                "markov_hit3": m_row["hit3"],
                "frequency_hit1": f_row["hit1"],
                "frequency_hit3": f_row["hit3"],
                "markov_fallback_hit1": fb_row["hit1"],
                "markov_fallback_hit3": fb_row["hit3"],
                "covered": is_covered,
                "ceiling": is_ceiling,
            })

    # Build tactic samples list for metadata mapping
    tac_samples_list = []
    for ep_id in sorted(ep_t_seqs.keys()):
        items = ep_t_seqs[ep_id]
        for k in range(len(items) - 1):
            sid = f"{ep_id}-tac-col-K{k + 1:02d}"
            tac_samples_list.append({
                "sample_id": sid,
                "episode_id": ep_id,
                "current_tactics": items[k]["tactics"],
                "target_tactics": items[k + 1]["tactics"],
            })

    assemble_csv_slice("collapsed_full", tech_raw_rows, tech_col_samples_no_e5, is_tactic=False)
    assemble_csv_slice("tactic_collapsed", tac_raw_rows, tac_samples_list, is_tactic=True)

    fieldnames = [
        "sample_id", "slice", "test_episode", "input_history", "target_set",
        "markov_top3", "frequency_top3", "markov_fallback_top3",
        "markov_status", "markov_hit1", "markov_hit3",
        "frequency_hit1", "frequency_hit3",
        "markov_fallback_hit1", "markov_fallback_hit3",
        "covered", "ceiling"
    ]
    with open(PREDICTIONS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Predictions CSV written: {len(csv_rows)} rows (93 tech + 74 tac).")
    assert len(csv_rows) == 167, f"Expected 167 rows, got {len(csv_rows)}"

    # 5. McNemar paired tests (sensitivity, raw p)
    print("\nComputing exact McNemar tests (sensitivity, raw p)...")
    mcnemar_results: dict[str, Any] = {}

    def compute_mcnemar_pair(slice_name: str, metric_name: str, m1_col: str, m2_col: str) -> dict[str, Any]:
        rows_slice = [r for r in csv_rows if r["slice"] == slice_name]
        n_tot = len(rows_slice)
        b_cnt = sum(1 for r in rows_slice if r[m1_col] == 1 and r[m2_col] == 0)
        c_cnt = sum(1 for r in rows_slice if r[m1_col] == 0 and r[m2_col] == 1)
        both_cnt = sum(1 for r in rows_slice if r[m1_col] == 1 and r[m2_col] == 1)
        neither_cnt = sum(1 for r in rows_slice if r[m1_col] == 0 and r[m2_col] == 0)
        p_val = exact_mcnemar(b_cnt, c_cnt)
        m1_rate = (b_cnt + both_cnt) / n_tot if n_tot > 0 else 0.0
        m2_rate = (c_cnt + both_cnt) / n_tot if n_tot > 0 else 0.0
        return {
            "slice": slice_name,
            "metric": metric_name,
            "model_1": "markov",
            "model_2": "frequency",
            "n_samples": n_tot,
            "table_2x2": {
                "both_hit": both_cnt,
                "m1_hit_m2_miss": b_cnt,
                "m1_miss_m2_hit": c_cnt,
                "neither_hit": neither_cnt,
            },
            "markov_rate": m1_rate,
            "frequency_rate": m2_rate,
            "difference": m1_rate - m2_rate,
            "p_value_raw": p_val,
            "label": "sensitivity, raw p",
        }

    mcnemar_results["technique_hit3"] = compute_mcnemar_pair("collapsed_full", "Hit@3", "markov_hit3", "frequency_hit3")
    mcnemar_results["tactic_hit3"] = compute_mcnemar_pair("tactic_collapsed", "Hit@3", "markov_hit3", "frequency_hit3")
    mcnemar_results["technique_hit1"] = compute_mcnemar_pair("collapsed_full", "Hit@1", "markov_hit1", "frequency_hit1")
    mcnemar_results["tactic_hit1"] = compute_mcnemar_pair("tactic_collapsed", "Hit@1", "markov_hit1", "frequency_hit1")

    # 6. Compare with 7-episode all-episodes numbers from 12a JSON by code
    print("\nComparing against 7-episode all-episodes evaluation results from 12a...")
    with open(ALL_EP_RESULTS_PATH, "r", encoding="utf-8") as f:
        all_ep_data = json.load(f)

    all_tech = all_ep_data["primary_slice_technique_collapsed_full"]
    all_tac = all_ep_data["secondary_slice_tactic_collapsed"]

    comparison: dict[str, Any] = {
        "technique_collapsed_full": {
            "all_7ep": {
                "n_samples": all_tech["n_samples"],
                "markov_hit1": all_tech["headline"]["markov"]["hit1"],
                "markov_hit3": all_tech["headline"]["markov"]["hit3"],
                "markov_top1": all_tech["headline"]["markov"]["top1"],
                "markov_top3": all_tech["headline"]["markov"]["top3"],
                "frequency_hit1": all_tech["headline"]["frequency"]["hit1"],
                "frequency_hit3": all_tech["headline"]["frequency"]["hit3"],
                "frequency_top1": all_tech["headline"]["frequency"]["top1"],
                "frequency_top3": all_tech["headline"]["frequency"]["top3"],
                "fallback_hit1": all_tech["headline"]["fallback"]["hit1"],
                "fallback_hit3": all_tech["headline"]["fallback"]["hit3"],
                "fallback_top1": all_tech["headline"]["fallback"]["top1"],
                "fallback_top3": all_tech["headline"]["fallback"]["top3"],
                "coverage_covered": all_tech["headline"]["coverage"]["covered_samples"],
                "coverage_rate": all_tech["headline"]["coverage"]["coverage_rate"],
                "ceiling_hits": all_tech["headline"]["ceiling"]["hits"],
                "ceiling_rate": all_tech["headline"]["ceiling"]["ceiling_rate"],
                "mcnemar_p_hit3": all_ep_data["paired_tests"]["P2_technique_collapsed_full_hit3"]["p_value_raw"],
            },
            "e5_removed_6ep": {
                "n_samples": tech_res["n_samples"],
                "markov_hit1": tech_res["headline"]["markov"]["hit1"],
                "markov_hit3": tech_res["headline"]["markov"]["hit3"],
                "markov_top1": tech_res["headline"]["markov"]["top1"],
                "markov_top3": tech_res["headline"]["markov"]["top3"],
                "frequency_hit1": tech_res["headline"]["frequency"]["hit1"],
                "frequency_hit3": tech_res["headline"]["frequency"]["hit3"],
                "frequency_top1": tech_res["headline"]["frequency"]["top1"],
                "frequency_top3": tech_res["headline"]["frequency"]["top3"],
                "fallback_hit1": tech_res["headline"]["fallback"]["hit1"],
                "fallback_hit3": tech_res["headline"]["fallback"]["hit3"],
                "fallback_top1": tech_res["headline"]["fallback"]["top1"],
                "fallback_top3": tech_res["headline"]["fallback"]["top3"],
                "coverage_covered": tech_res["headline"]["coverage"]["covered_samples"],
                "coverage_rate": tech_res["headline"]["coverage"]["coverage_rate"],
                "ceiling_hits": tech_res["headline"]["ceiling"]["hits"],
                "ceiling_rate": tech_res["headline"]["ceiling"]["ceiling_rate"],
                "mcnemar_p_hit3": mcnemar_results["technique_hit3"]["p_value_raw"],
            },
        },
        "tactic_collapsed": {
            "all_7ep": {
                "n_samples": all_tac["n_samples"],
                "markov_hit1": all_tac["headline"]["markov"]["hit1"],
                "markov_hit3": all_tac["headline"]["markov"]["hit3"],
                "markov_top1": all_tac["headline"]["markov"]["top1"],
                "markov_top3": all_tac["headline"]["markov"]["top3"],
                "frequency_hit1": all_tac["headline"]["frequency"]["hit1"],
                "frequency_hit3": all_tac["headline"]["frequency"]["hit3"],
                "frequency_top1": all_tac["headline"]["frequency"]["top1"],
                "frequency_top3": all_tac["headline"]["frequency"]["top3"],
                "fallback_hit1": all_tac["headline"]["markov_fallback"]["hit1"],
                "fallback_hit3": all_tac["headline"]["markov_fallback"]["hit3"],
                "fallback_top1": all_tac["headline"]["markov_fallback"]["top1"],
                "fallback_top3": all_tac["headline"]["markov_fallback"]["top3"],
                "coverage_covered": all_tac["coverage"]["covered_samples"],
                "coverage_rate": all_tac["coverage"]["coverage_rate"],
                "ceiling_hits": all_tac["ceiling"]["hits"],
                "ceiling_rate": all_tac["ceiling"]["ceiling_rate"],
                "mcnemar_p_hit3": all_ep_data["paired_tests"]["P1_tactic_collapsed_hit3"]["p_value_raw"],
            },
            "e5_removed_6ep": {
                "n_samples": tac_res["n_samples"],
                "markov_hit1": tac_res["headline"]["markov"]["hit1"],
                "markov_hit3": tac_res["headline"]["markov"]["hit3"],
                "markov_top1": tac_res["headline"]["markov"]["top1"],
                "markov_top3": tac_res["headline"]["markov"]["top3"],
                "frequency_hit1": tac_res["headline"]["frequency"]["hit1"],
                "frequency_hit3": tac_res["headline"]["frequency"]["hit3"],
                "frequency_top1": tac_res["headline"]["frequency"]["top1"],
                "frequency_top3": tac_res["headline"]["frequency"]["top3"],
                "fallback_hit1": tac_res["headline"]["markov_fallback"]["hit1"],
                "fallback_hit3": tac_res["headline"]["markov_fallback"]["hit3"],
                "fallback_top1": tac_res["headline"]["markov_fallback"]["top1"],
                "fallback_top3": tac_res["headline"]["markov_fallback"]["top3"],
                "coverage_covered": tac_res["coverage"]["covered_samples"],
                "coverage_rate": tac_res["coverage"]["coverage_rate"],
                "ceiling_hits": tac_res["ceiling"]["hits"],
                "ceiling_rate": tac_res["ceiling"]["ceiling_rate"],
                "mcnemar_p_hit3": mcnemar_results["tactic_hit3"]["p_value_raw"],
            },
        },
    }

    report_data: dict[str, Any] = {
        "metadata": {
            "analysis": "E5-Removed Sensitivity Analysis (6-fold LOEO)",
            "episodes": EPISODES_6,
            "excluded_episode": "E5",
            "folds": [f["fold_id"] for f in e5_removed_folds],
        },
        "technique_collapsed_full": tech_res,
        "tactic_collapsed": tac_res,
        "paired_tests": mcnemar_results,
        "comparison_with_all_7ep": comparison,
    }

    # 7. Write JSON
    print(f"Writing sensitivity JSON to {RESULTS_JSON_PATH}...")
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, sort_keys=True)

    # 8. Write Markdown report
    print(f"Writing sensitivity Markdown to {REPORT_MD_PATH}...")
    generate_markdown_report_e5_removed(report_data)

    print("E5-Removed Sensitivity Analysis completed successfully.")
    return report_data


def generate_markdown_report_e5_removed(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    cmp_data = data["comparison_with_all_7ep"]
    tech_data = data["technique_collapsed_full"]
    tac_data = data["tactic_collapsed"]
    p_tests = data["paired_tests"]

    A("# Pre-Registered E5-Removed Sensitivity Analysis Report")
    A()
    A("## Pre-Registered Context & Design (prereg Section 8)")
    A()
    A("- **Purpose**: Evaluate the sensitivity of findings to the inclusion of Episode E5 (which contains only 3 labeled steps and 2 transitions, with 0 coverage and 0 ceiling hits under 7-fold LOEO).")
    A("- **Protocol**: Full 6-fold Leave-One-Episode-Out cross-validation across {E1, E2, E3, E4, E6, E7}, with Episode E5 entirely excluded from both model training and evaluation.")
    A("- **Evaluated Slices**: Technique `collapsed_full` ($N=93$) and Tactic `tactic_collapsed` ($N=74$).")
    A("- **Statistical Labels**: Paired McNemar tests labeled strictly as `\"sensitivity, raw p\"`.")
    A()
    A("---")
    A()
    A("## Comparison: All 7 Episodes vs. E5-Removed (6 Episodes)")
    A()
    A("### Technique Level (`collapsed_full`)")
    A()
    A("| Metric | All 7 Episodes (N=95) | E5 Removed (N=93) | Difference (E5-Removed − All 7ep) |")
    A("|:---|:---:|:---:|:---:|")
    t_all = cmp_data["technique_collapsed_full"]["all_7ep"]
    t_no = cmp_data["technique_collapsed_full"]["e5_removed_6ep"]
    A(f"| Evaluated Samples ($N$) | {t_all['n_samples']} | {t_no['n_samples']} | -2 |")
    A(f"| Coverage Rate | {t_all['coverage_rate']:.4f} ({t_all['coverage_covered']}/{t_all['n_samples']}) | {t_no['coverage_rate']:.4f} ({t_no['coverage_covered']}/{t_no['n_samples']}) | {t_no['coverage_rate'] - t_all['coverage_rate']:+.4f} |")
    A(f"| Ceiling Rate | {t_all['ceiling_rate']:.4f} ({t_all['ceiling_hits']}/{t_all['n_samples']}) | {t_no['ceiling_rate']:.4f} ({t_no['ceiling_hits']}/{t_no['n_samples']}) | {t_no['ceiling_rate'] - t_all['ceiling_rate']:+.4f} |")
    A(f"| Markov Hit@1 | {t_all['markov_top1']:.4f} ({t_all['markov_hit1']}/{t_all['n_samples']}) | {t_no['markov_top1']:.4f} ({t_no['markov_hit1']}/{t_no['n_samples']}) | {t_no['markov_top1'] - t_all['markov_top1']:+.4f} |")
    A(f"| Markov Hit@3 | {t_all['markov_top3']:.4f} ({t_all['markov_hit3']}/{t_all['n_samples']}) | {t_no['markov_top3']:.4f} ({t_no['markov_hit3']}/{t_no['n_samples']}) | {t_no['markov_top3'] - t_all['markov_top3']:+.4f} |")
    A(f"| Frequency Hit@1 | {t_all['frequency_top1']:.4f} ({t_all['frequency_hit1']}/{t_all['n_samples']}) | {t_no['frequency_top1']:.4f} ({t_no['frequency_hit1']}/{t_no['n_samples']}) | {t_no['frequency_top1'] - t_all['frequency_top1']:+.4f} |")
    A(f"| Frequency Hit@3 | {t_all['frequency_top3']:.4f} ({t_all['frequency_hit3']}/{t_all['n_samples']}) | {t_no['frequency_top3']:.4f} ({t_no['frequency_hit3']}/{t_no['n_samples']}) | {t_no['frequency_top3'] - t_all['frequency_top3']:+.4f} |")
    A(f"| Fallback Hit@1 | {t_all['fallback_top1']:.4f} ({t_all['fallback_hit1']}/{t_all['n_samples']}) | {t_no['fallback_top1']:.4f} ({t_no['fallback_hit1']}/{t_no['n_samples']}) | {t_no['fallback_top1'] - t_all['fallback_top1']:+.4f} |")
    A(f"| Fallback Hit@3 | {t_all['fallback_top3']:.4f} ({t_all['fallback_hit3']}/{t_all['n_samples']}) | {t_no['fallback_top3']:.4f} ({t_no['fallback_hit3']}/{t_no['n_samples']}) | {t_no['fallback_top3'] - t_all['fallback_top3']:+.4f} |")
    A(f"| Exact McNemar p (Hit@3) | {t_all['mcnemar_p_hit3']:.4f} | {t_no['mcnemar_p_hit3']:.4f} (sensitivity, raw p) | {t_no['mcnemar_p_hit3'] - t_all['mcnemar_p_hit3']:+.4f} |")
    A()
    A("### Tactic Level (`tactic_collapsed`)")
    A()
    A("| Metric | All 7 Episodes (N=76) | E5 Removed (N=74) | Difference (E5-Removed − All 7ep) |")
    A("|:---|:---:|:---:|:---:|")
    tc_all = cmp_data["tactic_collapsed"]["all_7ep"]
    tc_no = cmp_data["tactic_collapsed"]["e5_removed_6ep"]
    A(f"| Evaluated Samples ($N$) | {tc_all['n_samples']} | {tc_no['n_samples']} | -2 |")
    A(f"| Coverage Rate | {tc_all['coverage_rate']:.4f} ({tc_all['coverage_covered']}/{tc_all['n_samples']}) | {tc_no['coverage_rate']:.4f} ({tc_no['coverage_covered']}/{tc_no['n_samples']}) | {tc_no['coverage_rate'] - tc_all['coverage_rate']:+.4f} |")
    A(f"| Ceiling Rate | {tc_all['ceiling_rate']:.4f} ({tc_all['ceiling_hits']}/{tc_all['n_samples']}) | {tc_no['ceiling_rate']:.4f} ({tc_no['ceiling_hits']}/{tc_no['n_samples']}) | {tc_no['ceiling_rate'] - tc_all['ceiling_rate']:+.4f} |")
    A(f"| Markov Hit@1 | {tc_all['markov_top1']:.4f} ({tc_all['markov_hit1']}/{tc_all['n_samples']}) | {tc_no['markov_top1']:.4f} ({tc_no['markov_hit1']}/{tc_no['n_samples']}) | {tc_no['markov_top1'] - tc_all['markov_top1']:+.4f} |")
    A(f"| Markov Hit@3 | {tc_all['markov_top3']:.4f} ({tc_all['markov_hit3']}/{tc_all['n_samples']}) | {tc_no['markov_top3']:.4f} ({tc_no['markov_hit3']}/{tc_no['n_samples']}) | {tc_no['markov_top3'] - tc_all['markov_top3']:+.4f} |")
    A(f"| Frequency Hit@1 | {tc_all['frequency_top1']:.4f} ({tc_all['frequency_hit1']}/{tc_all['n_samples']}) | {tc_no['frequency_top1']:.4f} ({tc_no['frequency_hit1']}/{tc_no['n_samples']}) | {tc_no['frequency_top1'] - tc_all['frequency_top1']:+.4f} |")
    A(f"| Frequency Hit@3 | {tc_all['frequency_top3']:.4f} ({tc_all['frequency_hit3']}/{tc_all['n_samples']}) | {tc_no['frequency_top3']:.4f} ({tc_no['frequency_hit3']}/{tc_no['n_samples']}) | {tc_no['frequency_top3'] - tc_all['frequency_top3']:+.4f} |")
    A(f"| Fallback Hit@1 | {tc_all['fallback_top1']:.4f} ({tc_all['fallback_hit1']}/{tc_all['n_samples']}) | {tc_no['fallback_top1']:.4f} ({tc_no['fallback_hit1']}/{tc_no['n_samples']}) | {tc_no['fallback_top1'] - tc_all['fallback_top1']:+.4f} |")
    A(f"| Fallback Hit@3 | {tc_all['fallback_top3']:.4f} ({tc_all['fallback_hit3']}/{tc_all['n_samples']}) | {tc_no['fallback_top3']:.4f} ({tc_no['fallback_hit3']}/{tc_no['n_samples']}) | {tc_no['fallback_top3'] - tc_all['fallback_top3']:+.4f} |")
    A(f"| Exact McNemar p (Hit@3) | {tc_all['mcnemar_p_hit3']:.4f} | {tc_no['mcnemar_p_hit3']:.4f} (sensitivity, raw p) | {tc_no['mcnemar_p_hit3'] - tc_all['mcnemar_p_hit3']:+.4f} |")
    A()
    A("---")
    A()
    A("## Pooled Results Summary (E5 Removed)")
    A()
    A("### Technique (`collapsed_full`, N=93)")
    A()
    h_tech = tech_data["headline"]
    n_tech = tech_data["n_samples"]
    A(f"- **Coverage**: `{h_tech['coverage']['covered_samples']}/{n_tech}` ({h_tech['coverage']['coverage_rate']:.4f})")
    A(f"- **Ceiling**: `{h_tech['ceiling']['hits']}/{n_tech}` ({h_tech['ceiling']['ceiling_rate']:.4f})")
    A(f"- **Markov Hit@1**: `{h_tech['markov']['hit1']}/{n_tech}` ({h_tech['markov']['top1']:.4f}, 95% Wilson: `[{h_tech['markov']['wilson95_top1'][0]:.4f}, {h_tech['markov']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Markov Hit@3**: `{h_tech['markov']['hit3']}/{n_tech}` ({h_tech['markov']['top3']:.4f}, 95% Wilson: `[{h_tech['markov']['wilson95_top3'][0]:.4f}, {h_tech['markov']['wilson95_top3'][1]:.4f}]`)")
    A(f"- **Frequency Hit@1**: `{h_tech['frequency']['hit1']}/{n_tech}` ({h_tech['frequency']['top1']:.4f}, 95% Wilson: `[{h_tech['frequency']['wilson95_top1'][0]:.4f}, {h_tech['frequency']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Frequency Hit@3**: `{h_tech['frequency']['hit3']}/{n_tech}` ({h_tech['frequency']['top3']:.4f}, 95% Wilson: `[{h_tech['frequency']['wilson95_top3'][0]:.4f}, {h_tech['frequency']['wilson95_top3'][1]:.4f}]`)")
    A(f"- **Fallback Hit@1**: `{h_tech['fallback']['hit1']}/{n_tech}` ({h_tech['fallback']['top1']:.4f}, 95% Wilson: `[{h_tech['fallback']['wilson95_top1'][0]:.4f}, {h_tech['fallback']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Fallback Hit@3**: `{h_tech['fallback']['hit3']}/{n_tech}` ({h_tech['fallback']['top3']:.4f}, 95% Wilson: `[{h_tech['fallback']['wilson95_top3'][0]:.4f}, {h_tech['fallback']['wilson95_top3'][1]:.4f}]`)")
    A()
    A("### Tactic (`tactic_collapsed`, N=74)")
    A()
    h_tac = tac_data["headline"]
    cov_tac = tac_data["coverage"]
    ceil_tac = tac_data["ceiling"]
    n_tac = tac_data["n_samples"]
    A(f"- **Coverage**: `{cov_tac['covered_samples']}/{n_tac}` ({cov_tac['coverage_rate']:.4f})")
    A(f"- **Ceiling**: `{ceil_tac['hits']}/{n_tac}` ({ceil_tac['ceiling_rate']:.4f})")
    A(f"- **Markov Hit@1**: `{h_tac['markov']['hit1']}/{n_tac}` ({h_tac['markov']['top1']:.4f}, 95% Wilson: `[{h_tac['markov']['wilson95_top1'][0]:.4f}, {h_tac['markov']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Markov Hit@3**: `{h_tac['markov']['hit3']}/{n_tac}` ({h_tac['markov']['top3']:.4f}, 95% Wilson: `[{h_tac['markov']['wilson95_top3'][0]:.4f}, {h_tac['markov']['wilson95_top3'][1]:.4f}]`)")
    A(f"- **Frequency Hit@1**: `{h_tac['frequency']['hit1']}/{n_tac}` ({h_tac['frequency']['top1']:.4f}, 95% Wilson: `[{h_tac['frequency']['wilson95_top1'][0]:.4f}, {h_tac['frequency']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Frequency Hit@3**: `{h_tac['frequency']['hit3']}/{n_tac}` ({h_tac['frequency']['top3']:.4f}, 95% Wilson: `[{h_tac['frequency']['wilson95_top3'][0]:.4f}, {h_tac['frequency']['wilson95_top3'][1]:.4f}]`)")
    A(f"- **Fallback Hit@1**: `{h_tac['markov_fallback']['hit1']}/{n_tac}` ({h_tac['markov_fallback']['top1']:.4f}, 95% Wilson: `[{h_tac['markov_fallback']['wilson95_top1'][0]:.4f}, {h_tac['markov_fallback']['wilson95_top1'][1]:.4f}]`)")
    A(f"- **Fallback Hit@3**: `{h_tac['markov_fallback']['hit3']}/{n_tac}` ({h_tac['markov_fallback']['top3']:.4f}, 95% Wilson: `[{h_tac['markov_fallback']['wilson95_top3'][0]:.4f}, {h_tac['markov_fallback']['wilson95_top3'][1]:.4f}]`)")
    A()
    A("---")
    A()
    A("## Per-Fold Performance Tables (E5 Removed)")
    A()
    A("### Technique Level (`collapsed_full`)")
    A()
    A("| Fold | Test Episode | N | Coverage | Ceiling | Markov Hit@1 | Markov Hit@3 | Frequency Hit@1 | Frequency Hit@3 | Fallback Hit@1 | Fallback Hit@3 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for f_id, fld in tech_data["per_fold"].items():
        cov_r = fld["markov"]["coverage"]
        ceil_r = fld["ceiling"]["rate"]
        A(f"| {f_id} | {fld['test_episode']} | {fld['n_samples']} | {cov_r:.4f} | {ceil_r:.4f} | {fld['markov']['top1']:.4f} | {fld['markov']['top3']:.4f} | {fld['frequency']['top1']:.4f} | {fld['frequency']['top3']:.4f} | {fld['fallback']['top1']:.4f} | {fld['fallback']['top3']:.4f} |")
    A()
    A("### Tactic Level (`tactic_collapsed`)")
    A()
    A("| Fold | Test Episode | N | Coverage | Ceiling | Markov Hit@1 | Markov Hit@3 | Frequency Hit@1 | Frequency Hit@3 | Fallback Hit@1 | Fallback Hit@3 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for f_id, fld in tac_data["per_fold"].items():
        cov_r = fld["covered_samples"] / fld["n_samples"] if fld["n_samples"] > 0 else 0.0
        ceil_r = fld["ceiling_hits"] / fld["n_samples"] if fld["n_samples"] > 0 else 0.0
        A(f"| {f_id} | {fld['test_episode']} | {fld['n_samples']} | {cov_r:.4f} | {ceil_r:.4f} | {fld['markov']['top1']:.4f} | {fld['markov']['top3']:.4f} | {fld['frequency']['top1']:.4f} | {fld['frequency']['top3']:.4f} | {fld['fallback']['top1']:.4f} | {fld['fallback']['top3']:.4f} |")
    A()
    A("---")
    A()
    A("## McNemar Paired Tests (Sensitivity Analysis)")
    A()
    A("| Comparison | N | Both Hit | Markov Only | Freq Only | Neither Hit | Markov Rate | Freq Rate | Difference | p-value (sensitivity, raw p) |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for k in ["technique_hit3", "tactic_hit3", "technique_hit1", "tactic_hit1"]:
        pt = p_tests[k]
        tb = pt["table_2x2"]
        A(f"| {pt['slice']} {pt['metric']} | {pt['n_samples']} | {tb['both_hit']} | {tb['m1_hit_m2_miss']} | {tb['m1_miss_m2_hit']} | {tb['neither_hit']} | {pt['markov_rate']:.4f} | {pt['frequency_rate']:.4f} | {pt['difference']:+.4f} | {pt['p_value_raw']:.4f} |")
    A()

    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_e5_removed_sensitivity()
