# CAM-LDS New Episodes Intake Audit: Scenario 5, 6, 7

**Audit Timestamp**: `2026-10-14T07:36:56.150072+00:00`  
**Scope**: Read-only intake audit of three candidate archives (`scenario_5.zip`, `scenario_6_macro_binary.zip`, `scenario_7.zip`).  
**Purpose**: Decide, from empirical facts, whether these three episodes are fit to be added as episodes E5, E6, E7 in a future extended experiment.  

---

## Pre-Declared Decision Rules

- **D1**: MD5 of each new zip equals the Zenodo MD5.
- **D2**: Each new zip contains attacker/logs/attackmate.json, and the set of top-level keys matches the schema of E1-E4.
- **D3**: Every labeled step has a parseable timestamp under Stage 1 UTC assumption.
- **D4**: Every technique ID exists in ATT&CK Enterprise v16.1 reference.
- **D5**: Each new episode yields at least 8 collapsed transitions (below 8 is flagged 'small', not failed).
- **D6**: The new episodes have unique collapsed technique sequences compared to E1-E4.

---

## Step 1: Archive Hashes (7 Archives)

| Episode | Scenario | Archive File | MD5 | Expected Zenodo MD5 | MD5 Match | SHA-256 |
|:---|:---|:---|:---|:---|:---:|:---|
| E1 | `scenario_1_sudo_pam` | `scenario_1_sudo_pam.zip` | `e7e5bd19cda62a5bfb9a68525715cd78` | `e7e5bd19cda62a5bfb9a68525715cd78` | **TRUE** | `0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc` |
| E2 | `scenario_2_cron` | `scenario_2_cron.zip` | `c33aca73d6962414bd6c2c3f82b934c4` | `c33aca73d6962414bd6c2c3f82b934c4` | **TRUE** | `b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791` |
| E3 | `scenario_3_vnc_apt` | `scenario_3_vnc_apt.zip` | `bfd7e44cdb2d038a9deab800350e4b98` | `bfd7e44cdb2d038a9deab800350e4b98` | **TRUE** | `5c23b9d614689194f43cc844e4a25ed43568879ae83edc43df93336e0a33f911` |
| E4 | `scenario_4` | `scenario_4.zip` | `f1bf6ecd793c6c51f922ee43e33d7cf4` | `f1bf6ecd793c6c51f922ee43e33d7cf4` | **TRUE** | `a79fefbfeebd25b163e57f9ec7b9581f8e6f0abed2f2775fba45cf55a004b637` |
| E5 | `scenario_5` | `scenario_5.zip` | `c56fce722a7b714eba004d6fd6319879` | `c56fce722a7b714eba004d6fd6319879` | **TRUE** | `e54df7f4c2f8e12e374272544809cee42b2c7e68ac37d950934e4123364f7911` |
| E6 | `scenario_6_macro_binary` | `scenario_6_macro_binary.zip` | `aedd7c0b51700b16c04539f10784d5d4` | `aedd7c0b51700b16c04539f10784d5d4` | **TRUE** | `73a31bf763c5a65ed1a14bb5919151dbbf324563d4f8eaabb0c58d9c0f67f3b1` |
| E7 | `scenario_7` | `scenario_7.zip` | `88122133a82079e07e7ed1b782bc203f` | `88122133a82079e07e7ed1b782bc203f` | **TRUE** | `7f0ff0b5d939437b5ebad7f52eea69dc024775e5c73663c5b4ac7ba58f1b3a56` |

---

## Step 2: Archive Structure Comparison

| Episode | Scenario | Total Files | Uncompressed Size | Top-Level Folders | `attackmate.json` Path | Other Log Subdirectories |
|:---|:---|:---|:---|:---|:---|:---|
| E1 | `scenario_1_sudo_pam` | 10505 | 992.1 MB (1,040,315,329 B) | `scenario_1_sudo_pam` | `scenario_1_sudo_pam/attacker/logs/attackmate.json` | `attacker`, `corpdns`, `inetfw`, `videoserver`, `wazuh` |
| E2 | `scenario_2_cron` | 10459 | 664.9 MB (697,174,408 B) | `scenario_2_cron` | `scenario_2_cron/attacker/logs/attackmate.json` | `attacker`, `corpdns`, `inetfw`, `videoserver`, `wazuh` |
| E3 | `scenario_3_vnc_apt` | 14402 | 855.6 MB (897,111,825 B) | `scenario_3_vnc_apt` | `scenario_3_vnc_apt/attacker/logs/attackmate.json` | `attacker`, `corpdns`, `inetfw`, `linuxshare`, `reposerver`, `wazuh` |
| E4 | `scenario_4` | 14398 | 830.3 MB (870,580,648 B) | `scenario_4` | `scenario_4/attacker/logs/attackmate.json` | `attacker`, `corpdns`, `inetfw`, `linuxshare`, `reposerver`, `wazuh` |
| E5 | `scenario_5` | 12939 | 766.5 MB (803,737,946 B) | `scenario_5` | `scenario_5/attacker/logs/attackmate.json` | `adminpc`, `attacker`, `corpdns`, `inetfw`, `videoserver`, `wazuh` |
| E6 | `scenario_6_macro_binary` | 13033 | 922.2 MB (966,957,209 B) | `scenario_6_macro_binary` | `scenario_6_macro_binary/attacker/logs/attackmate.json` | `attacker`, `client`, `corpdns`, `inetfw`, `videoserver`, `wazuh` |
| E7 | `scenario_7` | 10399 | 600.6 MB (629,762,251 B) | `scenario_7` | `scenario_7/attacker/logs/attackmate.json` | `attacker`, `corpdns`, `docker`, `inetfw`, `wazuh` |

---

## Step 3: AttackMate Profile & Control Invariants Reproduction

### Stage 1 Control Reproduction (E1–E4)

| Metric | Control Expected | Actual Measured | Reproduction Status |
|:---|:---:|:---:|:---:|
| Total AttackMate Events | 190 | 190 | **MATCH** |
| Labeled Steps | 99 | 99 | **MATCH** |
| Distinct ATT&CK Techniques | 64 | 64 | **MATCH** |
| Raw Sequence Length | 99 | 99 | **MATCH** |
| Collapsed Sequence Length | 71 | 71 | **MATCH** |

### Full 7-Episode Profile Summary

| Metric | E1 | E2 | E3 | E4 | E5 | E6 | E7 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Scenario Name | `scenario_1_sudo_pam` | `scenario_2_cron` | `scenario_3_vnc_apt` | `scenario_4` | `scenario_5` | `scenario_6_macro_binary` | `scenario_7` |
| Total Steps | 38 | 29 | 77 | 46 | 7 | 51 | 26 |
| Labeled Steps | 27 | 21 | 29 | 22 | 3 | 23 | 13 |
| Unlabeled Steps | 11 | 8 | 48 | 24 | 4 | 28 | 13 |
| Multi-Technique Steps | 6 | 7 | 6 | 3 | 2 | 2 | 6 |
| Distinct Techniques (Full) | 31 | 21 | 23 | 10 | 4 | 12 | 22 |
| Distinct Techniques (Parent) | 28 | 20 | 22 | 10 | 4 | 12 | 22 |
| Distinct Tactic Strings | 9 | 9 | 9 | 7 | 4 | 6 | 12 |
| Missing/Unparseable Timestamps | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Duplicate Timestamp Ties | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Raw Sequence Length | 27 | 21 | 29 | 22 | 3 | 23 | 13 |
| Collapsed Sequence Length | 19 | 20 | 21 | 11 | 3 | 15 | 13 |
| Next-Technique Samples (Raw) | 26 | 20 | 28 | 21 | 2 | 22 | 12 |
| Next-Technique Samples (Collapsed) | 18 | 19 | 20 | 10 | 2 | 14 | 12 |
| First Timestamp | `2025-09-22T13:48:30.907163+00:00` | `2025-10-01T10:14:14.955559+00:00` | `2025-12-12T18:07:53.665927+00:00` | `2025-12-15T11:02:51.184731+00:00` | `2025-10-09T11:08:38.165282+00:00` | `2025-12-09T10:46:25.607355+00:00` | `2026-01-21T10:10:08.725780+00:00` |
| Last Timestamp | `2025-09-22T14:10:54.791711+00:00` | `2025-10-01T10:35:06.286635+00:00` | `2025-12-12T18:34:13.417531+00:00` | `2025-12-15T11:13:30.318178+00:00` | `2025-10-09T11:10:36.553295+00:00` | `2025-12-09T10:59:08.871964+00:00` | `2026-01-21T10:45:55.222690+00:00` |

---

## Step 4: ATT&CK v16.1 Reference Validity & Tactic Discrepancies

### Technique Validity (Rule D4)

- **E5 (`scenario_5`)**:
  - Distinct Techniques: 4
  - Valid Active v16.1: 4
  - Unknown IDs: None
  - Revoked IDs: None
  - Deprecated IDs: None
- **E6 (`scenario_6_macro_binary`)**:
  - Distinct Techniques: 12
  - Valid Active v16.1: 12
  - Unknown IDs: None
  - Revoked IDs: None
  - Deprecated IDs: None
- **E7 (`scenario_7`)**:
  - Distinct Techniques: 22
  - Valid Active v16.1: 22
  - Unknown IDs: None
  - Revoked IDs: None
  - Deprecated IDs: None

### Tactic Discrepancy Classification

Discrepancies are categorized under Stage 1 criteria:
- **Type (a)**: The dataset names a tactic that is **not in the official set** for that technique.
- **Type (b)**: The dataset gives a **strict subset** of the official tactics.

#### Episode E5 (`scenario_5`)
- Exact matches: 1
- Type (a) discrepancies: 0
- Type (b) discrepancies (strict subset): 2
  - `E5-S001`: Techniques `['T1040', 'T1557.002']` | Dataset tactics `['Credential Access', 'Discovery']` | Official tactics `['Collection', 'Credential Access', 'Discovery']`
  - `E5-S002`: Techniques `['T1040', 'T1528']` | Dataset tactics `['Credential Access']` | Official tactics `['Credential Access', 'Discovery']`

#### Episode E6 (`scenario_6_macro_binary`)
- Exact matches: 19
- Type (a) discrepancies: 0
- Type (b) discrepancies (strict subset): 4
  - `E6-S035`: Techniques `['T1546', 'T1574.008']` | Dataset tactics `['Defense Evasion', 'Persistence']` | Official tactics `['Defense Evasion', 'Persistence', 'Privilege Escalation']`
  - `E6-S043`: Techniques `['T1053.003']` | Dataset tactics `['Persistence']` | Official tactics `['Execution', 'Persistence', 'Privilege Escalation']`
  - `E6-S046`: Techniques `['T1053.003']` | Dataset tactics `['Persistence']` | Official tactics `['Execution', 'Persistence', 'Privilege Escalation']`
  - `E6-S048`: Techniques `['T1053.003']` | Dataset tactics `['Persistence']` | Official tactics `['Execution', 'Persistence', 'Privilege Escalation']`

#### Episode E7 (`scenario_7`)
- Exact matches: 11
- Type (a) discrepancies: 1
  - `E7-S025`: Techniques `['T1003.008', 'T1041']` | Dataset tactics `['Collection', 'Credential Access', 'Exfiltration']` | Official tactics `['Credential Access', 'Exfiltration']` | Extra tactic(s): `['Collection']`
- Type (b) discrepancies (strict subset): 1
  - `E7-S004`: Techniques `['T1078.002', 'T1110.001', 'T1133']` | Dataset tactics `['Initial Access']` | Official tactics `['Credential Access', 'Defense Evasion', 'Initial Access', 'Persistence', 'Privilege Escalation']`

---

## Step 5: Pure Counting Bounds (No Models)

> [!IMPORTANT]
> **Definitional Notice**: These counting bounds are empirical set intersections based strictly on closed vocabulary properties. They are **pure counting facts** and do not represent model inference, prediction results, or evidence of model accuracy.

### Quoted Definitions from `src/c4/evaluation.py`

```python
train_target_pool: set[str] = set()
for ep in train_eps:
    items = ep_sequences[ep][variant]
    for i in range(len(items) - 1):
        train_target_pool.update(markov._extract_tech_set(items[i + 1]))
...
if tgt & train_target_pool:
    ceiling_hits += 1
...
covered = sum(1 for s in fold_samples if preds['markov'][s['sample_id']]['status'] == 'ok')
```

### Counting Bounds by Experimental Design

#### (a) 4-episode control

| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1 | E2, E3, E4 | 18 | 7 | 38.89% | 7 | 38.89% |
| fold_2 | E2 | E1, E3, E4 | 19 | 13 | 68.42% | 14 | 73.68% |
| fold_3 | E3 | E1, E2, E4 | 20 | 8 | 40.00% | 8 | 40.00% |
| fold_4 | E4 | E1, E2, E3 | 10 | 6 | 60.00% | 6 | 60.00% |
| **POOLED** | — | — | **67** | **34** | **50.75%** | **35** | **52.24%** |

#### (b) 7-episode design

| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1 | E2, E3, E4, E5, E6, E7 | 18 | 13 | 72.22% | 12 | 66.67% |
| fold_2 | E2 | E1, E3, E4, E5, E6, E7 | 19 | 13 | 68.42% | 15 | 78.95% |
| fold_3 | E3 | E1, E2, E4, E5, E6, E7 | 20 | 10 | 50.00% | 9 | 45.00% |
| fold_4 | E4 | E1, E2, E3, E5, E6, E7 | 10 | 6 | 60.00% | 6 | 60.00% |
| fold_5 | E5 | E1, E2, E3, E4, E6, E7 | 2 | 0 | 0.00% | 0 | 0.00% |
| fold_6 | E6 | E1, E2, E3, E4, E5, E7 | 14 | 8 | 57.14% | 7 | 50.00% |
| fold_7 | E7 | E1, E2, E3, E4, E5, E6 | 12 | 11 | 91.67% | 10 | 83.33% |
| **POOLED** | — | — | **95** | **61** | **64.21%** | **59** | **62.11%** |

#### (c1) E1-E4 + E5

| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1 | E2, E3, E4, E5 | 18 | 7 | 38.89% | 7 | 38.89% |
| fold_2 | E2 | E1, E3, E4, E5 | 19 | 13 | 68.42% | 14 | 73.68% |
| fold_3 | E3 | E1, E2, E4, E5 | 20 | 8 | 40.00% | 8 | 40.00% |
| fold_4 | E4 | E1, E2, E3, E5 | 10 | 6 | 60.00% | 6 | 60.00% |
| fold_5 | E5 | E1, E2, E3, E4 | 2 | 0 | 0.00% | 0 | 0.00% |
| **POOLED** | — | — | **69** | **34** | **49.28%** | **35** | **50.72%** |

#### (c2) E1-E4 + E6

| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1 | E2, E3, E4, E6 | 18 | 7 | 38.89% | 7 | 38.89% |
| fold_2 | E2 | E1, E3, E4, E6 | 19 | 13 | 68.42% | 14 | 73.68% |
| fold_3 | E3 | E1, E2, E4, E6 | 20 | 9 | 45.00% | 9 | 45.00% |
| fold_4 | E4 | E1, E2, E3, E6 | 10 | 6 | 60.00% | 6 | 60.00% |
| fold_5 | E6 | E1, E2, E3, E4 | 14 | 8 | 57.14% | 7 | 50.00% |
| **POOLED** | — | — | **81** | **43** | **53.09%** | **43** | **53.09%** |

#### (c3) E1-E4 + E7

| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |
|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|
| fold_1 | E1 | E2, E3, E4, E7 | 18 | 13 | 72.22% | 12 | 66.67% |
| fold_2 | E2 | E1, E3, E4, E7 | 19 | 13 | 68.42% | 15 | 78.95% |
| fold_3 | E3 | E1, E2, E4, E7 | 20 | 10 | 50.00% | 9 | 45.00% |
| fold_4 | E4 | E1, E2, E3, E7 | 10 | 6 | 60.00% | 6 | 60.00% |
| fold_5 | E7 | E1, E2, E3, E4 | 12 | 11 | 91.67% | 10 | 83.33% |
| **POOLED** | — | — | **79** | **53** | **67.09%** | **52** | **65.82%** |

---

## Step 6: Decision Rules & Intake Eligibility Summary

| Rule ID | Evaluated Criterion | E5 (`scenario_5`) | E6 (`scenario_6_macro_binary`) | E7 (`scenario_7`) |
|:---|:---|:---:|:---:|:---:|
| **D1** | Zenodo MD5 Hash Match | **PASS** | **PASS** | **PASS** |
| **D2** | AttackMate Schema & Top Keys Match | **PASS** | **PASS** | **PASS** |
| **D3** | Parseable Timestamps (UTC assumption) | **PASS** | **PASS** | **PASS** |
| **D4** | Valid ATT&CK Enterprise v16.1 IDs | **PASS** | **PASS** | **PASS** |
| **D5** | >= 8 Collapsed Transitions (Threshold) | **FLAG (small)** (2) | **PASS** (14) | **PASS** (12) |
| **D6** | Sequence Uniqueness vs E1–E4 | **PASS** | **PASS** | **PASS** |

### Eligibility Verdicts

- **E5 (`scenario_5`)**: **ELIGIBLE** (Note: D5 is FLAG (small) with 2 transitions)
- **E6 (`scenario_6_macro_binary`)**: **ELIGIBLE**
- **E7 (`scenario_7`)**: **ELIGIBLE**

