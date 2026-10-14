# E5-Removed Tactic Hit@1 Change Diagnostic

> [!NOTE]
> **Status**: diagnostic, not a pre-registered test.

## 1. Accounting Summary

- **Tactic 7-Episode Baseline**: Markov Hit@1 is 22 / 76 (0.2895).
- **E5 Test Sample Performance in 7-Episode LOEO**: 1 / 2 hits.
- **Performance on Remaining Folds (E1–E4, E6, E7, N=74)**:
  - In 7-episode run (E5 in training pool): 21 / 74 hits (0.2838).
  - In E5-removed run (E5 absent from training pool): 18 / 74 hits (0.2432).
  - Net difference in other folds: -3 hits.
- **Frequency Baseline Comparison on Remaining Folds (N=74)**:
  - In 7-episode run: 13 / 74 hits (0.1757).
  - In E5-removed run: 13 / 74 hits (0.1757).
  - Net difference in Frequency hits: +0 hits.

---

## 2. Markov Model Differing Samples

Total samples with differing Markov top-1 prediction or Hit@1: **7**.

| Sample ID | Test Episode | Current Tactics | Target Tactics | 7-Ep Top-1 | 7-Ep Hit@1 | No-E5 Top-1 | No-E5 Hit@1 | 7-Ep Transition Counts | 7-Ep Tied | No-E5 Transition Counts | No-E5 Tied |
|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---|:---:|
| E2-tac-col-K05 | E2 | credential-access | discovery | discovery | 1 | collection | 0 | `{collection: 1.0, credential-access: 0.25, defense-evasion: 0.6667, discovery: 1.1667, lateral-movement: 0.75, persistence: 0.0833, reconnaissance: 0.2}` | tied counts: no | `{collection: 1.0, credential-access: 0.0833, defense-evasion: 0.4167, discovery: 1.0, lateral-movement: 0.5, persistence: 0.0833, reconnaissance: 0.2}` | tied counts: yes |
| E2-tac-col-K07 | E2 | credential-access, exfiltration | collection | discovery | 0 | collection | 1 | `{credential-access->collection: 1.0, credential-access->credential-access: 0.25, credential-access->defense-evasion: 0.6667, credential-access->discovery: 1.1667, credential-access->lateral-movement: 0.75, credential-access->persistence: 0.0833, credential-access->reconnaissance: 0.2}` | tied counts: no | `{credential-access->collection: 1.0, credential-access->credential-access: 0.0833, credential-access->defense-evasion: 0.4167, credential-access->discovery: 1.0, credential-access->lateral-movement: 0.5, credential-access->persistence: 0.0833, credential-access->reconnaissance: 0.2}` | tied counts: yes |
| E2-tac-col-K08 | E2 | collection | exfiltration | discovery | 0 | defense-evasion | 0 | `{credential-access: 0.1667, defense-evasion: 1.0, discovery: 1.1667}` | tied counts: no | `{defense-evasion: 1.0, discovery: 1.0}` | tied counts: yes |
| E2-tac-col-K11 | E2 | collection | discovery | discovery | 1 | defense-evasion | 0 | `{credential-access: 0.1667, defense-evasion: 1.0, discovery: 1.1667}` | tied counts: no | `{defense-evasion: 1.0, discovery: 1.0}` | tied counts: yes |
| E2-tac-col-K13 | E2 | credential-access | discovery | discovery | 1 | collection | 0 | `{collection: 1.0, credential-access: 0.25, defense-evasion: 0.6667, discovery: 1.1667, lateral-movement: 0.75, persistence: 0.0833, reconnaissance: 0.2}` | tied counts: no | `{collection: 1.0, credential-access: 0.0833, defense-evasion: 0.4167, discovery: 1.0, lateral-movement: 0.5, persistence: 0.0833, reconnaissance: 0.2}` | tied counts: yes |
| E3-tac-col-K01 | E3 | credential-access, lateral-movement | lateral-movement | command-and-control | 0 | discovery | 0 | `{credential-access->collection: 0.5, credential-access->credential-access: 0.25, credential-access->defense-evasion: 0.6667, credential-access->discovery: 3.1667, credential-access->lateral-movement: 0.25, credential-access->persistence: 0.0833, credential-access->reconnaissance: 0.2, lateral-movement->command-and-control: 1.0, lateral-movement->discovery: 0.2}` | tied counts: no | `{credential-access->collection: 0.5, credential-access->credential-access: 0.0833, credential-access->defense-evasion: 0.4167, credential-access->discovery: 3.0, credential-access->persistence: 0.0833, credential-access->reconnaissance: 0.2, lateral-movement->command-and-control: 1.0, lateral-movement->discovery: 0.2}` | tied counts: no |
| E3-tac-col-K04 | E3 | collection | discovery | discovery | 1 | defense-evasion | 0 | `{credential-access: 0.1667, defense-evasion: 1.0, discovery: 1.1667, exfiltration: 1.0}` | tied counts: no | `{defense-evasion: 1.0, discovery: 1.0, exfiltration: 1.0}` | tied counts: yes |

---

## 3. Frequency Baseline Differing Samples

Total samples with differing Frequency top-1 prediction or Hit@1: **0**.

No evaluation samples in folds E1–E4, E6, or E7 exhibited differing top-1 predictions or Hit@1 flags for the Frequency baseline between the 7-episode run and the E5-removed run.

