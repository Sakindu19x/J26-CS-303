r"""Exploratory Post Hoc Variant: Tactic-Conditioned Technique Prediction (Amendment 7).

Declared under Amendment 7 to the 7-Episode Pre-Registration before execution.
EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT.

Algorithm:
1. Map current technique set to current tactic set using technique_tactic_reference.json.
2. Tactic-level Markov model trained on training episodes only (tactic_collapsed) predicts next tactics.
3. For each tactic in rank order, candidate techniques = techniques mapping to that tactic that occur
   in training episodes as targets (collapsed_full), sorted by (-training target frequency, technique id),
   concatenated and de-duplicated.
4. Top-k = first k.
5. If tactic Markov status is not ok or list is empty, fallback to fold Frequency baseline list.
6. Pad with Frequency baseline candidates if list has < k techniques.

Outputs:
- data/processed_7ep/exploratory_tactic_conditioned_predictions.csv
- reports/7ep/exploratory_tactic_conditioned_results.json
- reports/7ep/exploratory_tactic_conditioned_report.md
"""
from __future__ import annotations

import copy
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "src"))

from src.c4.models.frequency import FrequencyBaseline
from src.c4.models.markov import MarkovModel
from src.c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
    to_shortnames,
    wilson_interval,
)
from scripts.run_tie_sensitivity_7ep import (
    load_fold_model_from_disk,
    evaluate_sample_ties,
    exact_mcnemar,
)

DATA_7EP = REPO_ROOT / "data" / "processed_7ep"
REPORTS_7EP = REPO_ROOT / "reports" / "7ep"

SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
TECH_REF_PATH = DATA_7EP / "technique_tactic_reference.json"

OUT_CSV_PATH = DATA_7EP / "exploratory_tactic_conditioned_predictions.csv"
OUT_JSON_PATH = REPORTS_7EP / "exploratory_tactic_conditioned_results.json"
OUT_MD_PATH = REPORTS_7EP / "exploratory_tactic_conditioned_report.md"

EPISODES_7 = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
EPISODES_6 = ["E1", "E2", "E3", "E4", "E6", "E7"]


def load_tech_ref() -> dict[str, list[str]]:
    with open(TECH_REF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    mapping = {}
    for tech, info in data.items():
        mapping[tech.strip().upper()] = to_shortnames(info.get("official_tactics", []))
    return mapping


def run_exploratory_tactic_conditioned() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING EXPLORATORY TACTIC-CONDITIONED TECHNIQUE PREDICTION (AMENDMENT 7)")
    print("Status: POST HOC, NOT A PRE-REGISTERED RESULT")
    print("=" * 80)

    tech_ref_map = load_tech_ref()

    def tech_to_tacs(tech: str) -> list[str]:
        return tech_ref_map.get(tech.strip().upper(), [])

    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_raw = json.load(f)

    tech_samples = [
        s for s in samples_raw
        if s["variant"] == "collapsed" and s["granularity"] == "full"
    ]
    assert len(tech_samples) == 95, f"Expected 95 technique samples, got {len(tech_samples)}"

    # Build models for E5-removed
    seqs_no_e5 = {
        "causation_disclaimer": seqs_data.get("causation_disclaimer", ""),
        "episodes": {ep: copy.deepcopy(seqs_data["episodes"][ep]) for ep in EPISODES_6},
    }
    t_all_no_e5 = build_tactic_sequences(seqs_no_e5)
    ep_t_seqs_no_e5 = {ep: t_all_no_e5[ep]["tactic_collapsed"] for ep in EPISODES_6}

    models_no_e5 = {}
    for ep in EPISODES_6:
        tr = [e for e in EPISODES_6 if e != ep]
        m_cf = MarkovModel(variant="collapsed", granularity="full").fit(seqs_no_e5, tr)
        f_cf = FrequencyBaseline(variant="collapsed", granularity="full").fit(seqs_no_e5, tr)
        m_tac = TacticMarkovModel().fit(ep_t_seqs_no_e5, tr)
        f_tac = TacticFrequencyBaseline().fit(ep_t_seqs_no_e5, tr)
        models_no_e5[ep] = (m_tac, f_tac, m_cf, f_cf)

    # Models for 7ep
    models_7ep = {}
    for ep in EPISODES_7:
        t_m, t_f = load_fold_model_from_disk("tactic_collapsed", ep)
        m_m, m_f = load_fold_model_from_disk("collapsed_full", ep)
        models_7ep[ep] = (t_m, t_f, m_m, m_f)

    runs_config = [
        ("7ep", EPISODES_7, models_7ep),
        ("e5_removed", EPISODES_6, models_no_e5),
    ]

    results_data: dict[str, Any] = {
        "meta": {
            "disclaimer": "EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT",
            "amendment": "Amendment 7 (2026-10-15)",
            "verdict_statement": (
                "The pre-registered primary evaluation verdict (FAIL on P1, Markov does not outperform "
                "Frequency baseline at technique level) is finalized and cannot be modified or overturned "
                "by this exploratory variant."
            ),
        },
        "runs": {},
    }

    csv_rows: list[dict[str, Any]] = []

    for run_id, ep_list, models_dict in runs_config:
        run_samples = [s for s in tech_samples if s["episode_id"] in ep_list]
        N = len(run_samples)

        var_h1 = var_h3 = freq_h1 = freq_h3 = markov_h1 = markov_h3 = 0
        cov_count = 0
        ceil_count = 0

        # McNemar paired counts: b = var=1 & freq=0; c = var=0 & freq=1
        b_h1 = c_h1 = b_h3 = c_h3 = 0

        # Tie sensitivity tracking
        tied_samples_top1 = 0
        tied_samples_top3 = 0
        exp_h1_sum = exp_h3_sum = 0.0
        best_h1_sum = best_h3_sum = 0
        worst_h1_sum = worst_h3_sum = 0

        per_fold: dict[str, dict[str, Any]] = {}
        for ep in ep_list:
            per_fold[ep] = {
                "test_episode": ep,
                "n": 0,
                "variant_hit1": 0,
                "variant_hit3": 0,
                "frequency_hit1": 0,
                "frequency_hit3": 0,
                "markov_hit1": 0,
                "markov_hit3": 0,
                "covered": 0,
                "ceiling": 0,
                "exp_hit1": 0.0,
                "exp_hit3": 0.0,
                "best_hit1": 0,
                "best_hit3": 0,
                "worst_hit1": 0,
                "worst_hit3": 0,
            }

        for s in run_samples:
            sid = s["sample_id"]
            ep = s["episode_id"]
            per_fold[ep]["n"] += 1

            t_m, t_f, m_m, m_f = models_dict[ep]
            cur_techs = s["current_technique_set"]
            tgt_techs = set(s["target_technique_set"])
            train_tech_probs = m_f.probabilities

            # Ceiling
            is_ceil = bool(tgt_techs & set(train_tech_probs.keys()))
            if is_ceil:
                ceil_count += 1
                per_fold[ep]["ceiling"] += 1

            # Derive tactics from current techniques
            cur_tacs = sorted(list(set(tac for tech in cur_techs for tac in tech_to_tacs(tech))))
            t_res = t_m.predict(cur_tacs, k=None)
            t_status = t_res["status"]

            is_cov = (t_status == "ok")
            if is_cov:
                cov_count += 1
                per_fold[ep]["covered"] += 1

            # Variant candidates selection and scoring
            candidates: list[str] = []
            scored_candidates: list[tuple[str, float]] = []
            seen: set[str] = set()

            if is_cov and t_res.get("candidates"):
                n_tacs = len(t_res["candidates"])
                for tac_idx, (tac, p_tac) in enumerate(t_res["candidates"]):
                    matching_techs = [t for t in train_tech_probs if tac in tech_to_tacs(t)]
                    matching_techs.sort(key=lambda t: (-train_tech_probs[t], t))
                    base_score = (n_tacs - tac_idx) * 10.0
                    for t in matching_techs:
                        if t not in seen:
                            seen.add(t)
                            candidates.append(t)
                            scored_candidates.append((t, base_score + train_tech_probs[t]))

            # Fallback and padding
            freq_cands_sorted = [t for t, _ in sorted(train_tech_probs.items(), key=lambda x: (-x[1], x[0]))]
            for t in freq_cands_sorted:
                if t not in seen:
                    seen.add(t)
                    candidates.append(t)
                    scored_candidates.append((t, train_tech_probs[t]))

            # Variant hits
            vh1 = 1 if (candidates and candidates[0] in tgt_techs) else 0
            vh3 = 1 if any(c in tgt_techs for c in candidates[:3]) else 0
            var_h1 += vh1
            var_h3 += vh3
            per_fold[ep]["variant_hit1"] += vh1
            per_fold[ep]["variant_hit3"] += vh3

            # Frequency hits
            f_pred = m_f.predict(k=3)["candidates"]
            f_cands = [c[0] for c in f_pred]
            fh1 = 1 if (f_cands and f_cands[0] in tgt_techs) else 0
            fh3 = 1 if any(c in tgt_techs for c in f_cands[:3]) else 0
            freq_h1 += fh1
            freq_h3 += fh3
            per_fold[ep]["frequency_hit1"] += fh1
            per_fold[ep]["frequency_hit3"] += fh3

            # Markov hits
            m_pred = m_m.predict(cur_techs, k=3)
            if m_pred["status"] == "ok":
                m_cands = [c[0] for c in m_pred["candidates"]]
                mh1 = 1 if (m_cands and m_cands[0] in tgt_techs) else 0
                mh3 = 1 if any(c in tgt_techs for c in m_cands[:3]) else 0
            else:
                mh1 = mh3 = 0
            markov_h1 += mh1
            markov_h3 += mh3
            per_fold[ep]["markov_hit1"] += mh1
            per_fold[ep]["markov_hit3"] += mh3

            # McNemar paired
            if vh1 == 1 and fh1 == 0:
                b_h1 += 1
            elif vh1 == 0 and fh1 == 1:
                c_h1 += 1

            if vh3 == 1 and fh3 == 0:
                b_h3 += 1
            elif vh3 == 0 and fh3 == 1:
                c_h3 += 1

            # Tie sensitivity calculation using P2 machinery
            status_for_tie = "ok" if scored_candidates else "empty"
            g1, tgt_in_g1, exp_h1, best_h1, worst_h1 = evaluate_sample_ties(scored_candidates, tgt_techs, 1, status_for_tie)
            g3, tgt_in_g3, exp_h3, best_h3, worst_h3 = evaluate_sample_ties(scored_candidates, tgt_techs, 3, status_for_tie)

            t1_tied = (g1 > 1)
            t3_tied = (g3 > 1)
            if t1_tied:
                tied_samples_top1 += 1
            if t3_tied:
                tied_samples_top3 += 1

            exp_h1_sum += exp_h1
            exp_h3_sum += exp_h3
            best_h1_sum += best_h1
            best_h3_sum += best_h3
            worst_h1_sum += worst_h1
            worst_h3_sum += worst_h3

            per_fold[ep]["exp_hit1"] += exp_h1
            per_fold[ep]["exp_hit3"] += exp_h3
            per_fold[ep]["best_hit1"] += best_h1
            per_fold[ep]["best_hit3"] += best_h3
            per_fold[ep]["worst_hit1"] += worst_h1
            per_fold[ep]["worst_hit3"] += worst_h3

            if run_id == "7ep":
                csv_rows.append({
                    "sample_id": sid,
                    "slice": "collapsed_full",
                    "test_episode": ep,
                    "input_history": json.dumps(cur_techs),
                    "target_set": json.dumps(sorted(list(tgt_techs))),
                    "current_tactic_set": json.dumps(cur_tacs),
                    "tactic_markov_status": t_status,
                    "predicted_candidates_top3": json.dumps(candidates[:3]),
                    "variant_hit1": vh1,
                    "variant_hit3": vh3,
                    "frequency_hit1": fh1,
                    "frequency_hit3": fh3,
                    "markov_hit1": mh1,
                    "markov_hit3": mh3,
                    "top1_tied": t1_tied,
                    "top3_boundary_tied": t3_tied,
                    "top1_expected_hit": round(exp_h1, 6),
                    "top3_expected_hit": round(exp_h3, 6),
                    "top1_best_hit": best_h1,
                    "top3_best_hit": best_h3,
                    "top1_worst_hit": worst_h1,
                    "top3_worst_hit": worst_h3,
                })

        p_mcnemar_h1 = exact_mcnemar(b_h1, c_h1)
        p_mcnemar_h3 = exact_mcnemar(b_h3, c_h3)

        fold_mean_var_h1 = sum(per_fold[ep]["variant_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_var_h3 = sum(per_fold[ep]["variant_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_freq_h1 = sum(per_fold[ep]["frequency_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_freq_h3 = sum(per_fold[ep]["frequency_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_markov_h1 = sum(per_fold[ep]["markov_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_markov_h3 = sum(per_fold[ep]["markov_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)

        fold_mean_exp_h1 = sum(per_fold[ep]["exp_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_exp_h3 = sum(per_fold[ep]["exp_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_best_h1 = sum(per_fold[ep]["best_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_best_h3 = sum(per_fold[ep]["best_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_worst_h1 = sum(per_fold[ep]["worst_hit1"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)
        fold_mean_worst_h3 = sum(per_fold[ep]["worst_hit3"] / per_fold[ep]["n"] for ep in ep_list) / len(ep_list)

        run_summary = {
            "n_samples": N,
            "coverage": {
                "covered_samples": cov_count,
                "coverage_rate": cov_count / N,
            },
            "ceiling": {
                "ceiling_samples": ceil_count,
                "ceiling_rate": ceil_count / N,
            },
            "models": {
                "variant": {
                    "hit1": var_h1,
                    "hit3": var_h3,
                    "pooled_top1": var_h1 / N,
                    "pooled_top3": var_h3 / N,
                    "wilson95_top1": list(wilson_interval(var_h1, N)),
                    "wilson95_top3": list(wilson_interval(var_h3, N)),
                    "fold_mean_top1": fold_mean_var_h1,
                    "fold_mean_top3": fold_mean_var_h3,
                },
                "frequency": {
                    "hit1": freq_h1,
                    "hit3": freq_h3,
                    "pooled_top1": freq_h1 / N,
                    "pooled_top3": freq_h3 / N,
                    "wilson95_top1": list(wilson_interval(freq_h1, N)),
                    "wilson95_top3": list(wilson_interval(freq_h3, N)),
                    "fold_mean_top1": fold_mean_freq_h1,
                    "fold_mean_top3": fold_mean_freq_h3,
                },
                "markov": {
                    "hit1": markov_h1,
                    "hit3": markov_h3,
                    "pooled_top1": markov_h1 / N,
                    "pooled_top3": markov_h3 / N,
                    "wilson95_top1": list(wilson_interval(markov_h1, N)),
                    "wilson95_top3": list(wilson_interval(markov_h3, N)),
                    "fold_mean_top1": fold_mean_markov_h1,
                    "fold_mean_top3": fold_mean_markov_h3,
                },
            },
            "mcnemar_vs_frequency": {
                "top1": {"b": b_h1, "c": c_h1, "p_value": p_mcnemar_h1},
                "top3": {"b": b_h3, "c": c_h3, "p_value": p_mcnemar_h3},
            },
            "tie_sensitivity": {
                "tied_samples_top1": tied_samples_top1,
                "tied_samples_top3": tied_samples_top3,
                "top1": {
                    "observed": var_h1,
                    "observed_rate": var_h1 / N,
                    "expected": round(exp_h1_sum, 6),
                    "expected_rate": exp_h1_sum / N,
                    "best": best_h1_sum,
                    "best_rate": best_h1_sum / N,
                    "worst": worst_h1_sum,
                    "worst_rate": worst_h1_sum / N,
                    "fold_mean_observed": fold_mean_var_h1,
                    "fold_mean_expected": fold_mean_exp_h1,
                    "fold_mean_best": fold_mean_best_h1,
                    "fold_mean_worst": fold_mean_worst_h1,
                },
                "top3": {
                    "observed": var_h3,
                    "observed_rate": var_h3 / N,
                    "expected": round(exp_h3_sum, 6),
                    "expected_rate": exp_h3_sum / N,
                    "best": best_h3_sum,
                    "best_rate": best_h3_sum / N,
                    "worst": worst_h3_sum,
                    "worst_rate": worst_h3_sum / N,
                    "fold_mean_observed": fold_mean_var_h3,
                    "fold_mean_expected": fold_mean_exp_h3,
                    "fold_mean_best": fold_mean_best_h3,
                    "fold_mean_worst": fold_mean_worst_h3,
                },
            },
            "per_fold": per_fold,
        }

        results_data["runs"][run_id] = run_summary

    # Write predictions CSV
    fieldnames = [
        "sample_id", "slice", "test_episode", "input_history", "target_set",
        "current_tactic_set", "tactic_markov_status", "predicted_candidates_top3",
        "variant_hit1", "variant_hit3", "frequency_hit1", "frequency_hit3",
        "markov_hit1", "markov_hit3", "top1_tied", "top3_boundary_tied",
        "top1_expected_hit", "top3_expected_hit", "top1_best_hit", "top3_best_hit",
        "top1_worst_hit", "top3_worst_hit",
    ]
    with open(OUT_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Saved predictions CSV to {OUT_CSV_PATH}")

    # Write results JSON
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)
    print(f"Saved results JSON to {OUT_JSON_PATH}")

    # Render Markdown Report
    render_markdown_report(results_data)
    print(f"Saved Markdown report to {OUT_MD_PATH}")

    return results_data


def render_markdown_report(data: dict[str, Any]) -> None:
    r7 = data["runs"]["7ep"]
    re5 = data["runs"]["e5_removed"]

    lines: list[str] = [
        "# Exploratory Tactic-Conditioned Technique Prediction Report",
        "",
        "> [!IMPORTANT]",
        "> **EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT**",
        "> This variant was pre-declared under Amendment 7 (2026-10-15) as an exploratory post hoc investigation of whether tactic-level order signal can transfer to technique prediction. It is not part of the pre-registered Holm step-down hypothesis testing family. The pre-registered primary evaluation verdict (\"improvement over baseline not demonstrated\") is finalized and cannot be modified or overturned by this exploratory variant.",
        "",
        "## 1. Setup and Methodology",
        "",
        "- **Motivation**: Cross-episode diagnostics (`reports/7ep/diagnostics_7ep.md`) demonstrated cross-episode state sparsity (`F3_unseen_states_and_miss_shares.collapsed_full.pooled.unseen_current_state_rate` = 35.79%, 34/95 unseen current states), while permutation tests (`reports/7ep/permutation_7ep_report.md`) demonstrated statistically significant order signal at the tactic level ($p = 0.0430$ Hit@1, $p = 0.0060$ Hit@3 under S1; Holm-adjusted $p = 0.0180$). (Note: the claim of \"zero repeat transitions between different attack campaigns\" is withdrawn per Amendment 8 as no such statistic exists in `diagnostics_7ep.json`).",
        "- **Architecture**: Current techniques are mapped to current tactics; a LOEO fold tactic-level Markov model predicts next tactics; techniques mapping to those tactics in rank order are sorted by training target frequency and de-duplicated. If unseen state or empty, the model falls back to the fold Frequency baseline list.",
        "- **Scope**: Evaluated on primary slice `collapsed_full` ($N=95$ across 7 episodes; $N=93$ under E5-removed sensitivity).",
        "",
        "## 2. 7-Episode LOEO Results (Primary Slice: `collapsed_full`, N=95)",
        "",
        f"- **Coverage**: {r7['coverage']['covered_samples']}/{r7['n_samples']} ({r7['coverage']['coverage_rate']*100:.2f}%) samples had tactic Markov status `ok`.",
        f"- **Ceiling**: {r7['ceiling']['ceiling_samples']}/{r7['n_samples']} ({r7['ceiling']['ceiling_rate']*100:.2f}%) samples had at least one target technique seen in training.",
        "",
        "### Headline Performance Comparison",
        "",
        "| Model | H@1 | H@3 | Top-1 Pooled | Wilson 95% Top-1 | Top-3 Pooled | Wilson 95% Top-3 | Fold-Mean Top-1 | Fold-Mean Top-3 |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]

    for m_key, m_lbl in [
        ("variant", "Exploratory Variant (Tactic-Conditioned)"),
        ("frequency", "Frequency Baseline"),
        ("markov", "Markov Model (Technique)"),
    ]:
        m = r7["models"][m_key]
        w1 = f"[{m['wilson95_top1'][0]*100:.2f}%, {m['wilson95_top1'][1]*100:.2f}%]"
        w3 = f"[{m['wilson95_top3'][0]*100:.2f}%, {m['wilson95_top3'][1]*100:.2f}%]"
        lines.append(
            f"| {m_lbl} | {m['hit1']} | {m['hit3']} | {m['pooled_top1']*100:.2f}% | {w1} | "
            f"{m['pooled_top3']*100:.2f}% | {w3} | {m['fold_mean_top1']*100:.2f}% | {m['fold_mean_top3']*100:.2f}% |"
        )

    lines.extend([
        "",
        "### Paired Exact McNemar Test (Variant vs Frequency Baseline)",
        "",
        f"- **Top-1**: Variant hits and Frequency misses ($b={r7['mcnemar_vs_frequency']['top1']['b']}$); Frequency hits and Variant misses ($c={r7['mcnemar_vs_frequency']['top1']['c']}$); Exact McNemar $p = {r7['mcnemar_vs_frequency']['top1']['p_value']:.4f}$ (descriptive, raw p).",
        f"- **Top-3**: Variant hits and Frequency misses ($b={r7['mcnemar_vs_frequency']['top3']['b']}$); Frequency hits and Variant misses ($c={r7['mcnemar_vs_frequency']['top3']['c']}$); Exact McNemar $p = {r7['mcnemar_vs_frequency']['top3']['p_value']:.4f}$ (descriptive, raw p).",
        "",
        "## 3. Tie-Sensitivity Diagnostic (P2 Machinery)",
        "",
        f"- **Tied Samples**: {r7['tie_sensitivity']['tied_samples_top1']}/{r7['n_samples']} samples tied at Top-1 boundary; {r7['tie_sensitivity']['tied_samples_top3']}/{r7['n_samples']} samples tied at Top-3 boundary.",
        "",
        "| Metric | Observed Hits (Rate) | Expected Hits (Rate) | Best-Case Hits (Rate) | Worst-Case Hits (Rate) | Fold-Mean (Obs / Exp / Best / Worst) |",
        "|:---|:---:|:---:|:---:|:---:|:---:|",
    ])

    for k_val in ["top1", "top3"]:
        ts = r7["tie_sensitivity"][k_val]
        obs_str = f"{ts['observed']} ({ts['observed_rate']*100:.2f}%)"
        exp_str = f"{ts['expected']:.2f} ({ts['expected_rate']*100:.2f}%)"
        best_str = f"{ts['best']} ({ts['best_rate']*100:.2f}%)"
        worst_str = f"{ts['worst']} ({ts['worst_rate']*100:.2f}%)"
        fm_str = f"{ts['fold_mean_observed']*100:.2f}% / {ts['fold_mean_expected']*100:.2f}% / {ts['fold_mean_best']*100:.2f}% / {ts['fold_mean_worst']*100:.2f}%"
        lines.append(f"| Hit@{k_val[-1]} | {obs_str} | {exp_str} | {best_str} | {worst_str} | {fm_str} |")

    lines.extend([
        "",
        "## 4. E5-Removed Sensitivity Slice Repeat (N=93)",
        "",
        f"- **Coverage**: {re5['coverage']['covered_samples']}/{re5['n_samples']} ({re5['coverage']['coverage_rate']*100:.2f}%).",
        f"- **Ceiling**: {re5['ceiling']['ceiling_samples']}/{re5['n_samples']} ({re5['ceiling']['ceiling_rate']*100:.2f}%).",
        "",
        "| Model | H@1 | H@3 | Top-1 Pooled | Top-3 Pooled | Fold-Mean Top-1 | Fold-Mean Top-3 |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for m_key, m_lbl in [
        ("variant", "Exploratory Variant (Tactic-Conditioned)"),
        ("frequency", "Frequency Baseline"),
        ("markov", "Markov Model (Technique)"),
    ]:
        m = re5["models"][m_key]
        lines.append(
            f"| {m_lbl} | {m['hit1']} | {m['hit3']} | {m['pooled_top1']*100:.2f}% | "
            f"{m['pooled_top3']*100:.2f}% | {m['fold_mean_top1']*100:.2f}% | {m['fold_mean_top3']*100:.2f}% |"
        )

    lines.extend([
        "",
        f"- **McNemar vs Frequency (E5-Removed)**: Top-1 $p = {re5['mcnemar_vs_frequency']['top1']['p_value']:.4f}$; Top-3 $p = {re5['mcnemar_vs_frequency']['top3']['p_value']:.4f}$ (descriptive, raw p).",
        "",
        "## 5. Summary and Registration Integrity Verdict",
        "",
        f"- **Findings**: The exploratory tactic-conditioned variant achieved Hit@1 = {r7['models']['variant']['hit1']}/{r7['n_samples']} ({r7['models']['variant']['pooled_top1']*100:.2f}%) and Hit@3 = {r7['models']['variant']['hit3']}/{r7['n_samples']} ({r7['models']['variant']['pooled_top3']*100:.2f}%). While this numerically exceeds the technique-level Markov model ({r7['models']['markov']['hit1']}/{r7['n_samples']} Hit@1, {r7['models']['markov']['hit3']}/{r7['n_samples']} Hit@3), it does not exceed the unconditional Frequency baseline ({r7['models']['frequency']['hit1']}/{r7['n_samples']} Hit@1, {r7['models']['frequency']['hit3']}/{r7['n_samples']} Hit@3).",
        "- **Status**: The pre-registered primary evaluation verdict (\"improvement over baseline not demonstrated\") is finalized and cannot be modified or overturned by this exploratory variant.",
        "",
    ])

    OUT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    if "--md-only" in sys.argv:
        with open(OUT_JSON_PATH, "r", encoding="utf-8") as f:
            res_data = json.load(f)
        render_markdown_report(res_data)
        print(f"Regenerated Markdown report to {OUT_MD_PATH} (--md-only) [PASS]")
    else:
        run_exploratory_tactic_conditioned()

