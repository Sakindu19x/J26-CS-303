# Deliverables Re-Verification Report (Prompt 16 S1 / Prompt 17 T4 Recheck)

> [!IMPORTANT]
> Empirical re-verification of all deliverables generated dynamically by `scripts/audit/build_q16_s1_recheck.py`.
> Every metric, status cell, test result, and image dimension is measured directly from active repository code and files.

## 1. CLAIM-07 Empirical Content Check

- **Ceiling Definition**: A sample satisfies the vocabulary ceiling if at least one target in `target_set` was observed in training episodes for that LOEO fold (`target_set & training_vocabulary != empty`).
- **Technique Ceiling (N=95)**:
  - Numerator (samples with target in training vocab): **59**
  - Denominator (total evaluation samples): **95**
  - Computed Percentage: **62.11%** (62.1053%)
- **Tactic Ceiling (N=76)**:
  - Numerator (samples with target in training vocab): **73**
  - Denominator (total evaluation samples): **76**
  - Computed Percentage: **96.05%** (96.0526%)
- **Evaluation**: Technique ceiling 62.11% and perfect-order cap 64.98% are below 75%; tactic ceiling reaches 96.05%.
- **Status**: **PASS**

## 2. Requirements Trace Status Cells (FR2 & NFR5)

| Requirement ID | Actual Status Cell in `reports/7ep/requirements_trace.md` | Verification Gate | Status |
|:---|:---|:---|:---:|
| **FR2** (Attack Episode Separation) | ``IMPLEMENTED_DEMONSTRATED_ON_DATASET`` | Expected `IMPLEMENTED_DEMONSTRATED_ON_DATASET` | **PASS** |
| **NFR5** (C3 Interoperability) | ``PARTIAL`` | Expected `PARTIAL` | **PASS** |

## 3. Analyst Demo Script Test Suite Execution

- **Test Script Executed**: `tests/test_demo_script_steps.py`
- **Pytest Exit Code**: `0` (PASS)
- **Executed Test Names**:
  - `tests/test_demo_script_steps.py::test_demo_script_steps_2_to_10_execution` (**PASSED**)

## 4. Live Dashboard Screenshot Telemetry (PIL Verification)

| Screenshot File Name | Pixel Width | Pixel Height | Size (Bytes) | SHA-256 Checksum |
|:---|:---:|:---:|:---:|:---|
| `reports/measurements/live_prediction_panel.png` | 1440 px | 900 px | 155,267 B | `b35a3b095da3cc9909209da60b074cc1c8892fb8d6dc7874a5a258f087016ab2` |
| `reports/measurements/live_prediction_panel_1440.png` | 1440 px | 900 px | 155,267 B | `b35a3b095da3cc9909209da60b074cc1c8892fb8d6dc7874a5a258f087016ab2` |
| `reports/measurements/live_prediction_panel_390.png` | 390 px | 844 px | 37,726 B | `3e20b6b05405e511e53216b0c411a58bbc5673dc4cc4942edf6cbf0f863d9c81` |
| `reports/measurements/live_tactic_prediction.png` | 1440 px | 900 px | 156,083 B | `7a53b21ce54a71908f6ff4d4e287e08d4a833e446eb9c9540882565ea05074e1` |
| `reports/measurements/live_tactic_prediction_1440.png` | 1440 px | 900 px | 156,083 B | `7a53b21ce54a71908f6ff4d4e287e08d4a833e446eb9c9540882565ea05074e1` |
| `reports/measurements/live_tactic_prediction_390.png` | 390 px | 844 px | 37,834 B | `bfeed261fbe3e86f0baeb81097cde5ac6a2e11be056222d26b1256409cd3d674` |
| `reports/measurements/live_tied_case.png` | 1440 px | 900 px | 155,329 B | `ae0c3dc0c581b5414d47b0cfedcb2ce51a0cee3a34bb25510e587f1029957ce9` |
| `reports/measurements/live_tied_case_1440.png` | 1440 px | 900 px | 155,329 B | `ae0c3dc0c581b5414d47b0cfedcb2ce51a0cee3a34bb25510e587f1029957ce9` |
| `reports/measurements/live_tied_case_390.png` | 390 px | 844 px | 37,788 B | `a4d74a5e2841318597189d3f14e16c3b441d46d0cef7c90103eb980feff1777e` |
| `reports/measurements/live_timeline_1440.png` | 1440 px | 900 px | 154,447 B | `2b037d4e525d5be8491e323ff76d19a170c7d09344171a5d08f4108b26dfaadf` |
| `reports/measurements/live_timeline_390.png` | 390 px | 844 px | 37,573 B | `f8e41ca7e6f26fb0a2643998c4c4e775a869292d96428b637df2b89e3f55d37b` |
| `reports/measurements/live_unseen_state.png` | 1440 px | 900 px | 155,343 B | `18722995353fbea3bf89125b6ef23a17fb4e36f29a8152469b4eac560faa5977` |
| `reports/measurements/live_unseen_state_1440.png` | 1440 px | 900 px | 155,343 B | `18722995353fbea3bf89125b6ef23a17fb4e36f29a8152469b4eac560faa5977` |
| `reports/measurements/live_unseen_state_390.png` | 390 px | 844 px | 37,801 B | `5d03a30b0cb44069e2cbd74139c9a2f8ec07a2884e053b79a85b2d8dbfe965f3` |

## 5. Overall Recheck Verdict

**Master T4 Recheck Verdict**: **ALL CONTENT CHECKS PASSED**
