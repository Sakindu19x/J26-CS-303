# Hash Coverage Audit & Exceptions Register (P10.1)

> [!NOTE]
> **Audit Standard**: Evaluated across tracked artifacts in `reports/`, `data/processed*`, `artifacts/`, `viva_pack/`, `docs/`, `schemas/`.
> Files are categorized as **COVERED** (in baseline hash registry), **TRANSIENT** (declared measurement outputs), or **UNCOVERED** (cataloged below with technical rationale).

---

## 1. Executive Summary

| Category | Count | Percentage | Status |
|:---|:---:|:---:|:---|
| **Baseline Covered Artifacts** | 63 | 37.1% | Fully Verified via `verify_all_hashes.py` |
| **Declared Transient Measurements** | 6 | 3.5% | Runtime Timing & Screenshots (`reports/measurements/`) |
| **Documented Exceptions (Uncovered)** | 101 | 59.4% | Accounted for with Explicit Rationale |
| **Total Tracked Target Files** | 170 | 100.0% | Complete Coverage Accounted |

---

## 2. Exceptions Catalog by Functional Group

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

### Interface Contracts & Documentation (6 files)

| Tracked Path | Rationale |
|:---|:---|
| `docs/analyst_feedback_form.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/c3_c4_interface_contract.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/c3_open_questions.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/data_provenance.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/demo_script.md` | Analyst forms, C3 interface contracts, and data provenance documentation |
| `docs/models.md` | Analyst forms, C3 interface contracts, and data provenance documentation |

### JSON Schema Specifications (2 files)

| Tracked Path | Rationale |
|:---|:---|
| `schemas/c3_event.schema.json` | Formal schema contracts validated during pipeline execution and adapter tests |
| `schemas/c4_prediction_record.schema.json` | Formal schema contracts validated during pipeline execution and adapter tests |

### Narrative Markdown Reports (16 files)

| Tracked Path | Rationale |
|:---|:---|
| `reports/7ep/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/7ep/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/attack_version_comparison.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/audit/p1_findings.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/data_quality_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/dataset_inventory.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/new_episodes_intake_audit.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/permutation_test_v2_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_realscale_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/planted_structure_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/prereg_7episode_design.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/sequence_statistics.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/stage1_acceptance_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/step_type_summary.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |
| `reports/timeline_validation_report.md` | Human-readable markdown report rendered from baseline-verified JSON artifact |

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
*Report Generated: Deterministic Audit via `scripts/audit_hash_coverage.py`*
