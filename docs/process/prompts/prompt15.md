# PROMPT 15 – REPAIR RUN 2 (UNATTENDED)

Repo: `C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\c4`. Python: `..\.venv\Scripts\python.exe`. PowerShell.
These instructions are also saved in `docs\prompts\prompt15.md`: if you lose context, re-read THAT FILE.
NEVER open transcript files, task logs or brain\ logs (you did in Prompt 14; do not repeat).
No new modelling or hypotheses; the pre-registered verdict is not reopened.

## RULES
- **G1**: Final chat message = the table printed by `scripts/emit_final_table.py` (create it: reads `reports/overnight_ledger.md` and `git log` by commit-message prefix "R<n>:"; you never type a hash). No other text. Never retype numbers: every number in a document comes from code reading JSON/CSV.
- **G2**: Frozen unless named in the part. Baseline hash changes only where stated, via `scripts/record_baseline_change.py` (fixed in R1).
- **G3**: One commit per part, prefix "R<n>: ", explicit `git add` of named files only, clean `git status` after.
- **G4**: Generated docs: builder, independent verifier, test, mutation sweep, per-token exempt list in `reports/audit/exempt_<name>.txt`.
- **G5**: Failed gate => part FAIL in ledger, no threshold/code changes to pass it, continue independent parts.
- **G6**: Never copy files into a clone; never change git config to make a check pass.

**Order**: R0, R1, R3, R2, R4, R5, R6, R7.

---

### R0
Commit `docs/prompts/prompt15.md`; record HEAD, git status, verify_all_hashes, pytest count to `reports/audit/q15_R0_output.txt`.

### R1 BASELINE-CHANGE REGISTER
Rewrite `scripts/record_baseline_change.py` to compare ALL numeric leaves (JSON: every number by path; CSV: every cell; MD: every numeric token with line context) between HEAD and working tree and write, per file: counts old/new, leaves IDENTICAL, leaves CHANGED (old->new), leaves ADDED, leaves REMOVED, each listed. "VERIFIED" may be printed only when CHANGED = 0 and ADDED/REMOVED are each listed and justified by a rationale string supplied by the caller. Regenerate `reports/audit/q14_baseline_changes.md` as `reports/audit/q15_baseline_changes.md` for the three Prompt 14 changes (exploratory report, prediction records + examples, requirements trace). The McNemar b/c shown for the exploratory report must come from the CSV (the earlier "b=1, c=9" with p=0.0574 is wrong). List the 5 added exploratory leaves (incl. "F3 unseen state rate") and state in the file that they were added post hoc after results were seen. Add tests.

### R3 REQUIREMENTS TRACE
In `docs/proposal_requirements.json`/builder: FR2 status -> IMPLEMENTED_DEMONSTRATED_ON_DATASET (episodes are dataset labels); NFR5 -> PARTIAL (format proposed by C4, not agreed by C3; adapter tested only against C4's own fixtures); replace "cryptographically verified" for FR2 by "verified by test <node id>"; FR4 limits must cite the Hit@3 verdict (P1/P2 numbers read from evaluation_7ep_results.json/holm_claim_rule_results.json by code), not Hit@1. Every number in the matrix is produced by code from a named JSON pointer (verifier checks). Add rule: a row may be IMPLEMENTED_AND_TESTED only if at least one cited test file contains the name of an implementing module or the evidence file name (grep). Rebuild, sweep, update its baseline entry via the new register tool.

### R2 CLAIMS MAP
(a) Add per-claim `test_nodes` chosen by relevance: the verifier checks the cited test file text mentions the claim's evidence file or builder/verifier script name; where no such test exists write "none (verified by <script>)".
(b) CLAIM-11 evidence = the gate output file for immutability, not normalized_events.json.
(c) CLAIM-07 and the "75% accuracy" row: rewrite to "technique level: ceiling X (59/95 targets inside training vocabulary) and perfect-order cap Y (A4 planted report) are below 75%; tactic level: ceiling Z" with Z computed by code from evaluation_7ep_predictions.csv using the same definition as the technique ceiling; delete "mathematically and empirically impossible under LOEO". CLAIM-07 must cite the planted report for the cap.
(d) CLAIM-08: remove Hit@1 or label it "descriptive, not a headline".
(e) CLAIM-12: add that the share of cautioned records (92/171, from the records) means most predictions rest on <2 supporting episodes or <3 transitions.
(f) CLAIM-01 is generated from `reports/audit/rebuild_scope.json` written by R6; if R6 FAILs the claim text must say "not proven". Verifier + sweep + exempt list.

### R4 VIVA PACK AND DEMO
(a) Regenerate `viva_pack/07_reproduce.md` from the actual step list of `scripts/reproduce_all.py` (verifier: every script path named exists; the verifier count equals the real count; duration = measured from `reports/audit/q15_R7_output.txt` if present else omitted).
(b) `docs/demo_script.md`: every number (E1 event count, sample ids, example technique) is produced by code from the data or removed; add `tests/test_demo_script_steps.py` using streamlit.testing AppTest that executes steps 2-10 (select episode, select sample, read table, alternatives, tie notice, C3 "not provided", banner, hashes, schema badge) and fails if a described element is absent. Fix anything the test shows is wrong in the script (E1 has 38 events in nfr1_timing.json; the script says 19).
(c) Delete the unlabeled copies `dashboard_prediction_panel.png`, `dashboard_unseen_state.png`, `dashboard_tied_case.png`, `dashboard_tactic_prediction.png` (`git rm`) and update every reference; only `*_static_render.png` remain, labelled static everywhere.
(d) Try a LIVE capture in a SEPARATE venv (`python -m venv C:\c4_capture_venv`; `pip install playwright` there only; use channel="chrome", never download browsers, NEVER install into `..\.venv`). Drive the real app on port 8501, pick samples via the UI, save `reports/measurements/live_*.png` and a capture log. If it fails, log the exact error and keep static only.

### R5 HYGIENE
`git rm --cached -r scratch`; add `scratch/` to `.gitignore`. Add the missing Q0 row to `reports/overnight_ledger.md` (append a note, do not rewrite) and a note that the ledger's HEAD column is the commit BEFORE each part's own commit. Update known_limitations (generated) with: clean clone shares the venv; screenshots are static unless R4(d) succeeds; C3 contract unagreed; 92/171 low-support records; Streamlit ready time is health-endpoint time, not first render; Prompt 14 agent opened its transcript/task logs.

### R6 TRUE CLEAN-CLONE PROOF (after all other parts are committed)
Update `scripts/run_q2_clean_clone.py` so that it:
(1) removes `C:\c4_clean_clone_r2` and any older clone dirs, clones the CURRENT repo path to `C:\c4_clean_clone_r3`;
(2) copies ONLY `data/raw/*.zip` from the working repo (they are git-ignored) and prints each SHA-256 next to the value in `docs/data_provenance.md`;
(3) records git status/diff --stat of the clone before and after;
(4) DELETES all 61 baseline-protected files in the clone, runs `reproduce_all.py --rebuild`, then checks each of the 61 exists again and `verify_all_hashes` gives 61/61 MATCH; a file that exists only because it was not deleted or came from git is COPIED_FROM_GIT_ONLY;
(5) deletes and rebuilds a SECOND time and compares the 61 SHA-256 values run1 vs run2;
(6) prints per-step seconds;
(7) diffs pip freeze against `requirements.lock.txt` and states that the clone uses the same venv;
(8) GENERATES `reports/audit/rebuild_scope.md` and `rebuild_scope.json` from the run (delete the hand-written file; never hand-edit). Output `reports/audit/q15_R6_output.txt` written by the script. If anything fails, record exact files and FAIL; no workaround.

### R7 FINALISE
Re-run all verifiers and mutation sweeps (input to a file by script), pytest through update_ledger (it runs the tests), verify_all_hashes, `reproduce_all.py --verify-only` to `reports/audit/q15_R7_output.txt`, audit_hash_coverage (counts, categories of the exception list, reconciliation of 61 vs covered). New annotated tag `c4-7ep-verified-v3` on the final commit (do not move existing tags; message generated from measured counts). Then `git bundle create C:\c4_backup\c4_final_v3.bundle --all`, verify, list-heads to `C:\c4_backup\bundle_heads_v3.txt`, and also run `git log --oneline -n 25` and `git tag -n` into `reports/audit/q15_R7_git.txt` (committed before the tag only if you tag after; otherwise save under `C:\c4_backup`). Final message = `scripts/emit_final_table.py` output only.
