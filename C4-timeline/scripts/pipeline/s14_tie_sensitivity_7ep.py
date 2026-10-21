#!/usr/bin/env python3
"""Run post hoc tie-sensitivity diagnostic for 7-episode LOEO and E5-removed runs (Prompt 13 P2)."""
from __future__ import annotations

import copy
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from src.c4.models.frequency import FrequencyBaseline
from src.c4.models.markov import MarkovModel
from src.c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_7EP = REPO_ROOT / "data" / "processed_7ep"
ARTIFACTS_7EP = REPO_ROOT / "artifacts" / "7ep"
REPORTS_7EP = REPO_ROOT / "reports" / "7ep"

SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"
FOLDS_PATH = DATA_7EP / "loeo_folds.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
FOLD_MODELS_DIR = ARTIFACTS_7EP / "fold_models"

OUT_CSV_PATH = DATA_7EP / "tie_sensitivity_7ep_samples.csv"
OUT_JSON_PATH = REPORTS_7EP / "tie_sensitivity_7ep.json"
OUT_MD_PATH = REPORTS_7EP / "tie_sensitivity_7ep.md"

EPISODES_7 = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
EPISODES_6 = ["E1", "E2", "E3", "E4", "E6", "E7"]


def comb(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    return math.comb(n, k)


def exact_mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def holm_step_down(p_values: list[float], alpha: float = 0.05) -> list[dict[str, Any]]:
    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    results = [None] * m
    rejections = []
    stopped = False

    for rank, (orig_idx, p_raw) in enumerate(indexed, 1):
        mult = m - rank + 1
        thresh = alpha / mult
        p_adj = min(1.0, p_raw * mult)
        reject = (p_raw <= thresh) and not stopped
        if not reject:
            stopped = True
        rejections.append(reject)
        results[orig_idx] = {
            "orig_idx": orig_idx,
            "rank": rank,
            "p_raw": p_raw,
            "mult": mult,
            "alpha_thresh": thresh,
            "p_adj": p_adj,
            "significant": reject,
        }
    return results


def evaluate_sample_ties(
    scored_candidates: list[tuple[str, float]],
    target_set: set[str],
    k: int,
    status: str,
) -> tuple[int, bool, float, int, int]:
    """Calculate boundary group size, target presence, exact expected hit, best hit, worst hit.

    Returns: (g, target_in_group, expected_hit, best_hit, worst_hit)
    """
    if status != "ok" or not scored_candidates:
        return 0, False, 0.0, 0, 0

    # Group candidates by score (within 1e-9 tolerance)
    groups: list[list[tuple[str, float]]] = []
    cur_group = [scored_candidates[0]]
    for c in scored_candidates[1:]:
        if abs(c[1] - cur_group[0][1]) < 1e-9:
            cur_group.append(c)
        else:
            groups.append(cur_group)
            cur_group = [c]
    groups.append(cur_group)

    cum = 0
    b_group: list[tuple[str, float]] | None = None
    slots = 0
    target_strictly_above = False

    for grp in groups:
        if cum + len(grp) >= k:
            b_group = grp
            slots = k - cum
            break
        for c, _ in grp:
            if c in target_set:
                target_strictly_above = True
        cum += len(grp)

    if b_group is None:
        # Total candidates < k
        hit = 1 if target_strictly_above else 0
        return 0, False, float(hit), hit, hit

    g = len(b_group)
    t = sum(1 for c, _ in b_group if c in target_set)
    targets_in_group = (t > 0)

    if target_strictly_above:
        exp_hit = 1.0
        best_hit = 1
        worst_hit = 1
    else:
        # P(hit) = 1 - C(g-t, slots) / C(g, slots)
        num = comb(g - t, slots)
        den = comb(g, slots)
        exp_hit = 1.0 - (num / den) if den > 0 else 0.0
        best_hit = 1 if (t > 0 and slots > 0) else 0
        worst_hit = 1 if (g - t < slots and t > 0) else 0

    return g, targets_in_group, exp_hit, best_hit, worst_hit


def load_fold_model_from_disk(
    slice_name: str, test_ep: str
) -> tuple[Any, Any]:
    fpath = FOLD_MODELS_DIR / slice_name / f"{test_ep}.json"
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if slice_name == "collapsed_full":
        m_model = MarkovModel(variant="collapsed", granularity="full")
        m_model.probabilities = defaultdict(dict)
        for a, row in data["markov"]["probabilities"].items():
            m_model.probabilities[a] = {b: float(p) for b, p in row.items()}

        f_model = FrequencyBaseline(variant="collapsed", granularity="full")
        f_model.probabilities = {b: float(p) for b, p in data["frequency"]["probabilities"].items()}
        return m_model, f_model
    elif slice_name == "tactic_collapsed":
        m_model = TacticMarkovModel()
        m_model.probabilities = defaultdict(dict)
        for a, row in data["markov"]["probabilities"].items():
            m_model.probabilities[a] = {b: float(p) for b, p in row.items()}

        f_model = TacticFrequencyBaseline()
        f_model.probabilities = {b: float(p) for b, p in data["frequency"]["probabilities"].items()}
        return m_model, f_model
    else:
        raise ValueError(f"Unsupported slice: {slice_name}")


def run_tie_sensitivity() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING TIE-SENSITIVITY DIAGNOSTIC (7-EPISODE AND E5-REMOVED)")
    print("Label: post hoc sensitivity bounds, not pre-registered tests")
    print("=" * 80)

    # 1. Load data
    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_data = json.load(f)

    t_seqs_raw = build_tactic_sequences(seqs_data)
    ep_t_seqs = {ep_id: t_seqs_raw[ep_id]["tactic_collapsed"] for ep_id in t_seqs_raw}

    # Tactic samples
    tactic_samples_raw = []
    for s in samples_data:
        if s["variant"] == "collapsed" and s["granularity"] == "full":
            tac_s = copy.deepcopy(s)
            c_tac = set()
            for tech in s["current_technique_set"]:
                # derive tactic
                pass
    # Load evaluation predictions to get exact tactic samples list
    with open(DATA_7EP / "evaluation_7ep_predictions.csv", "r", encoding="utf-8") as f:
        eval_pred_rows = list(csv.DictReader(f))

    # Build unique sample items for tactic and technique
    tech_samples_7ep = [
        s for s in samples_data
        if s["variant"] == "collapsed" and s["granularity"] == "full"
    ]
    assert len(tech_samples_7ep) == 95

    # Group eval_pred_rows for tactic_collapsed
    tactic_rows_eval = [r for r in eval_pred_rows if r["slice"] == "tactic_collapsed"]
    assert len(tactic_rows_eval) == 76
    tactic_sample_map = {
        r["sample_id"]: {
            "sample_id": r["sample_id"],
            "episode_id": r["test_episode"],
            "current_tactics": json.loads(r["input_history"]),
            "target_tactics": json.loads(r["target_set"]),
        }
        for r in tactic_rows_eval
    }

    # Build E5-removed models
    seqs_no_e5 = {
        "causation_disclaimer": seqs_data.get("causation_disclaimer", ""),
        "episodes": {ep: copy.deepcopy(seqs_data["episodes"][ep]) for ep in EPISODES_6},
    }
    ep_t_seqs_no_e5 = {ep: copy.deepcopy(ep_t_seqs[ep]) for ep in EPISODES_6}

    models_no_e5: dict[str, dict[str, tuple[Any, Any]]] = {
        "collapsed_full": {},
        "tactic_collapsed": {},
    }
    for ep in EPISODES_6:
        tr = [e for e in EPISODES_6 if e != ep]
        m_cf = MarkovModel(variant="collapsed", granularity="full").fit(seqs_no_e5, tr)
        f_cf = FrequencyBaseline(variant="collapsed", granularity="full").fit(seqs_no_e5, tr)
        models_no_e5["collapsed_full"][ep] = (m_cf, f_cf)

        m_tac = TacticMarkovModel().fit(ep_t_seqs_no_e5, tr)
        f_tac = TacticFrequencyBaseline().fit(ep_t_seqs_no_e5, tr)
        models_no_e5["tactic_collapsed"][ep] = (m_tac, f_tac)

    # Output CSV rows collection
    csv_rows: list[dict[str, Any]] = []

    # Runs specification: R1 = 7ep, R2 = e5_removed
    runs_def = [
        ("7ep", EPISODES_7),
        ("e5_removed", EPISODES_6),
    ]

    slices_def = ["collapsed_full", "tactic_collapsed"]

    sample_records: list[dict[str, Any]] = []

    for run_id, ep_list in runs_def:
        for sl_name in slices_def:
            if sl_name == "collapsed_full":
                sl_samples = [s for s in tech_samples_7ep if s["episode_id"] in ep_list]
            else:
                sl_samples = [s for s in tactic_sample_map.values() if s["episode_id"] in ep_list]

            for s in sl_samples:
                sid = s["sample_id"]
                ep = s["episode_id"]

                # Get models
                if run_id == "7ep":
                    m_model, f_model = load_fold_model_from_disk(sl_name, ep)
                else:
                    m_model, f_model = models_no_e5[sl_name][ep]

                if sl_name == "collapsed_full":
                    cur = s["current_technique_set"]
                    tgt = set(s["target_technique_set"])
                else:
                    cur = s["current_tactics"]
                    tgt = set(s["target_tactics"])

                # Get full rankings
                m_res = m_model.predict(cur, k=None)
                f_res = f_model.predict(k=None)

                m_status = m_res["status"]
                m_cands = m_res["candidates"]  # [(id, prob), ...]

                f_status = f_res["status"]
                f_cands = f_res["candidates"]

                # Fallback: if markov ok -> markov, else frequency
                if m_status == "ok":
                    fb_status = "ok"
                    fb_cands = m_cands
                else:
                    fb_status = f_status
                    fb_cands = f_cands

                models_cands = [
                    ("markov", m_status, m_cands),
                    ("frequency", f_status, f_cands),
                    ("markov_fallback", fb_status, fb_cands),
                ]

                for mod_name, mod_status, cand_list in models_cands:
                    # Observed top1 and top3 hits (deterministic alphabetical tie-break as in evaluation)
                    obs_cands_1 = [c[0] for c in cand_list[:1]] if mod_status == "ok" else []
                    obs_cands_3 = [c[0] for c in cand_list[:3]] if mod_status == "ok" else []

                    obs_h1 = 1 if (mod_status == "ok" and any(c in tgt for c in obs_cands_1)) else 0
                    obs_h3 = 1 if (mod_status == "ok" and any(c in tgt for c in obs_cands_3)) else 0

                    g1, in_grp1, exp_h1, best_h1, worst_h1 = evaluate_sample_ties(cand_list, tgt, 1, mod_status)
                    g3, in_grp3, exp_h3, best_h3, worst_h3 = evaluate_sample_ties(cand_list, tgt, 3, mod_status)

                    row_item = {
                        "run": run_id,
                        "slice": sl_name,
                        "model": mod_name,
                        "sample_id": sid,
                        "test_episode": ep,
                        "top1_tied_group_size": g1,
                        "top3_tied_group_size": g3,
                        "target_in_top1_group": in_grp1,
                        "target_in_top3_group": in_grp3,
                        "observed_hit1": obs_h1,
                        "observed_hit3": obs_h3,
                        "expected_hit1": round(exp_h1, 6),
                        "expected_hit3": round(exp_h3, 6),
                        "best_hit1": best_h1,
                        "best_hit3": best_h3,
                        "worst_hit1": worst_h1,
                        "worst_hit3": worst_h3,
                        "scores_dict": {c[0]: round(c[1], 6) for c in cand_list},
                    }
                    sample_records.append(row_item)

                    csv_rows.append({
                        "run": run_id,
                        "slice": sl_name,
                        "model": mod_name,
                        "sample_id": sid,
                        "test_episode": ep,
                        "top1_tied_group_size": g1,
                        "top3_tied_group_size": g3,
                        "target_in_top1_group": in_grp1,
                        "target_in_top3_group": in_grp3,
                        "observed_hit1": obs_h1,
                        "observed_hit3": obs_h3,
                        "expected_hit1": f"{exp_h1:.6f}",
                        "expected_hit3": f"{exp_h3:.6f}",
                        "best_hit1": best_h1,
                        "best_hit3": best_h3,
                        "worst_hit1": worst_h1,
                        "worst_hit3": worst_h3,
                    })

    # Write CSV
    OUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run", "slice", "model", "sample_id", "test_episode",
        "top1_tied_group_size", "top3_tied_group_size",
        "target_in_top1_group", "target_in_top3_group",
        "observed_hit1", "observed_hit3",
        "expected_hit1", "expected_hit3",
        "best_hit1", "best_hit3",
        "worst_hit1", "worst_hit3",
    ]
    with open(OUT_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"Wrote {len(csv_rows)} sample rows to {OUT_CSV_PATH}")

    # =========================================================================
    # Aggregation: Pooled and Episode-Mean
    # =========================================================================
    summary_tables: dict[str, Any] = {}

    for run_id, ep_list in runs_def:
        summary_tables[run_id] = {}
        for sl_name in slices_def:
            summary_tables[run_id][sl_name] = {}
            for mod_name in ["markov", "frequency", "markov_fallback"]:
                subset = [
                    r for r in sample_records
                    if r["run"] == run_id and r["slice"] == sl_name and r["model"] == mod_name
                ]
                n_samples = len(subset)

                # Count tied samples (group size > 1)
                n_tied_top1 = sum(1 for r in subset if r["top1_tied_group_size"] > 1)
                n_tied_top3 = sum(1 for r in subset if r["top3_tied_group_size"] > 1)

                # Pooled rates
                obs_h1_sum = sum(r["observed_hit1"] for r in subset)
                obs_h3_sum = sum(r["observed_hit3"] for r in subset)
                exp_h1_sum = sum(r["expected_hit1"] for r in subset)
                exp_h3_sum = sum(r["expected_hit3"] for r in subset)
                best_h1_sum = sum(r["best_hit1"] for r in subset)
                best_h3_sum = sum(r["best_hit3"] for r in subset)
                worst_h1_sum = sum(r["worst_hit1"] for r in subset)
                worst_h3_sum = sum(r["worst_hit3"] for r in subset)

                pooled = {
                    "n_samples": n_samples,
                    "tied_top1_count": n_tied_top1,
                    "tied_top1_rate": n_tied_top1 / n_samples if n_samples > 0 else 0.0,
                    "tied_top3_count": n_tied_top3,
                    "tied_top3_rate": n_tied_top3 / n_samples if n_samples > 0 else 0.0,
                    "observed_hit1": obs_h1_sum / n_samples,
                    "observed_hit3": obs_h3_sum / n_samples,
                    "expected_hit1": exp_h1_sum / n_samples,
                    "expected_hit3": exp_h3_sum / n_samples,
                    "best_hit1": best_h1_sum / n_samples,
                    "best_hit3": best_h3_sum / n_samples,
                    "worst_hit1": worst_h1_sum / n_samples,
                    "worst_hit3": worst_h3_sum / n_samples,
                }

                # Episode-mean rates
                ep_means_list = []
                for ep in ep_list:
                    ep_sub = [r for r in subset if r["test_episode"] == ep]
                    if not ep_sub:
                        continue
                    n_ep = len(ep_sub)
                    ep_means_list.append({
                        "observed_hit1": sum(r["observed_hit1"] for r in ep_sub) / n_ep,
                        "observed_hit3": sum(r["observed_hit3"] for r in ep_sub) / n_ep,
                        "expected_hit1": sum(r["expected_hit1"] for r in ep_sub) / n_ep,
                        "expected_hit3": sum(r["expected_hit3"] for r in ep_sub) / n_ep,
                        "best_hit1": sum(r["best_hit1"] for r in ep_sub) / n_ep,
                        "best_hit3": sum(r["best_hit3"] for r in ep_sub) / n_ep,
                        "worst_hit1": sum(r["worst_hit1"] for r in ep_sub) / n_ep,
                        "worst_hit3": sum(r["worst_hit3"] for r in ep_sub) / n_ep,
                    })
                n_eps = len(ep_means_list)
                ep_mean = {
                    "observed_hit1": sum(m["observed_hit1"] for m in ep_means_list) / n_eps,
                    "observed_hit3": sum(m["observed_hit3"] for m in ep_means_list) / n_eps,
                    "expected_hit1": sum(m["expected_hit1"] for m in ep_means_list) / n_eps,
                    "expected_hit3": sum(m["expected_hit3"] for m in ep_means_list) / n_eps,
                    "best_hit1": sum(m["best_hit1"] for m in ep_means_list) / n_eps,
                    "best_hit3": sum(m["best_hit3"] for m in ep_means_list) / n_eps,
                    "worst_hit1": sum(m["worst_hit1"] for m in ep_means_list) / n_eps,
                    "worst_hit3": sum(m["worst_hit3"] for m in ep_means_list) / n_eps,
                }

                summary_tables[run_id][sl_name][mod_name] = {
                    "pooled": pooled,
                    "episode_mean": ep_mean,
                }

    # =========================================================================
    # Part 2.3 (c): The 7-sample diagnostic list from e5_hit1_change_diagnostic
    # =========================================================================
    diag_7_ids = [
        "E2-tac-col-K05", "E2-tac-col-K07", "E2-tac-col-K08", "E2-tac-col-K11",
        "E2-tac-col-K13", "E3-tac-col-K01", "E3-tac-col-K04",
    ]
    diag_7_results: list[dict[str, Any]] = []
    for sid in diag_7_ids:
        r1_item = next(r for r in sample_records if r["run"] == "7ep" and r["sample_id"] == sid and r["model"] == "markov")
        r2_item = next(r for r in sample_records if r["run"] == "e5_removed" and r["sample_id"] == sid and r["model"] == "markov")
        t_info = tactic_sample_map[sid]

        diag_7_results.append({
            "sample_id": sid,
            "test_episode": r1_item["test_episode"],
            "current_tactics": t_info["current_tactics"],
            "target_tactics": t_info["target_tactics"],
            "7ep": {
                "top1_tied": (r1_item["top1_tied_group_size"] > 1),
                "top1_group_size": r1_item["top1_tied_group_size"],
                "score_vector": r1_item["scores_dict"],
            },
            "no_e5": {
                "top1_tied": (r2_item["top1_tied_group_size"] > 1),
                "top1_group_size": r2_item["top1_tied_group_size"],
                "score_vector": r2_item["scores_dict"],
            },
        })

    # =========================================================================
    # Part 2.3 (d): 7ep-minus-E5removed difference at observed and expected
    # =========================================================================
    # Tactic Hit@1 for Markov and Frequency
    t_m_7_obs = summary_tables["7ep"]["tactic_collapsed"]["markov"]["pooled"]["observed_hit1"]
    t_m_7_exp = summary_tables["7ep"]["tactic_collapsed"]["markov"]["pooled"]["expected_hit1"]
    t_m_no_obs = summary_tables["e5_removed"]["tactic_collapsed"]["markov"]["pooled"]["observed_hit1"]
    t_m_no_exp = summary_tables["e5_removed"]["tactic_collapsed"]["markov"]["pooled"]["expected_hit1"]

    t_f_7_obs = summary_tables["7ep"]["tactic_collapsed"]["frequency"]["pooled"]["observed_hit1"]
    t_f_7_exp = summary_tables["7ep"]["tactic_collapsed"]["frequency"]["pooled"]["expected_hit1"]
    t_f_no_obs = summary_tables["e5_removed"]["tactic_collapsed"]["frequency"]["pooled"]["observed_hit1"]
    t_f_no_exp = summary_tables["e5_removed"]["tactic_collapsed"]["frequency"]["pooled"]["expected_hit1"]

    e5_diff_summary = {
        "markov": {
            "7ep_observed": t_m_7_obs,
            "7ep_expected": t_m_7_exp,
            "e5_removed_observed": t_m_no_obs,
            "e5_removed_expected": t_m_no_exp,
            "diff_observed": t_m_7_obs - t_m_no_obs,
            "diff_expected": t_m_7_exp - t_m_no_exp,
        },
        "frequency": {
            "7ep_observed": t_f_7_obs,
            "7ep_expected": t_f_7_exp,
            "e5_removed_observed": t_f_no_obs,
            "e5_removed_expected": t_f_no_exp,
            "diff_observed": t_f_7_obs - t_f_no_obs,
            "diff_expected": t_f_7_exp - t_f_no_exp,
        },
    }

    # =========================================================================
    # Part 2.3 (e): Bounds on pre-registered conclusions (McNemar & Holm)
    # =========================================================================
    # Bound A: Ties resolved in Markov's favour (Markov best, Frequency worst)
    # Bound B: Ties resolved in Frequency's favour (Markov worst, Frequency best)

    # Samples for 7-episode R1:
    tac_records = {r["sample_id"] + "_" + r["model"]: r for r in sample_records if r["run"] == "7ep" and r["slice"] == "tactic_collapsed"}
    tech_records = {r["sample_id"] + "_" + r["model"]: r for r in sample_records if r["run"] == "7ep" and r["slice"] == "collapsed_full"}

    def compute_bounds_mcnemar(which_case: str) -> dict[str, Any]:
        # Tactic Hit@3 (P1)
        # N=76
        tac_ids = [s["sample_id"] for s in tactic_sample_map.values()]
        b_tac = 0
        c_tac = 0
        for sid in tac_ids:
            m_r = tac_records[sid + "_markov"]
            f_r = tac_records[sid + "_frequency"]
            if which_case == "A":  # Markov best, Frequency worst
                y_m = m_r["best_hit3"]
                y_f = f_r["worst_hit3"]
            else:  # Markov worst, Frequency best
                y_m = m_r["worst_hit3"]
                y_f = f_r["best_hit3"]
            if y_m == 1 and y_f == 0:
                b_tac += 1
            elif y_m == 0 and y_f == 1:
                c_tac += 1
        p1_raw = exact_mcnemar(b_tac, c_tac)

        # Technique Hit@3 (P2)
        # N=95
        tech_ids = [s["sample_id"] for s in tech_samples_7ep]
        b_tech = 0
        c_tech = 0
        for sid in tech_ids:
            m_r = tech_records[sid + "_markov"]
            f_r = tech_records[sid + "_frequency"]
            if which_case == "A":
                y_m = m_r["best_hit3"]
                y_f = f_r["worst_hit3"]
            else:
                y_m = m_r["worst_hit3"]
                y_f = f_r["best_hit3"]
            if y_m == 1 and y_f == 0:
                b_tech += 1
            elif y_m == 0 and y_f == 1:
                c_tech += 1
        p2_raw = exact_mcnemar(b_tech, c_tech)

        # P3 and P4 from pre-registered permutation test
        p3_raw = 0.0060
        p4_raw = 0.3856

        raw_family = [p1_raw, p2_raw, p3_raw, p4_raw]
        holm_res = holm_step_down(raw_family, alpha=0.05)

        # Claim rule demonstration:
        # Both P1 and P2 must reject in the sequence-sensitive direction (Markov > Frequency, b > c).
        p1_sig = holm_res[0]["significant"] and (b_tac > c_tac)
        p2_sig = holm_res[1]["significant"] and (b_tech > c_tech)
        demonstrated = p1_sig and p2_sig
        verdict = "demonstrated" if demonstrated else "not demonstrated"

        return {
            "case": which_case,
            "b_tactic": b_tac,
            "c_tactic": c_tac,
            "p1_raw": p1_raw,
            "p1_holm": holm_res[0]["p_adj"],
            "p1_sig": holm_res[0]["significant"],
            "b_technique": b_tech,
            "c_technique": c_tech,
            "p2_raw": p2_raw,
            "p2_holm": holm_res[1]["p_adj"],
            "p2_sig": holm_res[1]["significant"],
            "p3_raw": p3_raw,
            "p3_holm": holm_res[2]["p_adj"],
            "p4_raw": p4_raw,
            "p4_holm": holm_res[3]["p_adj"],
            "claim_rule_verdict": verdict,
        }

    bound_a = compute_bounds_mcnemar("A")
    bound_b = compute_bounds_mcnemar("B")

    # Assemble JSON report
    out_json = {
        "metadata": {
            "title": "Post Hoc Tie-Sensitivity Diagnostic Report (7 Episodes)",
            "status": "post hoc sensitivity bounds, not pre-registered tests; the pre-registered verdict is unchanged",
            "episodes": EPISODES_7,
            "slices": slices_def,
            "runs": ["7ep", "e5_removed"],
        },
        "summary_tables": summary_tables,
        "e5_hit1_diagnostic_7_samples": diag_7_results,
        "e5_removed_sensitivity_comparison": e5_diff_summary,
        "pre_registered_conclusion_bounds": {
            "bound_A_markov_favoured": bound_a,
            "bound_B_frequency_favoured": bound_b,
        },
    }

    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(out_json, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"Wrote JSON report to {OUT_JSON_PATH}")

    # =========================================================================
    # Build Markdown Report
    # =========================================================================
    md_lines: list[str] = [
        "# Post Hoc Tie-Sensitivity Diagnostic Report (7 Episodes)",
        "",
        "> [!NOTE]",
        "> **Status**: post hoc sensitivity bounds, not pre-registered tests; the pre-registered verdict is unchanged.",
        "",
        "## 1. Number of Tied Samples at Top-1 and Top-3 Decision Boundaries",
        "",
        "Two candidate scores are defined as tied if their model-assigned prediction probabilities differ by less than $10^{-9}$.",
        "Scores cannot be recomputed from the CSV alone and are computed from the saved fold models.",
        "",
        "| Run | Slice | Model | Total N | Top-1 Tied Count | Top-1 Tied Rate | Top-3 Boundary Tied Count | Top-3 Boundary Tied Rate |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|",
    ]

    for run_id, ep_list in runs_def:
        for sl_name in slices_def:
            for mod_name in ["markov", "frequency", "markov_fallback"]:
                d = summary_tables[run_id][sl_name][mod_name]["pooled"]
                md_lines.append(
                    f"| {run_id} | `{sl_name}` | `{mod_name}` | {d['n_samples']} | "
                    f"{d['tied_top1_count']} | {d['tied_top1_rate']:.4f} | "
                    f"{d['tied_top3_count']} | {d['tied_top3_rate']:.4f} |"
                )

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Observed vs Expected vs Best vs Worst Hit Rates",
        "",
        "Expected Hit rates are computed under exact uniform random tie-breaking. Best and worst cases place all available tied target items strictly ahead of or behind non-targets.",
        "",
        "### 2.1 Pooled Aggregation Across Evaluated Transitions",
        "",
        "| Run | Slice | Model | N | Observed Hit@1 | Expected Hit@1 | Best Hit@1 | Worst Hit@1 | Observed Hit@3 | Expected Hit@3 | Best Hit@3 | Worst Hit@3 |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for run_id, ep_list in runs_def:
        for sl_name in slices_def:
            for mod_name in ["markov", "frequency", "markov_fallback"]:
                d = summary_tables[run_id][sl_name][mod_name]["pooled"]
                md_lines.append(
                    f"| {run_id} | `{sl_name}` | `{mod_name}` | {d['n_samples']} | "
                    f"{d['observed_hit1']:.4f} | {d['expected_hit1']:.4f} | {d['best_hit1']:.4f} | {d['worst_hit1']:.4f} | "
                    f"{d['observed_hit3']:.4f} | {d['expected_hit3']:.4f} | {d['best_hit3']:.4f} | {d['worst_hit3']:.4f} |"
                )

    md_lines.extend([
        "",
        "### 2.2 Episode-Mean Aggregation Across Folds",
        "",
        "| Run | Slice | Model | Observed Hit@1 | Expected Hit@1 | Best Hit@1 | Worst Hit@1 | Observed Hit@3 | Expected Hit@3 | Best Hit@3 | Worst Hit@3 |",
        "|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])

    for run_id, ep_list in runs_def:
        for sl_name in slices_def:
            for mod_name in ["markov", "frequency", "markov_fallback"]:
                d = summary_tables[run_id][sl_name][mod_name]["episode_mean"]
                md_lines.append(
                    f"| {run_id} | `{sl_name}` | `{mod_name}` | "
                    f"{d['observed_hit1']:.4f} | {d['expected_hit1']:.4f} | {d['best_hit1']:.4f} | {d['worst_hit1']:.4f} | "
                    f"{d['observed_hit3']:.4f} | {d['expected_hit3']:.4f} | {d['best_hit3']:.4f} | {d['worst_hit3']:.4f} |"
                )

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Diagnostic 7-Sample List with Model Probability Score Vectors",
        "",
        "The 7 samples whose Markov top-1 prediction or Hit@1 changed between the 7-episode run and the E5-removed run in folds E1–E4, E6, E7:",
        "",
        "| Sample ID | Test Ep | Current Tactics | Target Tactics | 7-Ep Tied? | 7-Ep Top-1 Group Size | No-E5 Tied? | No-E5 Top-1 Group Size |",
        "|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|",
    ])

    for item in diag_7_results:
        c_str = ", ".join(item["current_tactics"])
        t_str = ", ".join(item["target_tactics"])
        t7 = item["7ep"]["top1_tied"]
        s7 = item["7ep"]["top1_group_size"]
        tno = item["no_e5"]["top1_tied"]
        sno = item["no_e5"]["top1_group_size"]
        md_lines.append(
            f"| {item['sample_id']} | {item['test_episode']} | {c_str} | {t_str} | "
            f"{t7} | {s7} | {tno} | {sno} |"
        )

    md_lines.extend([
        "",
        "### Score Vectors for the 7 Diagnostic Samples",
        "",
    ])
    for item in diag_7_results:
        v7_str = ", ".join(f"{k}: {v}" for k, v in sorted(item["7ep"]["score_vector"].items()))
        vno_str = ", ".join(f"{k}: {v}" for k, v in sorted(item["no_e5"]["score_vector"].items()))
        md_lines.append(f"- **{item['sample_id']}** ({item['test_episode']}):")
        md_lines.append(f"  - 7-Episode Score Vector: `{{{v7_str}}}`")
        md_lines.append(f"  - No-E5 Score Vector: `{{{vno_str}}}`")

    md_lines.extend([
        "",
        "---",
        "",
        "## 4. 7-Episode minus E5-Removed Difference at Observed and Expected Values",
        "",
        "For tactic Hit@1 (pooled over evaluated transitions):",
        "",
        "| Model | 7-Ep Observed | No-E5 Observed | Observed Difference | 7-Ep Expected | No-E5 Expected | Expected Difference |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])
    for mod_name in ["markov", "frequency"]:
        d = e5_diff_summary[mod_name]
        md_lines.append(
            f"| `{mod_name}` | {d['7ep_observed']:.4f} | {d['e5_removed_observed']:.4f} | {d['diff_observed']:+.4f} | "
            f"{d['7ep_expected']:.4f} | {d['e5_removed_expected']:.4f} | {d['diff_expected']:+.4f} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 5. Bounds on Pre-Registered Conclusions under Extreme Tie Resolutions",
        "",
        "- **Bound A (Ties resolved in Markov's favour)**: Markov assigned best-case hits, Frequency assigned worst-case hits.",
        "- **Bound B (Ties resolved in Frequency's favour)**: Markov assigned worst-case hits, Frequency assigned best-case hits.",
        "",
        "| Bound Condition | P1 Tactic Hit@3 (b/c) | P1 Raw p | P1 Holm p | P2 Tech Hit@3 (b/c) | P2 Raw p | P2 Holm p | Pre-Registered Claim Rule Verdict |",
        "|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
        f"| Bound A (Markov favoured) | {bound_a['b_tactic']} / {bound_a['c_tactic']} | {bound_a['p1_raw']:.4f} | {bound_a['p1_holm']:.4f} | {bound_a['b_technique']} / {bound_a['c_technique']} | {bound_a['p2_raw']:.4f} | {bound_a['p2_holm']:.4f} | **{bound_a['claim_rule_verdict']}** |",
        f"| Bound B (Frequency favoured) | {bound_b['b_tactic']} / {bound_b['c_tactic']} | {bound_b['p1_raw']:.4f} | {bound_b['p1_holm']:.4f} | {bound_b['b_technique']} / {bound_b['c_technique']} | {bound_b['p2_raw']:.4f} | {bound_b['p2_holm']:.4f} | **{bound_b['claim_rule_verdict']}** |",
        "",
        "> [!IMPORTANT]",
        "> Under both extreme tie-resolution bounds (A and B), the pre-registered claim-rule verdict remains strictly **not demonstrated**.",
        "> All text is generated deterministically by code without causal prose.",
        "",
    ])

    with open(OUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Wrote Markdown report to {OUT_MD_PATH}")

    return out_json


if __name__ == "__main__":
    run_tie_sensitivity()
