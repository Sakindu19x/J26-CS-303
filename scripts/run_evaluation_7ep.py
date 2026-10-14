"""Pre-registered 7-Episode LOEO Evaluation Runner (E1-E7).

Evaluates Next-Technique and Next-Tactic prediction across 7 Leave-One-Episode-Out folds.
Follows reports/prereg_7episode_design.md with Amendments 1, 2, and 3.

Slices evaluated:
  1. collapsed_full (PRIMARY technique slice, N=95)
  2. tactic_collapsed (SECONDARY tactic slice, N=76)
  3. raw_full (REFERENCE technique slice, N=131)

Outputs:
  - data/processed_7ep/evaluation_7ep_predictions.csv
  - reports/7ep/evaluation_7ep_results.json
  - reports/7ep/evaluation_7ep_report.md
  - artifacts/7ep/fold_models/<slice>/<test_episode>.json
  - artifacts/7ep/fold_models/manifest.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
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

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_7EP = BASE_DIR / "data" / "processed_7ep"
REPORTS_7EP = BASE_DIR / "reports" / "7ep"
ARTIFACTS_7EP = BASE_DIR / "artifacts" / "7ep"
FOLD_MODELS_DIR = ARTIFACTS_7EP / "fold_models"

SEQUENCES_PATH = DATA_7EP / "attack_sequences.json"
FOLDS_PATH = DATA_7EP / "loeo_folds.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
REFERENCE_PATH = DATA_7EP / "technique_tactic_reference.json"

FROZEN_TECH_RESULTS = BASE_DIR / "reports" / "evaluation_results.json"
FROZEN_TAC_RESULTS = BASE_DIR / "reports" / "tactic_evaluation_results.json"

PREDICTIONS_CSV_PATH = DATA_7EP / "evaluation_7ep_predictions.csv"
RESULTS_JSON_PATH = REPORTS_7EP / "evaluation_7ep_results.json"
REPORT_MD_PATH = REPORTS_7EP / "evaluation_7ep_report.md"
MANIFEST_PATH = FOLD_MODELS_DIR / "manifest.json"


def exact_mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar test p-value based on the binomial distribution."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_technique_fold_model(
    slice_name: str,
    test_ep: str,
    train_eps: list[str],
    markov: MarkovModel,
    freq: FrequencyBaseline,
) -> Path:
    out_dir = FOLD_MODELS_DIR / slice_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{test_ep}.json"

    data = {
        "slice": slice_name,
        "test_episode": test_ep,
        "training_episodes": train_eps,
        "markov": {
            "n_step_transitions": dict(sorted(markov.n_step_transitions.items())),
            "counts": {
                a: dict(sorted(markov.counts[a].items()))
                for a in sorted(markov.counts.keys())
            },
            "probabilities": {
                a: dict(sorted(markov.probabilities[a].items()))
                for a in sorted(markov.probabilities.keys())
            },
        },
        "frequency": {
            "n_step_transitions": freq.n_step_transitions,
            "counts": dict(sorted(freq.counts.items())),
            "probabilities": dict(sorted(freq.probabilities.items())),
        },
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    return out_file


def save_tactic_fold_model(
    slice_name: str,
    test_ep: str,
    train_eps: list[str],
    m_model: TacticMarkovModel,
    f_model: TacticFrequencyBaseline,
) -> Path:
    out_dir = FOLD_MODELS_DIR / slice_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{test_ep}.json"

    data = {
        "slice": slice_name,
        "test_episode": test_ep,
        "training_episodes": train_eps,
        "markov": {
            "n_step_transitions": dict(sorted(m_model.n_step_transitions.items())),
            "counts": {
                a: dict(sorted(m_model.counts[a].items()))
                for a in sorted(m_model.counts.keys())
            },
            "probabilities": {
                a: dict(sorted(m_model.probabilities[a].items()))
                for a in sorted(m_model.probabilities.keys())
            },
        },
        "frequency": {
            "counts": dict(sorted(f_model.counts.items())),
            "probabilities": dict(sorted(f_model.probabilities.items())),
        },
    }
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    return out_file


def run_evaluation_7ep() -> dict[str, Any]:
    print("================================================================================")
    print("RUNNING 7-EPISODE PRE-REGISTERED LOEO EVALUATION (E1-E7)")
    print("================================================================================")

    with open(SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_data = json.load(f)

    REPORTS_7EP.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_7EP.mkdir(parents=True, exist_ok=True)
    FOLD_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Evaluate Primary Slice: collapsed_full (Technique)
    print("\n[1/3] Evaluating PRIMARY technique slice: collapsed_full (N=95)...")
    cf_samples = [s for s in samples_data if s["variant"] == "collapsed" and s["granularity"] == "full"]
    assert len(cf_samples) == 95, f"Expected 95 collapsed_full samples, got {len(cf_samples)}"

    tech_col_res, tech_col_rows = evaluate_loeo_slice(
        variant="collapsed",
        granularity="full",
        save_fold_models=False,
        sequences_data=seqs_data,
        folds_data=folds_data,
        samples_data=cf_samples,
    )

    # Save fold models for collapsed_full
    ep_seqs = seqs_data["episodes"]
    for fold in folds_data:
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        m_tech = MarkovModel(variant="collapsed", granularity="full").fit(ep_seqs, training_episodes=train_eps)
        f_tech = FrequencyBaseline(variant="collapsed", granularity="full").fit(ep_seqs, training_episodes=train_eps)
        save_technique_fold_model("collapsed_full", test_ep, train_eps, m_tech, f_tech)

    # 2. Evaluate Secondary Slice: tactic_collapsed (Tactic)
    print("[2/3] Evaluating SECONDARY tactic slice: tactic_collapsed (N=76)...")
    tac_res, tac_rows = evaluate_tactic_slice(
        variant="tactic_collapsed",
        sequences_data=seqs_data,
        folds_data=folds_data,
    )
    assert tac_res["n_samples"] == 76, f"Expected 76 tactic_collapsed samples, got {tac_res['n_samples']}"

    # Save fold models for tactic_collapsed
    t_seqs = build_tactic_sequences(seqs_data)["episodes"] if "episodes" in build_tactic_sequences(seqs_data) else build_tactic_sequences(seqs_data)
    ep_t_seqs = {ep_id: t_seqs[ep_id]["tactic_collapsed"] for ep_id in t_seqs}
    for fold in folds_data:
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        m_tac = TacticMarkovModel().fit(ep_t_seqs, train_eps)
        f_tac = TacticFrequencyBaseline().fit(ep_t_seqs, train_eps)
        save_tactic_fold_model("tactic_collapsed", test_ep, train_eps, m_tac, f_tac)

    # 3. Evaluate Reference Slice: raw_full (Technique)
    print("[3/3] Evaluating REFERENCE technique slice: raw_full (N=131)...")
    raw_samples = [s for s in samples_data if s["variant"] == "raw" and s["granularity"] == "full"]
    assert len(raw_samples) == 131, f"Expected 131 raw_full samples, got {len(raw_samples)}"

    tech_raw_res, tech_raw_rows = evaluate_loeo_slice(
        variant="raw",
        granularity="full",
        save_fold_models=False,
        sequences_data=seqs_data,
        folds_data=folds_data,
        samples_data=raw_samples,
    )

    # Save fold models for raw_full
    for fold in folds_data:
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        m_raw = MarkovModel(variant="raw", granularity="full").fit(ep_seqs, training_episodes=train_eps)
        f_raw = FrequencyBaseline(variant="raw", granularity="full").fit(ep_seqs, training_episodes=train_eps)
        save_technique_fold_model("raw_full", test_ep, train_eps, m_raw, f_raw)

    # 4. Generate Manifest of Saved Fold Models
    print("\nWriting fold models manifest...")
    manifest_entries: dict[str, dict[str, Any]] = {}
    for slice_dir in sorted(FOLD_MODELS_DIR.iterdir()):
        if slice_dir.is_dir():
            for model_file in sorted(slice_dir.glob("*.json")):
                rel_path = str(model_file.relative_to(BASE_DIR)).replace("\\", "/")
                manifest_entries[rel_path] = {
                    "sha256": sha256_file(model_file),
                    "size_bytes": model_file.stat().st_size,
                }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"files": manifest_entries}, f, indent=2, sort_keys=True)
    print(f"Manifest written with {len(manifest_entries)} fold model files.")

    # 5. Build Unified Predictions CSV (one row per sample and slice)
    print("\nAssembling evaluation_7ep_predictions.csv...")
    csv_rows: list[dict[str, Any]] = []

    def assemble_csv_slice(slice_name: str, raw_eval_rows: list[dict[str, Any]], samples_list: list[dict[str, Any]], is_tactic: bool) -> None:
        # Group rows by sample_id
        grouped: dict[str, dict[str, dict[str, Any]]] = {}
        for r in raw_eval_rows:
            sid = r["sample_id"]
            if sid not in grouped:
                grouped[sid] = {}
            grouped[sid][r["method"]] = r

        # Map sample_id to metadata
        meta_map = {s["sample_id"]: s for s in samples_list}

        # Determine ceiling per sample
        for sid, by_method in grouped.items():
            s_meta = meta_map[sid]
            test_ep = s_meta["episode_id"]
            
            # target set
            if is_tactic:
                cur_history = s_meta["current_tactics"]
                tgt_set = sorted(s_meta["target_tactics"])
            else:
                cur_history = s_meta["current_technique_set"]
                tgt_set = sorted(s_meta["target_technique_set"])

            m_row = by_method["markov"]
            f_row = by_method["frequency"]
            fb_row = by_method["markov_fallback"]

            # Covered: Markov status == ok
            is_covered = (m_row["status"] == "ok")

            # Ceiling: target set intersects training target pool
            # For technique: check fold training target pool
            # For tactic: check fold training tactic target pool
            if is_tactic:
                train_eps = [f["training_episodes"] for f in folds_data if f["test_episode"] == test_ep][0]
                t_pool: set[str] = set()
                for ep in train_eps:
                    itms = ep_t_seqs[ep]
                    for i in range(len(itms) - 1):
                        t_pool.update(itms[i + 1]["tactics"])
                is_ceiling = bool(set(tgt_set) & t_pool)
            else:
                variant_name = "collapsed" if "collapsed" in slice_name else "raw"
                train_eps = [f["training_episodes"] for f in folds_data if f["test_episode"] == test_ep][0]
                t_pool = set()
                for ep in train_eps:
                    itms = ep_seqs[ep][variant_name]
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

    assemble_csv_slice("collapsed_full", tech_col_rows, cf_samples, is_tactic=False)
    assemble_csv_slice("tactic_collapsed", tac_rows, tac_samples_list, is_tactic=True)
    assemble_csv_slice("raw_full", tech_raw_rows, raw_samples, is_tactic=False)

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
    print(f"Predictions CSV written: {len(csv_rows)} total rows (95 cf + 76 tac + 131 raw).")

    # 6. Pre-Registered McNemar Paired Tests (P1, P2) and Non-Primary Tests
    print("\nComputing McNemar paired tests...")
    paired_tests: dict[str, Any] = {}

    # Helper for paired test on predictions
    def compute_paired(slice_name: str, metric: str, m1_col: str, m2_col: str) -> dict[str, Any]:
        rows_slice = [r for r in csv_rows if r["slice"] == slice_name]
        n = len(rows_slice)
        both_hit = sum(1 for r in rows_slice if r[m1_col] == 1 and r[m2_col] == 1)
        m1_only = sum(1 for r in rows_slice if r[m1_col] == 1 and r[m2_col] == 0)
        m2_only = sum(1 for r in rows_slice if r[m1_col] == 0 and r[m2_col] == 1)
        neither = sum(1 for r in rows_slice if r[m1_col] == 0 and r[m2_col] == 0)
        p_val = exact_mcnemar(m1_only, m2_only)
        m1_rate = sum(r[m1_col] for r in rows_slice) / n
        m2_rate = sum(r[m2_col] for r in rows_slice) / n
        diff = m1_rate - m2_rate
        return {
            "slice": slice_name,
            "metric": metric,
            "m1_column": m1_col,
            "m2_column": m2_col,
            "n_samples": n,
            "table": {
                "both_hit": both_hit,
                "b_m1_only": m1_only,
                "c_m2_only": m2_only,
                "neither": neither,
            },
            "m1_rate": m1_rate,
            "m2_rate": m2_rate,
            "rate_difference": diff,
            "p_value_raw": p_val,
            "label": "raw p, pre-Holm",
        }

    # P1: Tactic tactic_collapsed Hit@3
    paired_tests["P1_tactic_collapsed_hit3"] = compute_paired(
        "tactic_collapsed", "Hit@3", "markov_hit3", "frequency_hit3"
    )
    # P2: Technique collapsed_full Hit@3
    paired_tests["P2_technique_collapsed_full_hit3"] = compute_paired(
        "collapsed_full", "Hit@3", "markov_hit3", "frequency_hit3"
    )
    # Non-primary descriptive comparisons
    paired_tests["descriptive_technique_collapsed_full_hit1"] = compute_paired(
        "collapsed_full", "Hit@1", "markov_hit1", "frequency_hit1"
    )
    paired_tests["descriptive_tactic_collapsed_hit1"] = compute_paired(
        "tactic_collapsed", "Hit@1", "markov_hit1", "frequency_hit1"
    )
    paired_tests["descriptive_technique_fallback_vs_freq_hit3"] = compute_paired(
        "collapsed_full", "Hit@3", "markov_fallback_hit3", "frequency_hit3"
    )
    paired_tests["descriptive_technique_fallback_vs_freq_hit1"] = compute_paired(
        "collapsed_full", "Hit@1", "markov_fallback_hit1", "frequency_hit1"
    )
    paired_tests["descriptive_tactic_fallback_vs_freq_hit3"] = compute_paired(
        "tactic_collapsed", "Hit@3", "markov_fallback_hit3", "frequency_hit3"
    )
    paired_tests["descriptive_tactic_fallback_vs_freq_hit1"] = compute_paired(
        "tactic_collapsed", "Hit@1", "markov_fallback_hit1", "frequency_hit1"
    )

    # 7. Load Frozen 4-Episode Results for Comparison
    with open(FROZEN_TECH_RESULTS, "r", encoding="utf-8") as f:
        frozen_tech = json.load(f)["primary_slice"]
    with open(FROZEN_TAC_RESULTS, "r", encoding="utf-8") as f:
        frozen_tac = json.load(f)["slices"]["tactic_collapsed"]

    comparison_4ep = {
        "technique_collapsed_full": {
            "4ep": {
                "n_samples": frozen_tech["n_samples"],
                "markov_hit1": frozen_tech["headline"]["markov"]["hit1"],
                "markov_hit3": frozen_tech["headline"]["markov"]["hit3"],
                "frequency_hit1": frozen_tech["headline"]["frequency"]["hit1"],
                "frequency_hit3": frozen_tech["headline"]["frequency"]["hit3"],
                "fallback_hit1": frozen_tech["headline"]["fallback"]["hit1"],
                "fallback_hit3": frozen_tech["headline"]["fallback"]["hit3"],
                "coverage_covered": frozen_tech["headline"]["coverage"]["covered_samples"],
                "ceiling_hits": frozen_tech["headline"]["ceiling"]["hits"],
            },
            "7ep": {
                "n_samples": tech_col_res["n_samples"],
                "markov_hit1": tech_col_res["headline"]["markov"]["hit1"],
                "markov_hit3": tech_col_res["headline"]["markov"]["hit3"],
                "frequency_hit1": tech_col_res["headline"]["frequency"]["hit1"],
                "frequency_hit3": tech_col_res["headline"]["frequency"]["hit3"],
                "fallback_hit1": tech_col_res["headline"]["fallback"]["hit1"],
                "fallback_hit3": tech_col_res["headline"]["fallback"]["hit3"],
                "coverage_covered": tech_col_res["headline"]["coverage"]["covered_samples"],
                "ceiling_hits": tech_col_res["headline"]["ceiling"]["hits"],
            },
        },
        "tactic_collapsed": {
            "4ep": {
                "n_samples": frozen_tac["n_samples"],
                "markov_hit1": frozen_tac["headline"]["markov"]["hit1"],
                "markov_hit3": frozen_tac["headline"]["markov"]["hit3"],
                "frequency_hit1": frozen_tac["headline"]["frequency"]["hit1"],
                "frequency_hit3": frozen_tac["headline"]["frequency"]["hit3"],
                "fallback_hit1": frozen_tac["headline"]["markov_fallback"]["hit1"],
                "fallback_hit3": frozen_tac["headline"]["markov_fallback"]["hit3"],
                "coverage_covered": frozen_tac["coverage"]["covered_samples"],
                "ceiling_hits": frozen_tac["ceiling"]["hits"],
            },
            "7ep": {
                "n_samples": tac_res["n_samples"],
                "markov_hit1": tac_res["headline"]["markov"]["hit1"],
                "markov_hit3": tac_res["headline"]["markov"]["hit3"],
                "frequency_hit1": tac_res["headline"]["frequency"]["hit1"],
                "frequency_hit3": tac_res["headline"]["frequency"]["hit3"],
                "fallback_hit1": tac_res["headline"]["markov_fallback"]["hit1"],
                "fallback_hit3": tac_res["headline"]["markov_fallback"]["hit3"],
                "coverage_covered": tac_res["coverage"]["covered_samples"],
                "ceiling_hits": tac_res["ceiling"]["hits"],
            },
        },
    }

    # 8. Assemble Full Results Dictionary
    results_7ep = {
        "metadata": {
            "evaluation_scope": "7-Episode LOEO (E1-E7)",
            "preregistration": "reports/prereg_7episode_design.md (with Amendments 1, 2, and 3)",
            "folds": [f["fold_id"] for f in folds_data],
            "episodes": [f["test_episode"] for f in folds_data],
            "tuning": "NO TUNING. Models, k, tie rules, and thresholds identical to src/c4 baseline.",
        },
        "primary_slice_technique_collapsed_full": tech_col_res,
        "secondary_slice_tactic_collapsed": tac_res,
        "reference_slice_technique_raw_full": tech_raw_res,
        "paired_tests": paired_tests,
        "comparison_with_4ep": comparison_4ep,
    }

    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results_7ep, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"Results JSON written to {RESULTS_JSON_PATH}")

    # 9. Generate Markdown Report
    print("Generating Markdown report...")
    md_lines: list[str] = []
    def A(line: str = "") -> None:
        md_lines.append(line)

    A("# Pre-Registered 7-Episode LOEO Evaluation Report (E1–E7)")
    A()
    A("This report documents the pre-registered leave-one-episode-out (LOEO) evaluation across all seven episodes (E1–E7) of the C4 dataset.")
    A("All procedures strictly adhere to `reports/prereg_7episode_design.md` with Amendments 1, 2, and 3.")
    A("No model parameters, candidate thresholds, tie rules, or evaluation metrics were tuned.")
    A()
    A("---")
    A()
    A("## 1. Setup and Pre-Registration Gates")
    A()
    A("- **Evaluated Episodes**: E1, E2, E3, E4, E5, E6, E7 ($7$ folds).")
    A("- **Evaluated Slices**:")
    A("  1. **Primary**: Technique `collapsed_full` ($N=95$ transition samples).")
    A("  2. **Secondary**: Tactic `tactic_collapsed` ($N=76$ transition samples).")
    A("  3. **Reference**: Technique `raw_full` ($N=131$ transition samples).")
    A("- **Models Evaluated**: `MarkovModel` (first-order Markov chain), `FrequencyBaseline` (unconditional frequency), and `markov_fallback` (fallback to frequency when Markov status is not ok).")
    A("- **Fold Models**: Stored deterministically in `artifacts/7ep/fold_models/<slice>/<test_episode>.json` with hashes recorded in `artifacts/7ep/fold_models/manifest.json`.")
    A("- **Episode E5**: Evaluated as an explicit test fold ($N=2$, covered=0, ceiling=0).")
    A()
    A("---")
    A()
    A("## 2. Primary Slice: Technique `collapsed_full` (N=95)")
    A()
    A("### Headline Pooled Results")
    A()
    A("| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    head_cf = tech_col_res["headline"]
    for m_key, m_label in [("markov", "Markov"), ("frequency", "Frequency"), ("fallback", "Markov Fallback")]:
        row = head_cf[m_key]
        w1 = f"[{row['wilson95_top1'][0]:.4f}, {row['wilson95_top1'][1]:.4f}]"
        w3 = f"[{row['wilson95_top3'][0]:.4f}, {row['wilson95_top3'][1]:.4f}]"
        A(f"| {m_label:15s} | {row['hit1']:2d} / 95 | {row['top1']:.4f} | {w1:21s} | {row['hit3']:2d} / 95 | {row['top3']:.4f} | {w3:21s} | {row['fold_mean_top1']:.4f} | {row['fold_mean_top3']:.4f} |")

    A()
    A(f"- **Coverage (Markov Status ok)**: {head_cf['coverage']['covered_samples']}/95 ({head_cf['coverage']['coverage_rate']:.4f}).")
    A(f"  - On covered samples ($N={head_cf['coverage']['covered_n']}$): Markov Hit@1 = {head_cf['coverage']['markov_on_covered_hit1']}/{head_cf['coverage']['covered_n']} ({head_cf['coverage']['markov_on_covered_top1']:.4f}), Frequency Hit@1 = {head_cf['coverage']['frequency_on_covered_hit1']}/{head_cf['coverage']['covered_n']} ({head_cf['coverage']['frequency_on_covered_top1']:.4f}).")
    A(f"  - On covered samples ($N={head_cf['coverage']['covered_n']}$): Markov Hit@3 = {head_cf['coverage']['markov_on_covered_hit3']}/{head_cf['coverage']['covered_n']} ({head_cf['coverage']['markov_on_covered_top3']:.4f}), Frequency Hit@3 = {head_cf['coverage']['frequency_on_covered_hit3']}/{head_cf['coverage']['covered_n']} ({head_cf['coverage']['frequency_on_covered_top3']:.4f}).")
    A(f"- **Target Ceiling**: {head_cf['ceiling']['hits']}/95 ({head_cf['ceiling']['ceiling_rate']:.4f}) of samples had at least one target technique appearing in training targets for that fold.")
    A()
    A("### Per-Fold Breakdown")
    A()
    A("| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for fid, f_data in sorted(tech_col_res["per_fold"].items(), key=lambda x: int(x[0].split("_")[1])):
        tep = f_data["test_episode"]
        fn = f_data["n_samples"]
        m_h1 = f_data["markov"]["hit1"]
        m_h3 = f_data["markov"]["hit3"]
        f_h1 = f_data["frequency"]["hit1"]
        f_h3 = f_data["frequency"]["hit3"]
        fb_h1 = f_data["fallback"]["hit1"]
        fb_h3 = f_data["fallback"]["hit3"]
        cov = f_data["markov"]["covered_samples"]
        ceil = f_data["ceiling"]["hits"]
        A(f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({f_data['markov']['top1']:.4f}) | {m_h3:2d} ({f_data['markov']['top3']:.4f}) | {f_h1:2d} ({f_data['frequency']['top1']:.4f}) | {f_h3:2d} ({f_data['frequency']['top3']:.4f}) | {fb_h1:2d} ({f_data['fallback']['top1']:.4f}) | {fb_h3:2d} ({f_data['fallback']['top3']:.4f}) | {cov:2d} / {fn:2d} | {ceil:2d} / {fn:2d} |")

    A()
    A("---")
    A()
    A("## 3. Secondary Slice: Tactic `tactic_collapsed` (N=76)")
    A()
    A("### Headline Pooled Results")
    A()
    A("| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    head_tac = tac_res["headline"]
    for m_key, m_label in [("markov", "Markov"), ("frequency", "Frequency"), ("markov_fallback", "Markov Fallback")]:
        row = head_tac[m_key]
        w1 = f"[{row['wilson95_top1'][0]:.4f}, {row['wilson95_top1'][1]:.4f}]"
        w3 = f"[{row['wilson95_top3'][0]:.4f}, {row['wilson95_top3'][1]:.4f}]"
        A(f"| {m_label:15s} | {row['hit1']:2d} / 76 | {row['top1']:.4f} | {w1:21s} | {row['hit3']:2d} / 76 | {row['top3']:.4f} | {w3:21s} | {row['fold_mean_top1']:.4f} | {row['fold_mean_top3']:.4f} |")

    # Random guess reference
    rg = tac_res["diagnostics"]["random_guess"]
    A(f"| Random (k=1,3)  |  --  / 76 | {rg['mean_p_hit1']:.4f} | [Expected Reference]  |  --  / 76 | {rg['mean_p_hit3']:.4f} | [Expected Reference]  |   --   |   --   |")

    A()
    A(f"- **Coverage (Markov Status ok)**: {tac_res['coverage']['covered_samples']}/76 ({tac_res['coverage']['coverage_rate']:.4f}).")
    A(f"- **Target Ceiling**: {tac_res['ceiling']['hits']}/76 ({tac_res['ceiling']['ceiling_rate']:.4f}).")
    A()
    A("### Per-Fold Breakdown")
    A()
    A("| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for fid, f_data in sorted(tac_res["per_fold"].items(), key=lambda x: int(x[0].split("_")[1])):
        tep = f_data["test_episode"]
        fn = f_data["n_samples"]
        m_h1 = f_data["markov"]["hit1"]
        m_h3 = f_data["markov"]["hit3"]
        f_h1 = f_data["frequency"]["hit1"]
        f_h3 = f_data["frequency"]["hit3"]
        fb_h1 = f_data["fallback"]["hit1"]
        fb_h3 = f_data["fallback"]["hit3"]
        cov = f_data["covered_samples"]
        ceil = f_data["ceiling_hits"]
        A(f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({f_data['markov']['top1']:.4f}) | {m_h3:2d} ({f_data['markov']['top3']:.4f}) | {f_h1:2d} ({f_data['frequency']['top1']:.4f}) | {f_h3:2d} ({f_data['frequency']['top3']:.4f}) | {fb_h1:2d} ({f_data['fallback']['top1']:.4f}) | {fb_h3:2d} ({f_data['fallback']['top3']:.4f}) | {cov:2d} / {fn:2d} | {ceil:2d} / {fn:2d} |")

    A()
    A("---")
    A()
    A("## 4. Reference Slice: Technique `raw_full` (N=131)")
    A()
    A("### Headline Pooled Results")
    A()
    A("| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    head_raw = tech_raw_res["headline"]
    for m_key, m_label in [("markov", "Markov"), ("frequency", "Frequency"), ("fallback", "Markov Fallback")]:
        row = head_raw[m_key]
        w1 = f"[{row['wilson95_top1'][0]:.4f}, {row['wilson95_top1'][1]:.4f}]"
        w3 = f"[{row['wilson95_top3'][0]:.4f}, {row['wilson95_top3'][1]:.4f}]"
        A(f"| {m_label:15s} | {row['hit1']:2d} / 131 | {row['top1']:.4f} | {w1:21s} | {row['hit3']:2d} / 131 | {row['top3']:.4f} | {w3:21s} | {row['fold_mean_top1']:.4f} | {row['fold_mean_top3']:.4f} |")

    A()
    A(f"- **Coverage (Markov Status ok)**: {head_raw['coverage']['covered_samples']}/131 ({head_raw['coverage']['coverage_rate']:.4f}).")
    A(f"- **Target Ceiling**: {head_raw['ceiling']['hits']}/131 ({head_raw['ceiling']['ceiling_rate']:.4f}).")
    A()
    A("### Per-Fold Breakdown")
    A()
    A("| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

    for fid, f_data in sorted(tech_raw_res["per_fold"].items(), key=lambda x: int(x[0].split("_")[1])):
        tep = f_data["test_episode"]
        fn = f_data["n_samples"]
        m_h1 = f_data["markov"]["hit1"]
        m_h3 = f_data["markov"]["hit3"]
        f_h1 = f_data["frequency"]["hit1"]
        f_h3 = f_data["frequency"]["hit3"]
        fb_h1 = f_data["fallback"]["hit1"]
        fb_h3 = f_data["fallback"]["hit3"]
        cov = f_data["markov"]["covered_samples"]
        ceil = f_data["ceiling"]["hits"]
        A(f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({f_data['markov']['top1']:.4f}) | {m_h3:2d} ({f_data['markov']['top3']:.4f}) | {f_h1:2d} ({f_data['frequency']['top1']:.4f}) | {f_h3:2d} ({f_data['frequency']['top3']:.4f}) | {fb_h1:2d} ({f_data['fallback']['top1']:.4f}) | {fb_h3:2d} ({f_data['fallback']['top3']:.4f}) | {cov:2d} / {fn:2d} | {ceil:2d} / {fn:2d} |")

    A()
    A("---")
    A()
    A("## 5. Pre-Registered Paired Comparisons (P1, P2) and Non-Primary Tests")
    A()
    A("Per `reports/prereg_7episode_design.md` Section 6, the paired comparisons between `MarkovModel` and `FrequencyBaseline` are evaluated using exact two-sided McNemar tests on per-sample binary hit outcomes:")
    A()

    # P1 Table
    p1 = paired_tests["P1_tactic_collapsed_hit3"]
    t1 = p1["table"]
    A("### P1: Secondary Slice (`tactic_collapsed`), Hit@3 (Markov vs Frequency)")
    A()
    A("| Contingency Cell | Count | Interpretation |")
    A("|:---|:---:|:---|")
    A(f"| Both Hit ($a$) | {t1['both_hit']:2d} | Both models predicted a correct tactic in top-3 |")
    A(f"| Markov Only ($b$) | {t1['b_m1_only']:2d} | Markov predicted correct in top-3, Frequency missed |")
    A(f"| Frequency Only ($c$) | {t1['c_m2_only']:2d} | Frequency predicted correct in top-3, Markov missed |")
    A(f"| Neither Hit ($d$) | {t1['neither']:2d} | Neither model predicted a correct tactic in top-3 |")
    A()
    A(f"- **Sample Size**: $N = {p1['n_samples']}$")
    A(f"- **Markov Pooled Rate**: {p1['m1_rate']:.4f} ({p1['m1_rate']*p1['n_samples']:.0f}/{p1['n_samples']})")
    A(f"- **Frequency Pooled Rate**: {p1['m2_rate']:.4f} ({p1['m2_rate']*p1['n_samples']:.0f}/{p1['n_samples']})")
    A(f"- **Pooled Rate Difference (Markov - Frequency)**: {p1['rate_difference']:+.4f}")
    A(f"- **Discordant Counts**: $b = {t1['b_m1_only']}$, $c = {t1['c_m2_only']}$")
    A(f"- **Exact Two-Sided McNemar Test**: $p = {p1['p_value_raw']:.4f}$ (raw p, pre-Holm)")
    A()

    # P2 Table
    p2 = paired_tests["P2_technique_collapsed_full_hit3"]
    t2 = p2["table"]
    A("### P2: Primary Slice (`collapsed_full`), Hit@3 (Markov vs Frequency)")
    A()
    A("| Contingency Cell | Count | Interpretation |")
    A("|:---|:---:|:---|")
    A(f"| Both Hit ($a$) | {t2['both_hit']:2d} | Both models predicted a correct technique in top-3 |")
    A(f"| Markov Only ($b$) | {t2['b_m1_only']:2d} | Markov predicted correct in top-3, Frequency missed |")
    A(f"| Frequency Only ($c$) | {t2['c_m2_only']:2d} | Frequency predicted correct in top-3, Markov missed |")
    A(f"| Neither Hit ($d$) | {t2['neither']:2d} | Neither model predicted a correct technique in top-3 |")
    A()
    A(f"- **Sample Size**: $N = {p2['n_samples']}$")
    A(f"- **Markov Pooled Rate**: {p2['m1_rate']:.4f} ({p2['m1_rate']*p2['n_samples']:.0f}/{p2['n_samples']})")
    A(f"- **Frequency Pooled Rate**: {p2['m2_rate']:.4f} ({p2['m2_rate']*p2['n_samples']:.0f}/{p2['n_samples']})")
    A(f"- **Pooled Rate Difference (Markov - Frequency)**: {p2['rate_difference']:+.4f}")
    A(f"- **Discordant Counts**: $b = {t2['b_m1_only']}$, $c = {t2['c_m2_only']}$")
    A(f"- **Exact Two-Sided McNemar Test**: $p = {p2['p_value_raw']:.4f}$ (raw p, pre-Holm)")
    A()

    # Non-primary table
    A("### Non-Primary Descriptive Paired Comparisons (raw p, pre-Holm)")
    A()
    A("| Comparison | Slice | Metric | Model 1 Rate | Model 2 Rate | Difference | b | c | Exact McNemar p | Label |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|")
    desc_keys = [
        ("descriptive_technique_collapsed_full_hit1", "Markov vs Frequency", "collapsed_full", "Hit@1"),
        ("descriptive_tactic_collapsed_hit1", "Markov vs Frequency", "tactic_collapsed", "Hit@1"),
        ("descriptive_technique_fallback_vs_freq_hit3", "Fallback vs Frequency", "collapsed_full", "Hit@3"),
        ("descriptive_technique_fallback_vs_freq_hit1", "Fallback vs Frequency", "collapsed_full", "Hit@1"),
        ("descriptive_tactic_fallback_vs_freq_hit3", "Fallback vs Frequency", "tactic_collapsed", "Hit@3"),
        ("descriptive_tactic_fallback_vs_freq_hit1", "Fallback vs Frequency", "tactic_collapsed", "Hit@1"),
    ]
    for k_test, comp_label, sl_label, met_label in desc_keys:
        pt = paired_tests[k_test]
        tt = pt["table"]
        A(f"| {comp_label:23s} | {sl_label:16s} | {met_label:5s} | {pt['m1_rate']:.4f} | {pt['m2_rate']:.4f} | {pt['rate_difference']:+.4f} | {tt['b_m1_only']:2d} | {tt['c_m2_only']:2d} | {pt['p_value_raw']:.4f} | raw p, pre-Holm |")

    A()
    A("---")
    A()
    A("## 6. Comparison with Archived 4-Episode Results")
    A()
    A("The following table compares the 7-episode results with the archived 4-episode baseline numbers read directly from `reports/evaluation_results.json` and `reports/tactic_evaluation_results.json`:")
    A()
    A("| Slice | Metric | 4-Episode Baseline (E1–E4) | 7-Episode Evaluation (E1–E7) | Absolute Change |")
    A("|:---|:---|:---:|:---:|:---:|")

    # Technique comparison rows
    c_tech = comparison_4ep["technique_collapsed_full"]
    c4_t = c_tech["4ep"]
    c7_t = c_tech["7ep"]
    A(f"| Technique (`collapsed_full`) | Sample Count ($N$) | {c4_t['n_samples']} | {c7_t['n_samples']} | +{c7_t['n_samples'] - c4_t['n_samples']} |")
    A(f"| Technique (`collapsed_full`) | Markov Hit@1 | {c4_t['markov_hit1']}/{c4_t['n_samples']} ({c4_t['markov_hit1']/c4_t['n_samples']:.4f}) | {c7_t['markov_hit1']}/{c7_t['n_samples']} ({c7_t['markov_hit1']/c7_t['n_samples']:.4f}) | {c7_t['markov_hit1']/c7_t['n_samples'] - c4_t['markov_hit1']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Markov Hit@3 | {c4_t['markov_hit3']}/{c4_t['n_samples']} ({c4_t['markov_hit3']/c4_t['n_samples']:.4f}) | {c7_t['markov_hit3']}/{c7_t['n_samples']} ({c7_t['markov_hit3']/c7_t['n_samples']:.4f}) | {c7_t['markov_hit3']/c7_t['n_samples'] - c4_t['markov_hit3']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Frequency Hit@1 | {c4_t['frequency_hit1']}/{c4_t['n_samples']} ({c4_t['frequency_hit1']/c4_t['n_samples']:.4f}) | {c7_t['frequency_hit1']}/{c7_t['n_samples']} ({c7_t['frequency_hit1']/c7_t['n_samples']:.4f}) | {c7_t['frequency_hit1']/c7_t['n_samples'] - c4_t['frequency_hit1']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Frequency Hit@3 | {c4_t['frequency_hit3']}/{c4_t['n_samples']} ({c4_t['frequency_hit3']/c4_t['n_samples']:.4f}) | {c7_t['frequency_hit3']}/{c7_t['n_samples']} ({c7_t['frequency_hit3']/c7_t['n_samples']:.4f}) | {c7_t['frequency_hit3']/c7_t['n_samples'] - c4_t['frequency_hit3']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Markov Fallback Hit@1 | {c4_t['fallback_hit1']}/{c4_t['n_samples']} ({c4_t['fallback_hit1']/c4_t['n_samples']:.4f}) | {c7_t['fallback_hit1']}/{c7_t['n_samples']} ({c7_t['fallback_hit1']/c7_t['n_samples']:.4f}) | {c7_t['fallback_hit1']/c7_t['n_samples'] - c4_t['fallback_hit1']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Markov Fallback Hit@3 | {c4_t['fallback_hit3']}/{c4_t['n_samples']} ({c4_t['fallback_hit3']/c4_t['n_samples']:.4f}) | {c7_t['fallback_hit3']}/{c7_t['n_samples']} ({c7_t['fallback_hit3']/c7_t['n_samples']:.4f}) | {c7_t['fallback_hit3']/c7_t['n_samples'] - c4_t['fallback_hit3']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Coverage (Status ok) | {c4_t['coverage_covered']}/{c4_t['n_samples']} ({c4_t['coverage_covered']/c4_t['n_samples']:.4f}) | {c7_t['coverage_covered']}/{c7_t['n_samples']} ({c7_t['coverage_covered']/c7_t['n_samples']:.4f}) | {c7_t['coverage_covered']/c7_t['n_samples'] - c4_t['coverage_covered']/c4_t['n_samples']:+.4f} |")
    A(f"| Technique (`collapsed_full`) | Target Ceiling | {c4_t['ceiling_hits']}/{c4_t['n_samples']} ({c4_t['ceiling_hits']/c4_t['n_samples']:.4f}) | {c7_t['ceiling_hits']}/{c7_t['n_samples']} ({c7_t['ceiling_hits']/c7_t['n_samples']:.4f}) | {c7_t['ceiling_hits']/c7_t['n_samples'] - c4_t['ceiling_hits']/c4_t['n_samples']:+.4f} |")

    # Tactic comparison rows
    c_tac = comparison_4ep["tactic_collapsed"]
    c4_a = c_tac["4ep"]
    c7_a = c_tac["7ep"]
    A(f"| Tactic (`tactic_collapsed`) | Sample Count ($N$) | {c4_a['n_samples']} | {c7_a['n_samples']} | +{c7_a['n_samples'] - c4_a['n_samples']} |")
    A(f"| Tactic (`tactic_collapsed`) | Markov Hit@1 | {c4_a['markov_hit1']}/{c4_a['n_samples']} ({c4_a['markov_hit1']/c4_a['n_samples']:.4f}) | {c7_a['markov_hit1']}/{c7_a['n_samples']} ({c7_a['markov_hit1']/c7_a['n_samples']:.4f}) | {c7_a['markov_hit1']/c7_a['n_samples'] - c4_a['markov_hit1']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Markov Hit@3 | {c4_a['markov_hit3']}/{c4_a['n_samples']} ({c4_a['markov_hit3']/c4_a['n_samples']:.4f}) | {c7_a['markov_hit3']}/{c7_a['n_samples']} ({c7_a['markov_hit3']/c7_a['n_samples']:.4f}) | {c7_a['markov_hit3']/c7_a['n_samples'] - c4_a['markov_hit3']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Frequency Hit@1 | {c4_a['frequency_hit1']}/{c4_a['n_samples']} ({c4_a['frequency_hit1']/c4_a['n_samples']:.4f}) | {c7_a['frequency_hit1']}/{c7_a['n_samples']} ({c7_a['frequency_hit1']/c7_a['n_samples']:.4f}) | {c7_a['frequency_hit1']/c7_a['n_samples'] - c4_a['frequency_hit1']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Frequency Hit@3 | {c4_a['frequency_hit3']}/{c4_a['n_samples']} ({c4_a['frequency_hit3']/c4_a['n_samples']:.4f}) | {c7_a['frequency_hit3']}/{c7_a['n_samples']} ({c7_a['frequency_hit3']/c7_a['n_samples']:.4f}) | {c7_a['frequency_hit3']/c7_a['n_samples'] - c4_a['frequency_hit3']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Markov Fallback Hit@1 | {c4_a['fallback_hit1']}/{c4_a['n_samples']} ({c4_a['fallback_hit1']/c4_a['n_samples']:.4f}) | {c7_a['fallback_hit1']}/{c7_a['n_samples']} ({c7_a['fallback_hit1']/c7_a['n_samples']:.4f}) | {c7_a['fallback_hit1']/c7_a['n_samples'] - c4_a['fallback_hit1']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Markov Fallback Hit@3 | {c4_a['fallback_hit3']}/{c4_a['n_samples']} ({c4_a['fallback_hit3']/c4_a['n_samples']:.4f}) | {c7_a['fallback_hit3']}/{c7_a['n_samples']} ({c7_a['fallback_hit3']/c7_a['n_samples']:.4f}) | {c7_a['fallback_hit3']/c7_a['n_samples'] - c4_a['fallback_hit3']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Coverage (Status ok) | {c4_a['coverage_covered']}/{c4_a['n_samples']} ({c4_a['coverage_covered']/c4_a['n_samples']:.4f}) | {c7_a['coverage_covered']}/{c7_a['n_samples']} ({c7_a['coverage_covered']/c7_a['n_samples']:.4f}) | {c7_a['coverage_covered']/c7_a['n_samples'] - c4_a['coverage_covered']/c4_a['n_samples']:+.4f} |")
    A(f"| Tactic (`tactic_collapsed`) | Target Ceiling | {c4_a['ceiling_hits']}/{c4_a['n_samples']} ({c4_a['ceiling_hits']/c4_a['n_samples']:.4f}) | {c7_a['ceiling_hits']}/{c7_a['n_samples']} ({c7_a['ceiling_hits']/c7_a['n_samples']:.4f}) | {c7_a['ceiling_hits']/c7_a['n_samples'] - c4_a['ceiling_hits']/c4_a['n_samples']:+.4f} |")

    A()
    A("---")
    A()
    A("## 7. Code-Generated Conclusion Summary")
    A()
    A("The following observational statements are generated strictly from the evaluation numbers without causal claims:")
    A(f"- **Primary Hypothesis P2 (Technique `collapsed_full` Hit@3)**: Markov achieved {p2['m1_rate']:.4f} ({p2['table']['both_hit'] + p2['table']['b_m1_only']}/{p2['n_samples']}) versus Frequency {p2['m2_rate']:.4f} ({p2['table']['both_hit'] + p2['table']['c_m2_only']}/{p2['n_samples']}), yielding pooled difference {p2['rate_difference']:+.4f} (discordant pairs: b={t2['b_m1_only']}, c={t2['c_m2_only']}, raw p={p2['p_value_raw']:.4f}).")
    A(f"- **Secondary Hypothesis P1 (Tactic `tactic_collapsed` Hit@3)**: Markov achieved {p1['m1_rate']:.4f} ({p1['table']['both_hit'] + p1['table']['b_m1_only']}/{p1['n_samples']}) versus Frequency {p1['m2_rate']:.4f} ({p1['table']['both_hit'] + p1['table']['c_m2_only']}/{p1['n_samples']}), yielding pooled difference {p1['rate_difference']:+.4f} (discordant pairs: b={t1['b_m1_only']}, c={t1['c_m2_only']}, raw p={p1['p_value_raw']:.4f}).")
    A(f"- **Sample Expansion**: Expanding from 4 to 7 episodes increased evaluated technique transition samples from 67 to 95 (+28 samples) and tactic transition samples from 53 to 76 (+23 samples).")
    A("- **Claim Rule Boundary**: Per pre-registration protocol, substantive claims of improvement or order-signal presence are governed by the joint P1–P4 criteria and Holm adjustment evaluated after permutation testing (Prompt 12b).")
    A()

    with open(REPORT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
    print(f"Report Markdown written to {REPORT_MD_PATH}")

    return results_7ep


if __name__ == "__main__":
    run_evaluation_7ep()
