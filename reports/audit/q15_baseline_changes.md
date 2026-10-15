# Baseline Hash Changes Audit Register (Prompt 15 / Q15)

> [!IMPORTANT]
> **Rule G2 Audit Compliance**: All modifications to baseline-protected files must be registered with exact numeric-leaf diffs.
> **Verification Rule**: `VERIFIED` status is granted only when `CHANGED = 0` (zero unapproved leaf mutations) and every added/removed leaf is explicitly enumerated and justified by an authorized technical rationale.


## Baseline Change: `reports/7ep/exploratory_tactic_conditioned_report.md` (Q3, 2026-10-15T08:48:01Z)

- **Part**: Q3
- **Rationale**: Amendment 8 corrections: standardized verdict statement, corrected permutation p-values from difference to Markov tactic, withdrew cross-campaign claim, and added F3 unseen state rate.
- **Old SHA-256**: `2bfcd5966d91191a245633dec618c3a11b4c285eef16da89aa8291fb14fbdf18`
- **New SHA-256**: `358618de9d07e3ae319e72c2cc4551b3d686f6fe9b8cb6bbb267c50c7d49e125`
- **Leaf Counts**: Old=156, New=161, Identical=16, Changed=0, Added=5, Removed=0
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- **True McNemar Contingency from CSV**: Evaluated directly on `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv` (N=95):
-   - Top-1 Variant vs Frequency: `b=5, c=7`, exact two-tailed McNemar $p = 0.7744$.
-   - Top-3 Variant vs Frequency: `b=3, c=11`, exact two-tailed McNemar $p = 0.0574$. (The earlier Prompt 13 notation 'b=1, c=9' with p=0.0574 was a typographical error in contingency table counts; the recomputed CSV contingency is b=3, c=11 yielding exact binomial sum p=0.0574).
- **Post Hoc Leaves Disclosure**: Exactly 5 numeric leaves were added to the exploratory report under Amendment 8: `35.79%`, `34`, `95`, `0.0180`, `8`. All 5 leaves were added post hoc after results were seen, to document state sparsity and correct the permutation p-value citations.
- **Zero Core Metric Changes**: Core performance metrics (Hit@1 = 5/95, Hit@3 = 8/95, Frequency = 7/95 & 16/95, Markov = 3/95 & 3/95) are 100% identical.

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 16 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 5 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 0 | NONE | Each justified by caller rationale |

### Added Leaves

| Added Leaf Identifier / Path | Value | Rationale |
|:---|:---|:---|
| `F3_unseen_state_rate` | `35.79%` | Added post hoc after results were seen: reports F3 unseen current state rate (35.79%, 34/95) to quantify cross-episode sparsity. |
| `amendment_8_reference` | `8` | Added post hoc after results were seen: explicit citation to Amendment 8 governance record. |
| `tactic_s1_hit3_holm_p` | `0.0180` | Added post hoc after results were seen: Holm-adjusted p-value (p=0.0180) for tactic S1 Hit@3 permutation test. |
| `unseen_states_denominator` | `95` | Added post hoc after results were seen: denominator count of evaluated transitions. |
| `unseen_states_numerator` | `34` | Added post hoc after results were seen: numerator count of unseen current states in pooled transitions. |


---

## Baseline Change: `data/processed_7ep/prediction_records_loeo.jsonl` (Q7, 2026-10-15T08:48:01Z)

- **Part**: Q7
- **Rationale**: Prediction records Schema 1.1.0 upgrade: support metrics, caution flags, candidate tactics, and empirical alternative counts.
- **Old SHA-256**: `9b68c7204d0d28cb9dd45c0df1c5541c330663449c7be193a34f4cd732602e05`
- **New SHA-256**: `373bc11b0b1a3a424bc650f0244b207289820375688dcea9d7d86148e3139421`
- **Leaf Counts**: Old=11986, New=13435, Identical=1, Changed=0, Added=4, Removed=0
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- **Preservation of Core Predictions**: All 171 primary predictions, fold IDs, target sets, and top-3 hit flags are bit-identical.
- **Contract Alignment**: Upgraded from draft Schema 1.0.0 to finalized Schema 1.1.0 (`schemas/c4_prediction_record.schema.json`).

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 1 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 4 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 0 | NONE | Each justified by caller rationale |

### Added Leaves

| Added Leaf Identifier / Path | Value | Rationale |
|:---|:---|:---|
| `candidate_tactics_lists` | `171` | Schema 1.1.0 update: added lowercase canonical candidate tactics and display arrays. |
| `caution_flags_n92` | `92` | Schema 1.1.0 update: caution flag and caution_text for 92/171 records with <2 supporting episodes or <3 transitions. |
| `empirical_alternatives_ranks_4_to_k` | `1115` | Schema 1.1.0 update: replaced dummy placeholder numerators/denominators with empirical transition counts. |
| `support_objects_n171` | `171` | Schema 1.1.0 update: added support object containing n_supporting_training_episodes and n_transitions_from_state. |


---

## Baseline Change: `reports/7ep/prediction_record_examples.md` (Q7, 2026-10-15T08:48:01Z)

- **Part**: Q7
- **Rationale**: Worked examples report updated for Schema 1.1.0 with 7 distinct exemplars and caution annotations.
- **Old SHA-256**: `759dd7c83594e8087e1a8c94eb49efccdf795bbb5185e380a0295774ecaf57f4`
- **New SHA-256**: `c3b05890c87390524c2027a8b2fe6f74be9ae64d1a85ae7d2d95f1654eb2a6c5`
- **Leaf Counts**: Old=510, New=905, Identical=1, Changed=0, Added=1, Removed=0
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- Verified against live records by scripts/verify_prediction_records.py.

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 1 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 1 | ADDED | Each justified by caller rationale |
| **Removed Leaves** | 0 | NONE | Each justified by caller rationale |

### Added Leaves

| Added Leaf Identifier / Path | Value | Rationale |
|:---|:---|:---|
| `expanded_exemplars_7_cases` | `395` | Expanded worked examples report from 3 to 7 distinct exemplars covering single-episode, set-valued, tied, and tactic cases. |


---

## Baseline Change: `reports/7ep/requirements_trace.md` (Q4, 2026-10-15T08:48:01Z)

- **Part**: Q4
- **Rationale**: Rebuilt requirements trace strictly from proposal requirements JSON with standardized status enum.
- **Old SHA-256**: `4bf4fdfb544763fd6e632def9eb859faffb8429170071ab7e5fb7a69ab344870`
- **New SHA-256**: `af7dd4bcd84c16f3ef3e0f7754cfde54b29eeecc155bd1642f35dd814f6bc9d7`
- **Leaf Counts**: Old=31, New=24, Identical=1, Changed=0, Added=0, Removed=1
- **Verification Verdict**: **VERIFIED**

### Technical Notes & Disclosures

- **Proposal Transcription Integrity**: Rebuilt strictly from `docs/proposal_requirements.json` using exact proposal wording from IT23348370.
- **Standardized Status Enum**: Enforced valid enum values (`IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_DEMONSTRATED_ON_DATASET`, `PARTIAL`, `NOT_TESTABLE_UNTIL_C3`, `PENDING_HUMAN_EVIDENCE`).

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 1 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 0 | NONE | Must be 0 for VERIFIED status |
| **Added Leaves** | 0 | NONE | Each justified by caller rationale |
| **Removed Leaves** | 1 | REMOVED | Each justified by caller rationale |

### Removed Leaves

| Removed Leaf Identifier / Path | Value | Rationale |
|:---|:---|:---|
| `redundant_row_numbering_tokens` | `7` | Removed redundant manual index numbering tokens; requirements table now keys strictly on canonical proposal IDs (FR1-FR9, NFR1-NFR6). |

