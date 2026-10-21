# Final Audit Report: Component 4 Evaluation & Deliverables

Generated automatically by `scripts/build_final_audit_report.py`.
- **Git HEAD**: `9322f5f9a3daf0e20af2eafcbf09d141a7872b55`
- **Release Tag**: `c4-7ep-verified-v3`
- **Prediction Record Schema Version**: `1.1.0`
- **Regression Test Suite**: 209 tests passed
- **Protected Baseline Hashes**: 61/61 verified

## 1. Integrity Verification Checks

| Verification Command | Exit Code | Status | Output Summary |
|:---|:---:|:---:|:---|
| `python scripts/verify_all_hashes.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_stage1_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_evaluation_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_prediction_records.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_learning_curve_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_e5_removed.py` | `0` | **PASS** | `ALL E5-REMOVED SENSITIVITY VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_planted_realscale_7ep.py` | `0` | **PASS** | `ALL 7-EPISODE REAL-SCALE POWER ANALYSIS VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_permutation_7ep.py` | `0` | **PASS** | `ALL 7-EPISODE PERMUTATION TEST VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_tie_sensitivity_7ep.py` | `0` | **PASS** | `ALL TIE-SENSITIVITY CHECKS PASSED (EXIT CODE 0).` |
| `python scripts/verify_exploratory_tactic_conditioned.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_holm_claim_rule.py` | `0` | **PASS** | `ALL HOLM STEP-DOWN AND CLAIM RULE VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify/verify_prereg_append_only.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_viva_pack.py` | `0` | **PASS** | `[PASS] All viva pack documents, figures, tokens, and 07_reproduce.md verified su` |
| `python scripts/verify_requirements_trace.py` | `0` | **PASS** | `Independent verification of requirements trace PASSED (15 requirements verified)` |
| `python scripts/verify_claims_map.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_overnight_summary.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_nfr1.py` | `0` | **PASS** | `================================================================================` |
| `pytest tests/` | `0` | **PASS** | `======================= 210 passed in 95.47s (0:01:35) ========================` |

## 2. Requirements Compliance & Verification Status

Requirements coverage derived directly from `docs/proposal_requirements.json`:
- **IMPLEMENTED_AND_TESTED**: 9 requirement(s)
- **IMPLEMENTED_DEMONSTRATED_ON_DATASET**: 2 requirement(s)
- **NOT_TESTABLE_UNTIL_C3**: 1 requirement(s)
- **PARTIAL**: 2 requirement(s)
- **PENDING_HUMAN_EVIDENCE**: 1 requirement(s)

> [!NOTE]
> In accordance with audit standards, requirements awaiting Component 3 live integration or external human usability trials are explicitly marked unverified:
> - FR8 (Context Integration (C3 information)): `NOT_TESTABLE_UNTIL_C3`
> - FR9 (Incident Information Display): `PARTIAL`
> - NFR4 (Usability): `PENDING_HUMAN_EVIDENCE`
> - NFR5 (Interoperability (accept C3 structured event format)): `PARTIAL`
>
> Consequently, FR8, FR9, NFR4, and NFR5 are NOT claimed as fully verified.

## 3. Overnight Execution Ledger

The complete execution ledger (`reports/overnight_ledger.md`):

```markdown
# Overnight Execution Ledger

> [!NOTE]
> Regenerated automatically by `scripts/audit/ledger.py` from `git log` and verified output logs.
> Each row records the exact commit containing that part's changes (commit author date in UTC).
> 'Full-Suite Pytest Total' is recorded strictly from full regression test suite executions.

| Part | Commit SHA | Author Date (UTC) | verify_all_hashes Exit | Full-Suite Pytest Total | New Tests Added | Status | Reconstructed |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **P0** | `42e941a53b3c3a126c7b98325939a1a9e4c8558a` | 2026-10-14T19:31:28Z | 0 | 151 | 0 | **PASS** | reconstructed |
| **P1** | `9cf7913f0011245f18c8407db3bcccecde83101c` | 2026-10-14T20:00:46Z | 0 | 151 | 0 | **PASS** | no |
| **P2** | `28902632103c13db83ddd2900b562a1237890f8b` | 2026-10-14T20:17:40Z | 0 | 152 | +1 | **PASS** | no |
| **P3** | `6055024ef7f1efbbd9df87ac1e9c93ce595ae7c8` | 2026-10-14T20:48:43Z | 0 | 152 | 0 | **PASS** | no |
| **P4** | `df49a9c02fa4ae3d13b92d02c380b37aea01ced5` | 2026-10-15T02:01:01Z | 0 | 157 | +5 | **PASS** | no |
| **P5** | `e45b3066f864e52c7012a16be223c43871859c48` | 2026-10-15T03:52:49Z | 0 | 163 | +6 | **PASS** | no |
| **P6** | `52f66c346ff577e2e25a134b0bc870e9ab061023` | 2026-10-15T04:01:23Z | 0 | 174 | +11 | **PASS** | no |
| **P7** | `404094040f90da2f75d8a8af807ce545eef7f31f` | 2026-10-15T04:16:45Z | 0 | 178 | +4 | **PASS** | no |
| **P8** | `dcd004a428de96f4f3a31784f68e13ccabe207f3` | 2026-10-15T04:32:22Z | 0 | 181 | +3 | **PASS** | no |
| **P9** | `d4557f4c0ab203da11e36e5f160270983936bcb1` | 2026-10-15T04:42:39Z | 0 | 184 | +3 | **PASS** | no |
| **P10** | `577de13ad08d11ad3dea4208b41a0b8e9ba52600` | 2026-10-15T05:30:36Z | 0 | 184 | 0 | **PASS** | no |
| **P11** | `996bd71102c8d87c8190d0617766b382f1051eb5` | 2026-10-15T05:34:32Z | 0 | 184 | 0 | **PASS** | no |
| **Q0** | `5a53d68d3b0e61a5537f777279e59477683ace4c` | 2026-10-15T06:02:47Z | 0 | 184 | 0 | **PASS** | reconstructed |
| **Q1** | `3dab166ce9a3ba72845554223ca6df458717b1dc` | 2026-10-15T06:06:48Z | 0 | 184 | 0 | **PASS** | no |
| **Q3** | `4f8d0c889e33d5df0d3ff679b596d5e44b65f7d5` | 2026-10-15T06:27:48Z | 0 | 184 | 0 | **PASS** | no |
| **Q7** | `53a5f1548b573f8619d11a9c815fb608664a9d44` | 2026-10-15T06:47:12Z | 0 | 188 | +4 | **PASS** | no |
| **Q9** | `cf6e5dbd885a7a6452817195abb0e1a284c25cec` | 2026-10-15T06:58:27Z | 0 | 189 | +1 | **PASS** | no |
| **Q4** | `4fc004bd150dbc599fa014ac64bbaf65bee59720` | 2026-10-15T07:07:04Z | 0 | 192 | +3 | **PASS** | no |
| **Q5** | `68908c47b14823141e9aa9b935710e878ae3249b` | 2026-10-15T07:35:30Z | 0 | 195 | +3 | **PASS** | no |
| **Q6** | `8779338e03c35defcb3158eaba163331987319ac` | 2026-10-15T07:42:37Z | 0 | 197 | +2 | **PASS** | no |
| **Q8** | `e567b8ac6cfa0dff24f53ba01039f5d1ebe104e6` | 2026-10-15T07:53:49Z | 0 | 202 | +5 | **PASS** | no |
| **Q2** | `f00c2175a8351e5d2da7b346fc81e8ad1a8b60a9` | 2026-10-15T08:13:11Z | 0 | 202 | 0 | **PASS** | no |
| **Q10** | `d859fcb71c1bb7d30b3312d99e6a974ede941a26` | 2026-10-15T08:24:05Z | 0 | 202 | 0 | **PASS** | no |
| **R0** | `6e58efc5a0807d7959ece791203158e32cc8215b` | 2026-10-15T08:43:15Z | 0 | 202 | 0 | **PASS** | reconstructed |
| **R1** | `fff7595a78b9268c76870b2a02314c7b7749a339` | 2026-10-15T08:49:05Z | 0 | not recorded | +5 | **PASS** | reconstructed |
| **R3** | `c6efee4343d3df6f62d22794458bd6dd08218b41` | 2026-10-15T10:14:40Z | 0 | not recorded | +2 | **PASS** | reconstructed |
| **R2** | `f494c0191f3477e04f0c185a26e42ac9792537c2` | 2026-10-15T10:35:11Z | 0 | not recorded | 0 | **PASS** | reconstructed |
| **R4** | `e33e008aa7da1ee4b8a9896dd6a1748935c660b1` | 2026-10-15T10:53:57Z | 0 | not recorded | +2 | **PASS** | reconstructed |
| **R5** | `3af318e8d92060b623be2c3e15a86a1a82a6ea27` | 2026-10-15T10:56:39Z | 0 | not recorded | 0 | **PASS** | reconstructed |
| **R6** | `8f0870fcce1b83045818544dd90eea426f158897` | 2026-10-15T13:12:43Z | 0 | not recorded | 0 | **PASS** | reconstructed |
| **R7** | `40cc9ed190f80d372fabee84a241dcb01ccb528a` | 2026-10-15T13:33:41Z | 0 | 209 | 0 | **PASS** | no |
| **S0** | `9322f5f9a3daf0e20af2eafcbf09d141a7872b55` | 2026-10-15T16:43:06Z | 0 | 209 | 0 | **PASS** | no |

## Notes and Historical Disclosures

Note: Prompt 13 final chat message blocks with contradictions vs generated files (by block name only):
- Exploratory Variant Block
- Hypothesis Test P2 / Tie Counts Block
- NFR1 Performance / CPU Telemetry Block
- Claims Map Block
- Requirements Trace Block
- Prediction Records Block
- Clean-Clone Verification Block
```

## 4. Decisions Register (Prompts 13, 14, 15, and 16)

# Overnight Decisions Log

| Part | Decision | Reason |
|:---|:---|:---|
| P0 | Use virtual environment at `..\.venv\Scripts\python.exe` | Standard workspace python environment containing all required scientific packages. |
| P2 | Full tie-sensitivity evaluation across min, max, random over 1000 trials | Exhaustive diagnostic check on all 171 LOEO prediction records to prove robustness to tie-breaking rules. |
| P5 | Train 7-episode production model on all 7 episodes | Deliverable required single production model covering all available empirical episodes with verified manifest. |
| P6 | Implement C3-C4 interface adapter with alias table | Allows seamless field renaming upon C3 owner agreement while maintaining CAM-LDS backwards compatibility. |
| P7 | Dashboard prediction panel built via decoupled modular component | Preserves FR1-FR3 timeline behavior without mutating existing dashboard files. |
| P8 | Declare response time defaults (warm median <= 2.0s, p95 <= 5.0s, cold <= 10.0s) | Proposal specified "acceptable response time"; defaults formally committed prior to timing benchmark. |
| P9 | Document raw archive SHA-256 and Zenodo provenance | Establishes raw data provenance; licence marked "licence text not found locally - student to confirm". |
| P10 | Use Git bundle for clean-clone reproduction | Bypasses OneDrive file-locking in clean external directory `C:\c4_clean_clone` while verifying bundle integrity. |

## Prompt 14 Decisions & Corrections (2026-10-15)

| Part | Decision / Correction | Technical Rationale |
|:---|:---|:---|
| P2 (Correction) | Exact expectation under uniform random tie-breaking, plus best/worst case bounds (Bound A and Bound B); not 1000 trials. | The tie-sensitivity evaluation computes the exact combinatorial expectation and extreme analytical bounds across candidate score permutations rather than Monte Carlo empirical trials. |
| P10 / Q2 (Correction) | True clean-clone rebuild from raw archives (`C:\c4_clean_clone_r2`) with zero intermediate/output copying and verified backup bundle `C:\c4_backup\c4_5921908.bundle`. | Replaces Prompt 13 clean clone where files had been copied from the working tree. Under Q2, only the 7 verified raw zip archives were copied to the clean clone. Two consecutive full rebuilds demonstrated 100% bit-identical hash parity across all 61 protected baseline files. |

## Prompt 15 Decisions & Repair Run (2026-10-15)

| Part | Decision / Action | Technical Rationale |
|:---|:---|:---|
| R1 | Strict baseline change register with leaf-level mathematical invariant enforcement. | Enforces `old = identical + changed + removed` and `new = identical + changed + added`; prints FAIL if changed > 0. |
| R2 | Rebuild viva claims map with code-substituted values and test node IDs. | Eliminates manual transcription; maps claims directly to empirical results and test node IDs. |
| R3 | Update requirements trace statuses for FR2, FR4, and NFR5. | Records FR2 as dataset-demonstrated, NFR5 as partial (adapter unagreed by C3), and FR4 limits citing pre-registered Hit@3 verdict. |
| R4 | Execute live interactive dashboard capture suite in isolated venv `C:\c4_capture_venv`. | Isolates playwright runtime from project dependencies; captures verified desktop (1440x900) and mobile (390x844) PNG evidence. |
| R6 | True clean-clone double rebuild in `C:\c4_clean_clone_r6`. | Proves complete bit-for-bit rebuild determinism from raw archives with zero drift across consecutive runs. |
| R7 | Finalise repair run, update overnight ledger, and verify all reproduction baselines. | Verifies all 61 baseline hashes, passes full pytest suite, and creates release bundle `C:\c4_backup\c4_40cc9ed.bundle`. |

## Prompt 16 Decisions & Protocol Evolution (2026-10-15)

| Part | Decision / Action | Technical Rationale |
|:---|:---|:---|
| S0 | Pre-cleanup safety net tag `pre-cleanup-v3` on initial HEAD (`40cc9ed`). | Preserves entire historical state before code clean-up; enforces Rule G4 provenance logging via `scripts/audit/run_logged.py`. |
| S1 | Audit repairs: ledger reconstruction, prereg Amendment 9, clean-clone line endings, and root of trust. | Puts all historical ledger rows on code-computed footing, establishes cryptographic root of trust in `docs/ROOT_OF_TRUST.md`, and proves clean-clone dirtiness cause by measurement. |
| S2 | Project clean-up and proper descriptive names for non-protected paths. | Standardizes pipeline stages into `scripts/pipeline/`, verifiers into `scripts/verify/`, audit tools into `scripts/audit/`, and moves prompts to `docs/process/prompts/`. |
| S3 | Industry-grade attack timeline and next-step advisor dashboard rebuild. | Delivers wide-layout analyst console with Altair swim-lane kill-chain visualization, WCAG 4.5:1 contrast, and live browser captures. |
| S4 | Code-derived data lineage documentation and comprehensive project map. | Parses data loaders and pipeline stages directly from AST/source to generate `docs/data_lineage.md` and `docs/PROJECT_MAP.md`. |
| S5 | Final release verification and release bundle packaging. | Runs clean-clone double rebuild in `C:\c4_clean_clone_s5`, creates annotated tag `c4-7ep-verified-v4`, and packages `C:\c4_backup\c4_final_v4.bundle`. |
| S6 | Non-destructive protected-path rename trial on branch `rename-protected-paths`. | Tests proposed folder renaming on isolated branch without modifying master baseline files. |

## 5. Open & Mitigated Items Register

The following items remain open or mitigated pending live environment deployment and formal C3 integration agreement:

| ID | Title | Category | Status | Target / Mitigation |
|:---|:---|:---|:---:|:---|
| **LIM-08** | Absence of Live Operational C3 Metadata in CAM-LDS | Interface Contract | *OPEN* | C4 prediction record and C3 adapter support pass-through with explicit null semantics pending live integration agreement with C3 owner. |
| **LIM-09** | Real-Time Streaming Ingestion and Dynamic Episode Demarcation | Operational Deployment | *OPEN* | Marked as an open research/engineering question in docs/c3_open_questions.md for Stage 3 production deployment. |
| **LIM-10** | Higher-Order Context Memory ($k \ge 2$ Markov Dynamics) | Model Expressiveness | *OPEN* | Exploratory analysis showed severe state space sparsity even at order 1; higher-order models require substantially larger cross-enterprise corpora. |
| **LIM-11** | Clean Clone Shares Parent Virtual Environment | Environment Isolation | *OPEN* | Environment parity is verified by comparing `pip freeze` against `requirements.lock.txt`. |
| **LIM-13** | C3 Interface Contract Unagreed by Component 3 | Integration Governance | *OPEN* | Status recorded as PARTIAL in requirements trace; adapter tested and validated against C4 internal fixtures only. |
| **LIM-14** | High Proportion of Low-Support Predictions (92/171 Cautioned) | Statistical Support | *MITIGATED* | Schema v1.1.0 enforces mandatory support caution flags and narrative warnings on all 92 low-support records, preventing over-confident claims; 92/171 records remain low-support due to benchmark dataset constraints. |
| **LIM-15** | Streamlit Readiness Metric Measures Health Endpoint, Not First Render | Performance Measurement | *OPEN* | Clarified in measurement documentation and known limitations; AppTest used for full headless DOM and component validation. |

## 6. Historical Tag Audit Note

> **Historical Discrepancy Note regarding `stage2-verified`**:
> The annotated tag message for `stage2-verified` states: `tests: 105 passed`. However, the test suite at that commit actually collected and passed **107 tests**. The commit and code were completely unmodified; the discrepancy occurred strictly in the handwritten annotation text of the tag. Tag `stage2-verified` remains untouched to preserve repository history.

