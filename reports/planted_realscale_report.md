# Real-Scale Planted-Structure Power Analysis (A4) Report

## Pre-Declared Design & Calibration Setup

- **Vocabulary (V)**: All 64 distinct MITRE ATT&CK technique IDs in real collapsed sequences E1–E4 (read at runtime, $V=64$).
- **Planted Successor Permutation (pi)**: Cyclic permutation $\pi(t_i) = t_{(i+1) \% V}$ over the sorted vocabulary without fixed points.
- **Episode Lengths**: Real collapsed lengths of E1–E4 (19, 20, 21, 11), yielding 67 evaluated transition samples per replicate dataset.
- **Evaluation Protocol**: 4-episode Leave-One-Episode-Out cross-validation using production `MarkovModel` and `FrequencyBaseline`.
- **Signal Levels (s)**: `0.00, 0.25, 0.50, 0.75, 1.00` (200 replicates per signal level, seeds 0..199).
- **Reachable Fraction (R)**: The share of test fold samples whose exact $(current \to target)$ transition appears at least once in that fold's training episodes (computed directly from sample lists, independent of the model).
- **Chance Top-1**: $1/(V - 1) = 1/63 = 0.015873$.

---

## Pre-Declared Gates Verification Summary

| Gate | Description | Measured Value | Threshold | Result |
|:---|:---|:---:|:---:|:---:|
| **G8** | s=0.0: |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE) | `0.0074` | `<= 0.0200` | **PASS** |
| **G9** | Markov Top-1 non-decreasing across s | `[0.0084, 0.0399, 0.1466, 0.3206, 0.6016]` | Non-decreasing | **PASS** |
| **G10** | s=1.0: Markov Top-1 <= R and mean Markov >= 0.99 * mean R | Ratio: `1.0000` | All <= R & Ratio >= 0.9900 | **PASS** |
| **G11** | Negative Control: broken Markov fails G10 | Ratio: `0.0260` | `< 0.9900 (must fail G10)` | **PASS (Failed G10 as expected)** |

---

## Real-Scale Power Analysis Results Table

| Signal (s) | Markov Top-1 (Mean ± SE) | Markov Top-3 (Mean ± SE) | Frequency Top-1 (Mean ± SE) | Frequency Top-3 (Mean) | Mean Reachable (R) | Markov Exceeds Freq by > 2 SE? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.00 | 0.0084 ± 0.0011 | 0.0116 ± 0.0013 | 0.0165 ± 0.0015 | 0.0457 | 0.0116 | NO (diff = -0.0081) |
| 0.25 | 0.0399 ± 0.0024 | 0.0528 ± 0.0028 | 0.0123 ± 0.0012 | 0.0413 | 0.0533 | **YES** (diff = +0.0275) |
| 0.50 | 0.1466 ± 0.0048 | 0.1731 ± 0.0050 | 0.0163 ± 0.0015 | 0.0508 | 0.1731 | **YES** (diff = +0.1303) |
| 0.75 | 0.3206 ± 0.0076 | 0.3438 ± 0.0078 | 0.0157 ± 0.0014 | 0.0460 | 0.3438 | **YES** (diff = +0.3049) |
| 1.00 | 0.6016 ± 0.0120 | 0.6016 ± 0.0120 | 0.0164 ± 0.0011 | 0.0487 | 0.6016 | **YES** (diff = +0.5852) |
| *Real Data* | `0.0149` | `0.0299` | `0.0597` | `0.1194` | — | *real data, different generator, shown for scale only* |

**Smallest signal $s$ at which Markov Top-1 exceeds Frequency Top-1 by > 2 combined SE**: `s = 0.25`.

---

## Key Methodological Insights (Power & Reachability Ceiling)

1. **The Reachability Ceiling at Real Scale**: Even under a 100% deterministic sequential process ($s=1.00$), Leave-One-Episode-Out cross-validation on four episodes with lengths 19, 20, 21, and 11 over a 64-technique vocabulary only achieves a maximum reachable transition coverage of $\approx 60.16\%$ ($R=0.6016$). The remaining $\approx 39.84\%$ of test transitions never appeared in the three training episodes of that fold.
2. **Markov Optimality**: At $s=1.00$, the production Markov model achieves an empirical Top-1 accuracy of exactly $0.6016$, matching the reachable fraction $R$ in every replicate. It captures 100% of reachable signal and nothing unobserved.
3. **Statistical Power**: At $s=0.25$, Markov Top-1 ($0.0399$) already exceeds Frequency Top-1 ($0.0123$) by more than 2 combined standard errors. This establishes that the experimental setup has sufficient power to detect modest sequential structure ($s \ge 0.25$) when present across independent folds.

