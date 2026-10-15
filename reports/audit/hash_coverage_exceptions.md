# Hash Coverage Audit & Exceptions Register (P10.1 & Prompt 14 Q10)

> [!NOTE]
> **Audit Standard**: Evaluated across tracked artifacts in `reports/`, `data/processed*`, `artifacts/`, `viva_pack/`, `docs/`, `schemas/`.
> Files are categorized as **COVERED** (in baseline hash registry), **TRANSIENT** (declared measurement outputs), or **UNCOVERED** (cataloged below with technical rationale).

---

## 1. Executive Summary

| Category | Count | Percentage | Status |
|:---|:---:|:---:|:---|
| **Baseline Covered Artifacts (Audit Matched)** | 63 | 29.0% | Accounted in baseline hash files |
| **Strict Exact Baseline Files** | 61 | -- | Verified by `verify_all_hashes.py` |
| **Declared Transient Measurements** | 12 | 5.5% | Runtime Timing & Screenshots (`reports/measurements/`) |
| **Documented Exceptions (Uncovered)** | 142 | 65.4% | Accounted for with Explicit Rationale |
| **Total Tracked Target Files** | 217 | 100.0% | Complete Coverage Accounted |

---

## 2. Reconciliation of Baseline Counts (63 Audit vs 61 verify_all_hashes)

The audit script reports **63** covered files while `scripts/verify_all_hashes.py` strictly checks **61** canonical baseline files.

The **2-file difference** arises from loose basename matching (`norm_k.split('/')[-1]`) in the legacy audit classifier, which matched two duplicate filenames:

1. `artifacts/7ep/fold_models/manifest.json`:
   Matched the basename `manifest.json` from the protected baseline `artifacts/7ep/production_model/manifest.json`.
2. `viva_pack/05_figures/learning_curve_7ep.png`:
   Matched the basename `learning_curve_7ep.png` from the protected baseline `reports/7ep/learning_curve_7ep.png`.

Both files are independently verified: the fold models are verified via internal fold validation checks, and the viva pack figure is verified by `scripts/verify_viva_pack.py`.

---

## 3. Exceptions Catalog by Functional Group (142 Files)

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

### Audit & Execution Ledgers (4 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/nfr_criteria.md` | Live tracking ledger, engineering criteria, and decisions log updated per part |
| `reports/overnight_decisions.md` | Live tracking ledger, engineering criteria, and decisions log updated per part |
| `reports/overnight_ledger.md` | Live tracking ledger, engineering criteria, and decisions log updated per part |
| `reports/test_coverage_map.md` | Live tracking ledger, engineering criteria, and decisions log updated per part |

### Audit & Verification Reports (Prompt 14 / Repair Run) (36 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/audit/exempt_claims_map.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/exempt_exploratory.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/exempt_overnight_summary.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/exempt_requirements_trace.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/exempt_viva_pack.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/hash_coverage_exceptions.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/known_limitations.json` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/known_limitations.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/line_ending_audit.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/p1_findings.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/prereg_compliance_map.json` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/prereg_compliance_map.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q0_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q10_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q1_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q2_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q3_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q4_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q5_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q6_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q7_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q8_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_Q9_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_baseline_changes.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_decisions.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q14_determinism_log.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R0_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R1_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R2_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R3_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R4_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R5_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_R6_output.txt` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/q15_baseline_changes.md` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/rebuild_scope.json` | Repair run verification logs, decision records, and per-token exempt registries |
| `reports/audit/rebuild_scope.md` | Repair run verification logs, decision records, and per-token exempt registries |

### Derivative Tabular CSV Exports (4 files)

| Tracked Path | Rationale |
|:---|:---|
| `data/processed_7ep/attack_timelines.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/next_technique_samples.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/normalized_events.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |
| `data/processed_7ep/wazuh_alerts_normalized.csv` | Tabular CSV representation derived from canonical baseline-hashed JSON |

### Fold Models (Covered by Internal Manifest) (21 files)

| Tracked Path | Rationale |
|:---|:---|
| `artifacts/7ep/fold_models/collapsed_full/E1.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E2.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E3.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E4.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E5.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E6.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/collapsed_full/E7.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E1.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E2.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E3.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E4.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E5.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E6.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/raw_full/E7.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E1.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E2.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E3.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E4.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E5.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E6.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |
| `artifacts/7ep/fold_models/tactic_collapsed/E7.json` | Fold-level LOEO Markov models covered by artifacts/7ep/fold_models/manifest.json |

### Historical 4-Episode Figures (3 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/figures/confusion_matrix_parent.png` | Pre-migration 4-episode visual figures |
| `reports/figures/headline_metrics.png` | Pre-migration 4-episode visual figures |
| `reports/figures/per_fold_performance.png` | Pre-migration 4-episode visual figures |

### Historical 4-Episode Processed Data (9 files)

| Tracked Path | Rationale |
|:---|:---|
| `data/processed/.gitkeep` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/attack_timelines.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/next_technique_samples.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/normalized_events.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/permutation_v2_null_distribution.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/planted_realscale_predictions.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/planted_structure_predictions.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/technique_tactic_reference_v19_2.json` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |
| `data/processed/wazuh_alerts_normalized.csv` | Legacy 4-episode dataset superseded by 7-episode campaign (data/processed_7ep/) |

### Interface Contracts & Documentation (8 files)

| Tracked Path | Rationale |
|:---|:---|
| `docs/analyst_feedback_form.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/c3_c4_interface_contract.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/c3_open_questions.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/data_provenance.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/demo_script.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/models.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/prompts/prompt15.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/proposal_requirements.json` | Analyst forms, C3 interface contracts, and data provenance documentation |

### JSON Schema Specifications (2 files)

| Tracked Path | Rationale |
|:---|:---|
| `schemas/c3_event.schema.json` | Formal schema contracts validated during pipeline execution and adapter tests |
| `schemas/c4_prediction_record.schema.json` | Formal schema contracts validated during pipeline execution and adapter tests |

### Narrative Markdown Reports (18 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/7ep/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/attack_version_comparison.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/dataset_inventory.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/final_audit_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/new_episodes_intake_audit.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/overnight_summary.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/permutation_test_v2_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_realscale_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_structure_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/prereg_7episode_design.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/stage1_acceptance_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/step_type_summary.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/viva/claims_to_evidence_map.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |

### Supplementary Analysis Artifacts (17 files)

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
| `reports/viva/claims.json` | Supplementary audit or reference dataset |

### Viva Examination Pack (Code-Generated) (9 files)

| Tracked Path | Rationale |
|:---|:---|
| `viva_pack/01_dataset.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/02_split_and_training.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/03_scores.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/04_worked_examples.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/05_figures/a4_power_curve.png` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/05_figures/loeo_performance_bar_chart.png` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/06_claims_and_limits.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/07_reproduce.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |
| `viva_pack/README.md` | Generated viva deliverables verified deterministically by scripts/verify_viva_pack.py |

---

## 4. Claims Map Cited Files Verification Guard

All 18 distinct files cited as sources or evidence in `reports/viva/claims.json` are strictly accounted for:
- **12 files** are canonical baseline artifacts verified directly by `scripts/verify_all_hashes.py`.
- **6 files** (`reports/measurements/nfr1_timing.json`, `reports/audit/rebuild_scope.md`, `reports/audit/q14_Q2_output.txt`, `reports/audit/q14_determinism_log.txt`, `schemas/c4_prediction_record.schema.json`, `docs/c3_c4_interface_contract.md`) are covered by dedicated automated verifiers and test suites (`scripts/verify_nfr1.py`, `scripts/verify_prediction_records.py`, `tests/test_c3_adapter.py`, `tests/test_nfr1.py`).
- **Zero uncovered cited files**.

---
*Report Generated: Deterministic Audit via `scripts/audit_hash_coverage.py`*
