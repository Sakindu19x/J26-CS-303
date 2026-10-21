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
    ("Hash Verification (All Baselines)", [PYTHON, "scripts/verify/verify_all_hashes.py"]),
    ("Stage 1 7-Episode Verifier", [PYTHON, "scripts/verify/verify_stage1_7ep.py"]),
    ("Stage 2 7-Episode Evaluation Verifier", [PYTHON, "scripts/verify/verify_evaluation_7ep.py"]),
    ("Explainable Prediction Records Verifier", [PYTHON, "scripts/verify/verify_prediction_records.py"]),
    ("Learning Curve Verifier", [PYTHON, "scripts/verify/verify_learning_curve_7ep.py"]),
    ("Permutation Order Test Verifier", [PYTHON, "scripts/verify_permutation_7ep.py"]),
    ("Planted Structure Power Analysis Verifier", [PYTHON, "scripts/verify/verify_planted_realscale_7ep.py"]),
    ("E5-Removed Ablation Verifier", [PYTHON, "scripts/verify/verify_e5_removed.py"]),
    ("E5 Hit@1 Diagnostic Verifier", [PYTHON, "scripts/verify/verify_e5_hit1_diagnostic.py"]),
    ("Tie Sensitivity Diagnostic Verifier", [PYTHON, "scripts/verify/verify_tie_sensitivity_7ep.py"]),
    ("Exploratory Tactic-Conditioned Verifier", [PYTHON, "scripts/verify/verify_exploratory_tactic_conditioned.py"]),
    ("Holm Claim Rule Verifier", [PYTHON, "scripts/verify/verify_holm_claim_rule.py"]),
    ("Viva Pack Verifier", [PYTHON, "scripts/verify/verify_viva_pack.py"]),
    ("Requirements Trace Verifier", [PYTHON, "scripts/verify/verify_requirements_trace.py"]),
    ("Claims Map Verifier", [PYTHON, "scripts/verify/verify_claims_map.py"]),
    ("Overnight Summary Verifier", [PYTHON, "scripts/verify/verify_overnight_summary.py"]),
    ("NFR1 Verifier", [PYTHON, "scripts/verify/verify_nfr1.py"]),
    ("Pytest Suite (Full Regression)", [PYTHON, "-m", "pytest", "-q"]),
]

PIPELINE_STEPS = [
    ("1. Stage 1 Normalization (4 Episodes)", [PYTHON, "scripts/pipeline/s01_normalize_events.py", "--episodes", "4", "--processed-dir", "data/processed", "--reports-dir", "reports"]),
    ("2. Timeline & ATT&CK Sequences (4 Episodes)", [PYTHON, "scripts/pipeline/s02_timeline_pipeline.py", "--processed-dir", "data/processed", "--reports-dir", "reports"]),
    ("3. Samples & Statistics (4 Episodes)", [PYTHON, "scripts/pipeline/s03_samples_and_stats.py", "--processed-dir", "data/processed", "--reports-dir", "reports"]),
    ("4. LOEO Model Training & Evaluation (4 Episodes - Technique)", [PYTHON, "scripts/pipeline/s04_evaluation_4ep_technique.py"]),
    ("5. LOEO Model Training & Evaluation (4 Episodes - Tactic)", [PYTHON, "scripts/pipeline/s05_evaluation_4ep_tactic.py"]),
    ("6. Stage 1 Normalization (7 Episodes)", [PYTHON, "scripts/pipeline/s01_normalize_events.py", "--episodes", "7", "--processed-dir", "data/processed_7ep", "--reports-dir", "reports/7ep"]),
    ("7. Timeline & ATT&CK Sequences (7 Episodes)", [PYTHON, "scripts/pipeline/s02_timeline_pipeline.py", "--processed-dir", "data/processed_7ep", "--reports-dir", "reports/7ep"]),
    ("8. Samples & Statistics (7 Episodes)", [PYTHON, "scripts/pipeline/s03_samples_and_stats.py", "--processed-dir", "data/processed_7ep", "--reports-dir", "reports/7ep"]),
    ("9. LOEO Model Training & Evaluation (7 Episodes)", [PYTHON, "scripts/pipeline/s06_evaluation_7ep.py"]),
    ("10. Learning Curve Evaluation (7 Episodes)", [PYTHON, "scripts/pipeline/s07_learning_curve_7ep.py"]),
    ("11. Permutation Tests (7 Episodes, B=1000)", [PYTHON, "scripts/pipeline/s08_permutation_test_7ep.py"]),
    ("12. Planted Structure Power Analysis (7 Episodes)", [PYTHON, "scripts/pipeline/s09_planted_power_7ep.py"]),
    ("13. E5-Removed Sensitivity (7 Episodes)", [PYTHON, "scripts/pipeline/s10_e5_removed_sensitivity.py"]),
    ("14. Holm Claim Rule Evaluation (7 Episodes)", [PYTHON, "scripts/pipeline/s11_holm_claim_rule.py"]),
    ("15. Diagnostics Evaluation (7 Episodes)", [PYTHON, "scripts/pipeline/s12_diagnostics_7ep.py"]),
    ("16. E5 Hit@1 Change Diagnostic", [PYTHON, "scripts/pipeline/s13_e5_hit1_diagnostic.py"]),
    ("17. Tie Sensitivity Diagnostic (7 Episodes)", [PYTHON, "scripts/pipeline/s14_tie_sensitivity_7ep.py"]),
    ("18. Exploratory Tactic-Conditioned Evaluation", [PYTHON, "scripts/pipeline/s15_exploratory_tactic_conditioned.py"]),
    ("19. Production Model Fitting", [PYTHON, "scripts/pipeline/s16_train_production_model.py"]),
    ("20. Explainable Prediction Records Build", [PYTHON, "scripts/pipeline/s17_build_prediction_records.py"]),
    ("21. Requirements Trace Generation", [PYTHON, "scripts/build_requirements_trace.py"]),
    ("22. Viva Pack Generation", [PYTHON, "scripts/pipeline/s18_build_viva_pack.py"]),
    ("23. Claims Map Generation", [PYTHON, "scripts/pipeline/s19_build_claims_map.py"]),
    ("24. Overnight Summary Generation", [PYTHON, "scripts/pipeline/s20_build_overnight_summary.py"]),
    ("25. Baseline Hash Verification", [PYTHON, "scripts/verify/verify_all_hashes.py"]),
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
