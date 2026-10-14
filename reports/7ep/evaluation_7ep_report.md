# Pre-Registered 7-Episode LOEO Evaluation Report (E1–E7)

This report documents the pre-registered leave-one-episode-out (LOEO) evaluation across all seven episodes (E1–E7) of the C4 dataset.
All procedures strictly adhere to `reports/prereg_7episode_design.md` with Amendments 1, 2, and 3.
No model parameters, candidate thresholds, tie rules, or evaluation metrics were tuned.

---

## 1. Setup and Pre-Registration Gates

- **Evaluated Episodes**: E1, E2, E3, E4, E5, E6, E7 ($7$ folds).
- **Evaluated Slices**:
  1. **Primary**: Technique `collapsed_full` ($N=95$ transition samples).
  2. **Secondary**: Tactic `tactic_collapsed` ($N=76$ transition samples).
  3. **Reference**: Technique `raw_full` ($N=131$ transition samples).
- **Models Evaluated**: `MarkovModel` (first-order Markov chain), `FrequencyBaseline` (unconditional frequency), and `markov_fallback` (fallback to frequency when Markov status is not ok).
- **Fold Models**: Stored deterministically in `artifacts/7ep/fold_models/<slice>/<test_episode>.json` with hashes recorded in `artifacts/7ep/fold_models/manifest.json`.
- **Episode E5**: Evaluated as an explicit test fold ($N=2$, covered=0, ceiling=0).

---

## 2. Primary Slice: Technique `collapsed_full` (N=95)

### Headline Pooled Results

| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Markov          |  3 / 95 | 0.0316 | [0.0108, 0.0888]      |  3 / 95 | 0.0316 | [0.0108, 0.0888]      | 0.0337 | 0.0337 |
| Frequency       |  7 / 95 | 0.0737 | [0.0361, 0.1444]      | 16 / 95 | 0.1684 | [0.1064, 0.2562]      | 0.0595 | 0.1448 |
| Markov Fallback |  3 / 95 | 0.0316 | [0.0108, 0.0888]      |  4 / 95 | 0.0421 | [0.0165, 0.1033]      | 0.0337 | 0.0439 |

- **Coverage (Markov Status ok)**: 61/95 (0.6421).
  - On covered samples ($N=61$): Markov Hit@1 = 3/61 (0.0492), Frequency Hit@1 = 7/61 (0.1148).
  - On covered samples ($N=61$): Markov Hit@3 = 3/61 (0.0492), Frequency Hit@3 = 15/61 (0.2459).
- **Target Ceiling**: 59/95 (0.6211) of samples had at least one target technique appearing in training targets for that fold.

### Per-Fold Breakdown

| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1           | 18 |  0 (0.0000) |  0 (0.0000) |  2 (0.1111) |  4 (0.2222) |  0 (0.0000) |  0 (0.0000) | 13 / 18 | 12 / 18 |
| fold_2 | E2           | 19 |  1 (0.0526) |  1 (0.0526) |  2 (0.1053) |  4 (0.2105) |  1 (0.0526) |  1 (0.0526) | 13 / 19 | 15 / 19 |
| fold_3 | E3           | 20 |  0 (0.0000) |  0 (0.0000) |  2 (0.1000) |  2 (0.1000) |  0 (0.0000) |  0 (0.0000) | 10 / 20 |  9 / 20 |
| fold_4 | E4           | 10 |  1 (0.1000) |  1 (0.1000) |  1 (0.1000) |  1 (0.1000) |  1 (0.1000) |  1 (0.1000) |  6 / 10 |  6 / 10 |
| fold_5 | E5           |  2 |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 /  2 |  0 /  2 |
| fold_6 | E6           | 14 |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  3 (0.2143) |  0 (0.0000) |  1 (0.0714) |  8 / 14 |  7 / 14 |
| fold_7 | E7           | 12 |  1 (0.0833) |  1 (0.0833) |  0 (0.0000) |  2 (0.1667) |  1 (0.0833) |  1 (0.0833) | 11 / 12 | 10 / 12 |

---

## 3. Secondary Slice: Tactic `tactic_collapsed` (N=76)

### Headline Pooled Results

| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Markov          | 22 / 76 | 0.2895 | [0.1996, 0.3996]      | 48 / 76 | 0.6316 | [0.5193, 0.7312]      | 0.3093 | 0.6252 |
| Frequency       | 14 / 76 | 0.1842 | [0.1130, 0.2858]      | 48 / 76 | 0.6316 | [0.5193, 0.7312]      | 0.2269 | 0.6973 |
| Markov Fallback | 24 / 76 | 0.3158 | [0.2223, 0.4270]      | 50 / 76 | 0.6579 | [0.5460, 0.7546]      | 0.3284 | 0.6442 |
| Random (k=1,3)  |  --  / 76 | 0.1231 | [Expected Reference]  |  --  / 76 | 0.3298 | [Expected Reference]  |   --   |   --   |

- **Coverage (Markov Status ok)**: 74/76 (0.9737).
- **Target Ceiling**: 73/76 (0.9605).

### Per-Fold Breakdown

| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1           | 13 |  5 (0.3846) | 10 (0.7692) |  5 (0.3846) | 10 (0.7692) |  5 (0.3846) | 10 (0.7692) | 13 / 13 | 13 / 13 |
| fold_2 | E2           | 15 |  7 (0.4667) |  9 (0.6000) |  1 (0.0667) |  8 (0.5333) |  8 (0.5333) | 10 (0.6667) | 14 / 15 | 15 / 15 |
| fold_3 | E3           | 15 |  2 (0.1333) |  7 (0.4667) |  2 (0.1333) |  7 (0.4667) |  3 (0.2000) |  8 (0.5333) | 14 / 15 | 13 / 15 |
| fold_4 | E4           | 10 |  2 (0.2000) |  8 (0.8000) |  1 (0.1000) |  9 (0.9000) |  2 (0.2000) |  8 (0.8000) | 10 / 10 | 10 / 10 |
| fold_5 | E5           |  2 |  1 (0.5000) |  1 (0.5000) |  1 (0.5000) |  2 (1.0000) |  1 (0.5000) |  1 (0.5000) |  2 /  2 |  2 /  2 |
| fold_6 | E6           | 13 |  3 (0.2308) |  8 (0.6154) |  2 (0.1538) |  6 (0.4615) |  3 (0.2308) |  8 (0.6154) | 13 / 13 | 13 / 13 |
| fold_7 | E7           |  8 |  2 (0.2500) |  5 (0.6250) |  2 (0.2500) |  6 (0.7500) |  2 (0.2500) |  5 (0.6250) |  8 /  8 |  7 /  8 |

---

## 4. Reference Slice: Technique `raw_full` (N=131)

### Headline Pooled Results

| Model | Hit@1 Hits / N | Hit@1 Rate | Wilson 95% CI (Hit@1) | Hit@3 Hits / N | Hit@3 Rate | Wilson 95% CI (Hit@3) | Fold-Mean Hit@1 | Fold-Mean Hit@3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Markov          | 14 / 131 | 0.1069 | [0.0647, 0.1714]      | 15 / 131 | 0.1145 | [0.0706, 0.1803]      | 0.0843 | 0.0911 |
| Frequency       |  1 / 131 | 0.0076 | [0.0013, 0.0420]      | 11 / 131 | 0.0840 | [0.0475, 0.1441]      | 0.0051 | 0.0670 |
| Markov Fallback | 14 / 131 | 0.1069 | [0.0647, 0.1714]      | 15 / 131 | 0.1145 | [0.0706, 0.1803]      | 0.0843 | 0.0911 |

- **Coverage (Markov Status ok)**: 83/131 (0.6336).
- **Target Ceiling**: 81/131 (0.6183).

### Per-Fold Breakdown

| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1           | 26 |  6 (0.2308) |  6 (0.2308) |  0 (0.0000) |  6 (0.2308) |  6 (0.2308) |  6 (0.2308) | 20 / 26 | 19 / 26 |
| fold_2 | E2           | 20 |  1 (0.0500) |  1 (0.0500) |  0 (0.0000) |  0 (0.0000) |  1 (0.0500) |  1 (0.0500) | 14 / 20 | 16 / 20 |
| fold_3 | E3           | 28 |  5 (0.1786) |  5 (0.1786) |  1 (0.0357) |  3 (0.1071) |  5 (0.1786) |  5 (0.1786) | 15 / 28 | 14 / 28 |
| fold_4 | E4           | 21 |  1 (0.0476) |  2 (0.0952) |  0 (0.0000) |  1 (0.0476) |  1 (0.0476) |  2 (0.0952) |  8 / 21 |  8 / 21 |
| fold_5 | E5           |  2 |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 /  2 |  0 /  2 |
| fold_6 | E6           | 22 |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) |  0 (0.0000) | 15 / 22 | 14 / 22 |
| fold_7 | E7           | 12 |  1 (0.0833) |  1 (0.0833) |  0 (0.0000) |  1 (0.0833) |  1 (0.0833) |  1 (0.0833) | 11 / 12 | 10 / 12 |

---

## 5. Pre-Registered Paired Comparisons (P1, P2) and Non-Primary Tests

Per `reports/prereg_7episode_design.md` Section 6, the paired comparisons between `MarkovModel` and `FrequencyBaseline` are evaluated using exact two-sided McNemar tests on per-sample binary hit outcomes:

### P1: Secondary Slice (`tactic_collapsed`), Hit@3 (Markov vs Frequency)

| Contingency Cell | Count | Interpretation |
|:---|:---:|:---|
| Both Hit ($a$) | 36 | Both models predicted a correct tactic in top-3 |
| Markov Only ($b$) | 12 | Markov predicted correct in top-3, Frequency missed |
| Frequency Only ($c$) | 12 | Frequency predicted correct in top-3, Markov missed |
| Neither Hit ($d$) | 16 | Neither model predicted a correct tactic in top-3 |

- **Sample Size**: $N = 76$
- **Markov Pooled Rate**: 0.6316 (48/76)
- **Frequency Pooled Rate**: 0.6316 (48/76)
- **Pooled Rate Difference (Markov - Frequency)**: +0.0000
- **Discordant Counts**: $b = 12$, $c = 12$
- **Exact Two-Sided McNemar Test**: $p = 1.0000$ (raw p, pre-Holm)

### P2: Primary Slice (`collapsed_full`), Hit@3 (Markov vs Frequency)

| Contingency Cell | Count | Interpretation |
|:---|:---:|:---|
| Both Hit ($a$) |  1 | Both models predicted a correct technique in top-3 |
| Markov Only ($b$) |  2 | Markov predicted correct in top-3, Frequency missed |
| Frequency Only ($c$) | 15 | Frequency predicted correct in top-3, Markov missed |
| Neither Hit ($d$) | 77 | Neither model predicted a correct technique in top-3 |

- **Sample Size**: $N = 95$
- **Markov Pooled Rate**: 0.0316 (3/95)
- **Frequency Pooled Rate**: 0.1684 (16/95)
- **Pooled Rate Difference (Markov - Frequency)**: -0.1368
- **Discordant Counts**: $b = 2$, $c = 15$
- **Exact Two-Sided McNemar Test**: $p = 0.0023$ (raw p, pre-Holm)

### Non-Primary Descriptive Paired Comparisons (raw p, pre-Holm)

| Comparison | Slice | Metric | Model 1 Rate | Model 2 Rate | Difference | b | c | Exact McNemar p | Label |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov vs Frequency     | collapsed_full   | Hit@1 | 0.0316 | 0.0737 | -0.0421 |  2 |  6 | 0.2891 | raw p, pre-Holm |
| Markov vs Frequency     | tactic_collapsed | Hit@1 | 0.2895 | 0.1842 | +0.1053 | 16 |  8 | 0.1516 | raw p, pre-Holm |
| Fallback vs Frequency   | collapsed_full   | Hit@3 | 0.0421 | 0.1684 | -0.1263 |  2 | 14 | 0.0042 | raw p, pre-Holm |
| Fallback vs Frequency   | collapsed_full   | Hit@1 | 0.0316 | 0.0737 | -0.0421 |  2 |  6 | 0.2891 | raw p, pre-Holm |
| Fallback vs Frequency   | tactic_collapsed | Hit@3 | 0.6579 | 0.6316 | +0.0263 | 12 | 10 | 0.8318 | raw p, pre-Holm |
| Fallback vs Frequency   | tactic_collapsed | Hit@1 | 0.3158 | 0.1842 | +0.1316 | 16 |  6 | 0.0525 | raw p, pre-Holm |

---

## 6. Comparison with Archived 4-Episode Results

The following table compares the 7-episode results with the archived 4-episode baseline numbers read directly from `reports/evaluation_results.json` and `reports/tactic_evaluation_results.json`:

| Slice | Metric | 4-Episode Baseline (E1–E4) | 7-Episode Evaluation (E1–E7) | Absolute Change |
|:---|:---|:---:|:---:|:---:|
| Technique (`collapsed_full`) | Sample Count ($N$) | 67 | 95 | +28 |
| Technique (`collapsed_full`) | Markov Hit@1 | 1/67 (0.0149) | 3/95 (0.0316) | +0.0167 |
| Technique (`collapsed_full`) | Markov Hit@3 | 2/67 (0.0299) | 3/95 (0.0316) | +0.0017 |
| Technique (`collapsed_full`) | Frequency Hit@1 | 4/67 (0.0597) | 7/95 (0.0737) | +0.0140 |
| Technique (`collapsed_full`) | Frequency Hit@3 | 8/67 (0.1194) | 16/95 (0.1684) | +0.0490 |
| Technique (`collapsed_full`) | Markov Fallback Hit@1 | 2/67 (0.0299) | 3/95 (0.0316) | +0.0017 |
| Technique (`collapsed_full`) | Markov Fallback Hit@3 | 5/67 (0.0746) | 4/95 (0.0421) | -0.0325 |
| Technique (`collapsed_full`) | Coverage (Status ok) | 34/67 (0.5075) | 61/95 (0.6421) | +0.1346 |
| Technique (`collapsed_full`) | Target Ceiling | 35/67 (0.5224) | 59/95 (0.6211) | +0.0987 |
| Tactic (`tactic_collapsed`) | Sample Count ($N$) | 53 | 76 | +23 |
| Tactic (`tactic_collapsed`) | Markov Hit@1 | 11/53 (0.2075) | 22/76 (0.2895) | +0.0819 |
| Tactic (`tactic_collapsed`) | Markov Hit@3 | 28/53 (0.5283) | 48/76 (0.6316) | +0.1033 |
| Tactic (`tactic_collapsed`) | Frequency Hit@1 | 9/53 (0.1698) | 14/76 (0.1842) | +0.0144 |
| Tactic (`tactic_collapsed`) | Frequency Hit@3 | 33/53 (0.6226) | 48/76 (0.6316) | +0.0089 |
| Tactic (`tactic_collapsed`) | Markov Fallback Hit@1 | 13/53 (0.2453) | 24/76 (0.3158) | +0.0705 |
| Tactic (`tactic_collapsed`) | Markov Fallback Hit@3 | 30/53 (0.5660) | 50/76 (0.6579) | +0.0919 |
| Tactic (`tactic_collapsed`) | Coverage (Status ok) | 50/53 (0.9434) | 74/76 (0.9737) | +0.0303 |
| Tactic (`tactic_collapsed`) | Target Ceiling | 49/53 (0.9245) | 73/76 (0.9605) | +0.0360 |

---

## 7. Code-Generated Conclusion Summary

The following observational statements are generated strictly from the evaluation numbers without causal claims:
- **Primary Hypothesis P2 (Technique `collapsed_full` Hit@3)**: Markov achieved 0.0316 (3/95) versus Frequency 0.1684 (16/95), yielding pooled difference -0.1368 (discordant pairs: b=2, c=15, raw p=0.0023).
- **Secondary Hypothesis P1 (Tactic `tactic_collapsed` Hit@3)**: Markov achieved 0.6316 (48/76) versus Frequency 0.6316 (48/76), yielding pooled difference +0.0000 (discordant pairs: b=12, c=12, raw p=1.0000).
- **Sample Expansion**: Expanding from 4 to 7 episodes increased evaluated technique transition samples from 67 to 95 (+28 samples) and tactic transition samples from 53 to 76 (+23 samples).
- **Claim Rule Boundary**: Per pre-registration protocol, substantive claims of improvement or order-signal presence are governed by the joint P1–P4 criteria and Holm adjustment evaluated after permutation testing (Prompt 12b).

