# CAM-LDS Sequence Statistics & Next-Step Coverage Report

> [!IMPORTANT]
> **Forensic Scope Notice:** This report presents telemetry sequence distribution and coverage analysis only; no machine learning model was trained and no predictive accuracy is reported.

## 1. Next-Step Sample Volume & Self-Repeat Rates

| Slice (Variant + Granularity) | Total Samples | Expected | Mismatch? | E1 | E2 | E3 | E4 | Multi Inputs | Multi Targets | Self-Repeats | Self-Repeat Rate (%) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **collapsed (full)** | **95** | 67 | FLAG | 18 | 19 | 20 | 10 | 29 | 26 | 0 | **0.00%** |
| **collapsed (parent)** | **95** | 67 | FLAG | 18 | 19 | 20 | 10 | 29 | 26 | 1 | **1.05%** |
| **raw (full)** | **131** | 95 | FLAG | 26 | 20 | 28 | 21 | 30 | 27 | 36 | **27.48%** |
| **raw (parent)** | **131** | 95 | FLAG | 26 | 20 | 28 | 21 | 30 | 27 | 37 | **28.24%** |

## 2. Technique Overlap Across Episodes (Full Technique ID)

### Distinct Technique Counts per Episode

| **E1** | **E2** | **E3** | **E4** | **E5** | **E6** | **E7** |
| --- | --- | --- | --- | --- | --- | --- |
| 31 | 21 | 23 | 10 | 4 | 12 | 22 |

### Pairwise Technique Overlap Matrix

| Episode | E1 | E2 | E3 | E4 |
|---|---|---|---|---|
| **E1** | 31 | 9 | 4 | 4 | 0 | 2 | 9 |
| **E2** | 9 | 21 | 5 | 3 | 0 | 1 | 7 |
| **E3** | 4 | 5 | 23 | 3 | 0 | 4 | 6 |
| **E4** | 4 | 3 | 3 | 10 | 0 | 2 | 1 |
| **E5** | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| **E6** | 2 | 1 | 4 | 2 | 0 | 12 | 2 |
| **E7** | 9 | 7 | 6 | 1 | 0 | 2 | 22 |

### Pairwise Shared Techniques

- **E1 & E2** (9 shared): `T1003.008`, `T1007`, `T1016`, `T1049`, `T1057`, `T1070.004`, `T1083`, `T1105`, `T1201`
- **E1 & E3** (4 shared): `T1003.008`, `T1059`, `T1083`, `T1105`
- **E1 & E4** (4 shared): `T1070.004`, `T1082`, `T1105`, `T1548.003`
- **E1 & E5** (0 shared): 
- **E1 & E6** (2 shared): `T1082`, `T1105`
- **E1 & E7** (9 shared): `T1003.008`, `T1016`, `T1033`, `T1057`, `T1083`, `T1190`, `T1590.002`, `T1591`, `T1592.002`
- **E2 & E3** (5 shared): `T1003.008`, `T1018`, `T1071.001`, `T1083`, `T1105`
- **E2 & E4** (3 shared): `T1070.004`, `T1071.001`, `T1105`
- **E2 & E5** (0 shared): 
- **E2 & E6** (1 shared): `T1105`
- **E2 & E7** (7 shared): `T1003.008`, `T1016`, `T1041`, `T1057`, `T1071.001`, `T1083`, `T1573.001`
- **E3 & E4** (3 shared): `T1036.005`, `T1071.001`, `T1105`
- **E3 & E5** (0 shared): 
- **E3 & E6** (4 shared): `T1053.003`, `T1059.004`, `T1105`, `T1564.001`
- **E3 & E7** (6 shared): `T1003.008`, `T1053.003`, `T1059.004`, `T1071.001`, `T1083`, `T1110.001`
- **E4 & E5** (0 shared): 
- **E4 & E6** (2 shared): `T1082`, `T1105`
- **E4 & E7** (1 shared): `T1071.001`
- **E5 & E6** (0 shared): 
- **E5 & E7** (0 shared): 
- **E6 & E7** (2 shared): `T1053.003`, `T1059.004`

## 3. Leave-One-Episode-Out (LOEO) Fold Coverage Analysis

Each fold tests on one isolated episode while training strictly on the remaining three episodes.

### Slice: `collapsed` variant at `full` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4, E5, E6, E7 | 18 | **72.2%** (13/18) | **66.7%** (12/18) | **14** | `T1059.006`, `T1069`, `T1087`, `T1120` (+10 more) |
| **E2** | E1, E3, E4, E5, E6, E7 | 19 | **68.4%** (13/19) | **78.9%** (15/19) | **7** | `T1003`, `T1005`, `T1046`, `T1074.001` (+3 more) |
| **E3** | E1, E2, E4, E5, E6, E7 | 20 | **50.0%** (10/20) | **45.0%** (9/20) | **12** | `T1021.005`, `T1039`, `T1072`, `T1087.001` (+8 more) |
| **E4** | E1, E2, E3, E5, E6, E7 | 10 | **60.0%** (6/10) | **60.0%** (6/10) | **4** | `T1078.003`, `T1205.001`, `T1543.002`, `T1599` |
| **E5** | E1, E2, E3, E4, E6, E7 | 2 | **0.0%** (0/2) | **0.0%** (0/2) | **3** | `T1040`, `T1528`, `T1550.001` |
| **E6** | E1, E2, E3, E4, E5, E7 | 14 | **57.1%** (8/14) | **50.0%** (7/14) | **7** | `T1010`, `T1070.003`, `T1115`, `T1204.002` (+3 more) |
| **E7** | E1, E2, E3, E4, E5, E6 | 12 | **91.7%** (11/12) | **83.3%** (10/12) | **8** | `T1078.002`, `T1095`, `T1110.001`, `T1133` (+4 more) |

### Slice: `collapsed` variant at `parent` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4, E5, E6, E7 | 18 | **72.2%** (13/18) | **66.7%** (12/18) | **10** | `T1069`, `T1120`, `T1124`, `T1218` (+6 more) |
| **E2** | E1, E3, E4, E5, E6, E7 | 19 | **78.9%** (15/19) | **84.2%** (16/19) | **6** | `T1005`, `T1046`, `T1074`, `T1547` (+2 more) |
| **E3** | E1, E2, E4, E5, E6, E7 | 20 | **65.0%** (13/20) | **55.0%** (11/20) | **10** | `T1021`, `T1039`, `T1072`, `T1213` (+6 more) |
| **E4** | E1, E2, E3, E5, E6, E7 | 10 | **80.0%** (8/10) | **80.0%** (8/10) | **3** | `T1205`, `T1543`, `T1599` |
| **E5** | E1, E2, E3, E4, E6, E7 | 2 | **0.0%** (0/2) | **0.0%** (0/2) | **3** | `T1040`, `T1528`, `T1550` |
| **E6** | E1, E2, E3, E4, E5, E7 | 14 | **64.3%** (9/14) | **64.3%** (9/14) | **5** | `T1010`, `T1115`, `T1204`, `T1222` (+1 more) |
| **E7** | E1, E2, E3, E4, E5, E6 | 12 | **91.7%** (11/12) | **91.7%** (11/12) | **7** | `T1095`, `T1110`, `T1133`, `T1210` (+3 more) |

### Slice: `raw` variant at `full` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4, E5, E6, E7 | 26 | **76.9%** (20/26) | **73.1%** (19/26) | **14** | `T1059.006`, `T1069`, `T1087`, `T1120` (+10 more) |
| **E2** | E1, E3, E4, E5, E6, E7 | 20 | **70.0%** (14/20) | **80.0%** (16/20) | **7** | `T1003`, `T1005`, `T1046`, `T1074.001` (+3 more) |
| **E3** | E1, E2, E4, E5, E6, E7 | 28 | **53.6%** (15/28) | **50.0%** (14/28) | **12** | `T1021.005`, `T1039`, `T1072`, `T1087.001` (+8 more) |
| **E4** | E1, E2, E3, E5, E6, E7 | 21 | **38.1%** (8/21) | **38.1%** (8/21) | **4** | `T1078.003`, `T1205.001`, `T1543.002`, `T1599` |
| **E5** | E1, E2, E3, E4, E6, E7 | 2 | **0.0%** (0/2) | **0.0%** (0/2) | **3** | `T1040`, `T1528`, `T1550.001` |
| **E6** | E1, E2, E3, E4, E5, E7 | 22 | **68.2%** (15/22) | **63.6%** (14/22) | **7** | `T1010`, `T1070.003`, `T1115`, `T1204.002` (+3 more) |
| **E7** | E1, E2, E3, E4, E5, E6 | 12 | **91.7%** (11/12) | **83.3%** (10/12) | **8** | `T1078.002`, `T1095`, `T1110.001`, `T1133` (+4 more) |

### Slice: `raw` variant at `parent` granularity

| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |
|---|---|---|---|---|---|---|
| **E1** | E2, E3, E4, E5, E6, E7 | 26 | **76.9%** (20/26) | **73.1%** (19/26) | **10** | `T1069`, `T1120`, `T1124`, `T1218` (+6 more) |
| **E2** | E1, E3, E4, E5, E6, E7 | 20 | **80.0%** (16/20) | **85.0%** (17/20) | **6** | `T1005`, `T1046`, `T1074`, `T1547` (+2 more) |
| **E3** | E1, E2, E4, E5, E6, E7 | 28 | **71.4%** (20/28) | **57.1%** (16/28) | **10** | `T1021`, `T1039`, `T1072`, `T1213` (+6 more) |
| **E4** | E1, E2, E3, E5, E6, E7 | 21 | **66.7%** (14/21) | **66.7%** (14/21) | **3** | `T1205`, `T1543`, `T1599` |
| **E5** | E1, E2, E3, E4, E6, E7 | 2 | **0.0%** (0/2) | **0.0%** (0/2) | **3** | `T1040`, `T1528`, `T1550` |
| **E6** | E1, E2, E3, E4, E5, E7 | 22 | **72.7%** (16/22) | **72.7%** (16/22) | **5** | `T1010`, `T1115`, `T1204`, `T1222` (+1 more) |
| **E7** | E1, E2, E3, E4, E5, E6 | 12 | **91.7%** (11/12) | **91.7%** (11/12) | **7** | `T1095`, `T1110`, `T1133`, `T1210` (+3 more) |

## 4. Evaluation Feasibility & Dataset Limitations

Empirical Limitations of CAM-LDS Next-Stage Modeling:
1. Dataset Sample Size: Across all four distinct attack campaigns, only 67 collapsed transition samples (95 raw transition samples) are available at full technique granularity.
2. Closed-Vocabulary Bounds (Full ID Granularity): Pooled over the 4 collapsed full-ID folds, 34 of 67 test samples (50.7%) have a current technique seen in training and 35 of 67 (52.2%) have a target technique seen in training. These values establish the empirical upper bounds on what any closed-vocabulary model can achieve on this dataset.
3. Closed-Vocabulary Bounds (Parent Granularity): For parent granularity, 41 of 67 test samples (61.2%) have a current technique seen in training and 39 of 67 (58.2%) have a target technique seen in training targets.
