# C4 — CTI-Assisted Forensic Timeline Reconstruction & Next-Stage Attack Prediction

Component 4 (C4) of the research project: **"CTI-Assisted Digital Forensic Investigation Tool for SMEs: Explainable Attack Timeline Reconstruction and Next-Stage Prediction Model"**.

Processes the CAM-LDS (Cyber Attack Manifestations Log Data Set) dataset across 7 attack simulation scenarios (`E1` through `E7`). Evaluates First-Order Markov transition models against Global Frequency baselines under Leave-One-Episode-Out (LOEO) cross-validation with exact mathematical bounds and pre-registered hypotheses.

---

## Repository Directory Layout

```
c4/
├── data/
│   ├── raw/                 Read-only original CAM-LDS zip archives and Zenodo checksums
│   ├── reference/           Official MITRE ATT&CK Enterprise STIX v16.1 reference
│   ├── interim/             Temporary / staging extraction directories
│   ├── processed/           Stage 1 4-episode artifacts (timelines, sequences, samples)
│   └── processed_7ep/       Stage 1 7-episode artifacts, prediction records, and predictions
├── src/c4/                  Core library package:
│   ├── data_loading.py          Raw archive loading & integrity verification
│   ├── normalization.py         AttackMate event normalization & whitespace cleaning
│   ├── mitre_reference.py       MITRE ATT&CK v16.1 reference & discrepancy resolution
│   ├── episodes.py              Episode container & strict isolation manager
│   ├── timeline.py              Chronological timeline reconstruction & filters
│   ├── attack_sequence.py       Raw & collapsed ATT&CK manifestation sequences
│   ├── samples.py               Prefix-target sequence sample generator
│   ├── sequence_statistics.py   LOEO fold coverage & overlap matrix calculator
│   ├── c3_adapter.py            Component 3 structured event intake adapter
│   ├── models/                  Markov and Frequency next-stage predictor engines
│   └── dashboard/               Streamlit + Altair forensic investigation console
├── scripts/
│   ├── pipeline/            Numbered pipeline execution stages:
│   │   ├── s01_normalize_events.py           Stage 1: Event normalization & telemetry
│   │   ├── s02_timeline_pipeline.py          Stage 2: Chronological timelines & sequences
│   │   ├── s03_samples_and_stats.py          Stage 3: Samples & LOEO fold matrices
│   │   ├── s04_evaluation_4ep_technique.py   Stage 4: 4-ep technique LOEO evaluation
│   │   ├── s05_evaluation_4ep_tactic.py      Stage 5: 4-ep tactic LOEO evaluation
│   │   ├── s06_evaluation_7ep.py             Stage 6: 7-ep primary LOEO evaluation
│   │   ├── s07_learning_curve_7ep.py         Stage 7: Combinatorial subset learning curve
│   │   ├── s08_permutation_test_7ep.py       Stage 8: Permutation null distribution tests
│   │   ├── s09_planted_power_7ep.py          Stage 9: Planted structure power analysis
│   │   ├── s10_e5_removed_sensitivity.py     Stage 10: E5-removed ablation sensitivity
│   │   ├── s11_holm_claim_rule.py            Stage 11: Holm step-down claim rule
│   │   ├── s12_diagnostics_7ep.py            Stage 12: Sequence and gap diagnostics
│   │   ├── s13_e5_hit1_diagnostic.py         Stage 13: E5 Hit@1 change diagnostic
│   │   ├── s14_tie_sensitivity_7ep.py        Stage 14: Exact tie-break sensitivity bounds
│   │   ├── s15_exploratory_tactic_conditioned.py Stage 15: Tactic-conditioned exploration
│   │   ├── s16_train_production_model.py     Stage 16: Production model serialization
│   │   ├── s17_build_prediction_records.py   Stage 17: Explainable JSONL prediction records
│   │   ├── s18_build_viva_pack.py            Stage 18: Examiner viva briefing pack builder
│   │   ├── s19_build_claims_map.py           Stage 19: Claims-to-evidence map generator
│   │   └── s20_build_overnight_summary.py    Stage 20: Comprehensive overnight report
│   ├── verify/              Deterministic verifiers and integrity checkers:
│   │   ├── verify_all_hashes.py              SHA-256 baseline hash verifier (61/61)
│   │   ├── verify_prereg_append_only.py      Pre-registration append-only integrity verifier
│   │   ├── verify_stage1_7ep.py              Stage 1 7-episode artifact verifier
│   │   ├── verify_evaluation_7ep.py          7-episode LOEO evaluation verifier
│   │   ├── verify_prediction_records.py      JSONL prediction records verifier
│   │   ├── verify_learning_curve_7ep.py      Learning curve artifact verifier
│   │   ├── verify_planted_realscale_7ep.py   Planted structure power analysis verifier
│   │   ├── verify_e5_removed.py              E5-removed ablation verifier
│   │   ├── verify_e5_hit1_diagnostic.py      E5 Hit@1 diagnostic verifier
│   │   ├── verify_tie_sensitivity_7ep.py     Exact tie-break bounds verifier
│   │   ├── verify_exploratory_tactic_conditioned.py Exploratory variant verifier
│   │   ├── verify_holm_claim_rule.py         Holm claim rule decision verifier
│   │   ├── verify_viva_pack.py               Viva pack integrity and figure verifier
│   │   ├── verify_requirements_trace.py      Requirements trace matrix verifier
│   │   ├── verify_claims_map.py              Claims-to-evidence verifier
│   │   ├── verify_overnight_summary.py       Overnight summary report verifier
│   │   ├── verify_nfr1.py                    NFR1 timing performance verifier
│   │   └── verify_tactic_evaluation.py       4-episode tactic evaluation verifier
│   ├── audit/               Audit tools and provenance tracking:
│   │   ├── ledger.py                         Execution ledger generator
│   │   ├── run_logged.py                     Standardized audit logging wrapper (Rule G4)
│   │   ├── check_output_provenance.py        Audit log header validator
│   │   ├── audit_hash_coverage.py            Full-workspace hash coverage auditor
│   │   ├── record_baseline_change.py         Baseline change diff and audit recorder
│   │   └── emit_final_table.py               Clean execution table generator (Rule G1)
│   ├── dashboard/           Dashboard launchers and browser capture scripts:
│   │   ├── run_dashboard.ps1                 Unified PowerShell dashboard launcher
│   │   ├── capture_live_dashboard.py         Automated live dashboard screenshot capture
│   │   └── capture_dashboard_screenshots.py  Render capture tool
│   └── reproduce_all.py     Master one-command reproduction runner (--verify-only, --rebuild)
├── tests/                   Pytest regression test suite (descriptive naming):
│   ├── test_basic.py                        Package import and version smoke tests
│   ├── test_c3_adapter.py                   C3 schema ingestion & duplicate handling
│   ├── test_checks_detect_errors.py         Synthetic error injection detection
│   ├── test_claims_map.py                   Claims matrix and prohibited value guards
│   ├── test_dashboard.py                    Forensic investigation timeline app tests
│   ├── test_dashboard_launch.py             Launcher specification & render tests
│   ├── test_demo_script_steps.py            Demonstration script workflow tests
│   ├── test_evaluation.py                   4-episode technique evaluation tests
│   ├── test_evaluation_7ep.py               7-episode LOEO evaluation regression tests
│   ├── test_evaluation_consistency.py       Technique evaluation invariant checks
│   ├── test_exploratory_tactic_conditioned.py Exploratory tactic-conditioned variant tests
│   ├── test_inference_7ep.py                Inference, Holm claim rules, and tie bounds
│   ├── test_intake_audit.py                 Raw data integrity and intake checks
│   ├── test_models.py                       Markov and Frequency mathematical models
│   ├── test_mutation_sweep.py               Full mutation sweeps across evaluation
│   ├── test_nfr1.py                         NFR1 latency and timing schema assertions
│   ├── test_normalization.py                AttackMate normalization & event parsing
│   ├── test_overnight_summary.py            Overnight summary report structure tests
│   ├── test_permutation_test.py             Permutation test baseline assertions
│   ├── test_permutation_test_v2.py          Permutation test v2 invariant assertions
│   ├── test_planted_realscale.py            Planted structure real-scale simulation tests
│   ├── test_planted_structure.py            Planted structure synthetic power tests
│   ├── test_prediction_panel.py             Prediction panel UI component tests
│   ├── test_prediction_record.py            JSONL prediction records schema validation
│   ├── test_record_baseline_change.py       Audit tool leaf diff and invariant tests
│   ├── test_requirements_trace.py           Proposal requirements traceability tests
│   ├── test_samples_and_stats.py            Prefix-target sample generation tests
│   ├── test_stage1_7ep.py                   Stage 1 7-episode pipeline assertions
│   ├── test_tactic_evaluation.py            4-episode tactic evaluation tests
│   ├── test_tactic_evaluation_consistency.py Tactic evaluation invariant & discrepancy tests
│   ├── test_timeline_and_sequences.py       Timeline reconstruction & sequence compression
│   └── test_viva_pack_sweep.py              Examiner viva pack mutation sweep tests
├── docs/                    System documentation, specifications, and root of trust:
│   ├── architecture.md                      System architecture & mathematical formulations
│   ├── data_provenance.md                   Raw CAM-LDS dataset provenance & Zenodo records
│   ├── c3_c4_interface_contract.md          C3/C4 interface contract and JSON schema
│   ├── demo_script.md                       10-step examiner demonstration script
│   ├── proposal_requirements.json           Authoritative proposal requirements register
│   ├── analyst_feedback_form.md             Analyst evaluation and feedback instrument
│   ├── c3_open_questions.md                 Open questions for upstream Component 3 team
│   ├── ROOT_OF_TRUST.md                     Cryptographic digests of baseline registries
│   ├── PROJECT_MAP.md                       One-line directory and script inventory
│   └── process/
│       ├── cleanup_map.md                   Refactoring and migration registry
│       └── prompts/                         Formal prompt specifications (prompt15, prompt16)
├── reports/                 Generated evaluation results, audit logs, and measurements
├── artifacts/               Serialized production models and fold models
└── viva_pack/               Examiner viva briefing pack (dataset, scores, figures, reproduce)
```

---

## Setup & Quick Start

Ensure Python 3.10+ (or Python 3.12) is installed.

```bash
# Activate virtual environment
..\.venv\Scripts\activate

# Install requirements / package
pip install -r requirements.txt
pip install -e .
```

---

## One-Command Reproduction

Execute the master reproduction runner:

```bash
# Fast, non-destructive verification of all baselines and test suite:
python scripts/reproduce_all.py --verify-only

# Rebuild entire pipeline from raw archives and assert byte-identical matching:
python scripts/reproduce_all.py --rebuild
```

---

## Launching the Analyst Dashboard

Launch the unified forensic investigation and prediction dashboard:

```powershell
# Prediction Dashboard (Port 8501):
.\scripts\dashboard\run_dashboard.ps1 -App prediction

# Attack Timeline Dashboard (Port 8502):
.\scripts\dashboard\run_dashboard.ps1 -App timeline
```

---

## Running Tests

Execute the full regression test suite (210 tests):

```bash
pytest -v
```
