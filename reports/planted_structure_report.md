# Planted-Structure Validation Experiment Report

## Pre-Declared Specifications & Experimental Setup

- **Vocabulary (V)**: 12 techniques (the 12 smallest sorted distinct technique IDs from E1–E4 collapsed sequences):
  `T1003, T1003.008, T1005, T1007, T1016, T1018, T1021.004, T1021.005, T1033, T1036.005, T1039, T1041`
- **Planted Successor Permutation (pi)**: Cyclic permutation `pi(t_i) = t_{(i+1) % 12}` without fixed points (marginal target frequencies are uniform).
- **Generator**: stdlib `random.Random` (seeds 0..19). Episode length: 26 items; 8 episodes per replicate dataset; 20 replicate datasets per signal level.
- **Signal Levels (s)**: `0.0, 0.25, 0.50, 0.75, 1.00`.
- **Evaluation Code**: Production `MarkovModel` and `FrequencyBaseline` evaluated under 8-fold Leave-One-Episode-Out cross-validation.
- **Theoretical Closed Forms**: Oracle Top-1 = `s + (1-s)/(V-1)`; Chance Top-1 = `1/(V-1) = 1/11 = 0.090909`.

---

## Pre-Declared Gates Verification Summary

| Gate | Description | Measured Value | Threshold | Result |
|:---|:---|:---:|:---:|:---:|
| **G1** | A1, s=1.0: Markov Top-1 >= 0.98 | `1.0000` | `>= 0.9800` | **PASS** |
| **G2** | A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE) | `0.0074` | `<= 0.0219` | **PASS** |
| **G3** | A1: Markov Top-1 non-decreasing across s | `[0.0835, 0.2787, 0.536, 0.775, 1.0]` | Non-decreasing | **PASS** |
| **G4** | A1, s >= 0.25: Markov within 0.05 of oracle | Max diff: `0.0394` | `<= 0.0500` | **PASS** |
| **G5** | A1, s >= 0.5: Markov exceeds Freq by >= 0.20 | Min excess: `0.4653` | `>= 0.2000` | **PASS** |
| **G6** | A2: |Markov Top-1 - Frequency Top-1| <= 0.03 (no order) | `0.0112` | `<= 0.0300` | **PASS** |
| **G7** | A3, s=1.0: Markov Top-1 >= 0.98 and non-decreasing | s=1.0: `1.0000` | `>= 0.9800 & non-decreasing` | **PASS** |
| **NegCtrl** | Negative control: broken Markov fails G1 | `0.0825` | `< 0.9800 (must fail G1)` | **PASS (Failed G1 as expected)** |

---

## Detailed Results by Variant

### Variant A1: Order Structure Recovery (Single-Technique Steps)

| Signal Level (s) | Oracle Top-1 | Markov Top-1 Mean | Markov SE | Frequency Top-1 Mean | |Markov - Oracle| | Markov - Frequency |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.00 | 0.0909 | 0.0835 | 0.0073 | 0.0875 | 0.0074 | -0.0040 |
| 0.25 | 0.3182 | 0.2787 | 0.0094 | 0.0833 | 0.0394 | +0.1955 |
| 0.50 | 0.5455 | 0.5360 | 0.0071 | 0.0708 | 0.0095 | +0.4653 |
| 0.75 | 0.7727 | 0.7750 | 0.0066 | 0.0810 | 0.0023 | +0.6940 |
| 1.00 | 1.0000 | 1.0000 | 0.0000 | 0.0835 | 0.0000 | +0.9165 |

### Variant A2: Skewed Targets (No Order Structure)

Evaluates i.i.d. draws with one dominant technique having probability 0.30 and the remaining 11 techniques uniform (`(1 - 0.30)/11 = 0.0636`):
- **Markov Top-1 Mean**: `0.2347`
- **Frequency Baseline Top-1 Mean**: `0.2458`
- **Absolute Difference**: `0.0112` (Gate G6 requires `<= 0.0300`)

### Variant A3: Set-Valued Steps {x, c(x)}

Evaluates pair-valued steps using companion permutation `c(x) = t_{(x+6) % 12}` testing the `1/(m*n)` set-weighting logic under production Hit@k:

| Signal Level (s) | A3 Markov Top-1 Mean | A3 Frequency Top-1 Mean |
|:---:|:---:|:---:|
| 0.00 | 0.2002 | 0.1730 |
| 0.25 | 0.4099 | 0.1747 |
| 0.50 | 0.6157 | 0.1615 |
| 0.75 | 0.8146 | 0.1631 |
| 1.00 | 1.0000 | 0.1653 |

---

## Negative Control Result

When Markov is deliberately broken (monkeypatched to predict a single fixed candidate `T1003` regardless of input):
- Broken Markov Top-1 at s=1.0: `0.0825`
- Gate G1 threshold: `>= 0.9800`
- Verdict: **G1 FAILS as expected**, proving that the test gate has non-trivial discriminating power.
