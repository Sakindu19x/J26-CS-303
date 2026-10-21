# CAM-LDS Data Quality & Normalization Report

## 1. Episode Summary

| Episode | Scenario | Source Archive | Total Events | Labeled | Unlabeled | Multi-Tech Steps | Window Start (UTC) | Window End (UTC) |
|---|---|---|---|---|---|---|---|---|
| **E1** | `scenario_1_sudo_pam` | `scenario_1_sudo_pam.zip` | 38 | 27 | 11 | 6 | `2025-09-22T13:48:30.907163+00:00` | `2025-09-22T14:10:54.791711+00:00` |
| **E2** | `scenario_2_cron` | `scenario_2_cron.zip` | 29 | 21 | 8 | 7 | `2025-10-01T10:14:14.955559+00:00` | `2025-10-01T10:35:06.286635+00:00` |
| **E3** | `scenario_3_vnc_apt` | `scenario_3_vnc_apt.zip` | 77 | 29 | 48 | 6 | `2025-12-12T18:07:53.665927+00:00` | `2025-12-12T18:34:13.417531+00:00` |
| **E4** | `scenario_4` | `scenario_4.zip` | 46 | 22 | 24 | 3 | `2025-12-15T11:02:51.184731+00:00` | `2025-12-15T11:13:30.318178+00:00` |

## 2. Quality Checks & Cleaning Actions

- **Whitespace Fixes Applied (4):**
  - [E1 Step 36] Field `tactics`: `' Discovery'` -> `'Discovery'`
  - [E3 Step 5] Field `tactics`: `' Lateral Movement'` -> `'Lateral Movement'`
  - [E3 Step 38] Field `techniques`: `'T1564.001 '` -> `'T1564.001'`
  - [E3 Step 47] Field `techniques`: `'T1071.001 '` -> `'T1071.001'`

- **Malformed Records Recovered (1):**
  - [E1 Step 23] Malformed technique_name JSON key with embedded quotes/colons recovered: raw key `'technique_name:"Ingress Tool Transfer,Modify Authentication Process'`, raw val `'Pluggable Authentication Modules"'` -> recovered name: `Ingress Tool Transfer,Modify Authentication Process: Pluggable Authentication Modules`

- **Invalid Technique IDs (0):** None (all matched `^T\d{4}(\.\d{3})?$`)
- **Missing Timestamps (0):** None (all AttackMate steps have valid ISO timestamps)
- **Skipped Records (0):** None (100% of AttackMate steps preserved)

## 3. Wazuh Alert In-Window Enrichment

| Episode | Total Alerts in File | In Attack Window | Excluded (Before) | Excluded (After) | With Rule ID | With MITRE |
|---|---|---|---|---|---|---|
| **E1** | 15006 | **14355** | 487 | 164 | 14355 | 1542 |
| **E2** | 657 | **10** | 492 | 155 | 10 | 6 |
| **E3** | 661 | **110** | 454 | 97 | 110 | 0 |
| **E4** | 598 | **99** | 310 | 189 | 99 | 47 |

### Top 10 Wazuh Rules by Count per Episode (In-Window Alerts)

#### Episode E1 (Total in-window: 14355)

| Rank | Rule ID | Description | Count | Share (%) |
|---|---|---|---|---|
| 1 | `31101` | Web server 400 error code. | 11004 | 76.66% |
| 2 | `20101` | IDS event. | 869 | 6.05% |
| 3 | `31151` | Multiple web server 400 error codes from same source ip. | 846 | 5.89% |
| 4 | `31104` | Common web attack. | 324 | 2.26% |
| 5 | `31105` | XSS (Cross Site Scripting) attempt. | 259 | 1.8% |
| 6 | `86601` | Suricata: Alert - ET WEB_SERVER Script tag in URI Possible Cross Site Scripting Attempt | 217 | 1.51% |
| 7 | `86601` | Suricata: Alert - SURICATA HTTP unable to match response to request | 215 | 1.5% |
| 8 | `86601` | Suricata: Alert - ET WEB_SERVER /etc/passwd Detected in URI | 204 | 1.42% |
| 9 | `20100` | First time this IDS alert is generated. | 82 | 0.57% |
| 10 | `31153` | Multiple common web attacks from same source ip. | 35 | 0.24% |

#### Episode E2 (Total in-window: 10)

| Rank | Rule ID | Description | Count | Share (%) |
|---|---|---|---|---|
| 1 | `5501` | PAM: Login session opened. | 4 | 40.0% |
| 2 | `5715` | sshd: authentication success. | 2 | 20.0% |
| 3 | `86601` | Suricata: Alert - SURICATA STREAM excessive retransmissions | 2 | 20.0% |
| 4 | `20100` | First time this IDS alert is generated. | 2 | 20.0% |

#### Episode E3 (Total in-window: 110)

| Rank | Rule ID | Description | Count | Share (%) |
|---|---|---|---|---|
| 1 | `20101` | IDS event. | 46 | 41.82% |
| 2 | `86601` | Suricata: Alert - SURICATA STREAM pkt seen on wrong thread | 44 | 40.0% |
| 3 | `20100` | First time this IDS alert is generated. | 8 | 7.27% |
| 4 | `86601` | Suricata: Alert - ET POLICY GNU/Linux APT User-Agent Outbound likely related to package management | 6 | 5.45% |
| 5 | `80730` | Auditd: SELinux permission check. | 2 | 1.82% |
| 6 | `86601` | Suricata: Alert - ET HUNTING curl User-Agent to Dotted Quad | 2 | 1.82% |
| 7 | `86601` | Suricata: Alert - SURICATA STREAM excessive retransmissions | 1 | 0.91% |
| 8 | `86601` | Suricata: Alert - ET POLICY Executable and linking format (ELF) file download Over HTTP | 1 | 0.91% |

#### Episode E4 (Total in-window: 99)

| Rank | Rule ID | Description | Count | Share (%) |
|---|---|---|---|---|
| 1 | `5501` | PAM: Login session opened. | 24 | 24.24% |
| 2 | `5502` | PAM: Login session closed. | 17 | 17.17% |
| 3 | `86601` | Suricata: Alert - SURICATA STREAM pkt seen on wrong thread | 17 | 17.17% |
| 4 | `20101` | IDS event. | 17 | 17.17% |
| 5 | `5402` | Successful sudo to ROOT executed. | 14 | 14.14% |
| 6 | `5403` | First time user executed sudo. | 4 | 4.04% |
| 7 | `5715` | sshd: authentication success. | 3 | 3.03% |
| 8 | `5104` | Interface entered in promiscuous(sniffing) mode. | 2 | 2.02% |
| 9 | `80710` | Auditd: Device enables promiscuous mode. | 1 | 1.01% |

> [!NOTE]
> Wazuh alert MITRE mappings are detector-derived signature triggers and are kept strictly isolated in `data/processed/wazuh_alerts_normalized.csv` without merging into AttackMate ground-truth labels.

## 4. Field Provenance & C3 Integration Plan

| Field | Provenance in CAM-LDS | Source / Derivation | C3 Forensic Role |
|---|---|---|---|
| `event_id` | **Derived (deterministic)** | episode_id + 1-indexed step number (e.g. E1-S001) | Unique stable identifier for forensic timeline graph nodes |
| `episode_id` | **Observed / mapped** | CAM-LDS scenario archive mapping (E1..E4) | Episode isolation boundary (runs never combined) |
| `timestamp` | **Observed + UTC assumption** | attackmate.json start-datetime standardized to ISO 8601 UTC | Temporal anchor for chronological timeline ordering |
| `step_type, cmd, hostname, username` | **Observed** | attackmate.json parameters | Forensic event evidence and entity metadata |
| `techniques, tactics, technique_names` | **Observed (ground-truth label)** | attackmate.json parameters.metadata (cleaned) | Ground-truth labels for evaluation of next-stage prediction |
| `local_occurrence` | **Derived (forensic computation)** | Formula (derived): per-technique mapping {technique_id: cumulative 1-indexed occurrence count within episode up to this event}. For unlabeled events, null. | derived by C4 for CAM-LDS; the real C3 will supply its own value (format to be agreed) |
| `ioc, ioc_type` | **Missing in CAM-LDS (null)** | Not present in simulation logs | to be supplied by C3; format to be agreed with the C3 owner |
| `incident_stage` | **Missing in CAM-LDS (null)** | Not present in simulation logs | to be supplied by C3; format to be agreed with the C3 owner |
| `asset_criticality` | **Missing in CAM-LDS (null)** | Not present in simulation logs | to be supplied by C3; format to be agreed with the C3 owner |
| `cti_confidence, freshness` | **Missing in CAM-LDS (null)** | Not present in simulation logs | to be supplied by C3; format to be agreed with the C3 owner |
| `c3_threat_score, investigation_priority` | **Missing in CAM-LDS (null)** | Not present in simulation logs | to be supplied by C3; format to be agreed with the C3 owner |
