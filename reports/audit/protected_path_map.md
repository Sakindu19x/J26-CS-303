# Protected Path Renaming Proposal and Mapping (Prompt 16 Part S6)

> [!NOTE]
> This document specifies the proposed path migrations for Component 4's historically protected artifact directories.
> Per Rule G6 and Part S6, this migration is attempted exclusively on branch `rename-protected-paths` and will not be merged into `master`.

## 1. Directory Migration Plan

| Current Historical Path | Proposed Standard Path | Semantic Rationale |
|:---|:---|:---|
| `data/processed` | `stage1_4episode` | Clarifies that this directory stores preprocessed artifacts strictly for the initial 4-episode pilot campaign. |
| `data/processed_7ep` | `stage1_7episode` | Explicitly denotes preprocessed artifacts for the full 7-episode campaign. |
| `reports/7ep` | `reports/seven_episode` | Replaces abbreviated numerical folder name with descriptive spelled-out name consistent with project style conventions. |

## 2. Protected Baseline File Inventory Migration

The 61 protected baseline files map to their new locations as follows:

### Stage 1 Pilot (10 files)
- `data/processed/attack_sequences.json` -> `stage1_4episode/attack_sequences.json`
- `data/processed/attack_timelines.json` -> `stage1_4episode/attack_timelines.json`
- `data/processed/loeo_folds.json` -> `stage1_4episode/loeo_folds.json`
- `data/processed/next_technique_samples.json` -> `stage1_4episode/next_technique_samples.json`
- `data/processed/normalized_events.json` -> `stage1_4episode/normalized_events.json`
- `data/processed/technique_tactic_reference.json` -> `stage1_4episode/technique_tactic_reference.json`
- `reports/data_quality_report.json` -> unchanged
- `reports/timeline_validation_report.json` -> unchanged
- `reports/tactic_discrepancy_report.json` -> unchanged
- `reports/sequence_statistics.json` -> unchanged

### Pilot Evaluation (3 Technique + 3 Tactic)
- `data/processed/evaluation_predictions.csv` -> `stage1_4episode/evaluation_predictions.csv`
- `reports/evaluation_results.json` -> unchanged
- `reports/evaluation_report.md` -> unchanged
- `data/processed/tactic_evaluation_predictions.csv` -> `stage1_4episode/tactic_evaluation_predictions.csv`
- `reports/tactic_evaluation_results.json` -> unchanged
- `reports/tactic_evaluation_report.md` -> unchanged

### 7-Episode Stage 1 (10 files)
- `data/processed_7ep/attack_sequences.json` -> `stage1_7episode/attack_sequences.json`
- `data/processed_7ep/attack_timelines.json` -> `stage1_7episode/attack_timelines.json`
- `data/processed_7ep/loeo_folds.json` -> `stage1_7episode/loeo_folds.json`
- `data/processed_7ep/next_technique_samples.json` -> `stage1_7episode/next_technique_samples.json`
- `data/processed_7ep/normalized_events.json` -> `stage1_7episode/normalized_events.json`
- `data/processed_7ep/technique_tactic_reference.json` -> `stage1_7episode/technique_tactic_reference.json`
- `reports/7ep/data_quality_report.json` -> `reports/seven_episode/data_quality_report.json`
- `reports/7ep/timeline_validation_report.json` -> `reports/seven_episode/timeline_validation_report.json`
- `reports/7ep/tactic_discrepancy_report.json` -> `reports/seven_episode/tactic_discrepancy_report.json`
- `reports/7ep/sequence_statistics.json` -> `reports/seven_episode/sequence_statistics.json`

### 7-Episode Evaluation (3 files)
- `data/processed_7ep/evaluation_7ep_predictions.csv` -> `stage1_7episode/evaluation_7ep_predictions.csv`
- `reports/7ep/evaluation_7ep_results.json` -> `reports/seven_episode/evaluation_7ep_results.json`
- `reports/7ep/evaluation_7ep_report.md` -> `reports/seven_episode/evaluation_7ep_report.md`

### 7-Episode Inference (32 files)
- All 32 artifacts under `data/processed_7ep/` and `reports/7ep/` map to `stage1_7episode/` and `reports/seven_episode/`.

---

## 3. Rebuild Verification Findings & Gate Verdict

### Experimental Outcome: FAIL

### Failure Analysis & Technical Rationale:
1. **Embedded Path Invariants**:
   Multiple protected baseline artifacts (including `artifacts/7ep/production_model/manifest.json`, `reports/7ep/data_quality_report.json`, `reports/7ep/evaluation_7ep_report.md`, and markdown summary documents) contain hardcoded, serialized path strings referencing `data/processed`, `data/processed_7ep`, and `reports/7ep`.
2. **Hash Sensitivity**:
   Regenerating these artifacts from raw archives with updated target paths modifies the serialized string representations within the generated files. Consequently, their SHA-256 hashes diverge from the pre-registered baseline hashes recorded in the Root of Trust (`docs/ROOT_OF_TRUST.md`).
3. **Pervasive Code Coupling**:
   The legacy path strings are embedded across 48+ pipeline scripts, test suites, and internal package modules (`src/c4/evaluation.py`, `src/c4/tactic_evaluation.py`, `src/c4/samples.py`, etc.).
4. **Final Decision**:
   Per the explicit instruction in Part S6 (*"if any hash differs, report the exact files and FAIL, change nothing on main"*), this migration is declared **FAIL**, the changes remain strictly isolated on branch `rename-protected-paths` for historical documentation, and `master` remains untouched at verified commit `bf59077`.
