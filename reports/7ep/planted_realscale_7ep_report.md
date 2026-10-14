# Real-Scale Planted-Structure Power Analysis Report (7 Episodes)

## Pre-Declared Design & Setup (7 Episodes)

- **Vocabulary (V)**: All 82 distinct MITRE ATT&CK technique IDs across real collapsed sequences E1–E7 (read at runtime, $V=82$).
- **Planted Successor Permutation (pi)**: Cyclic permutation $\pi(t_i) = t_{(i+1) \% V}$ over the sorted vocabulary without fixed points.
- **Episode Lengths**: Real collapsed lengths of E1–E7 (E1: 19, E2: 20, E3: 21, E4: 11, E5: 3, E6: 15, E7: 13), yielding 95 evaluated transition samples per replicate dataset (93 samples when excluding E5).
- **Evaluation Protocol**: 7-episode Leave-One-Episode-Out cross-validation using production `MarkovModel` and `FrequencyBaseline`.
- **Signal Levels (s)**: `0.00, 0.25, 0.50, 0.75, 1.00` (200 replicates per signal level, seeds 0..199).
- **Reachable Fraction (R)**: The share of test fold samples whose exact $(current \to target)$ transition appears at least once in that fold's training episodes.
  - **Mean R at $s=1.0$ across all 7 episodes (95 samples)**: `0.6498`
  - **Mean R at $s=1.0$ excluding E5 (93 samples)**: `0.6482` (Note: E5 has length 3 items, yielding 2 transition samples, with 0 reachable transitions).
- **Chance Top-1**: $1/(V - 1) = 1/81 = 0.012346$.

---

## Pre-Declared Gates Verification Summary

| Gate | Description (Quoted from Pre-Registration) | Measured Value | Threshold | Result |
|:---|:---|:---:|:---:|:---:|
| **G8** | at s=0, |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE) | `0.0054` | `<= 0.0200` | **PASS** |
| **G9** | Markov Top-1 mean is non-decreasing across s levels | `[0.0069, 0.0485, 0.1773, 0.3716, 0.6498]` | Non-decreasing | **PASS** |
| **G10** | at s=1.0, Markov Top-1 <= R + 1e-9 in every replicate AND mean Markov Top-1 >= 0.99 * mean R | Ratio: `1.0000` | All <= R & Ratio >= 0.9900 | **PASS** |
| **G11** | Negative control: with Markov deliberately broken (fixed candidate), G10 fails | Ratio: `0.0192` | `< 0.9900 (must fail G10)` | **PASS (Failed G10 as expected)** |

---

## Real-Scale Power Analysis Results Table (7 Episodes)

| Signal (s) | Markov Top-1 (Mean ± SE) | Markov Top-3 (Mean ± SE) | Frequency Top-1 (Mean ± SE) | Frequency Top-3 (Mean) | Mean Reachable R (All 7ep) | Mean Reachable R (No E5) | Markov Exceeds Freq by > 2 SE? |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.00 | 0.0069 ± 0.0008 | 0.0103 ± 0.0010 | 0.0113 ± 0.0011 | 0.0377 | 0.0104 | 0.0105 | NO (diff = -0.0043) |
| 0.25 | 0.0485 ± 0.0025 | 0.0671 ± 0.0029 | 0.0129 ± 0.0012 | 0.0354 | 0.0674 | 0.0672 | **YES** (diff = +0.0356) |
| 0.50 | 0.1773 ± 0.0043 | 0.2105 ± 0.0047 | 0.0116 ± 0.0011 | 0.0358 | 0.2111 | 0.2107 | **YES** (diff = +0.1656) |
| 0.75 | 0.3716 ± 0.0054 | 0.3991 ± 0.0054 | 0.0119 ± 0.0011 | 0.0362 | 0.3992 | 0.3990 | **YES** (diff = +0.3597) |
| 1.00 | 0.6498 ± 0.0090 | 0.6498 ± 0.0090 | 0.0124 ± 0.0010 | 0.0369 | 0.6498 | 0.6482 | **YES** (diff = +0.6374) |
| *Real Data* | `0.0316` | `0.0316` | `0.0737` | `0.1684` | — | — | *real data, different generator, shown for scale only* |

**Smallest signal $s$ at which Markov Top-1 exceeds Frequency Top-1 by > 2 combined SE**: `s = 0.25`.

---

## Reachable Fraction Analysis (E5 Sensitivity)

- Under full signal ($s=1.00$), the 7-episode design achieves a mean reachable fraction of $R = 0.6498$ across all 95 transition samples.
- When excluding episode E5 (which contains only 2 transition samples and exhibits 0 training transitions), the mean reachable fraction is $R = 0.6482$ across the remaining 93 samples.
- Production MarkovModel captures 100% of reachable signal at $s=1.00$ (mean Top-1 matches mean $R$ exactly).

