# C2 audit report

Run: 2026-10-15 01:11:29 | Python 3.12.10 | pandas 3.0.6 | numpy 2.5.3 | OS Windows-11-10.0.26300-SP0

Result: **32 PASS, 0 FAIL**

| ID | Check | Result | Detail |
|---|---|---|---|
| A1 | all 7 scripts present with the audited md5 | PASS | {'c2_pipeline.py': 'c2\\pipeline\\c2_pipeline.py', 'stage1_sensitivity.py': 'c2\\stage1\\stage1_sensitivity.py', 'stage1_shap.py': 'c2\\stag |
| A2 | every step exited 0 | PASS | {'1_stage1': 248.0, '2_stage1_diagnostics': 29.4, '3_stage1_shap': 13.4, '4_sensitivity': 24.6, '5_stage2': 5.1, '6_stage3': 2.6, '7_pipelin |
| A3 | re-running stage 2, stage 3 and the pipeline gives byte-identical outputs (NFR-03) | PASS | [] |
| A4 | input data files unchanged by the run (NFR-07) | PASS | task_A, task_B sha256 compared before/after |
| A5 | task A: no scenario appears in more than one split | PASS | 35 scenarios, overlap=0 |
| A5 | task B: no scenario appears in more than one split | PASS | 33 scenarios, overlap=0 |
| A6 | Stage 1 model uses only allowed behavioural features (no scenario/session/source/label/raw-IP columns) | PASS | 62 features; unexpected=[]; feature_set=core |
| A7 | S1 test_overall.random_forest.accuracy = 0.93929 | PASS | got 0.93929173693086 |
| A7 | S1 test_overall.random_forest.macro_f1 = 0.71772 | PASS | got 0.7177167411485923 |
| A7 | S1 by_source.Windows-APT-2025.random_forest.accuracy = 1.0 | PASS | got 1.0 |
| A7 | S1 by_source.OTRF.random_forest.accuracy = 0.88 | PASS | got 0.88 |
| A7 | S1 by_source.OTRF.majority_baseline.accuracy = 0.89333 | PASS | got 0.8933333333333333 |
| A7 | S2 selected_alpha = 1.0 | PASS | got 1.0 |
| A7 | S2 test_by_source.Windows-APT-2025.markov.top1 = 0.4648370497427101 | PASS | got 0.4648370497427101 |
| A7 | S2 test_by_source.Windows-APT-2025.markov.top3 = 0.8970840480274442 | PASS | got 0.8970840480274442 |
| A7 | S2 test_by_source.Windows-APT-2025.frequency_baseline.top1 = 0.29588336192109777 | PASS | got 0.29588336192109777 |
| A7 | S2 test_by_source.Windows-APT-2025.frequency_baseline.top3 = 0.7590051457975986 | PASS | got 0.7590051457975986 |
| A7 | S3 test_all.auc = 0.9307431935246505 | PASS | got 0.9307431935246505 |
| A7 | S3 test_by_source.Windows-APT-2025.auc = 0.9620792039357378 | PASS | got 0.9620792039357378 |
| A7 | PIPE events = 1278 | PASS | got 1278 |
| A7 | PIPE detected = 1178 | PASS | got 1178 |
| A7 | PIPE mismatches_with_stage3 = 0 | PASS | got 0 |
| A7 | sensitivity A_train_WAPT_test_OTRF/V_full/rf AUC = 0.678594 | PASS | got 0.678594 |
| A7 | sensitivity A_train_WAPT_test_OTRF/V_full/hgb AUC = 0.770945 | PASS | got 0.770945 |
| A7 | sensitivity A_train_WAPT_test_OTRF/V_minimal/hgb AUC = 0.716207 | PASS | got 0.716207 |
| A7 | sensitivity B_leave_one_OTRF_capture_out/V_full/rf AUC = 0.519881 | PASS | got 0.519881 |
| A8 | handoff file: 1,278 unique events, CSV and JSON agree on count, schema_version 1.0 | PASS | csv=1278 json=1278 |
| A8 | all probabilities lie in [0,1] | PASS | ['classification_probability', 'malicious_probability', 'next_1_prob', 'next_2_prob', 'next_3_prob', 'escalation_probability'] |
| A8 | next_1 >= next_2 >= next_3 and the three sum to <= 1 | PASS |  |
| A8 | undetected events have empty detection/prediction fields; detected events have all of them | PASS |  |
| A8 | observed_sequence of a detected event ends with its detected technique | PASS |  |
| A8 | events are in time order within each session (FR-04) | PASS |  |

## Findings to state honestly in the report and viva

- Windows-APT test split contains 0 benign rows (OTRF: 1072); false-positive behaviour cannot be measured on Windows-APT.
- Windows-APT Stage 1 accuracy 1.000: labels come from Wazuh rules, so this is rule re-learning, not detection capability.
- OTRF Stage 1 accuracy 0.880 is BELOW the majority baseline 0.893; end-to-end only 12 of 112 OTRF malicious test events are flagged.
- All-rows Stage 1 accuracy 0.939 mixes both sources and must not be the headline.
- Test classes never seen in training: ['T1047', 'T1069.001', 'T1087.001'] (2.909% of test rows).
- Stage 2 OTRF test: 48.2% of states unseen in training; OTRF results there are not meaningful. All OTRF test transitions are self-transitions, so escalation has no positive cases there.
- Task A/B labels come from the dataset audit; tactic order (stage 3) is the official ATT&CK order with the 'latest tactic' rule for multi-tactic techniques (author's assumption).
- Stage 1 itself was not re-run twice here; its reproducibility rests on the two independent runs already compared (0 of 2,372 predictions differ).
- NFR-05 (scalability to additional records) was not tested.

## Step timings (seconds)

{"1_stage1": 248.0, "2_stage1_diagnostics": 29.4, "3_stage1_shap": 13.4, "4_sensitivity": 24.6, "5_stage2": 5.1, "6_stage3": 2.6, "7_pipeline": 1.5, "8_rerun_stage2": 7.0, "9_rerun_stage3": 4.0, "10_rerun_pipeline": 1.6}
