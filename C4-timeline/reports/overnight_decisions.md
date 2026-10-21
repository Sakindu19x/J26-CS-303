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

