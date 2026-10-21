# Read-Only Diagnostics Report (7 Episodes)

> [!NOTE]
> **Diagnostic Label**: diagnostic, not a pre-registered test. No new models, no parameter tuning.

---

## Diagnostic F1: Candidate List Distribution & Rank of Correct Target

Evaluated exclusively on samples where Markov status is `ok` (conditioning state observed in training):

| Slice | N (Markov ok) | Model | 1 Cand | 2 Cands | 3 Cands | ≥4 Cands | Target Intersects Full List | First Correct Mean Rank |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| Technique (collapsed_full) | 61 | Markov | 16 | 15 | 6 | 24 | 4/61 (0.0656) | 2.25 |
| | | Frequency | 0 | 0 | 0 | 61 | 39/61 (0.6393) | 18.13 |
| Tactic (tactic_collapsed) | 74 | Markov | 0 | 3 | 3 | 68 | 64/74 (0.8649) | 2.56 |
| | | Frequency | 0 | 0 | 0 | 74 | 71/74 (0.9595) | 3.42 |
| Technique (raw_full) | 83 | Markov | 16 | 15 | 16 | 36 | 16/83 (0.1928) | 1.44 |
| | | Frequency | 0 | 0 | 0 | 83 | 61/83 (0.7349) | 18.39 |

### First Correct Candidate Rank Distribution (when target is in full candidate list)

#### Technique (collapsed_full)
- **Markov Rank Counts**: `{1: 3, 6: 1}`
- **Frequency Rank Counts**: `{1: 7, 2: 2, 3: 6, 7: 1, 8: 1, 10: 1, 11: 1, 15: 1, 16: 1, 18: 2, 19: 1, 20: 1, 22: 2, 24: 2, 26: 3, 34: 1, 41: 1, 45: 1, 50: 1, 64: 2, 68: 1}`

#### Tactic (tactic_collapsed)
- **Markov Rank Counts**: `{1: 22, 2: 22, 3: 4, 4: 9, 5: 1, 6: 1, 7: 2, 8: 2, 9: 1}`
- **Frequency Rank Counts**: `{1: 12, 2: 28, 3: 6, 4: 7, 5: 8, 7: 4, 8: 2, 10: 2, 12: 1, 13: 1}`

#### Technique (raw_full)
- **Markov Rank Counts**: `{1: 14, 2: 1, 7: 1}`
- **Frequency Rank Counts**: `{1: 1, 2: 7, 3: 3, 4: 9, 7: 3, 8: 1, 9: 2, 10: 2, 12: 2, 14: 2, 16: 2, 18: 1, 20: 2, 23: 1, 24: 6, 25: 1, 27: 2, 28: 1, 30: 2, 31: 3, 37: 1, 47: 1, 48: 2, 50: 1, 64: 2, 68: 1}`

---

## Diagnostic F2: Raw Sequence Self-Repeat Analysis (`raw_full`)

- **Total Samples in `raw_full`**: 131
- **Self-Repeat Samples (`target == current`)**: 36 out of 131 (0.2748 of all samples).
- **Total Markov Hit@1 Hits in `raw_full`**: 14 hits (0.1069).
- **Markov Hit@1 Hits on Self-Repeats**: 11 out of 14 total hits (0.7857 of hits occurred on self-repeats).
- **Performance Restricted to Non-Self-Repeat Targets ($N=95$)**:
  - **Markov Hit@1**: 3/95 (0.0316)
  - **Frequency Hit@1**: 1/95 (0.0105)

---

## Diagnostic F3: Unseen Current Conditioning States & Share of Misses

### Technique Level (`collapsed_full`, $N=95$)

| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| E1 | 18 | 5 | 0.2778 | 18 | 5 | 0.2778 |
| E2 | 19 | 6 | 0.3158 | 18 | 6 | 0.3333 |
| E3 | 20 | 10 | 0.5000 | 20 | 10 | 0.5000 |
| E4 | 10 | 4 | 0.4000 | 9 | 4 | 0.4444 |
| E5 | 2 | 2 | 1.0000 | 2 | 2 | 1.0000 |
| E6 | 14 | 6 | 0.4286 | 14 | 6 | 0.4286 |
| E7 | 12 | 1 | 0.0833 | 11 | 1 | 0.0909 |
| **Pooled Total** | **95** | **34** | **0.3579** | **92** | **34** | **0.3696** |

### Tactic Level (`tactic_collapsed`, $N=76$)

| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| E1 | 13 | 0 | 0.0000 | 3 | 0 | 0.0000 |
| E2 | 15 | 1 | 0.0667 | 6 | 1 | 0.1667 |
| E3 | 15 | 1 | 0.0667 | 8 | 1 | 0.1250 |
| E4 | 10 | 0 | 0.0000 | 2 | 0 | 0.0000 |
| E5 | 2 | 0 | 0.0000 | 1 | 0 | 0.0000 |
| E6 | 13 | 0 | 0.0000 | 5 | 0 | 0.0000 |
| E7 | 8 | 0 | 0.0000 | 3 | 0 | 0.0000 |
| **Pooled Total** | **76** | **2** | **0.0263** | **28** | **2** | **0.0714** |

### Reference Slice (`raw_full`, $N=131$)

| Held-Out Episode | Total Samples | Unseen Current States | Unseen State Rate | Total Markov Hit@3 Misses | Unseen State Hit@3 Misses | Share of Hit@3 Misses from Unseen States |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| E1 | 26 | 6 | 0.2308 | 20 | 6 | 0.3000 |
| E2 | 20 | 6 | 0.3000 | 19 | 6 | 0.3158 |
| E3 | 28 | 13 | 0.4643 | 23 | 13 | 0.5652 |
| E4 | 21 | 13 | 0.6190 | 19 | 13 | 0.6842 |
| E5 | 2 | 2 | 1.0000 | 2 | 2 | 1.0000 |
| E6 | 22 | 7 | 0.3182 | 22 | 7 | 0.3182 |
| E7 | 12 | 1 | 0.0833 | 11 | 1 | 0.0909 |
| **Pooled Total** | **131** | **48** | **0.3664** | **116** | **48** | **0.4138** |

