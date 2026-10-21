r"""Read-Only Diagnostics for 7-Episode Inference (Part F).

Label: "diagnostic, not a pre-registered test"
No new models, no tuning.

Evaluations:
- F1: For each slice (collapsed_full, tactic_collapsed, raw_full), when Markov status is ok:
  distribution of the number of candidates returned (1, 2, 3, more),
  how often target set intersects full Markov candidate list at any rank,
  and the rank of the first correct candidate; compared with Frequency on the same samples.
- F2: For technique raw_full:
  number of samples where target equals current technique (self-repeat),
  number of Markov Hit@1 hits that are self-repeat predictions,
  and Markov Hit@1 restricted to non-self-repeat targets (with Frequency alongside).
- F3: Per held-out episode (for collapsed_full, tactic_collapsed, and raw_full):
  number of samples with a current state never seen in training,
  and their share of misses.

Outputs:
  - reports/7ep/diagnostics_7ep.json
  - reports/7ep/diagnostics_7ep.md
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

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
PREDICTIONS_CSV_PATH = DATA_7EP / "evaluation_7ep_predictions.csv"

OUT_JSON_PATH = REPORTS_7EP / "diagnostics_7ep.json"
OUT_MD_PATH = REPORTS_7EP / "diagnostics_7ep.md"


def run_diagnostics_7ep() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING READ-ONLY DIAGNOSTICS (F1, F2, F3) - 7 EPISODES")
    print("Label: diagnostic, not a pre-registered test")
    print("=" * 80)

    # Load data
    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_data = json.load(f)
    with open(PREDICTIONS_CSV_PATH, "r", encoding="utf-8") as f:
        pred_rows = list(csv.DictReader(f))

    # Build fold models for each slice to inspect full candidate list
    t_seqs = build_tactic_sequences(seqs_data)["episodes"] if "episodes" in build_tactic_sequences(seqs_data) else build_tactic_sequences(seqs_data)
    ep_t_seqs = {ep_id: t_seqs[ep_id]["tactic_collapsed"] for ep_id in t_seqs}

    models_by_slice: dict[str, dict[str, tuple[Any, Any]]] = {
        "collapsed_full": {},
        "raw_full": {},
        "tactic_collapsed": {},
    }

    for fold in folds_data:
        ep = fold["test_episode"]
        tr = fold["training_episodes"]
        # collapsed_full
        m_cf = MarkovModel(variant="collapsed", granularity="full").fit(seqs_data, tr)
        f_cf = FrequencyBaseline(variant="collapsed", granularity="full").fit(seqs_data, tr)
        models_by_slice["collapsed_full"][ep] = (m_cf, f_cf)

        # raw_full
        m_raw = MarkovModel(variant="raw", granularity="full").fit(seqs_data, tr)
        f_raw = FrequencyBaseline(variant="raw", granularity="full").fit(seqs_data, tr)
        models_by_slice["raw_full"][ep] = (m_raw, f_raw)

        # tactic_collapsed
        m_tac = TacticMarkovModel().fit(ep_t_seqs, tr)
        f_tac = TacticFrequencyBaseline().fit(ep_t_seqs, tr)
        models_by_slice["tactic_collapsed"][ep] = (m_tac, f_tac)

    # ----------------------------------------------------
    # DIAGNOSTIC F1: Candidate list distribution & rank analysis
    # ----------------------------------------------------
    print("\n[F1] Computing candidate list distribution and target ranks when Markov status is ok...")
    f1_results: dict[str, Any] = {}

    slices_info = [
        ("collapsed_full", "technique", "collapsed", "full"),
        ("raw_full", "technique", "raw", "full"),
        ("tactic_collapsed", "tactic", "tactic_collapsed", None),
    ]

    for sl_name, sl_type, var, gran in slices_info:
        m_cand_dist = {"1": 0, "2": 0, "3": 0, "4_or_more": 0}
        f_cand_dist = {"1": 0, "2": 0, "3": 0, "4_or_more": 0}
        m_intersects = 0
        f_intersects = 0
        m_ranks: list[int] = []
        f_ranks: list[int] = []
        n_ok = 0
        total_samples = 0

        if sl_type == "technique":
            s_samples = [s for s in samples_data if s["variant"] == var and s["granularity"] == gran]
            total_samples = len(s_samples)
            for s in s_samples:
                ep = s["episode_id"]
                m_model, f_model = models_by_slice[sl_name][ep]
                cur = s["current_technique_set"]
                tgt = set(s["target_technique_set"])

                m_res = m_model.predict(cur, k=None)
                if m_res["status"] != "ok":
                    continue
                n_ok += 1

                m_cands = [c[0] for c in m_res["candidates"]]
                f_res = f_model.predict(k=None)
                f_cands = [c[0] for c in f_res["candidates"]]

                # Candidate list size distribution
                len_m = len(m_cands)
                if len_m in [1, 2, 3]:
                    m_cand_dist[str(len_m)] += 1
                else:
                    m_cand_dist["4_or_more"] += 1

                len_f = len(f_cands)
                if len_f in [1, 2, 3]:
                    f_cand_dist[str(len_f)] += 1
                else:
                    f_cand_dist["4_or_more"] += 1

                # Target rank in Markov
                m_hit_rank = None
                for idx, c in enumerate(m_cands):
                    if c in tgt:
                        m_hit_rank = idx + 1
                        break
                if m_hit_rank is not None:
                    m_intersects += 1
                    m_ranks.append(m_hit_rank)

                # Target rank in Frequency
                f_hit_rank = None
                for idx, c in enumerate(f_cands):
                    if c in tgt:
                        f_hit_rank = idx + 1
                        break
                if f_hit_rank is not None:
                    f_intersects += 1
                    f_ranks.append(f_hit_rank)
        else:
            # tactic_collapsed
            for ep in sorted(ep_t_seqs.keys()):
                items = ep_t_seqs[ep]
                m_model, f_model = models_by_slice[sl_name][ep]
                for k in range(len(items) - 1):
                    total_samples += 1
                    cur = items[k]["tactics"]
                    tgt = set(items[k + 1]["tactics"])

                    m_res = m_model.predict(cur, k=None)
                    if m_res["status"] != "ok":
                        continue
                    n_ok += 1

                    m_cands = [c[0] for c in m_res["candidates"]]
                    f_res = f_model.predict(k=None)
                    f_cands = [c[0] for c in f_res["candidates"]]

                    len_m = len(m_cands)
                    if len_m in [1, 2, 3]:
                        m_cand_dist[str(len_m)] += 1
                    else:
                        m_cand_dist["4_or_more"] += 1

                    len_f = len(f_cands)
                    if len_f in [1, 2, 3]:
                        f_cand_dist[str(len_f)] += 1
                    else:
                        f_cand_dist["4_or_more"] += 1

                    m_hit_rank = None
                    for idx, c in enumerate(m_cands):
                        if c in tgt:
                            m_hit_rank = idx + 1
                            break
                    if m_hit_rank is not None:
                        m_intersects += 1
                        m_ranks.append(m_hit_rank)

                    f_hit_rank = None
                    for idx, c in enumerate(f_cands):
                        if c in tgt:
                            f_hit_rank = idx + 1
                            break
                    if f_hit_rank is not None:
                        f_intersects += 1
                        f_ranks.append(f_hit_rank)

        f1_results[sl_name] = {
            "total_samples": total_samples,
            "n_samples_markov_ok": n_ok,
            "markov_candidate_count_distribution": m_cand_dist,
            "markov_target_intersects_full_list_count": m_intersects,
            "markov_target_intersects_full_list_rate": m_intersects / n_ok if n_ok > 0 else 0.0,
            "markov_first_correct_rank_distribution": dict(sorted(Counter(m_ranks).items())),
            "markov_first_correct_mean_rank": sum(m_ranks) / len(m_ranks) if m_ranks else None,
            "frequency_candidate_count_distribution": f_cand_dist,
            "frequency_target_intersects_full_list_count": f_intersects,
            "frequency_target_intersects_full_list_rate": f_intersects / n_ok if n_ok > 0 else 0.0,
            "frequency_first_correct_rank_distribution": dict(sorted(Counter(f_ranks).items())),
            "frequency_first_correct_mean_rank": sum(f_ranks) / len(f_ranks) if f_ranks else None,
        }
        print(f"  {sl_name:18s} | N_ok={n_ok}/{total_samples} | Markov intersects full list: {m_intersects}/{n_ok} ({m_intersects/n_ok:.4f}) vs Freq: {f_intersects}/{n_ok} ({f_intersects/n_ok:.4f})")

    # ----------------------------------------------------
    # DIAGNOSTIC F2: Raw full self-repeats analysis
    # ----------------------------------------------------
    print("\n[F2] Computing raw_full self-repeat diagnostics...")
    raw_preds = [p for p in pred_rows if p["slice"] == "raw_full"]
    n_raw = len(raw_preds)
    assert n_raw == 131, f"Expected 131 raw_full samples, got {n_raw}"

    self_repeat_samples = 0
    markov_hit1_total = 0
    markov_hit1_on_self_repeat = 0
    frequency_hit1_total = 0
    frequency_hit1_on_self_repeat = 0

    non_self_repeat_total = 0
    non_self_markov_hit1 = 0
    non_self_frequency_hit1 = 0

    for p in raw_preds:
        cur = set(json.loads(p["input_history"]))
        tgt = set(json.loads(p["target_set"]))
        is_self_repeat = (cur == tgt)

        m1 = int(p["markov_hit1"])
        f1 = int(p["frequency_hit1"])

        if is_self_repeat:
            self_repeat_samples += 1
            if m1 == 1:
                markov_hit1_on_self_repeat += 1
            if f1 == 1:
                frequency_hit1_on_self_repeat += 1
        else:
            non_self_repeat_total += 1
            if m1 == 1:
                non_self_markov_hit1 += 1
            if f1 == 1:
                non_self_frequency_hit1 += 1

        if m1 == 1:
            markov_hit1_total += 1
        if f1 == 1:
            frequency_hit1_total += 1

    f2_results = {
        "slice": "raw_full",
        "total_samples": n_raw,
        "self_repeat_samples": self_repeat_samples,
        "self_repeat_share": self_repeat_samples / n_raw,
        "markov_hit1_total": markov_hit1_total,
        "markov_hit1_on_self_repeat": markov_hit1_on_self_repeat,
        "markov_hit1_self_repeat_share": markov_hit1_on_self_repeat / markov_hit1_total if markov_hit1_total > 0 else 0.0,
        "frequency_hit1_total": frequency_hit1_total,
        "frequency_hit1_on_self_repeat": frequency_hit1_on_self_repeat,
        "non_self_repeat_samples": non_self_repeat_total,
        "non_self_repeat_markov_hit1": non_self_markov_hit1,
        "non_self_repeat_markov_hit1_rate": non_self_markov_hit1 / non_self_repeat_total if non_self_repeat_total > 0 else 0.0,
        "non_self_repeat_frequency_hit1": non_self_frequency_hit1,
        "non_self_repeat_frequency_hit1_rate": non_self_frequency_hit1 / non_self_repeat_total if non_self_repeat_total > 0 else 0.0,
    }

    print(f"  Total raw_full samples: {n_raw}")
    print(f"  Self-repeat samples: {self_repeat_samples} ({self_repeat_samples/n_raw:.4f})")
    print(f"  Markov Hit@1 total hits: {markov_hit1_total}")
    print(f"  Markov Hit@1 hits on self-repeats: {markov_hit1_on_self_repeat} ({f2_results['markov_hit1_self_repeat_share']:.4f} of hits)")
    print(f"  Restricted to non-self-repeat (N={non_self_repeat_total}):")
    print(f"    Markov Hit@1: {non_self_markov_hit1}/{non_self_repeat_total} ({f2_results['non_self_repeat_markov_hit1_rate']:.4f})")
    print(f"    Frequency Hit@1: {non_self_frequency_hit1}/{non_self_repeat_total} ({f2_results['non_self_repeat_frequency_hit1_rate']:.4f})")

    # ----------------------------------------------------
    # DIAGNOSTIC F3: Unseen states and share of misses per episode
    # ----------------------------------------------------
    print("\n[F3] Computing unseen conditioning states and miss shares per held-out episode...")
    f3_results: dict[str, Any] = {}

    for sl_name in ["collapsed_full", "tactic_collapsed", "raw_full"]:
        sl_preds = [p for p in pred_rows if p["slice"] == sl_name]
        by_ep: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for p in sl_preds:
            by_ep[p["test_episode"]].append(p)

        ep_stats = {}
        pooled_n = len(sl_preds)
        pooled_unseen = sum(1 for r in sl_preds if r["covered"].lower() != "true")
        pooled_m3_miss = sum(1 for r in sl_preds if int(r["markov_hit3"]) == 0)
        pooled_unseen_miss = sum(1 for r in sl_preds if r["covered"].lower() != "true" and int(r["markov_hit3"]) == 0)

        for ep in sorted(by_ep.keys()):
            e_rows = by_ep[ep]
            n_ep = len(e_rows)
            unseen_cnt = sum(1 for r in e_rows if r["covered"].lower() != "true")
            m1_miss_cnt = sum(1 for r in e_rows if int(r["markov_hit1"]) == 0)
            m3_miss_cnt = sum(1 for r in e_rows if int(r["markov_hit3"]) == 0)
            unseen_m1_miss = sum(1 for r in e_rows if r["covered"].lower() != "true" and int(r["markov_hit1"]) == 0)
            unseen_m3_miss = sum(1 for r in e_rows if r["covered"].lower() != "true" and int(r["markov_hit3"]) == 0)

            share_m3 = unseen_m3_miss / m3_miss_cnt if m3_miss_cnt > 0 else 0.0
            share_m1 = unseen_m1_miss / m1_miss_cnt if m1_miss_cnt > 0 else 0.0

            ep_stats[ep] = {
                "n_samples": n_ep,
                "unseen_current_state_count": unseen_cnt,
                "unseen_current_state_rate": unseen_cnt / n_ep if n_ep > 0 else 0.0,
                "markov_hit3_miss_count": m3_miss_cnt,
                "unseen_state_hit3_miss_count": unseen_m3_miss,
                "unseen_state_share_of_hit3_misses": share_m3,
                "markov_hit1_miss_count": m1_miss_cnt,
                "unseen_state_hit1_miss_count": unseen_m1_miss,
                "unseen_state_share_of_hit1_misses": share_m1,
            }

        f3_results[sl_name] = {
            "pooled": {
                "total_samples": pooled_n,
                "unseen_current_state_count": pooled_unseen,
                "unseen_current_state_rate": pooled_unseen / pooled_n if pooled_n > 0 else 0.0,
                "total_hit3_misses": pooled_m3_miss,
                "unseen_state_hit3_misses": pooled_unseen_miss,
                "unseen_share_of_hit3_misses": pooled_unseen_miss / pooled_m3_miss if pooled_m3_miss > 0 else 0.0,
            },
            "per_episode": ep_stats,
        }

    for ep, st in f3_results["collapsed_full"]["per_episode"].items():
        print(f"  collapsed_full {ep:2s} | N={st['n_samples']:2d} | Unseen={st['unseen_current_state_count']:2d} ({st['unseen_current_state_rate']:.4f}) | Misses(Hit@3)={st['markov_hit3_miss_count']:2d} | Unseen Share of Misses={st['unseen_state_share_of_hit3_misses']:.4f}")

    report_data = {
        "metadata": {
            "title": "Read-Only Diagnostics Report (7 Episodes)",
            "label": "diagnostic, not a pre-registered test",
            "episodes": ["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
        },
        "F1_candidate_distribution_and_ranks": f1_results,
        "F2_raw_full_self_repeats": f2_results,
        "F3_unseen_states_and_miss_shares": f3_results,
    }

    # Write JSON
    print(f"\nWriting diagnostics JSON to {OUT_JSON_PATH}...")
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, sort_keys=True)

    # Write Markdown
    print(f"Writing diagnostics Markdown to {OUT_MD_PATH}...")
    generate_markdown_diagnostics(report_data)

    print("Diagnostics completed successfully.")
    return report_data


def generate_markdown_diagnostics(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    f1 = data["F1_candidate_distribution_and_ranks"]
    f2 = data["F2_raw_full_self_repeats"]
    f3 = data["F3_unseen_states_and_miss_shares"]

    A("# Read-Only Diagnostics Report (7 Episodes)")
    A()
    A("> [!NOTE]")
    A("> **Diagnostic Label**: diagnostic, not a pre-registered test. No new models, no parameter tuning.")
    A()
    A("---")
    A()
    A("## Diagnostic F1: Candidate List Distribution & Rank of Correct Target")
    A()
    A("Evaluated exclusively on samples where Markov status is `ok` (conditioning state observed in training):")
    A()
    A("| Slice | N (Markov ok) | Model | 1 Cand | 2 Cands | 3 Cands | ≥4 Cands | Target Intersects Full List | First Correct Mean Rank |")
    A("|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for sl, sl_label in [
        ("collapsed_full", "Technique (collapsed_full)"),
        ("tactic_collapsed", "Tactic (tactic_collapsed)"),
        ("raw_full", "Technique (raw_full)"),
    ]:
        d = f1[sl]
        n_ok = d["n_samples_markov_ok"]
        mc = d["markov_candidate_count_distribution"]
        fc = d["frequency_candidate_count_distribution"]
        m_int = f"{d['markov_target_intersects_full_list_count']}/{n_ok} ({d['markov_target_intersects_full_list_rate']:.4f})"
        f_int = f"{d['frequency_target_intersects_full_list_count']}/{n_ok} ({d['frequency_target_intersects_full_list_rate']:.4f})"
        m_mr = f"{d['markov_first_correct_mean_rank']:.2f}" if d["markov_first_correct_mean_rank"] is not None else "—"
        f_mr = f"{d['frequency_first_correct_mean_rank']:.2f}" if d["frequency_first_correct_mean_rank"] is not None else "—"

        A(f"| {sl_label} | {n_ok} | Markov | {mc['1']} | {mc['2']} | {mc['3']} | {mc['4_or_more']} | {m_int} | {m_mr} |")
        A(f"| | | Frequency | {fc['1']} | {fc['2']} | {fc['3']} | {fc['4_or_more']} | {f_int} | {f_mr} |")
    A()
    A("### First Correct Candidate Rank Distribution (when target is in full candidate list)")
    A()
    for sl, sl_label in [
        ("collapsed_full", "Technique (collapsed_full)"),
        ("tactic_collapsed", "Tactic (tactic_collapsed)"),
        ("raw_full", "Technique (raw_full)"),
    ]:
        d = f1[sl]
        A(f"#### {sl_label}")
        A(f"- **Markov Rank Counts**: `{d['markov_first_correct_rank_distribution']}`")
        A(f"- **Frequency Rank Counts**: `{d['frequency_first_correct_rank_distribution']}`")
        A()
    A("---")
    A()
    A("## Diagnostic F2: Raw Sequence Self-Repeat Analysis (`raw_full`)")
    A()
    A(f"- **Total Samples in `raw_full`**: {f2['total_samples']}")
    A(f"- **Self-Repeat Samples (`target == current`)**: {f2['self_repeat_samples']} out of {f2['total_samples']} ({f2['self_repeat_share']:.4f} of all samples).")
    A(f"- **Total Markov Hit@1 Hits in `raw_full`**: {f2['markov_hit1_total']} hits ({f2['markov_hit1_total']/f2['total_samples']:.4f}).")
    A(f"- **Markov Hit@1 Hits on Self-Repeats**: {f2['markov_hit1_on_self_repeat']} out of {f2['markov_hit1_total']} total hits ({f2['markov_hit1_self_repeat_share']:.4f} of hits occurred on self-repeats).")
    A(f"- **Performance Restricted to Non-Self-Repeat Targets ($N={f2['non_self_repeat_samples']}$)**:")
    A(f"  - **Markov Hit@1**: {f2['non_self_repeat_markov_hit1']}/{f2['non_self_repeat_samples']} ({f2['non_self_repeat_markov_hit1_rate']:.4f})")
    A(f"  - **Frequency Hit@1**: {f2['non_self_repeat_frequency_hit1']}/{f2['non_self_repeat_samples']} ({f2['non_self_repeat_frequency_hit1_rate']:.4f})")
    A()
    A("---")
    A()
    A("## Diagnostic F3: Unseen Current Conditioning States & Share of Misses")
    A()
    A("### Technique Level (`collapsed_full`, $N=95$)")
    A()
    A("| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for ep, st in f3["collapsed_full"]["per_episode"].items():
        A(f"| {ep} | {st['n_samples']} | {st['unseen_current_state_count']} | {st['unseen_current_state_rate']:.4f} | {st['markov_hit3_miss_count']} | {st['unseen_state_hit3_miss_count']} | {st['unseen_state_share_of_hit3_misses']:.4f} |")
    p_cf = f3["collapsed_full"]["pooled"]
    A(f"| **Pooled Total** | **{p_cf['total_samples']}** | **{p_cf['unseen_current_state_count']}** | **{p_cf['unseen_current_state_rate']:.4f}** | **{p_cf['total_hit3_misses']}** | **{p_cf['unseen_state_hit3_misses']}** | **{p_cf['unseen_share_of_hit3_misses']:.4f}** |")
    A()
    A("### Tactic Level (`tactic_collapsed`, $N=76$)")
    A()
    A("| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for ep, st in f3["tactic_collapsed"]["per_episode"].items():
        A(f"| {ep} | {st['n_samples']} | {st['unseen_current_state_count']} | {st['unseen_current_state_rate']:.4f} | {st['markov_hit3_miss_count']} | {st['unseen_state_hit3_miss_count']} | {st['unseen_state_share_of_hit3_misses']:.4f} |")
    p_tac = f3["tactic_collapsed"]["pooled"]
    A(f"| **Pooled Total** | **{p_tac['total_samples']}** | **{p_tac['unseen_current_state_count']}** | **{p_tac['unseen_current_state_rate']:.4f}** | **{p_tac['total_hit3_misses']}** | **{p_tac['unseen_state_hit3_misses']}** | **{p_tac['unseen_share_of_hit3_misses']:.4f}** |")
    A()
    A("### Reference Slice (`raw_full`, $N=131$)")
    A()
    A("| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for ep, st in f3["raw_full"]["per_episode"].items():
        A(f"| {ep} | {st['n_samples']} | {st['unseen_current_state_count']} | {st['unseen_current_state_rate']:.4f} | {st['markov_hit3_miss_count']} | {st['unseen_state_hit3_miss_count']} | {st['unseen_state_share_of_hit3_misses']:.4f} |")
    p_raw = f3["raw_full"]["pooled"]
    A(f"| **Pooled Total** | **{p_raw['total_samples']}** | **{p_raw['unseen_current_state_count']}** | **{p_raw['unseen_current_state_rate']:.4f}** | **{p_raw['total_hit3_misses']}** | **{p_raw['unseen_state_hit3_misses']}** | **{p_raw['unseen_share_of_hit3_misses']:.4f}** |")
    A()

    with open(OUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_diagnostics_7ep()
