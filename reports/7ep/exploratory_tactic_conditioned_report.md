# Exploratory Tactic-Conditioned Technique Prediction Report

> [!IMPORTANT]
> **EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT**
> This variant was pre-declared under Amendment 7 (2026-10-15) as an exploratory post hoc investigation of whether tactic-level order signal can transfer to technique prediction. It is not part of the pre-registered Holm step-down hypothesis testing family. The pre-registered primary evaluation verdict (FAIL on P1, Markov does not outperform Frequency baseline at technique level) is finalized and cannot be modified or overturned by this exploratory variant.

## 1. Setup and Methodology

- **Motivation**: Cross-episode diagnostics (`reports/7ep/diagnostics_7ep.md`) showed zero cross-scenario technique transition transfer, while permutation tests (`reports/7ep/permutation_7ep_report.md`) demonstrated statistically significant order signal at the tactic level ($p = 0.0410$ Hit@1, $p = 0.0390$ Hit@3 under S1).
- **Architecture**: Current techniques are mapped to current tactics; a LOEO fold tactic-level Markov model predicts next tactics; techniques mapping to those tactics in rank order are sorted by training target frequency and de-duplicated. If unseen state or empty, the model falls back to the fold Frequency baseline list.
- **Scope**: Evaluated on primary slice `collapsed_full` ($N=95$ across 7 episodes; $N=93$ under E5-removed sensitivity).

## 2. 7-Episode LOEO Results (Primary Slice: `collapsed_full`, N=95)

- **Coverage**: 90/95 (94.74%) samples had tactic Markov status `ok`.
- **Ceiling**: 59/95 (62.11%) samples had at least one target technique seen in training.

### Headline Performance Comparison

| Model | H@1 | H@3 | Top-1 Pooled | Wilson 95% Top-1 | Top-3 Pooled | Wilson 95% Top-3 | Fold-Mean Top-1 | Fold-Mean Top-3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Exploratory Variant (Tactic-Conditioned) | 5 | 8 | 5.26% | [2.27%, 11.73%] | 8.42% | [4.33%, 15.75%] | 4.28% | 7.29% |
| Frequency Baseline | 7 | 16 | 7.37% | [3.61%, 14.44%] | 16.84% | [10.64%, 25.62%] | 5.95% | 14.48% |
| Markov Model (Technique) | 3 | 3 | 3.16% | [1.08%, 8.88%] | 3.16% | [1.08%, 8.88%] | 3.37% | 3.37% |

### Paired Exact McNemar Test (Variant vs Frequency Baseline)

- **Top-1**: Variant hits and Frequency misses ($b=5$); Frequency hits and Variant misses ($c=7$); Exact McNemar $p = 0.7744$ (descriptive, raw p).
- **Top-3**: Variant hits and Frequency misses ($b=3$); Frequency hits and Variant misses ($c=11$); Exact McNemar $p = 0.0574$ (descriptive, raw p).

## 3. Tie-Sensitivity Diagnostic (P2 Machinery)

- **Tied Samples**: 6/95 samples tied at Top-1 boundary; 68/95 samples tied at Top-3 boundary.

| Metric | Observed Hits (Rate) | Expected Hits (Rate) | Best-Case Hits (Rate) | Worst-Case Hits (Rate) | Fold-Mean (Obs / Exp / Best / Worst) |
|:---|:---:|:---:|:---:|:---:|:---:|
| Hit@1 | 5 (5.26%) | 5.00 (5.26%) | 5 (5.26%) | 5 (5.26%) | 4.28% / 4.28% / 4.28% / 4.28% |
| Hit@3 | 8 (8.42%) | 8.25 (8.68%) | 9 (9.47%) | 8 (8.42%) | 7.29% / 7.46% / 8.00% / 7.29% |

## 4. E5-Removed Sensitivity Slice Repeat (N=93)

- **Coverage**: 88/93 (94.62%).
- **Ceiling**: 59/93 (63.44%).

| Model | H@1 | H@3 | Top-1 Pooled | Top-3 Pooled | Fold-Mean Top-1 | Fold-Mean Top-3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Exploratory Variant (Tactic-Conditioned) | 5 | 8 | 5.38% | 8.60% | 5.00% | 8.50% |
| Frequency Baseline | 7 | 16 | 7.53% | 17.20% | 6.94% | 16.90% |
| Markov Model (Technique) | 3 | 3 | 3.23% | 3.23% | 3.93% | 3.93% |

- **McNemar vs Frequency (E5-Removed)**: Top-1 $p = 0.7744$; Top-3 $p = 0.0574$ (descriptive, raw p).

## 5. Summary and Registration Integrity Verdict

- **Findings**: The exploratory tactic-conditioned variant achieved Hit@1 = 5/95 (5.26%) and Hit@3 = 8/95 (8.42%). While this numerically exceeds the technique-level Markov model (3/95 Hit@1, 3/95 Hit@3), it does not exceed the unconditional Frequency baseline (7/95 Hit@1, 16/95 Hit@3).
- **Status**: The pre-registered primary evaluation verdict (FAIL on P1, Markov does not outperform Frequency baseline at technique level) is finalized and cannot be modified or overturned by this exploratory variant.

