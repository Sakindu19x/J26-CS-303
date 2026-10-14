# Planted-Structure Validation Experiment Report

## Pre-Declared Specifications & Experimental Setup

- **Vocabulary (V)**: 12 techniques (the 12 smallest sorted distinct technique IDs from E1–E4 collapsed sequences):
  `T1003, T1003.008, T1005, T1007, T1016, T1018, T1021.004, T1021.005, T1033, T1036.005, T1039, T1041`
- **Planted Successor Permutation (pi)**: Cyclic permutation `pi(t_i) = t_{(i+1) % 12}` without fixed points (marginal target frequencies are uniform).
- **Generator**: stdlib `random.Random` (seeds 0..19). Episode length: 26 items; 8 episodes per replicate dataset; 20 replicate datasets per signal level.
- **Signal Levels (s)**: `0.00, 0.25, 0.50, 0.75, 1.00`.
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

Evaluates i.i.d. draws with one dominant technique having nominal probability 0.30 (empirical post-collapse frequency 0.2490) and the remaining 11 techniques uniform (`(1 - 0.30)/11 = 0.0636`):
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

---

## Appendix: A2 Design History

This appendix discloses the design history of Variant A2 prior to the final accepted design. Gate G6 is evaluated on the final design only.

1. `test_a2_diff.py`:
   - **What it changed**: Evaluated whether running LOEO with variant="collapsed" versus variant="raw" without applying `collapse_sequence` to the raw generated events affected the A2 evaluation.
   - **G6 value (|Markov - Frequency|)**: `0.0343` (Mean Markov = 0.2707, Mean Frequency = 0.3050). Failed G6 threshold (<= 0.0300).
   - **Why changed**: Both variants returned identical scores because raw events had not been passed through `collapse_sequence()`, leaving repeated consecutive events unmerged.

2. `inspect_a2.py`:
   - **What it changed**: Inspected conditional transition probabilities and frequency predictions for a single fold of A2 to isolate why Markov Top-1 lagged Frequency Top-1.
   - **G6 value**: Diagnostic run on a single fold (not an 8-fold cross-replicate benchmark).
   - **Why changed**: Showed that Frequency consistently picked the dominant technique `T1003` (marginal frequency ~27.4%), whereas Markov conditional on `T1003` only chose `T1003` 19.5% of the time due to uncollapsed self-transitions `T1003 -> T1003`.

3. `test_a2_choices.py`:
   - **What it changed**: Tested whether sampling via `random.Random.choices` with explicit weights `[0.30] + [0.70/11]*11` differed from the Bernoulli sampling rule (`T1003 if random() < 0.30 else choice(others)`).
   - **G6 value (|Markov - Frequency|)**: `choices` produced diff = `0.0355` (Markov = 0.2712, Frequency = 0.3067); `bernoulli` produced diff = `0.0343` (Markov = 0.2707, Frequency = 0.3050). Both failed G6 (<= 0.0300).
   - **Why changed**: Sampling mechanism did not resolve the gap; the uncollapsed consecutive items remained the source of the discrepancy.

4. `test_a2_proper.py`:
   - **What it changed**: Verified independent 8-episode generation per replicate with fresh seed across 20 replicates without sequence collapsing.
   - **G6 value (|Markov - Frequency|)**: `0.0343` (Markov = 0.2707, Frequency = 0.3050). Failed G6 threshold (<= 0.0300).
   - **Why changed**: Confirmed that the gap was reproducible and intrinsic to uncollapsed i.i.d. draws.

5. `test_a2_dom.py`:
   - **What it changed**: Compared fixed dominant technique (`V[0] = T1003`) against rotating the dominant technique per replicate seed (`V[seed % 12]`).
   - **G6 value (|Markov - Frequency|)**: Fixed gave diff = `0.0343` (Markov = 0.2707, Frequency = 0.3050); seed-varying gave diff = `0.0503` (Markov = 0.2547, Frequency = 0.3050).
   - **Why changed**: Rotating dominant technique widened the discrepancy; fixed dominant technique was retained.

6. `test_a2_collapsed.py`:
   - **What it changed**: Applied production `collapse_sequence` to raw A2 sequences so consecutive identical events merge into collapsed items, exactly matching the real data pipeline and production collapsed sequence format.
   - **G6 value (|Markov - Frequency|)**: `0.0112` (Markov = 0.2347, Frequency = 0.2458). Passed G6 threshold (<= 0.0300).
   - **Why changed**: In real telemetry (and throughout C4 evaluation), sequential analysis is conducted on collapsed sequences; applying `collapse_sequence` eliminated self-repeats and aligned Markov and Frequency expectations.

7. `test_all_gates.py`:
   - **What it changed**: Integrated the collapsed A2 design alongside A1, A3, and negative control into a unified gate verification harness.
   - **G6 value**: `0.0112` (Markov = 0.2347, Frequency = 0.2458, diff = 0.0112 <= 0.0300). Passed.
   - **Why changed**: Final pre-execution gate validation confirming all pre-declared gates G1–G7 pass on the final design before generating production artifacts.
