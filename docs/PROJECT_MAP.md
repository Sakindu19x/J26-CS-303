# C4 Project Map

This document describes every top-level folder, script subdirectory, and root script in the C4 repository.
Derived directly from repository filesystem structure.

## Top-Level Directories and Root Files

- [`.streamlit/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/.streamlit): Streamlit configuration and UI theme settings
- [`artifacts/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/artifacts): Workspace directory
- [`data/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data): Dataset archives, raw logs, and processed pipeline artifacts
- [`docs/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/docs): System architecture, specifications, requirements, and process logs
- [`reports/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports): Pre-registered experimental reports, baseline hashes, audit ledgers, and viva pack
- [`schemas/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/schemas): Workspace directory
- [`scratch/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scratch): Workspace directory
- [`scripts/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts): Executable pipeline stages, verification harnesses, audit tools, and dashboard scripts
- [`src/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/src): Production Python package (c4: data loading, models, evaluation, dashboard)
- [`tests/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/tests): Automated regression, integrity, model invariant, and property tests
- [`viva_pack/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/viva_pack): Viva pack presentation slides, worked examples, and reproduction guide
- [`pyproject.toml`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/pyproject.toml): Root project file
- [`README.md`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/README.md): Root project file
- [`requirements.lock.txt`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/requirements.lock.txt): Root project file
- [`requirements.txt`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/requirements.txt): Root project file

## Scripts Subsystems (`scripts/`)

- [`scripts/audit/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/audit): Audit provenance, hash coverage, baseline changes, and ledger verification scripts
- [`scripts/dashboard/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/dashboard): Streamlit dashboard launch scripts and automated browser screenshot capture tools
- [`scripts/pipeline/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline): Numbered sequential pipeline stages (s01 to s20) executing end-to-end data processing and evaluation
- [`scripts/verify/`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/verify): Independent single-purpose verifier scripts checking baseline outputs and reports

## Root Scripts (`scripts/*.py`)

- [`scripts/build_prediction_records.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/build_prediction_records.py): Stage runner generating explainable prediction JSON records (embedded in requirements trace)
- [`scripts/build_requirements_trace.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/build_requirements_trace.py): Stage runner generating requirements trace matrix (embedded in requirements trace)
- [`scripts/check_regression_gate.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/check_regression_gate.py): Pre-registered regression gate validator for LOEO evaluation
- [`scripts/measure_nfr1.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/measure_nfr1.py): NFR1 dashboard warm render latency benchmark harness (embedded in requirements trace)
- [`scripts/mutation_sweep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/mutation_sweep.py): Mutation testing harness validating verifier sensitivity (embedded in prereg design)
- [`scripts/mutation_sweep_requirements_trace.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/mutation_sweep_requirements_trace.py): Mutation testing harness validating requirements trace verifier
- [`scripts/reproduce_all.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/reproduce_all.py): Canonical full reproduction and verify-only entrypoint
- [`scripts/run_holm_claim_rule.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_holm_claim_rule.py): Stage runner executing Holm-Bonferroni family-wise error control (embedded in prereg design)
- [`scripts/run_permutation_test_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_permutation_test_7ep.py): Stage runner executing 7-episode order permutation test (embedded in prereg design)
- [`scripts/run_permutation_test_v2.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_permutation_test_v2.py): Stage runner executing 4-episode order permutation test (embedded in prereg design)
- [`scripts/run_planted_realscale.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_planted_realscale.py): Planted structure power analysis validation runner
- [`scripts/run_planted_structure.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_planted_structure.py): Planted Markov transition structure power test runner
- [`scripts/run_q7_gates.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/run_q7_gates.py): Gate verification script supporting CLAIM-10 and CLAIM-11 in claims map
- [`scripts/verify_evaluation.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/verify_evaluation.py): Independent verifier for 4-episode LOEO evaluation (embedded in prereg design)
- [`scripts/verify_permutation_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/verify_permutation_7ep.py): Independent verifier for 7-episode permutation test (embedded in prereg design)
- [`scripts/verify_permutation_test_v2.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/verify_permutation_test_v2.py): Independent verifier for 4-episode permutation test (embedded in prereg design)
