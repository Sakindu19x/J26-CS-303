# Baseline Rebuild Scope Classification (Part S5 Clean Clone Rebuild)

**Generated:** 2026-10-16 00:48:23Z  
**Component:** Component 4 (`c4`)  
**Scope:** 61 Protected Baseline Files Across All Baselines

## 1. Executive Summary

| Category | Count | Percentage |
|:---|:---:|:---:|
| **REBUILT_FROM_RAW** | 61 | 100.0% |
| **COPIED_FROM_GIT_ONLY** | 0 | 0.0% |
| **Total Protected Baselines** | **61** | **100.0%** |

Every single protected baseline file is deleted prior to rebuild and regenerated deterministically from raw scenario archives (`scenario_*.zip`) and tracked ATT&CK reference data in an isolated clean clone (`C:\c4_clean_clone_s5`).

## 2. Rebuild Scope Inventory

| # | Relative Path | Classification | Regenerating Command | SHA-256 (Run 1) | Run 2 Parity |
|:---:|:---|:---:|:---|:---|:---:|
| 1 | `reports/evaluation_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a0129000fc380a77...` | **MATCH** |
| 2 | `reports/evaluation_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `b99f93f2b738593a...` | **MATCH** |
| 3 | `data/processed/evaluation_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `3d152046cdc773e7...` | **MATCH** |
| 4 | `data/processed/attack_sequences.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `d76fcadc27b510b3...` | **MATCH** |
| 5 | `data/processed/attack_timelines.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `5592c69735495a65...` | **MATCH** |
| 6 | `data/processed/loeo_folds.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a4bf2fa577e54b3e...` | **MATCH** |
| 7 | `data/processed/next_technique_samples.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `6208603ce67e673a...` | **MATCH** |
| 8 | `data/processed/normalized_events.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `963f37f74b2497c6...` | **MATCH** |
| 9 | `data/processed/technique_tactic_reference.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `087c390fc2f5abca...` | **MATCH** |
| 10 | `reports/data_quality_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `56fea61d59f52cf0...` | **MATCH** |
| 11 | `reports/timeline_validation_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `0f5d0832c6a0c0dc...` | **MATCH** |
| 12 | `reports/tactic_discrepancy_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `0621ee6ad3d00253...` | **MATCH** |
| 13 | `reports/sequence_statistics.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `dc1eb91ba37fadee...` | **MATCH** |
| 14 | `reports/tactic_evaluation_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `3d14f459a0f12200...` | **MATCH** |
| 15 | `reports/tactic_evaluation_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `64bd267d3520ca9e...` | **MATCH** |
| 16 | `data/processed/tactic_evaluation_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `af213f80e8ebd72d...` | **MATCH** |
| 17 | `data/processed_7ep/attack_sequences.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `f835cee2c0272fd0...` | **MATCH** |
| 18 | `data/processed_7ep/attack_timelines.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `81f1e68e4c896cc3...` | **MATCH** |
| 19 | `data/processed_7ep/loeo_folds.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `765233e5c89e79f5...` | **MATCH** |
| 20 | `data/processed_7ep/next_technique_samples.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a5b779f64904a4ae...` | **MATCH** |
| 21 | `data/processed_7ep/normalized_events.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `346919e2d23dd293...` | **MATCH** |
| 22 | `data/processed_7ep/technique_tactic_reference.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `087c390fc2f5abca...` | **MATCH** |
| 23 | `reports/7ep/data_quality_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `3d0fc4bccec33220...` | **MATCH** |
| 24 | `reports/7ep/timeline_validation_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `e84c43cd773df2d6...` | **MATCH** |
| 25 | `reports/7ep/tactic_discrepancy_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `381ca059854c6073...` | **MATCH** |
| 26 | `reports/7ep/sequence_statistics.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `faebd88c67a9e6e5...` | **MATCH** |
| 27 | `data/processed_7ep/evaluation_7ep_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `6b1edbfd33b03388...` | **MATCH** |
| 28 | `reports/7ep/evaluation_7ep_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `61888fcb4824705a...` | **MATCH** |
| 29 | `reports/7ep/evaluation_7ep_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `d358af27b4d2787f...` | **MATCH** |
| 30 | `data/processed_7ep/learning_curve_7ep.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `6b43483d0800a1c5...` | **MATCH** |
| 31 | `reports/7ep/learning_curve_7ep_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `826b964dfe0c9661...` | **MATCH** |
| 32 | `reports/7ep/learning_curve_7ep_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `00a5947ec909691c...` | **MATCH** |
| 33 | `reports/7ep/learning_curve_7ep.png` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `6477f996ef65d8db...` | **MATCH** |
| 34 | `reports/7ep/learning_curve_7ep_plot_data.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `b4aa2bbb6b296e02...` | **MATCH** |
| 35 | `data/processed_7ep/permutation_7ep_null_distribution.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `803b342afc594066...` | **MATCH** |
| 36 | `reports/7ep/permutation_7ep_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `81344d37636d8802...` | **MATCH** |
| 37 | `reports/7ep/permutation_7ep_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `ae3f1bdc75408820...` | **MATCH** |
| 38 | `data/processed_7ep/planted_realscale_7ep_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `410e90d2e83440f8...` | **MATCH** |
| 39 | `reports/7ep/planted_realscale_7ep_report.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `b3268be7fb131bb4...` | **MATCH** |
| 40 | `reports/7ep/planted_realscale_7ep_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a8545dc96a78cb4f...` | **MATCH** |
| 41 | `data/processed_7ep/e5_removed_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `60cb6e3e0cddfc9e...` | **MATCH** |
| 42 | `reports/7ep/e5_removed_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `40582dee4d868410...` | **MATCH** |
| 43 | `reports/7ep/e5_removed_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `95c4b223b4ed7136...` | **MATCH** |
| 44 | `reports/7ep/holm_claim_rule_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `b54d334e3137e0a9...` | **MATCH** |
| 45 | `reports/7ep/holm_claim_rule_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `e8e1052eb762ef81...` | **MATCH** |
| 46 | `reports/7ep/diagnostics_7ep.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a370e03f002571fa...` | **MATCH** |
| 47 | `reports/7ep/diagnostics_7ep.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `78141dffb359f877...` | **MATCH** |
| 48 | `reports/7ep/e5_hit1_change_diagnostic.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `3d7533ae5a928cd8...` | **MATCH** |
| 49 | `reports/7ep/e5_hit1_change_diagnostic.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `9e10a8892c1930ed...` | **MATCH** |
| 50 | `data/processed_7ep/tie_sensitivity_7ep_samples.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `de5178196ede4af5...` | **MATCH** |
| 51 | `reports/7ep/tie_sensitivity_7ep.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a7f9263237440954...` | **MATCH** |
| 52 | `reports/7ep/tie_sensitivity_7ep.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `125d0b5c31e85d2c...` | **MATCH** |
| 53 | `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `a2fb5f358b08a5b9...` | **MATCH** |
| 54 | `reports/7ep/exploratory_tactic_conditioned_results.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `72ce8ad8cc7c12b3...` | **MATCH** |
| 55 | `reports/7ep/exploratory_tactic_conditioned_report.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `358618de9d07e3ae...` | **MATCH** |
| 56 | `artifacts/7ep/production_model/collapsed_full.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `73002ab557b86143...` | **MATCH** |
| 57 | `artifacts/7ep/production_model/tactic_collapsed.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `250dd1f09f5b3c20...` | **MATCH** |
| 58 | `artifacts/7ep/production_model/manifest.json` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `b2dd54c51b41e6c6...` | **MATCH** |
| 59 | `data/processed_7ep/prediction_records_loeo.jsonl` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `373bc11b0b1a3a42...` | **MATCH** |
| 60 | `reports/7ep/prediction_record_examples.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `6becdc124ffac443...` | **MATCH** |
| 61 | `reports/7ep/requirements_trace.md` | `REBUILT_FROM_RAW` | `scripts/reproduce_all.py --rebuild` | `fa4c437c50b54f92...` | **MATCH** |
