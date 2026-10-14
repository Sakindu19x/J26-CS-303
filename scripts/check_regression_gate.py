"""Regression gate script to verify 4-episode baseline reproduction.

Runs evaluation on 4-episode data (data/processed) into a scratch dir,
compares metrics and predictions with frozen files:
  - technique collapsed_full:
      Markov 1/67 and 2/67
      Frequency 4/67 and 8/67
      fallback 2/67 and 5/67
      coverage 34/67
      ceiling 35/67
  - tactic_collapsed (N=53):
      Markov 11/53 and 28/53
      Frequency 9/53 and 33/53
      fallback 13/53 and 30/53
  - per-sample predictions equal the rows of evaluation_predictions.csv
    and tactic_evaluation_predictions.csv for all shared columns.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from src.c4.evaluation import evaluate_loeo_slice
from src.c4.tactic_evaluation import evaluate_tactic_slice

DATA_4EP = BASE_DIR / "data" / "processed"
SCRATCH_DIR = BASE_DIR / "scratch_regression_gate"


def run_regression_gate() -> bool:
    print("================================================================================")
    print("RUNNING 4-EPISODE REGRESSION GATE")
    print("================================================================================")

    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)
    all_passed = True

    try:
        with open(DATA_4EP / "attack_sequences.json", "r", encoding="utf-8") as f:
            seqs4 = json.load(f)
        with open(DATA_4EP / "loeo_folds.json", "r", encoding="utf-8") as f:
            folds4 = json.load(f)
        with open(DATA_4EP / "next_technique_samples.json", "r", encoding="utf-8") as f:
            samples4 = json.load(f)

        cf_samples = [s for s in samples4 if s["variant"] == "collapsed" and s["granularity"] == "full"]

        # Run technique collapsed_full
        tech_res, tech_rows = evaluate_loeo_slice(
            variant="collapsed",
            granularity="full",
            save_fold_models=False,
            sequences_data=seqs4,
            folds_data=folds4,
            samples_data=cf_samples,
        )

        # Run tactic tactic_collapsed
        tac_res, tac_rows = evaluate_tactic_slice(
            variant="tactic_collapsed",
            sequences_data=seqs4,
            folds_data=folds4,
        )

        # 1. Technique checks
        t_head = tech_res["headline"]
        n_tech = tech_res["n_samples"]
        checks = [
            ("technique collapsed_full N=67", n_tech == 67, f"N={n_tech}"),
            ("technique Markov Hit@1 == 1/67", t_head["markov"]["hit1"] == 1, f"hit1={t_head['markov']['hit1']}"),
            ("technique Markov Hit@3 == 2/67", t_head["markov"]["hit3"] == 2, f"hit3={t_head['markov']['hit3']}"),
            ("technique Frequency Hit@1 == 4/67", t_head["frequency"]["hit1"] == 4, f"hit1={t_head['frequency']['hit1']}"),
            ("technique Frequency Hit@3 == 8/67", t_head["frequency"]["hit3"] == 8, f"hit3={t_head['frequency']['hit3']}"),
            ("technique Fallback Hit@1 == 2/67", t_head["fallback"]["hit1"] == 2, f"hit1={t_head['fallback']['hit1']}"),
            ("technique Fallback Hit@3 == 5/67", t_head["fallback"]["hit3"] == 5, f"hit3={t_head['fallback']['hit3']}"),
            ("technique Coverage == 34/67", t_head["coverage"]["covered_samples"] == 34, f"covered={t_head['coverage']['covered_samples']}"),
            ("technique Ceiling == 35/67", t_head["ceiling"]["hits"] == 35, f"ceiling={t_head['ceiling']['hits']}"),
        ]

        # 2. Tactic checks
        a_head = tac_res["headline"]
        n_tac = tac_res["n_samples"]
        checks.extend([
            ("tactic tactic_collapsed N=53", n_tac == 53, f"N={n_tac}"),
            ("tactic Markov Hit@1 == 11/53", a_head["markov"]["hit1"] == 11, f"hit1={a_head['markov']['hit1']}"),
            ("tactic Markov Hit@3 == 28/53", a_head["markov"]["hit3"] == 28, f"hit3={a_head['markov']['hit3']}"),
            ("tactic Frequency Hit@1 == 9/53", a_head["frequency"]["hit1"] == 9, f"hit1={a_head['frequency']['hit1']}"),
            ("tactic Frequency Hit@3 == 33/53", a_head["frequency"]["hit3"] == 33, f"hit3={a_head['frequency']['hit3']}"),
            ("tactic Fallback Hit@1 == 13/53", a_head["markov_fallback"]["hit1"] == 13, f"hit1={a_head['markov_fallback']['hit1']}"),
            ("tactic Fallback Hit@3 == 30/53", a_head["markov_fallback"]["hit3"] == 30, f"hit3={a_head['markov_fallback']['hit3']}"),
        ])

        print("\n--- Summary Metric Verification ---")
        for desc, passed, actual in checks:
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {desc} ({actual})")
            if not passed:
                all_passed = False

        # 3. Row-by-row prediction comparison
        print("\n--- Per-Sample Predictions Verification (Shared Columns) ---")
        df_runner_tech = pd.DataFrame(tech_rows)
        df_frozen_tech = pd.read_csv(DATA_4EP / "evaluation_predictions.csv")
        df_frozen_tech = df_frozen_tech[df_frozen_tech["configuration"] == "collapsed_full"].reset_index(drop=True)

        shared_cols = ["sample_id", "method", "status", "hit1", "hit3", "predicted_candidates_top3"]
        tech_row_match = True
        for col in shared_cols:
            col_match = (df_runner_tech[col].astype(str) == df_frozen_tech[col].astype(str)).all()
            print(f"[{'PASS' if col_match else 'FAIL'}] technique shared column '{col}' exact match")
            if not col_match:
                tech_row_match = False
                all_passed = False

        df_runner_tac = pd.DataFrame(tac_rows)
        df_frozen_tac = pd.read_csv(DATA_4EP / "tactic_evaluation_predictions.csv")
        df_frozen_tac = df_frozen_tac[df_frozen_tac["configuration"] == "tactic_collapsed"].reset_index(drop=True)

        tac_row_match = True
        for col in shared_cols:
            col_match = (df_runner_tac[col].astype(str) == df_frozen_tac[col].astype(str)).all()
            print(f"[{'PASS' if col_match else 'FAIL'}] tactic shared column '{col}' exact match")
            if not col_match:
                tac_row_match = False
                all_passed = False

    finally:
        if SCRATCH_DIR.exists():
            shutil.rmtree(SCRATCH_DIR)

    print("\n================================================================================")
    print(f"REGRESSION GATE OVERALL RESULT: {'PASS' if all_passed else 'FAIL'}")
    print("================================================================================")
    return all_passed


if __name__ == "__main__":
    success = run_regression_gate()
    sys.exit(0 if success else 1)
