# Baseline Change Register (Prompt 16 S1a Audit)

> [!IMPORTANT]
> **Rule G2 & Frozen Baseline Policy**: Protected baseline files remain byte-identical unless explicitly authorized.
> Every change records old and new SHA-256 (both as raw git blob and working tree checkout), compares all numeric leaves,
> asserts strict mathematical leaf invariants (`old = id + ch + rm` and `new = id + ch + ad`), and enforces that `VERIFIED`
> may be printed ONLY when `changed == 0`. Where an entry cannot satisfy these constraints, `FAIL` is printed.

---
## Baseline Change: `reports/7ep/exploratory_tactic_conditioned_report.md` (Q3)

- **Part**: `Q3`
- **Commit**: `4f8d0c889e` (Author Date: `2026-10-15T11:57:48+05:30`)
- **Parent Commit (Before Part)**: `3dab166ce9`
- **Rationale**: Amendment 8 corrections: standardized verdict statement, corrected permutation p-values from difference to Markov tactic, withdrew cross-campaign claim, and added F3 unseen state rate.
- **Old SHA-256 (Git Blob)**: `2bfcd5966d91191a245633dec618c3a11b4c285eef16da89aa8291fb14fbdf18`
- **Old SHA-256 (Working Tree)**: `N/A (not in working tree)` (File examined from historical git blob only.)
- **New SHA-256 (Git Blob)**: `cbe33f0355de2e65d2a32b4690f054d0a04da70dce39b1549fd248c2245c765a`
- **New SHA-256 (Working Tree)**: `358618de9d07e3ae319e72c2cc4551b3d686f6fe9b8cb6bbb267c50c7d49e125` (Hash difference measured by line endings: git blob is stored LF (4415 bytes) whereas working-tree checkout has 57 CRLF line breaks (4472 bytes).)
- **Invariant 1 (`old = identical + changed + removed`)**: `158 = 153 + 5 + 0` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `163 = 153 + 5 + 5` (**PASS**)
- **Verification Verdict**: **FAIL (5 changed leaves violate frozen baseline policy)**

### Technical Notes & Disclosures

- **Post Hoc Addition Disclosure**: The 5 added exploratory leaves (including `F3_unseen_state_rate` = 35.79%, 34/95 evaluation samples) were added post hoc after results were seen.
- **Recomputed Contingency Table**: Paired McNemar contingency numbers recomputed from `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv`: exact discordant pairs are $b=5, c=7$ (two-sided exact McNemar $p = 0.7744$).
- The earlier report draft had cited $b=3, c=11$ ($p=0.0574$) which corresponded to an exploratory subset slice, not the full N=95 technique set.

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 153 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 5 | CHANGED (POLICY VIOLATION) | Must be 0 for VERIFIED status |
| **Added Leaves** | 5 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 0 | NONE | Each justified by caller rationale |

### Changed Leaves (5 leaves: old -> new)

| # | Leaf Path / Key | Old Value | New Value |
|:---:|:---|:---:|:---:|
| 1 | `L9[tok_1] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `7` | `35.79%` |
| 2 | `L9[tok_2] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `0.0410` | `34` |
| 3 | `L9[tok_3] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `1` | `95` |
| 4 | `L9[tok_4] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `0.0390` | `7` |
| 5 | `L9[tok_5] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `3` | `0.0430` |

### Added Leaves (5 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L9[tok_6] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `1` | Added F3 unseen state rate (35.79%, 34/95) and Markov tactic permutation p-values (p=0.0060 raw, p=0.0180 Holm) added post hoc after results were seen. |
| 2 | `L9[tok_7] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `0.0060` | Added F3 unseen state rate (35.79%, 34/95) and Markov tactic permutation p-values (p=0.0060 raw, p=0.0180 Holm) added post hoc after results were seen. |
| 3 | `L9[tok_8] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `3` | Added F3 unseen state rate (35.79%, 34/95) and Markov tactic permutation p-values (p=0.0060 raw, p=0.0180 Holm) added post hoc after results were seen. |
| 4 | `L9[tok_9] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `0.0180` | Added F3 unseen state rate (35.79%, 34/95) and Markov tactic permutation p-values (p=0.0060 raw, p=0.0180 Holm) added post hoc after results were seen. |
| 5 | `L9[tok_10] in `- **Motivation**: Cross-episode diagnostics (`reports/7ep/di`` | `8` | Added F3 unseen state rate (35.79%, 34/95) and Markov tactic permutation p-values (p=0.0060 raw, p=0.0180 Holm) added post hoc after results were seen. |


---

## Baseline Change: `data/processed_7ep/prediction_records_loeo.jsonl` (Q7)

- **Part**: `Q7`
- **Commit**: `53a5f1548b` (Author Date: `2026-10-15T12:17:12+05:30`)
- **Parent Commit (Before Part)**: `4f8d0c889e`
- **Rationale**: Prediction records Schema 1.1.0 upgrade: support metrics, caution flags, candidate tactics, and empirical alternative counts.
- **Old SHA-256 (Git Blob)**: `9b68c7204d0d28cb9dd45c0df1c5541c330663449c7be193a34f4cd732602e05`
- **Old SHA-256 (Working Tree)**: `N/A (not in working tree)` (File examined from historical git blob only.)
- **New SHA-256 (Git Blob)**: `e4e440d0aaae61cdabe3242a35d80db29c33687a40378b3dfd4dbd738616018d`
- **New SHA-256 (Working Tree)**: `373bc11b0b1a3a424bc650f0244b207289820375688dcea9d7d86148e3139421` (Hash difference measured by line endings: git blob is stored LF (985911 bytes) whereas working-tree checkout has 171 CRLF line breaks (986082 bytes).)
- **Invariant 1 (`old = identical + changed + removed`)**: `6327 = 4486 + 1746 + 95` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `6574 = 4486 + 1746 + 342` (**PASS**)
- **Verification Verdict**: **FAIL (1746 changed leaves violate frozen baseline policy)**

### Technical Notes & Disclosures

- **Preservation of Core Ground Truth & Primary Predictions**: All 171 primary predictions, fold IDs, target sets, and top-3 hit flags are bit-identical.
- **Contract Alignment**: Upgraded from draft Schema 1.0.0 to finalized Schema 1.1.0 (`schemas/c4_prediction_record.schema.json`).

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 4486 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 1746 | CHANGED (POLICY VIOLATION) | Must be 0 for VERIFIED status |
| **Added Leaves** | 342 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 95 | REMOVED | Each justified by caller rationale |

### Changed Leaves (1746 leaves: old -> new)

| # | Leaf Path / Key | Old Value | New Value |
|:---:|:---|:---:|:---:|
| 1 | `line[2].technique_prediction.alternatives[0].denominator` | `1.0` | `77.0` |
| 2 | `line[2].technique_prediction.alternatives[0].numerator` | `0.0` | `3.0` |
| 3 | `line[2].technique_prediction.alternatives[0].supporting_episodes_count` | `0` | `3` |
| 4 | `line[2].technique_prediction.alternatives[1].denominator` | `1.0` | `77.0` |
| 5 | `line[2].technique_prediction.alternatives[1].numerator` | `0.0` | `2.3333333333333335` |
| 6 | `line[2].technique_prediction.alternatives[1].supporting_episodes_count` | `0` | `3` |
| 7 | `line[2].technique_prediction.alternatives[2].denominator` | `1.0` | `77.0` |
| 8 | `line[2].technique_prediction.alternatives[2].numerator` | `0.0` | `2.333333333333333` |
| 9 | `line[2].technique_prediction.alternatives[2].supporting_episodes_count` | `0` | `1` |
| 10 | `line[2].technique_prediction.alternatives[3].denominator` | `1.0` | `77.0` |
| 11 | `line[2].technique_prediction.alternatives[3].numerator` | `0.0` | `2.0` |
| 12 | `line[2].technique_prediction.alternatives[3].supporting_episodes_count` | `0` | `2` |
| 13 | `line[2].technique_prediction.alternatives[4].denominator` | `1.0` | `77.0` |
| 14 | `line[2].technique_prediction.alternatives[4].numerator` | `0.0` | `2.0` |
| 15 | `line[2].technique_prediction.alternatives[4].supporting_episodes_count` | `0` | `2` |
| 16 | `line[3].technique_prediction.alternatives[0].denominator` | `1.0` | `77.0` |
| 17 | `line[3].technique_prediction.alternatives[0].numerator` | `0.0` | `3.0` |
| 18 | `line[3].technique_prediction.alternatives[0].supporting_episodes_count` | `0` | `3` |
| 19 | `line[3].technique_prediction.alternatives[1].denominator` | `1.0` | `77.0` |
| 20 | `line[3].technique_prediction.alternatives[1].numerator` | `0.0` | `2.3333333333333335` |
| 21 | `line[3].technique_prediction.alternatives[1].supporting_episodes_count` | `0` | `3` |
| 22 | `line[3].technique_prediction.alternatives[2].denominator` | `1.0` | `77.0` |
| 23 | `line[3].technique_prediction.alternatives[2].numerator` | `0.0` | `2.333333333333333` |
| 24 | `line[3].technique_prediction.alternatives[2].supporting_episodes_count` | `0` | `1` |
| 25 | `line[3].technique_prediction.alternatives[3].denominator` | `1.0` | `77.0` |
| 26 | `line[3].technique_prediction.alternatives[3].numerator` | `0.0` | `2.0` |
| 27 | `line[3].technique_prediction.alternatives[3].supporting_episodes_count` | `0` | `2` |
| 28 | `line[3].technique_prediction.alternatives[4].denominator` | `1.0` | `77.0` |
| 29 | `line[3].technique_prediction.alternatives[4].numerator` | `0.0` | `2.0` |
| 30 | `line[3].technique_prediction.alternatives[4].supporting_episodes_count` | `0` | `2` |
| 31 | `line[5].technique_prediction.alternatives[0].denominator` | `1.0` | `4.583333333333333` |
| 32 | `line[5].technique_prediction.alternatives[0].numerator` | `0.0` | `0.5` |
| 33 | `line[5].technique_prediction.alternatives[0].supporting_episodes_count` | `0` | `1` |
| 34 | `line[5].technique_prediction.alternatives[1].denominator` | `1.0` | `4.583333333333333` |
| 35 | `line[5].technique_prediction.alternatives[1].numerator` | `0.0` | `0.5` |
| 36 | `line[5].technique_prediction.alternatives[1].supporting_episodes_count` | `0` | `1` |
| 37 | `line[5].technique_prediction.alternatives[2].denominator` | `1.0` | `4.583333333333333` |
| 38 | `line[5].technique_prediction.alternatives[2].numerator` | `0.0` | `0.5` |
| 39 | `line[5].technique_prediction.alternatives[2].supporting_episodes_count` | `0` | `1` |
| 40 | `line[5].technique_prediction.alternatives[3].denominator` | `1.0` | `4.583333333333333` |
| 41 | `line[5].technique_prediction.alternatives[3].numerator` | `0.0` | `0.5` |
| 42 | `line[5].technique_prediction.alternatives[3].supporting_episodes_count` | `0` | `1` |
| 43 | `line[5].technique_prediction.alternatives[4].denominator` | `1.0` | `4.583333333333333` |
| 44 | `line[5].technique_prediction.alternatives[4].numerator` | `0.0` | `0.3333333333333333` |
| 45 | `line[5].technique_prediction.alternatives[4].supporting_episodes_count` | `0` | `1` |
| 46 | `line[6].technique_prediction.alternatives[0].denominator` | `1.0` | `0.6666666666666666` |
| 47 | `line[6].technique_prediction.alternatives[0].numerator` | `0.0` | `0.16666666666666666` |
| 48 | `line[6].technique_prediction.alternatives[0].supporting_episodes_count` | `0` | `1` |
| 49 | `line[7].technique_prediction.alternatives[0].denominator` | `1.0` | `11.583333333333332` |
| 50 | `line[7].technique_prediction.alternatives[0].numerator` | `0.0` | `1.0` |
| ... | *(truncated: 1696 additional changed leaves)* | ... | ... |

### Added Leaves (342 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `line[0].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 2 | `line[0].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 3 | `line[1].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 4 | `line[1].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 5 | `line[2].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 6 | `line[2].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 7 | `line[3].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 8 | `line[3].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 9 | `line[4].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 10 | `line[4].technique_prediction.support.n_transitions_from_state` | `0.3333333333333333` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 11 | `line[5].technique_prediction.support.n_supporting_training_episodes` | `4` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 12 | `line[5].technique_prediction.support.n_transitions_from_state` | `6.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 13 | `line[6].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 14 | `line[6].technique_prediction.support.n_transitions_from_state` | `1.5` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 15 | `line[7].technique_prediction.support.n_supporting_training_episodes` | `4` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 16 | `line[7].technique_prediction.support.n_transitions_from_state` | `14.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 17 | `line[8].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 18 | `line[8].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 19 | `line[9].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 20 | `line[9].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 21 | `line[10].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 22 | `line[10].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 23 | `line[11].technique_prediction.support.n_supporting_training_episodes` | `4` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 24 | `line[11].technique_prediction.support.n_transitions_from_state` | `6.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 25 | `line[12].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 26 | `line[12].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 27 | `line[13].technique_prediction.support.n_supporting_training_episodes` | `2` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 28 | `line[13].technique_prediction.support.n_transitions_from_state` | `2.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 29 | `line[14].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 30 | `line[14].technique_prediction.support.n_transitions_from_state` | `1.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 31 | `line[15].technique_prediction.support.n_supporting_training_episodes` | `2` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 32 | `line[15].technique_prediction.support.n_transitions_from_state` | `2.5` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 33 | `line[16].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 34 | `line[16].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 35 | `line[17].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 36 | `line[17].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 37 | `line[18].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 38 | `line[18].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 39 | `line[19].technique_prediction.support.n_supporting_training_episodes` | `3` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 40 | `line[19].technique_prediction.support.n_transitions_from_state` | `2.6666666666666665` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 41 | `line[20].technique_prediction.support.n_supporting_training_episodes` | `4` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 42 | `line[20].technique_prediction.support.n_transitions_from_state` | `6.166666666666666` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 43 | `line[21].technique_prediction.support.n_supporting_training_episodes` | `0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 44 | `line[21].technique_prediction.support.n_transitions_from_state` | `0.0` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 45 | `line[22].technique_prediction.support.n_supporting_training_episodes` | `3` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 46 | `line[22].technique_prediction.support.n_transitions_from_state` | `2.0769230769230766` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 47 | `line[23].technique_prediction.support.n_supporting_training_episodes` | `2` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 48 | `line[23].technique_prediction.support.n_transitions_from_state` | `2.0769230769230766` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 49 | `line[24].technique_prediction.support.n_supporting_training_episodes` | `1` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| 50 | `line[24].technique_prediction.support.n_transitions_from_state` | `0.07692307692307693` | Schema 1.1.0 update: support metrics (n_supporting_training_episodes, n_transitions_from_state), caution flag for 92/171 records, candidate tactics, and empirical alternative counts. |
| ... | *(truncated: 292 additional added leaves)* | ... | ... |

### Removed Leaves (95 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `line[0].input.event_index` | `1` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 2 | `line[1].input.event_index` | `2` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 3 | `line[2].input.event_index` | `3` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 4 | `line[3].input.event_index` | `4` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 5 | `line[4].input.event_index` | `5` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 6 | `line[5].input.event_index` | `6` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 7 | `line[6].input.event_index` | `7` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 8 | `line[7].input.event_index` | `8` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 9 | `line[8].input.event_index` | `9` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 10 | `line[9].input.event_index` | `10` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 11 | `line[10].input.event_index` | `11` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 12 | `line[11].input.event_index` | `12` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 13 | `line[12].input.event_index` | `13` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 14 | `line[13].input.event_index` | `14` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 15 | `line[14].input.event_index` | `15` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 16 | `line[15].input.event_index` | `16` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 17 | `line[16].input.event_index` | `17` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 18 | `line[17].input.event_index` | `18` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 19 | `line[18].input.event_index` | `1` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 20 | `line[19].input.event_index` | `2` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 21 | `line[20].input.event_index` | `3` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 22 | `line[21].input.event_index` | `4` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 23 | `line[22].input.event_index` | `5` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 24 | `line[23].input.event_index` | `6` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 25 | `line[24].input.event_index` | `7` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 26 | `line[25].input.event_index` | `8` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 27 | `line[26].input.event_index` | `9` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 28 | `line[27].input.event_index` | `10` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 29 | `line[28].input.event_index` | `11` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 30 | `line[29].input.event_index` | `12` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 31 | `line[30].input.event_index` | `13` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 32 | `line[31].input.event_index` | `14` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 33 | `line[32].input.event_index` | `15` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 34 | `line[33].input.event_index` | `16` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 35 | `line[34].input.event_index` | `17` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 36 | `line[35].input.event_index` | `18` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 37 | `line[36].input.event_index` | `19` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 38 | `line[37].input.event_index` | `1` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 39 | `line[38].input.event_index` | `2` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 40 | `line[39].input.event_index` | `3` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 41 | `line[40].input.event_index` | `4` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 42 | `line[41].input.event_index` | `5` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 43 | `line[42].input.event_index` | `6` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 44 | `line[43].input.event_index` | `7` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 45 | `line[44].input.event_index` | `8` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 46 | `line[45].input.event_index` | `9` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 47 | `line[46].input.event_index` | `10` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 48 | `line[47].input.event_index` | `11` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 49 | `line[48].input.event_index` | `12` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| 50 | `line[49].input.event_index` | `13` | Dummy uncalibrated probability tokens removed and replaced with empirical transition frequencies. |
| ... | *(truncated: 45 additional removed leaves)* | ... | ... |


---

## Baseline Change: `reports/7ep/prediction_record_examples.md` (Q7)

- **Part**: `Q7`
- **Commit**: `53a5f1548b` (Author Date: `2026-10-15T12:17:12+05:30`)
- **Parent Commit (Before Part)**: `4f8d0c889e`
- **Rationale**: Worked examples report updated for Schema 1.1.0 with 7 distinct exemplars and caution annotations.
- **Old SHA-256 (Git Blob)**: `759dd7c83594e8087e1a8c94eb49efccdf795bbb5185e380a0295774ecaf57f4`
- **Old SHA-256 (Working Tree)**: `N/A (not in working tree)` (File examined from historical git blob only.)
- **New SHA-256 (Git Blob)**: `9f36b249a1bea7ec559709bf82a9128cba8fab5f716952a85e81ce5846013088`
- **New SHA-256 (Working Tree)**: `6becdc124ffac4434a2e9a12498445d4bf519986608f8b73b463f7f8ca076c2c` (Hash difference measured by line endings: git blob is stored LF (64552 bytes) whereas working-tree checkout has 1638 CRLF line breaks (66742 bytes).)
- **Invariant 1 (`old = identical + changed + removed`)**: `544 = 5 + 0 + 539` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `952 = 5 + 0 + 947` (**PASS**)
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- Verified against live records by `scripts/verify_prediction_records.py`.

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 5 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 947 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 539 | REMOVED | Each justified by caller rationale |

### Added Leaves (947 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L1[tok_0] in `# Explainable Prediction Record Worked Examples (7 Episodes,`` | `7` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 2 | `L1[tok_1] in `# Explainable Prediction Record Worked Examples (7 Episodes,`` | `1.1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 3 | `L1[tok_2] in `# Explainable Prediction Record Worked Examples (7 Episodes,`` | `0` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 4 | `L6[tok_0] in `> Every record conforms to `schemas/c4_prediction_record.sch`` | `1.1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 5 | `L6[tok_1] in `> Every record conforms to `schemas/c4_prediction_record.sch`` | `0` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 6 | `L13[tok_0] in `- **Total Prediction Records**: 171 (95 technique, 76 tactic`` | `171` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 7 | `L13[tok_1] in `- **Total Prediction Records**: 171 (95 technique, 76 tactic`` | `95` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 8 | `L13[tok_2] in `- **Total Prediction Records**: 171 (95 technique, 76 tactic`` | `76` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 9 | `L14[tok_0] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `92` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 10 | `L14[tok_1] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `171` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 11 | `L14[tok_2] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `83` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 12 | `L14[tok_3] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `95` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 13 | `L14[tok_4] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `9` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 14 | `L14[tok_5] in `- **Cautioned Records**: 92/171 (83/95 technique records, 9/`` | `76` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 15 | `L15[tok_0] in `- **Caution Threshold Policy**: A prediction record is flagg`` | `2` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 16 | `L15[tok_1] in `- **Caution Threshold Policy**: A prediction record is flagg`` | `3` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 17 | `L15[tok_2] in `- **Caution Threshold Policy**: A prediction record is flagg`` | `34` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 18 | `L18[tok_0] in `## Summary of Exemplars (7 Distinct Sample IDs)`` | `7` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 19 | `L20[tok_0] in `| Exemplar Category | Sample ID | Episode | Level | Status |`` | `1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 20 | `L20[tok_1] in `| Exemplar Category | Sample ID | Episode | Level | Status |`` | `1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 21 | `L22[tok_0] in `| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | `` | `1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 22 | `L22[tok_1] in `| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | `` | `0.4815` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 23 | `L23[tok_0] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `2` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 24 | `L23[tok_1] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `002` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 25 | `L23[tok_2] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `1.0000` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 26 | `L24[tok_0] in `| 3. Frequency Fallback (Unseen State) | `E1-col-ful-K03` | `` | `3` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 27 | `L24[tok_1] in `| 3. Frequency Fallback (Unseen State) | `E1-col-ful-K03` | `` | `0.0714` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 28 | `L25[tok_0] in `| 4. Tied Rank Boundary | `E1-col-ful-K02` | E1 | technique `` | `4` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 29 | `L25[tok_1] in `| 4. Tied Rank Boundary | `E1-col-ful-K02` | E1 | technique `` | `001` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 30 | `L25[tok_2] in `| 4. Tied Rank Boundary | `E1-col-ful-K02` | E1 | technique `` | `0.5000` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 31 | `L26[tok_0] in `| 5. Tactic-Level Prediction | `E1-tac-col-K01` | E1 | tacti`` | `5` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 32 | `L26[tok_1] in `| 5. Tactic-Level Prediction | `E1-tac-col-K01` | E1 | tacti`` | `0.5000` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 33 | `L27[tok_0] in `| 6. Single-Episode Support State | `E1-col-ful-K05` | E1 | `` | `6` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 34 | `L27[tok_1] in `| 6. Single-Episode Support State | `E1-col-ful-K05` | E1 | `` | `1.0000` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 35 | `L28[tok_0] in `| 7. Set-Valued State | `E1-col-ful-K08` | E1 | technique | `` | `7` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 36 | `L28[tok_1] in `| 7. Set-Valued State | `E1-col-ful-K08` | E1 | technique | `` | `0.2083` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 37 | `L30[tok_0] in `## Exemplar: 1. First Hit (`E2-col-ful-K05`)`` | `1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 38 | `L33[tok_0] in `- **Record ID**: `27251c1aabbbcc25ac635333954a24ab164b2f4fd6`` | `27251` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 39 | `L36[tok_0] in `- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76`` | `256` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 40 | `L36[tok_1] in `- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76`` | `3823` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 41 | `L37[tok_0] in `- **Input Events SHA-256**: `c0d116b9f5e9f000b2aa4a660bebfe4`` | `256` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 42 | `L38[tok_0] in `- **Record SHA-256**: `5490301c6d6a8abdb6898c01f6afe15f9a6d7`` | `256` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 43 | `L38[tok_1] in `- **Record SHA-256**: `5490301c6d6a8abdb6898c01f6afe15f9a6d7`` | `5490301` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 44 | `L41[tok_0] in `- **Support Metrics**: Supporting Episodes=3, Transitions fr`` | `3` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 45 | `L41[tok_1] in `- **Support Metrics**: Supporting Episodes=3, Transitions fr`` | `2.08` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 46 | `L42[tok_0] in `- **Caution Text**: Caution: low historical support (observe`` | `3` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 47 | `L42[tok_1] in `- **Caution Text**: Caution: low historical support (observe`` | `2.1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 48 | `L42[tok_2] in `- **Caution Text**: Caution: low historical support (observe`` | `2` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 49 | `L42[tok_3] in `- **Caution Text**: Caution: low historical support (observe`` | `3` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| 50 | `L48[tok_0] in `| 1 | `T1057` | Process Discovery | 0.4815 | `transition_pro`` | `1` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |
| ... | *(truncated: 897 additional added leaves)* | ... | ... |

### Removed Leaves (539 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L1[tok_0] in `# Explainable Prediction Record Worked Examples (7 Episodes)`` | `7` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 2 | `L13[tok_0] in `| Exemplar Type | Sample ID | Episode | Level | Status | Top`` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 3 | `L13[tok_1] in `| Exemplar Type | Sample ID | Episode | Level | Status | Top`` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 4 | `L15[tok_0] in `| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | `` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 5 | `L15[tok_1] in `| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | `` | `0.4815` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 6 | `L16[tok_0] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `2` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 7 | `L16[tok_1] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `002` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 8 | `L16[tok_2] in `| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` |`` | `1.0000` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 9 | `L17[tok_0] in `| 3. First Fallback | `E1-col-ful-K03` | E1 | technique | `f`` | `3` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 10 | `L17[tok_1] in `| 3. First Fallback | `E1-col-ful-K03` | E1 | technique | `f`` | `0.0714` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 11 | `L18[tok_0] in `| 4. First Unseen State | `E1-col-ful-K03` | E1 | technique `` | `4` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 12 | `L18[tok_1] in `| 4. First Unseen State | `E1-col-ful-K03` | E1 | technique `` | `0.0714` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 13 | `L19[tok_0] in `| 5. First Tied Boundary | `E1-col-ful-K02` | E1 | technique`` | `5` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 14 | `L19[tok_1] in `| 5. First Tied Boundary | `E1-col-ful-K02` | E1 | technique`` | `001` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 15 | `L19[tok_2] in `| 5. First Tied Boundary | `E1-col-ful-K02` | E1 | technique`` | `0.5000` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 16 | `L21[tok_0] in `## Exemplar: 1. First Hit (`E2-col-ful-K05`)`` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 17 | `L26[tok_0] in `- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76`` | `256` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 18 | `L26[tok_1] in `- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76`` | `3823` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 19 | `L27[tok_0] in `- **Input Events SHA-256**: `c0d116b9f5e9f000b2aa4a660bebfe4`` | `256` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 20 | `L28[tok_0] in `- **Record SHA-256**: `0384175ad1ff253d80ae1fd8b639c85235855`` | `256` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 21 | `L28[tok_1] in `- **Record SHA-256**: `0384175ad1ff253d80ae1fd8b639c85235855`` | `0384175` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 22 | `L36[tok_0] in `| 1 | `T1057` | None | 0.4815 | `transition_probability` | 1`` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 23 | `L36[tok_1] in `| 1 | `T1057` | None | 0.4815 | `transition_probability` | 1`` | `0.4815` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 24 | `L36[tok_2] in `| 1 | `T1057` | None | 0.4815 | `transition_probability` | 1`` | `1.00` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 25 | `L36[tok_3] in `| 1 | `T1057` | None | 0.4815 | `transition_probability` | 1`` | `2.08` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 26 | `L37[tok_0] in `| 2 | `T1059.004` | None | 0.4815 | `transition_probability``` | `2` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 27 | `L37[tok_1] in `| 2 | `T1059.004` | None | 0.4815 | `transition_probability``` | `004` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 28 | `L37[tok_2] in `| 2 | `T1059.004` | None | 0.4815 | `transition_probability``` | `0.4815` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 29 | `L37[tok_3] in `| 2 | `T1059.004` | None | 0.4815 | `transition_probability``` | `1.00` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 30 | `L37[tok_4] in `| 2 | `T1059.004` | None | 0.4815 | `transition_probability``` | `2.08` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 31 | `L38[tok_0] in `| 3 | `T1033` | None | 0.0370 | `transition_probability` | 0`` | `3` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 32 | `L38[tok_1] in `| 3 | `T1033` | None | 0.0370 | `transition_probability` | 0`` | `0.0370` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 33 | `L38[tok_2] in `| 3 | `T1033` | None | 0.0370 | `transition_probability` | 0`` | `0.08` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 34 | `L38[tok_3] in `| 3 | `T1033` | None | 0.0370 | `transition_probability` | 0`` | `2.08` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 35 | `L42[tok_0] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `0.4815` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 36 | `L42[tok_1] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `1.00` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 37 | `L42[tok_2] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `2.08` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 38 | `L42[tok_3] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `1` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 39 | `L42[tok_4] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `004` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 40 | `L42[tok_5] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `95` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 41 | `L42[tok_6] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `3` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 42 | `L42[tok_7] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `3.16%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 43 | `L42[tok_8] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `1.08%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 44 | `L42[tok_9] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `8.88%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 45 | `L42[tok_10] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `16.84%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 46 | `L42[tok_11] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `10.64%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 47 | `L42[tok_12] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `25.62%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 48 | `L42[tok_13] in `> State [T1083] recognized in training episodes (E1, E3, E4,`` | `64.21%` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 49 | `L66[tok_0] in `"event_index": 5,`` | `5` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| 50 | `L68[tok_0] in `"last_timestamp": "2025-10-01T10:16:01.232391+00:00",`` | `2025` | Old 3-exemplar draft replaced by comprehensive 7-exemplar verified worked examples. |
| ... | *(truncated: 489 additional removed leaves)* | ... | ... |


---

## Baseline Change: `reports/7ep/requirements_trace.md` (Q4)

- **Part**: `Q4`
- **Commit**: `4fc004bd15` (Author Date: `2026-10-15T12:37:04+05:30`)
- **Parent Commit (Before Part)**: `cf6e5dbd88`
- **Rationale**: Rebuilt requirements trace strictly from proposal requirements JSON with standardized status enum.
- **Old SHA-256 (Git Blob)**: `4bf4fdfb544763fd6e632def9eb859faffb8429170071ab7e5fb7a69ab344870`
- **Old SHA-256 (Working Tree)**: `N/A (not in working tree)` (File examined from historical git blob only.)
- **New SHA-256 (Git Blob)**: `cebee90b4905acaea8904dcba51e3043dd696236f1a2ead50496445a5b46ede1`
- **New SHA-256 (Working Tree)**: `fa4c437c50b54f92724c589daa5076ed5a5795c35d47af505c5f8c9bea4c8576` (Hash difference measured by line endings: git blob is stored LF (7334 bytes) whereas working-tree checkout has 31 CRLF line breaks (7476 bytes).)
- **Invariant 1 (`old = identical + changed + removed`)**: `38 = 0 + 0 + 38` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `31 = 0 + 0 + 31` (**PASS**)
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- Rebuilt strictly from `docs/proposal_requirements.json` using exact proposal wording.
- Enforced valid enum values (`IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_DEMONSTRATED_ON_DATASET`, `PARTIAL`, `NOT_TESTABLE_UNTIL_C3`, `PENDING_HUMAN_EVIDENCE`).

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 0 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 31 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 38 | REMOVED | Each justified by caller rationale |

### Added Leaves (31 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L1[tok_0] in `# Requirements Traceability Matrix (Prompt 14 Q4 Rebuild)`` | `14` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 2 | `L14[tok_0] in `| **FR1** | Attack Timeline Reconstruction | `src/c4/timelin`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 3 | `L15[tok_0] in `| **FR2** | Attack Episode Separation | `src/c4/episodes.py``` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 4 | `L16[tok_0] in `| **FR3** | ATT&CK Sequence Representation | `src/c4/attack_`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 5 | `L17[tok_0] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 6 | `L17[tok_1] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 7 | `L17[tok_2] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `95` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 8 | `L17[tok_3] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `76` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 9 | `L17[tok_4] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `1` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 10 | `L17[tok_5] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `3` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 11 | `L17[tok_6] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `95` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 12 | `L17[tok_7] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 13 | `L17[tok_8] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `95` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 14 | `L18[tok_0] in `| **FR5** | Probability Output | `src/c4/prediction_record.p`` | `1.0` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 15 | `L19[tok_0] in `| **FR6** | Alternative Predictions | `src/c4/prediction_rec`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 16 | `L19[tok_1] in `| **FR6** | Alternative Predictions | `src/c4/prediction_rec`` | `4` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 17 | `L20[tok_0] in `| **FR7** | Explainable Prediction | `src/c4/prediction_reco`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 18 | `L20[tok_1] in `| **FR7** | Explainable Prediction | `src/c4/prediction_reco`` | `92` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 19 | `L20[tok_2] in `| **FR7** | Explainable Prediction | `src/c4/prediction_reco`` | `171` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 20 | `L21[tok_0] in `| **FR8** | Context Integration (C3 information) | `src/c4/c`` | `3` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 21 | `L22[tok_0] in `| **FR9** | Incident Information Display | `src/c4/dashboard`` | `171` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 22 | `L23[tok_0] in `| **NFR1** | Performance ("acceptable response time", the pr`` | `2.00` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 23 | `L23[tok_1] in `| **NFR1** | Performance ("acceptable response time", the pr`` | `5.00` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 24 | `L23[tok_2] in `| **NFR1** | Performance ("acceptable response time", the pr`` | `10.00` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 25 | `L24[tok_0] in `| **NFR2** | Reliability (consistent predictions) | `src/c4/`` | `100%` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 26 | `L24[tok_1] in `| **NFR2** | Reliability (consistent predictions) | `src/c4/`` | `0` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 27 | `L24[tok_2] in `| **NFR2** | Reliability (consistent predictions) | `src/c4/`` | `1` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 28 | `L24[tok_3] in `| **NFR2** | Reliability (consistent predictions) | `src/c4/`` | `4242` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 29 | `L24[tok_4] in `| **NFR2** | Reliability (consistent predictions) | `src/c4/`` | `256` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 30 | `L25[tok_0] in `| **NFR3** | Security (shall not modify original event recor`` | `256` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |
| 31 | `L28[tok_0] in `| **NFR6** | Explainability | `src/c4/prediction_record.py`,`` | `7` | Proposal requirement IDs FR1-FR9 and NFR1-NFR6 keyed strictly on canonical proposal wording. |

### Removed Leaves (38 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L1[tok_0] in `# Component 4 Requirements Traceability Matrix`` | `4` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 2 | `L4[tok_0] in `> **SYSTEM REQUIREMENTS VERIFICATION AUDIT (G-P5-6)**`` | `6` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 3 | `L5[tok_0] in `> Generated on: 2026-10-15T00:00:00Z`` | `2026` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 4 | `L5[tok_1] in `> Generated on: 2026-10-15T00:00:00Z`` | `10` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 5 | `L5[tok_2] in `> Generated on: 2026-10-15T00:00:00Z`` | `15` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 6 | `L5[tok_3] in `> Generated on: 2026-10-15T00:00:00Z`` | `00` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 7 | `L5[tok_4] in `> Generated on: 2026-10-15T00:00:00Z`` | `00` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 8 | `L10[tok_0] in `## 1. Functional Requirements Matrix (FR1 - FR9)`` | `1` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 9 | `L24[tok_0] in `## 2. Non-Functional Requirements Matrix (NFR1 - NFR6)`` | `2` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 10 | `L28[tok_0] in `| **NFR1** | Performance and Execution Latency | Median <= 2`` | `2.0` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 11 | `L28[tok_1] in `| **NFR1** | Performance and Execution Latency | Median <= 2`` | `5.0` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 12 | `L28[tok_2] in `| **NFR1** | Performance and Execution Latency | Median <= 2`` | `10` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 13 | `L31[tok_0] in `| **NFR4** | Usability and Interpretability for Analysts | C`` | `7` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 14 | `L35[tok_0] in `## 3. Requirement Details and Trace Notes`` | `3` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 15 | `L45[tok_0] in `- **Audit Notes**: Ingests 274 events across 7 episodes with`` | `274` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 16 | `L45[tok_1] in `- **Audit Notes**: Ingests 274 events across 7 episodes with`` | `7` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 17 | `L65[tok_0] in `- **Audit Notes**: Maps 100% of labeled techniques to offici`` | `100%` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 18 | `L75[tok_0] in `- **Audit Notes**: Top-k candidates and order equal evaluati`` | `1` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 19 | `L85[tok_0] in `- **Audit Notes**: Transition weights independently recounte`` | `1` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 20 | `L85[tok_1] in `- **Audit Notes**: Transition weights independently recounte`` | `9` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 21 | `L85[tok_2] in `- **Audit Notes**: Transition weights independently recounte`` | `2` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 22 | `L95[tok_0] in `- **Audit Notes**: Surfaces ranks 4..k alternatives, boundar`` | `4` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 23 | `L105[tok_0] in `- **Audit Notes**: Fallback labeled as training_frequency_sh`` | `95%` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 24 | `L130[tok_0] in `- **Scope**: Median <= 2.0s, P95 <= 5.0s warm; <= 10s cold s`` | `2.0` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 25 | `L130[tok_1] in `- **Scope**: Median <= 2.0s, P95 <= 5.0s warm; <= 10s cold s`` | `5.0` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 26 | `L130[tok_2] in `- **Scope**: Median <= 2.0s, P95 <= 5.0s warm; <= 10s cold s`` | `10` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 27 | `L135[tok_0] in `- **Audit Notes**: Execution timing benchmarked across 7 epi`` | `7` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 28 | `L135[tok_1] in `- **Audit Notes**: Execution timing benchmarked across 7 epi`` | `30` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 29 | `L145[tok_0] in `- **Audit Notes**: Gate G-P5-3: byte-identical JSONL across `` | `3` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 30 | `L145[tok_1] in `- **Audit Notes**: Gate G-P5-3: byte-identical JSONL across `` | `0` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 31 | `L145[tok_2] in `- **Audit Notes**: Gate G-P5-3: byte-identical JSONL across `` | `1` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 32 | `L145[tok_3] in `- **Audit Notes**: Gate G-P5-3: byte-identical JSONL across `` | `4242` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 33 | `L155[tok_0] in `- **Audit Notes**: Gate G-P5-4: deep-frozen inputs non-modif`` | `4` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 34 | `L161[tok_0] in `- **Implementation**: `docs/analyst_feedback_form.md`, `repo`` | `7` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 35 | `L165[tok_0] in `- **Audit Notes**: Exemplars report and 8-question feedback `` | `8` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 36 | `L185[tok_0] in `- **Audit Notes**: Gate G-P5-5: 100% of prediction records v`` | `5` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 37 | `L185[tok_1] in `- **Audit Notes**: Gate G-P5-5: 100% of prediction records v`` | `100%` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |
| 38 | `L185[tok_2] in `- **Audit Notes**: Gate G-P5-5: 100% of prediction records v`` | `07` | Redundant manual table row numbering tokens removed; keyed on canonical proposal IDs. |


---

## Baseline Change: `reports/7ep/requirements_trace.md` (R3)

- **Part**: `R3`
- **Commit**: `c6efee4343` (Author Date: `2026-10-15T15:44:40+05:30`)
- **Parent Commit (Before Part)**: `fff7595a78`
- **Rationale**: Updated requirements trace: FR2 demonstrated on dataset, NFR5 partial, Hit@3 pre-registered limits, and module grep test validation rule.
- **Old SHA-256 (Git Blob)**: `cebee90b4905acaea8904dcba51e3043dd696236f1a2ead50496445a5b46ede1`
- **Old SHA-256 (Working Tree)**: `N/A (not in working tree)` (File examined from historical git blob only.)
- **New SHA-256 (Git Blob)**: `c55da33731cb265917249842266c4577277fa6a07372427a8b0608f88aeb7678`
- **New SHA-256 (Working Tree)**: `fa4c437c50b54f92724c589daa5076ed5a5795c35d47af505c5f8c9bea4c8576` (Hash difference measured by line endings: git blob is stored LF (7445 bytes) whereas working-tree checkout has 31 CRLF line breaks (7476 bytes).)
- **Invariant 1 (`old = identical + changed + removed`)**: `31 = 29 + 2 + 0` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `38 = 29 + 2 + 7` (**PASS**)
- **Verification Verdict**: **FAIL (2 changed leaves violate frozen baseline policy)**

### Technical Notes & Disclosures

- FR2 updated to IMPLEMENTED_DEMONSTRATED_ON_DATASET.
- NFR5 updated to PARTIAL (adapter format proposed by C4, contract not agreed by C3).
- FR4 limits cite pre-registered primary Hit@3 endpoints instead of descriptive Hit@1.

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 29 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 2 | CHANGED (POLICY VIOLATION) | Must be 0 for VERIFIED status |
| **Added Leaves** | 7 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 0 | NONE | Each justified by caller rationale |

### Changed Leaves (2 leaves: old -> new)

| # | Leaf Path / Key | Old Value | New Value |
|:---:|:---|:---:|:---:|
| 1 | `L17[tok_4] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `1` | `3` |
| 2 | `L17[tok_7] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `7` | `16` |

### Added Leaves (7 leaves)

| # | Leaf Path / Key | Value | Caller Rationale |
|:---:|:---|:---:|:---|
| 1 | `L17[tok_9] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `0.0094` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 2 | `L17[tok_10] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `3` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 3 | `L17[tok_11] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `48` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 4 | `L17[tok_12] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `76` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 5 | `L17[tok_13] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `48` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 6 | `L17[tok_14] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `76` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |
| 7 | `L17[tok_15] in `| **FR4** | Next-Technique Prediction (First-Order Markov) |`` | `1.0000` | Hit@3 limits for P1 (48/76, p=1.0000) and P2 (3/95 vs 16/95, p=0.0094) cited directly from evaluation_7ep_results.json and holm_claim_rule_results.json. |

