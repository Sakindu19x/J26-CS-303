# Component 4 Viva Examination Pack

> [!NOTE]
> This folder contains the complete, audit-verified evidence pack for the Component 4 MPhil viva examination.
> All numbers, tables, and figures are generated deterministically by `scripts/build_viva_pack.py` directly from
> verified JSON artifacts and tested against baseline hashes.

---

## Pack Contents & Document Index

| Document | Topic | Description |
|:---|:---|:---|
| [**01_dataset.md**](file:///viva_pack/01_dataset.md) | Dataset & Provenance | 7 CAM-LDS simulation archives, SHA-256 hashes, Zenodo record, Stage 1 extraction & normalization |
| [**02_split_and_training.md**](file:///viva_pack/02_split_and_training.md) | Data Splits & Training Protocol | LOEO 7-fold scheme, fold transition counts, model file hashes, deterministic frequency counting |
| [**03_scores.md**](file:///viva_pack/03_scores.md) | Empirical Performance Scores | Top-1/Top-3 accuracy, precision/recall/F1, reachability ceilings, and explicit documentation of missing metrics |
| [**04_worked_examples.md**](file:///viva_pack/04_worked_examples.md) | Forensic Prediction Records | Worked forensic records: first hit, first miss, first fallback, first unseen state, and tied case |
| [**05_figures/**](file:///viva_pack/05_figures/) | High-Resolution Figures | Empirical learning curve, A4 power curve, and LOEO cross-validation bar chart |
| [**06_claims_and_limits.md**](file:///viva_pack/06_claims_and_limits.md) | Scientific Claims & Limitations | Statistically demonstrated claims, Holm claim rule decisions, negative result rationale, and known boundaries |
| [**07_reproduce.md**](file:///viva_pack/07_reproduce.md) | Independent Reproduction Guide | One-command reproduction using `scripts/reproduce_all.py` (--verify-only and --rebuild) |

---
*Pack Version: 1.0.0 (October 2026)*
