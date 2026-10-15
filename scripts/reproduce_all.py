"""One-command full reproduction and verification script (P9, G6).

Supported modes:
  --verify-only : Re-runs all deterministic verifiers, the pytest suite, and verify_all_hashes without mutating data.
  --rebuild     : Re-runs the entire pipeline from raw archives to all outputs, then asserts baseline hash parity.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable

VERIFIERS = [
    ("Hash Verification (All Baselines)", [PYTHON, "scripts/verify_all_hashes.py"]),
    ("Stage 1 7-Episode Verifier", [PYTHON, "scripts/verify_stage1_7ep.py"]),
    ("Stage 2 7-Episode Evaluation Verifier", [PYTHON, "scripts/verify_evaluation_7ep.py"]),
    ("Explainable Prediction Records Verifier", [PYTHON, "scripts/verify_prediction_records.py"]),
    ("Learning Curve Verifier", [PYTHON, "scripts/verify_learning_curve_7ep.py"]),
    ("Permutation Order Test Verifier", [PYTHON, "scripts/verify_permutation_7ep.py"]),
    ("Planted Structure Power Analysis Verifier", [PYTHON, "scripts/verify_planted_realscale_7ep.py"]),
    ("E5-Removed Ablation Verifier", [PYTHON, "scripts/verify_e5_removed.py"]),
    ("E5 Hit@1 Diagnostic Verifier", [PYTHON, "scripts/verify_e5_hit1_diagnostic.py"]),
    ("Tie Sensitivity Diagnostic Verifier", [PYTHON, "scripts/verify_tie_sensitivity_7ep.py"]),
    ("Exploratory Tactic-Conditioned Verifier", [PYTHON, "scripts/verify_exploratory_tactic_conditioned.py"]),
    ("Holm Claim Rule Verifier", [PYTHON, "scripts/verify_holm_claim_rule.py"]),
    ("Viva Pack Verifier", [PYTHON, "scripts/verify_viva_pack.py"]),
    ("Pytest Suite (Full Regression)", [PYTHON, "-m", "pytest", "-q"]),
]

PIPELINE_STEPS = [
    ("1. Stage 1 Ingestion (7 Episodes)", [PYTHON, "scripts/run_stage1_pipeline_7ep.py"]),
    ("2. LOEO Model Training & Evaluation", [PYTHON, "scripts/run_7ep_evaluation.py"]),
    ("3. Inference & Diagnostics Suite", [PYTHON, "scripts/run_inference_7ep.py"]),
    ("4. Production Model Fitting", [PYTHON, "scripts/train_production_model.py"]),
    ("5. Explainable Prediction Records Build", [PYTHON, "scripts/build_prediction_records.py"]),
    ("6. Requirements Trace Generation", [PYTHON, "scripts/build_requirements_trace.py"]),
    ("7. Viva Pack Generation", [PYTHON, "scripts/build_viva_pack.py"]),
    ("8. Baseline Hash Verification", [PYTHON, "scripts/verify_all_hashes.py"]),
]


def run_verify_only() -> int:
    print("================================================================================")
    print("   COMPONENT 4 ONE-COMMAND REPRODUCTION: VERIFY-ONLY MODE")
    print("================================================================================")
    print(f"Repository Root : {REPO_ROOT}")
    print(f"Python Runtime  : {PYTHON}\n")

    t_start = time.perf_counter()
    failures = []

    for name, cmd in VERIFIERS:
        print(f"[*] Running: {name}...")
        t0 = time.perf_counter()
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        elapsed = time.perf_counter() - t0
        if res.returncode == 0:
            print(f"    -> [PASS] ({elapsed:.2f}s)")
        else:
            print(f"    -> [FAIL] (exit code {res.returncode}, {elapsed:.2f}s)")
            print("--- STDOUT ---")
            print(res.stdout[-1000:] if len(res.stdout) > 1000 else res.stdout)
            print("--- STDERR ---")
            print(res.stderr[-1000:] if len(res.stderr) > 1000 else res.stderr)
            failures.append((name, res.returncode))

    total_elapsed = time.perf_counter() - t_start
    print("\n================================================================================")
    if not failures:
        print(f"ALL {len(VERIFIERS)} VERIFICATION CHECKS PASSED PERFECTLY ({total_elapsed:.2f}s)")
        print("Status: REPRODUCIBILITY VERIFIED (100% compliant with baselines)")
        print("================================================================================")
        return 0
    else:
        print(f"VERIFICATION FAILED: {len(failures)}/{len(VERIFIERS)} checks failed ({total_elapsed:.2f}s)")
        for name, code in failures:
            print(f"  - {name} (exit code {code})")
        print("================================================================================")
        return 1


def run_rebuild() -> int:
    print("================================================================================")
    print("   COMPONENT 4 ONE-COMMAND REPRODUCTION: REBUILD PIPELINE MODE")
    print("================================================================================")
    print(f"Repository Root : {REPO_ROOT}")
    print(f"Python Runtime  : {PYTHON}\n")

    t_start = time.perf_counter()

    for step_name, cmd in PIPELINE_STEPS:
        print(f"[*] Executing {step_name}...")
        t0 = time.perf_counter()
        res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
        elapsed = time.perf_counter() - t0
        if res.returncode != 0:
            print(f"\n[!] Pipeline step failed at: {step_name} (exit code {res.returncode})")
            print("--- STDOUT ---")
            print(res.stdout[-1500:] if len(res.stdout) > 1500 else res.stdout)
            print("--- STDERR ---")
            print(res.stderr[-1500:] if len(res.stderr) > 1500 else res.stderr)
            return res.returncode
        print(f"    -> [DONE] ({elapsed:.2f}s)")

    total_elapsed = time.perf_counter() - t_start
    print("\n================================================================================")
    print(f"PIPELINE REBUILD COMPLETE AND ALL BASELINES MATCH EXACTLY ({total_elapsed:.2f}s)")
    print("================================================================================")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Component 4 Reproduction Runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--verify-only", action="store_true", help="Re-run verifiers and test suite without regenerating data")
    group.add_argument("--rebuild", action="store_true", help="Rebuild entire pipeline from raw data and assert baseline parity")

    args = parser.parse_args()

    if args.verify_only:
        code = run_verify_only()
        sys.exit(code)
    elif args.rebuild:
        code = run_rebuild()
        sys.exit(code)


if __name__ == "__main__":
    main()
