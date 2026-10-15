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
