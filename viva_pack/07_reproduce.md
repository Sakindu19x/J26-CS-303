# 07. Independent Reproduction Guide

---

## 1. Verification-Only Reproduction (Fast, Non-Destructive)

To re-run all 18 deterministic verifiers, hash verifications, and the complete pytest test suite without regenerating data:

```powershell
# From repository root
..\.venv\Scripts\python.exe scripts/reproduce_all.py --verify-only
```

Exit code 0 indicates 100% hash parity and passing verification.

---

## 2. Full Pipeline Rebuild from Raw Archives

To execute the entire forensic pipeline from the raw ZIP archives to all processed datasets, models, and reports:

```powershell
..\.venv\Scripts\python.exe scripts/reproduce_all.py --rebuild
```

Pipeline execution order (25 steps):
1. Stage 1 Normalization (4 Episodes) (`scripts/run_normalization.py`)
2. Timeline & ATT&CK Sequences (4 Episodes) (`scripts/run_timeline_pipeline.py`)
3. Samples & Statistics (4 Episodes) (`scripts/run_samples_and_stats.py`)
4. LOEO Model Training & Evaluation (4 Episodes - Technique) (`scripts/run_evaluation.py`)
5. LOEO Model Training & Evaluation (4 Episodes - Tactic) (`scripts/run_tactic_evaluation.py`)
6. Stage 1 Normalization (7 Episodes) (`scripts/run_normalization.py`)
7. Timeline & ATT&CK Sequences (7 Episodes) (`scripts/run_timeline_pipeline.py`)
8. Samples & Statistics (7 Episodes) (`scripts/run_samples_and_stats.py`)
9. LOEO Model Training & Evaluation (7 Episodes) (`scripts/run_evaluation_7ep.py`)
10. Learning Curve Evaluation (7 Episodes) (`scripts/run_learning_curve_7ep.py`)
11. Permutation Tests (7 Episodes, B=1000) (`scripts/run_permutation_test_7ep.py`)
12. Planted Structure Power Analysis (7 Episodes) (`scripts/run_planted_realscale_7ep.py`)
13. E5-Removed Sensitivity (7 Episodes) (`scripts/run_e5_removed_sensitivity.py`)
14. Holm Claim Rule Evaluation (7 Episodes) (`scripts/run_holm_claim_rule.py`)
15. Diagnostics Evaluation (7 Episodes) (`scripts/run_diagnostics_7ep.py`)
16. E5 Hit@1 Change Diagnostic (`scripts/run_e5_hit1_diagnostic.py`)
17. Tie Sensitivity Diagnostic (7 Episodes) (`scripts/run_tie_sensitivity_7ep.py`)
18. Exploratory Tactic-Conditioned Evaluation (`scripts/run_exploratory_tactic_conditioned.py`)
19. Production Model Fitting (`scripts/train_production_model.py`)
20. Explainable Prediction Records Build (`scripts/build_prediction_records.py`)
21. Requirements Trace Generation (`scripts/build_requirements_trace.py`)
22. Viva Pack Generation (`scripts/build_viva_pack.py`)
23. Claims Map Generation (`scripts/build_claims_map.py`)
24. Overnight Summary Generation (`scripts/build_overnight_summary.py`)
25. Baseline Hash Verification (`scripts/verify_all_hashes.py`)

All outputs are compared against baseline hashes upon completion.
