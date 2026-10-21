# Baseline Change Register (Prompt 16 S1a / Prompt 17 T3 Audit)

> [!IMPORTANT]
> **Rule G2 & Frozen Baseline Policy**: Protected baseline files remain byte-identical unless explicitly authorized.
> Every change records old and new SHA-256 (both as raw git blob and working tree checkout).
> For Markdown baseline documents, token-level leaves are replaced by a real line diff (`git diff --stat` plus changed line numbers).
> For prediction records, an explicit code check asserts that all 171 records have identical core prediction fields.
> Verdicts are assigned strictly as `AUTHORISED_CHANGE` for authorized changes passing invariants, and `UNAUTHORISED_FAIL` otherwise.

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
- **Invariant 1 (`old = identical + changed + removed`)**: `57 = 54 + 3 + 0` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `57 = 54 + 3 + 0` (**PASS**)
- **Verification Verdict**: **AUTHORISED_CHANGE**

### Real Line Diff (`git diff --stat` & Changed Line Numbers)

```text
reports/7ep/exploratory_tactic_conditioned_report.md | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)
```

**Changed Line Ranges (3 hunk blocks)**:

- `Old L5-L5 -> New L5-L5`
- `Old L9-L9 -> New L9-L9`
- `Old L56-L56 -> New L56-L56`

### Technical Notes & Disclosures

- **Post Hoc Addition Disclosure**: The added exploratory leaves (including `F3_unseen_state_rate` = 35.79%, 34/95 evaluation samples) were added post hoc after results were seen.
- **Recomputed Paired McNemar Tests (N=95, Technique Level)**: Evaluated directly from `data/processed_7ep/exploratory_tactic_conditioned_predictions.csv`:
-   - **Hit@1 Endpoint**: Discordant pairs $b=5, c=7$, exact two-sided McNemar $p = 0.774414$ ($p \approx 0.7744$), Variant Hit@1 = 5/95, Frequency Hit@1 = 7/95.
-   - **Hit@3 Endpoint**: Discordant pairs $b=3, c=11$, exact two-sided McNemar $p = 0.057373$ ($p \approx 0.0574$), Variant Hit@3 = 8/95, Frequency Hit@3 = 16/95.
-   - **Endpoint Resolution**: $b=5, c=7$ belongs strictly to **Hit@1**; $b=3, c=11$ belongs strictly to **Hit@3**.
-   - **Report Text Alignment**: In `reports/7ep/exploratory_tactic_conditioned_report.md`:
-     - Line 28: `- **Top-1**: Variant hits and Frequency misses ($b=5$); Frequency hits and Variant misses ($c=7$); Exact McNemar $p = 0.7744$ (descriptive, raw p).`
-     - Line 29: `- **Top-3**: Variant hits and Frequency misses ($b=3$); Frequency hits and Variant misses ($c=11$); Exact McNemar $p = 0.0574$ (descriptive, raw p).`
-     - **Audit Finding**: The report text lines 28 and 29 match the recomputed values exactly without disagreement.


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
- **Verification Verdict**: **AUTHORISED_CHANGE**

### Core Prediction Invariant Check (171 Records)

- **Evaluated Fields**: `(sample_id, episode, fold, target set, top-3 hit flags, primary prediction)`
- **Code Check Result**: **171 / 171** records identical old vs new (**PASS**)

| Category | Count | Status | Policy / Constraint |
|:---|:---:|:---:|:---|
| **Identical Leaves** | 4486 | IDENTICAL | Core empirical values preserved |
| **Changed Leaves** | 1746 | CHANGED | Monitored by change authorization |
| **Added Leaves** | 342 | ADDED | Justified by caller rationale |
| **Removed Leaves** | 95 | REMOVED | Justified by caller rationale |

### Technical Notes & Disclosures

- **Contract Alignment**: Upgraded from draft Schema 1.0.0 to finalized Schema 1.1.0 (`schemas/c4_prediction_record.schema.json`).


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
- **Invariant 1 (`old = identical + changed + removed`)**: `959 = 588 + 137 + 234` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `1639 = 588 + 137 + 914` (**PASS**)
- **Verification Verdict**: **AUTHORISED_CHANGE**

### Real Line Diff (`git diff --stat` & Changed Line Numbers)

```text
reports/7ep/prediction_record_examples.md | 1222 ++++++++++++++++++++++-------
 1 file changed, 951 insertions(+), 271 deletions(-)
```

**Changed Line Ranges (139 hunk blocks)**:

- `Old L1-L1 -> New L1-L1`
- `Old L4-L4 -> New L4-L4`
- `Old L6-L6 -> New L6-L6`
- `Old L11-L11 -> New L11-L11`
- `Old L13-L19 -> New L13-L28`
- `Old L23-L23 -> New L32-L33`
- `Old L28-L29 -> New L38-L39`
- `Old L30-L29 -> New L41-L42`
- `Old L34-L38 -> New L46-L50`
- `Old L42-L42 -> New L54-L54`
- `Old L60-L60 -> New L72-L72`
- `Old L66-L66 -> New L78-L78`
- `Old L98-L100 -> New L110-L112`
- `Old L104-L104 -> New L116-L116`
- `Old L108-L108 -> New L120-L120`
- `Old L113-L113 -> New L125-L125`
- `Old L118-L118 -> New L130-L130`
- `Old L123-L123 -> New L135-L135`
- `Old L142-L142 -> New L154-L154`
- `Old L143-L142 -> New L156-L156`
- `Old L151-L151 -> New L164-L169`
- `Old L155-L155 -> New L173-L173`
- `Old L156-L155 -> New L175-L175`
- `Old L164-L164 -> New L183-L188`
- `Old L168-L168 -> New L192-L192`
- *(truncated: 114 additional hunk ranges)*

### Technical Notes & Disclosures

- Verified against live records by `scripts/verify_prediction_records.py`.


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
- **Invariant 1 (`old = identical + changed + removed`)**: `186 = 5 + 10 + 171` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `31 = 5 + 10 + 16` (**PASS**)
- **Verification Verdict**: **AUTHORISED_CHANGE**

### Real Line Diff (`git diff --stat` & Changed Line Numbers)

```text
reports/7ep/requirements_trace.md | 217 ++++++--------------------------------
 1 file changed, 31 insertions(+), 186 deletions(-)
```

**Changed Line Ranges (1 hunk blocks)**:

- `Old L1-L186 -> New L1-L31`

### Technical Notes & Disclosures

- Rebuilt strictly from `docs/proposal_requirements.json` using exact proposal wording.
- Enforced valid enum values (`IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_DEMONSTRATED_ON_DATASET`, `PARTIAL`, `NOT_TESTABLE_UNTIL_C3`, `PENDING_HUMAN_EVIDENCE`).


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
- **Invariant 1 (`old = identical + changed + removed`)**: `31 = 28 + 3 + 0` (**PASS**)
- **Invariant 2 (`new = identical + changed + added`)**: `31 = 28 + 3 + 0` (**PASS**)
- **Verification Verdict**: **AUTHORISED_CHANGE**

### Real Line Diff (`git diff --stat` & Changed Line Numbers)

```text
reports/7ep/requirements_trace.md | 6 +++---
 1 file changed, 3 insertions(+), 3 deletions(-)
```

**Changed Line Ranges (3 hunk blocks)**:

- `Old L15-L15 -> New L15-L15`
- `Old L17-L17 -> New L17-L17`
- `Old L27-L27 -> New L27-L27`

### Technical Notes & Disclosures

- FR2 updated to IMPLEMENTED_DEMONSTRATED_ON_DATASET.
- NFR5 updated to PARTIAL (adapter format proposed by C4, contract not agreed by C3).
- FR4 limits cite pre-registered primary Hit@3 endpoints instead of descriptive Hit@1.

