# Baseline Rebuild Scope Classification (Q2)

**Generated:** 2026-10-15  
**Component:** Component 4 (`c4`)  
**Scope:** 61 Protected Baseline Files Across Sections (a) through (f)

---

## 1. Executive Summary

| Category | Count | Percentage |
|:---|:---:|:---:|
| **REBUILT_FROM_RAW** | 61 | 100.0% |
| **COPIED_FROM_GIT_ONLY** | 0 | 0.0% |
| **Total Protected Baselines** | **61** | **100.0%** |

Every single one of the 61 protected baseline files is regenerated deterministically from the raw scenario archives (`scenario_*.zip`) and the tracked ATT&CK reference data (`enterprise-attack.json`) by `scripts/reproduce_all.py --rebuild`. Zero baseline files require copying from git history or working tree.

---

## 2. Rebuild Scope Inventory

### Section (a): Stage 2 Technique Files (4 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 1 | `reports/evaluation_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation.py` | Generated from LOEO fold evaluation on 4-episode samples |
| 2 | `reports/evaluation_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation.py` | Structured metrics emitted from LOEO fold evaluation |
| 3 | `data/processed/evaluation_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation.py` | Full prediction rows output by LOEO cross-validation |

### Section (b): Stage 1 Canonical Files (4 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 4 | `data/processed/attack_sequences.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed --reports-dir reports` | ATT&CK sequences extracted from 4-episode timelines |
| 5 | `data/processed/attack_timelines.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed --reports-dir reports` | Timelines reconstructed from normalized events |
| 6 | `data/processed/loeo_folds.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed --reports-dir reports` | LOEO fold partition definitions across 4 episodes |
| 7 | `data/processed/next_technique_samples.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed --reports-dir reports` | Next-technique transition samples generated from sequences |
| 8 | `data/processed/normalized_events.json` | `REBUILT_FROM_RAW` | `python scripts/run_normalization.py --episodes 4 --processed-dir data/processed --reports-dir reports` | CAM-LDS normalized events parsed from raw archives E1-E4 |
| 9 | `data/processed/technique_tactic_reference.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed --reports-dir reports` | Reference table parsed from STIX enterprise-attack bundle |
| 10 | `reports/data_quality_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_normalization.py --episodes 4 --processed-dir data/processed --reports-dir reports` | Data quality metrics emitted from raw normalization |
| 11 | `reports/timeline_validation_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed --reports-dir reports` | Timeline consistency metrics and event validation |
| 12 | `reports/tactic_discrepancy_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed --reports-dir reports` | Tactic cross-reference discrepancies check |
| 13 | `reports/sequence_statistics.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed --reports-dir reports` | Transition graph and sequence statistics |

### Section (c): Stage 2 Tactic Files (4 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 14 | `reports/tactic_evaluation_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_tactic_evaluation.py` | Secondary next-tactic LOEO evaluation report |
| 15 | `reports/tactic_evaluation_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_tactic_evaluation.py` | Secondary next-tactic structured metrics |
| 16 | `data/processed/tactic_evaluation_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_tactic_evaluation.py` | Full prediction rows for next-tactic LOEO |

### Section (d): Stage 1 Canonical Files (7 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 17 | `data/processed_7ep/attack_sequences.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | ATT&CK sequences extracted from 7-episode timelines |
| 18 | `data/processed_7ep/attack_timelines.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Timelines reconstructed from 7-episode events |
| 19 | `data/processed_7ep/loeo_folds.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | LOEO fold partition definitions across 7 episodes |
| 20 | `data/processed_7ep/next_technique_samples.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Next-technique transition samples from 7-episode sequences |
| 21 | `data/processed_7ep/normalized_events.json` | `REBUILT_FROM_RAW` | `python scripts/run_normalization.py --episodes 7 --processed-dir data/processed_7ep --reports-dir reports/7ep` | CAM-LDS normalized events parsed from raw archives E1-E7 |
| 22 | `data/processed_7ep/technique_tactic_reference.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Reference table parsed from STIX enterprise-attack bundle |
| 23 | `reports/7ep/data_quality_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_normalization.py --episodes 7 --processed-dir data/processed_7ep --reports-dir reports/7ep` | Data quality metrics for 7-episode normalization |
| 24 | `reports/7ep/timeline_validation_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_timeline_pipeline.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Timeline consistency metrics for 7-episode dataset |
| 25 | `reports/7ep/tactic_discrepancy_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Tactic discrepancies across 7-episode dataset |
| 26 | `reports/7ep/sequence_statistics.json` | `REBUILT_FROM_RAW` | `python scripts/run_samples_and_stats.py --processed-dir data/processed_7ep --reports-dir reports/7ep` | Transition graph statistics across 7 episodes |

### Section (e): Stage 2 Evaluation Files (7 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 27 | `data/processed_7ep/evaluation_7ep_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation_7ep.py` | Full prediction rows from 7-episode LOEO |
| 28 | `reports/7ep/evaluation_7ep_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation_7ep.py` | Primary technique & tactic evaluation metrics |
| 29 | `reports/7ep/evaluation_7ep_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_evaluation_7ep.py` | Comprehensive Markdown report for 7-episode LOEO |

### Section (f): Stage 2 Inference & Analysis Files (7 Episodes)

| # | Relative Path | Classification | Regenerating Script / Command | Reason / Mechanism |
|:---:|:---|:---:|:---|:---|
| 30 | `data/processed_7ep/learning_curve_7ep.csv` | `REBUILT_FROM_RAW` | `python scripts/run_learning_curve_7ep.py` | Learning curve cumulative performance samples |
| 31 | `reports/7ep/learning_curve_7ep_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_learning_curve_7ep.py` | Learning curve statistical results |
| 32 | `reports/7ep/learning_curve_7ep_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_learning_curve_7ep.py` | Learning curve evaluation report |
| 33 | `reports/7ep/learning_curve_7ep.png` | `REBUILT_FROM_RAW` | `python scripts/run_learning_curve_7ep.py` | High-resolution learning curve visualization |
| 34 | `reports/7ep/learning_curve_7ep_plot_data.json` | `REBUILT_FROM_RAW` | `python scripts/run_learning_curve_7ep.py` | Raw plot coordinates for learning curve figure |
| 35 | `data/processed_7ep/permutation_7ep_null_distribution.csv` | `REBUILT_FROM_RAW` | `python scripts/run_permutation_test_7ep.py` | Full B=1000 null distribution (seeds 0..999) |
| 36 | `reports/7ep/permutation_7ep_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_permutation_test_7ep.py` | Structured permutation test p-values |
| 37 | `reports/7ep/permutation_7ep_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_permutation_test_7ep.py` | Markdown permutation report for P3 and P4 |
| 38 | `data/processed_7ep/planted_realscale_7ep_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_planted_realscale_7ep.py` | Synthetic planted structure predictions |
| 39 | `reports/7ep/planted_realscale_7ep_report.json` | `REBUILT_FROM_RAW` | `python scripts/run_planted_realscale_7ep.py` | Statistical power analysis results |
| 40 | `reports/7ep/planted_realscale_7ep_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_planted_realscale_7ep.py` | Power analysis verification report |
| 41 | `data/processed_7ep/e5_removed_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_e5_removed_sensitivity.py` | Prediction rows for E5-removed ablation (N=93) |
| 42 | `reports/7ep/e5_removed_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_e5_removed_sensitivity.py` | E5-removed sensitivity metrics |
| 43 | `reports/7ep/e5_removed_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_e5_removed_sensitivity.py` | E5-removed ablation Markdown report |
| 44 | `reports/7ep/holm_claim_rule_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_holm_claim_rule.py` | Formal Holm-Bonferroni multi-testing results |
| 45 | `reports/7ep/holm_claim_rule_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_holm_claim_rule.py` | Holm decision rule audit report |
| 46 | `reports/7ep/diagnostics_7ep.json` | `REBUILT_FROM_RAW` | `python scripts/run_diagnostics_7ep.py` | Extended transition diagnostics results |
| 47 | `reports/7ep/diagnostics_7ep.md` | `REBUILT_FROM_RAW` | `python scripts/run_diagnostics_7ep.py` | Diagnostic analysis report |
| 48 | `reports/7ep/e5_hit1_change_diagnostic.json` | `REBUILT_FROM_RAW` | `python scripts/run_e5_hit1_diagnostic.py` | Investigation of E5 technique Hit@1 drop |
| 49 | `reports/7ep/e5_hit1_change_diagnostic.md` | `REBUILT_FROM_RAW` | `python scripts/run_e5_hit1_diagnostic.py` | E5 Hit@1 drop explanation report |
| 50 | `data/processed_7ep/tie_sensitivity_7ep_samples.csv` | `REBUILT_FROM_RAW` | `python scripts/run_tie_sensitivity_7ep.py` | Per-sample tie status and bound contributions |
| 51 | `reports/7ep/tie_sensitivity_7ep.json` | `REBUILT_FROM_RAW` | `python scripts/run_tie_sensitivity_7ep.py` | Bound A and Bound B exact expectations |
| 52 | `reports/7ep/tie_sensitivity_7ep.md` | `REBUILT_FROM_RAW` | `python scripts/run_tie_sensitivity_7ep.py` | Tie sensitivity analysis report |
| 53 | `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv` | `REBUILT_FROM_RAW` | `python scripts/run_exploratory_tactic_conditioned.py` | Exploratory tactic-conditioned prediction rows |
| 54 | `reports/7ep/exploratory_tactic_conditioned_results.json` | `REBUILT_FROM_RAW` | `python scripts/run_exploratory_tactic_conditioned.py` | Exploratory model metrics |
| 55 | `reports/7ep/exploratory_tactic_conditioned_report.md` | `REBUILT_FROM_RAW` | `python scripts/run_exploratory_tactic_conditioned.py` | Exploratory model negative verdict report |
| 56 | `artifacts/7ep/production_model/collapsed_full.json` | `REBUILT_FROM_RAW` | `python scripts/train_production_model.py` | Trained production model weights (technique) |
| 57 | `artifacts/7ep/production_model/tactic_collapsed.json` | `REBUILT_FROM_RAW` | `python scripts/train_production_model.py` | Trained production model weights (tactic) |
| 58 | `artifacts/7ep/production_model/manifest.json` | `REBUILT_FROM_RAW` | `python scripts/train_production_model.py` | Production model artifact manifest |
| 59 | `data/processed_7ep/prediction_records_loeo.jsonl` | `REBUILT_FROM_RAW` | `python scripts/build_prediction_records.py` | 171 explainable prediction records (Schema 1.1.0) |
| 60 | `reports/7ep/prediction_record_examples.md` | `REBUILT_FROM_RAW` | `python scripts/build_prediction_records.py` | Exemplar explainability records |
| 61 | `reports/7ep/requirements_trace.md` | `REBUILT_FROM_RAW` | `python scripts/build_requirements_trace.py` | Proposal requirements traceability matrix |
