# Permutation Test on Real Episodes (E1–E4) v2 Report

## Pre-Declared Test Design & Purpose

- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines in real telemetry episodes E1–E4.
- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: The items of the stored collapsed sequence for each episode are shuffled strictly within the episode. Sample counts $N$ are strictly invariant ($N=67$ for technique, $N=53$ for tactic in every permutation). Headline decisions are made solely under S1.
- **Sensitivity Scheme (S2 - Raw-Shuffle Rate-Based)**: Raw labeled events are shuffled within each episode and re-collapsed, yielding variable sample counts ($N \in [82, 95]$ technique, $N \in [74, 90]$ tactic). The statistic is evaluated as hit rate (hits / $N_{perm}$) compared against observed hit rate.
- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999).
- **One-Sided p-value Formula**: `p = (1 + count(null >= observed)) / (1 + B)`.
- **Pre-Declared Decision Rule**: `p < 0.05` under S1 only. Sensitivity scheme S2 is documented alongside S1 for methodological completeness.
- **Conclusion Text Generation Rule**: Every conclusion sentence is generated strictly by code from the p-value: if $p < 0.05$, *'observed exceeds the shuffled-order null (p=...)'*; else *'not distinguishable from the shuffled-order null at this sample size (this is not proof of absence)'*. No causal inferences are asserted.

---

## Sample Count Distribution (Confound Resolution)

| Scheme | Level | Observed N | Permutation Min N | Permutation Mean N | Permutation Max N | Invariant N? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| S1 (Collapsed-Order) | Technique (collapsed_full) | 67 | 67 | 67.00 | 67 | **YES (Constant)** |
| S1 (Collapsed-Order) | Tactic (tactic_collapsed) | 53 | 53 | 53.00 | 53 | **YES (Constant)** |
| S2 (Raw-Shuffle) | Technique (collapsed_full) | 67 | 82 | 89.36 | 95 | NO (Variable) |
| S2 (Raw-Shuffle) | Tactic (tactic_collapsed) | 53 | 74 | 82.51 | 90 | NO (Variable) |

---

## Primary Scheme S1 Results (Headline)

### Technique Level (`collapsed_full`, N=67)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.0149 | 1 / 67    | +0.0075 | 0.0118 | +0.0000 | +0.0448 | 0.3467 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3467) |
| Markov Hit@3               | +0.0299 | 2 / 67    | +0.0151 | 0.0176 | +0.0000 | +0.0597 | 0.3327 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3327) |
| Frequency Hit@1            | +0.0597 | 4 / 67    | +0.0493 | 0.0253 | +0.0149 | +0.0896 | 0.6114 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6114) |
| Frequency Hit@3            | +0.1194 | 8 / 67    | +0.1082 | 0.0253 | +0.0448 | +0.1343 | 0.5944 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5944) |
| Markov Fallback Hit@1      | +0.0299 | 2 / 67    | +0.0366 | 0.0213 | +0.0000 | +0.0746 | 0.7103 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.7103) |
| Markov Fallback Hit@3      | +0.0746 | 5 / 67    | +0.0749 | 0.0266 | +0.0299 | +0.1194 | 0.6194 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6194) |
| Markov - Frequency Hit@1   | -0.0448 | -3 / 67   | -0.0418 | 0.0273 | -0.0896 | +0.0149 | 0.5445 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5445) |
| Markov - Frequency Hit@3   | -0.0896 | -6 / 67   | -0.0931 | 0.0307 | -0.1343 | -0.0149 | 0.4745 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.4745) |

### Tactic Level (`tactic_collapsed`, N=53)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.2075 | 11 / 53   | +0.1574 | 0.0588 | +0.0566 | +0.2830 | 0.2298 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2298) |
| Markov Hit@3               | +0.5283 | 28 / 53   | +0.3909 | 0.0811 | +0.2264 | +0.5472 | 0.0589 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0589) |
| Frequency Hit@1            | +0.1698 | 9 / 53    | +0.1842 | 0.0491 | +0.1321 | +0.2642 | 0.5095 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5095) |
| Frequency Hit@3            | +0.6226 | 33 / 53   | +0.5637 | 0.0652 | +0.4340 | +0.6226 | 0.1299 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1299) |
| Markov Fallback Hit@1      | +0.2453 | 13 / 53   | +0.1730 | 0.0593 | +0.0755 | +0.3019 | 0.1429 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1429) |
| Markov Fallback Hit@3      | +0.5660 | 30 / 53   | +0.4310 | 0.0793 | +0.2825 | +0.5849 | 0.0609 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0609) |
| Markov - Frequency Hit@1   | +0.0377 | +2 / 53   | -0.0268 | 0.0725 | -0.1698 | +0.1321 | 0.2328 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2328) |
| Markov - Frequency Hit@3   | -0.0943 | -5 / 53   | -0.1728 | 0.0966 | -0.3585 | +0.0377 | 0.2208 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2208) |

---

## Sensitivity Scheme S2 Results (Rate-Based Comparison)

### Technique Level (`collapsed_full`, N_perm in [82, 95])

| Statistic | Observed Rate | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.0149 | +0.0070 | 0.0106 | +0.0000 | +0.0337 | 0.1758 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1758) |
| Markov Hit@3               | +0.0299 | +0.0166 | 0.0164 | +0.0000 | +0.0556 | 0.2298 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2298) |
| Frequency Hit@1            | +0.0597 | +0.0641 | 0.0501 | +0.0000 | +0.1413 | 0.3656 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3656) |
| Frequency Hit@3            | +0.1194 | +0.1181 | 0.0302 | +0.0435 | +0.1548 | 0.6853 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6853) |
| Markov Fallback Hit@1      | +0.0299 | +0.0484 | 0.0363 | +0.0000 | +0.1196 | 0.6693 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6693) |
| Markov Fallback Hit@3      | +0.0746 | +0.0937 | 0.0283 | +0.0324 | +0.1444 | 0.7952 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.7952) |
| Markov - Frequency Hit@1   | -0.0448 | -0.0570 | 0.0512 | -0.1349 | +0.0225 | 0.4585 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.4585) |
| Markov - Frequency Hit@3   | -0.0896 | -0.1015 | 0.0346 | -0.1461 | -0.0112 | 0.2537 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2537) |

### Tactic Level (`tactic_collapsed`, N_perm in [74, 90])

| Statistic | Observed Rate | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.2075 | +0.1016 | 0.0409 | +0.0361 | +0.1951 | 0.0150 | observed exceeds the shuffled-order null (p=0.0150) |
| Markov Hit@3               | +0.5283 | +0.2725 | 0.0647 | +0.1511 | +0.4070 | 0.0010 | observed exceeds the shuffled-order null (p=0.0010) |
| Frequency Hit@1            | +0.1698 | +0.1296 | 0.0201 | +0.0976 | +0.1810 | 0.0270 | observed exceeds the shuffled-order null (p=0.0270) |
| Frequency Hit@3            | +0.6226 | +0.5552 | 0.0601 | +0.4046 | +0.6585 | 0.1978 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1978) |
| Markov Fallback Hit@1      | +0.2453 | +0.1226 | 0.0417 | +0.0513 | +0.2208 | 0.0070 | observed exceeds the shuffled-order null (p=0.0070) |
| Markov Fallback Hit@3      | +0.5660 | +0.3362 | 0.0655 | +0.2184 | +0.4750 | 0.0010 | observed exceeds the shuffled-order null (p=0.0010) |
| Markov - Frequency Hit@1   | +0.0377 | -0.0279 | 0.0424 | -0.1011 | +0.0698 | 0.0679 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0679) |
| Markov - Frequency Hit@3   | -0.0943 | -0.2828 | 0.0822 | -0.4405 | -0.1071 | 0.0210 | observed exceeds the shuffled-order null (p=0.0210) |

---

## What this test cannot show

Statistical power in this permutation test is inherently limited by sample size:
- The technique evaluation contains only $N=67$ transition samples, and the tactic evaluation contains only $N=53$ transition samples across four episodes.
- In leave-one-episode-out cross-validation, models are trained on only three episodes per fold, limiting transition coverage across a large technique vocabulary ($V=64$).
- Therefore, failure to reject the shuffled-order null ($p \ge 0.05$) does not constitute proof of absence of sequential structure in cybersecurity attacks in general. It reflects the limited statistical power achievable with three training episodes on this dataset.
- See the accompanying real-scale planted-structure power analysis (A4 in `reports/planted_realscale_report.md`) for empirical demonstration of the sample-size and reachability constraints governing Markov model power under identical scale.

