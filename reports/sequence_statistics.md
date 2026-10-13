# CAM-LDS Sequence Statistics & Next-Step Coverage Report

> [!IMPORTANT]
> **Forensic Scope Notice:** This report presents telemetry sequence distribution and coverage analysis only; no machine learning model was trained and no predictive accuracy is reported.

## 1. Next-Step Sample Volume & Self-Repeat Rates

| Slice (Variant + Granularity) | Total Samples | Expected | Mismatch? | E1 | E2 | E3 | E4 | Multi Inputs | Multi Targets | Self-Repeats | Self-Repeat Rate (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **collapsed (full)** | **67** | 67 | None | 18 | 19 | 20 | 10 | 20 | 19 | 0 | **0.00%** |
| **collapsed (parent)** | **67** | 67 | None | 18 | 19 | 20 | 10 | 20 | 19 | 1 | **1.49%** |
| **raw (full)** | **95** | 95 | None | 26 | 20 | 28 | 21 | 21 | 20 | 28 | **29.47%** |
| **raw (parent)** | **95** | 95 | None | 26 | 20 | 28 | 21 | 21 | 20 | 29 | **30.53%** |

## 2. Technique Overlap Across Episodes (Full Technique ID)

### Distinct Technique Counts per Episode

| **E1** | **E2** | **E3** | **E4** |
| --- | --- | --- | --- |
| 31 | 21 | 23 | 10 |

### Pairwise Technique Overlap Matrix

| Episode | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| **E1** | 31 | 9 | 4 | 4 |
| **E2** | 9 | 21 | 5 | 3 |
| **E3** | 4 | 5 | 23 | 3 |
| **E4** | 4 | 3 | 3 | 10 |

### Pairwise Shared Techniques

- **E1 & E2** (9 shared): `T1003.008`, `T1007`, `T1016`, `T1049`, `T1057`, `T1070.004`, `T1083`, `T1105`, `T1201`
- **E1 & E3** (4 shared): `T1003.008`, `T1059`, `T1083`, `T1105`
- **E1 & E4** (4 shared): `T1070.004`, `T1082`, `T1105`, `T1548.003`
- **E2 & E3** (5 shared): `T1003.008`, `T1018`, `T1071.001`, `T1083`, `T1105`
- **E2 & E4** (3 shared): `T1070.004`, `T1071.001`, `T1105`
- **E3 & E4** (3 shared): `T1036.005`, `T1071.001`, `T1105`

## 3. Leave-One-Episode-Out (LOEO) Fold Coverage Analysis

Each fold tests on one isolated episode while training strictly on the remaining three episodes.

### Slice: `collapsed` variant at `full` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4 | 18 | **38.9%** (7/18) | **38.9%** (7/18) | **17** | `T1033`, `T1059.006`, `T1069`, `T1087` (+13 more) |
| **E2** | E1, E3, E4 | 19 | **68.4%** (13/19) | **73.7%** (14/19) | **9** | `T1003`, `T1005`, `T1041`, `T1046` (+5 more) |
| **E3** | E1, E2, E4 | 20 | **40.0%** (8/20) | **40.0%** (8/20) | **15** | `T1021.005`, `T1039`, `T1053.003`, `T1059.004` (+11 more) |
| **E4** | E1, E2, E3 | 10 | **60.0%** (6/10) | **60.0%** (6/10) | **4** | `T1078.003`, `T1205.001`, `T1543.002`, `T1599` |

### Slice: `collapsed` variant at `parent` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4 | 18 | **44.4%** (8/18) | **44.4%** (8/18) | **13** | `T1033`, `T1069`, `T1120`, `T1124` (+9 more) |
| **E2** | E1, E3, E4 | 19 | **78.9%** (15/19) | **78.9%** (15/19) | **8** | `T1005`, `T1041`, `T1046`, `T1074` (+4 more) |
| **E3** | E1, E2, E4 | 20 | **60.0%** (12/20) | **50.0%** (10/20) | **13** | `T1021`, `T1039`, `T1053`, `T1072` (+9 more) |
| **E4** | E1, E2, E3 | 10 | **60.0%** (6/10) | **60.0%** (6/10) | **4** | `T1078`, `T1205`, `T1543`, `T1599` |

### Slice: `raw` variant at `full` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4 | 26 | **53.8%** (14/26) | **53.8%** (14/26) | **17** | `T1033`, `T1059.006`, `T1069`, `T1087` (+13 more) |
| **E2** | E1, E3, E4 | 20 | **70.0%** (14/20) | **75.0%** (15/20) | **9** | `T1003`, `T1005`, `T1041`, `T1046` (+5 more) |
| **E3** | E1, E2, E4 | 28 | **46.4%** (13/28) | **46.4%** (13/28) | **15** | `T1021.005`, `T1039`, `T1053.003`, `T1059.004` (+11 more) |
| **E4** | E1, E2, E3 | 21 | **38.1%** (8/21) | **38.1%** (8/21) | **4** | `T1078.003`, `T1205.001`, `T1543.002`, `T1599` |

### Slice: `raw` variant at `parent` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4 | 26 | **57.7%** (15/26) | **57.7%** (15/26) | **13** | `T1033`, `T1069`, `T1120`, `T1124` (+9 more) |
| **E2** | E1, E3, E4 | 20 | **80.0%** (16/20) | **80.0%** (16/20) | **8** | `T1005`, `T1041`, `T1046`, `T1074` (+4 more) |
| **E3** | E1, E2, E4 | 28 | **67.9%** (19/28) | **53.6%** (15/28) | **13** | `T1021`, `T1039`, `T1053`, `T1072` (+9 more) |
| **E4** | E1, E2, E3 | 21 | **38.1%** (8/21) | **38.1%** (8/21) | **4** | `T1078`, `T1205`, `T1543`, `T1599` |

## 4. Evaluation Feasibility & Dataset Limitations

Empirical Limitations of CAM-LDS Next-Stage Modeling:
1. Dataset Sample Size: Across all four distinct attack campaigns, only 67 collapsed transition samples (95 raw transition samples) are available at full technique granularity.
2. Closed-Vocabulary Bounds (Full ID Granularity): Pooled over the 4 collapsed full-ID folds, 34 of 67 test samples (50.7%) have a current technique seen in training and 35 of 67 (52.2%) have a target technique seen in training. These values establish the empirical upper bounds on what any closed-vocabulary model can achieve on this dataset.
3. Closed-Vocabulary Bounds (Parent Granularity): For parent granularity, 41 of 67 test samples (61.2%) have a current technique seen in training and 39 of 67 (58.2%) have a target technique seen in training targets.
