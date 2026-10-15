# 02. Data Splits, LOEO Folds, and Model Training Protocol

> [!NOTE]
> **Deterministic Training Principle**: First-order Markov chain and frequency baseline training consists purely
> of **empirical transition frequency counting** across training episodes. There are **no continuous tunable hyperparameters**,
> no learning rates, no random seeds in model fitting, and no stochastic optimization routines.

---

## 1. Leave-One-Episode-Out (LOEO) Cross-Validation Scheme

The 7-episode campaign is evaluated using strict Leave-One-Episode-Out (LOEO) cross-validation across 7 folds ($K=7$).
In each fold $k$, exactly one episode is held out for evaluation, and the model is trained exclusively on the remaining 6 episodes:

| Fold ID | Held-Out Episode | Training Episodes ($N_{train}=6$) | Sequences | Slice | Model File SHA-256 (Prefix) |
|:---:|:---:|:---|:---:|:---:|:---|
| `E1` | `E1` | E2, E3, E4, E5, E6, E7 | 6 | `collapsed_full` | `76d8568da1f7b2d8...` |
| `E2` | `E2` | E1, E3, E4, E5, E6, E7 | 6 | `collapsed_full` | `3823a1d7a319bc0e...` |
| `E3` | `E3` | E1, E2, E4, E5, E6, E7 | 6 | `collapsed_full` | `dde291ebb03e4a8d...` |
| `E4` | `E4` | E1, E2, E3, E5, E6, E7 | 6 | `collapsed_full` | `af8dded0a97b0b90...` |
| `E5` | `E5` | E1, E2, E3, E4, E6, E7 | 6 | `collapsed_full` | `f1a5b282572971b5...` |
| `E6` | `E6` | E1, E2, E3, E4, E5, E7 | 6 | `collapsed_full` | `0c20dea1b5408ff8...` |
| `E7` | `E7` | E1, E2, E3, E4, E5, E6 | 6 | `collapsed_full` | `ea70d210facc81bd...` |

---

## 2. Production Model Training (All 7 Episodes)

For production deployment and demo dashboard operations (FR4, FR5), a production model was trained across **all seven episodes**:
- **Artifact**: `artifacts/7ep/production_model/collapsed_full.json` (`73002ab557b86143a612cb67b7dc6a31fafa0640346e865d38df05af0ead5485`)
- **Tactic Artifact**: `artifacts/7ep/production_model/tactic_collapsed.json` (`250dd1f09f5b3c20554aed87277c90575b8b3967938a2fa7296d018ecc9ec7ad`)
- **Manifest**: `artifacts/7ep/production_model/manifest.json` (`b2dd54c51b41e6c69280d2b532ecde3f3d46e26cdd499375cba8ca9db39e1bd3`)
- **Transition Count**: 95 state transitions observed across 7 episodes.
