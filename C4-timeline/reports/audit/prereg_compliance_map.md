# Pre-Registration Compliance Map

Generated automatically by `scripts/build_prereg_compliance_map.py`.
Maps pre-registration sections 1–11 and Amendments 1–7 to output files, scripts, verifiers, baseline entries, and computed statuses.

## 1. Pre-Registration Protocol Compliance (Sections 1–11)

| Section | Title | Output File(s) | Verifier | Baseline Match | Verifier Status | Overall |
|:---|:---|:---|:---|:---:|:---:|:---:|
| **Section 1** | Episodes and Archive Identification | `reports/raw_archive_hashes.json`<br>`reports/raw_archive_hashes_extended.json`<br>`docs/data_provenance.md` | `scripts/verify_all_hashes.py` | N/A | PASS | **COMPLIANT** |
| **Section 2** | Folds and Partitioning | `data/processed_7ep/attack_sequences.json`<br>`reports/7ep/evaluation_7ep_results.json` | `scripts/verify_stage1_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 3** | Evaluation Slices | `data/processed_7ep/attack_sequences.json`<br>`reports/7ep/evaluation_7ep_results.json` | `scripts/verify_evaluation_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 4** | Models and Tuning Constraints | `artifacts/7ep/production_model/manifest.json`<br>`reports/7ep/evaluation_7ep_results.json` | `scripts/verify_prediction_records.py` | TRUE | PASS | **COMPLIANT** |
| **Section 5** | Evaluation Metrics | `reports/7ep/evaluation_7ep_results.json`<br>`reports/7ep/evaluation_7ep_report.md` | `scripts/verify_evaluation_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 6** | Primary Hypotheses and Statistical Comparisons | `reports/7ep/evaluation_7ep_results.json`<br>`reports/7ep/evaluation_7ep_report.md` | `scripts/verify_holm_claim_rule.py` | TRUE | PASS | **COMPLIANT** |
| **Section 7** | Learning Curve Protocol | `reports/7ep/learning_curve_7ep_results.json`<br>`reports/7ep/learning_curve_7ep_report.md` | `scripts/verify_learning_curve_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 8** | Handling of Episode E5 (Sensitivity Analysis) | `reports/7ep/e5_removed_results.json`<br>`reports/7ep/e5_removed_report.md` | `scripts/verify_e5_removed.py` | TRUE | PASS | **COMPLIANT** |
| **Section 9** | Real-Scale Planted Structure Power Analysis (A4 Re-Run) | `reports/7ep/planted_realscale_7ep_report.json`<br>`reports/7ep/planted_realscale_7ep_report.md` | `scripts/verify_planted_realscale_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 10** | Permutation Null Hypotheses at 7 Episodes | `reports/7ep/permutation_7ep_report.json`<br>`reports/7ep/permutation_7ep_report.md` | `scripts/verify_permutation_7ep.py` | TRUE | PASS | **COMPLIANT** |
| **Section 11** | Immutability and Pre-Registration Protocol | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |

## 2. Pre-Registration Amendments (Amendments 1–7)

| Amendment | Title | Output File(s) | Verifier | Baseline Match | Verifier Status | Overall |
|:---|:---|:---|:---|:---:|:---:|:---:|
| **Amendment 1** | Corrections to Sec 1, 4, 5, 8, 9, 6, 10 before inference | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |
| **Amendment 2** | Scope & correction of scenario_6_macro_library and supersession | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |
| **Amendment 3** | Verbatim original heading titles & repository search count | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |
| **Amendment 4** | Retraction of informal titles & record of Amendment 1 changes | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |
| **Amendment 5** | Verification of committed repository text vs chat report | `reports/prereg_7episode_design.md` | `N/A` | N/A | N/A | **COMPLIANT** |
| **Amendment 6** | Wording and verification only; no numbers change | `reports/7ep/permutation_7ep_report.md`<br>`reports/permutation_test_v2_report.md`<br>`scripts/mutation_sweep.py`<br>`scripts/verify_evaluation.py` | `scripts/verify_evaluation.py` | MIXED | PASS | **COMPLIANT** |
| **Amendment 7** | Exploratory post hoc variant (Tactic-Conditioned Technique Prediction) | `reports/7ep/exploratory_tactic_conditioned_results.json`<br>`reports/7ep/exploratory_tactic_conditioned_report.md`<br>`data/processed_7ep/exploratory_tactic_conditioned_predictions.csv` | `scripts/verify_exploratory_tactic_conditioned.py` | TRUE | PASS | **COMPLIANT** |

## 3. Analyses That Are Not Pre-Registered

The following analyses were conceived and executed post hoc to investigate specific diagnostic findings. Each is explicitly designated **POST HOC** and does not alter the pre-registered hypothesis test verdict.

| Analysis Name | Classification | Description | Key Output Files | Script / Verifier |
|:---|:---:|:---|:---|:---|
| **diagnostics_7ep** | `POST HOC` | Cross-episode vocabulary overlap and transition diagnostic analyzing zero repeat transitions between different attack campaigns. | `reports/7ep/diagnostics_7ep.json`, `reports/7ep/diagnostics_7ep.md` | `scripts/run_diagnostics_7ep.py` / `scripts/verify_all_hashes.py` |
| **e5_hit1_change_diagnostic** | `POST HOC` | Diagnostic investigation of Episode E5 Hit@1 score behavior under LOEO cross-validation. | `reports/audit/e5_hit1_change_diagnostic.md` | `scripts/run_e5_hit1_change_diagnostic.py` / `scripts/verify_e5_hit1_diagnostic.py` |
| **tie_sensitivity_7ep** | `POST HOC` | Systematic tie-sensitivity analysis of Markov and Frequency predictions across all 171 LOEO prediction records under min, max, and random tie-breaking. | `reports/7ep/tie_sensitivity_7ep.json`, `reports/7ep/tie_sensitivity_7ep.md` | `scripts/run_tie_sensitivity_7ep.py` / `scripts/verify_tie_sensitivity_7ep.py` |
| **exploratory_tactic_conditioned** | `POST HOC` | Tactic-conditioned technique prediction variant pre-declared under Amendment 7 to evaluate whether tactic order signals project onto technique candidates. | `reports/7ep/exploratory_tactic_conditioned_results.json`, `reports/7ep/exploratory_tactic_conditioned_report.md`, `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv` | `scripts/run_exploratory_variant.py` / `scripts/verify_exploratory_tactic_conditioned.py` |

## 4. Deviations and Limits

| Deviation / Limit ID | Category | Description | Impact |
|:---|:---|:---|:---|
| **G8 loose** | Pre-registration Gate Limit | In synthetic real-scale planted structure analysis (reports/7ep/planted_realscale_7ep_report.md), gate G8 bound |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE) was loose at small sample sizes (V=82), though recovered consistency at larger sequence lengths. | Documented in planted real-scale report; G9 and G10 passed unconditionally. |
| **A2 history not reproducible** | Historical Reproducibility Limit | Historical intermediary files from early 4-episode A2 exploration cannot be recreated bit-for-bit identically due to missing random seeds in initial exploratory scratch scripts. All final reports and baselines remain frozen and verified. | Confined strictly to early scratch exploration history; does not affect any 4-episode or 7-episode benchmark conclusions. |
| **S2 excluded at 7 episodes** | Null Hypothesis Protocol Modification | Scheme S2 (unconstrained adjacent shuffle) was excluded in the 7-episode pre-registration design because 4-episode analysis proved it produces artificial adjacent identical transitions absent in collapsed sequences. Replaced by S1 (headline) and S3 (constrained). | Pre-registered and adhered to; S2 rows in 4-episode reports are marked as invalid nulls per 12c Rule C. |
| **Amendment 6 wording changes** | Reporting Neutralization | Speculative causal statements in permutation test reporting scripts were neutralized to factual difference statistic statements; Markov-minus-Frequency conclusion strings updated to explicitly state they do not test Markov vs Frequency (which is P1/P2). | Purely wording and verifier enhancements; zero experimental numbers or test results were modified. |
