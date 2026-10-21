# C4 Stage 1 Acceptance Audit Report

**Audit Date:** 2026-10-13  
**Audit Target:** Component 4 (C4) Forensic Timeline Reconstruction & Dataset Preparation Pipeline  
**Dataset:** CAM-LDS (Cyber Attack Manifestations Log Data Set) — [Zenodo Record 18390560](https://zenodo.org/records/18390560)  
**Overall Verdict:** **PASS (All 15 Requirements Satisfied with Empirical Verification)**

---

## Executive Summary

Before any prediction modeling or evaluation began, an exhaustive audit across the entire C4 pipeline was conducted—spanning raw archive discovery, byte-level immutability, normalization integrity, timestamp ordering, episode isolation, label ground truth, C3 telemetry placeholders, sequence compression, prefix-target sample construction, LOEO cross-validation bounds, Streamlit dashboard rendering via `AppTest`, end-to-end reproducibility, and test suite coverage.

Zero fake data was generated. All counts, hashes, and metrics reported below are empirically verified from real code executions on the raw dataset. Reproducible defects identified during the audit were fixed in place, and every requirement is backed by concrete files, commands, and outputs.

---

## Acceptance Audit Matrix (R1 – R15)

| Requirement | Description | Status | Concrete Evidence / Real Verification Counts |
|---|---|:---:|---|
| **R1** | All 4 archives discovered and parsed according to real formats | **PASS** | 4 raw archives inspected in `data/raw/`:<br>• `scenario_1_sudo_pam.zip`: 10,505 members (9,070 regular files), 38 AttackMate steps<br>• `scenario_2_cron.zip`: 10,459 members (9,024 regular files), 29 AttackMate steps<br>• `scenario_3_vnc_apt.zip`: 14,402 members (12,538 regular files), 77 AttackMate steps<br>• `scenario_4.zip`: 14,398 members (12,534 regular files), 46 AttackMate steps |
| **R2** | Original archives unchanged | **PASS** | Hashes recorded in [raw_archive_hashes.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/raw_archive_hashes.json).<br>• **Baseline Notice:** Local SHA-256 hashes represent the local baseline recorded at audit start.<br>• **Published Integrity Check:** CAM-LDS archives are hosted on Zenodo Record 18390560. Zenodo publishes MD5 checksums for all archive files. Computed local MD5s match published Zenodo MD5s byte-for-byte across all 4 archives:<br>  - `scenario_1_sudo_pam.zip`: `e7e5bd19cda62a5bfb9a68525715cd78` (matches Zenodo MD5)<br>  - `scenario_2_cron.zip`: `c33aca73d6962414bd6c2c3f82b934c4` (matches Zenodo MD5)<br>  - `scenario_3_vnc_apt.zip`: `bfd7e44cdb2d038a9deab800350e4b98` (matches Zenodo MD5)<br>  - `scenario_4.zip`: `f1bf6ecd793c6c51f922ee43e33d7cf4` (matches Zenodo MD5)<br>Source code audit confirms zero write modes (`'w'`, `'a'`, `'x'`, `'+'`) targeting `data/raw/` (read-only enforcement in [data_loading.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/src/c4/data_loading.py)). Archive mtimes are `2026-08-28` across all 4 files. |
| **R3** | Normalized records keep source references & episode IDs | **PASS** | 190 total events across 4 episodes:<br>• Labeled counts: E1=27, E2=21, E3=29, E4=22 (total 99)<br>• Unlabeled counts: E1=11, E2=8, E3=48, E4=24 (total 91)<br>• Whitespace fixes applied: 4<br>• Malformed record recoveries: **1** (in **E1 Step 23**, where `technique_name` key had corrupted quotes/colon: `technique_name:"Ingress Tool Transfer,Modify Authentication Process`: `Pluggable Authentication Modules"` recovered to `Ingress Tool Transfer,Modify Authentication Process: Pluggable Authentication Modules`).<br>• Invalid technique IDs: 0<br>Source provenance preserved on 100% of events (`episode_id`, `scenario_id`, `source_archive`, `source_file`, `source_line_or_step_index`). |
| **R4** | Timestamp normalization & ordering | **PASS** | 100% of timestamps are UTC-aware ISO-8601 strings. 0 missing timestamps.<br>• **Raw Monotonicity Audit:** Raw AttackMate file order is strictly monotonic in E1, E2, and E4, but **non-monotonic in E3**, which exhibits 2 timestamp inversions:<br>  1. Step index 5 (`18:09:04.102559`) occurred 15.01s before Step index 4 (`18:09:19.112907`). Step 5 is a composite `type='loop'` step (`cmd='items(LISTA)'`, VNC password brute-forcing with techniques `T1110.001, T1021.005`).<br>  2. Step index 67 (`18:30:25.124334`) occurred 96.52s before Step index 66 (`18:32:01.643304`). Step 67 is a composite `type='include'` step (`cmd='include commands'`, importing `upgrade.yml`).<br>• **Chronological Reconstruction:** Reconstructed timelines and ATT&CK sequences sort strictly chronologically by `(timestamp, step_index)`, placing Step 5 before Step 4. |
| **R5** | Strict episode isolation | **PASS** | Zero cross-episode leakage detected across all 190 events, 4 reconstructed timelines, 4 sequences, and 324 generated transition samples. Every record references exactly one episode ID. |
| **R6** | ATT&CK ground truth integrity | **PASS** | ATT&CK labels sourced exclusively from AttackMate `parameters.metadata['techniques']` and `['tactics']`.<br>All 14,574 in-window Wazuh host alerts reside in [wazuh_alerts_normalized.csv](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/data/processed/wazuh_alerts_normalized.csv) and are explicitly flagged `is_detector_derived = True`. Zero detector tags appear in event ground-truth labels. |
| **R7** | Missing/invalid data reported, not fabricated | **PASS** | Columns always null for every event (190/190) in [normalized_events.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/data/processed/normalized_events.json):<br>• Exactly 8 columns: `asset_criticality`, `c3_threat_score`, `cti_confidence`, `freshness`, `incident_stage`, `investigation_priority`, `ioc`, `ioc_type`.<br>• Proposal C3 fields: `ioc`, `ioc_type`, `incident_stage`, `asset_criticality`, `cti_confidence`, `freshness`, `c3_threat_score`, and `investigation_priority` are 100% null. `local_occurrence` is present and derived by C4 on all 99 labeled events (and null on 91 unlabeled events).<br>• `alert_volume_pre_window`, `alert_volume_in_window`, `snort_alerts_count`, and `wazuh_alerts_count` do **NOT** exist as event columns in `normalized_events.json`; they are host/network log summary metrics from raw simulation logs and are not C3 fields. |
| **R8** | Timeline exports contain expected fields & IDs | **PASS** | Both [attack_timelines.csv](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/data/processed/attack_timelines.csv) and [attack_timelines.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/data/processed/attack_timelines.json) preserve `event_id`, `episode_id`, `timestamp`, `techniques`, `tactics`, and `label_status` with 0 null values for IDs. Tested in [test_dashboard.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/tests/test_dashboard.py). |
| **R9** | ATT&CK Sequence construction & compression | **PASS** | Sequences constructed strictly from labeled events (91 unlabeled steps excluded):<br>• Raw lengths: E1=27, E2=21, E3=29, E4=22 (total 99)<br>• Collapsed lengths: E1=19, E2=20, E3=21, E4=11 (total 71)<br>• `unlabeled_steps_skipped_before` and `unlabeled_steps_skipped_between` accurately track merged gaps. |
| **R10** | Prefix-target sample alignment | **PASS** | Generated 324 total samples across the 2x2 grid (collapsed/raw × full/parent):<br>• 67 collapsed full-ID samples, 95 raw full-ID samples.<br>• Parent technique granularity mapped accurately via MITRE reference.<br>• Prefix/target alignment independently verified on 10 randomly sampled instances by direct recomputation from sequences. 0 cross-episode samples. |
| **R11** | Independent LOEO coverage bound recomputation | **PASS** | Independently recomputed pooled leave-one-episode-out coverage bounds matching [sequence_statistics.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/sequence_statistics.json):<br>• Collapsed full ID: 34 / 67 usable sources (50.7%), 35 / 67 reachable targets (52.2%)<br>• Collapsed parent ID: 41 / 67 usable sources (61.2%), 39 / 67 reachable targets (58.2%)<br>Zero test-episode data used in training partitions. |
| **R12** | Streamlit dashboard headless validation | **PASS** | Automated validation performed using `streamlit.testing.v1.AppTest` in [test_dashboard.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/tests/test_dashboard.py):<br>• All 9 sections render for each of E1, E2, E3, and E4 without unhandled exceptions.<br>• Filters (host, technique, tactic, label) and CSV/JSON export utilities verified.<br>• *Environment notice: Programmatic AppTest runner used without interactive browser session.* |
| **R13** | Reproducibility from scratch | **PASS** | Deleted `data/processed/` and generated reports, reran documented pipeline scripts in order ([run_normalization.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/scripts/run_normalization.py), [run_timeline_pipeline.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/scripts/run_timeline_pipeline.py), [run_samples_and_stats.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/scripts/run_samples_and_stats.py)).<br>Removed dynamic/hard-coded `generated_at` timestamps to ensure natural bit-level stability.<br>All 6 processed JSON files and 4 report JSON files match baseline SHA-256 hashes 100% across consecutive runs.<br>[dataset_inventory.md](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/dataset_inventory.md), [dataset_inventory.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/dataset_inventory.json), and [raw_archive_hashes.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/raw_archive_hashes.json) are preserved. |
| **R14** | README instructions verified | **PASS** | Tested in a brand-new temporary virtual environment (`C:\Users\Lenovo\AppData\Local\Temp\c4_test_venv`):<br>• `pip install -r requirements.txt` (Exit code 0)<br>• `pip install -e .` (Exit code 0)<br>• `pip install pytest` (Exit code 0)<br>• `python scripts/run_normalization.py` (Exit code 0)<br>• `python scripts/run_timeline_pipeline.py` (Exit code 0)<br>• `python scripts/run_samples_and_stats.py` (Exit code 0)<br>• `pytest -v` (**38 passed in 3.14s**). |
| **R15** | Automated test coverage mapping | **PASS** | 38 automated tests in `tests/` covering normal input, malformed records, missing values, timestamp ties, duplicate events, and episode boundaries.<br>Full pytest run: **38 passed in 3.54s**, 0 failed, 0 skipped. |

---

## Reproducible Defects Identified & Fixed

During this audit, four specific defects were identified and resolved:

1. **MITRE Reference JSON Dump Non-Determinism (R13):**
   - *Defect:* `technique_tactic_reference.json` serialized keys in arbitrary order depending on runtime dictionary memory layout, causing SHA-256 hash drift when regenerated.
   - *Fix:* Enforced `sort_keys=True` in `json.dump` within [mitre_reference.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/src/c4/mitre_reference.py).

2. **Report Generation Timestamp Drift (R13):**
   - *Defect:* Reports previously embedded dynamic `datetime.now()` timestamps (or risked artificial hard-coded timestamps), causing hash mismatches across independent pipeline reruns.
   - *Fix:* Omitted the optional `generated_at` timestamp from generated JSON and Markdown reports, producing natural, byte-identical deterministic files on regeneration.

3. **Packaging & Pytest Resolution (R14, R15):**
   - *Defect:* Pytest test discovery relied on manual `sys.path.insert`, and editable installation was unavailable due to a missing `pyproject.toml`.
   - *Fix:* Created [pyproject.toml](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/pyproject.toml) with standard setuptools build metadata and added `pythonpath = src` to [pytest.ini](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/pytest.ini).

4. **Automated Dashboard Verification Gap (R12, R15):**
   - *Defect:* Streamlit dashboard rendering across all 4 episodes was previously only run manually in a scratch script rather than integrated into automated test execution.
   - *Fix:* Added `test_dashboard_renders_all_episodes_via_apptest()` to [test_dashboard.py](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/tests/test_dashboard.py), programmatically exercising episode switching and section rendering for E1..E4.

---

## ATT&CK Enterprise Version Empirical Comparison

As audited in [attack_version_comparison.md](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/attack_version_comparison.md) and [attack_version_comparison.json](file:///c:/Users/Lenovo/OneDrive%20-%20EGUARDIAN/Documents/Dataset/c4/reports/attack_version_comparison.json), the baseline reference (v16.1) was compared directly against the newest available STIX collection (v19.2, 53.8 MB):

- **Baseline:** Enterprise ATT&CK **v16.1** (`https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-16.1.json`, 799 techniques).
- **Newest:** Enterprise ATT&CK **v19.2** (`https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-19.2.json`, 858 techniques).
- **Finding:** The Zenodo record text (record 18390560) was checked and does not state an explicit MITRE ATT&CK version. The published CAM-LDS research paper itself was not inspected locally, so no claim is made regarding what the paper states. In v19.2, MITRE ATT&CK introduced the *Stealth* and *Defense Impairment* tactics, reorganizing *Defense Evasion*. Evaluating CAM-LDS against v19.2 increases tactic discrepancies from 8 to 22 because CAM-LDS labels use the classic Defense Evasion tactic. All 8 baseline discrepant events (`E2-S016`, `E2-S017`, `E2-S024`, `E4-S003`, `E4-S007`, `E4-S009`, `E4-S041`, `E4-S043`) are strictly preserved. Maintaining v16.1 as the baseline reference is therefore justified on computed alignment (8 discrepancies under v16.1 vs 22 under v19.2).

---

## Known Project & Dataset Limitations

1. **Small Dataset Sample Size:**  
   CAM-LDS comprises only 4 attack scenarios (`scenario_1_sudo_pam`, `scenario_2_cron`, `scenario_3_vnc_apt`, `scenario_4`), generating 190 total events and only 67 collapsed transition samples (95 raw transition samples) at full technique granularity.
2. **Single Run per Archive:**  
   Each raw archive captures exactly one campaign execution without replication. It is impossible to calculate intra-scenario variance or assess stochastic variations in attacker execution.
3. **Attack Window UTC Assumption:**  
   The UTC timezone assumption is verified against SSH authentication records in host `audit.log` files (`videoserver/logs/log/audit/audit.log` for E1 and `inetfw/logs/log/audit/audit.log` for E4, where epoch timestamps corroborate AttackMate execution timing). For E2 and E3, host clocks are internally consistent and set to `Etc/UTC`, but lack independent external corroboration.
4. **Absence of Real C3 Telemetry:**  
   The 8 proposal C3 fields (`ioc`, `ioc_type`, `incident_stage`, `asset_criticality`, `cti_confidence`, `freshness`, `c3_threat_score`, `investigation_priority`) are null across all 190 events in CAM-LDS. Only `local_occurrence` is populated (derived by C4 for labeled events).
5. **MITRE ATT&CK Tactic Discrepancies:**  
   8 steps in CAM-LDS exhibit discrepancies between AttackMate recorded tactics and official MITRE ATT&CK v16.1 enterprise mappings. For example:
   - `E2-S024`: Technique `T1003.008` (OS Credential Dumping: /etc/passwd and /etc/shadow) is recorded under tactic **Discovery**, whereas official ATT&CK classifies it strictly under **Credential Access**.
   - `E4-S007`: Technique `T1078.003` (Local Accounts) is recorded under tactic **Lateral Movement**, whereas official ATT&CK maps it to **Defense Evasion**, **Initial Access**, **Persistence**, and **Privilege Escalation**.
6. **Closed-Vocabulary Reachability Bounds:**  
   Because attack techniques diverge significantly across scenarios, pooled leave-one-episode-out coverage indicates that only **50.7% (34/67)** of test samples have a current technique seen during training, and only **52.2% (35/67)** have a target technique seen during training at full technique ID granularity. This represents a fundamental upper bound on closed-vocabulary prediction models on this dataset.

---

## Automated Test Coverage Mapping (R15)

The test suite contains 38 unit and regression tests in `tests/`:

- **Normal Input Processing:**
  - `test_basic.py::test_reads_synthetic_zip_without_modifying`
  - `test_normalization.py::test_timestamp_parsing_and_utc_assumption`
  - `test_timeline_and_sequences.py::test_real_archives_regression`
  - `test_dashboard.py::test_load_dashboard_data_success`
- **Malformed Record Handling:**
  - `test_normalization.py::test_malformed_key_case` (handles `technique_name` key formatting in E1 Step 23)
  - `test_basic.py::test_unreadable_archive` (handles corrupted zip headers)
- **Missing Value & Edge-Case Handling:**
  - `test_normalization.py::test_invalid_technique_id`
  - `test_basic.py::test_missing_archives_reported`
  - `test_normalization.py::test_timestamp_tie_ordering_and_missing_last`
  - `test_dashboard.py::test_export_empty_timeline`
  - `test_dashboard.py::test_charts_empty_timeline_figure`
- **Timestamp Ties & Sequence Ordering:**
  - `test_normalization.py::test_timestamp_tie_ordering_and_missing_last`
  - `test_timeline_and_sequences.py::test_timeline_ordering_ties_and_missing_timestamps`
- **Duplicate Events & Identifier Stability:**
  - `test_normalization.py::test_stable_event_ids_across_runs`
  - `test_timeline_and_sequences.py::test_pipeline_hash_stability_double_run`
  - `test_timeline_and_sequences.py::test_real_archives_regression`
- **Episode Boundary Isolation:**
  - `test_normalization.py::test_episode_separation`
  - `test_timeline_and_sequences.py::test_episode_manager_synthetic`
  - `test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence`
  - `test_samples_and_stats.py::test_no_cross_episode_samples_synthetic`
  - `test_samples_and_stats.py::test_fold_construction_never_leaks_test_episode_synthetic`
- **Dashboard UI & Component Rendering:**
  - `test_dashboard.py::test_dashboard_renders_all_episodes_via_apptest` (E1, E2, E3, E4)
  - `test_dashboard.py::test_export_timeline_to_csv_preserves_ids`
  - `test_dashboard.py::test_export_timeline_to_json_preserves_ids`
  - `test_dashboard.py::test_timeline_filters_empty_and_invalid`

---

## Pytest Suite Execution Output

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\c4
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collecting ... collected 38 items

tests/test_basic.py::test_missing_archives_reported PASSED               [  2%]
tests/test_basic.py::test_reads_synthetic_zip_without_modifying PASSED   [  5%]
tests/test_basic.py::test_unreadable_archive PASSED                      [  7%]
tests/test_basic.py::test_runs_not_merged_and_unlabeled_skipped PASSED   [ 10%]
tests/test_dashboard.py::test_load_dashboard_data_success PASSED         [ 13%]
tests/test_dashboard.py::test_export_timeline_to_csv_preserves_ids PASSED [ 15%]
tests/test_dashboard.py::test_export_timeline_to_json_preserves_ids PASSED [ 18%]
tests/test_dashboard.py::test_export_empty_timeline PASSED               [ 21%]
tests/test_dashboard.py::test_charts_empty_timeline_figure PASSED        [ 23%]
tests/test_dashboard.py::test_charts_with_synthetic_timeline PASSED      [ 26%]
tests/test_dashboard.py::test_timeline_filters_empty_and_invalid PASSED  [ 28%]
tests/test_dashboard.py::test_dashboard_renders_all_episodes_via_apptest PASSED [ 31%]
tests/test_normalization.py::test_timestamp_parsing_and_utc_assumption PASSED [ 34%]
tests/test_normalization.py::test_whitespace_cleaning PASSED             [ 36%]
tests/test_normalization.py::test_invalid_technique_id PASSED            [ 39%]
tests/test_normalization.py::test_multi_technique_step_kept_as_one_event PASSED [ 42%]
tests/test_normalization.py::test_unlabeled_step_preserved PASSED        [ 44%]
tests/test_normalization.py::test_episode_separation PASSED              [ 47%]
tests/test_normalization.py::test_timestamp_tie_ordering_and_missing_last PASSED [ 50%]
tests/test_normalization.py::test_stable_event_ids_across_runs PASSED    [ 52%]
tests/test_normalization.py::test_malformed_key_case PASSED              [ 55%]
tests/test_samples_and_stats.py::test_prefix_target_alignment_synthetic PASSED [ 57%]
tests/test_samples_and_stats.py::test_no_cross_episode_samples_synthetic PASSED [ 60%]
tests/test_samples_and_stats.py::test_parent_granularity_mapping_synthetic PASSED [ 63%]
tests/test_samples_and_stats.py::test_multi_technique_inputs_targets_kept_as_sets_synthetic PASSED [ 65%]
tests/test_samples_and_stats.py::test_fold_construction_never_leaks_test_episode_synthetic PASSED [ 68%]
tests/test_samples_and_stats.py::test_collapsed_gaps_list_synthetic PASSED [ 71%]
tests/test_samples_and_stats.py::test_real_data_total_sample_counts PASSED [ 73%]
tests/test_timeline_and_sequences.py::test_real_archives_regression PASSED [ 76%]
tests/test_timeline_and_sequences.py::test_pipeline_hash_stability_double_run PASSED [ 78%]
tests/test_timeline_and_sequences.py::test_episode_manager_synthetic PASSED [ 81%]
tests/test_timeline_and_sequences.py::test_timeline_ordering_ties_and_missing_timestamps PASSED [ 84%]
tests/test_timeline_and_sequences.py::test_unlabeled_steps_in_timeline_and_label_status PASSED [ 86%]
tests/test_timeline_and_sequences.py::test_timeline_filters_including_empty_and_invalid PASSED [ 89%]
tests/test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence PASSED [ 92%]
tests/test_timeline_and_sequences.py::test_unlabeled_steps_excluded_from_sequences PASSED [ 94%]
tests/test_timeline_and_sequences.py::test_collapsed_variant_merges_only_identical_consecutive_sets PASSED [ 97%]
tests/test_timeline_and_sequences.py::test_unlabeled_steps_skipped_before_tracking PASSED [100%]

============================= 38 passed in 3.54s ==============================
```
