# 07. Independent Reproduction Guide

---

## 1. Verification-Only Reproduction (Fast, Non-Destructive)

To re-run all 13 deterministic verifiers, hash verifications, and the complete pytest test suite without regenerating data:

```powershell
# From repository root
..\.venv\Scripts\python.exe scripts/reproduce_all.py --verify-only
```

Expected duration: ~2.5 minutes. Exit code 0 indicates 100% hash parity and passing verification.

---

## 2. Full Pipeline Rebuild from Raw Archives

To execute the entire forensic pipeline from the raw ZIP archives to all processed datasets, models, and reports:

```powershell
..\.venv\Scripts\python.exe scripts/reproduce_all.py --rebuild
```

Pipeline execution order:
1. Stage 1 Extraction & Normalization (`scripts/run_stage1_pipeline_7ep.py`)
2. LOEO Cross-Validation & Model Training (`scripts/run_7ep_evaluation.py`)
3. Inference Suite, Diagnostics & Permutation Tests (`scripts/run_inference_7ep.py`)
4. Production Model Fitting (`scripts/train_production_model.py`)
5. Explainable Prediction Records Build (`scripts/build_prediction_records.py`)
6. Requirements Trace Generation (`scripts/build_requirements_trace.py`)
7. Viva Pack Generation (`scripts/build_viva_pack.py`)
8. Baseline Hash Verification (`scripts/verify_all_hashes.py`)

All outputs are compared against baseline hashes upon completion.
