"""Independent verification script for LOEO evaluation metrics (Historical / Dev).

NOTE: This script is SUPERSEDED by scripts/verify_evaluation.py, which provides
comprehensive, independent verification across all five configurations, all metrics,
2x2 paired tests, frequency splits, support buckets, tie diagnostics, concentration,
and full sequence/sample reconstruction checks.

Retained here in scripts/dev/ for historical reference and quick micro-metric sanity checks.
Reads ONLY data/processed/evaluation_predictions.csv and data/processed/next_technique_samples.json
and recomputes pooled Top-1, Top-3, coverage, and micro precision/recall/F1 for the primary slice,
confirming exact equality with reports/evaluation_results.json.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "data" / "processed" / "evaluation_predictions.csv"
SAMPLES_PATH = BASE_DIR / "data" / "processed" / "next_technique_samples.json"
RESULTS_JSON_PATH = BASE_DIR / "reports" / "evaluation_results.json"


def verify_independent() -> bool:
    # 1. Read predictions CSV
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Filter primary slice: configuration == 'collapsed_full'
    cf_rows = [r for r in rows if r["configuration"] == "collapsed_full"]
    m_rows = [r for r in cf_rows if r["method"] == "markov"]
    f_rows = [r for r in cf_rows if r["method"] == "frequency"]

    n_samples = len(m_rows)
    assert n_samples == 67, f"Expected 67 samples in collapsed_full, got {n_samples}"

    # Recompute Markov pooled Top-1, Top-3, coverage
    m_hit1_count = sum(int(r["hit1"]) for r in m_rows)
    m_hit3_count = sum(int(r["hit3"]) for r in m_rows)
    m_cov_count = sum(1 for r in m_rows if r["status"] == "ok")

    m_top1 = m_hit1_count / n_samples
    m_top3 = m_hit3_count / n_samples
    m_cov = m_cov_count / n_samples

    # Recompute Frequency pooled Top-1, Top-3
    f_hit1_count = sum(int(r["hit1"]) for r in f_rows)
    f_hit3_count = sum(int(r["hit3"]) for r in f_rows)
    f_top1 = f_hit1_count / n_samples
    f_top3 = f_hit3_count / n_samples

    # Recompute micro Precision/Recall/F1
    def calc_micro(method_rows: list[dict[str, str]], k: int) -> dict[str, float]:
        tp, fp, fn = 0, 0, 0
        for r in method_rows:
            tgt = set(json.loads(r["target_technique_set"]))
            status = r["status"]
            cands_raw = json.loads(r["predicted_candidates_top3"])
            if status == "ok" and cands_raw:
                preds = set([c[0] for c in cands_raw[:k]])
            else:
                preds = set()

            tp += len(preds & tgt)
            fp += len(preds - tgt)
            fn += len(tgt - preds)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2.0 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        return {"precision": prec, "recall": rec, "f1": f1, "tp": tp, "fp": fp, "fn": fn}

    m_t1_micro = calc_micro(m_rows, 1)
    m_t3_micro = calc_micro(m_rows, 3)
    f_t1_micro = calc_micro(f_rows, 1)
    f_t3_micro = calc_micro(f_rows, 3)

    # 2. Compare against reports/evaluation_results.json
    with open(RESULTS_JSON_PATH, encoding="utf-8") as f:
        res_json = json.load(f)

    prim_json = res_json["primary_slice"]
    head_json = prim_json["headline"]
    pr_json = prim_json["precision_recall_f1"]

    matches = []

    # Check headline Markov
    matches.append(("Markov Top-1", m_top1, head_json["markov"]["top1"]))
    matches.append(("Markov Top-3", m_top3, head_json["markov"]["top3"]))
    matches.append(("Markov Coverage", m_cov, head_json["coverage"]["coverage_rate"]))

    # Check headline Frequency
    matches.append(("Frequency Top-1", f_top1, head_json["frequency"]["top1"]))
    matches.append(("Frequency Top-3", f_top3, head_json["frequency"]["top3"]))

    # Check micro P/R/F1
    matches.append(("Markov Top-1 micro P", m_t1_micro["precision"], pr_json["markov_top1"]["micro"]["precision"]))
    matches.append(("Markov Top-1 micro R", m_t1_micro["recall"], pr_json["markov_top1"]["micro"]["recall"]))
    matches.append(("Markov Top-1 micro F1", m_t1_micro["f1"], pr_json["markov_top1"]["micro"]["f1"]))

    matches.append(("Markov Top-3 micro P", m_t3_micro["precision"], pr_json["markov_top3"]["micro"]["precision"]))
    matches.append(("Markov Top-3 micro R", m_t3_micro["recall"], pr_json["markov_top3"]["micro"]["recall"]))
    matches.append(("Markov Top-3 micro F1", m_t3_micro["f1"], pr_json["markov_top3"]["micro"]["f1"]))

    matches.append(("Freq Top-1 micro P", f_t1_micro["precision"], pr_json["frequency_top1"]["micro"]["precision"]))
    matches.append(("Freq Top-1 micro R", f_t1_micro["recall"], pr_json["frequency_top1"]["micro"]["recall"]))
    matches.append(("Freq Top-1 micro F1", f_t1_micro["f1"], pr_json["frequency_top1"]["micro"]["f1"]))

    matches.append(("Freq Top-3 micro P", f_t3_micro["precision"], pr_json["frequency_top3"]["micro"]["precision"]))
    matches.append(("Freq Top-3 micro R", f_t3_micro["recall"], pr_json["frequency_top3"]["micro"]["recall"]))
    matches.append(("Freq Top-3 micro F1", f_t3_micro["f1"], pr_json["frequency_top3"]["micro"]["f1"]))

    all_ok = True
    print(f"{'Metric':25s} {'Recomputed':15s} {'evaluation_results.json':25s} {'Match?'}")
    print("-" * 75)
    for name, recomputed, expected in matches:
        diff = abs(recomputed - expected)
        is_match = diff < 1e-9
        if not is_match:
            all_ok = False
        print(f"{name:25s} {recomputed:<15.6f} {expected:<25.6f} {is_match}")

    print("-" * 75)
    print(f"Independent Verification Result: {'ALL MATCH (PASS)' if all_ok else 'MISMATCH (FAIL)'}")
    return all_ok


if __name__ == "__main__":
    success = verify_independent()
    if not success:
        exit(1)
