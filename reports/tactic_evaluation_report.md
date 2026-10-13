Primary result remains technique-level, collapsed/full (reports/evaluation_report.md). This tactic-level evaluation is secondary and exploratory. All slices are reported; none is selected after the fact.

# C4 Secondary Next-Tactic Prediction: LOEO Evaluation Report

This report evaluates next-tactic prediction across the 14 MITRE ATT&CK Enterprise tactics. All models are strictly fitted on training episodes under Leave-One-Episode-Out (LOEO) cross-validation.

## 1. Setup and Sample Counts

- **Tactic Universe**: 14 ATT&CK Enterprise v16.1 tactics (shortname tokens, e.g. `initial-access`, `defense-evasion`).
- **Folds**: 4 leave-one-episode-out folds reusing `data/processed/loeo_folds.json`.

| Slice | Total N | E1 | E2 | E3 | E4 | Merge Rule |
|---|---|---|---|---|---|---|
| `tactic_collapsed` | 53 | 13 | 15 | 15 | 10 | Consecutive identical tactic sets collapsed |
| `tactic_raw` | 95 | 26 | 20 | 28 | 21 | Raw event transitions (no collapse) |

## 2. Headline Results (Official ATT&CK Tactics)

| Slice | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 | Coverage | Ceiling |
|---|---|---|---|---|---|---|---|---|---|---|
| `tactic_collapsed` | markov | 53 | 11 | 28 | 20.75% | 52.83% | 19.10% | 54.04% | 94.34% | 92.45% |
| `tactic_collapsed` | frequency | 53 | 9 | 33 | 16.98% | 62.26% | 17.12% | 65.06% | - | 92.45% |
| `tactic_collapsed` | markov_fallback | 53 | 13 | 30 | 24.53% | 56.60% | 22.44% | 57.37% | - | 92.45% |
| `tactic_raw` | markov | 95 | 35 | 62 | 36.84% | 65.26% | 36.19% | 66.58% | 90.53% | 87.37% |
| `tactic_raw` | frequency | 95 | 13 | 64 | 13.68% | 67.37% | 12.81% | 67.34% | - | 87.37% |
| `tactic_raw` | markov_fallback | 95 | 36 | 65 | 37.89% | 68.42% | 37.08% | 69.68% | - | 87.37% |

### Wilson 95% Score Intervals (Pooled)

| Slice | Method | N | Top-1 interval | Top-3 interval |
|---|---|---|---|---|
| `tactic_collapsed` | markov | 53 | [12.00%, 33.46%] | [39.66%, 65.62%] |
| `tactic_collapsed` | frequency | 53 | [9.20%, 29.23%] | [48.81%, 74.06%] |
| `tactic_collapsed` | markov_fallback | 53 | [14.93%, 37.57%] | [43.27%, 69.05%] |
| `tactic_raw` | markov | 95 | [27.83%, 46.88%] | [55.26%, 74.08%] |
| `tactic_raw` | frequency | 95 | [8.17%, 22.02%] | [57.43%, 75.96%] |
| `tactic_raw` | markov_fallback | 95 | [28.79%, 47.94%] | [58.51%, 76.90%] |

### Per-Fold Performance Breakdown (All Configurations)

| Configuration | Fold | Test Episode | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate |
|---|---|---|---|---|---|---|---|---|
| `tactic_collapsed` | fold_1 | E1 | markov | 13 | 3 | 6 | 23.08% | 46.15% |
| `tactic_collapsed` | fold_1 | E1 | frequency | 13 | 5 | 10 | 38.46% | 76.92% |
| `tactic_collapsed` | fold_1 | E1 | markov_fallback | 13 | 3 | 6 | 23.08% | 46.15% |
| `tactic_collapsed` | fold_2 | E2 | markov | 15 | 6 | 9 | 40.00% | 60.00% |
| `tactic_collapsed` | fold_2 | E2 | frequency | 15 | 1 | 8 | 6.67% | 53.33% |
| `tactic_collapsed` | fold_2 | E2 | markov_fallback | 15 | 7 | 10 | 46.67% | 66.67% |
| `tactic_collapsed` | fold_3 | E3 | markov | 15 | 2 | 6 | 13.33% | 40.00% |
| `tactic_collapsed` | fold_3 | E3 | frequency | 15 | 2 | 6 | 13.33% | 40.00% |
| `tactic_collapsed` | fold_3 | E3 | markov_fallback | 15 | 3 | 7 | 20.00% | 46.67% |
| `tactic_collapsed` | fold_4 | E4 | markov | 10 | 0 | 7 | 0.00% | 70.00% |
| `tactic_collapsed` | fold_4 | E4 | frequency | 10 | 1 | 9 | 10.00% | 90.00% |
| `tactic_collapsed` | fold_4 | E4 | markov_fallback | 10 | 0 | 7 | 0.00% | 70.00% |
| `tactic_raw` | fold_1 | E1 | markov | 26 | 13 | 16 | 50.00% | 61.54% |
| `tactic_raw` | fold_1 | E1 | frequency | 26 | 8 | 21 | 30.77% | 80.77% |
| `tactic_raw` | fold_1 | E1 | markov_fallback | 26 | 13 | 17 | 50.00% | 65.38% |
| `tactic_raw` | fold_2 | E2 | markov | 20 | 8 | 15 | 40.00% | 75.00% |
| `tactic_raw` | fold_2 | E2 | frequency | 20 | 1 | 12 | 5.00% | 60.00% |
| `tactic_raw` | fold_2 | E2 | markov_fallback | 20 | 8 | 16 | 40.00% | 80.00% |
| `tactic_raw` | fold_3 | E3 | markov | 28 | 10 | 15 | 35.71% | 53.57% |
| `tactic_raw` | fold_3 | E3 | frequency | 28 | 3 | 16 | 10.71% | 57.14% |
| `tactic_raw` | fold_3 | E3 | markov_fallback | 28 | 11 | 16 | 39.29% | 57.14% |
| `tactic_raw` | fold_4 | E4 | markov | 21 | 4 | 16 | 19.05% | 76.19% |
| `tactic_raw` | fold_4 | E4 | frequency | 21 | 1 | 15 | 4.76% | 71.43% |
| `tactic_raw` | fold_4 | E4 | markov_fallback | 21 | 4 | 16 | 19.05% | 76.19% |
| `tactic_collapsed_dataset_tactics` | fold_1 | E1 | markov | 13 | 2 | 5 | 15.38% | 38.46% |
| `tactic_collapsed_dataset_tactics` | fold_1 | E1 | frequency | 13 | 5 | 9 | 38.46% | 69.23% |
| `tactic_collapsed_dataset_tactics` | fold_1 | E1 | markov_fallback | 13 | 2 | 5 | 15.38% | 38.46% |
| `tactic_collapsed_dataset_tactics` | fold_2 | E2 | markov | 13 | 4 | 6 | 30.77% | 46.15% |
| `tactic_collapsed_dataset_tactics` | fold_2 | E2 | frequency | 13 | 4 | 6 | 30.77% | 46.15% |
| `tactic_collapsed_dataset_tactics` | fold_2 | E2 | markov_fallback | 13 | 4 | 7 | 30.77% | 53.85% |
| `tactic_collapsed_dataset_tactics` | fold_3 | E3 | markov | 15 | 1 | 3 | 6.67% | 20.00% |
| `tactic_collapsed_dataset_tactics` | fold_3 | E3 | frequency | 15 | 2 | 6 | 13.33% | 40.00% |
| `tactic_collapsed_dataset_tactics` | fold_3 | E3 | markov_fallback | 15 | 2 | 4 | 13.33% | 26.67% |
| `tactic_collapsed_dataset_tactics` | fold_4 | E4 | markov | 11 | 0 | 2 | 0.00% | 18.18% |
| `tactic_collapsed_dataset_tactics` | fold_4 | E4 | frequency | 11 | 1 | 5 | 9.09% | 45.45% |
| `tactic_collapsed_dataset_tactics` | fold_4 | E4 | markov_fallback | 11 | 0 | 2 | 0.00% | 18.18% |
| `tactic_raw_dataset_tactics` | fold_1 | E1 | markov | 26 | 12 | 17 | 46.15% | 65.38% |
| `tactic_raw_dataset_tactics` | fold_1 | E1 | frequency | 26 | 8 | 14 | 30.77% | 53.85% |
| `tactic_raw_dataset_tactics` | fold_1 | E1 | markov_fallback | 26 | 12 | 17 | 46.15% | 65.38% |
| `tactic_raw_dataset_tactics` | fold_2 | E2 | markov | 20 | 8 | 13 | 40.00% | 65.00% |
| `tactic_raw_dataset_tactics` | fold_2 | E2 | frequency | 20 | 1 | 12 | 5.00% | 60.00% |
| `tactic_raw_dataset_tactics` | fold_2 | E2 | markov_fallback | 20 | 8 | 14 | 40.00% | 70.00% |
| `tactic_raw_dataset_tactics` | fold_3 | E3 | markov | 28 | 12 | 15 | 42.86% | 53.57% |
| `tactic_raw_dataset_tactics` | fold_3 | E3 | frequency | 28 | 3 | 15 | 10.71% | 53.57% |
| `tactic_raw_dataset_tactics` | fold_3 | E3 | markov_fallback | 28 | 13 | 16 | 46.43% | 57.14% |
| `tactic_raw_dataset_tactics` | fold_4 | E4 | markov | 21 | 4 | 9 | 19.05% | 42.86% |
| `tactic_raw_dataset_tactics` | fold_4 | E4 | frequency | 21 | 1 | 7 | 4.76% | 33.33% |
| `tactic_raw_dataset_tactics` | fold_4 | E4 | markov_fallback | 21 | 4 | 9 | 19.05% | 42.86% |

## 3. Diagnostic Baselines and Self-Repeat Analysis

### Reference Baselines (Repeat-Current-Set and Random-Guess)

| Slice | Reference Baseline | Top-1 | Top-3 | Wilson 95% Top-1 | Wilson 95% Top-3 |
|---|---|---|---|---|---|
| `tactic_collapsed` | Repeat-current-set (10/53 t1, 20/53 t3) | 18.87% | 37.74% | [10.59%, 31.36%] | [25.94%, 51.19%] |
| `tactic_collapsed` | Random-guess (uniform from 14) | 12.26% | 32.99% | - | - |
| `tactic_raw` | Repeat-current-set (52/95 t1, 62/95 t3) | 54.74% | 65.26% | [44.74%, 64.37%] | [55.26%, 74.08%] |
| `tactic_raw` | Random-guess (uniform from 14) | 11.43% | 31.14% | - | - |

### Self-Repeat Rates Across Slices

| Slice | N | Target == Current Set (count) | Target == Current Set (rate) | Target Shares >=1 Tactic (count) | Target Shares >=1 Tactic (rate) |
|---|---|---|---|---|---|
| `tactic_collapsed` | 53 | 0 | 0.00% | 20 | 37.74% |
| `tactic_raw` | 95 | 42 | 44.21% | 62 | 65.26% |

### Strict Single-Tactic Target Subset

Evaluated exclusively on samples where the target consists of exactly one tactic:

| Slice | Single-Tactic N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 | Repeat Top-1 | Repeat Top-3 |
|---|---|---|---|---|---|---|---|---|---|
| `tactic_collapsed` | 33 | 7 | 15 | 8 | 19 | 9 | 17 | 1 | 7 |
| `tactic_raw` | 64 | 27 | 38 | 11 | 40 | 28 | 40 | 32 | 38 |

## 4. Paired Comparison and Frequency-Only Split

### 2x2 Paired Tables (Markov vs Frequency)

| Slice | k | Both hit | Markov-only | Frequency-only | Neither |
|---|---|---|---|---|---|
| `tactic_collapsed` | 1 | 2 | 9 | 7 | 35 |
| `tactic_collapsed` | 3 | 21 | 7 | 12 | 13 |
| `tactic_raw` | 1 | 7 | 28 | 6 | 54 |
| `tactic_raw` | 3 | 53 | 9 | 11 | 22 |

### Frequency-Only Hits Split by Markov Status

| Slice | k | Frequency-only hits | Markov returned a prediction and missed (status ok) | Markov abstained (insufficient_evidence) | Other status |
|---|---|---|---|---|---|
| `tactic_collapsed` | 1 | 7 | 5 | 2 | 0 |
| `tactic_collapsed` | 3 | 12 | 10 | 2 | 0 |
| `tactic_raw` | 1 | 6 | 5 | 1 | 0 |
| `tactic_raw` | 3 | 11 | 8 | 3 | 0 |

## 5. Covered-Only Comparison (Markov Status ok)

| Slice | Covered N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |
|---|---|---|---|---|---|---|---|
| `tactic_collapsed` | 50 | 11 | 28 | 7 | 31 | 11 | 28 |
| `tactic_raw` | 86 | 35 | 62 | 12 | 61 | 35 | 62 |

## 6. Tie Diagnostic (Markov predictions with status ok)

| Slice | Covered N | Top-1 tied | Top-3 boundary tied | n_equal_top >= 3 | Tied N | Tied Top-1 | Tied Top-3 | Not tied N | Not tied Top-1 | Not tied Top-3 |
|---|---|---|---|---|---|---|---|---|---|---|
| `tactic_collapsed` | 50 | 8 | 8 | 0 | 8 | 5 | 7 | 42 | 6 | 21 |
| `tactic_raw` | 86 | 7 | 10 | 0 | 7 | 2 | 5 | 79 | 33 | 57 |

- `tactic_collapsed`: 8 of 50 Markov predictions have their Top-1 choice decided by the tactic-name tie-break.
- `tactic_raw`: 7 of 86 Markov predictions have their Top-1 choice decided by the tactic-name tie-break.

## 7. Hit Concentration by Tactic (`tactic_collapsed`)

| Method | Tactic | Top-1 hit samples | Top-3 hit samples |
|---|---|---|---|
| markov | defense-evasion | 1 | 10 |
| markov | discovery | 3 | 8 |
| markov | credential-access | 5 | 5 |
| markov | collection | 1 | 2 |
| markov | command-and-control | 0 | 2 |
| markov | persistence | 0 | 2 |
| markov | execution | 1 | 1 |
| frequency | defense-evasion | 1 | 17 |
| frequency | discovery | 8 | 14 |
| frequency | credential-access | 0 | 4 |
| frequency | execution | 0 | 1 |
| markov_fallback | defense-evasion | 2 | 11 |
| markov_fallback | discovery | 4 | 9 |
| markov_fallback | credential-access | 5 | 5 |
| markov_fallback | collection | 1 | 2 |
| markov_fallback | command-and-control | 0 | 2 |
| markov_fallback | persistence | 0 | 2 |
| markov_fallback | execution | 1 | 1 |

Most frequent target tactics pooled over all four episodes (descriptive only; computed on all episodes, not a leakage-free baseline):

| Rank | Target Tactic | Test samples containing target (pooled) |
|---|---|---|
| 1 | defense-evasion | 17 |
| 2 | discovery | 14 |
| 3 | persistence | 12 |
| 4 | privilege-escalation | 10 |
| 5 | command-and-control | 9 |

## 8. Sensitivity: Ground-Truth Dataset Tactics (Attackmate)

Total events differing between official tactics and ground-truth dataset tactics: **25**.
- **Type (a)** (dataset contains a tactic NOT in official MITRE set): **8 events** (E2-S016, E2-S017, E2-S024, E4-S003, E4-S007, E4-S009, E4-S041, E4-S043).
- **Type (b)** (dataset tactic set is a strict subset of official MITRE set): **17 events** (E1-S008, E1-S024, E2-S006, E2-S026, E3-S043, E3-S046, E3-S048, E4-S005, E4-S010, E4-S012, E4-S013, E4-S023, E4-S025, E4-S027, E4-S029, E4-S031, E4-S040).

### Discrepant Events Breakdown

| Event ID | Episode | Class | Techniques | Dataset tactics | Official MITRE tactics |
|---|---|---|---|---|---|
| E1-S008 | E1 | Type (b) | T1059.006, T1190 | initial-access | execution, initial-access |
| E1-S024 | E1 | Type (b) | T1105, T1556.003 | command-and-control, credential-access, persistence | command-and-control, credential-access, defense-evasion, persistence |
| E2-S006 | E2 | Type (b) | T1547, T1569 | execution, persistence | execution, persistence, privilege-escalation |
| E2-S016 | E2 | Type (a) | T1003.008, T1041 | collection, credential-access, exfiltration | credential-access, exfiltration |
| E2-S017 | E2 | Type (a) | T1074.001, T1560.001 | collection, exfiltration | collection |
| E2-S024 | E2 | Type (a) | T1003.008 | discovery | credential-access |
| E2-S026 | E2 | Type (b) | T1018, T1046, T1105 | command-and-control | command-and-control, discovery |
| E3-S043 | E3 | Type (b) | T1574 | defense-evasion, persistence | defense-evasion, persistence, privilege-escalation |
| E3-S046 | E3 | Type (b) | T1059, T1574 | execution | defense-evasion, execution, persistence, privilege-escalation |
| E3-S048 | E3 | Type (b) | T1053.003, T1071.001, T1105 | command-and-control, persistence | command-and-control, execution, persistence, privilege-escalation |
| E4-S003 | E4 | Type (a) | T1078.003, T1105, T1205.001 | defense-evasion, initial-access, lateral-movement | command-and-control, defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S005 | E4 | Type (b) | T1078.003 | initial-access | defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S007 | E4 | Type (a) | T1078.003 | lateral-movement | defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S009 | E4 | Type (a) | T1078.003 | lateral-movement | defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S010 | E4 | Type (b) | T1548.003 | privilege-escalation | defense-evasion, privilege-escalation |
| E4-S012 | E4 | Type (b) | T1548.003 | privilege-escalation | defense-evasion, privilege-escalation |
| E4-S013 | E4 | Type (b) | T1036.005, T1205.001 | defense-evasion | command-and-control, defense-evasion, persistence |
| E4-S023 | E4 | Type (b) | T1543.002 | persistence | persistence, privilege-escalation |
| E4-S025 | E4 | Type (b) | T1543.002 | persistence | persistence, privilege-escalation |
| E4-S027 | E4 | Type (b) | T1543.002 | persistence | persistence, privilege-escalation |
| E4-S029 | E4 | Type (b) | T1543.002 | persistence | persistence, privilege-escalation |
| E4-S031 | E4 | Type (b) | T1543.002 | persistence | persistence, privilege-escalation |
| E4-S040 | E4 | Type (b) | T1078.003 | initial-access | defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S041 | E4 | Type (a) | T1078.003 | lateral-movement | defense-evasion, initial-access, persistence, privilege-escalation |
| E4-S043 | E4 | Type (a) | T1078.003 | lateral-movement | defense-evasion, initial-access, persistence, privilege-escalation |

### Sensitivity Results (Dataset Tactics)

| Slice | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 |
|---|---|---|---|---|---|---|---|---|
| `tactic_collapsed_dataset_tactics` | markov | 52 | 7 | 16 | 13.46% | 30.77% | 13.21% | 30.70% |
| `tactic_collapsed_dataset_tactics` | frequency | 52 | 12 | 26 | 23.08% | 50.00% | 22.91% | 50.21% |
| `tactic_collapsed_dataset_tactics` | markov_fallback | 52 | 8 | 18 | 15.38% | 34.62% | 14.87% | 34.29% |
| `tactic_raw_dataset_tactics` | markov | 95 | 36 | 54 | 37.89% | 56.84% | 37.01% | 56.70% |
| `tactic_raw_dataset_tactics` | frequency | 95 | 13 | 48 | 13.68% | 50.53% | 12.81% | 50.19% |
| `tactic_raw_dataset_tactics` | markov_fallback | 95 | 37 | 56 | 38.95% | 58.95% | 37.91% | 58.85% |

### Markov vs Frequency Ordering Comparison

- For `tactic_collapsed` at k=1: under official tactics Markov (11) is above Frequency (9), and under dataset tactics Markov (7) is below Frequency (12); the Markov-vs-Frequency ordering is **different**.
- For `tactic_collapsed` at k=3: under official tactics Markov (28) is below Frequency (33), and under dataset tactics Markov (16) is below Frequency (26); the Markov-vs-Frequency ordering is **the same**.
- For `tactic_raw` at k=1: under official tactics Markov (35) is above Frequency (13), and under dataset tactics Markov (36) is above Frequency (13); the Markov-vs-Frequency ordering is **the same**.
- For `tactic_raw` at k=3: under official tactics Markov (62) is below Frequency (64), and under dataset tactics Markov (54) is above Frequency (48); the Markov-vs-Frequency ordering is **different**.

## 9. Derived-Tactic Evaluation from Technique-Level Predictions

Scored by mapping each of the top-k predicted techniques from `evaluation_predictions.csv` to its official ATT&CK tactics, and testing for intersection with the target's official tactic set.

| Technique Configuration | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Wilson 95% Top-1 | Wilson 95% Top-3 | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| `collapsed_full` | markov | 67 | 13 | 21 | 19.40% | 31.34% | [11.71%, 30.42%] | [21.51%, 43.20%] | 50.75% |
| `collapsed_full` | frequency | 67 | 17 | 32 | 25.37% | 47.76% | [16.49%, 36.93%] | [36.25%, 59.51%] | 100.00% |
| `collapsed_full` | markov_fallback | 67 | 19 | 38 | 28.36% | 56.72% | [18.97%, 40.09%] | [44.81%, 67.90%] | 100.00% |
| `raw_full` | markov | 95 | 28 | 37 | 29.47% | 38.95% | [21.25%, 39.29%] | [29.75%, 49.00%] | 51.58% |
| `raw_full` | frequency | 95 | 12 | 33 | 12.63% | 34.74% | [7.38%, 20.79%] | [25.92%, 44.74%] | 100.00% |
| `raw_full` | markov_fallback | 95 | 31 | 48 | 32.63% | 50.53% | [24.04%, 42.57%] | [40.65%, 60.36%] | 100.00% |

> [!NOTE]
> Derived scoring uses any-overlap between the tactic set of the predicted technique(s) and the target tactic set; one technique can map to several tactics so derived Top-1 covers a tactic set, not a single tactic; the derived table uses technique slices (N=67 and N=95) while the direct table uses tactic slices (N=53 and N=95); therefore the two tables are not directly comparable.

### Mean Official Tactics per Top-1 Predicted Technique

| Technique Configuration | Method | Evaluated Predictions N | Mean Official Tactics per Top-1 Prediction |
|---|---|---|---|
| `collapsed_full` | markov | 34 | 1.21 |
| `collapsed_full` | frequency | 67 | 1.00 |
| `collapsed_full` | markov_fallback | 67 | 1.10 |
| `raw_full` | markov | 49 | 1.16 |
| `raw_full` | frequency | 95 | 1.88 |
| `raw_full` | markov_fallback | 95 | 1.56 |

