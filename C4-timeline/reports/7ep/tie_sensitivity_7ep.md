# Post Hoc Tie-Sensitivity Diagnostic Report (7 Episodes)

> [!NOTE]
> **Status**: post hoc sensitivity bounds, not pre-registered tests; the pre-registered verdict is unchanged.

## 1. Number of Tied Samples at Top-1 and Top-3 Decision Boundaries

Two candidate scores are defined as tied if their model-assigned prediction probabilities differ by less than $10^{-9}$.
Scores cannot be recomputed from the CSV alone and are computed from the saved fold models.

| Run | Slice | Model | Total N | Top-1 Tied Count | Top-1 Tied Rate | Top-3 Boundary Tied Count | Top-3 Boundary Tied Rate |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| 7ep | `collapsed_full` | `markov` | 95 | 25 | 0.2632 | 22 | 0.2316 |
| 7ep | `collapsed_full` | `frequency` | 95 | 0 | 0.0000 | 51 | 0.5368 |
| 7ep | `collapsed_full` | `markov_fallback` | 95 | 25 | 0.2632 | 39 | 0.4105 |
| 7ep | `tactic_collapsed` | `markov` | 76 | 2 | 0.0263 | 5 | 0.0658 |
| 7ep | `tactic_collapsed` | `frequency` | 76 | 0 | 0.0000 | 0 | 0.0000 |
| 7ep | `tactic_collapsed` | `markov_fallback` | 76 | 2 | 0.0263 | 5 | 0.0658 |
| e5_removed | `collapsed_full` | `markov` | 93 | 25 | 0.2688 | 22 | 0.2366 |
| e5_removed | `collapsed_full` | `frequency` | 93 | 0 | 0.0000 | 51 | 0.5484 |
| e5_removed | `collapsed_full` | `markov_fallback` | 93 | 25 | 0.2688 | 39 | 0.4194 |
| e5_removed | `tactic_collapsed` | `markov` | 74 | 8 | 0.1081 | 5 | 0.0676 |
| e5_removed | `tactic_collapsed` | `frequency` | 74 | 0 | 0.0000 | 0 | 0.0000 |
| e5_removed | `tactic_collapsed` | `markov_fallback` | 74 | 8 | 0.1081 | 5 | 0.0676 |

---

## 2. Observed vs Expected vs Best vs Worst Hit Rates

Expected Hit rates are computed under exact uniform random tie-breaking. Best and worst cases place all available tied target items strictly ahead of or behind non-targets.

### 2.1 Pooled Aggregation Across Evaluated Transitions

| Run | Slice | Model | N | Observed Hit@1 | Expected Hit@1 | Best Hit@1 | Worst Hit@1 | Observed Hit@3 | Expected Hit@3 | Best Hit@3 | Worst Hit@3 |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 7ep | `collapsed_full` | `markov` | 95 | 0.0316 | 0.0211 | 0.0316 | 0.0105 | 0.0316 | 0.0316 | 0.0316 | 0.0316 |
| 7ep | `collapsed_full` | `frequency` | 95 | 0.0737 | 0.0737 | 0.0737 | 0.0737 | 0.1684 | 0.1544 | 0.1684 | 0.1368 |
| 7ep | `collapsed_full` | `markov_fallback` | 95 | 0.0316 | 0.0211 | 0.0316 | 0.0105 | 0.0421 | 0.0421 | 0.0421 | 0.0421 |
| 7ep | `tactic_collapsed` | `markov` | 76 | 0.2895 | 0.2961 | 0.3026 | 0.2895 | 0.6316 | 0.6368 | 0.6447 | 0.6316 |
| 7ep | `tactic_collapsed` | `frequency` | 76 | 0.1842 | 0.1842 | 0.1842 | 0.1842 | 0.6316 | 0.6316 | 0.6316 | 0.6316 |
| 7ep | `tactic_collapsed` | `markov_fallback` | 76 | 0.3158 | 0.3224 | 0.3289 | 0.3158 | 0.6579 | 0.6632 | 0.6711 | 0.6579 |
| e5_removed | `collapsed_full` | `markov` | 93 | 0.0323 | 0.0215 | 0.0323 | 0.0108 | 0.0323 | 0.0323 | 0.0323 | 0.0323 |
| e5_removed | `collapsed_full` | `frequency` | 93 | 0.0753 | 0.0753 | 0.0753 | 0.0753 | 0.1720 | 0.1577 | 0.1720 | 0.1398 |
| e5_removed | `collapsed_full` | `markov_fallback` | 93 | 0.0323 | 0.0215 | 0.0323 | 0.0108 | 0.0430 | 0.0430 | 0.0430 | 0.0430 |
| e5_removed | `tactic_collapsed` | `markov` | 74 | 0.2432 | 0.2680 | 0.3108 | 0.2297 | 0.6351 | 0.6405 | 0.6486 | 0.6351 |
| e5_removed | `tactic_collapsed` | `frequency` | 74 | 0.1757 | 0.1757 | 0.1757 | 0.1757 | 0.6216 | 0.6216 | 0.6216 | 0.6216 |
| e5_removed | `tactic_collapsed` | `markov_fallback` | 74 | 0.2703 | 0.2950 | 0.3378 | 0.2568 | 0.6622 | 0.6676 | 0.6757 | 0.6622 |

### 2.2 Episode-Mean Aggregation Across Folds

| Run | Slice | Model | Observed Hit@1 | Expected Hit@1 | Best Hit@1 | Worst Hit@1 | Observed Hit@3 | Expected Hit@3 | Best Hit@3 | Worst Hit@3 |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 7ep | `collapsed_full` | `markov` | 0.0337 | 0.0240 | 0.0337 | 0.0143 | 0.0337 | 0.0337 | 0.0337 | 0.0337 |
| 7ep | `collapsed_full` | `frequency` | 0.0595 | 0.0595 | 0.0595 | 0.0595 | 0.1448 | 0.1347 | 0.1448 | 0.1218 |
| 7ep | `collapsed_full` | `markov_fallback` | 0.0337 | 0.0240 | 0.0337 | 0.0143 | 0.0439 | 0.0439 | 0.0439 | 0.0439 |
| 7ep | `tactic_collapsed` | `markov` | 0.3093 | 0.3183 | 0.3272 | 0.3093 | 0.6252 | 0.6296 | 0.6362 | 0.6252 |
| 7ep | `tactic_collapsed` | `frequency` | 0.2269 | 0.2269 | 0.2269 | 0.2269 | 0.6973 | 0.6973 | 0.6973 | 0.6973 |
| 7ep | `tactic_collapsed` | `markov_fallback` | 0.3284 | 0.3373 | 0.3462 | 0.3284 | 0.6442 | 0.6486 | 0.6552 | 0.6442 |
| e5_removed | `collapsed_full` | `markov` | 0.0393 | 0.0280 | 0.0393 | 0.0167 | 0.0393 | 0.0393 | 0.0393 | 0.0393 |
| e5_removed | `collapsed_full` | `frequency` | 0.0694 | 0.0694 | 0.0694 | 0.0694 | 0.1690 | 0.1571 | 0.1690 | 0.1421 |
| e5_removed | `collapsed_full` | `markov_fallback` | 0.0393 | 0.0280 | 0.0393 | 0.0167 | 0.0512 | 0.0512 | 0.0512 | 0.0512 |
| e5_removed | `tactic_collapsed` | `markov` | 0.2442 | 0.2695 | 0.3095 | 0.2331 | 0.6460 | 0.6512 | 0.6589 | 0.6460 |
| e5_removed | `tactic_collapsed` | `frequency` | 0.1814 | 0.1814 | 0.1814 | 0.1814 | 0.6468 | 0.6468 | 0.6468 | 0.6468 |
| e5_removed | `tactic_collapsed` | `markov_fallback` | 0.2665 | 0.2917 | 0.3317 | 0.2553 | 0.6683 | 0.6734 | 0.6811 | 0.6683 |

---

## 3. Diagnostic 7-Sample List with Model Probability Score Vectors

The 7 samples whose Markov top-1 prediction or Hit@1 changed between the 7-episode run and the E5-removed run in folds E1–E4, E6, E7:

| Sample ID | Test Ep | Current Tactics | Target Tactics | 7-Ep Tied? | 7-Ep Top-1 Group Size | No-E5 Tied? | No-E5 Top-1 Group Size |
|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|
| E2-tac-col-K05 | E2 | credential-access | discovery | False | 1 | True | 2 |
| E2-tac-col-K07 | E2 | credential-access, exfiltration | collection | False | 1 | True | 2 |
| E2-tac-col-K08 | E2 | collection | exfiltration | False | 1 | True | 2 |
| E2-tac-col-K11 | E2 | collection | discovery | False | 1 | True | 2 |
| E2-tac-col-K13 | E2 | credential-access | discovery | False | 1 | True | 2 |
| E3-tac-col-K01 | E3 | credential-access, lateral-movement | lateral-movement | False | 1 | False | 1 |
| E3-tac-col-K04 | E3 | collection | discovery | False | 1 | True | 3 |

### Score Vectors for the 7 Diagnostic Samples

- **E2-tac-col-K05** (E2):
  - 7-Episode Score Vector: `{collection: 0.242915, credential-access: 0.060729, defense-evasion: 0.161943, discovery: 0.283401, lateral-movement: 0.182186, persistence: 0.020243, reconnaissance: 0.048583}`
  - No-E5 Score Vector: `{collection: 0.304569, credential-access: 0.025381, defense-evasion: 0.126904, discovery: 0.304569, lateral-movement: 0.152284, persistence: 0.025381, reconnaissance: 0.060914}`
- **E2-tac-col-K07** (E2):
  - 7-Episode Score Vector: `{collection: 0.242915, credential-access: 0.060729, defense-evasion: 0.161943, discovery: 0.283401, lateral-movement: 0.182186, persistence: 0.020243, reconnaissance: 0.048583}`
  - No-E5 Score Vector: `{collection: 0.304569, credential-access: 0.025381, defense-evasion: 0.126904, discovery: 0.304569, lateral-movement: 0.152284, persistence: 0.025381, reconnaissance: 0.060914}`
- **E2-tac-col-K08** (E2):
  - 7-Episode Score Vector: `{credential-access: 0.071429, defense-evasion: 0.428571, discovery: 0.5}`
  - No-E5 Score Vector: `{defense-evasion: 0.5, discovery: 0.5}`
- **E2-tac-col-K11** (E2):
  - 7-Episode Score Vector: `{credential-access: 0.071429, defense-evasion: 0.428571, discovery: 0.5}`
  - No-E5 Score Vector: `{defense-evasion: 0.5, discovery: 0.5}`
- **E2-tac-col-K13** (E2):
  - 7-Episode Score Vector: `{collection: 0.242915, credential-access: 0.060729, defense-evasion: 0.161943, discovery: 0.283401, lateral-movement: 0.182186, persistence: 0.020243, reconnaissance: 0.048583}`
  - No-E5 Score Vector: `{collection: 0.304569, credential-access: 0.025381, defense-evasion: 0.126904, discovery: 0.304569, lateral-movement: 0.152284, persistence: 0.025381, reconnaissance: 0.060914}`
- **E3-tac-col-K01** (E3):
  - 7-Episode Score Vector: `{collection: 0.04886, command-and-control: 0.416667, credential-access: 0.02443, defense-evasion: 0.065147, discovery: 0.39278, lateral-movement: 0.02443, persistence: 0.008143, reconnaissance: 0.019544}`
  - No-E5 Score Vector: `{collection: 0.058366, command-and-control: 0.416667, credential-access: 0.009728, defense-evasion: 0.048638, discovery: 0.433528, persistence: 0.009728, reconnaissance: 0.023346}`
- **E3-tac-col-K04** (E3):
  - 7-Episode Score Vector: `{credential-access: 0.05, defense-evasion: 0.3, discovery: 0.35, exfiltration: 0.3}`
  - No-E5 Score Vector: `{defense-evasion: 0.333333, discovery: 0.333333, exfiltration: 0.333333}`

---

## 4. 7-Episode minus E5-Removed Difference at Observed and Expected Values

For tactic Hit@1 (pooled over evaluated transitions):

| Model | 7-Ep Observed | No-E5 Observed | Observed Difference | 7-Ep Expected | No-E5 Expected | Expected Difference |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `markov` | 0.2895 | 0.2432 | +0.0462 | 0.2961 | 0.2680 | +0.0280 |
| `frequency` | 0.1842 | 0.1757 | +0.0085 | 0.1842 | 0.1757 | +0.0085 |

---

## 5. Bounds on Pre-Registered Conclusions under Extreme Tie Resolutions

- **Bound A (Ties resolved in Markov's favour)**: Markov assigned best-case hits, Frequency assigned worst-case hits.
- **Bound B (Ties resolved in Frequency's favour)**: Markov assigned worst-case hits, Frequency assigned best-case hits.

| Bound Condition | P1 Tactic Hit@3 (b/c) | P1 Raw p | P1 Holm p | P2 Tech Hit@3 (b/c) | P2 Raw p | P2 Holm p | Pre-Registered Claim Rule Verdict |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Bound A (Markov favoured) | 13 / 12 | 1.0000 | 1.0000 | 2 / 12 | 0.0129 | 0.0388 | **not demonstrated** |
| Bound B (Frequency favoured) | 12 / 12 | 1.0000 | 1.0000 | 2 / 15 | 0.0023 | 0.0094 | **not demonstrated** |

> [!IMPORTANT]
> Under both extreme tie-resolution bounds (A and B), the pre-registered claim-rule verdict remains strictly **not demonstrated**.
> All text is generated deterministically by code without causal prose.

