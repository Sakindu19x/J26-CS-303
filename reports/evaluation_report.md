# C4 Next-Technique Prediction: LOEO Evaluation Report

All numbers and explanatory sentences below are generated from this run's prediction rows. Sentences labelled *Hypothesis (not tested)* are not backed by a computation in this report. Probabilities are estimates from observed training sequences, not guarantees. No significance test is performed and nothing here supports a generalization claim.

## 1. Setup

- Evaluation unit: samples in `data/processed/next_technique_samples.json`; primary configuration `collapsed_full` (N=67).
- Folds: 4 leave-one-episode-out folds (test = one complete episode, training = the others). A fresh `MarkovModel` and `FrequencyBaseline` is fitted per fold on training episodes only; runtime assertions check that no fold model lists the test episode as training and no evidence entry references it.
- Prediction: from `current_technique_set` only, k=3, no smoothing, no tuning, no randomness. Markov abstains when status is `insufficient_evidence` (counted as a miss). Frequency never abstains.
- `markov_fallback` is an **extension, NOT part of the proposal**, implemented in the evaluation module only: Markov when status is ok, else the frequency prediction.
- Configurations run: `collapsed_full`, `collapsed_parent`, `raw_full`, `raw_parent`, `collapsed_full_no_s006`.

## 2. Definitions

- **Hit@k**: 1 if at least one of the top-k returned candidates is in the target set, else 0. Abstention is a miss. No padding of Top-3.
- **Pooled rate**: hits / N over all test samples of the configuration. **Fold mean**: unweighted mean of the per-fold rates.
- **Coverage**: fraction of samples with Markov status ok.
- **Ceiling**: fraction of test samples whose target set contains at least one technique that appears as a target in that fold's training episodes.
- **Micro P/R/F1**: TP = sum |pred ∩ target|, FP = sum |pred − target|, FN = sum |target − pred| (abstention = empty pred set, so only FN).
- **Macro P/R/F1**: per-technique TP/FP/FN over every technique appearing in any target or prediction, averaged over those techniques, zero_division = 0.
- **Wilson 95% interval**: score interval for a pooled hit rate. Samples within an episode are not independent, so the intervals understate uncertainty.

## 3. Results by configuration and method

| Configuration | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 | Markov coverage |
|---|---|---|---|---|---|---|---|---|---|
| collapsed_full | markov | 67 | 1 | 2 | 1.49% | 2.99% | 2.50% | 3.82% | 50.75% |
| collapsed_full | frequency | 67 | 4 | 8 | 5.97% | 11.94% | 6.39% | 11.80% | - |
| collapsed_full | markov_fallback | 67 | 2 | 5 | 2.99% | 7.46% | 3.89% | 7.98% | - |
| collapsed_parent | markov | 67 | 4 | 5 | 5.97% | 7.46% | 6.39% | 7.70% | 61.19% |
| collapsed_parent | frequency | 67 | 2 | 11 | 2.99% | 16.42% | 2.64% | 15.83% | - |
| collapsed_parent | markov_fallback | 67 | 5 | 8 | 7.46% | 11.94% | 7.78% | 11.87% | - |
| raw_full | markov | 95 | 12 | 13 | 12.63% | 13.68% | 11.42% | 12.61% | 51.58% |
| raw_full | frequency | 95 | 6 | 14 | 6.32% | 14.74% | 5.77% | 13.21% | - |
| raw_full | markov_fallback | 95 | 12 | 15 | 12.63% | 15.79% | 11.42% | 14.40% | - |
| raw_parent | markov | 95 | 12 | 16 | 12.63% | 16.84% | 11.42% | 15.36% | 61.05% |
| raw_parent | frequency | 95 | 15 | 16 | 15.79% | 16.84% | 13.87% | 15.06% | - |
| raw_parent | markov_fallback | 95 | 15 | 19 | 15.79% | 20.00% | 14.17% | 18.11% | - |
| collapsed_full_no_s006 | markov | 66 | 1 | 2 | 1.52% | 3.03% | 2.50% | 3.82% | 51.52% |
| collapsed_full_no_s006 | frequency | 66 | 4 | 8 | 6.06% | 12.12% | 6.52% | 11.93% | - |
| collapsed_full_no_s006 | markov_fallback | 66 | 2 | 5 | 3.03% | 7.58% | 3.89% | 7.98% | - |

### Wilson 95% intervals (pooled)

| Configuration | Method | N | Top-1 interval | Top-3 interval |
|---|---|---|---|---|
| collapsed_full | markov | 67 | [0.26%, 7.98%] | [0.82%, 10.25%] |
| collapsed_full | frequency | 67 | [2.35%, 14.37%] | [6.18%, 21.83%] |
| collapsed_full | markov_fallback | 67 | [0.82%, 10.25%] | [3.23%, 16.31%] |
| collapsed_parent | markov | 67 | [2.35%, 14.37%] | [3.23%, 16.31%] |
| collapsed_parent | frequency | 67 | [0.82%, 10.25%] | [9.42%, 27.06%] |
| collapsed_parent | markov_fallback | 67 | [3.23%, 16.31%] | [6.18%, 21.83%] |
| raw_full | markov | 95 | [7.38%, 20.79%] | [8.17%, 22.02%] |
| raw_full | frequency | 95 | [2.93%, 13.10%] | [8.99%, 23.23%] |
| raw_full | markov_fallback | 95 | [7.38%, 20.79%] | [9.81%, 24.43%] |
| raw_parent | markov | 95 | [7.38%, 20.79%] | [10.64%, 25.62%] |
| raw_parent | frequency | 95 | [9.81%, 24.43%] | [10.64%, 25.62%] |
| raw_parent | markov_fallback | 95 | [9.81%, 24.43%] | [13.19%, 29.14%] |
| collapsed_full_no_s006 | markov | 66 | [0.27%, 8.10%] | [0.83%, 10.39%] |
| collapsed_full_no_s006 | frequency | 66 | [2.38%, 14.57%] | [6.27%, 22.14%] |
| collapsed_full_no_s006 | markov_fallback | 66 | [0.83%, 10.39%] | [3.28%, 16.54%] |

### Markov versus frequency baseline (computed comparison of hit counts)

- `collapsed_full`: Top-1 Markov 1/67 is **below** Frequency 4/67; Top-3 Markov 2/67 is **below** Frequency 8/67.
- `collapsed_parent`: Top-1 Markov 4/67 is **above** Frequency 2/67; Top-3 Markov 5/67 is **below** Frequency 11/67.
- `raw_full`: Top-1 Markov 12/95 is **above** Frequency 6/95; Top-3 Markov 13/95 is **below** Frequency 14/95.
- `raw_parent`: Top-1 Markov 12/95 is **below** Frequency 15/95; Top-3 Markov 16/95 is **equal to** Frequency 16/95.
- `collapsed_full_no_s006`: Top-1 Markov 1/66 is **below** Frequency 4/66; Top-3 Markov 2/66 is **below** Frequency 8/66.

## 4. Per-fold results

| Configuration | Fold | Test episode | Method | N | Top-1 hits | Top-3 hits |
|---|---|---|---|---|---|---|
| collapsed_full | fold_1 | E1 | markov | 18 | 0 | 0 |
| collapsed_full | fold_2 | E2 | markov | 19 | 0 | 1 |
| collapsed_full | fold_3 | E3 | markov | 20 | 0 | 0 |
| collapsed_full | fold_4 | E4 | markov | 10 | 1 | 1 |
| collapsed_full | fold_1 | E1 | frequency | 18 | 1 | 3 |
| collapsed_full | fold_2 | E2 | frequency | 19 | 0 | 2 |
| collapsed_full | fold_3 | E3 | frequency | 20 | 2 | 2 |
| collapsed_full | fold_4 | E4 | frequency | 10 | 1 | 1 |
| collapsed_full | fold_1 | E1 | markov_fallback | 18 | 1 | 3 |
| collapsed_full | fold_2 | E2 | markov_fallback | 19 | 0 | 1 |
| collapsed_full | fold_3 | E3 | markov_fallback | 20 | 0 | 0 |
| collapsed_full | fold_4 | E4 | markov_fallback | 10 | 1 | 1 |
| collapsed_parent | fold_1 | E1 | markov | 18 | 1 | 1 |
| collapsed_parent | fold_2 | E2 | markov | 19 | 0 | 1 |
| collapsed_parent | fold_3 | E3 | markov | 20 | 2 | 2 |
| collapsed_parent | fold_4 | E4 | markov | 10 | 1 | 1 |
| collapsed_parent | fold_1 | E1 | frequency | 18 | 1 | 5 |
| collapsed_parent | fold_2 | E2 | frequency | 19 | 0 | 2 |
| collapsed_parent | fold_3 | E3 | frequency | 20 | 1 | 3 |
| collapsed_parent | fold_4 | E4 | frequency | 10 | 0 | 1 |
| collapsed_parent | fold_1 | E1 | markov_fallback | 18 | 2 | 4 |
| collapsed_parent | fold_2 | E2 | markov_fallback | 19 | 0 | 1 |
| collapsed_parent | fold_3 | E3 | markov_fallback | 20 | 2 | 2 |
| collapsed_parent | fold_4 | E4 | markov_fallback | 10 | 1 | 1 |
| raw_full | fold_1 | E1 | markov | 26 | 6 | 6 |
| raw_full | fold_2 | E2 | markov | 20 | 0 | 0 |
| raw_full | fold_3 | E3 | markov | 28 | 5 | 5 |
| raw_full | fold_4 | E4 | markov | 21 | 1 | 2 |
| raw_full | fold_1 | E1 | frequency | 26 | 6 | 6 |
| raw_full | fold_2 | E2 | frequency | 20 | 0 | 0 |
| raw_full | fold_3 | E3 | frequency | 28 | 0 | 7 |
| raw_full | fold_4 | E4 | frequency | 21 | 0 | 1 |
| raw_full | fold_1 | E1 | markov_fallback | 26 | 6 | 6 |
| raw_full | fold_2 | E2 | markov_fallback | 20 | 0 | 0 |
| raw_full | fold_3 | E3 | markov_fallback | 28 | 5 | 7 |
| raw_full | fold_4 | E4 | markov_fallback | 21 | 1 | 2 |
| raw_parent | fold_1 | E1 | markov | 26 | 6 | 7 |
| raw_parent | fold_2 | E2 | markov | 20 | 0 | 0 |
| raw_parent | fold_3 | E3 | markov | 28 | 5 | 7 |
| raw_parent | fold_4 | E4 | markov | 21 | 1 | 2 |
| raw_parent | fold_1 | E1 | frequency | 26 | 7 | 7 |
| raw_parent | fold_2 | E2 | frequency | 20 | 0 | 0 |
| raw_parent | fold_3 | E3 | frequency | 28 | 8 | 8 |
| raw_parent | fold_4 | E4 | frequency | 21 | 0 | 1 |
| raw_parent | fold_1 | E1 | markov_fallback | 26 | 7 | 8 |
| raw_parent | fold_2 | E2 | markov_fallback | 20 | 0 | 0 |
| raw_parent | fold_3 | E3 | markov_fallback | 28 | 7 | 9 |
| raw_parent | fold_4 | E4 | markov_fallback | 21 | 1 | 2 |
| collapsed_full_no_s006 | fold_1 | E1 | markov | 18 | 0 | 0 |
| collapsed_full_no_s006 | fold_2 | E2 | markov | 19 | 0 | 1 |
| collapsed_full_no_s006 | fold_3 | E3 | markov | 19 | 0 | 0 |
| collapsed_full_no_s006 | fold_4 | E4 | markov | 10 | 1 | 1 |
| collapsed_full_no_s006 | fold_1 | E1 | frequency | 18 | 1 | 3 |
| collapsed_full_no_s006 | fold_2 | E2 | frequency | 19 | 0 | 2 |
| collapsed_full_no_s006 | fold_3 | E3 | frequency | 19 | 2 | 2 |
| collapsed_full_no_s006 | fold_4 | E4 | frequency | 10 | 1 | 1 |
| collapsed_full_no_s006 | fold_1 | E1 | markov_fallback | 18 | 1 | 3 |
| collapsed_full_no_s006 | fold_2 | E2 | markov_fallback | 19 | 0 | 1 |
| collapsed_full_no_s006 | fold_3 | E3 | markov_fallback | 19 | 0 | 0 |
| collapsed_full_no_s006 | fold_4 | E4 | markov_fallback | 10 | 1 | 1 |

## 5. Coverage and ceiling

| Configuration | N | Markov covered | Coverage | Samples with target seen in training (ceiling) | Ceiling rate |
|---|---|---|---|---|---|
| collapsed_full | 67 | 34 | 50.75% | 35 | 52.24% |
| collapsed_parent | 67 | 41 | 61.19% | 39 | 58.21% |
| raw_full | 95 | 49 | 51.58% | 50 | 52.63% |
| raw_parent | 95 | 58 | 61.05% | 54 | 56.84% |
| collapsed_full_no_s006 | 66 | 34 | 51.52% | 35 | 53.03% |

Per-fold ceiling and coverage for `collapsed_full`:

| Fold | Test episode | N | Covered | Ceiling hits |
|---|---|---|---|---|
| fold_1 | E1 | 18 | 7 | 7 |
| fold_2 | E2 | 19 | 13 | 14 |
| fold_3 | E3 | 20 | 8 | 8 |
| fold_4 | E4 | 10 | 6 | 6 |

## 6. Covered-only comparison (samples where Markov status is ok)

| Configuration | Covered N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |
|---|---|---|---|---|---|---|---|
| collapsed_full | 34 | 1 | 2 | 3 | 5 | 1 | 2 |
| collapsed_parent | 41 | 4 | 5 | 1 | 8 | 4 | 5 |
| raw_full | 49 | 12 | 13 | 6 | 12 | 12 | 13 |
| raw_parent | 58 | 12 | 16 | 12 | 13 | 12 | 16 |
| collapsed_full_no_s006 | 34 | 1 | 2 | 3 | 5 | 1 | 2 |

Values are hit counts on that subset.

## 7. Strict subset (target set has exactly one technique)

| Configuration | N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |
|---|---|---|---|---|---|---|---|
| collapsed_full | 48 | 0 | 1 | 1 | 3 | 1 | 3 |
| collapsed_parent | 48 | 1 | 2 | 2 | 5 | 2 | 3 |
| raw_full | 75 | 11 | 12 | 6 | 12 | 11 | 13 |
| raw_parent | 75 | 11 | 13 | 13 | 13 | 12 | 14 |
| collapsed_full_no_s006 | 47 | 0 | 1 | 1 | 3 | 1 | 3 |

Values are hit counts.

## 8. Precision / recall / F1 (`collapsed_full`)

| Method | Cutoff | TP | FP | FN | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 | Classes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| markov | Top-1 | 1 | 33 | 100 | 0.0294 | 0.0099 | 0.0148 | 0.0056 | 0.0024 | 0.0033 | 60 |
| markov | Top-3 | 2 | 73 | 99 | 0.0267 | 0.0198 | 0.0227 | 0.0067 | 0.0048 | 0.0056 | 60 |
| frequency | Top-1 | 4 | 63 | 97 | 0.0597 | 0.0396 | 0.0476 | 0.0026 | 0.0113 | 0.0042 | 60 |
| frequency | Top-3 | 8 | 193 | 93 | 0.0398 | 0.0792 | 0.0530 | 0.0023 | 0.0208 | 0.0042 | 60 |
| fallback | Top-1 | 2 | 65 | 99 | 0.0299 | 0.0198 | 0.0238 | 0.0024 | 0.0065 | 0.0035 | 60 |
| fallback | Top-3 | 5 | 169 | 96 | 0.0287 | 0.0495 | 0.0364 | 0.0028 | 0.0137 | 0.0046 | 60 |

## 9. Paired comparison (Markov vs Frequency, counts only)

| Configuration | k | Both hit | Markov-only | Frequency-only | Neither |
|---|---|---|---|---|---|
| collapsed_full | 1 | 1 | 0 | 3 | 63 |
| collapsed_full | 3 | 2 | 0 | 6 | 59 |
| collapsed_parent | 1 | 0 | 4 | 2 | 61 |
| collapsed_parent | 3 | 5 | 0 | 6 | 56 |
| raw_full | 1 | 5 | 7 | 1 | 82 |
| raw_full | 3 | 11 | 2 | 3 | 79 |
| raw_parent | 1 | 10 | 2 | 5 | 78 |
| raw_parent | 3 | 11 | 5 | 5 | 74 |
| collapsed_full_no_s006 | 1 | 1 | 0 | 3 | 62 |
| collapsed_full_no_s006 | 3 | 2 | 0 | 6 | 58 |

### Frequency-only hits split by Markov status

| Configuration | k | Frequency-only hits | Markov returned a prediction and missed (status ok) | Markov abstained (insufficient_evidence) | Other status |
|---|---|---|---|---|---|
| collapsed_full | 1 | 3 | 2 | 1 | 0 |
| collapsed_full | 3 | 6 | 3 | 3 | 0 |
| collapsed_parent | 1 | 2 | 1 | 1 | 0 |
| collapsed_parent | 3 | 6 | 3 | 3 | 0 |
| raw_full | 1 | 1 | 1 | 0 | 0 |
| raw_full | 3 | 3 | 1 | 2 | 0 |
| raw_parent | 1 | 5 | 2 | 3 | 0 |
| raw_parent | 3 | 5 | 2 | 3 | 0 |
| collapsed_full_no_s006 | 1 | 3 | 2 | 1 | 0 |
| collapsed_full_no_s006 | 3 | 6 | 3 | 3 | 0 |

- `collapsed_full`: Of 3 frequency-only Top-1 hits, 2 occurred where Markov returned a prediction and missed, and 1 where Markov abstained.
- `collapsed_full`: Of 6 frequency-only Top-3 hits, 3 occurred where Markov returned a prediction and missed, and 3 where Markov abstained.
- `collapsed_parent`: Of 2 frequency-only Top-1 hits, 1 occurred where Markov returned a prediction and missed, and 1 where Markov abstained.
- `collapsed_parent`: Of 6 frequency-only Top-3 hits, 3 occurred where Markov returned a prediction and missed, and 3 where Markov abstained.
- `raw_full`: Of 1 frequency-only Top-1 hits, 1 occurred where Markov returned a prediction and missed, and 0 where Markov abstained.
- `raw_full`: Of 3 frequency-only Top-3 hits, 1 occurred where Markov returned a prediction and missed, and 2 where Markov abstained.
- `raw_parent`: Of 5 frequency-only Top-1 hits, 2 occurred where Markov returned a prediction and missed, and 3 where Markov abstained.
- `raw_parent`: Of 5 frequency-only Top-3 hits, 2 occurred where Markov returned a prediction and missed, and 3 where Markov abstained.
- `collapsed_full_no_s006`: Of 3 frequency-only Top-1 hits, 2 occurred where Markov returned a prediction and missed, and 1 where Markov abstained.
- `collapsed_full_no_s006`: Of 6 frequency-only Top-3 hits, 3 occurred where Markov returned a prediction and missed, and 3 where Markov abstained.

## 10. Sensitivity configurations

Sensitivity runs use the same code path. Their hit counts appear in sections 3-9 (one row per configuration); the comparison sentences in section 3 are computed. The `collapsed_full_no_s006` configuration has N=66 versus N=67 for `collapsed_full`.

Hypothesis (not tested): differences between raw/collapsed or full/parent configurations may reflect changes in vocabulary size or in the number of repeated consecutive techniques; this report does not test either explanation (see Diagnostics for repeat rates).

## 11. Confusion analysis

### Most frequent Top-1 errors at full ID (`collapsed_full`; Markov status ok and Top-1 not in target)

| Target technique | Predicted Top-1 | Count |
|---|---|---|
| T1003.008 | T1033 | 2 |
| T1105 | T1007 | 2 |
| T1003 | T1033 | 1 |
| T1005 | T1033 | 1 |
| T1007 | T1033 | 1 |
| T1007 | T1105 | 1 |
| T1016 | T1033 | 1 |
| T1016 | T1105 | 1 |
| T1018 | T1033 | 1 |
| T1018 | T1087.001 | 1 |

### Abstentions by target technique (a sample with several targets counts once per target)

| Target technique | Abstentions |
|---|---|
| T1003.008 | 2 |
| T1036.005 | 2 |
| T1059 | 2 |
| T1070.004 | 2 |
| T1071.001 | 2 |
| T1083 | 2 |
| T1105 | 2 |
| T1548.003 | 2 |
| T1018 | 1 |
| T1021.005 | 1 |
| T1039 | 1 |
| T1041 | 1 |
| T1049 | 1 |
| T1059.006 | 1 |
| T1078.003 | 1 |

Parent-level confusion matrix (single-target samples only, N=48): 33 target rows x 15 prediction columns (including ABSTAIN), 42 of 495 cells non-zero (8.48%); the matrix is sparse. Saved as `reports/confusion_matrix_parent.csv` and `reports/figures/confusion_matrix_parent.png`.

## 12. Examples chosen by rule (`collapsed_full`)

Rules: (i) every sample where Markov hit at Top-1; (ii) up to 3 samples where Frequency hit at Top-1, Markov status ok and Markov missed at Top-1, ordered by sample_id; (iii) up to 3 samples where Markov abstained (insufficient_evidence), ordered by sample_id.

### (i) Markov Top-1 hits (1 shown)

| Sample | Fold | Current set | Target set | Markov status | Markov candidates | Frequency candidates |
|---|---|---|---|---|---|---|
| E4-col-ful-K01 | fold_4 | T1071.001 | T1078.003, T1105, T1205.001 | ok | T1105 (0.600), T1072 (0.400) | T1105 (0.064), T1003.008 (0.061), T1033 (0.054) |

### (ii) Frequency-only Top-1 hits with Markov status ok (2 shown)

| Sample | Fold | Current set | Target set | Markov status | Markov candidates | Frequency candidates |
|---|---|---|---|---|---|---|
| E3-col-ful-K10 | fold_3 | T1059, T1574 | T1053.003, T1071.001, T1105 | ok | T1007 (0.077), T1016 (0.077), T1033 (0.077) | T1105 (0.067), T1033 (0.065), T1070.004 (0.064) |
| E3-col-ful-K13 | fold_3 | T1059 | T1105, T1486 | ok | T1007 (0.077), T1016 (0.077), T1033 (0.077) | T1105 (0.067), T1033 (0.065), T1070.004 (0.064) |

### (iii) Abstention cases (3 shown)

| Sample | Fold | Current set | Target set | Markov status | Markov candidates | Frequency candidates |
|---|---|---|---|---|---|---|
| E1-col-ful-K01 | fold_1 | T1590.002, T1591 | T1592.002, T1595 | insufficient_evidence | (none) | T1003.008 (0.051), T1105 (0.051), T1078.003 (0.048) |
| E1-col-ful-K02 | fold_1 | T1592.002, T1595 | T1595.002 | insufficient_evidence | (none) | T1003.008 (0.051), T1105 (0.051), T1078.003 (0.048) |
| E1-col-ful-K03 | fold_1 | T1595.002 | T1595.003 | insufficient_evidence | (none) | T1003.008 (0.051), T1105 (0.051), T1078.003 (0.048) |

## 13. Diagnostics

### 13.1 Self-repeat rate per slice (all samples of the slice)

| Slice | N | Target shares >=1 technique with current set | Rate | Target == current set | Rate |
|---|---|---|---|---|---|
| raw_full | 95 | 35 | 36.84% | 28 | 29.47% |
| raw_parent | 95 | 37 | 38.95% | 29 | 30.53% |
| collapsed_full | 67 | 7 | 10.45% | 0 | 0.00% |
| collapsed_parent | 67 | 9 | 13.43% | 1 | 1.49% |

### 13.2 Repeat-current-set reference (DIAGNOSTIC REFERENCE, not a proposed model)

Top-k candidates are the members of the current set (ties by technique ID ascending, truncated to k). It uses no training data, so it is evaluated on every sample of each slice.

| Slice | N | Top-1 hits | Top-1 | Top-1 Wilson 95% | Top-3 hits | Top-3 | Top-3 Wilson 95% |
|---|---|---|---|---|---|---|---|
| raw_full | 95 | 32 | 33.68% | [24.98%, 43.66%] | 35 | 36.84% | [27.83%, 46.88%] |
| raw_parent | 95 | 33 | 34.74% | [25.92%, 44.74%] | 37 | 38.95% | [29.75%, 49.00%] |
| collapsed_full | 67 | 4 | 5.97% | [2.35%, 14.37%] | 7 | 10.45% | [5.15%, 20.03%] |
| collapsed_parent | 67 | 5 | 7.46% | [3.23%, 16.31%] | 9 | 13.43% | [7.23%, 23.60%] |

Comparison with the proposal methods on the same slice (hit counts, computed):

- `raw_full`: repeat-current-set Top-1 32/95 is above Markov (12) and above Frequency (6); Top-3 35/95 is above Markov (13) and above Frequency (14).
- `raw_parent`: repeat-current-set Top-1 33/95 is above Markov (12) and above Frequency (15); Top-3 37/95 is above Markov (16) and above Frequency (16).
- `collapsed_full`: repeat-current-set Top-1 4/67 is above Markov (1) and equal to Frequency (4); Top-3 7/67 is above Markov (2) and below Frequency (8).
- `collapsed_parent`: repeat-current-set Top-1 5/67 is above Markov (4) and above Frequency (2); Top-3 9/67 is above Markov (5) and below Frequency (11).

### 13.3 Markov hit rate by support strength (status ok only)

`support_episodes` is the number of distinct training episodes contributing evidence for the source technique(s); `support_mass` (per row in `evaluation_predictions.csv`) is their total outgoing transition mass.

| Configuration | support_episodes | N | Top-1 hits | Top-3 hits |
|---|---|---|---|---|
| collapsed_full | 1 | 14 | 0 | 0 |
| collapsed_full | 2 | 13 | 1 | 2 |
| collapsed_full | 3 | 7 | 0 | 0 |
| collapsed_parent | 1 | 20 | 3 | 3 |
| collapsed_parent | 2 | 14 | 1 | 2 |
| collapsed_parent | 3 | 7 | 0 | 0 |
| raw_full | 1 | 27 | 11 | 12 |
| raw_full | 2 | 15 | 1 | 1 |
| raw_full | 3 | 7 | 0 | 0 |
| raw_parent | 1 | 35 | 11 | 15 |
| raw_parent | 2 | 16 | 1 | 1 |
| raw_parent | 3 | 7 | 0 | 0 |
| collapsed_full_no_s006 | 1 | 14 | 0 | 0 |
| collapsed_full_no_s006 | 2 | 13 | 1 | 2 |
| collapsed_full_no_s006 | 3 | 7 | 0 | 0 |

Some buckets have fewer than 30 samples, so these buckets are too small for inference.

### 13.4 What the frequency baseline predicts per fold (`collapsed_full`)

| Fold | Test episode | Test N | Rank | Technique | Probability | Training transitions with this target | Test samples containing it as target |
|---|---|---|---|---|---|---|---|
| fold_1 | E1 | 18 | 1 | T1003.008 | 0.0510 | 3 | 1 |
| fold_1 | E1 | 18 | 2 | T1105 | 0.0510 | 5 | 2 |
| fold_1 | E1 | 18 | 3 | T1078.003 | 0.0476 | 3 | 0 |
| fold_2 | E2 | 19 | 1 | T1033 | 0.0641 | 4 | 0 |
| fold_2 | E2 | 19 | 2 | T1105 | 0.0556 | 5 | 2 |
| fold_2 | E2 | 19 | 3 | T1059 | 0.0521 | 3 | 0 |
| fold_3 | E3 | 20 | 1 | T1105 | 0.0674 | 5 | 2 |
| fold_3 | E3 | 20 | 2 | T1033 | 0.0655 | 4 | 0 |
| fold_3 | E3 | 20 | 3 | T1070.004 | 0.0638 | 3 | 0 |
| fold_4 | E4 | 10 | 1 | T1105 | 0.0643 | 6 | 1 |
| fold_4 | E4 | 10 | 2 | T1003.008 | 0.0614 | 4 | 0 |
| fold_4 | E4 | 10 | 3 | T1033 | 0.0540 | 4 | 0 |

- fold_1: 3 of 18 test samples have at least one of the three top targets in their target set.
- fold_2: 2 of 19 test samples have at least one of the three top targets in their target set.
- fold_3: 2 of 20 test samples have at least one of the three top targets in their target set.
- fold_4: 1 of 10 test samples have at least one of the three top targets in their target set.

### 13.5 Tie diagnostic (status ok Markov predictions only)

| Configuration | Covered N | Top-1 tied | Top-3 boundary tied | n_equal_top >= 3 | Tied N | Tied Top-1 hits | Tied Top-3 hits | Not tied N | Not tied Top-1 hits | Not tied Top-3 hits |
|---|---|---|---|---|---|---|---|---|---|---|
| collapsed_full | 34 | 15 | 10 | 4 | 15 | 0 | 1 | 19 | 1 | 1 |
| collapsed_parent | 41 | 15 | 10 | 3 | 15 | 0 | 1 | 26 | 4 | 4 |
| raw_full | 49 | 14 | 14 | 3 | 14 | 0 | 1 | 35 | 12 | 12 |
| raw_parent | 58 | 18 | 20 | 4 | 18 | 0 | 1 | 40 | 12 | 15 |
| collapsed_full_no_s006 | 34 | 15 | 10 | 4 | 15 | 0 | 1 | 19 | 1 | 1 |

- `collapsed_full`: 15 of 34 Markov predictions have their Top-1 choice decided by the technique-ID tie-break.
- `collapsed_parent`: 15 of 41 Markov predictions have their Top-1 choice decided by the technique-ID tie-break.
- `raw_full`: 14 of 49 Markov predictions have their Top-1 choice decided by the technique-ID tie-break.
- `raw_parent`: 18 of 58 Markov predictions have their Top-1 choice decided by the technique-ID tie-break.
- `collapsed_full_no_s006`: 15 of 34 Markov predictions have their Top-1 choice decided by the technique-ID tie-break.

### 13.6 Hit concentration by technique (`collapsed_full`, descriptive)

| Method | Technique | Top-1 hit samples | Top-3 hit samples |
|---|---|---|---|
| markov | T1105 | 1 | 2 |
| frequency | T1105 | 3 | 7 |
| frequency | T1003.008 | 1 | 1 |
| markov_fallback | T1105 | 1 | 4 |
| markov_fallback | T1003.008 | 1 | 1 |

Most frequent targets in the primary slice pooled over all four episodes (descriptive only; computed on all episodes, not a leakage-free baseline):

| Rank | Target technique | Test samples containing target (pooled) |
|---|---|---|
| 1 | T1105 | 7 |
| 2 | T1033 | 4 |
| 3 | T1003.008 | 4 |
| 4 | T1059 | 3 |
| 5 | T1083 | 3 |

- In `collapsed_full`, 7 of 8 Frequency Top-3 hits involve technique T1105.

## 14. Limitations (only statements backed by numbers in this report)

- Sample size: 67 test samples in `collapsed_full` from 4 episodes; Wilson intervals in section 3 are wide and understate uncertainty because samples within an episode are not independent.
- Closed vocabulary: in `collapsed_full`, 35 of 67 samples (52.24%) have at least one target technique seen as a training target; 32 do not, so neither method can hit them.
- Markov coverage in `collapsed_full` is 34 of 67 (50.75%); the other 33 samples are abstentions counted as misses.
- The frequency baseline and the Markov model are compared on hit counts only; no significance test was run.

Hypothesis (not tested): low Markov hit counts may be related to few repeated transitions across episodes; the support-bucket table (13.3) and the repeat-current-set reference (13.2) are the only related computations here and do not establish a cause.

Hypothesis (not tested): the techniques the frequency baseline predicts may be common across episodes for reasons specific to this dataset; table 13.4 shows only how often they occur as targets.

## 15. Figures

- `reports/figures/headline_metrics.png`
- `reports/figures/per_fold_performance.png`
- `reports/figures/confusion_matrix_parent.png`
