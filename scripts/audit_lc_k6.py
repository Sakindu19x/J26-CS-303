#!/usr/bin/env python3
"""Audit learning curve k=6 aggregation vs evaluation_7ep_results.json for Prompt 13 P1.5."""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    print("=" * 80)
    print("LEARNING CURVE k=6 AGGREGATION AUDIT (1.5)")
    print("=" * 80)

    eval_json_path = REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json"
    lc_json_path = REPO_ROOT / "reports" / "7ep" / "learning_curve_7ep_results.json"

    eval_d = json.loads(eval_json_path.read_text(encoding="utf-8"))
    lc_d = json.loads(lc_json_path.read_text(encoding="utf-8"))

    slices = [
        ("technique_collapsed_full", "primary_slice_technique_collapsed_full"),
        ("tactic_collapsed", "secondary_slice_tactic_collapsed"),
    ]

    all_diffs_zero = True

    for sl_name, sl_key in slices:
        print(f"\n=======================================================")
        print(f"Slice: {sl_name}")
        print(f"=======================================================")

        per_fold = eval_d[sl_key]["per_fold"]
        folds = [per_fold[f"fold_{i}"] for i in range(1, 8)]
        n_tot = sum(f["n_samples"] for f in folds)

        if sl_name == "technique_collapsed_full":
            cov_fold_vals = [f["markov"]["coverage"] for f in folds]
            cov_pool_val = sum(f["markov"]["covered_samples"] for f in folds) / n_tot
            ceil_fold_vals = [f["ceiling"]["rate"] for f in folds]
            ceil_pool_val = sum(f["ceiling"]["hits"] for f in folds) / n_tot
        else:
            cov_fold_vals = [f["covered_samples"] / f["n_samples"] for f in folds]
            cov_pool_val = sum(f["covered_samples"] for f in folds) / n_tot
            ceil_fold_vals = [f["ceiling_hits"] / f["n_samples"] for f in folds]
            ceil_pool_val = sum(f["ceiling_hits"] for f in folds) / n_tot

        eval_metrics = {
            "markov_hit1": ([f["markov"]["top1"] for f in folds], sum(f["markov"]["hit1"] for f in folds) / n_tot),
            "markov_hit3": ([f["markov"]["top3"] for f in folds], sum(f["markov"]["hit3"] for f in folds) / n_tot),
            "frequency_hit1": ([f["frequency"]["top1"] for f in folds], sum(f["frequency"]["hit1"] for f in folds) / n_tot),
            "frequency_hit3": ([f["frequency"]["top3"] for f in folds], sum(f["frequency"]["hit3"] for f in folds) / n_tot),
            "markov_fallback_hit1": ([f["fallback"]["top1"] for f in folds], sum(f["fallback"]["hit1"] for f in folds) / n_tot),
            "markov_fallback_hit3": ([f["fallback"]["top3"] for f in folds], sum(f["fallback"]["hit3"] for f in folds) / n_tot),
            "coverage": (cov_fold_vals, cov_pool_val),
            "ceiling": (ceil_fold_vals, ceil_pool_val),
        }

        k6 = lc_d["learning_curve"][sl_name]["k_6"]
        unw = k6["unweighted_episode_mean"]
        pw = k6["pooled_sample_weighted"]

        print(f"\n| Metric Column | LC k=6 Ep-Mean | Eval Fold-Mean | Abs Diff (Ep-Mean) | LC k=6 Pooled | Eval Pooled | Abs Diff (Pooled) | < 1e-9? |")
        print(f"|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

        for m_name, (fold_vals, pool_val) in eval_metrics.items():
            eval_fold_mean = sum(fold_vals) / 7.0
            lc_ep_mean = unw[m_name]
            diff_ep = abs(lc_ep_mean - eval_fold_mean)

            lc_pooled = pw[m_name]
            diff_pw = abs(lc_pooled - pool_val)

            passes = (diff_ep < 1e-9) and (diff_pw < 1e-9)
            if not passes:
                all_diffs_zero = False

            print(
                f"| {m_name:<20} | {lc_ep_mean:.10f} | {eval_fold_mean:.10f} | {diff_ep:.2e} | "
                f"{lc_pooled:.10f} | {pool_val:.10f} | {diff_pw:.2e} | **{passes}** |"
            )
            assert diff_ep < 1e-9, f"Episode-mean difference >= 1e-9 for {m_name}: {diff_ep}"
            assert diff_pw < 1e-9, f"Sample-weighted difference >= 1e-9 for {m_name}: {diff_pw}"

    print("\nAssertion passed: all learning curve k=6 values equal evaluation_7ep_results.json within < 1e-9.")


if __name__ == "__main__":
    main()
