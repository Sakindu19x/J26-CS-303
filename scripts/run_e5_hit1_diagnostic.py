"""Diagnostic: Tactic Markov and Frequency Hit@1 changes when E5 is removed.

Diagnostic, not a pre-registered test.

Investigates why tactic Markov Hit@1 changes from 22/76 to 18/74 when E5 is removed:
Removing E5's two test samples accounts for at most 1 hit (from 22 to 21),
so at least 3 hits in other folds change due to E5's transitions being absent from training.

Evaluates every sample in E1-E4, E6, and E7 (N=74) under:
1. 7-Episode LOEO training set (trained on 6 episodes including E5)
2. E5-Removed LOEO training set (trained on 5 episodes excluding E5)

Identifies all samples where:
- Markov top-1 prediction or hit1 differs
- Frequency top-1 prediction or hit1 differs

Outputs:
- reports/7ep/e5_hit1_change_diagnostic.json
- reports/7ep/e5_hit1_change_diagnostic.md
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
)

DATA_7EP = BASE_DIR / "data" / "processed_7ep"
REPORTS_7EP = BASE_DIR / "reports" / "7ep"
SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"

JSON_OUT = REPORTS_7EP / "e5_hit1_change_diagnostic.json"
MD_OUT = REPORTS_7EP / "e5_hit1_change_diagnostic.md"

ALL_EPISODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
EVAL_EPISODES = ["E1", "E2", "E3", "E4", "E6", "E7"]


def check_candidates_tied(candidates: list[tuple[str, float]]) -> str:
    """Return 'yes' if multiple candidates share the maximum score, 'no' otherwise."""
    if not candidates:
        return "no"
    max_score = candidates[0][1]
    top_cands = [c for c, s in candidates if abs(s - max_score) < 1e-9]
    return "yes" if len(top_cands) > 1 else "no"


def format_counts_dict(counts_dict: dict[str, dict[str, float]], current_tactics: list[str]) -> dict[str, float]:
    """Format transition counts for the current tactic set into a flat dict."""
    if len(current_tactics) == 1:
        t = current_tactics[0]
        return {b: round(c, 4) for b, c in sorted(counts_dict.get(t, {}).items())}
    res = {}
    for t in current_tactics:
        for b, c in sorted(counts_dict.get(t, {}).items()):
            res[f"{t}->{b}"] = round(c, 4)
    return res


def run_e5_hit1_diagnostic() -> dict[str, Any]:
    print("================================================================================")
    print("RUNNING E5 HIT@1 CHANGE DIAGNOSTIC (TACTIC LEVEL)")
    print("diagnostic, not a pre-registered test")
    print("================================================================================")

    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)

    t_seqs = build_tactic_sequences(seqs_data)
    if "episodes" in t_seqs:
        t_seqs = t_seqs["episodes"]
    ep_t_seqs = {ep_id: t_seqs[ep_id]["tactic_collapsed"] for ep_id in t_seqs}

    # Build evaluation samples for E1-E4, E6, E7 (N=74)
    eval_samples: list[dict[str, Any]] = []
    for ep_id in EVAL_EPISODES:
        items = ep_t_seqs[ep_id]
        for idx in range(len(items) - 1):
            cur = tuple(items[idx]["tactics"])
            tgt = tuple(items[idx + 1]["tactics"])
            sid = f"{ep_id}-tac-col-K{idx + 1:02d}"
            eval_samples.append({
                "sample_id": sid,
                "episode_id": ep_id,
                "current_tactics": list(cur),
                "target_tactics": list(tgt),
                "current_tuple": cur,
                "target_tuple": tgt,
            })

    print(f"Total evaluation samples in E1-E4, E6, E7: {len(eval_samples)}")

    markov_diff_samples: list[dict[str, Any]] = []
    frequency_diff_samples: list[dict[str, Any]] = []

    markov_hits_7ep = 0
    markov_hits_no_e5 = 0
    frequency_hits_7ep = 0
    frequency_hits_no_e5 = 0

    # Fit models per held-out episode
    models_7ep: dict[str, tuple[TacticMarkovModel, TacticFrequencyBaseline]] = {}
    models_no_e5: dict[str, tuple[TacticMarkovModel, TacticFrequencyBaseline]] = {}

    for ep_id in EVAL_EPISODES:
        train_7ep = [e for e in ALL_EPISODES if e != ep_id]
        train_no_e5 = [e for e in EVAL_EPISODES if e != ep_id]

        m7 = TacticMarkovModel().fit(ep_t_seqs, train_7ep)
        f7 = TacticFrequencyBaseline().fit(ep_t_seqs, train_7ep)
        models_7ep[ep_id] = (m7, f7)

        m_no = TacticMarkovModel().fit(ep_t_seqs, train_no_e5)
        f_no = TacticFrequencyBaseline().fit(ep_t_seqs, train_no_e5)
        models_no_e5[ep_id] = (m_no, f_no)

    for s in eval_samples:
        ep = s["episode_id"]
        cur = s["current_tuple"]
        tgt_set = set(s["target_tuple"])

        m7, f7 = models_7ep[ep]
        m_no, f_no = models_no_e5[ep]

        # 1. Markov Evaluation
        res_m7 = m7.predict(cur, k=1)
        res_m_no = m_no.predict(cur, k=1)

        pred_m7 = res_m7["candidates"][0][0] if res_m7["status"] == "ok" and res_m7["candidates"] else None
        pred_m_no = res_m_no["candidates"][0][0] if res_m_no["status"] == "ok" and res_m_no["candidates"] else None

        hit_m7 = 1 if pred_m7 in tgt_set else 0
        hit_m_no = 1 if pred_m_no in tgt_set else 0

        markov_hits_7ep += hit_m7
        markov_hits_no_e5 += hit_m_no

        counts_m7 = format_counts_dict(m7.counts, s["current_tactics"])
        counts_m_no = format_counts_dict(m_no.counts, s["current_tactics"])

        tied_m7 = check_candidates_tied(res_m7.get("all_candidates", []))
        tied_m_no = check_candidates_tied(res_m_no.get("all_candidates", []))

        if pred_m7 != pred_m_no or hit_m7 != hit_m_no:
            markov_diff_samples.append({
                "sample_id": s["sample_id"],
                "episode_id": ep,
                "current_tactics": s["current_tactics"],
                "target_tactics": s["target_tactics"],
                "pred_7ep": pred_m7,
                "hit1_7ep": hit_m7,
                "pred_no_e5": pred_m_no,
                "hit1_no_e5": hit_m_no,
                "transition_counts_7ep": counts_m7,
                "tied_7ep": tied_m7,
                "transition_counts_no_e5": counts_m_no,
                "tied_no_e5": tied_m_no,
            })

        # 2. Frequency Evaluation
        res_f7 = f7.predict(k=1)
        res_f_no = f_no.predict(k=1)

        pred_f7 = res_f7["candidates"][0][0] if res_f7["candidates"] else None
        pred_f_no = res_f_no["candidates"][0][0] if res_f_no["candidates"] else None

        hit_f7 = 1 if pred_f7 in tgt_set else 0
        hit_f_no = 1 if pred_f_no in tgt_set else 0

        frequency_hits_7ep += hit_f7
        frequency_hits_no_e5 += hit_f_no

        counts_f7 = {k: round(v, 4) for k, v in sorted(f7.counts.items())}
        counts_f_no = {k: round(v, 4) for k, v in sorted(f_no.counts.items())}

        f7_cands = [(k, v) for k, v in sorted(f7.counts.items(), key=lambda x: (-x[1], x[0]))]
        f_no_cands = [(k, v) for k, v in sorted(f_no.counts.items(), key=lambda x: (-x[1], x[0]))]

        tied_f7 = check_candidates_tied(f7_cands)
        tied_f_no = check_candidates_tied(f_no_cands)

        if pred_f7 != pred_f_no or hit_f7 != hit_f_no:
            frequency_diff_samples.append({
                "sample_id": s["sample_id"],
                "episode_id": ep,
                "current_tactics": s["current_tactics"],
                "target_tactics": s["target_tactics"],
                "pred_7ep": pred_f7,
                "hit1_7ep": hit_f7,
                "pred_no_e5": pred_f_no,
                "hit1_no_e5": hit_f_no,
                "frequency_counts_7ep": counts_f7,
                "tied_7ep": tied_f7,
                "frequency_counts_no_e5": counts_f_no,
                "tied_no_e5": tied_f_no,
            })

    # Accounting for E5 test samples in 7-episode LOEO
    e5_items = ep_t_seqs["E5"]
    e5_markov_hits = 0
    train_for_e5 = [e for e in ALL_EPISODES if e != "E5"]
    m_e5 = TacticMarkovModel().fit(ep_t_seqs, train_for_e5)
    f_e5 = TacticFrequencyBaseline().fit(ep_t_seqs, train_for_e5)

    e5_f7 = f_e5.predict(k=1)
    e5_f_cand = e5_f7["candidates"][0][0] if e5_f7["candidates"] else None
    e5_freq_hits = 0

    for idx in range(len(e5_items) - 1):
        cur = tuple(e5_items[idx]["tactics"])
        tgt = set(e5_items[idx + 1]["tactics"])
        res = m_e5.predict(cur, k=1)
        pred = res["candidates"][0][0] if res["status"] == "ok" and res["candidates"] else None
        if pred in tgt:
            e5_markov_hits += 1
        if e5_f_cand in tgt:
            e5_freq_hits += 1

    print(f"Markov Hits across 6 evaluation episodes (N=74):")
    print(f"  7-Episode run:   {markov_hits_7ep} / 74 (plus E5 hits: {e5_markov_hits} / 2 -> Total {markov_hits_7ep + e5_markov_hits} / 76)")
    print(f"  E5-Removed run:  {markov_hits_no_e5} / 74")
    print(f"  Difference:      {markov_hits_no_e5 - markov_hits_7ep} hits across remaining folds")
    print(f"Differing Markov samples count: {len(markov_diff_samples)}")
    print(f"Differing Frequency samples count: {len(frequency_diff_samples)}")

    diagnostic_data: dict[str, Any] = {
        "metadata": {
            "label": "diagnostic, not a pre-registered test",
            "slice": "tactic_collapsed",
            "all_episodes": ALL_EPISODES,
            "evaluated_episodes": EVAL_EPISODES,
            "n_evaluation_samples": len(eval_samples),
            "n_e5_test_samples": len(e5_items) - 1,
            "summary_accounting": {
                "markov_total_hits_7ep": markov_hits_7ep + e5_markov_hits,
                "markov_total_samples_7ep": 76,
                "markov_e5_test_hits": e5_markov_hits,
                "markov_e5_test_samples": 2,
                "markov_hits_6ep_in_7ep_run": markov_hits_7ep,
                "markov_hits_6ep_in_e5_removed_run": markov_hits_no_e5,
                "markov_hits_difference_in_6ep": markov_hits_no_e5 - markov_hits_7ep,
                "frequency_total_hits_7ep": frequency_hits_7ep + e5_freq_hits,
                "frequency_total_samples_7ep": 76,
                "frequency_e5_test_hits": e5_freq_hits,
                "frequency_e5_test_samples": 2,
                "frequency_hits_6ep_in_7ep_run": frequency_hits_7ep,
                "frequency_hits_6ep_in_e5_removed_run": frequency_hits_no_e5,
                "frequency_hits_difference_in_6ep": frequency_hits_no_e5 - frequency_hits_7ep,
            },
        },
        "markov_differing_samples": markov_diff_samples,
        "frequency_differing_samples": frequency_diff_samples,
    }

    # Write JSON
    print(f"Writing diagnostic JSON to {JSON_OUT}...")
    with open(JSON_OUT, "w", encoding="utf-8") as f:
        json.dump(diagnostic_data, f, indent=2)

    # Generate Markdown
    print(f"Writing diagnostic Markdown to {MD_OUT}...")
    generate_diagnostic_markdown(diagnostic_data)

    print("Diagnostic completed successfully.")
    return diagnostic_data


def generate_diagnostic_markdown(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    meta = data["metadata"]
    acc = meta["summary_accounting"]
    m_diffs = data["markov_differing_samples"]
    f_diffs = data["frequency_differing_samples"]

    A("# E5-Removed Tactic Hit@1 Change Diagnostic")
    A()
    A("> [!NOTE]")
    A(f"> **Status**: {meta['label']}.")
    A()
    A("## 1. Accounting Summary")
    A()
    A(f"- **Tactic 7-Episode Baseline**: Markov Hit@1 is {acc['markov_total_hits_7ep']} / {acc['markov_total_samples_7ep']} ({acc['markov_total_hits_7ep'] / acc['markov_total_samples_7ep']:.4f}).")
    A(f"- **E5 Test Sample Performance in 7-Episode LOEO**: {acc['markov_e5_test_hits']} / {acc['markov_e5_test_samples']} hits.")
    A(f"- **Performance on Remaining Folds (E1–E4, E6, E7, N=74)**:")
    A(f"  - In 7-episode run (E5 in training pool): {acc['markov_hits_6ep_in_7ep_run']} / 74 hits ({acc['markov_hits_6ep_in_7ep_run'] / 74:.4f}).")
    A(f"  - In E5-removed run (E5 absent from training pool): {acc['markov_hits_6ep_in_e5_removed_run']} / 74 hits ({acc['markov_hits_6ep_in_e5_removed_run'] / 74:.4f}).")
    A(f"  - Net difference in other folds: {acc['markov_hits_difference_in_6ep']:+d} hits.")
    A(f"- **Frequency Baseline Comparison on Remaining Folds (N=74)**:")
    A(f"  - In 7-episode run: {acc['frequency_hits_6ep_in_7ep_run']} / 74 hits ({acc['frequency_hits_6ep_in_7ep_run'] / 74:.4f}).")
    A(f"  - In E5-removed run: {acc['frequency_hits_6ep_in_e5_removed_run']} / 74 hits ({acc['frequency_hits_6ep_in_e5_removed_run'] / 74:.4f}).")
    A(f"  - Net difference in Frequency hits: {acc['frequency_hits_difference_in_6ep']:+d} hits.")
    A()
    A("---")
    A()
    A("## 2. Markov Model Differing Samples")
    A()
    A(f"Total samples with differing Markov top-1 prediction or Hit@1: **{len(m_diffs)}**.")
    A()
    A("| Sample ID | Test Episode | Current Tactics | Target Tactics | 7-Ep Top-1 | 7-Ep Hit@1 | No-E5 Top-1 | No-E5 Hit@1 | 7-Ep Transition Counts | 7-Ep Tied | No-E5 Transition Counts | No-E5 Tied |")
    A("|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---|:---:|")

    for d in m_diffs:
        c_str = ", ".join(d["current_tactics"])
        t_str = ", ".join(d["target_tactics"])
        counts_7_str = ", ".join(f"{k}: {v}" for k, v in sorted(d["transition_counts_7ep"].items()))
        counts_no_str = ", ".join(f"{k}: {v}" for k, v in sorted(d["transition_counts_no_e5"].items()))
        A(
            f"| {d['sample_id']} | {d['episode_id']} | {c_str} | {t_str} | "
            f"{d['pred_7ep']} | {d['hit1_7ep']} | {d['pred_no_e5']} | {d['hit1_no_e5']} | "
            f"`{{{counts_7_str}}}` | tied counts: {d['tied_7ep']} | `{{{counts_no_str}}}` | tied counts: {d['tied_no_e5']} |"
        )

    A()
    A("---")
    A()
    A("## 3. Frequency Baseline Differing Samples")
    A()
    A(f"Total samples with differing Frequency top-1 prediction or Hit@1: **{len(f_diffs)}**.")
    A()
    if not f_diffs:
        A("No evaluation samples in folds E1–E4, E6, or E7 exhibited differing top-1 predictions or Hit@1 flags for the Frequency baseline between the 7-episode run and the E5-removed run.")
    else:
        A("| Sample ID | Test Episode | Current Tactics | Target Tactics | 7-Ep Top-1 | 7-Ep Hit@1 | No-E5 Top-1 | No-E5 Hit@1 | 7-Ep Tied | No-E5 Tied |")
        A("|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
        for d in f_diffs:
            c_str = ", ".join(d["current_tactics"])
            t_str = ", ".join(d["target_tactics"])
            A(
                f"| {d['sample_id']} | {d['episode_id']} | {c_str} | {t_str} | "
                f"{d['pred_7ep']} | {d['hit1_7ep']} | {d['pred_no_e5']} | {d['hit1_no_e5']} | "
                f"tied counts: {d['tied_7ep']} | tied counts: {d['tied_no_e5']} |"
            )

    A()

    with open(MD_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_e5_hit1_diagnostic()
