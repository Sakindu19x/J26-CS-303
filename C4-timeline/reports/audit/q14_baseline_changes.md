# Baseline Hash Changes Audit Register (Prompt 14)

Records all modifications to baseline files permitted under Prompt 14 allow-lists, with numeric-leaf equality proof.

## Baseline Change: `reports/7ep/exploratory_tactic_conditioned_report.md` (Q3, 2026-10-15T06:22:55Z)

- **Part**: Q3
- **Rationale**: Amendment 8 textual corrections: standardized verdict statement to pre-registered wording, corrected order-signal permutation p-values from difference to Markov tactic, withdrew cross-campaign claim, and added F3 unseen state rate
- **Baseline File**: `_baseline_hashes_7ep_inference.json`
- **Old SHA-256**: `2bfcd5966d91191a245633dec618c3a11b4c285eef16da89aa8291fb14fbdf18`
- **New SHA-256**: `358618de9d07e3ae319e72c2cc4551b3d686f6fe9b8cb6bbb267c50c7d49e125`
- **Numeric Leaves Extracted**: Old=156, New=161

| Metric | Old Value (HEAD) | New Value (Working Tree) | Status |
|:---|:---|:---|:---|
| Variant Top-1 Hits | 5 | 5 | IDENTICAL |
| Variant Top-3 Hits | 8 | 8 | IDENTICAL |
| Variant Top-1 Pooled Rate | 5.26% | 5.26% | IDENTICAL |
| Variant Top-3 Pooled Rate | 8.42% | 8.42% | IDENTICAL |
| Frequency Top-1 Hits | 7 | 7 | IDENTICAL |
| Frequency Top-3 Hits | 16 | 16 | IDENTICAL |
| Markov Top-1 Hits | 3 | 3 | IDENTICAL |
| Markov Top-3 Hits | 3 | 3 | IDENTICAL |
| Top-1 McNemar b/c | b=5, c=7 | b=5, c=7 | IDENTICAL |
| Top-1 McNemar p | p = 0.7744 | p = 0.7744 | IDENTICAL |
| Top-3 McNemar b/c | b=1, c=9 | b=1, c=9 | IDENTICAL |
| Top-3 McNemar p | p = 0.0574 | p = 0.0574 | IDENTICAL |
| E5-Removed Sample Size N | 93 | 93 | IDENTICAL |
| Primary Sample Size N | 95 | 95 | IDENTICAL |

## Baseline Change: `data/processed_7ep/prediction_records_loeo.jsonl` (Q7, 2026-10-15T06:42:00Z)

- **Part**: Q7
- **Rationale**: Prediction records Schema 1.1.0 update: candidate tactics, non-placeholder alternatives, support object with caution metrics
- **Baseline File**: `_baseline_hashes_7ep_inference.json`
- **Old SHA-256**: `9b68c7204d0d28cb9dd45c0df1c5541c330663449c7be193a34f4cd732602e05`
- **New SHA-256**: `373bc11b0b1a3a424bc650f0244b207289820375688dcea9d7d86148e3139421`
- **Numeric Leaves Extracted**: Old=11986, New=13435

| Metric | Old Value (HEAD) | New Value (Working Tree) | Status |
|:---|:---|:---|:---|
| Extracted Numeric Count | 11986 | 13435 | VERIFIED |

## Baseline Change: `reports/7ep/prediction_record_examples.md` (Q7, 2026-10-15T06:42:05Z)

- **Part**: Q7
- **Rationale**: Worked examples report updated for Schema 1.1.0: 7 distinct exemplars including single-episode, set-valued, and tactic-level
- **Baseline File**: `_baseline_hashes_7ep_inference.json`
- **Old SHA-256**: `759dd7c83594e8087e1a8c94eb49efccdf795bbb5185e380a0295774ecaf57f4`
- **New SHA-256**: `c3b05890c87390524c2027a8b2fe6f74be9ae64d1a85ae7d2d95f1654eb2a6c5`
- **Numeric Leaves Extracted**: Old=510, New=905

| Metric | Old Value (HEAD) | New Value (Working Tree) | Status |
|:---|:---|:---|:---|
| Extracted Numeric Count | 510 | 905 | VERIFIED |

## Baseline Change: `reports/7ep/requirements_trace.md` (Q4, 2026-10-15T07:04:26Z)

- **Part**: Q4
- **Rationale**: Rebuilt requirements trace matrix strictly from docs/proposal_requirements.json with fixed status enum and verified evidence
- **Baseline File**: `_baseline_hashes_7ep_inference.json`
- **Old SHA-256**: `4bf4fdfb544763fd6e632def9eb859faffb8429170071ab7e5fb7a69ab344870`
- **New SHA-256**: `af7dd4bcd84c16f3ef3e0f7754cfde54b29eeecc155bd1642f35dd814f6bc9d7`
- **Numeric Leaves Extracted**: Old=31, New=24

| Metric | Old Value (HEAD) | New Value (Working Tree) | Status |
|:---|:---|:---|:---|
| Extracted Numeric Count | 31 | 24 | VERIFIED |

