# Test Coverage Map: Evaluation Reports vs Automated Consistency Checks

This document maps EVERY table and EVERY generated sentence that contains a number in both `reports/tactic_evaluation_report.md` and `reports/evaluation_report.md` to the test in the test suite that checks it.

---

## 1. Secondary Next-Tactic Evaluation Report (`reports/tactic_evaluation_report.md`)

| Section Heading | Element Type | Content Description | Checking Test |
|---|---|---|---|
| **1. Setup and Sample Counts** | Sentence | 14 ATT&CK Enterprise v16.1 tactics | `tests/test_tactic_evaluation_consistency.py::test_tactic_sample_counts_per_episode` |
| **1. Setup and Sample Counts** | Sentence | 4 leave-one-episode-out folds | `tests/test_tactic_evaluation_consistency.py::test_tactic_sample_counts_per_episode` |
| **1. Setup and Sample Counts** | Table 1.1 | Slice Sample Counts (N per episode E1-E4 and Total N) | `tests/test_tactic_evaluation_consistency.py::test_tactic_sample_counts_per_episode` |
| **2. Headline Results** | Table 2.1 | Headline Results: N, hit1, hit3 | `tests/test_tactic_evaluation_consistency.py::test_headline_rows_and_percentages_match_recomputed` |
| **2. Headline Results** | Table 2.1 | Headline Results: Top-1 %, Top-3 %, Fold-mean Top-1/3 %, Coverage %, Ceiling % | `tests/test_tactic_evaluation_consistency.py::test_headline_rows_and_percentages_match_recomputed` |
| **2. Headline Results** | Table 2.2 | Wilson 95% Score Intervals (Pooled) | `tests/test_tactic_evaluation_consistency.py::test_wilson_intervals_matches_recomputed` |
| **2. Headline Results** | Table 2.3 | Per-Fold Performance Breakdown (All 48 rows across 4 configurations, 4 folds, 3 methods) | `tests/test_tactic_evaluation_consistency.py::test_per_fold_breakdown_matches_recomputed` |
| **3. Diagnostic Baselines** | Table 3.1 | Reference Baselines: Repeat-current-set (counts, percentages, Wilson intervals) | `tests/test_tactic_evaluation_consistency.py::test_reference_baselines_match_recomputed` |
| **3. Diagnostic Baselines** | Table 3.1 | Reference Baselines: Random-guess (expected Top-1 and Top-3 rates from 14 tactics) | `tests/test_tactic_evaluation_consistency.py::test_reference_baselines_match_recomputed` |
| **3. Diagnostic Baselines** | Table 3.2 | Self-Repeat Rates Across Slices (N, equal count/rate, overlap count/rate) | `tests/test_tactic_evaluation_consistency.py::test_self_repeat_and_strict_single_tactic_match_recomputed` |
| **3. Diagnostic Baselines** | Table 3.3 | Strict Single-Tactic Target Subset (N=33, N=64; all methods hit1/hit3 and repeat hit1/hit3) | `tests/test_tactic_evaluation_consistency.py::test_self_repeat_and_strict_single_tactic_match_recomputed` |
| **4. Paired Comparison** | Table 4.1 | 2x2 Paired Tables (Markov vs Frequency) at k=1 and k=3 (both, markov-only, freq-only, neither) | `tests/test_tactic_evaluation_consistency.py::test_paired_2x2_and_frequency_only_split_match_recomputed` |
| **4. Paired Comparison** | Table 4.2 | Frequency-Only Hits Split by Markov Status (status ok vs abstained) at k=1 and k=3 | `tests/test_tactic_evaluation_consistency.py::test_paired_2x2_and_frequency_only_split_match_recomputed` |
| **5. Covered-Only Comparison** | Table 5.1 | Covered-Only Comparison Table (Markov status ok: N=50, N=86; hit1/hit3 for all methods) | `tests/test_tactic_evaluation_consistency.py::test_paired_2x2_and_frequency_only_split_match_recomputed` |
| **6. Tie Diagnostic** | Table 6.1 | Tie Diagnostic Table (Covered N, Top-1 tied, Top-3 boundary tied, n_equal_top >= 3, tied vs not-tied hits) | `tests/test_tactic_evaluation_consistency.py::test_tie_diagnostic_matches_recomputed` |
| **6. Tie Diagnostic** | Sentence | `tactic_collapsed`: 8 of 50 Markov predictions decided by tie-break | `tests/test_tactic_evaluation_consistency.py::test_tie_diagnostic_matches_recomputed` |
| **6. Tie Diagnostic** | Sentence | `tactic_raw`: 7 of 86 Markov predictions decided by tie-break | `tests/test_tactic_evaluation_consistency.py::test_tie_diagnostic_matches_recomputed` |
| **7. Hit Concentration** | Table 7.1 | Hit Concentration by Tactic (`tactic_collapsed`: hit1 and hit3 samples per method) | `tests/test_tactic_evaluation_consistency.py::test_hit_concentration_matches_recomputed` |
| **7. Hit Concentration** | Table 7.2 | Most frequent target tactics pooled over all four episodes (Rank 1-5, target count) | `tests/test_tactic_evaluation_consistency.py::test_hit_concentration_matches_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Sentence | Total events differing between official tactics and ground-truth dataset tactics: 25 | `tests/test_tactic_evaluation_consistency.py::test_discrepancy_table_and_counts_match_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Sentence | Type (a) (dataset contains tactic NOT in official MITRE set): 8 events | `tests/test_tactic_evaluation_consistency.py::test_discrepancy_table_and_counts_match_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Sentence | Type (b) (dataset tactic set is strict subset of official MITRE set): 17 events | `tests/test_tactic_evaluation_consistency.py::test_discrepancy_table_and_counts_match_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Table 8.1 | Discrepant Events Breakdown (all 25 individual event IDs and tactic classifications) | `tests/test_tactic_evaluation_consistency.py::test_discrepancy_table_and_counts_match_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Table 8.2 | Sensitivity Results (Dataset Tactics): N, hit1, hit3, Top-1 %, Top-3 %, Fold-mean % | `tests/test_tactic_evaluation_consistency.py::test_dataset_tactics_sensitivity_and_ordering_match_recomputed` |
| **8. Sensitivity: Dataset Tactics** | Sentences | Markov vs Frequency Ordering Comparison (4 bullet sentences for collapsed/raw at k=1/3; recomputed 2 of 4 change ordering) | `tests/test_tactic_evaluation_consistency.py::test_dataset_tactics_sensitivity_and_ordering_match_recomputed` |
| **9. Derived-Tactic Evaluation** | Table 9.1 | Derived-Tactic Evaluation: every column (N, hit1, hit3, Top-1 %, Top-3 %, Wilson intervals, coverage %) | `tests/test_tactic_evaluation_consistency.py::test_derived_tactics_table_matches_recomputed` |
| **9. Derived-Tactic Evaluation** | Table 9.2 | Mean Official Tactics per Top-1 Predicted Technique (Evaluated N, mean tactics) | `tests/test_tactic_evaluation_consistency.py::test_derived_tactics_table_matches_recomputed` |

---

## 2. Primary Next-Technique Evaluation Report (`reports/evaluation_report.md`)

| Section Heading | Element Type | Content Description | Checking Test |
|---|---|---|---|
| **1. Setup** | Sentence | primary configuration `collapsed_full` (N=67) | `tests/test_evaluation_consistency.py::test_markdown_report_matches_recomputation` |
| **1. Setup** | Sentence | 4 leave-one-episode-out folds | `tests/test_evaluation_consistency.py::test_recomputation_matches_json_and_internal_consistency` |
| **1. Setup** | Sentence | prediction parameter k=3 | `tests/test_evaluation_consistency.py::test_recomputation_matches_json_and_internal_consistency` |
| **3. Results by configuration and method** | Table 3.1 | Results table: N, hit1, hit3, Top-1 %, Top-3 %, Fold-mean Top-1/3 %, Markov coverage | `tests/test_evaluation_consistency.py::test_markdown_report_matches_recomputation` |
| **3. Results by configuration and method** | Table 3.2 | Wilson 95% intervals (pooled) for all 5 configurations and 3 methods | `tests/test_evaluation_consistency.py::test_wilson_intervals_section_3_matches_report` |
| **3. Results by configuration and method** | Sentences | Markov versus frequency baseline comparison sentences (5 bullet sentences across configurations) | `tests/test_evaluation_consistency.py::test_section_3_markov_vs_frequency_sentences_match_recomputed` |
| **4. Per-fold results** | Table 4.1 | Per-fold results table (all 60 rows across 5 configurations, 4 folds, 3 methods) | `tests/test_evaluation_consistency.py::test_section_4_per_fold_table_matches_recomputed` |
| **5. Coverage and ceiling** | Table 5.1 | Coverage and ceiling table: N, Markov covered, Coverage %, Ceiling count, Ceiling % | `tests/test_evaluation_consistency.py::test_coverage_and_covered_only_sections_match_recompute` |
| **5. Coverage and ceiling** | Table 5.2 | Per-fold ceiling and coverage for `collapsed_full` (4 fold rows: N, Covered, Ceiling hits) | `tests/test_evaluation_consistency.py::test_section_5_per_fold_ceiling_and_coverage_matches_recomputed` |
| **6. Covered-only comparison** | Table 6.1 | Covered-only comparison table: Covered N, Markov Top-1/3, Frequency Top-1/3, Fallback Top-1/3 | `tests/test_evaluation_consistency.py::test_coverage_and_covered_only_sections_match_recompute` |
| **7. Strict subset** | Table 7.1 | Strict single-target subset table: Single-target N, all method hit counts | `tests/test_evaluation_consistency.py::test_strict_single_target_subset_matches_report` |
| **8. Precision / recall / F1** | Table 8.1 | Precision / recall / F1 table: TP, FP, FN, Micro P/R/F1, Macro P/R/F1, Classes | `tests/test_evaluation_consistency.py::test_micro_precision_recall_f1_collapsed_full_matches_report` |
| **9. Paired comparison** | Table 9.1 | Paired comparison 2x2 table across all 5 configurations at k=1 and k=3 | `tests/test_evaluation_consistency.py::test_markdown_report_matches_recomputation` |
| **9. Paired comparison** | Table 9.2 | Frequency-only hits split by Markov status table across all 5 configurations at k=1 and k=3 | `tests/test_evaluation_consistency.py::test_frequency_only_split_and_support_buckets_match_recompute` |
| **9. Paired comparison** | Sentences | Frequency-only hits split bullet sentences (10 generated bullet sentences) | `tests/test_evaluation_consistency.py::test_generated_sentences_numbers_backed_by_recompute` |
| **10. Sensitivity configurations** | Sentence | The `collapsed_full_no_s006` configuration has N=66 versus N=67 for `collapsed_full` | `tests/test_evaluation_consistency.py::test_section_10_sensitivity_sentences_match_recomputed` |
| **11. Confusion analysis** | Table 11.1 | Most frequent Top-1 errors at full ID (10 error transition rows and counts) | `tests/test_evaluation_consistency.py::test_section_11_top1_errors_and_confusion_sentence_match_recomputed` |
| **11. Confusion analysis** | Table 11.2 | Abstentions by target technique table (15 target techniques and counts) | `tests/test_evaluation_consistency.py::test_abstentions_by_target_technique_matches_report` |
| **11. Confusion analysis** | Sentence | Parent-level confusion matrix sentence: N=48, 33 target rows x 15 columns, 42 of 495 non-zero (8.48%) | `tests/test_evaluation_consistency.py::test_section_11_top1_errors_and_confusion_sentence_match_recomputed` |
| **12. Examples chosen by rule** | Subheadings | Headings: (i) (1 shown), (ii) (2 shown), (iii) (3 shown) | `tests/test_evaluation_consistency.py::test_generated_sentences_numbers_backed_by_recompute` |
| **12. Examples chosen by rule** | Tables 12.1-3 | Concrete example tables for Markov Top-1, Frequency-only Top-1, and Abstentions | `tests/test_evaluation_consistency.py::test_section_12_examples_tables_match_recomputed` |
| **13. Diagnostics** | Table 13.1 | 13.1 Self-repeat rate per slice (N, target shares count/rate, target equals count/rate) | `tests/test_evaluation_consistency.py::test_self_repeat_and_repeat_current_set_matches_report` |
| **13. Diagnostics** | Table 13.2 | 13.2 Repeat-current-set reference table: N, Top-1/3 hits, rates, Wilson intervals | `tests/test_evaluation_consistency.py::test_self_repeat_and_repeat_current_set_matches_report` |
| **13. Diagnostics** | Sentences | 13.2 Comparison sentences with proposal methods on same slice (4 bullet sentences) | `tests/test_evaluation_consistency.py::test_section_13_diagnostics_match_recomputed` |
| **13. Diagnostics** | Table 13.3 | 13.3 Markov hit rate by support strength table (support_episodes 1, 2, 3 buckets) | `tests/test_evaluation_consistency.py::test_frequency_only_split_and_support_buckets_match_recompute` |
| **13. Diagnostics** | Table 13.4 | 13.4 Frequency baseline predictions per fold (12 prediction rows: fold, rank, technique, prob, counts) | `tests/test_evaluation_consistency.py::test_section_13_diagnostics_match_recomputed` |
| **13. Diagnostics** | Sentences | 13.4 Bullet sentences: test samples containing top targets (4 bullet sentences for folds 1-4) | `tests/test_evaluation_consistency.py::test_section_13_diagnostics_match_recomputed` |
| **13. Diagnostics** | Table 13.5 | 13.5 Tie diagnostic table: Covered N, Top-1 tied, Top-3 boundary tied, n_equal_top >= 3, tied/untied hits | `tests/test_evaluation_consistency.py::test_tie_diagnostic_and_hit_concentration_match_recompute` |
| **13. Diagnostics** | Sentences | 13.5 Tie diagnostic bullet sentences (5 bullet sentences across configurations) | `tests/test_evaluation_consistency.py::test_tie_diagnostic_and_hit_concentration_match_recompute` |
| **13. Diagnostics** | Table 13.6 | 13.6 Hit concentration by technique table (`collapsed_full` hit samples) | `tests/test_evaluation_consistency.py::test_tie_diagnostic_and_hit_concentration_match_recompute` |
| **13. Diagnostics** | Table 13.6.2 | Most frequent targets pooled over all 4 episodes (Ranks 1-5, target counts) | `tests/test_evaluation_consistency.py::test_section_13_diagnostics_match_recomputed` |
| **13. Diagnostics** | Sentence | 13.6 Concentration sentence: 7 of 8 Frequency Top-3 hits involve technique T1105 | `tests/test_evaluation_consistency.py::test_section_13_diagnostics_match_recomputed` |
| **14. Limitations** | Sentences | Sample size (67 samples, 4 episodes); Closed vocabulary (35/67, 52.24%); Coverage (34/67, 50.75%) | `tests/test_evaluation_consistency.py::test_generated_sentences_numbers_backed_by_recompute` |

---

## 3. Structural Sequence and Sample Reconstruction Checks

| Component | Target Description | Checking Test |
|---|---|---|
| **Tactic Sample Reconstruction** | Rebuilds tactic evaluation samples from `attack_sequences.json` and verifies against `tactic_evaluation_predictions.csv` | `tests/test_tactic_evaluation_consistency.py::test_tactic_sample_reconstruction_from_sequences` |
| **Technique Sample Reconstruction** | Rebuilds technique evaluation samples from `attack_sequences.json` and verifies against `evaluation_predictions.csv` | `tests/test_evaluation_consistency.py::test_technique_sample_reconstruction_from_sequences` |
| **Technique Sequence Collapse** | Merges raw per-event technique sets from `attack_sequences.json` and asserts exact equality with stored collapsed sequences per episode | `tests/test_evaluation_consistency.py::test_technique_collapse_reconstruction_matches` |

---

## 4. Non-Tautology Verification Suite (`tests/test_checks_detect_errors.py`)

| Check Tested | Tested In-Memory Mutation | Verifying Failure Test |
|---|---|---|
| `check_headline_counts` | Corrupt Top-1 hit count from 11 to 99 in `tactic_collapsed` markov | `test_headline_counts_detects_error` |
| `check_headline_percentages` | Corrupt Top-1 percentage from 20.75% to 99.99% in `tactic_collapsed` markov | `test_headline_percentages_detects_error` |
| `check_paired_2x2` | Corrupt Both-hit cell from 2 to 99 in `tactic_collapsed` k=1 | `test_paired_2x2_detects_error` |
| `check_frequency_only_split` | Corrupt Frequency-only count from 7 to 99 in `tactic_collapsed` k=1 | `test_frequency_only_split_detects_error` |
| `check_tie_diagnostic` | Corrupt tie-break count from 8 to 99 in sentence | `test_tie_diagnostic_detects_error` |
| `check_sensitivity_sentence` | Corrupt ordering status from `**different**` to `**the same**` | `test_sensitivity_sentence_detects_error` |

---

## Summary (Mechanically Generated)

- **Direct Report File Inventory**:
  - `tactic_evaluation_report.md`: 17 contiguous table blocks, 26 non-table lines with digits.
  - `evaluation_report.md`: 22 contiguous table blocks, 73 non-table lines with digits.
- **Coverage Map Entries**:
  - Tactic evaluation map entries: 19 table entries, 8 sentence entries (total: 27).
  - Technique evaluation map entries: 20 table entries, 13 sentence entries (total: 33).
  - Total mapped items: 39 table entries, 21 sentence/subheading entries (total: 60).
- **Test Suite References**:
  - Total test references in map: 63 (33 unique test functions across the suite).
  - Missing test references: 0 (all test targets verified present in collected pytest tests).
- **Measured Mutation Sweep Sensitivity (Part C)**:
  - `tactic_evaluation_report.md`: 995 tokens total (15 exempt, 980 tested) -> 980 DETECTED (100.00%), 0 UNDETECTED.
  - `evaluation_report.md`: 1522 tokens total (39 exempt, 1483 tested) -> 1483 DETECTED (100.00%), 0 UNDETECTED.
  - Combined: 2463 tested numeric tokens across both reports -> 2463 DETECTED (100.00%), 0 UNDETECTED outside the explicit exempt list.
