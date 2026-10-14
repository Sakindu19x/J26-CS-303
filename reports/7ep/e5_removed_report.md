# Pre-Registered E5-Removed Sensitivity Analysis Report

## Pre-Registered Context & Design (prereg Section 8)

- **Purpose**: Evaluate the sensitivity of findings to the inclusion of Episode E5 (which contains only 3 labeled steps and 2 transitions, with 0 coverage and 0 ceiling hits under 7-fold LOEO).
- **Protocol**: Full 6-fold Leave-One-Episode-Out cross-validation across {E1, E2, E3, E4, E6, E7}, with Episode E5 entirely excluded from both model training and evaluation.
- **Evaluated Slices**: Technique `collapsed_full` ($N=93$) and Tactic `tactic_collapsed` ($N=74$).
- **Statistical Labels**: Paired McNemar tests labeled strictly as `"sensitivity, raw p"`.

---

## Comparison: All 7 Episodes vs. E5-Removed (6 Episodes)

### Technique Level (`collapsed_full`)

| Metric | All 7 Episodes (N=95) | E5 Removed (N=93) | Difference (E5-Removed − All 7ep) |
|:---|:---:|:---:|:---:|
| Evaluated Samples ($N$) | 95 | 93 | -2 |
| Coverage Rate | 0.6421 (61/95) | 0.6559 (61/93) | +0.0138 |
| Ceiling Rate | 0.6211 (59/95) | 0.6344 (59/93) | +0.0134 |
| Markov Hit@1 | 0.0316 (3/95) | 0.0323 (3/93) | +0.0007 |
| Markov Hit@3 | 0.0316 (3/95) | 0.0323 (3/93) | +0.0007 |
| Frequency Hit@1 | 0.0737 (7/95) | 0.0753 (7/93) | +0.0016 |
| Frequency Hit@3 | 0.1684 (16/95) | 0.1720 (16/93) | +0.0036 |
| Fallback Hit@1 | 0.0316 (3/95) | 0.0323 (3/93) | +0.0007 |
| Fallback Hit@3 | 0.0421 (4/95) | 0.0430 (4/93) | +0.0009 |
| Exact McNemar p (Hit@3) | 0.0023 | 0.0023 (sensitivity, raw p) | +0.0000 |

### Tactic Level (`tactic_collapsed`)

| Metric | All 7 Episodes (N=76) | E5 Removed (N=74) | Difference (E5-Removed − All 7ep) |
|:---|:---:|:---:|:---:|
| Evaluated Samples ($N$) | 76 | 74 | -2 |
| Coverage Rate | 0.9737 (74/76) | 0.9730 (72/74) | -0.0007 |
| Ceiling Rate | 0.9605 (73/76) | 0.9595 (71/74) | -0.0011 |
| Markov Hit@1 | 0.2895 (22/76) | 0.2432 (18/74) | -0.0462 |
| Markov Hit@3 | 0.6316 (48/76) | 0.6351 (47/74) | +0.0036 |
| Frequency Hit@1 | 0.1842 (14/76) | 0.1757 (13/74) | -0.0085 |
| Frequency Hit@3 | 0.6316 (48/76) | 0.6216 (46/74) | -0.0100 |
| Fallback Hit@1 | 0.3158 (24/76) | 0.2703 (20/74) | -0.0455 |
| Fallback Hit@3 | 0.6579 (50/76) | 0.6622 (49/74) | +0.0043 |
| Exact McNemar p (Hit@3) | 1.0000 | 1.0000 (sensitivity, raw p) | +0.0000 |

---

## Pooled Results Summary (E5 Removed)

### Technique (`collapsed_full`, N=93)

- **Coverage**: `61/93` (0.6559)
- **Ceiling**: `59/93` (0.6344)
- **Markov Hit@1**: `3/93` (0.0323, 95% Wilson: `[0.0110, 0.0906]`)
- **Markov Hit@3**: `3/93` (0.0323, 95% Wilson: `[0.0110, 0.0906]`)
- **Frequency Hit@1**: `7/93` (0.0753, 95% Wilson: `[0.0369, 0.1473]`)
- **Frequency Hit@3**: `16/93` (0.1720, 95% Wilson: `[0.1088, 0.2613]`)
- **Fallback Hit@1**: `3/93` (0.0323, 95% Wilson: `[0.0110, 0.0906]`)
- **Fallback Hit@3**: `4/93` (0.0430, 95% Wilson: `[0.0169, 0.1054]`)

### Tactic (`tactic_collapsed`, N=74)

- **Coverage**: `72/74` (0.9730)
- **Ceiling**: `71/74` (0.9595)
- **Markov Hit@1**: `18/74` (0.2432, 95% Wilson: `[0.1598, 0.3521]`)
- **Markov Hit@3**: `47/74` (0.6351, 95% Wilson: `[0.5213, 0.7356]`)
- **Frequency Hit@1**: `13/74` (0.1757, 95% Wilson: `[0.1056, 0.2777]`)
- **Frequency Hit@3**: `46/74` (0.6216, 95% Wilson: `[0.5077, 0.7235]`)
- **Fallback Hit@1**: `20/74` (0.2703, 95% Wilson: `[0.1823, 0.3809]`)
- **Fallback Hit@3**: `49/74` (0.6622, 95% Wilson: `[0.5488, 0.7595]`)

---

## Per-Fold Performance Tables (E5 Removed)

### Technique Level (`collapsed_full`)

| Fold | Test Episode | N | Coverage | Ceiling | Markov Hit@1 | Markov Hit@3 | Frequency Hit@1 | Frequency Hit@3 | Fallback Hit@1 | Fallback Hit@3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| fold_e1 | E1 | 18 | 0.7222 | 0.6667 | 0.0000 | 0.0000 | 0.1111 | 0.2222 | 0.0000 | 0.0000 |
| fold_e2 | E2 | 19 | 0.6842 | 0.7895 | 0.0526 | 0.0526 | 0.1053 | 0.2105 | 0.0526 | 0.0526 |
| fold_e3 | E3 | 20 | 0.5000 | 0.4500 | 0.0000 | 0.0000 | 0.1000 | 0.1000 | 0.0000 | 0.0000 |
| fold_e4 | E4 | 10 | 0.6000 | 0.6000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 | 0.1000 |
| fold_e6 | E6 | 14 | 0.5714 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.2143 | 0.0000 | 0.0714 |
| fold_e7 | E7 | 12 | 0.9167 | 0.8333 | 0.0833 | 0.0833 | 0.0000 | 0.1667 | 0.0833 | 0.0833 |

### Tactic Level (`tactic_collapsed`)

| Fold | Test Episode | N | Coverage | Ceiling | Markov Hit@1 | Markov Hit@3 | Frequency Hit@1 | Frequency Hit@3 | Fallback Hit@1 | Fallback Hit@3 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| fold_e1 | E1 | 13 | 1.0000 | 1.0000 | 0.3846 | 0.7692 | 0.3846 | 0.7692 | 0.3846 | 0.7692 |
| fold_e2 | E2 | 15 | 0.9333 | 1.0000 | 0.3333 | 0.6000 | 0.0667 | 0.5333 | 0.4000 | 0.6667 |
| fold_e3 | E3 | 15 | 0.9333 | 0.8667 | 0.0667 | 0.4667 | 0.1333 | 0.4667 | 0.1333 | 0.5333 |
| fold_e4 | E4 | 10 | 1.0000 | 1.0000 | 0.2000 | 0.8000 | 0.1000 | 0.9000 | 0.2000 | 0.8000 |
| fold_e6 | E6 | 13 | 1.0000 | 1.0000 | 0.2308 | 0.6154 | 0.1538 | 0.4615 | 0.2308 | 0.6154 |
| fold_e7 | E7 | 8 | 1.0000 | 0.8750 | 0.2500 | 0.6250 | 0.2500 | 0.7500 | 0.2500 | 0.6250 |

---

## McNemar Paired Tests (Sensitivity Analysis)

| Comparison | N | Both Hit | Markov Only | Freq Only | Neither Hit | Markov Rate | Freq Rate | Difference | p-value (sensitivity, raw p) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| collapsed_full Hit@3 | 93 | 1 | 2 | 15 | 75 | 0.0323 | 0.1720 | -0.1398 | 0.0023 |
| tactic_collapsed Hit@3 | 74 | 35 | 12 | 11 | 16 | 0.6351 | 0.6216 | +0.0135 | 1.0000 |
| collapsed_full Hit@1 | 93 | 1 | 2 | 6 | 84 | 0.0323 | 0.0753 | -0.0430 | 0.2891 |
| tactic_collapsed Hit@1 | 74 | 4 | 14 | 9 | 47 | 0.2432 | 0.1757 | +0.0676 | 0.4049 |

