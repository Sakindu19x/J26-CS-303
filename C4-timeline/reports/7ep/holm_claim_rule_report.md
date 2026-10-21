# Pre-Registered Holm Step-Down Adjustment and Substantive Claim Rule Report

## Pre-Registered Protocol Context (prereg Section 6 & Amendment 1)

- **Primary Hypotheses Family**: $m=4$ pre-registered hypothesis tests:
  - **P1**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation).
  - **P2**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation).
  - **P3**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside).
  - **P4**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside).
- **Multiple Comparisons Procedure**: Holm-Bonferroni step-down correction applied across the family.
- **Pre-Declared Substantive Claim Rule**:
  > An **"improvement over the baseline demonstrated"** conclusion will be claimed **if and only if**:
  > 1. Pooled Markov Hit@3 > Pooled Frequency Hit@3, **AND**
  > 2. The Holm-adjusted $p$-value is $< 0.05$ for at least one slice level (technique or tactic).
  > 
  > Otherwise, the formal conclusion must report: **"not demonstrated"**.
- **Separate Order Signal Question**: Hypotheses P3 and P4 address the separate question: *"Does sequence order carry detectable predictive signal beyond unigram frequency?"*

---

## Holm Step-Down Adjustment Table

| Hypothesis | Target Level | Test Type | Raw $p$-value | Step-Down Rank | Multiplier | Holm-Adjusted $p$ | Significant at $\alpha=0.05$? | Pooled Markov Hit@3 | Pooled Freq Hit@3 | Markov > Freq? |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **P2** | `collapsed_full` | Exact two-sided McNemar | `0.0023` | 1 | 4 | `0.0094` | **YES (p < 0.05)** | `0.0316` | `0.1684` | NO (Markov < Freq) |
| **P3** | `tactic_collapsed` | One-sided S1 Permutation Test (B=1000) | `0.0060` | 2 | 3 | `0.0180` | **YES (p < 0.05)** | `0.6316` | `0.6316` | NO (Markov == Freq) |
| **P4** | `collapsed_full` | One-sided S1 Permutation Test (B=1000) | `0.3856` | 3 | 2 | `0.7712` | NO (p ≥ 0.05) | `0.0316` | `0.1684` | NO (Markov < Freq) |
| **P1** | `tactic_collapsed` | Exact two-sided McNemar | `1.0000` | 4 | 1 | `1.0000` | NO (p ≥ 0.05) | `0.6316` | `0.6316` | NO (Markov == Freq) |

*(Note for P3 and P4: S3 constrained shuffle p-values reported alongside S1 are $p=0.0110$ for tactic P3 and $p=0.3656$ for technique P4; per Amendment 1, only the pre-declared headline S1 p-values enter the Holm adjustment).*

---

## Formal Pre-Registered Verdict

### Substantive Baseline Improvement: **not demonstrated**

> Under the pre-registered claim rule, an improvement over the baseline is not demonstrated because: (1) At the technique level (P2), although the McNemar difference is statistically significant (Holm-adjusted p=0.0094), pooled Markov Hit@3 (0.0316) is lower than Frequency Hit@3 (0.1684), favoring the baseline; and (2) At the tactic level (P1), pooled Markov Hit@3 (0.6316) equals Frequency Hit@3 (0.6316) with Holm-adjusted p=1.0000.

### Order-Signal Question (P3 and P4)

> Order carries detectable predictive signal beyond the shuffled-order null at the tactic level (Holm-adjusted p=0.0180), but order signal is not distinguishable from the shuffled-order null at the technique level (Holm-adjusted p=0.7712).

