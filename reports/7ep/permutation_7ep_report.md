# Pre-Registered 7-Episode Permutation Test Report (E1–E7)

## Pre-Declared Test Design & Purpose

- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines across all seven episodes (E1–E7).
- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: Pre-declared headline null hypothesis (prereg Section 10). Shuffles the collapsed sequence strictly within each episode, preserving exact sample counts ($N=95$ technique, $N=76$ tactic) and marginal item frequencies. S1 p-values enter the pre-registered Holm step-down correction for hypotheses P3 and P4.
- **Constrained Scheme (S3 - Adjacency-Constrained Shuffle)**: Shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items share identical technique sets (technique level) or identical tactic sets (tactic level), using rejection sampling with up to 10,000 tries per episode. Reported alongside S1.
- **Excluded Scheme (S2)**: S2 (raw-event shuffle) is excluded from the 7-episode design per prereg Section 10.
- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999).
- **One-Sided p-value Formula**: `p = (1 + count(null >= observed)) / (1 + B)`.
- **Pre-Registered Primary Comparisons**: P3 = Tactic Markov Hit@3 vs S1 null; P4 = Technique Markov Hit@3 vs S1 null.
- **Conclusion Text Generation Rule**: Generated strictly by code from p-values without causal claims. If any scheme fails order-free validity, its conclusions are prefixed with *'INVALID NULL - do not cite:'*.

---

## Scheme Validity Check (Order-Free Frequency Statistics)

A valid order-only null permutation must not perturb the performance of an **order-free** model (FrequencyBaseline). If an order-free statistic exhibits $p < 0.05$, the scheme alters marginal event distributions or set compositions in addition to order, confounding order-signal tests.

| Scheme | Level | Statistic | Observed Rate | Null Mean Rate | p-value | MC SE | Order-Free Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---|
| S1 (Collapsed-Order) | Technique | Frequency Hit@1 | +0.0737 | +0.0710 | 0.6633 | 0.0149 | PASS (Valid) |
| S1 (Collapsed-Order) | Technique | Frequency Hit@3 | +0.1684 | +0.1582 | 0.5624 | 0.0157 | PASS (Valid) |
| S1 (Collapsed-Order) | Tactic | Frequency Hit@1 | +0.1842 | +0.2042 | 0.5425 | 0.0158 | PASS (Valid) |
| S1 (Collapsed-Order) | Tactic | Frequency Hit@3 | +0.6316 | +0.6045 | 0.3257 | 0.0148 | PASS (Valid) |
| S3 (Constrained Shuffle) | Technique | Frequency Hit@1 | +0.0737 | +0.0715 | 0.6723 | 0.0148 | PASS (Valid) |
| S3 (Constrained Shuffle) | Technique | Frequency Hit@3 | +0.1684 | +0.1570 | 0.5405 | 0.0158 | PASS (Valid) |
| S3 (Constrained Shuffle) | Tactic | Frequency Hit@1 | +0.1842 | +0.2023 | 0.5295 | 0.0158 | PASS (Valid) |
| S3 (Constrained Shuffle) | Tactic | Frequency Hit@3 | +0.6316 | +0.6016 | 0.2767 | 0.0141 | PASS (Valid) |

- **S1 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \ge 0.05$).
- **S3 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \ge 0.05$).

---

## Sample Count Distribution (Confound Resolution)

| Scheme | Level | Observed N | Permutation Min N | Permutation Mean N | Permutation Max N | Invariant N? |
|:---|:---|:---:|:---:|:---:|:---:|:---:|
| S1 (Collapsed-Order) | Technique (collapsed_full) | 95 | 95 | 95.00 | 95 | **YES (Constant)** |
| S1 (Collapsed-Order) | Tactic (tactic_collapsed) | 76 | 76 | 76.00 | 76 | **YES (Constant)** |
| S3 (Constrained Shuffle) | Technique (collapsed_full) | 95 | 95 | 95.00 | 95 | **YES (Constant)** |
| S3 (Constrained Shuffle) | Tactic (tactic_collapsed) | 76 | 76 | 76.00 | 76 | **YES (Constant)** |

### S3 Constrained Shuffle Rejection Sampling Statistics

- **Max Tries Allowed Per Episode**: 10000
- **Technique Level**: Excluded Permutations = 0, Min Tries = 7, Mean Tries = 8.82, Max Tries = 18
- **Tactic Level**: Excluded Permutations = 0, Min Tries = 7, Mean Tries = 19.38, Max Tries = 61

---

## Primary Scheme S1 Results (Headline)

### Technique Level (`collapsed_full`, N=95)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.0316 | 3 / 95    | +0.0124 | 0.0138 | +0.0000 | +0.0421 | 0.1548 | 0.0114 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1548) |
| Markov Hit@3               | +0.0316 | 3 / 95    | +0.0236 | 0.0196 | +0.0000 | +0.0632 | 0.3856 | 0.0154 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3856) |
| Frequency Hit@1            | +0.0737 | 7 / 95    | +0.0710 | 0.0101 | +0.0526 | +0.1053 | 0.6633 | 0.0149 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6633) |
| Frequency Hit@3            | +0.1684 | 16 / 95   | +0.1582 | 0.0238 | +0.1053 | +0.1895 | 0.5624 | 0.0157 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5624) |
| Markov Fallback Hit@1      | +0.0316 | 3 / 95    | +0.0422 | 0.0184 | +0.0105 | +0.0842 | 0.8012 | 0.0126 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.8012) |
| Markov Fallback Hit@3      | +0.0421 | 4 / 95    | +0.0842 | 0.0259 | +0.0421 | +0.1368 | 0.9810 | 0.0043 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.9810) |
| Markov - Frequency Hit@1   | -0.0421 | -4 / 95   | -0.0586 | 0.0169 | -0.0947 | -0.0211 | 0.2358 | 0.0134 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2358) |
| Markov - Frequency Hit@3   | -0.1368 | -13 / 95  | -0.1346 | 0.0297 | -0.1789 | -0.0737 | 0.5475 | 0.0157 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5475) |

### Tactic Level (`tactic_collapsed`, N=76)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.2895 | 22 / 76   | +0.1869 | 0.0522 | +0.0921 | +0.3026 | 0.0430 | 0.0064 | observed exceeds the shuffled-order null (p=0.0430) |
| Markov Hit@3               | +0.6316 | 48 / 76   | +0.4777 | 0.0618 | +0.3553 | +0.5921 | 0.0060 | 0.0024 | observed exceeds the shuffled-order null (p=0.0060) |
| Frequency Hit@1            | +0.1842 | 14 / 76   | +0.2042 | 0.0408 | +0.1447 | +0.2632 | 0.5425 | 0.0158 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5425) |
| Frequency Hit@3            | +0.6316 | 48 / 76   | +0.6045 | 0.0392 | +0.5263 | +0.6711 | 0.3257 | 0.0148 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3257) |
| Markov Fallback Hit@1      | +0.3158 | 24 / 76   | +0.1909 | 0.0521 | +0.1053 | +0.3026 | 0.0200 | 0.0044 | observed exceeds the shuffled-order null (p=0.0200) |
| Markov Fallback Hit@3      | +0.6579 | 50 / 76   | +0.4911 | 0.0614 | +0.3684 | +0.6056 | 0.0020 | 0.0014 | observed exceeds the shuffled-order null (p=0.0020) |
| Markov - Frequency Hit@1   | +0.1053 | +8 / 76   | -0.0173 | 0.0639 | -0.1316 | +0.1184 | 0.0410 | 0.0063 | observed exceeds the shuffled-order null (p=0.0410) |
| Markov - Frequency Hit@3   | +0.0000 | +0 / 76   | -0.1269 | 0.0672 | -0.2500 | +0.0000 | 0.0390 | 0.0061 | observed exceeds the shuffled-order null (p=0.0390) |

---

## Constrained Scheme S3 Results (Adjacency-Constrained Null)

### Technique Level (`collapsed_full`, N=95)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.0316 | 3 / 95    | +0.0121 | 0.0133 | +0.0000 | +0.0421 | 0.1439 | 0.0111 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.1439) |
| Markov Hit@3               | +0.0316 | 3 / 95    | +0.0224 | 0.0184 | +0.0000 | +0.0632 | 0.3656 | 0.0152 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.3656) |
| Frequency Hit@1            | +0.0737 | 7 / 95    | +0.0715 | 0.0108 | +0.0526 | +0.1053 | 0.6723 | 0.0148 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.6723) |
| Frequency Hit@3            | +0.1684 | 16 / 95   | +0.1570 | 0.0243 | +0.1053 | +0.1895 | 0.5405 | 0.0158 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5405) |
| Markov Fallback Hit@1      | +0.0316 | 3 / 95    | +0.0414 | 0.0181 | +0.0105 | +0.0842 | 0.7872 | 0.0129 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.7872) |
| Markov Fallback Hit@3      | +0.0421 | 4 / 95    | +0.0837 | 0.0257 | +0.0421 | +0.1368 | 0.9770 | 0.0047 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.9770) |
| Markov - Frequency Hit@1   | -0.0421 | -4 / 95   | -0.0594 | 0.0170 | -0.0947 | -0.0211 | 0.2158 | 0.0130 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2158) |
| Markov - Frequency Hit@3   | -0.1368 | -13 / 95  | -0.1346 | 0.0298 | -0.1789 | -0.0737 | 0.5544 | 0.0157 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5544) |

### Tactic Level (`tactic_collapsed`, N=76)

| Statistic | Observed Rate | Observed Hits / N | Null Mean Rate | Null SD | Null 2.5% | Null 97.5% | p-value | MC SE | Code-Generated Conclusion |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov Hit@1               | +0.2895 | 22 / 76   | +0.2026 | 0.0545 | +0.1053 | +0.3158 | 0.0759 | 0.0084 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0759) |
| Markov Hit@3               | +0.6316 | 48 / 76   | +0.4921 | 0.0612 | +0.3684 | +0.6053 | 0.0110 | 0.0033 | observed exceeds the shuffled-order null (p=0.0110) |
| Frequency Hit@1            | +0.1842 | 14 / 76   | +0.2023 | 0.0404 | +0.1447 | +0.2632 | 0.5295 | 0.0158 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.5295) |
| Frequency Hit@3            | +0.6316 | 48 / 76   | +0.6016 | 0.0372 | +0.5263 | +0.6711 | 0.2767 | 0.0141 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.2767) |
| Markov Fallback Hit@1      | +0.3158 | 24 / 76   | +0.2073 | 0.0545 | +0.1053 | +0.3158 | 0.0400 | 0.0062 | observed exceeds the shuffled-order null (p=0.0400) |
| Markov Fallback Hit@3      | +0.6579 | 50 / 76   | +0.5063 | 0.0605 | +0.3816 | +0.6184 | 0.0090 | 0.0030 | observed exceeds the shuffled-order null (p=0.0090) |
| Markov - Frequency Hit@1   | +0.1053 | +8 / 76   | +0.0003 | 0.0621 | -0.1184 | +0.1316 | 0.0639 | 0.0077 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0639) |
| Markov - Frequency Hit@3   | +0.0000 | +0 / 76   | -0.1095 | 0.0674 | -0.2500 | +0.0132 | 0.0609 | 0.0076 | not distinguishable from the shuffled-order null at this sample size (this is not proof of absence) (p=0.0609) |

### S1 vs S3 Monte Carlo Consistency

Monte Carlo permutation standard errors are given by $\text{SE}_{\text{MC}}(p) = \sqrt{p(1-p)/B}$ ($B=1000$). S1 and S3 p-values differing by less than two combined Monte Carlo standard errors are statistically consistent:

#### Technique Level (`collapsed_full`)

- **Markov Hit@1**: S1 $p = 0.1548$ (MC SE $= 0.0114$), S3 $p = 0.1439$ (MC SE $= 0.0111$); difference $|p_{S1} - p_{S3}| = 0.0110$ is less than two combined Monte Carlo standard errors (0.0319), confirming S1 and S3 are consistent.
- **Markov Hit@3**: S1 $p = 0.3856$ (MC SE $= 0.0154$), S3 $p = 0.3656$ (MC SE $= 0.0152$); difference $|p_{S1} - p_{S3}| = 0.0200$ is less than two combined Monte Carlo standard errors (0.0433), confirming S1 and S3 are consistent.
- **Frequency Hit@1**: S1 $p = 0.6633$ (MC SE $= 0.0149$), S3 $p = 0.6723$ (MC SE $= 0.0148$); difference $|p_{S1} - p_{S3}| = 0.0090$ is less than two combined Monte Carlo standard errors (0.0421), confirming S1 and S3 are consistent.
- **Frequency Hit@3**: S1 $p = 0.5624$ (MC SE $= 0.0157$), S3 $p = 0.5405$ (MC SE $= 0.0158$); difference $|p_{S1} - p_{S3}| = 0.0220$ is less than two combined Monte Carlo standard errors (0.0445), confirming S1 and S3 are consistent.
- **Markov Fallback Hit@1**: S1 $p = 0.8012$ (MC SE $= 0.0126$), S3 $p = 0.7872$ (MC SE $= 0.0129$); difference $|p_{S1} - p_{S3}| = 0.0140$ is less than two combined Monte Carlo standard errors (0.0362), confirming S1 and S3 are consistent.
- **Markov Fallback Hit@3**: S1 $p = 0.9810$ (MC SE $= 0.0043$), S3 $p = 0.9770$ (MC SE $= 0.0047$); difference $|p_{S1} - p_{S3}| = 0.0040$ is less than two combined Monte Carlo standard errors (0.0128), confirming S1 and S3 are consistent.
- **Markov - Frequency Hit@1**: S1 $p = 0.2358$ (MC SE $= 0.0134$), S3 $p = 0.2158$ (MC SE $= 0.0130$); difference $|p_{S1} - p_{S3}| = 0.0200$ is less than two combined Monte Carlo standard errors (0.0374), confirming S1 and S3 are consistent.
- **Markov - Frequency Hit@3**: S1 $p = 0.5475$ (MC SE $= 0.0157$), S3 $p = 0.5544$ (MC SE $= 0.0157$); difference $|p_{S1} - p_{S3}| = 0.0070$ is less than two combined Monte Carlo standard errors (0.0445), confirming S1 and S3 are consistent.

#### Tactic Level (`tactic_collapsed`)

- **Markov Hit@1**: S1 $p = 0.0430$ (MC SE $= 0.0064$), S3 $p = 0.0759$ (MC SE $= 0.0084$); difference $|p_{S1} - p_{S3}| = 0.0330$ exceeds two combined Monte Carlo standard errors (0.0211), reflecting sensitivity to the adjacency constraint on collapsed sequences.
- **Markov Hit@3**: S1 $p = 0.0060$ (MC SE $= 0.0024$), S3 $p = 0.0110$ (MC SE $= 0.0033$); difference $|p_{S1} - p_{S3}| = 0.0050$ is less than two combined Monte Carlo standard errors (0.0082), confirming S1 and S3 are consistent.
- **Frequency Hit@1**: S1 $p = 0.5425$ (MC SE $= 0.0158$), S3 $p = 0.5295$ (MC SE $= 0.0158$); difference $|p_{S1} - p_{S3}| = 0.0130$ is less than two combined Monte Carlo standard errors (0.0446), confirming S1 and S3 are consistent.
- **Frequency Hit@3**: S1 $p = 0.3257$ (MC SE $= 0.0148$), S3 $p = 0.2767$ (MC SE $= 0.0141$); difference $|p_{S1} - p_{S3}| = 0.0490$ exceeds two combined Monte Carlo standard errors (0.0410), reflecting sensitivity to the adjacency constraint on collapsed sequences.
- **Markov Fallback Hit@1**: S1 $p = 0.0200$ (MC SE $= 0.0044$), S3 $p = 0.0400$ (MC SE $= 0.0062$); difference $|p_{S1} - p_{S3}| = 0.0200$ exceeds two combined Monte Carlo standard errors (0.0152), reflecting sensitivity to the adjacency constraint on collapsed sequences.
- **Markov Fallback Hit@3**: S1 $p = 0.0020$ (MC SE $= 0.0014$), S3 $p = 0.0090$ (MC SE $= 0.0030$); difference $|p_{S1} - p_{S3}| = 0.0070$ exceeds two combined Monte Carlo standard errors (0.0066), reflecting sensitivity to the adjacency constraint on collapsed sequences.
- **Markov - Frequency Hit@1**: S1 $p = 0.0410$ (MC SE $= 0.0063$), S3 $p = 0.0639$ (MC SE $= 0.0077$); difference $|p_{S1} - p_{S3}| = 0.0230$ exceeds two combined Monte Carlo standard errors (0.0199), reflecting sensitivity to the adjacency constraint on collapsed sequences.
- **Markov - Frequency Hit@3**: S1 $p = 0.0390$ (MC SE $= 0.0061$), S3 $p = 0.0609$ (MC SE $= 0.0076$); difference $|p_{S1} - p_{S3}| = 0.0220$ exceeds two combined Monte Carlo standard errors (0.0195), reflecting sensitivity to the adjacency constraint on collapsed sequences.

---

## Pre-Registered Hypotheses P3 and P4 (S1 Headline)

- **Hypothesis P3 (Tactic Markov Hit@3 vs S1 Null)**: Raw $p = 0.0060$ (S3 reported alongside: $p = 0.0110$).
- **Hypothesis P4 (Technique Markov Hit@3 vs S1 Null)**: Raw $p = 0.3856$ (S3 reported alongside: $p = 0.3656$).

