# Hash Coverage Audit & Exceptions Register (Prompt 16 S1e)

> [!NOTE]
> **Audit Standard**: Evaluated across tracked artifacts in `reports/`, `data/processed*`, `artifacts/`, `viva_pack/`, `docs/`, `schemas/`.
> Exact path matching is used against all 61 canonical baseline files verified by `scripts/verify_all_hashes.py`.
> Files are categorized as **COVERED** (exact baseline match), **TRANSIENT** (declared measurement outputs), or **UNCOVERED** (cataloged below with explicit technical rationale).

---

## 1. Executive Summary

| Category | Count | Percentage | Status |
|:---|:---:|:---:|:---|
| **Baseline Covered Artifacts (Exact Path)** | 61 | 27.5% | Verified by `scripts/verify_all_hashes.py` |
| **Declared Transient Measurements** | 12 | 5.4% | Runtime Timing & Screenshots (`reports/measurements/`) |
| **Documented Exceptions (Uncovered)** | 149 | 67.1% | Accounted for with Explicit Rationale |
| **Total Tracked Target Files** | 222 | 100.0% | Complete Coverage Accounted |

---

## 2. Exceptions Catalog by Functional Group (149 Files)

### Archived Historical Analyses (11 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/archive/a2_design_history/README.md` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/inspect_a2.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_a2_choices.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_a2_collapsed.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_a2_diff.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_a2_dom.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_a2_proper.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/a2_design_history/test_all_gates.py` | Superseded exploratory scripts and historical design archives |
| `reports/archive/permutation_null_distribution_v1_counts_superseded.csv` | Superseded exploratory scripts and historical design archives |
| `reports/archive/permutation_test_report_v1_counts_superseded.json` | Superseded exploratory scripts and historical design archives |
| `reports/archive/permutation_test_report_v1_counts_superseded.md` | Superseded exploratory scripts and historical design archives |

### Audit & Execution Ledgers (6 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/final_audit_report.md` | Final audit verification report generated from test suites, baseline digests, and requirements |
| `reports/nfr_criteria.md` | Non-functional engineering criteria specification and pass/fail thresholds |
| `reports/overnight_decisions.md` | Project design decisions register updated across prompt milestones |
| `reports/overnight_ledger.md` | Deterministic execution tracking ledger regenerated from git history by scripts/audit/ledger.py |
| `reports/overnight_summary.md` | Overnight execution master summary verified deterministically by scripts/verify_overnight_summary.py |
| `reports/test_coverage_map.md` | Test mapping documentation linking requirements to unit and integration test nodes |

### Audit & Verification Reports (40 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/audit/exempt_claims_map.txt` | Verification logs, decision records, or change register |
| `reports/audit/exempt_exploratory.txt` | Verification logs, decision records, or change register |
| `reports/audit/exempt_overnight_summary.txt` | Verification logs, decision records, or change register |
| `reports/audit/exempt_requirements_trace.txt` | Verification logs, decision records, or change register |
| `reports/audit/exempt_viva_pack.txt` | Verification logs, decision records, or change register |
| `reports/audit/hash_coverage_exceptions.md` | Verification logs, decision records, or change register |
| `reports/audit/known_limitations.json` | Verification logs, decision records, or change register |
| `reports/audit/known_limitations.md` | Verification logs, decision records, or change register |
| `reports/audit/line_ending_audit.md` | Verification logs, decision records, or change register |
| `reports/audit/p1_findings.md` | Verification logs, decision records, or change register |
| `reports/audit/prereg_compliance_map.json` | Verification logs, decision records, or change register |
| `reports/audit/prereg_compliance_map.md` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q0_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q10_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q1_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q2_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q3_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q4_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q5_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q6_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q7_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q8_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_Q9_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q14_baseline_changes.md` | Verification logs, decision records, or change register |
| `reports/audit/q14_decisions.md` | Verification logs, decision records, or change register |
| `reports/audit/q14_determinism_log.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R0_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R1_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R2_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R3_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R4_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R5_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R6_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R7_git.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R7_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_R7_sweeps.txt` | Verification logs, decision records, or change register |
| `reports/audit/q15_baseline_changes.md` | Verification logs, decision records, or change register |
| `reports/audit/q16_S0_output.txt` | Verification logs, decision records, or change register |
| `reports/audit/rebuild_scope.json` | Verification logs, decision records, or change register |
| `reports/audit/rebuild_scope.md` | Verification logs, decision records, or change register |

### Derivative Tabular CSV Exports (4 files)

| Tracked Path | Rationale |
|:---|:---|
| `data/processed_7ep/attack_timelines.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/next_technique_samples.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/normalized_events.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/wazuh_alerts_normalized.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |

### Fold Models (Covered by Internal Manifest) (22 files)

| Tracked Path | Rationale |
|:---|:---|
| `artifacts/7ep/fold_models/collapsed_full/E1.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E2.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E3.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E4.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E5.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E6.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E7.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/manifest.json` | Cryptographic manifest covering all 21 fold-level LOEO Markov model files |
| `artifacts/7ep/fold_models/raw_full/E1.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E2.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E3.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E4.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E5.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E6.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E7.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E1.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E2.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E3.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E4.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E5.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E6.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E7.json` | Fold-level LOEO Markov model covered by artifacts/7ep/fold_models/manifest.json |

### Historical 4-Episode Figures (3 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/figures/confusion_matrix_parent.png` | Pre-migration 4-episode visual figures |
| `reports/figures/headline_metrics.png` | Pre-migration 4-episode visual figures |
| `reports/figures/per_fold_performance.png` | Pre-migration 4-episode visual figures |

### Historical 4-Episode Processed Data (9 files)

| Tracked Path | Rationale |
|:---|:---|
| `data/processed/.gitkeep` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/attack_timelines.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/next_technique_samples.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/normalized_events.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/permutation_v2_null_distribution.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/planted_realscale_predictions.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/planted_structure_predictions.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/technique_tactic_reference_v19_2.json` | Legacy 4-episode dataset representation superseded by 7-episode campaign |
| `data/processed/wazuh_alerts_normalized.csv` | Legacy 4-episode dataset representation superseded by 7-episode campaign |

### Interface Contracts & Documentation (9 files)

| Tracked Path | Rationale |
|:---|:---|
| `docs/analyst_feedback_form.md` | Specification, interface contract, or requirements specification document |
| `docs/c3_c4_interface_contract.md` | Specification, interface contract, or requirements specification document |
| `docs/c3_open_questions.md` | Specification, interface contract, or requirements specification document |
| `docs/data_provenance.md` | Specification, interface contract, or requirements specification document |
| `docs/demo_script.md` | Specification, interface contract, or requirements specification document |
| `docs/models.md` | Specification, interface contract, or requirements specification document |
| `docs/prompts/prompt15.md` | Specification, interface contract, or requirements specification document |
| `docs/prompts/prompt16.md` | Specification, interface contract, or requirements specification document |
| `docs/proposal_requirements.json` | Specification, interface contract, or requirements specification document |

### JSON Schema Specifications (2 files)

| Tracked Path | Rationale |
|:---|:---|
| `schemas/c3_event.schema.json` | Formal schema contract validated during pipeline execution and adapter tests |
| `schemas/c4_prediction_record.schema.json` | Formal schema contract validated during pipeline execution and adapter tests |

### Narrative Markdown Reports (14 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/7ep/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/attack_version_comparison.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/dataset_inventory.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/new_episodes_intake_audit.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/permutation_test_v2_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_realscale_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_structure_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/stage1_acceptance_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/step_type_summary.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |

### Pre-Registration Protocol (Append-Only) (1 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/prereg_7episode_design.md` | Pre-registration protocol (append-only, protected by scripts/verify/verify_prereg_append_only.py) |

### Supplementary Analysis Artifacts (16 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/_baseline_hashes_7ep_eval.json` | Supplementary audit or reference dataset |
| `reports/_baseline_hashes_7ep_inference.json` | Supplementary audit or reference dataset |
| `reports/_baseline_hashes_7ep_stage1.json` | Supplementary audit or reference dataset |
| `reports/_baseline_hashes_stage2.json` | Supplementary audit or reference dataset |
| `reports/_baseline_hashes_tactic.json` | Supplementary audit or reference dataset |
| `reports/attack_version_comparison.json` | Supplementary audit or reference dataset |
| `reports/confusion_matrix_parent.csv` | Supplementary audit or reference dataset |
| `reports/dataset_inventory.json` | Supplementary audit or reference dataset |
| `reports/new_episodes_intake_audit.json` | Supplementary audit or reference dataset |
| `reports/permutation_test_v2_report.json` | Supplementary audit or reference dataset |
| `reports/planted_realscale_report.json` | Supplementary audit or reference dataset |
| `reports/planted_structure_report.json` | Supplementary audit or reference dataset |
| `reports/raw_archive_hashes.json` | Supplementary audit or reference dataset |
| `reports/raw_archive_hashes_extended.json` | Supplementary audit or reference dataset |
| `reports/stage1_acceptance_report.json` | Supplementary audit or reference dataset |
| `reports/step_type_summary.json` | Supplementary audit or reference dataset |

### Viva Examination Pack (Code-Generated) (12 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/viva/claims.json` | Formal machine-readable claims definition verified by scripts/verify_claims_map.py |
| `reports/viva/claims_to_evidence_map.md` | Traceability matrix linking viva claims to empirical artifacts verified by scripts/verify_claims_map.py |
| `viva_pack/01_dataset.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/02_split_and_training.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/03_scores.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/04_worked_examples.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/05_figures/a4_power_curve.png` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/05_figures/learning_curve_7ep.png` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/05_figures/loeo_performance_bar_chart.png` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/06_claims_and_limits.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/07_reproduce.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/README.md` | Generated viva deliverable verified deterministically by scripts/verify_viva_pack.py |

---

## 3. Claims Map Cited Files Verification Guard

All files cited as sources or evidence in `reports/viva/claims.json` are strictly accounted for:
- Canonical baseline artifacts are verified directly by `scripts/verify_all_hashes.py`.
- Non-baseline cited files are covered by dedicated automated verifiers and test suites (`scripts/verify_nfr1.py`, `scripts/verify_prediction_records.py`, `tests/test_c3_adapter.py`, `tests/test_nfr1.py`).
- **Zero uncovered cited files**.

---
*Report Generated: Deterministic Audit via `scripts/audit_hash_coverage.py`*
