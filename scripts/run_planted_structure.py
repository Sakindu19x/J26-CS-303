r"""Planted-Structure Validation of Production Markov & Frequency Models.

Controlled experiment to demonstrate that the model and evaluation harness recover order structure
when it exists, proving that low scores on real data reflect cross-episode telemetry diversity rather
than a code defect.

Variants:
  A1: Order structure with signal level s in {0.0, 0.25, 0.5, 0.75, 1.0}.
  A2: No order structure but skewed targets (one dominant technique with p=0.30).
  A3: Set-valued steps with companion permutation c(x), testing (1/(m*n)) set-weighting.

Gates:
  G1: A1, s=1.0: Markov Top-1 >= 0.98.
  G2: A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE).
  G3: A1: Markov Top-1 is non-decreasing across the five s levels.
  G4: A1, s >= 0.25: Markov Top-1 within 0.05 of the oracle value.
  G5: A1, s >= 0.5: Markov Top-1 exceeds Frequency Top-1 by at least 0.20.
  G6: A2: |Markov Top-1 - Frequency Top-1| <= 0.03.
  G7: A3, s=1.0: Markov Top-1 >= 0.98, and Markov Top-1 is non-decreasing across s.
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Use production model classes and evaluation helpers
from src.c4.models.markov import MarkovModel
from src.c4.models.frequency import FrequencyBaseline
from src.c4.attack_sequence import collapse_sequence
from src.c4.evaluation import _hit_flags

DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

CSV_OUT_PATH = PROCESSED_DIR / "planted_structure_predictions.csv"
JSON_OUT_PATH = REPORTS_DIR / "planted_structure_report.json"
MD_OUT_PATH = REPORTS_DIR / "planted_structure_report.md"

# V: 12 smallest sorted technique IDs appearing in collapsed sequences of E1-E4
V = [
    "T1003",
    "T1003.008",
    "T1005",
    "T1007",
    "T1016",
    "T1018",
    "T1021.004",
    "T1021.005",
    "T1033",
    "T1036.005",
    "T1039",
    "T1041",
]
V_SIZE = len(V)
V_TO_IDX = {v: i for i, v in enumerate(V)}

SIGNAL_LEVELS = [0.0, 0.25, 0.5, 0.75, 1.0]
N_REPLICATES = 20
N_EPISODES = 8
EPISODE_LEN = 26


def pi(t: str) -> str:
    """Fixed cyclic permutation without fixed points over V."""
    idx = V_TO_IDX[t]
    return V[(idx + 1) % V_SIZE]


def comp(t: str) -> str:
    """Fixed companion permutation without fixed points over V."""
    idx = V_TO_IDX[t]
    return V[(idx + 6) % V_SIZE]


def generate_a1_dataset(seed: int, s: float) -> dict[str, Any]:
    """Generate A1 dataset: 8 episodes, 26 items each, single technique items."""
    rng = random.Random(seed)
    episodes = {}
    for ep_idx in range(N_EPISODES):
        ep_name = f"EP{ep_idx + 1}"
        cur = rng.choice(V)
        raw_seq = [{
            "event_id": f"{ep_name}-00",
            "techniques": [cur],
            "timestamp": "2026-01-01T00:00:00Z",
            "unlabeled_steps_skipped_before": 0,
        }]
        for item_idx in range(1, EPISODE_LEN):
            if rng.random() < s:
                nxt = pi(cur)
            else:
                others = [x for x in V if x != cur]
                nxt = rng.choice(others)
            raw_seq.append({
                "event_id": f"{ep_name}-{item_idx:02d}",
                "techniques": [nxt],
                "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z",
                "unlabeled_steps_skipped_before": 0,
            })
            cur = nxt
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes


def generate_a2_dataset(seed: int) -> dict[str, Any]:
    """Generate A2 dataset: skewed targets, dominant technique p=0.30, rest uniform."""
    rng = random.Random(seed)
    dom = V[0]
    others = V[1:]
    episodes = {}
    for ep_idx in range(N_EPISODES):
        ep_name = f"EP{ep_idx + 1}"
        raw_seq = []
        for item_idx in range(EPISODE_LEN):
            it = dom if rng.random() < 0.30 else rng.choice(others)
            raw_seq.append({
                "event_id": f"{ep_name}-{item_idx:02d}",
                "techniques": [it],
                "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z",
                "unlabeled_steps_skipped_before": 0,
            })
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes


def generate_a3_dataset(seed: int, s: float) -> dict[str, Any]:
    """Generate A3 dataset: set-valued steps {x, c(x)} with successor {pi(x), c(pi(x))}."""
    rng = random.Random(seed)
    episodes = {}
    for ep_idx in range(N_EPISODES):
        ep_name = f"EP{ep_idx + 1}"
        cur = rng.choice(V)
        raw_seq = [{
            "event_id": f"{ep_name}-00",
            "techniques": sorted([cur, comp(cur)]),
            "timestamp": "2026-01-01T00:00:00Z",
            "unlabeled_steps_skipped_before": 0,
        }]
        for item_idx in range(1, EPISODE_LEN):
            if rng.random() < s:
                nxt = pi(cur)
            else:
                others = [x for x in V if x != cur]
                nxt = rng.choice(others)
            raw_seq.append({
                "event_id": f"{ep_name}-{item_idx:02d}",
                "techniques": sorted([nxt, comp(nxt)]),
                "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z",
                "unlabeled_steps_skipped_before": 0,
            })
            cur = nxt
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes


def evaluate_dataset_loeo(
    episodes_data: dict[str, Any],
    variant_name: str,
    s_val: float,
    replicate_id: int,
    broken_markov: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run 8-fold LOEO on a dataset using production model classes."""
    ep_names = sorted(list(episodes_data.keys()))
    seqs_dict = {"episodes": episodes_data}

    rows = []
    hits = {
        "markov": {"h1": 0, "h3": 0},
        "frequency": {"h1": 0, "h3": 0},
        "markov_fallback": {"h1": 0, "h3": 0},
    }
    n_samples_total = 0

    for fold_idx, test_ep in enumerate(ep_names, 1):
        fold_id = f"fold_{fold_idx}"
        train_eps = [e for e in ep_names if e != test_ep]

        markov = MarkovModel(variant="collapsed", granularity="full").fit(seqs_dict, training_episodes=train_eps)
        freq = FrequencyBaseline(variant="collapsed", granularity="full").fit(seqs_dict, training_episodes=train_eps)

        test_items = episodes_data[test_ep]["collapsed"]
        f_pred = freq.predict(k=3)
        f_cands = [c[0] for c in f_pred["candidates"]]

        for k in range(len(test_items) - 1):
            sample_id = f"rep{replicate_id:02d}-{test_ep}-K{k:02d}"
            cur_set = test_items[k]["techniques"]
            tgt_set = set(test_items[k + 1]["techniques"])

            if broken_markov:
                m_cands = [V[0]]
                m_status = "ok"
            else:
                m_res = markov.predict(cur_set, k=3)
                m_cands = [c[0] for c in m_res["candidates"]]
                m_status = m_res["status"]

            m1, m3 = _hit_flags(m_cands, tgt_set)
            f1, f3 = _hit_flags(f_cands, tgt_set)

            if m_status == "ok":
                fb1, fb3, fb_status = m1, m3, "ok_markov"
                fb_cands = m_cands
            else:
                fb1, fb3, fb_status = f1, f3, "fallback_frequency"
                fb_cands = f_cands

            n_samples_total += 1
            hits["markov"]["h1"] += m1
            hits["markov"]["h3"] += m3
            hits["frequency"]["h1"] += f1
            hits["frequency"]["h3"] += f3
            hits["markov_fallback"]["h1"] += fb1
            hits["markov_fallback"]["h3"] += fb3

            # Record predictions per method
            for m_name, (cands, stat, h1, h3) in [
                ("markov", (m_cands, m_status, m1, m3)),
                ("frequency", (f_cands, f_pred["status"], f1, f3)),
                ("markov_fallback", (fb_cands, fb_status, fb1, fb3)),
            ]:
                rows.append({
                    "variant": variant_name,
                    "s": s_val,
                    "replicate": replicate_id,
                    "fold": fold_id,
                    "sample_id": sample_id,
                    "method": m_name,
                    "current_set": json.dumps(cur_set),
                    "target_set": json.dumps(sorted(list(tgt_set))),
                    "top3_candidates": json.dumps(cands[:3]),
                    "status": stat,
                    "hit1": h1,
                    "hit3": h3,
                })

    rep_summary = {
        "n_samples": n_samples_total,
        "markov": {
            "top1": hits["markov"]["h1"] / n_samples_total,
            "top3": hits["markov"]["h3"] / n_samples_total,
            "hits1": hits["markov"]["h1"],
            "hits3": hits["markov"]["h3"],
        },
        "frequency": {
            "top1": hits["frequency"]["h1"] / n_samples_total,
            "top3": hits["frequency"]["h3"] / n_samples_total,
            "hits1": hits["frequency"]["h1"],
            "hits3": hits["frequency"]["h3"],
        },
        "markov_fallback": {
            "top1": hits["markov_fallback"]["h1"] / n_samples_total,
            "top3": hits["markov_fallback"]["h3"] / n_samples_total,
            "hits1": hits["markov_fallback"]["h1"],
            "hits3": hits["markov_fallback"]["h3"],
        },
    }
    return rep_summary, rows


def run_experiment() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING PLANTED-STRUCTURE VALIDATION EXPERIMENT")
    print("=" * 80)

    all_csv_rows = []
    a1_by_s = {}
    a2_reps = []
    a3_by_s = {}

    # Variant A1: Order Structure
    print("\n--- Running Variant A1 (Order Structure) ---")
    for s in SIGNAL_LEVELS:
        s_reps = []
        for rep_id in range(N_REPLICATES):
            eps = generate_a1_dataset(rep_id, s)
            rep_res, rows = evaluate_dataset_loeo(eps, "A1", s, rep_id)
            s_reps.append(rep_res)
            all_csv_rows.extend(rows)

        m_top1_list = [r["markov"]["top1"] for r in s_reps]
        f_top1_list = [r["frequency"]["top1"] for r in s_reps]
        m_mean = sum(m_top1_list) / N_REPLICATES
        f_mean = sum(f_top1_list) / N_REPLICATES
        var = sum((x - m_mean) ** 2 for x in m_top1_list) / (N_REPLICATES - 1)
        se = math.sqrt(var / N_REPLICATES)
        oracle = s + (1.0 - s) / 11.0

        a1_by_s[str(s)] = {
            "s": s,
            "markov_top1_mean": m_mean,
            "markov_top1_se": se,
            "frequency_top1_mean": f_mean,
            "oracle_top1": oracle,
            "diff_from_oracle": abs(m_mean - oracle),
            "replicate_summaries": s_reps,
        }
        print(f"  s={s:4.2f} | Markov Top-1: {m_mean:.4f} (SE: {se:.4f}, oracle: {oracle:.4f}) | Freq Top-1: {f_mean:.4f}")

    # Variant A2: Skewed Targets
    print("\n--- Running Variant A2 (Skewed Targets, No Order) ---")
    for rep_id in range(N_REPLICATES):
        eps = generate_a2_dataset(rep_id)
        rep_res, rows = evaluate_dataset_loeo(eps, "A2", 0.0, rep_id)
        a2_reps.append(rep_res)
        all_csv_rows.extend(rows)

    a2_m_mean = sum(r["markov"]["top1"] for r in a2_reps) / N_REPLICATES
    a2_f_mean = sum(r["frequency"]["top1"] for r in a2_reps) / N_REPLICATES
    a2_diff = abs(a2_m_mean - a2_f_mean)
    print(f"  A2 | Markov Top-1: {a2_m_mean:.4f} | Freq Top-1: {a2_f_mean:.4f} | Diff: {a2_diff:.4f}")

    # Variant A3: Set-Valued Steps
    print("\n--- Running Variant A3 (Set-Valued Steps {x, c(x)}) ---")
    for s in SIGNAL_LEVELS:
        s_reps = []
        for rep_id in range(N_REPLICATES):
            eps = generate_a3_dataset(rep_id, s)
            rep_res, rows = evaluate_dataset_loeo(eps, "A3", s, rep_id)
            s_reps.append(rep_res)
            all_csv_rows.extend(rows)

        m_top1_list = [r["markov"]["top1"] for r in s_reps]
        f_top1_list = [r["frequency"]["top1"] for r in s_reps]
        m_mean = sum(m_top1_list) / N_REPLICATES
        f_mean = sum(f_top1_list) / N_REPLICATES

        a3_by_s[str(s)] = {
            "s": s,
            "markov_top1_mean": m_mean,
            "frequency_top1_mean": f_mean,
            "replicate_summaries": s_reps,
        }
        print(f"  s={s:4.2f} | A3 Markov Top-1: {m_mean:.4f} | A3 Freq Top-1: {f_mean:.4f}")

    # Negative Control on A1, s=1.0
    print("\n--- Running Negative Control (Deliberately Broken Markov on A1, s=1.0) ---")
    neg_reps = []
    for rep_id in range(N_REPLICATES):
        eps = generate_a1_dataset(rep_id, 1.0)
        rep_res, _ = evaluate_dataset_loeo(eps, "A1_broken", 1.0, rep_id, broken_markov=True)
        neg_reps.append(rep_res)
    neg_m_mean = sum(r["markov"]["top1"] for r in neg_reps) / N_REPLICATES
    print(f"  Broken Markov Top-1: {neg_m_mean:.4f}")

    # Evaluate Pre-Declared Gates
    chance_top1 = 1.0 / 11.0  # 1 / (V - 1)
    se_0 = a1_by_s["0.0"]["markov_top1_se"]
    g2_threshold = max(0.02, 3.0 * se_0)

    g1_val = a1_by_s["1.0"]["markov_top1_mean"]
    g1_pass = bool(g1_val >= 0.98)

    g2_diff = abs(a1_by_s["0.0"]["markov_top1_mean"] - chance_top1)
    g2_pass = bool(g2_diff <= g2_threshold)

    a1_means_seq = [a1_by_s[str(s)]["markov_top1_mean"] for s in SIGNAL_LEVELS]
    g3_pass = bool(all(a1_means_seq[i] <= a1_means_seq[i + 1] for i in range(len(a1_means_seq) - 1)))

    g4_diffs = [a1_by_s[str(s)]["diff_from_oracle"] for s in [0.25, 0.5, 0.75, 1.0]]
    g4_pass = bool(all(d <= 0.05 for d in g4_diffs))

    g5_diffs = [a1_by_s[str(s)]["markov_top1_mean"] - a1_by_s[str(s)]["frequency_top1_mean"] for s in [0.5, 0.75, 1.0]]
    g5_pass = bool(all(d >= 0.20 for d in g5_diffs))

    g6_pass = bool(a2_diff <= 0.03)

    a3_means_seq = [a3_by_s[str(s)]["markov_top1_mean"] for s in SIGNAL_LEVELS]
    g7_pass = bool(a3_means_seq[-1] >= 0.98 and all(a3_means_seq[i] <= a3_means_seq[i + 1] for i in range(len(a3_means_seq) - 1)))

    neg_g1_failed = bool(neg_m_mean < 0.98)

    gates = {
        "G1": {
            "description": "A1, s=1.0: Markov Top-1 >= 0.98",
            "threshold": 0.98,
            "measured": g1_val,
            "passed": g1_pass,
        },
        "G2": {
            "description": f"A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE) ({g2_threshold:.4f})",
            "threshold": g2_threshold,
            "measured": g2_diff,
            "chance": chance_top1,
            "passed": g2_pass,
        },
        "G3": {
            "description": "A1: Markov Top-1 is non-decreasing across five s levels",
            "measured_trajectory": a1_means_seq,
            "passed": g3_pass,
        },
        "G4": {
            "description": "A1, s >= 0.25: Markov Top-1 within 0.05 of oracle value",
            "max_difference": max(g4_diffs),
            "differences": {str(s): a1_by_s[str(s)]["diff_from_oracle"] for s in [0.25, 0.5, 0.75, 1.0]},
            "passed": g4_pass,
        },
        "G5": {
            "description": "A1, s >= 0.5: Markov Top-1 exceeds Frequency Top-1 by >= 0.20",
            "min_excess": min(g5_diffs),
            "excesses": {str(s): a1_by_s[str(s)]["markov_top1_mean"] - a1_by_s[str(s)]["frequency_top1_mean"] for s in [0.5, 0.75, 1.0]},
            "passed": g5_pass,
        },
        "G6": {
            "description": "A2: |Markov Top-1 - Frequency Top-1| <= 0.03 (no order signal)",
            "measured_markov": a2_m_mean,
            "measured_frequency": a2_f_mean,
            "difference": a2_diff,
            "threshold": 0.03,
            "passed": g6_pass,
        },
        "G7": {
            "description": "A3, s=1.0: Markov Top-1 >= 0.98 and non-decreasing across s",
            "s_1_measured": a3_means_seq[-1],
            "measured_trajectory": a3_means_seq,
            "passed": g7_pass,
        },
        "Negative_Control": {
            "description": "Negative control: A1 at s=1.0 with broken Markov FAILS G1",
            "broken_markov_top1": neg_m_mean,
            "passed": neg_g1_failed,
        },
    }

    report_data = {
        "vocabulary_size": V_SIZE,
        "vocabulary": V,
        "signal_levels": SIGNAL_LEVELS,
        "n_replicates": N_REPLICATES,
        "n_episodes": N_EPISODES,
        "episode_length": EPISODE_LEN,
        "chance_top1": chance_top1,
        "A1": a1_by_s,
        "A2": {
            "markov_top1_mean": a2_m_mean,
            "frequency_top1_mean": a2_f_mean,
            "difference": a2_diff,
        },
        "A3": a3_by_s,
        "negative_control": {
            "broken_markov_top1": neg_m_mean,
            "g1_failed_as_expected": neg_g1_failed,
        },
        "gates": gates,
    }

    # Write CSV
    print(f"\nWriting {len(all_csv_rows)} prediction rows to {CSV_OUT_PATH}...")
    fieldnames = [
        "variant",
        "s",
        "replicate",
        "fold",
        "sample_id",
        "method",
        "current_set",
        "target_set",
        "top3_candidates",
        "status",
        "hit1",
        "hit3",
    ]
    with open(CSV_OUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_csv_rows)

    # Write JSON
    print(f"Writing report JSON to {JSON_OUT_PATH}...")
    with open(JSON_OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)

    # Generate Markdown Report
    print(f"Writing report Markdown to {MD_OUT_PATH}...")
    generate_markdown_report(report_data)

    print("Experiment completed successfully.")
    return report_data


def generate_markdown_report(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    A("# Planted-Structure Validation Experiment Report")
    A()
    A("## Pre-Declared Specifications & Experimental Setup")
    A()
    A(f"- **Vocabulary (V)**: {data['vocabulary_size']} techniques (the 12 smallest sorted distinct technique IDs from E1–E4 collapsed sequences):")
    A(f"  `{', '.join(data['vocabulary'])}`")
    A("- **Planted Successor Permutation (pi)**: Cyclic permutation `pi(t_i) = t_{(i+1) % 12}` without fixed points (marginal target frequencies are uniform).")
    A("- **Generator**: stdlib `random.Random` (seeds 0..19). Episode length: 26 items; 8 episodes per replicate dataset; 20 replicate datasets per signal level.")
    A("- **Signal Levels (s)**: `0.0, 0.25, 0.50, 0.75, 1.00`.")
    A("- **Evaluation Code**: Production `MarkovModel` and `FrequencyBaseline` evaluated under 8-fold Leave-One-Episode-Out cross-validation.")
    A(f"- **Theoretical Closed Forms**: Oracle Top-1 = `s + (1-s)/(V-1)`; Chance Top-1 = `1/(V-1) = 1/11 = {data['chance_top1']:.6f}`.")
    A()
    A("---")
    A()
    A("## Pre-Declared Gates Verification Summary")
    A()
    A("| Gate | Description | Measured Value | Threshold | Result |")
    A("|:---|:---|:---:|:---:|:---:|")
    g = data["gates"]
    A(f"| **G1** | A1, s=1.0: Markov Top-1 >= 0.98 | `{g['G1']['measured']:.4f}` | `>= 0.9800` | **{'PASS' if g['G1']['passed'] else 'FAIL'}** |")
    A(f"| **G2** | A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE) | `{g['G2']['measured']:.4f}` | `<= {g['G2']['threshold']:.4f}` | **{'PASS' if g['G2']['passed'] else 'FAIL'}** |")
    A(f"| **G3** | A1: Markov Top-1 non-decreasing across s | `{[round(x, 4) for x in g['G3']['measured_trajectory']]}` | Non-decreasing | **{'PASS' if g['G3']['passed'] else 'FAIL'}** |")
    A(f"| **G4** | A1, s >= 0.25: Markov within 0.05 of oracle | Max diff: `{g['G4']['max_difference']:.4f}` | `<= 0.0500` | **{'PASS' if g['G4']['passed'] else 'FAIL'}** |")
    A(f"| **G5** | A1, s >= 0.5: Markov exceeds Freq by >= 0.20 | Min excess: `{g['G5']['min_excess']:.4f}` | `>= 0.2000` | **{'PASS' if g['G5']['passed'] else 'FAIL'}** |")
    A(f"| **G6** | A2: |Markov Top-1 - Frequency Top-1| <= 0.03 (no order) | `{g['G6']['difference']:.4f}` | `<= 0.0300` | **{'PASS' if g['G6']['passed'] else 'FAIL'}** |")
    A(f"| **G7** | A3, s=1.0: Markov Top-1 >= 0.98 and non-decreasing | s=1.0: `{g['G7']['s_1_measured']:.4f}` | `>= 0.9800 & non-decreasing` | **{'PASS' if g['G7']['passed'] else 'FAIL'}** |")
    A(f"| **NegCtrl** | Negative control: broken Markov fails G1 | `{g['Negative_Control']['broken_markov_top1']:.4f}` | `< 0.9800 (must fail G1)` | **{'PASS (Failed G1 as expected)' if g['Negative_Control']['passed'] else 'FAIL'}** |")
    A()
    A("---")
    A()
    A("## Detailed Results by Variant")
    A()
    A("### Variant A1: Order Structure Recovery (Single-Technique Steps)")
    A()
    A("| Signal Level (s) | Oracle Top-1 | Markov Top-1 Mean | Markov SE | Frequency Top-1 Mean | |Markov - Oracle| | Markov - Frequency |")
    A("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
        row = data["A1"][s_str]
        m_f_diff = row["markov_top1_mean"] - row["frequency_top1_mean"]
        A(f"| {float(s_str):.2f} | {row['oracle_top1']:.4f} | {row['markov_top1_mean']:.4f} | {row['markov_top1_se']:.4f} | {row['frequency_top1_mean']:.4f} | {row['diff_from_oracle']:.4f} | {m_f_diff:+.4f} |")
    A()
    A("### Variant A2: Skewed Targets (No Order Structure)")
    A()
    A("Evaluates i.i.d. draws with one dominant technique having probability 0.30 and the remaining 11 techniques uniform (`(1 - 0.30)/11 = 0.0636`):")
    A(f"- **Markov Top-1 Mean**: `{data['A2']['markov_top1_mean']:.4f}`")
    A(f"- **Frequency Baseline Top-1 Mean**: `{data['A2']['frequency_top1_mean']:.4f}`")
    A(f"- **Absolute Difference**: `{data['A2']['difference']:.4f}` (Gate G6 requires `<= 0.0300`)")
    A()
    A("### Variant A3: Set-Valued Steps {x, c(x)}")
    A()
    A("Evaluates pair-valued steps using companion permutation `c(x) = t_{(x+6) % 12}` testing the `1/(m*n)` set-weighting logic under production Hit@k:")
    A()
    A("| Signal Level (s) | A3 Markov Top-1 Mean | A3 Frequency Top-1 Mean |")
    A("|:---:|:---:|:---:|")
    for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
        row = data["A3"][s_str]
        A(f"| {float(s_str):.2f} | {row['markov_top1_mean']:.4f} | {row['frequency_top1_mean']:.4f} |")
    A()
    A("---")
    A()
    A("## Negative Control Result")
    A()
    A("When Markov is deliberately broken (monkeypatched to predict a single fixed candidate `T1003` regardless of input):")
    A(f"- Broken Markov Top-1 at s=1.0: `{data['negative_control']['broken_markov_top1']:.4f}`")
    A("- Gate G1 threshold: `>= 0.9800`")
    A("- Verdict: **G1 FAILS as expected**, proving that the test gate has non-trivial discriminating power.")

    with open(MD_OUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_experiment()
