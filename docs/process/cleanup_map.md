# Workspace Clean-up and Reorganisation Map (Part S2)

This document maps all file reorganisations, removals, and retentions executed during Part S2 clean-up.
Per Rule G6, scripts embedded in protected baselines are preserved in-place.

| Original Path | Target Path / Status | Action | Rationale |
|:---|:---|:---|:---|
| `docs/prompts/prompt15.md` | `docs/process/prompts/prompt15.md` | **MOVED** | Reorganized into docs/process/prompts/ |
| `docs/prompts/prompt16.md` | `docs/process/prompts/prompt16.md` | **MOVED** | Reorganized into docs/process/prompts/ |
| `reports/audit/q14_Q0_output.txt` | `reports/audit/history/q14_Q0_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q10_output.txt` | `reports/audit/history/q14_Q10_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q1_output.txt` | `reports/audit/history/q14_Q1_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q3_output.txt` | `reports/audit/history/q14_Q3_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q4_output.txt` | `reports/audit/history/q14_Q4_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q5_output.txt` | `reports/audit/history/q14_Q5_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q6_output.txt` | `reports/audit/history/q14_Q6_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q8_output.txt` | `reports/audit/history/q14_Q8_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q14_Q9_output.txt` | `reports/audit/history/q14_Q9_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R0_output.txt` | `reports/audit/history/q15_R0_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R1_output.txt` | `reports/audit/history/q15_R1_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R2_output.txt` | `reports/audit/history/q15_R2_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R3_output.txt` | `reports/audit/history/q15_R3_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R4_output.txt` | `reports/audit/history/q15_R4_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R5_output.txt` | `reports/audit/history/q15_R5_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R6_output.txt` | `reports/audit/history/q15_R6_output.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R7_git.txt` | `reports/audit/history/q15_R7_git.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `reports/audit/q15_R7_sweeps.txt` | `reports/audit/history/q15_R7_sweeps.txt` | **MOVED** | Archived legacy un-cited prompt run log |
| `scripts/append_q6_corrections.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit/run_s0.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit/run_s1.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_and_fix_line_endings.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_hash_coverage.py` | `scripts/audit/audit_hash_coverage.py` | **MOVED** | Reorganized into audit tool directory |
| `scripts/audit_lc_k6.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_new_archives.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_png_anomaly.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_prereg_strings.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_s1s3_unchanged.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/audit_tie_handling_code.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_amendment8.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_amendment9.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_claims_map.py` | `scripts/pipeline/s19_build_claims_map.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/build_final_audit_report.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_known_limitations.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_overnight_summary.py` | `scripts/pipeline/s20_build_overnight_summary.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/build_prediction_records.py` | `scripts/build_prediction_records.py` | **KEPT** | KEPT - name embedded in output (reports/7ep/requirements_trace.md) |
| `scripts/build_prereg_compliance_map.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/build_requirements_trace.py` | `scripts/build_requirements_trace.py` | **KEPT** | KEPT - name embedded in output (reports/7ep/requirements_trace.md) |
| `scripts/build_viva_pack.py` | `scripts/pipeline/s18_build_viva_pack.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/capture_dashboard_screenshots.py` | `scripts/dashboard/capture_dashboard_screenshots.py` | **MOVED** | Reorganized into dashboard runner directory |
| `scripts/capture_live_dashboard.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/check_full_b_reproducibility.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/check_planted_realscale_7ep_reproducibility.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/check_regression_gate.py` | `scripts/check_regression_gate.py` | **KEPT** | KEPT - used by tests/test_evaluation_7ep.py |
| `scripts/check_stage1_7ep_acceptance.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/compare_attack_versions.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/dev/print_tactic_audit.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/dev/verify_evaluation_independent.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/emit_final_table.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/generate_baseline_hashes_7ep_inference.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/generate_step_type_summary.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/measure_nfr1.py` | `scripts/measure_nfr1.py` | **KEPT** | KEPT - name embedded in output (reports/7ep/requirements_trace.md) |
| `scripts/mutation_sweep.py` | `scripts/mutation_sweep.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/mutation_sweep_claims_map.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/mutation_sweep_overnight_summary.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/mutation_sweep_requirements_trace.py` | `scripts/mutation_sweep_requirements_trace.py` | **KEPT** | KEPT - used for requirements trace mutation testing |
| `scripts/print_exempt_tokens.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/print_file.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/print_seed_samples.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/record_baseline_change.py` | `scripts/audit/record_baseline_change.py` | **MOVED** | Reorganized into audit tool directory |
| `scripts/record_q14_decision.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/reorganize_workspace.ps1` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/reproduce_all.py` | `scripts/reproduce_all.py` | **KEPT** | KEPT - canonical reproduction & verification harness |
| `scripts/reproduce_clean_clone.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_dashboard.ps1` | `scripts/dashboard/run_dashboard.ps1` | **MOVED** | Reorganized into dashboard runner directory |
| `scripts/run_diagnostics_7ep.py` | `scripts/pipeline/s12_diagnostics_7ep.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_e5_hit1_diagnostic.py` | `scripts/pipeline/s13_e5_hit1_diagnostic.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_e5_removed_sensitivity.py` | `scripts/pipeline/s10_e5_removed_sensitivity.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_evaluation.py` | `scripts/pipeline/s04_evaluation_4ep_technique.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_evaluation_7ep.py` | `scripts/pipeline/s06_evaluation_7ep.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_exploratory_tactic_conditioned.py` | `scripts/pipeline/s15_exploratory_tactic_conditioned.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_holm_claim_rule.py` | `scripts/run_holm_claim_rule.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/run_inventory.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_learning_curve_7ep.py` | `scripts/pipeline/s07_learning_curve_7ep.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_normalization.py` | `scripts/pipeline/s01_normalize_events.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_permutation_test.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_permutation_test_7ep.py` | `scripts/run_permutation_test_7ep.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/run_permutation_test_v2.py` | `scripts/run_permutation_test_v2.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/run_planted_realscale.py` | `scripts/run_planted_realscale.py` | **KEPT** | KEPT - used by tests/test_planted_realscale.py |
| `scripts/run_planted_realscale_7ep.py` | `scripts/pipeline/s09_planted_power_7ep.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_planted_structure.py` | `scripts/run_planted_structure.py` | **KEPT** | KEPT - used by tests/test_planted_structure.py |
| `scripts/run_q0_baseline.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q2_clean_clone.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q3_pipeline.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q4_trace.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q5_claims.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q6_summary.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q7_gates.py` | `scripts/run_q7_gates.py` | **KEPT** | KEPT - used by reports/viva/claims.json (CLAIM-10, CLAIM-11) |
| `scripts/run_q8_dashboard.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_q9_nfr1.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_r0.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_r7.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/run_samples_and_stats.py` | `scripts/pipeline/s03_samples_and_stats.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_tactic_evaluation.py` | `scripts/pipeline/s05_evaluation_4ep_tactic.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_tie_sensitivity_7ep.py` | `scripts/pipeline/s14_tie_sensitivity_7ep.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/run_timeline_pipeline.py` | `scripts/pipeline/s02_timeline_pipeline.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/summarize_inventory.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/test_q1_proof.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/train_production_model.py` | `scripts/pipeline/s16_train_production_model.py` | **MOVED** | Standardized pipeline stage script |
| `scripts/update_ledger.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/validate_coverage_map.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/verify/recheck_s1.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `scripts/verify_all_hashes.py` | `scripts/verify/verify_all_hashes.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_claims_map.py` | `scripts/verify/verify_claims_map.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_e5_hit1_diagnostic.py` | `scripts/verify/verify_e5_hit1_diagnostic.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_e5_removed.py` | `scripts/verify/verify_e5_removed.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_evaluation.py` | `scripts/verify_evaluation.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/verify_evaluation_7ep.py` | `scripts/verify/verify_evaluation_7ep.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_exploratory_tactic_conditioned.py` | `scripts/verify/verify_exploratory_tactic_conditioned.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_holm_claim_rule.py` | `scripts/verify/verify_holm_claim_rule.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_learning_curve_7ep.py` | `scripts/verify/verify_learning_curve_7ep.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_nfr1.py` | `scripts/verify/verify_nfr1.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_overnight_summary.py` | `scripts/verify/verify_overnight_summary.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_permutation_7ep.py` | `scripts/verify_permutation_7ep.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/verify_permutation_test.py` | `scripts/verify/verify_permutation_test.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_permutation_test_v2.py` | `scripts/verify_permutation_test_v2.py` | **KEPT** | KEPT - name embedded in output (reports/prereg_7episode_design.md) |
| `scripts/verify_planted_realscale.py` | `scripts/verify/verify_planted_realscale.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_planted_realscale_7ep.py` | `scripts/verify/verify_planted_realscale_7ep.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_planted_structure.py` | `scripts/verify/verify_planted_structure.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_prediction_records.py` | `scripts/verify/verify_prediction_records.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_requirements_trace.py` | `scripts/verify/verify_requirements_trace.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_stage1_7ep.py` | `scripts/verify/verify_stage1_7ep.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_tactic_evaluation.py` | `scripts/verify/verify_tactic_evaluation.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_tie_sensitivity_7ep.py` | `scripts/verify/verify_tie_sensitivity_7ep.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/verify_viva_pack.py` | `scripts/verify/verify_viva_pack.py` | **MOVED** | Reorganized into dedicated verifier directory |
| `scripts/write_p1_findings.py` | `-` | **REMOVED** | Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3) |
| `tests/test_dashboard_q8.py` | `tests/test_dashboard_launch.py` | **MOVED** | Renamed to descriptive test name without prompt number |
