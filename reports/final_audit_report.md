# Final Audit Report: Component 4 Evaluation & Deliverables

Generated automatically by `scripts/build_final_audit_report.py`.
Summarizes verification gate results, baseline integrity, test coverage, ledger progression, and git diff statistics.

## 1. Integrity Verification Checks

| Verification Command | Exit Code | Status | Output Summary |
|:---|:---:|:---:|:---|
| `python scripts/verify_all_hashes.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_evaluation.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_tactic_evaluation.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_stage1_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_evaluation_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_prediction_records.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_learning_curve_7ep.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_e5_removed.py` | `0` | **PASS** | `ALL E5-REMOVED SENSITIVITY VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_planted_realscale_7ep.py` | `0` | **PASS** | `ALL 7-EPISODE REAL-SCALE POWER ANALYSIS VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_permutation_7ep.py` | `0` | **PASS** | `ALL 7-EPISODE PERMUTATION TEST VERIFICATIONS PASSED SUCCESSFULLY.` |
| `python scripts/verify_tie_sensitivity_7ep.py` | `0` | **PASS** | `ALL TIE-SENSITIVITY CHECKS PASSED (EXIT CODE 0).` |
| `python scripts/verify_exploratory_tactic_conditioned.py` | `0` | **PASS** | `================================================================================` |
| `python scripts/verify_viva_pack.py` | `0` | **PASS** | `[PASS] All viva pack documents, figures, and tokens verified successfully!` |
| `pytest tests/` | `0` | **PASS** | `======================= 184 passed in 92.40s (0:01:32) ========================` |

## 2. Key Verified Counts

- **Total Unit / Integration Tests**: 184 passed
- **Total Protected Baseline Hashes**: 61 SHA-256 digests verified
- **Evaluated LOEO Prediction Records**: 171 records (95 technique + 76 tactic) across 7 episodes
- **Schema Validation**: 100% compliant with JSON Schema `v1.0.0`
- **Requirements Coverage**: FR1–FR9 and NFR1–NFR6 mapped and verified

## 3. Overnight Execution Ledger

The current overnight execution ledger (`reports/overnight_ledger.md`):

```markdown
# Overnight Execution Ledger

| Part | Git HEAD (SHA) | verify_all_hashes Exit | Pytest Passed | Pytest Failed | Status | UTC Timestamp |
|:---|:---|:---:|:---:|:---:|:---|:---:|
| P0 | `42e941a53b3c3a126c7b98325939a1a9e4c8558a` | 0 | 151 | 0 | PASS | 2026-10-14T19:51:23Z |
| P1 | `9cf7913f0011245f18c8407db3bcccecde83101c` | 0 | 151 | 0 | PASS | 2026-10-14T20:00:58Z |
| P2 | `28902632103c13db83ddd2900b562a1237890f8b` | 0 | 152 | 0 | PASS | 2026-10-14T20:18:05Z |
| P3 | `6055024ef7f1efbbd9df87ac1e9c93ce595ae7c8` | 0 | 152 | 0 | PASS | 2026-10-14T20:48:48Z |
| P4 | `5d2a30919896f292b82094effb93fb539428f165` | 0 | 157 | 0 | PASS | 2026-10-15T01:58:27Z |
| P5 | `4cd70e6e09e99fc542a6c7903303c973e043d981` | 0 | 163 | 0 | PASS | 2026-10-15T02:17:30Z |
| P6 | `526236f4c4a62f8a3f404aa4526a71a50da37492` | 0 | 174 | 0 | PASS | 2026-10-15T03:56:22Z |
| P7 | `24215585916ce78d1256140953a2c61505ecf752` | 0 | 178 | 0 | PASS | 2026-10-15T04:14:46Z |
| P8 | `c4ae715d552b8d43789cde45d10e1e545f6ed212` | 0 | 181 | 0 | PASS | 2026-10-15T04:30:23Z |
| P9 | `0e28a209fb26ef8085223806c74ea141723aaa95` | 0 | 184 | 0 | PASS | 2026-10-15T04:41:08Z |
```

## 4. Git Diff Summary (`git diff --stat 42e941a`)

```text
artifacts/7ep/production_model/collapsed_full.json |  969 +++++++++++++++++++
 artifacts/7ep/production_model/manifest.json       |   50 +
 .../7ep/production_model/tactic_collapsed.json     |  305 ++++++
 .../exploratory_tactic_conditioned_predictions.csv |   96 ++
 data/processed_7ep/prediction_records_loeo.jsonl   |  171 ++++
 data/processed_7ep/tie_sensitivity_7ep_samples.csv | 1015 ++++++++++++++++++++
 docs/analyst_feedback_form.md                      |   41 +
 docs/c3_c4_interface_contract.md                   |   62 ++
 docs/c3_open_questions.md                          |   53 +
 docs/data_provenance.md                            |   37 +
 docs/demo_script.md                                |   51 +
 .../7ep/exploratory_tactic_conditioned_report.md   |   57 ++
 .../exploratory_tactic_conditioned_results.json    |  457 +++++++++
 reports/7ep/permutation_7ep_report.json            |   16 +-
 reports/7ep/permutation_7ep_report.md              |   28 +-
 reports/7ep/prediction_record_examples.md          |  959 ++++++++++++++++++
 reports/7ep/requirements_trace.md                  |  186 ++++
 reports/7ep/tie_sensitivity_7ep.json               |  649 +++++++++++++
 reports/7ep/tie_sensitivity_7ep.md                 |  132 +++
 reports/_baseline_hashes_7ep_inference.json        |   18 +-
 reports/audit/p1_findings.md                       |  127 +++
 .../measurements/dashboard_prediction_panel.png    |  Bin 0 -> 91554 bytes
 .../measurements/dashboard_tactic_prediction.png   |  Bin 0 -> 96618 bytes
 reports/measurements/dashboard_tied_case.png       |  Bin 0 -> 97610 bytes
 reports/measurements/dashboard_unseen_state.png    |  Bin 0 -> 105272 bytes
 reports/measurements/nfr1_timing.json              |  133 +++
 reports/measurements/nfr1_timing.md                |   61 ++
 reports/nfr_criteria.md                            |   54 ++
 reports/overnight_decisions.md                     |    4 +
 reports/overnight_ledger.md                        |   14 +
 reports/permutation_test_v2_report.json            |   24 +-
 reports/permutation_test_v2_report.md              |   32 +-
 reports/prereg_7episode_design.md                  |   63 ++
 schemas/c3_event.schema.json                       |   73 ++
 schemas/c4_prediction_record.schema.json           |  298 ++++++
 scripts/audit_lc_k6.py                             |   90 ++
 scripts/audit_png_anomaly.py                       |   84 ++
 scripts/audit_prereg_strings.py                    |  112 +++
 scripts/audit_s1s3_unchanged.py                    |  152 +++
 scripts/audit_tie_handling_code.py                 |   61 ++
 scripts/build_prediction_records.py                |  679 +++++++++++++
 scripts/build_requirements_trace.py                |  296 ++++++
 scripts/build_viva_pack.py                         |  383 ++++++++
 scripts/capture_dashboard_screenshots.py           |   79 ++
 scripts/generate_baseline_hashes_7ep_inference.py  |    3 +
 scripts/measure_nfr1.py                            |  641 ++++++++++++
 scripts/mutation_sweep.py                          |  261 ++++-
 scripts/print_exempt_tokens.py                     |  118 +++
 scripts/print_file.py                              |   33 +
 scripts/reproduce_all.py                           |  134 +++
 scripts/run_exploratory_tactic_conditioned.py      |  557 +++++++++++
 scripts/run_permutation_test_7ep.py                |   15 +-
 scripts/run_permutation_test_v2.py                 |   10 +-
 scripts/run_tie_sensitivity_7ep.py                 |  783 +++++++++++++++
 scripts/train_production_model.py                  |  184 ++++
 scripts/update_ledger.py                           |   88 ++
 scripts/verify_evaluation.py                       |  170 ++++
 scripts/verify_exploratory_tactic_conditioned.py   |  187 ++++
 scripts/verify_permutation_7ep.py                  |   13 +-
 scripts/verify_permutation_test_v2.py              |    9 +-
 scripts/verify_prediction_records.py               |  226 +++++
 scripts/verify_tie_sensitivity_7ep.py              |  120 +++
 scripts/verify_viva_pack.py                        |  124 +++
 scripts/write_p1_findings.py                       |  355 +++++++
 src/c4/c3_adapter.py                               |  289 ++++++
 src/c4/dashboard/prediction_app.py                 |  259 +++++
 src/c4/dashboard/prediction_panel.py               |  350 +++++++
 src/c4/prediction_record.py                        |  175 ++++
 tests/fixtures/c3/malformed_invalid_priority.json  |    7 +
 tests/fixtures/c3/malformed_missing_episode.json   |    4 +
 tests/fixtures/c3/valid_event.json                 |   19 +
 tests/test_c3_adapter.py                           |  238 +++++
 tests/test_exploratory_tactic_conditioned.py       |   66 ++
 tests/test_inference_7ep.py                        |   37 +
 tests/test_nfr1.py                                 |  104 ++
 tests/test_prediction_panel.py                     |  120 +++
 tests/test_prediction_record.py                    |  154 +++
 tests/test_viva_pack_sweep.py                      |   77 ++
 viva_pack/01_dataset.md                            |   33 +
 viva_pack/02_split_and_training.md                 |   33 +
 viva_pack/03_scores.md                             |   38 +
 viva_pack/04_worked_examples.md                    |  959 ++++++++++++++++++
 viva_pack/05_figures/a4_power_curve.png            |  Bin 0 -> 222031 bytes
 viva_pack/05_figures/learning_curve_7ep.png        |  Bin 0 -> 374522 bytes
 .../05_figures/loeo_performance_bar_chart.png      |  Bin 0 -> 139000 bytes
 viva_pack/06_claims_and_limits.md                  |   35 +
 viva_pack/07_reproduce.md                          |   36 +
 viva_pack/README.md                                |   23 +
 88 files changed, 15188 insertions(+), 70 deletions(-)

warning: in the working copy of 'reports/confusion_matrix_parent.csv', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'reports/evaluation_report.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'reports/tactic_evaluation_report.md', LF will be replaced by CRLF the next time Git touches it
```

## 5. Open Items Register

The following items remain open pending live environment deployment and formal C3 integration agreement:

| ID | Title | Category | Status | Target / Notes |
|:---|:---|:---|:---:|:---|
| **LIM-08** | Absence of Live Operational C3 Metadata in CAM-LDS | Interface Contract | *OPEN* | C4 prediction record and C3 adapter support pass-through with explicit null semantics pending live integration agreement with C3 owner. |
| **LIM-09** | Real-Time Streaming Ingestion and Dynamic Episode Demarcation | Operational Deployment | *OPEN* | Marked as an open research/engineering question in docs/c3_open_questions.md for Stage 3 production deployment. |
| **LIM-10** | Higher-Order Context Memory ($k \ge 2$ Markov Dynamics) | Model Expressiveness | *OPEN* | Exploratory analysis showed severe state space sparsity even at order 1; higher-order models require substantially larger cross-enterprise corpora. |

## 6. Historical Tag Audit Note

> **Historical Discrepancy Note regarding `stage2-verified`**:
> The annotated tag message for `stage2-verified` states: `tests: 105 passed`. However, the test suite at that commit actually collected and passed **107 tests**. The commit and code were completely unmodified; the discrepancy occurred strictly in the handwritten annotation text of the tag. Tag `stage2-verified` remains untouched to preserve repository history.

