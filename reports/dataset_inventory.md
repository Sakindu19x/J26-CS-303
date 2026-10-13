# Dataset Inventory (CAM-LDS)

Generated: 2026-10-13T06:50:06.223133+00:00
Raw dir: `C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\c4\data\raw` (read-only)

## 1. Archive status

| Archive | Present | Readable | Files | Error |
|---|---|---|---|---|
| scenario_1_sudo_pam.zip | True | True | 9070 |  |
| scenario_2_cron.zip | True | True | 9024 |  |
| scenario_3_vnc_apt.zip | True | True | 12538 |  |
| scenario_4.zip | True | True | 12534 |  |

Issues: none

## 2. Scenario comparison

| Metric | scenario_1_sudo_pam | scenario_2_cron | scenario_3_vnc_apt | scenario_4 |
|---|---|---|---|---|
| attackmate steps | 38 | 29 | 77 | 46 |
| labeled / unlabeled | 27 / 11 | 21 / 8 | 29 / 48 | 22 / 24 |
| steps with >1 technique | 6 | 7 | 6 | 3 |
| attackmate time range (no tz) | 2025-09-22T13:48:30.907163 .. 2025-09-22T14:10:54.791711 | 2025-10-01T10:14:14.955559 .. 2025-10-01T10:35:06.286635 | 2025-12-12T18:07:53.665927 .. 2025-12-12T18:34:13.417531 | 2025-12-15T11:02:51.184731 .. 2025-12-15T11:13:30.318178 |
| duration (s) | 1343.9 | 1251.3 | 1579.8 | 639.1 |
| distinct techniques (cleaned) | 31 | 21 | 23 | 10 |
| distinct tactics (cleaned) | 9 | 9 | 9 | 7 |
| hosts | attacker, corpdns, inetfw, videoserver, wazuh | attacker, corpdns, inetfw, videoserver, wazuh | attacker, corpdns, inetfw, linuxshare, reposerver, wazuh | attacker, corpdns, inetfw, linuxshare, reposerver, wazuh |
| Wazuh alerts.json (size B) | 14860021 | 1219551 | 945482 | 857598 |
| Wazuh alerts / with rule.id / with MITRE | 15006 / 15006 / 1654 | 657 / 657 / 117 | 661 / 661 / 64 | 598 / 598 / 103 |
| Wazuh alerts inside attackmate window (UTC reading) | 14355 | 10 | 110 | 99 |
| timestamp reading | consistent with UTC | unclear | unclear | consistent with UTC |

## 3. scenario_1_sudo_pam

- attackmate: `['attacker/logs/attackmate.json']`; unparseable lines: 0
- step types: {'shell': 5, 'sleep': 5, 'msf-module': 1, 'msf-session': 20, 'ssh': 7}
- distinct techniques (31): ['T1003.008', 'T1007', 'T1016', 'T1033', 'T1049', 'T1057', 'T1059', 'T1059.006', 'T1069', 'T1070.004', 'T1082', 'T1083', 'T1087', 'T1105', 'T1120', 'T1124', 'T1190', 'T1201', 'T1218', 'T1497.001', 'T1518', 'T1548.003', 'T1556.003', 'T1590.002', 'T1591', 'T1592.002', 'T1595', 'T1595.002', 'T1595.003', 'T1614', 'T1615']
- distinct tactics (9): ['Command and Control', 'Credential Access', 'Defense Evasion', 'Discovery', 'Execution', 'Initial Access', 'Persistence', 'Privilege Escalation', 'Reconnaissance']
- unlabeled breakdown: {'metadata_null': 11}
- metadata keys: {'techniques': 27, 'tactics': 27, 'technique_name': 26, 'technique_name:"Ingress Tool Transfer,Modify Authentication Process': 1}
- metadata key anomalies (non-identifier characters): ['technique_name:"Ingress Tool Transfer,Modify Authentication Process']

### Log sources per host (exact path patterns, non-empty files)

| Host | Sources (files / bytes) |
|---|---|
| attacker | attackmate.json: 1 / 22387; syslog: 1 / 193877; journal: 14 / 117440512; auth.log: 1 / 26086 |
| corpdns | syslog: 1 / 980778; journal: 4 / 58720256; auth.log: 1 / 3855; collectd.log: 1 / 13353253; audit.log: 1 / 4521031 |
| inetfw | syslog: 1 / 354111; journal: 4 / 58720256; auth.log: 1 / 3958; collectd.log: 1 / 5880623; audit.log: 1 / 6452680 |
| videoserver | syslog: 1 / 517632; journal: 25 / 276824064; auth.log: 1 / 13704; collectd.log: 1 / 8787426; audit.log: 1 / 19233691 |
| wazuh | wazuh alerts: 6 / 55876240 |

### Label analysis

- steps with more than one technique: **6**
- real examples:
```json
{"step_index": 1, "type": "shell", "cmd": "dnsenum -f /usr/local/share/SecLists/Discovery/DNS/subdomains-top1mill", "metadata": {"techniques": "T1590.002,T1591", "tactics": "Reconnaissance", "technique_name": "Gather Victim Network Information: DNS,Gather Victim Org Information"}, "ids": ["T1590.002", "T1591"]}
{"step_index": 2, "type": "shell", "cmd": "sudo nmap -O -sT --top-ports 100 video.attackbed.com", "metadata": {"techniques": "T1595,T1592.002", "tactics": "Reconnaissance", "technique_name": "Active Scanning,Gather Victim Host Information: Software"}, "ids": ["T1595", "T1592.002"]}
{"step_index": 7, "type": "msf-module", "cmd": "exploit/unix/webapp/zoneminder_snapshots", "metadata": {"techniques": "T1190,T1059.006", "tactics": "Initial Access", "technique_name": "Exploit Public-Facing Application,Command and Scripting Interpreter: Python"}, "ids": ["T1190", "T1059.006"]}
```
- strictly adjacent steps (both labeled) with identical technique set: **7**
- consecutive labeled steps (unlabeled skipped) with identical technique set: **8**
- consecutive labeled steps sharing at least one technique: 10

Real `parameters.metadata` of 3 labeled steps:
```json
{"step_index": 1, "type": "shell", "cmd": "dnsenum -f /usr/local/share/SecLists/Discovery/DNS/subdomains-top1mill", "metadata": {"techniques": "T1590.002,T1591", "tactics": "Reconnaissance", "technique_name": "Gather Victim Network Information: DNS,Gather Victim Org Information"}}
{"step_index": 2, "type": "shell", "cmd": "sudo nmap -O -sT --top-ports 100 video.attackbed.com", "metadata": {"techniques": "T1595,T1592.002", "tactics": "Reconnaissance", "technique_name": "Active Scanning,Gather Victim Host Information: Software"}}
{"step_index": 3, "type": "shell", "cmd": "nikto -host video.attackbed.com", "metadata": {"techniques": "T1595.002", "tactics": "Reconnaissance", "technique_name": "Active Scanning: Vulnerability Scanning"}}
```
Real `parameters.metadata` of 3 unlabeled steps:
```json
{"step_index": 0, "type": "shell", "cmd": "echo \"Target:  ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC2341xHMhWhD+62pj", "metadata": null}
{"step_index": 4, "type": "sleep", "cmd": "sleep", "metadata": null}
{"step_index": 6, "type": "sleep", "cmd": "sleep", "metadata": null}
```

Values needing whitespace / case cleaning:

- step 36 `tactics`: raw `'Defense Evasion, Discovery'` -> problems ' Discovery'->'Discovery' ['whitespace']
- tactic spellings differing only by case: none

Ordered cleaned technique sequence (labeled steps only; `+` joins several techniques in one step):

`T1590.002+T1591 -> T1595+T1592.002 -> T1595.002 -> T1595.003 -> T1190+T1059.006 -> T1105 -> T1059 -> T1059 -> T1059 -> T1059 -> T1059 -> T1059 -> T1087+T1083+T1201+T1069+T1057+T1518+T1082+T1614+T1016+T1049+T1033+T1007+T1615 -> T1033 -> T1548.003 -> T1548.003 -> T1033 -> T1105+T1556.003 -> T1218+T1556.003 -> T1070.004 -> T1070.004 -> T1033 -> T1003.008 -> T1120 -> T1120 -> T1124 -> T1497.001`

### Wazuh files (wazuh host, exact archive paths)

| Path | Size | CRC32 |
|---|---|---|
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json` | 1052664 | c949b261 |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.log` | 1454934 | 374faa23 |
| `wazuh/logs/alerts/2025/Sep/ossec-alerts-22.json` | 14860021 | c65191ce |
| `wazuh/logs/alerts/2025/Sep/ossec-alerts-22.log` | 11824300 | 8aead1ae |
| `wazuh/logs/alerts/alerts.json` | 14860021 | c65191ce |
| `wazuh/logs/alerts/alerts.log` | 11824300 | 8aead1ae |

- byte-identical groups (same size and CRC32): [['wazuh/logs/alerts/2025/Sep/ossec-alerts-22.json', 'wazuh/logs/alerts/alerts.json'], ['wazuh/logs/alerts/2025/Sep/ossec-alerts-22.log', 'wazuh/logs/alerts/alerts.log']]
- archives.json / ossec.log / api.log / cluster.log present: none found

- `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json`: 500 alerts; rule.id 500; MITRE ids on 3; 11 rule ids; time 2025-06-02T10:08:06.498000+00:00 .. 2025-06-02T10:09:26.544000+00:00; agents {'atb-wazuh-image-2025-06-02t10-01-35z': 500}
  - in attackmate window (UTC reading): 0 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []
- `wazuh/logs/alerts/2025/Sep/ossec-alerts-22.json`: 15006 alerts; rule.id 15006; MITRE ids on 1654; 42 rule ids; time 2025-09-22T13:34:24.087000+00:00 .. 2025-09-22T15:32:27.527000+00:00; agents {'wazuh': 13, 'inetfw': 2115, 'videoserver': 12878}
  - in attackmate window (UTC reading): 14355 alerts, 1542 with MITRE; MITRE ids in window ['T1021', 'T1055', 'T1057', 'T1059', 'T1059.007', 'T1078', 'T1083', 'T1190', 'T1210', 'T1499', 'T1548.003', 'T1595.002']; also in attackmate labels: ['T1057', 'T1059', 'T1083', 'T1190', 'T1548.003', 'T1595.002']
- `wazuh/logs/alerts/alerts.json`: 15006 alerts; rule.id 15006; MITRE ids on 1654; 42 rule ids; time 2025-09-22T13:34:24.087000+00:00 .. 2025-09-22T15:32:27.527000+00:00; agents {'wazuh': 13, 'inetfw': 2115, 'videoserver': 12878}
  - in attackmate window (UTC reading): 14355 alerts, 1542 with MITRE; MITRE ids in window ['T1021', 'T1055', 'T1057', 'T1059', 'T1059.007', 'T1078', 'T1083', 'T1190', 'T1210', 'T1499', 'T1548.003', 'T1595.002']; also in attackmate labels: ['T1057', 'T1059', 'T1083', 'T1190', 'T1548.003', 'T1595.002']

Real Wazuh alert fields (example with MITRE):
```json
{"timestamp": "2025-06-02T10:08:10.507+0000", "agent": "atb-wazuh-image-2025-06-02t10-01-35z", "rule": {"id": "5403", "level": 4, "description": "First time user executed sudo.", "mitre": {"id": ["T1548.003"], "tactic": ["Privilege Escalation", "Defense Evasion"], "technique": ["Sudo and Sudo Caching"]}}}
```

### Timestamp formats (real samples)

- **journal**: Binary systemd journal (signature LPKSHHRH). Header realtime fields are microseconds since the Unix epoch (UTC by systemd definition). Per-entry text fields were not decoded (UNVERIFIED).
  - `videoserver:videoserver/logs/log/journal/9729f3e6f1d545e7a1cf4cffbc93efda/system.journal`: first entries [{'seqnum': 41545, 'realtime_utc': '2025-09-22T13:56:08.185627+00:00'}, {'seqnum': 41546, 'realtime_utc': '2025-09-22T13:56:08.193294+00:00'}, {'seqnum': 41547, 'realtime_utc': '2025-09-22T13:56:08.193331+00:00'}]; message strings ['PATH item=0 name="/usr/bin/grep" inode=1664 dev=fe:01 mode=0100755 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 cap_fe=0 cap_f', 'PATH item=1 name="/usr/bin/grep" inode=1664 dev=fe:01 mode=0100755 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 cap_fe=0 cap_f', 'PATH item=2 name="/lib64/ld-linux-x86-64.so.2" inode=1964 dev=fe:01 mode=0100755 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 ']
  - `inetfw:inetfw/logs/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7/system.journal`: first entries [{'seqnum': 33938, 'realtime_utc': '2025-09-22T13:35:15.559568+00:00'}, {'seqnum': 33939, 'realtime_utc': '2025-09-22T13:35:15.584608+00:00'}, {'seqnum': 33940, 'realtime_utc': '2025-09-22T13:35:15.584638+00:00'}]; message strings ['SOCKADDR saddr=02000035C02A02020000000000000000', 'PROCTITLE proctitle="/var/ossec/bin/wazuh-modulesd"', 'SYSCALL arch=c000003e syscall=42 success=yes exit=0 a0=4 a1=7fc050705354 a2=10 a3=7ffd3946d3f4 items=0 ppid=2570 pid=3119 auid=4294967295 ui']
  - videoserver: 25 files, header range 2025-06-18T13:51:38.061652+00:00 .. 2025-09-22T15:30:37.813694+00:00
  - inetfw: 4 files, header range 2025-09-17T13:07:40.426054+00:00 .. 2025-09-22T14:20:19.782155+00:00
  - attacker: 14 files, header range 2025-05-19T14:39:23.888323+00:00 .. 2025-09-22T15:32:39.000030+00:00
  - corpdns: 4 files, header range 2025-09-17T11:16:28.587737+00:00 .. 2025-09-22T15:31:42.406760+00:00
- **audit.log**: msg=audit(<unix epoch seconds.millis>:<serial>): epoch time => no timezone ambiguity (UTC).
  - videoserver: `type=SYSCALL msg=audit(1750254698.047:2729): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55fc157739a0 a2=241 a3=1b6 items=2 ppid=39616 pid=39629 auid=1000`  ...  `type=PROCTITLE msg=audit(1758555037.808:15626): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-06-18T13:51:38.047000+00:00 .. 2025-09-22T15:30:37.808000+00:00
  - inetfw: `type=PATH msg=audit(1758114460.424:2211): item=0 name="/var/log/" inode=80887 dev=fc:01 mode=040775 ouid=0 ogid=111 rdev=00:00 nametype=PARENT cap_fp=0 cap_fi=0 cap_fe=0 `  ...  `type=PROCTITLE msg=audit(1758550819.776:6912): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T13:07:18.688000+00:00 .. 2025-09-22T14:20:19.776000+00:00
  - corpdns: `type=SYSCALL msg=audit(1758107788.584:2473): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55ae93e00490 a2=241 a3=1b6 items=2 ppid=14993 pid=15006 auid=1000`  ...  `type=PROCTITLE msg=audit(1758555102.328:4768): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T11:16:28.584000+00:00 .. 2025-09-22T15:31:42.328000+00:00
- **collectd.log**: '[YYYY-MM-DD HH:MM:SS]' without timezone; value lines carry a unix epoch. bracket_minus_epoch_seconds_observed == [0] means the bracket time equals UTC epoch time.
  - videoserver: `[2025-06-18 13:51:41] [info] write_log values:` / `atb-videoserver-image-2025-06-18t13-40-32z_novalocal.cpu-0.cpu-user 15181 1750254701`; range 2025-06-18 13:51:41 .. 2025-09-22 15:30:30; bracket-epoch offsets [0]
  - inetfw: `[2025-09-17 13:07:45] [info] write_log values:` / `atb-fw-image-2025-09-17t12-57-26z.cpu-0.cpu-user 20361 1758114465`; range 2025-09-17 13:07:45 .. 2025-09-22 14:20:11; bracket-epoch offsets [0]
  - corpdns: `[2025-09-17 11:16:35] [info] write_log values:` / `atb-corpdns-image-2025-09-17t11-07-58z.cpu-0.cpu-user 18574 1758107795`; range 2025-09-17 11:16:35 .. 2025-09-22 15:31:41; bracket-epoch offsets [0]
- **attacker auth.log / syslog**: {"syslog": {"lines": 1582, "first": "2025-09-22T13:34:44.090113+00:00 attacker systemd-modules-load[344]: Inserted module 'msr'", "last": "2025-09-22T15:32:38.711864+00:00 attacker systemd[1]: Started session-24.scope - Session 24 of User aecid.", "min": "2025-09-22T13:34:44.090113+00:00", "max": "2025-09-22T15:32:38.711864+00:00"}, "auth.log": {"lines": 191, "first": "2025-09-22T13:34:44.094220+00:00 attacker passwd[772]: password for 'ubuntu' changed by 'root'", "last": "2025-09-22T15:32:39.000356+00:00 attacker sudo: pam_unix(sudo:session): session opened for user root(uid=0) by aecid(uid=1001)", "min": "2025-09-22T13:34:44.094220+00:00", "max": "2025-09-22T15:32:39.000356+00:00"}}
- **Wazuh alerts**: timestamp example `2025-06-02T10:08:06.498+0000` (ISO 8601 with +0000 offset)
- **attackmate.json**: `start-datetime` e.g. `2025-09-22T13:48:30.907163`; no timezone
- host `/etc/timezone` files: {'videoserver': 'Etc/UTC', 'wazuh': 'Etc/UTC', 'inetfw': 'Etc/UTC', 'attacker': 'Etc/UTC', 'corpdns': 'Etc/UTC'}

### Alignment of attackmate times with host logs

attackmate first/last step: 2025-09-22T13:48:30.907163+00:00 .. 2025-09-22T14:10:54.791711+00:00 (read as UTC)

| Source | Host | Log min | Log max | First step inside | Last step inside |
|---|---|---|---|---|---|
| journal | videoserver | 2025-06-18T13:51:38.061652+00:00 | 2025-09-22T15:30:37.813694+00:00 | True | True |
| journal | inetfw | 2025-09-17T13:07:40.426054+00:00 | 2025-09-22T14:20:19.782155+00:00 | True | True |
| journal | attacker | 2025-05-19T14:39:23.888323+00:00 | 2025-09-22T15:32:39.000030+00:00 | True | True |
| journal | corpdns | 2025-09-17T11:16:28.587737+00:00 | 2025-09-22T15:31:42.406760+00:00 | True | True |
| audit.log | videoserver | 2025-06-18T13:51:38.047000+00:00 | 2025-09-22T15:30:37.808000+00:00 | True | True |
| audit.log | inetfw | 2025-09-17T13:07:18.688000+00:00 | 2025-09-22T14:20:19.776000+00:00 | True | True |
| audit.log | corpdns | 2025-09-17T11:16:28.584000+00:00 | 2025-09-22T15:31:42.328000+00:00 | True | True |
| collectd.log | videoserver | 2025-06-18 13:51:41 | 2025-09-22 15:30:30 | True | True |
| collectd.log | inetfw | 2025-09-17 13:07:45 | 2025-09-22 14:20:11 | True | True |
| collectd.log | corpdns | 2025-09-17 11:16:35 | 2025-09-22 15:31:41 | True | True |
| syslog | attacker | 2025-09-22T13:34:44.090113+00:00 | 2025-09-22T15:32:38.711864+00:00 | True | True |
| auth.log | attacker | 2025-09-22T13:34:44.094220+00:00 | 2025-09-22T15:32:39.000356+00:00 | True | True |
| wazuh alerts.json | wazuh | 2025-09-22T13:34:24.087000+00:00 | 2025-09-22T15:32:27.527000+00:00 | True | True |

sshd audit proximity (nearest sshd audit record to ssh-related steps):

```json
{"step_index": 0, "start_datetime": "2025-09-22T13:48:30.907163", "nearest_sshd_audit_record": {"host": "videoserver", "type": "type=USER_AUTH", "utc": "2025-09-22T14:09:24.976000+00:00", "delta_seconds_audit_minus_step": 1254.069}}
{"step_index": 30, "start_datetime": "2025-09-22T14:09:24.030431", "nearest_sshd_audit_record": {"host": "videoserver", "type": "type=USER_AUTH", "utc": "2025-09-22T14:09:24.976000+00:00", "delta_seconds_audit_minus_step": 0.946}}
{"step_index": 31, "start_datetime": "2025-09-22T14:09:39.387367", "nearest_sshd_audit_record": {"host": "videoserver", "type": "type=CRED_ACQ", "utc": "2025-09-22T14:09:25.212000+00:00", "delta_seconds_audit_minus_step": -14.175}}
```
**Verdict:** consistent with UTC: 2/3 ssh-related steps have an sshd audit record within 30 s when the attackmate time is read as UTC.

### Run identification

- root folder(s): ['scenario_1_sudo_pam'] (equals archive name: False)
- zip comment: ''; attackmate.json files: 1
- README files checked: 86; with scenario/run/simulation keywords: none
- .placeholder files: 32 (non-empty 27; example ('videoserver/configs/etc/cron.monthly/.placeholder', '# DO NOT EDIT OR REMOVE\n# This file is a simple placeholder to keep dpkg from re'))
- wazuh/facts.json: {'inventory_hostname': '192.168.100.130', 'group_names': ['wazuh'], 'gathered_iso8601': '2025-09-22T15:33:34Z', 'has_run_or_scenario_key': False}
- attackmate timeline: {'steps': 38, 'monotonic_non_decreasing': True, 'max_gap_seconds': 615.0, 'duration_seconds': 1343.9}

## 3. scenario_2_cron

- attackmate: `['attacker/logs/attackmate.json']`; unparseable lines: 0
- step types: {'ssh': 2, 'sliver': 2, 'shell': 1, 'sftp': 1, 'sliver-session': 16, 'regex': 1, 'debug': 1, 'mktemp': 4, 'sleep': 1}
- distinct techniques (21): ['T1003', 'T1003.008', 'T1005', 'T1007', 'T1016', 'T1018', 'T1021.004', 'T1041', 'T1046', 'T1049', 'T1057', 'T1070.004', 'T1071.001', 'T1074.001', 'T1083', 'T1105', 'T1201', 'T1547', 'T1560.001', 'T1569', 'T1573.001']
- distinct tactics (9): ['Collection', 'Command and Control', 'Credential Access', 'Defense Evasion', 'Discovery', 'Execution', 'Exfiltration', 'Lateral Movement', 'Persistence']
- unlabeled breakdown: {'metadata_null': 8}
- metadata keys: {'techniques': 21, 'tactics': 21, 'technique_name': 21}
- metadata key anomalies (non-identifier characters): none

### Log sources per host (exact path patterns, non-empty files)

| Host | Sources (files / bytes) |
|---|---|
| attacker | attackmate.json: 1 / 15301; syslog: 1 / 189543; journal: 14 / 117440512; auth.log: 1 / 16999 |
| corpdns | syslog: 1 / 137274; journal: 3 / 41943040; auth.log: 1 / 3659; collectd.log: 1 / 5188823; audit.log: 1 / 4241525 |
| inetfw | syslog: 1 / 334640; journal: 4 / 58720256; auth.log: 1 / 3669; collectd.log: 1 / 5678407; audit.log: 1 / 6667358 |
| videoserver | syslog: 1 / 287828; journal: 4 / 58720256; auth.log: 1 / 11578; collectd.log: 1 / 3930472; audit.log: 1 / 5828801 |
| wazuh | wazuh alerts: 6 / 8478414 |

### Label analysis

- steps with more than one technique: **7**
- real examples:
```json
{"step_index": 2, "type": "sliver", "cmd": "start_https_listener", "metadata": {"techniques": "T1071.001,T1573.001", "tactics": "Command and Control", "technique_name": "Application Layer Protocol: Web Protocols,Encrypted Channel: Symmetric Cryptography"}, "ids": ["T1071.001", "T1573.001"]}
{"step_index": 5, "type": "ssh", "cmd": "sed -i 's/#!\\/bin\\/sh/#!\\/bin\\/sh\\n\\/usr\\/bin\\/zmcontroller \\&\\n/' /us", "metadata": {"techniques": "T1547,T1569", "tactics": "Persistence,Execution", "technique_name": "Boot or Logon Autostart Execution,System Services"}, "ids": ["T1547", "T1569"]}
{"step_index": 15, "type": "sliver-session", "cmd": "download", "metadata": {"techniques": "T1003.008,T1041", "tactics": "Credential Access,Collection,Exfiltration", "technique_name": "OS Credential Dumping: /etc/passwd and /etc/shadow,Exfiltration Over C2 Channel"}, "ids": ["T1003.008", "T1041"]}
```
- strictly adjacent steps (both labeled) with identical technique set: **1**
- consecutive labeled steps (unlabeled skipped) with identical technique set: **1**
- consecutive labeled steps sharing at least one technique: 2

Real `parameters.metadata` of 3 labeled steps:
```json
{"step_index": 0, "type": "ssh", "cmd": "hostname", "metadata": {"techniques": "T1021.004", "tactics": "Lateral Movement", "technique_name": "Remote Services: SSH"}}
{"step_index": 2, "type": "sliver", "cmd": "start_https_listener", "metadata": {"techniques": "T1071.001,T1573.001", "tactics": "Command and Control", "technique_name": "Application Layer Protocol: Web Protocols,Encrypted Channel: Symmetric Cryptography"}}
{"step_index": 4, "type": "sftp", "cmd": "put", "metadata": {"techniques": "T1105", "tactics": "Command and Control", "technique_name": "Ingress Tool Transfer"}}
```
Real `parameters.metadata` of 3 unlabeled steps:
```json
{"step_index": 1, "type": "sliver", "cmd": "generate_implant", "metadata": null}
{"step_index": 3, "type": "shell", "cmd": "ls /tmp/tmp6q87c7nv", "metadata": null}
{"step_index": 9, "type": "debug", "cmd": "659", "metadata": null}
```

Values needing whitespace / case cleaning:

- none
- tactic spellings differing only by case: none

Ordered cleaned technique sequence (labeled steps only; `+` joins several techniques in one step):

`T1021.004 -> T1071.001+T1573.001 -> T1105 -> T1547+T1569 -> T1083 -> T1057 -> T1007 -> T1003 -> T1049 -> T1016 -> T1003.008+T1041 -> T1560.001+T1074.001 -> T1041 -> T1070.004 -> T1005 -> T1201 -> T1003.008 -> T1201 -> T1105+T1046+T1018 -> T1046+T1018 -> T1046+T1018`

### Wazuh files (wazuh host, exact archive paths)

| Path | Size | CRC32 |
|---|---|---|
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json` | 1052664 | c949b261 |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.log` | 1454934 | 374faa23 |
| `wazuh/logs/alerts/2025/Oct/ossec-alerts-01.json` | 1219551 | 73935d82 |
| `wazuh/logs/alerts/2025/Oct/ossec-alerts-01.log` | 1765857 | 84e6acc1 |
| `wazuh/logs/alerts/alerts.json` | 1219551 | 73935d82 |
| `wazuh/logs/alerts/alerts.log` | 1765857 | 84e6acc1 |

- byte-identical groups (same size and CRC32): [['wazuh/logs/alerts/2025/Oct/ossec-alerts-01.json', 'wazuh/logs/alerts/alerts.json'], ['wazuh/logs/alerts/2025/Oct/ossec-alerts-01.log', 'wazuh/logs/alerts/alerts.log']]
- archives.json / ossec.log / api.log / cluster.log present: none found

- `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json`: 500 alerts; rule.id 500; MITRE ids on 3; 11 rule ids; time 2025-06-02T10:08:06.498000+00:00 .. 2025-06-02T10:09:26.544000+00:00; agents {'atb-wazuh-image-2025-06-02t10-01-35z': 500}
  - in attackmate window (UTC reading): 0 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []
- `wazuh/logs/alerts/2025/Oct/ossec-alerts-01.json`: 657 alerts; rule.id 657; MITRE ids on 117; 22 rule ids; time 2025-10-01T09:57:32.789000+00:00 .. 2025-10-01T10:46:00.623000+00:00; agents {'wazuh': 14, 'inetfw': 352, 'videoserver': 291}
  - in attackmate window (UTC reading): 10 alerts, 6 with MITRE; MITRE ids in window ['T1021', 'T1078']; also in attackmate labels: []
- `wazuh/logs/alerts/alerts.json`: 657 alerts; rule.id 657; MITRE ids on 117; 22 rule ids; time 2025-10-01T09:57:32.789000+00:00 .. 2025-10-01T10:46:00.623000+00:00; agents {'wazuh': 14, 'inetfw': 352, 'videoserver': 291}
  - in attackmate window (UTC reading): 10 alerts, 6 with MITRE; MITRE ids in window ['T1021', 'T1078']; also in attackmate labels: []

Real Wazuh alert fields (example with MITRE):
```json
{"timestamp": "2025-06-02T10:08:10.507+0000", "agent": "atb-wazuh-image-2025-06-02t10-01-35z", "rule": {"id": "5403", "level": 4, "description": "First time user executed sudo.", "mitre": {"id": ["T1548.003"], "tactic": ["Privilege Escalation", "Defense Evasion"], "technique": ["Sudo and Sudo Caching"]}}}
```

### Timestamp formats (real samples)

- **journal**: Binary systemd journal (signature LPKSHHRH). Header realtime fields are microseconds since the Unix epoch (UTC by systemd definition). Per-entry text fields were not decoded (UNVERIFIED).
  - `videoserver:videoserver/logs/log/journal/9729f3e6f1d545e7a1cf4cffbc93efda/system.journal`: first entries [{'seqnum': 13892, 'realtime_utc': '2025-10-01T09:55:09.700883+00:00'}, {'seqnum': 13893, 'realtime_utc': '2025-10-01T09:55:09.700883+00:00'}, {'seqnum': 13894, 'realtime_utc': '2025-10-01T09:55:09.788538+00:00'}]; message strings ['Time spent on flushing to /var/log/journal/9729f3e6f1d545e7a1cf4cffbc93efda is 42.484ms for 529 entries.', 'System Journal (/var/log/journal/9729f3e6f1d545e7a1cf4cffbc93efda) is 24.0M, max 2.4G, 2.4G free.', 'Finished Create Static Device Nodes in /dev.']
  - `inetfw:inetfw/logs/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7/system.journal`: first entries [{'seqnum': 35231, 'realtime_utc': '2025-10-01T09:58:24.682187+00:00'}, {'seqnum': 35232, 'realtime_utc': '2025-10-01T09:58:24.723745+00:00'}, {'seqnum': 35233, 'realtime_utc': '2025-10-01T09:58:24.723792+00:00'}]; message strings ['PATH item=0 name="/bin/sh" inode=1586 dev=fc:01 mode=0100755 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 cap_fe=0 cap_fver=0 ', 'PATH item=1 name="/lib64/ld-linux-x86-64.so.2" inode=3599 dev=fc:01 mode=0100755 ouid=0 ogid=0 rdev=00:00 nametype=NORMAL cap_fp=0 cap_fi=0 ', 'PROCTITLE proctitle=7368002D63002F62696E2F7073202D7020333830203E202F6465762F6E756C6C20323E2631']
  - videoserver: 4 files, header range 2025-06-18T13:51:38.061652+00:00 .. 2025-10-01T10:45:05.198737+00:00
  - inetfw: 4 files, header range 2025-09-17T13:07:40.426054+00:00 .. 2025-10-01T10:38:03.038886+00:00
  - attacker: 14 files, header range 2025-05-19T14:39:23.888323+00:00 .. 2025-10-01T10:45:31.105804+00:00
  - corpdns: 3 files, header range 2025-09-17T11:16:28.587737+00:00 .. 2025-10-01T10:38:03.480722+00:00
- **audit.log**: msg=audit(<unix epoch seconds.millis>:<serial>): epoch time => no timezone ambiguity (UTC).
  - videoserver: `type=SYSCALL msg=audit(1750254698.047:2729): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55fc157739a0 a2=241 a3=1b6 items=2 ppid=39616 pid=39629 auid=1000`  ...  `type=PROCTITLE msg=audit(1759315505.193:5793): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-06-18T13:51:38.047000+00:00 .. 2025-10-01T10:45:05.193000+00:00
  - inetfw: `type=PATH msg=audit(1758114460.424:2211): item=0 name="/var/log/" inode=80887 dev=fc:01 mode=040775 ouid=0 ogid=111 rdev=00:00 nametype=PARENT cap_fp=0 cap_fi=0 cap_fe=0 `  ...  `type=PROCTITLE msg=audit(1759315082.984:7105): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T13:07:18.688000+00:00 .. 2025-10-01T10:38:02.984000+00:00
  - corpdns: `type=SYSCALL msg=audit(1758107788.584:2473): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55ae93e00490 a2=241 a3=1b6 items=2 ppid=14993 pid=15006 auid=1000`  ...  `type=PROCTITLE msg=audit(1759315083.440:4499): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T11:16:28.584000+00:00 .. 2025-10-01T10:38:03.440000+00:00
- **collectd.log**: '[YYYY-MM-DD HH:MM:SS]' without timezone; value lines carry a unix epoch. bracket_minus_epoch_seconds_observed == [0] means the bracket time equals UTC epoch time.
  - videoserver: `[2025-06-18 13:51:41] [info] write_log values:` / `atb-videoserver-image-2025-06-18t13-40-32z_novalocal.cpu-0.cpu-user 15181 1750254701`; range 2025-06-18 13:51:41 .. 2025-10-01 10:45:03; bracket-epoch offsets [0]
  - inetfw: `[2025-09-17 13:07:45] [info] write_log values:` / `atb-fw-image-2025-09-17t12-57-26z.cpu-0.cpu-user 20361 1758114465`; range 2025-09-17 13:07:45 .. 2025-10-01 10:37:58; bracket-epoch offsets [0]
  - corpdns: `[2025-09-17 11:16:35] [info] write_log values:` / `atb-corpdns-image-2025-09-17t11-07-58z.cpu-0.cpu-user 18574 1758107795`; range 2025-09-17 11:16:35 .. 2025-10-01 10:38:02; bracket-epoch offsets [0]
- **attacker auth.log / syslog**: {"syslog": {"lines": 1542, "first": "2025-10-01T09:59:22.585925+00:00 attacker systemd-modules-load[345]: Inserted module 'msr'", "last": "2025-10-01T10:45:30.886154+00:00 attacker systemd[1]: Started session-14.scope - Session 14 of User aecid.", "min": "2025-10-01T09:59:22.585925+00:00", "max": "2025-10-01T10:45:30.886154+00:00"}, "auth.log": {"lines": 127, "first": "2025-10-01T09:59:22.590007+00:00 attacker passwd[774]: password for 'ubuntu' changed by 'root'", "last": "2025-10-01T10:45:31.106342+00:00 attacker sudo: pam_unix(sudo:session): session opened for user root(uid=0) by aecid(uid=1001)", "min": "2025-10-01T09:59:22.590007+00:00", "max": "2025-10-01T10:45:31.106342+00:00"}}
- **Wazuh alerts**: timestamp example `2025-06-02T10:08:06.498+0000` (ISO 8601 with +0000 offset)
- **attackmate.json**: `start-datetime` e.g. `2025-10-01T10:14:14.955559`; no timezone
- host `/etc/timezone` files: {'videoserver': 'Etc/UTC', 'wazuh': 'Etc/UTC', 'inetfw': 'Etc/UTC', 'attacker': 'Etc/UTC', 'corpdns': 'Etc/UTC'}

### Alignment of attackmate times with host logs

attackmate first/last step: 2025-10-01T10:14:14.955559+00:00 .. 2025-10-01T10:35:06.286635+00:00 (read as UTC)

| Source | Host | Log min | Log max | First step inside | Last step inside |
|---|---|---|---|---|---|
| journal | videoserver | 2025-06-18T13:51:38.061652+00:00 | 2025-10-01T10:45:05.198737+00:00 | True | True |
| journal | inetfw | 2025-09-17T13:07:40.426054+00:00 | 2025-10-01T10:38:03.038886+00:00 | True | True |
| journal | attacker | 2025-05-19T14:39:23.888323+00:00 | 2025-10-01T10:45:31.105804+00:00 | True | True |
| journal | corpdns | 2025-09-17T11:16:28.587737+00:00 | 2025-10-01T10:38:03.480722+00:00 | True | True |
| audit.log | videoserver | 2025-06-18T13:51:38.047000+00:00 | 2025-10-01T10:45:05.193000+00:00 | True | True |
| audit.log | inetfw | 2025-09-17T13:07:18.688000+00:00 | 2025-10-01T10:38:02.984000+00:00 | True | True |
| audit.log | corpdns | 2025-09-17T11:16:28.584000+00:00 | 2025-10-01T10:38:03.440000+00:00 | True | True |
| collectd.log | videoserver | 2025-06-18 13:51:41 | 2025-10-01 10:45:03 | True | True |
| collectd.log | inetfw | 2025-09-17 13:07:45 | 2025-10-01 10:37:58 | True | True |
| collectd.log | corpdns | 2025-09-17 11:16:35 | 2025-10-01 10:38:02 | True | True |
| syslog | attacker | 2025-10-01T09:59:22.585925+00:00 | 2025-10-01T10:45:30.886154+00:00 | True | True |
| auth.log | attacker | 2025-10-01T09:59:22.590007+00:00 | 2025-10-01T10:45:31.106342+00:00 | True | True |
| wazuh alerts.json | wazuh | 2025-10-01T09:57:32.789000+00:00 | 2025-10-01T10:46:00.623000+00:00 | True | True |

sshd audit proximity (nearest sshd audit record to ssh-related steps):

```json
{"step_index": 0, "start_datetime": "2025-10-01T10:14:14.955559", "nearest_sshd_audit_record": {"host": "videoserver", "type": "type=USER_ACCT", "utc": "2025-10-01T10:14:15.129000+00:00", "delta_seconds_audit_minus_step": 0.173}}
{"step_index": 5, "start_datetime": "2025-10-01T10:15:46.147666", "nearest_sshd_audit_record": {"host": "videoserver", "type": "type=USER_START", "utc": "2025-10-01T10:14:15.269000+00:00", "delta_seconds_audit_minus_step": -90.879}}
```
**Verdict:** unclear: sshd audit proximity did not give a clear match.

### Run identification

- root folder(s): ['scenario_2_cron'] (equals archive name: False)
- zip comment: ''; attackmate.json files: 1
- README files checked: 81; with scenario/run/simulation keywords: none
- .placeholder files: 32 (non-empty 27; example ('videoserver/configs/etc/cron.monthly/.placeholder', '# DO NOT EDIT OR REMOVE\n# This file is a simple placeholder to keep dpkg from re'))
- wazuh/facts.json: {'inventory_hostname': '192.168.100.130', 'group_names': ['wazuh'], 'gathered_iso8601': '2025-10-01T10:46:19Z', 'has_run_or_scenario_key': False}
- attackmate timeline: {'steps': 29, 'monotonic_non_decreasing': True, 'max_gap_seconds': 856.1, 'duration_seconds': 1251.3}

## 3. scenario_3_vnc_apt

- attackmate: `['attacker/logs/attackmate.json']`; unparseable lines: 0
- step types: {'mktemp': 1, 'msf-payload': 1, 'msf-module': 1, 'webserv': 1, 'vnc': 38, 'loop': 1, 'sleep': 16, 'shell': 1, 'msf-session': 15, 'setvar': 1, 'include': 1}
- distinct techniques (23): ['T1003.008', 'T1018', 'T1021.005', 'T1036.005', 'T1039', 'T1053.003', 'T1059', 'T1059.004', 'T1071.001', 'T1072', 'T1083', 'T1087.001', 'T1105', 'T1110.001', 'T1213', 'T1485', 'T1486', 'T1489', 'T1490', 'T1531', 'T1564.001', 'T1565.001', 'T1574']
- distinct tactics (9): ['Collection', 'Command and Control', 'Credential Access', 'Defense Evasion', 'Discovery', 'Execution', 'Impact', 'Lateral Movement', 'Persistence']
- unlabeled breakdown: {'metadata_null': 34, 'metadata_dict_without_technique': 14}
- metadata keys: {'techniques': 29, 'tactics': 29, 'technique_name': 29, 'action': 17, 'delayed_manifestation': 1}
- metadata key anomalies (non-identifier characters): none

### Log sources per host (exact path patterns, non-empty files)

| Host | Sources (files / bytes) |
|---|---|
| attacker | attackmate.json: 1 / 41920; syslog: 1 / 213220; journal: 6 / 50331648; auth.log: 1 / 19304 |
| corpdns | syslog: 1 / 129981; journal: 4 / 50331648; auth.log: 1 / 3318; collectd.log: 1 / 8228431; audit.log: 1 / 3722384 |
| inetfw | syslog: 1 / 1077330; journal: 4 / 67108864; auth.log: 1 / 3990; collectd.log: 1 / 9619276; audit.log: 1 / 6763068 |
| linuxshare | syslog: 1 / 145171; journal: 4 / 56457328; auth.log: 1 / 11743; collectd.log: 1 / 6771066; audit.log: 1 / 15970873 |
| reposerver | syslog: 1 / 182631; journal: 6 / 100663296; auth.log: 1 / 6163; collectd.log: 1 / 10676187; audit.log: 1 / 16266245 |
| wazuh | wazuh alerts: 6 / 6896706 |

### Label analysis

- steps with more than one technique: **6**
- real examples:
```json
{"step_index": 5, "type": "loop", "cmd": "items(LISTA)", "metadata": {"techniques": "T1110.001,T1021.005", "tactics": "Credential Access, Lateral Movement", "technique_name": "Brute Force: Password Guessing,Remote Services: VNC"}, "ids": ["T1110.001", "T1021.005"]}
{"step_index": 38, "type": "vnc", "cmd": "key", "metadata": {"techniques": "T1036.005,T1564.001 ", "tactics": "Defense Evasion", "technique_name": "Masquerading: Match Legitimate Name or Location,Hide Artifacts: Hidden Files and Directories"}, "ids": ["T1036.005", "T1564.001"]}
{"step_index": 45, "type": "vnc", "cmd": "type", "metadata": {"techniques": "T1059,T1574", "tactics": "Execution", "technique_name": "Command and Scripting Interpreter,Hijack Execution Flow", "action": "sed DEBIAN/control"}, "ids": ["T1059", "T1574"]}
```
- strictly adjacent steps (both labeled) with identical technique set: **5**
- consecutive labeled steps (unlabeled skipped) with identical technique set: **8**
- consecutive labeled steps sharing at least one technique: 11

Real `parameters.metadata` of 3 labeled steps:
```json
{"step_index": 5, "type": "loop", "cmd": "items(LISTA)", "metadata": {"techniques": "T1110.001,T1021.005", "tactics": "Credential Access, Lateral Movement", "technique_name": "Brute Force: Password Guessing,Remote Services: VNC"}}
{"step_index": 6, "type": "vnc", "cmd": "click", "metadata": {"techniques": "T1021.005", "tactics": "Lateral Movement", "technique_name": "Remote Services: VNC"}}
{"step_index": 8, "type": "vnc", "cmd": "type", "metadata": {"techniques": "T1021.005", "tactics": "Lateral Movement", "technique_name": "Remote Services: VNC", "action": "terminal"}}
```
Real `parameters.metadata` of 3 unlabeled steps:
```json
{"step_index": 16, "type": "vnc", "cmd": "type", "metadata": {"action": "id"}}
{"step_index": 0, "type": "mktemp", "cmd": "file", "metadata": null}
{"step_index": 1, "type": "msf-payload", "cmd": "cmd/unix/python/meterpreter/reverse_tcp", "metadata": null}
```

Values needing whitespace / case cleaning:

- step 5 `tactics`: raw `'Credential Access, Lateral Movement'` -> problems ' Lateral Movement'->'Lateral Movement' ['whitespace']
- step 38 `techniques`: raw `'T1036.005,T1564.001 '` -> problems 'T1564.001 '->'T1564.001' ['whitespace']
- step 47 `techniques`: raw `'T1053.003,T1105,T1071.001 '` -> problems 'T1071.001 '->'T1071.001' ['whitespace']
- tactic spellings differing only by case: none

Ordered cleaned technique sequence (labeled steps only; `+` joins several techniques in one step):

`T1110.001+T1021.005 -> T1021.005 -> T1021.005 -> T1021.005 -> T1003.008 -> T1213 -> T1039 -> T1083 -> T1059.004 -> T1036.005+T1564.001 -> T1574 -> T1059+T1574 -> T1053.003+T1105+T1071.001 -> T1072 -> T1072 -> T1059 -> T1059 -> T1059 -> T1059 -> T1059 -> T1059 -> T1486+T1105 -> T1486+T1565.001 -> T1018 -> T1087.001 -> T1531 -> T1485 -> T1490 -> T1489`

### Wazuh files (wazuh host, exact archive paths)

| Path | Size | CRC32 |
|---|---|---|
| `wazuh/logs/alerts/2025/Dec/ossec-alerts-12.json` | 945482 | ddd2a404 |
| `wazuh/logs/alerts/2025/Dec/ossec-alerts-12.log` | 1249072 | bbad0ef9 |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json` | 1052664 | c949b261 |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.log` | 1454934 | 374faa23 |
| `wazuh/logs/alerts/alerts.json` | 945482 | ddd2a404 |
| `wazuh/logs/alerts/alerts.log` | 1249072 | bbad0ef9 |

- byte-identical groups (same size and CRC32): [['wazuh/logs/alerts/2025/Dec/ossec-alerts-12.json', 'wazuh/logs/alerts/alerts.json'], ['wazuh/logs/alerts/2025/Dec/ossec-alerts-12.log', 'wazuh/logs/alerts/alerts.log']]
- archives.json / ossec.log / api.log / cluster.log present: none found

- `wazuh/logs/alerts/2025/Dec/ossec-alerts-12.json`: 661 alerts; rule.id 661; MITRE ids on 64; 23 rule ids; time 2025-12-12T17:19:54.784000+00:00 .. 2025-12-12T18:44:08.284000+00:00; agents {'wazuh': 24, 'inetfw': 637}
  - in attackmate window (UTC reading): 110 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []
- `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json`: 500 alerts; rule.id 500; MITRE ids on 3; 11 rule ids; time 2025-06-02T10:08:06.498000+00:00 .. 2025-06-02T10:09:26.544000+00:00; agents {'atb-wazuh-image-2025-06-02t10-01-35z': 500}
  - in attackmate window (UTC reading): 0 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []
- `wazuh/logs/alerts/alerts.json`: 661 alerts; rule.id 661; MITRE ids on 64; 23 rule ids; time 2025-12-12T17:19:54.784000+00:00 .. 2025-12-12T18:44:08.284000+00:00; agents {'wazuh': 24, 'inetfw': 637}
  - in attackmate window (UTC reading): 110 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []

Real Wazuh alert fields (example with MITRE):
```json
{"timestamp": "2025-12-12T17:20:07.225+0000", "agent": "inetfw", "rule": {"id": "506", "level": 3, "description": "Wazuh agent stopped.", "mitre": {"id": ["T1562.001"], "tactic": ["Defense Evasion"], "technique": ["Disable or Modify Tools"]}}}
```

### Timestamp formats (real samples)

- **journal**: Binary systemd journal (signature LPKSHHRH). Header realtime fields are microseconds since the Unix epoch (UTC by systemd definition). Per-entry text fields were not decoded (UNVERIFIED).
  - `inetfw:inetfw/logs/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7/system.journal`: first entries [{'seqnum': 13715, 'realtime_utc': '2025-12-12T17:18:42.729730+00:00'}, {'seqnum': 13716, 'realtime_utc': '2025-12-12T17:18:42.729730+00:00'}, {'seqnum': 13717, 'realtime_utc': '2025-12-12T17:18:42.834206+00:00'}]; message strings ['Time spent on flushing to /var/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7 is 47.097ms for 642 entries.', 'System Journal (/var/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7) is 24.0M, max 2.4G, 2.3G free.', 'Starting Flush Journal to Persistent Storage...']
  - `attacker:attacker/logs/log/journal/c103eaa6ed72493ca84e51a8eabc77ef/system.journal`: first entries [{'seqnum': 5499, 'realtime_utc': '2025-12-12T17:19:59.708865+00:00'}, {'seqnum': 5522, 'realtime_utc': '2025-12-12T17:19:59.710240+00:00'}, {'seqnum': 5523, 'realtime_utc': '2025-12-12T17:19:59.710304+00:00'}]; message strings ['/var/log/journal/c103eaa6ed72493ca84e51a8eabc77ef/user-1001.journal: Journal file uses a different sequence number ID, rotating.', 'Started user@1001.service - User Manager for UID 1001.', 'Started session-c1.scope - Session c1 of User aecid.']
  - inetfw: 4 files, header range 2025-09-17T13:07:40.426054+00:00 .. 2025-12-12T18:37:07.372039+00:00
  - attacker: 6 files, header range 2025-12-10T13:43:21.585468+00:00 .. 2025-12-12T18:44:03.955250+00:00
  - linuxshare: 4 files, header range 2025-12-11T12:39:09.600830+00:00 .. 2025-12-12T18:43:40.972385+00:00
  - corpdns: 4 files, header range 2025-09-17T11:16:28.587737+00:00 .. 2025-12-12T18:37:08.811943+00:00
  - reposerver: 6 files, header range 2025-12-11T13:00:13.036184+00:00 .. 2025-12-12T18:43:17.023572+00:00
- **audit.log**: msg=audit(<unix epoch seconds.millis>:<serial>): epoch time => no timezone ambiguity (UTC).
  - inetfw: `type=PATH msg=audit(1758114460.424:2211): item=0 name="/var/log/" inode=80887 dev=fc:01 mode=040775 ouid=0 ogid=111 rdev=00:00 nametype=PARENT cap_fp=0 cap_fi=0 cap_fe=0 `  ...  `type=PROCTITLE msg=audit(1765564627.368:7199): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T13:07:18.688000+00:00 .. 2025-12-12T18:37:07.368000+00:00
  - linuxshare: `type=SYSCALL msg=audit(1765456749.600:1298): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55a1e6b7a250 a2=241 a3=1b6 items=2 ppid=13551 pid=13564 auid=1000`  ...  `type=PROCTITLE msg=audit(1765565020.928:13768): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-12-11T12:39:09.600000+00:00 .. 2025-12-12T18:43:40.928000+00:00
  - corpdns: `type=SYSCALL msg=audit(1758107788.584:2473): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55ae93e00490 a2=241 a3=1b6 items=2 ppid=14993 pid=15006 auid=1000`  ...  `type=PROCTITLE msg=audit(1765564628.760:3881): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T11:16:28.584000+00:00 .. 2025-12-12T18:37:08.760000+00:00
  - reposerver: `type=SYSCALL msg=audit(1765458013.032:6157): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=56295ea51c30 a2=241 a3=1b6 items=2 ppid=32447 pid=32460 auid=1000`  ...  `type=PROCTITLE msg=audit(1765564996.892:17715): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-12-11T13:00:02.072000+00:00 .. 2025-12-12T18:43:16.892000+00:00
- **collectd.log**: '[YYYY-MM-DD HH:MM:SS]' without timezone; value lines carry a unix epoch. bracket_minus_epoch_seconds_observed == [0] means the bracket time equals UTC epoch time.
  - inetfw: `[2025-09-17 13:07:45] [info] write_log values:` / `atb-fw-image-2025-09-17t12-57-26z.cpu-0.cpu-user 20361 1758114465`; range 2025-09-17 13:07:45 .. 2025-12-12 18:37:01; bracket-epoch offsets [0]
  - linuxshare: `[2025-12-11 12:39:17] [info] write_log values:` / `linuxshare_attackbed_local.cpu-0.cpu-user 10015 1765456757`; range 2025-12-11 12:39:17 .. 2025-12-12 18:43:33; bracket-epoch offsets [0]
  - corpdns: `[2025-09-17 11:16:35] [info] write_log values:` / `atb-corpdns-image-2025-09-17t11-07-58z.cpu-0.cpu-user 18574 1758107795`; range 2025-09-17 11:16:35 .. 2025-12-12 18:37:02; bracket-epoch offsets [0]
  - reposerver: `[2025-12-11 13:00:15] [info] write_log values:` / `puppet_attackbed_local.cpu-0.cpu-user 12368 1765458015`; range 2025-12-11 13:00:15 .. 2025-12-12 18:43:11; bracket-epoch offsets [0]
- **attacker auth.log / syslog**: {"syslog": {"lines": 1726, "first": "2025-12-10T13:43:21.585726+00:00 atb-attacker-image-2025-12-10t12-35-00z x11vnc[26407]:  --- x11vnc loop: 92 ---", "last": "2025-12-12T18:44:03.733938+00:00 attacker systemd[1]: Started session-19.scope - Session 19 of User aecid.", "min": "2025-12-10T13:43:21.585726+00:00", "max": "2025-12-12T18:44:03.733938+00:00"}, "auth.log": {"lines": 148, "first": "2025-12-10T13:43:56.227741+00:00 atb-attacker-image-2025-12-10t12-35-00z sshd[1697]: Received disconnect from 10.110.0.254 port 41", "last": "2025-12-12T18:44:03.955795+00:00 attacker sudo: pam_unix(sudo:session): session opened for user root(uid=0) by aecid(uid=1001)", "min": "2025-12-10T13:43:56.227741+ ...(truncated)
- **Wazuh alerts**: timestamp example `2025-12-12T17:19:54.784+0000` (ISO 8601 with +0000 offset)
- **attackmate.json**: `start-datetime` e.g. `2025-12-12T18:07:53.665927`; no timezone
- host `/etc/timezone` files: {'wazuh': 'Etc/UTC', 'inetfw': 'Etc/UTC', 'attacker': 'Etc/UTC', 'linuxshare': 'Etc/UTC', 'corpdns': 'Etc/UTC', 'reposerver': 'Etc/UTC'}

### Alignment of attackmate times with host logs

attackmate first/last step: 2025-12-12T18:07:53.665927+00:00 .. 2025-12-12T18:34:13.417531+00:00 (read as UTC)

| Source | Host | Log min | Log max | First step inside | Last step inside |
|---|---|---|---|---|---|
| journal | inetfw | 2025-09-17T13:07:40.426054+00:00 | 2025-12-12T18:37:07.372039+00:00 | True | True |
| journal | attacker | 2025-12-10T13:43:21.585468+00:00 | 2025-12-12T18:44:03.955250+00:00 | True | True |
| journal | linuxshare | 2025-12-11T12:39:09.600830+00:00 | 2025-12-12T18:43:40.972385+00:00 | True | True |
| journal | corpdns | 2025-09-17T11:16:28.587737+00:00 | 2025-12-12T18:37:08.811943+00:00 | True | True |
| journal | reposerver | 2025-12-11T13:00:13.036184+00:00 | 2025-12-12T18:43:17.023572+00:00 | True | True |
| audit.log | inetfw | 2025-09-17T13:07:18.688000+00:00 | 2025-12-12T18:37:07.368000+00:00 | True | True |
| audit.log | linuxshare | 2025-12-11T12:39:09.600000+00:00 | 2025-12-12T18:43:40.928000+00:00 | True | True |
| audit.log | corpdns | 2025-09-17T11:16:28.584000+00:00 | 2025-12-12T18:37:08.760000+00:00 | True | True |
| audit.log | reposerver | 2025-12-11T13:00:02.072000+00:00 | 2025-12-12T18:43:16.892000+00:00 | True | True |
| collectd.log | inetfw | 2025-09-17 13:07:45 | 2025-12-12 18:37:01 | True | True |
| collectd.log | linuxshare | 2025-12-11 12:39:17 | 2025-12-12 18:43:33 | True | True |
| collectd.log | corpdns | 2025-09-17 11:16:35 | 2025-12-12 18:37:02 | True | True |
| collectd.log | reposerver | 2025-12-11 13:00:15 | 2025-12-12 18:43:11 | True | True |
| syslog | attacker | 2025-12-10T13:43:21.585726+00:00 | 2025-12-12T18:44:03.733938+00:00 | True | True |
| auth.log | attacker | 2025-12-10T13:43:56.227741+00:00 | 2025-12-12T18:44:03.955795+00:00 | True | True |
| wazuh alerts.json | wazuh | 2025-12-12T17:19:54.784000+00:00 | 2025-12-12T18:44:08.284000+00:00 | True | True |

sshd audit proximity (nearest sshd audit record to ssh-related steps):

```json
{"step_index": 57, "start_datetime": "2025-12-12T18:25:23.561147", "nearest_sshd_audit_record": {"host": "linuxshare", "type": "type=USER_ACCT", "utc": "2025-12-12T18:26:59.872000+00:00", "delta_seconds_audit_minus_step": 96.311}}
```
**Verdict:** unclear: sshd audit proximity did not give a clear match.

### Run identification

- root folder(s): ['scenario_3_vnc_apt'] (equals archive name: False)
- zip comment: ''; attackmate.json files: 1
- README files checked: 96; with scenario/run/simulation keywords: none
- .placeholder files: 39 (non-empty 33; example ('wazuh/configs/etc/cron.monthly/.placeholder', '# DO NOT EDIT OR REMOVE\n# This file is a simple placeholder to keep dpkg from re'))
- wazuh/facts.json: {'inventory_hostname': '192.168.100.130', 'group_names': ['wazuh'], 'gathered_iso8601': '2025-12-12T18:44:28Z', 'has_run_or_scenario_key': False}
- attackmate timeline: {'steps': 77, 'monotonic_non_decreasing': False, 'max_gap_seconds': 375.0, 'duration_seconds': 1579.8}

## 3. scenario_4

- attackmate: `['attacker/logs/attackmate.json']`; unparseable lines: 0
- step types: {'sliver': 2, 'shell': 2, 'sleep': 15, 'ssh': 24, 'webserv': 1, 'sliver-session': 2}
- distinct techniques (10): ['T1036.005', 'T1070.004', 'T1071.001', 'T1078.003', 'T1082', 'T1105', 'T1205.001', 'T1543.002', 'T1548.003', 'T1599']
- distinct tactics (7): ['Command and Control', 'Defense Evasion', 'Discovery', 'Initial Access', 'Lateral Movement', 'Persistence', 'Privilege Escalation']
- unlabeled breakdown: {'metadata_null': 24}
- metadata keys: {'techniques': 22, 'tactics': 22, 'technique_name': 22}
- metadata key anomalies (non-identifier characters): none

### Log sources per host (exact path patterns, non-empty files)

| Host | Sources (files / bytes) |
|---|---|
| attacker | attackmate.json: 1 / 28176; syslog: 1 / 211229; journal: 6 / 50331648; auth.log: 1 / 25842 |
| corpdns | syslog: 1 / 138863; journal: 4 / 50331648; auth.log: 1 / 3659; collectd.log: 1 / 6987515; audit.log: 1 / 4289224 |
| inetfw | syslog: 1 / 1041395; journal: 5 / 75497472; auth.log: 1 / 8107; collectd.log: 1 / 7234701; audit.log: 1 / 7348605 |
| linuxshare | syslog: 1 / 144812; journal: 4 / 41943040; auth.log: 1 / 9922; collectd.log: 1 / 5614275; audit.log: 1 / 4577459 |
| reposerver | syslog: 1 / 193612; journal: 6 / 100663296; auth.log: 1 / 8039; collectd.log: 1 / 8532874; audit.log: 1 / 16861550 |
| wazuh | wazuh alerts: 6 / 6490952 |

### Label analysis

- steps with more than one technique: **3**
- real examples:
```json
{"step_index": 2, "type": "shell", "cmd": "sshpass -p 'rambo' scp -o StrictHostKeyChecking=no -o ProxyCommand=\"ss", "metadata": {"techniques": "T1078.003,T1105,T1205.001", "tactics": "Initial Access,Lateral Movement,Defense Evasion", "technique_name": "Valid Accounts: Local Accounts,Ingress Tool Transfer,Traffic Signaling: Port Knocking"}, "ids": ["T1078.003", "T1105", "T1205.001"]}
{"step_index": 12, "type": "ssh", "cmd": "sudo tar -xzf /tmp/auditf.tar.gz -C /usr/bin\n", "metadata": {"techniques": "T1036.005,T1205.001", "tactics": "Defense Evasion", "technique_name": "Masquerading: Match Legitimate Name or Location,Traffic Signaling: Port Knocking"}, "ids": ["T1036.005", "T1205.001"]}
{"step_index": 35, "type": "shell", "cmd": "/home/aecid/knock-cli -c knock.yaml -r knock-firewall", "metadata": {"techniques": "T1205.001,T1071.001,T1036.005", "tactics": "Defense Evasion,Persistence,Command and Control", "technique_name": "Traffic Signaling: Port Knocking,Application Layer Protocol: Web Protocols,Masquerading: Match Legitimate Name or Location"}, "ids": ["T1205.001", "T1071.001", "T1036.005"]}
```
- strictly adjacent steps (both labeled) with identical technique set: **3**
- consecutive labeled steps (unlabeled skipped) with identical technique set: **11**
- consecutive labeled steps sharing at least one technique: 12

Real `parameters.metadata` of 3 labeled steps:
```json
{"step_index": 0, "type": "sliver", "cmd": "generate_implant", "metadata": {"techniques": "T1071.001", "tactics": "Command and Control", "technique_name": "Application Layer Protocol: Web Protocols"}}
{"step_index": 1, "type": "sliver", "cmd": "start_https_listener", "metadata": {"techniques": "T1071.001", "tactics": "Command and Control", "technique_name": "Application Layer Protocol: Web Protocols"}}
{"step_index": 2, "type": "shell", "cmd": "sshpass -p 'rambo' scp -o StrictHostKeyChecking=no -o ProxyCommand=\"ss", "metadata": {"techniques": "T1078.003,T1105,T1205.001", "tactics": "Initial Access,Lateral Movement,Defense Evasion", "technique_name": "Valid Accounts: Local Accounts,Ingress Tool Transfer,Traffic Signaling: Port Knocking"}}
```
Real `parameters.metadata` of 3 unlabeled steps:
```json
{"step_index": 3, "type": "sleep", "cmd": "sleep", "metadata": null}
{"step_index": 5, "type": "sleep", "cmd": "sleep", "metadata": null}
{"step_index": 7, "type": "sleep", "cmd": "sleep", "metadata": null}
```

Values needing whitespace / case cleaning:

- none
- tactic spellings differing only by case: none

Ordered cleaned technique sequence (labeled steps only; `+` joins several techniques in one step):

`T1071.001 -> T1071.001 -> T1078.003+T1105+T1205.001 -> T1078.003 -> T1078.003 -> T1078.003 -> T1548.003 -> T1548.003 -> T1036.005+T1205.001 -> T1070.004 -> T1543.002 -> T1543.002 -> T1543.002 -> T1543.002 -> T1543.002 -> T1205.001+T1071.001+T1036.005 -> T1599 -> T1599 -> T1078.003 -> T1078.003 -> T1078.003 -> T1082`

### Wazuh files (wazuh host, exact archive paths)

| Path | Size | CRC32 |
|---|---|---|
| `wazuh/logs/alerts/2025/Dec/ossec-alerts-15.json` | 857598 | 8346dae0 |
| `wazuh/logs/alerts/2025/Dec/ossec-alerts-15.log` | 1134079 | b61e118a |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json` | 1052664 | c949b261 |
| `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.log` | 1454934 | 374faa23 |
| `wazuh/logs/alerts/alerts.json` | 857598 | 8346dae0 |
| `wazuh/logs/alerts/alerts.log` | 1134079 | b61e118a |

- byte-identical groups (same size and CRC32): [['wazuh/logs/alerts/2025/Dec/ossec-alerts-15.json', 'wazuh/logs/alerts/alerts.json'], ['wazuh/logs/alerts/2025/Dec/ossec-alerts-15.log', 'wazuh/logs/alerts/alerts.log']]
- archives.json / ossec.log / api.log / cluster.log present: none found

- `wazuh/logs/alerts/2025/Dec/ossec-alerts-15.json`: 598 alerts; rule.id 598; MITRE ids on 103; 23 rule ids; time 2025-12-15T10:46:44.222000+00:00 .. 2025-12-15T11:55:01.426000+00:00; agents {'wazuh': 26, 'inetfw': 572}
  - in attackmate window (UTC reading): 99 alerts, 47 with MITRE; MITRE ids in window ['T1021', 'T1040', 'T1078', 'T1548.003']; also in attackmate labels: ['T1548.003']
- `wazuh/logs/alerts/2025/Jun/ossec-alerts-02.json`: 500 alerts; rule.id 500; MITRE ids on 3; 11 rule ids; time 2025-06-02T10:08:06.498000+00:00 .. 2025-06-02T10:09:26.544000+00:00; agents {'atb-wazuh-image-2025-06-02t10-01-35z': 500}
  - in attackmate window (UTC reading): 0 alerts, 0 with MITRE; MITRE ids in window []; also in attackmate labels: []
- `wazuh/logs/alerts/alerts.json`: 598 alerts; rule.id 598; MITRE ids on 103; 23 rule ids; time 2025-12-15T10:46:44.222000+00:00 .. 2025-12-15T11:55:01.426000+00:00; agents {'wazuh': 26, 'inetfw': 572}
  - in attackmate window (UTC reading): 99 alerts, 47 with MITRE; MITRE ids in window ['T1021', 'T1040', 'T1078', 'T1548.003']; also in attackmate labels: ['T1548.003']

Real Wazuh alert fields (example with MITRE):
```json
{"timestamp": "2025-12-15T10:46:58.941+0000", "agent": "inetfw", "rule": {"id": "506", "level": 3, "description": "Wazuh agent stopped.", "mitre": {"id": ["T1562.001"], "tactic": ["Defense Evasion"], "technique": ["Disable or Modify Tools"]}}}
```

### Timestamp formats (real samples)

- **journal**: Binary systemd journal (signature LPKSHHRH). Header realtime fields are microseconds since the Unix epoch (UTC by systemd definition). Per-entry text fields were not decoded (UNVERIFIED).
  - `inetfw:inetfw/logs/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7/system.journal`: first entries [{'seqnum': 13716, 'realtime_utc': '2025-12-15T10:43:30.725541+00:00'}, {'seqnum': 13717, 'realtime_utc': '2025-12-15T10:43:30.725541+00:00'}, {'seqnum': 13718, 'realtime_utc': '2025-12-15T10:43:30.833625+00:00'}]; message strings ['Time spent on flushing to /var/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7 is 47.637ms for 643 entries.', 'System Journal (/var/log/journal/9fb1ee6c2f0c4af18a11bbb205f59be7) is 24.0M, max 2.4G, 2.3G free.', 'loop0: detected capacity change from 0 to 79520']
  - `attacker:attacker/logs/log/journal/c103eaa6ed72493ca84e51a8eabc77ef/system.journal`: first entries [{'seqnum': 5496, 'realtime_utc': '2025-12-15T10:48:41.763490+00:00'}, {'seqnum': 5519, 'realtime_utc': '2025-12-15T10:48:41.770202+00:00'}, {'seqnum': 5521, 'realtime_utc': '2025-12-15T10:48:41.770382+00:00'}]; message strings ['/var/log/journal/c103eaa6ed72493ca84e51a8eabc77ef/user-1001.journal: Journal file uses a different sequence number ID, rotating.', 'Started user@1001.service - User Manager for UID 1001.', 'Started session-c1.scope - Session c1 of User aecid.']
  - inetfw: 5 files, header range 2025-09-17T13:07:40.426054+00:00 .. 2025-12-15T11:44:42.404483+00:00
  - attacker: 6 files, header range 2025-12-10T13:43:21.585468+00:00 .. 2025-12-15T11:54:57.322882+00:00
  - linuxshare: 4 files, header range 2025-12-11T12:39:09.600830+00:00 .. 2025-12-15T11:54:34.684079+00:00
  - corpdns: 4 files, header range 2025-09-17T11:16:28.587737+00:00 .. 2025-12-15T11:44:42.225446+00:00
  - reposerver: 6 files, header range 2025-12-11T13:00:13.036184+00:00 .. 2025-12-15T11:54:10.672823+00:00
- **audit.log**: msg=audit(<unix epoch seconds.millis>:<serial>): epoch time => no timezone ambiguity (UTC).
  - inetfw: `type=PATH msg=audit(1758114460.424:2211): item=0 name="/var/log/" inode=80887 dev=fc:01 mode=040775 ouid=0 ogid=111 rdev=00:00 nametype=PARENT cap_fp=0 cap_fi=0 cap_fe=0 `  ...  `type=PROCTITLE msg=audit(1765799082.400:7815): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T13:07:18.688000+00:00 .. 2025-12-15T11:44:42.400000+00:00
  - linuxshare: `type=SYSCALL msg=audit(1765456749.600:1298): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55a1e6b7a250 a2=241 a3=1b6 items=2 ppid=13551 pid=13564 auid=1000`  ...  `type=PROCTITLE msg=audit(1765799674.648:4645): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-12-11T12:39:09.600000+00:00 .. 2025-12-15T11:54:34.648000+00:00
  - corpdns: `type=SYSCALL msg=audit(1758107788.584:2473): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=55ae93e00490 a2=241 a3=1b6 items=2 ppid=14993 pid=15006 auid=1000`  ...  `type=PROCTITLE msg=audit(1765799082.184:4540): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-09-17T11:16:28.584000+00:00 .. 2025-12-15T11:44:42.184000+00:00
  - reposerver: `type=SYSCALL msg=audit(1765458013.032:6157): arch=c000003e syscall=257 success=yes exit=3 a0=ffffff9c a1=56295ea51c30 a2=241 a3=1b6 items=2 ppid=32447 pid=32460 auid=1000`  ...  `type=PROCTITLE msg=audit(1765799650.536:18355): proctitle=7273796E63002D2D736572766572002D2D73656E646572002D6C4C6F674474727A652E4C73667843497675002E002F7661722F6C6F67`; range 2025-12-11T13:00:02.072000+00:00 .. 2025-12-15T11:54:10.536000+00:00
- **collectd.log**: '[YYYY-MM-DD HH:MM:SS]' without timezone; value lines carry a unix epoch. bracket_minus_epoch_seconds_observed == [0] means the bracket time equals UTC epoch time.
  - inetfw: `[2025-09-17 13:07:45] [info] write_log values:` / `atb-fw-image-2025-09-17t12-57-26z.cpu-0.cpu-user 20361 1758114465`; range 2025-09-17 13:07:45 .. 2025-12-15 11:44:38; bracket-epoch offsets [0]
  - linuxshare: `[2025-12-11 12:39:17] [info] write_log values:` / `linuxshare_attackbed_local.cpu-0.cpu-user 10015 1765456757`; range 2025-12-11 12:39:17 .. 2025-12-15 11:54:30; bracket-epoch offsets [0]
  - corpdns: `[2025-09-17 11:16:35] [info] write_log values:` / `atb-corpdns-image-2025-09-17t11-07-58z.cpu-0.cpu-user 18574 1758107795`; range 2025-09-17 11:16:35 .. 2025-12-15 11:44:37; bracket-epoch offsets [0]
  - reposerver: `[2025-12-11 13:00:15] [info] write_log values:` / `puppet_attackbed_local.cpu-0.cpu-user 12368 1765458015`; range 2025-12-11 13:00:15 .. 2025-12-15 11:54:02; bracket-epoch offsets [0]
- **attacker auth.log / syslog**: {"syslog": {"lines": 1710, "first": "2025-12-10T13:43:21.585726+00:00 atb-attacker-image-2025-12-10t12-35-00z x11vnc[26407]:  --- x11vnc loop: 92 ---", "last": "2025-12-15T11:54:57.082923+00:00 attacker systemd[1]: Started session-16.scope - Session 16 of User aecid.", "min": "2025-12-10T13:43:21.585726+00:00", "max": "2025-12-15T11:54:57.082923+00:00"}, "auth.log": {"lines": 184, "first": "2025-12-10T13:43:56.227741+00:00 atb-attacker-image-2025-12-10t12-35-00z sshd[1697]: Received disconnect from 10.110.0.254 port 41", "last": "2025-12-15T11:54:57.323310+00:00 attacker sudo: pam_unix(sudo:session): session opened for user root(uid=0) by aecid(uid=1001)", "min": "2025-12-10T13:43:56.227741+ ...(truncated)
- **Wazuh alerts**: timestamp example `2025-12-15T10:46:44.222+0000` (ISO 8601 with +0000 offset)
- **attackmate.json**: `start-datetime` e.g. `2025-12-15T11:02:51.184731`; no timezone
- host `/etc/timezone` files: {'wazuh': 'Etc/UTC', 'inetfw': 'Etc/UTC', 'attacker': 'Etc/UTC', 'linuxshare': 'Etc/UTC', 'corpdns': 'Etc/UTC', 'reposerver': 'Etc/UTC'}

### Alignment of attackmate times with host logs

attackmate first/last step: 2025-12-15T11:02:51.184731+00:00 .. 2025-12-15T11:13:30.318178+00:00 (read as UTC)

| Source | Host | Log min | Log max | First step inside | Last step inside |
|---|---|---|---|---|---|
| journal | inetfw | 2025-09-17T13:07:40.426054+00:00 | 2025-12-15T11:44:42.404483+00:00 | True | True |
| journal | attacker | 2025-12-10T13:43:21.585468+00:00 | 2025-12-15T11:54:57.322882+00:00 | True | True |
| journal | linuxshare | 2025-12-11T12:39:09.600830+00:00 | 2025-12-15T11:54:34.684079+00:00 | True | True |
| journal | corpdns | 2025-09-17T11:16:28.587737+00:00 | 2025-12-15T11:44:42.225446+00:00 | True | True |
| journal | reposerver | 2025-12-11T13:00:13.036184+00:00 | 2025-12-15T11:54:10.672823+00:00 | True | True |
| audit.log | inetfw | 2025-09-17T13:07:18.688000+00:00 | 2025-12-15T11:44:42.400000+00:00 | True | True |
| audit.log | linuxshare | 2025-12-11T12:39:09.600000+00:00 | 2025-12-15T11:54:34.648000+00:00 | True | True |
| audit.log | corpdns | 2025-09-17T11:16:28.584000+00:00 | 2025-12-15T11:44:42.184000+00:00 | True | True |
| audit.log | reposerver | 2025-12-11T13:00:02.072000+00:00 | 2025-12-15T11:54:10.536000+00:00 | True | True |
| collectd.log | inetfw | 2025-09-17 13:07:45 | 2025-12-15 11:44:38 | True | True |
| collectd.log | linuxshare | 2025-12-11 12:39:17 | 2025-12-15 11:54:30 | True | True |
| collectd.log | corpdns | 2025-09-17 11:16:35 | 2025-12-15 11:44:37 | True | True |
| collectd.log | reposerver | 2025-12-11 13:00:15 | 2025-12-15 11:54:02 | True | True |
| syslog | attacker | 2025-12-10T13:43:21.585726+00:00 | 2025-12-15T11:54:57.082923+00:00 | True | True |
| auth.log | attacker | 2025-12-10T13:43:56.227741+00:00 | 2025-12-15T11:54:57.323310+00:00 | True | True |
| wazuh alerts.json | wazuh | 2025-12-15T10:46:44.222000+00:00 | 2025-12-15T11:55:01.426000+00:00 | True | True |

sshd audit proximity (nearest sshd audit record to ssh-related steps):

```json
{"step_index": 2, "start_datetime": "2025-12-15T11:03:35.743321", "nearest_sshd_audit_record": {"host": "reposerver", "type": "type=USER_AUTH", "utc": "2025-12-15T11:03:37.088000+00:00", "delta_seconds_audit_minus_step": 1.345}}
{"step_index": 4, "start_datetime": "2025-12-15T11:04:05.173316", "nearest_sshd_audit_record": {"host": "reposerver", "type": "type=USER_AUTH", "utc": "2025-12-15T11:04:06.336000+00:00", "delta_seconds_audit_minus_step": 1.163}}
{"step_index": 6, "start_datetime": "2025-12-15T11:04:31.397715", "nearest_sshd_audit_record": {"host": "reposerver", "type": "type=USER_LOGIN", "utc": "2025-12-15T11:04:31.820000+00:00", "delta_seconds_audit_minus_step": 0.422}}
```
**Verdict:** consistent with UTC: 3/3 ssh-related steps have an sshd audit record within 30 s when the attackmate time is read as UTC.

### Run identification

- root folder(s): ['scenario_4'] (equals archive name: False)
- zip comment: ''; attackmate.json files: 1
- README files checked: 96; with scenario/run/simulation keywords: none
- .placeholder files: 39 (non-empty 33; example ('wazuh/configs/etc/cron.monthly/.placeholder', '# DO NOT EDIT OR REMOVE\n# This file is a simple placeholder to keep dpkg from re'))
- wazuh/facts.json: {'inventory_hostname': '192.168.100.130', 'group_names': ['wazuh'], 'gathered_iso8601': '2025-12-15T11:55:43Z', 'has_run_or_scenario_key': False}
- attackmate timeline: {'steps': 46, 'monotonic_non_decreasing': True, 'max_gap_seconds': 30.0, 'duration_seconds': 639.1}

## 4. Cross-scenario findings (computed)

- Wazuh files byte-identical across several archives (same name, size, CRC32): {'ossec-alerts-02.json (1052664 B)': ['scenario_1_sudo_pam', 'scenario_2_cron', 'scenario_3_vnc_apt', 'scenario_4'], 'ossec-alerts-02.log (1454934 B)': ['scenario_1_sudo_pam', 'scenario_2_cron', 'scenario_3_vnc_apt', 'scenario_4']}
- Host logs (journal/audit/collectd) start before the attack window (see ranges above), so they are not limited to the simulated attack.

## 5. Verified field table

| Field | Source file | Meaning | Ground truth or metadata | Evidence |
|---|---|---|---|---|
| start-datetime | attackmate.json | Step start time, ISO 8601 without timezone | metadata | scenario_1_sudo_pam: 2025-09-22T13:48:30.907163 .. 2025-09-22T14:10:54.791711; scenario_2_cron: 2025-10-01T10:14:14.955559 .. 2025-10-01T10:35:06.286635; scenario_3_vnc_apt: 2025-12-12T18:07:53.665927 .. 2025-12-12T18:34:13.417531; scenario_4: 2025-12-15T11:02:51.184731 .. 2025-12-15T11:13:30.318178 |
| type, cmd | attackmate.json | Attack tool/step kind and command executed by AttackMate | metadata | scenario_1_sudo_pam: 38 steps, types ['msf-module', 'msf-session', 'shell', 'sleep', 'ssh']; scenario_2_cron: 29 steps, types ['debug', 'mktemp', 'regex', 'sftp', 'shell', 'sleep']; scenario_3_vnc_apt: 77 steps, types ['include', 'loop', 'mktemp', 'msf-module', 'msf-payload', 'msf-session']; scenario_4: 46 steps, types ['shell', 'sleep', 'sliver', 'sliver-session', 'ssh', 'webserv'] |
| parameters.metadata.techniques | attackmate.json | ATT&CK technique IDs of the step; comma-separated string, may hold several IDs | GROUND TRUTH (label) | scenario_1_sudo_pam: 27/38 steps labeled; scenario_2_cron: 21/29 steps labeled; scenario_3_vnc_apt: 29/77 steps labeled; scenario_4: 22/46 steps labeled |
| parameters.metadata.tactics | attackmate.json | ATT&CK tactic names of the step; comma-separated string | GROUND TRUTH (label) | scenario_1_sudo_pam: 9 distinct tactics; scenario_2_cron: 9 distinct tactics; scenario_3_vnc_apt: 9 distinct tactics; scenario_4: 7 distinct tactics |
| parameters.metadata.technique_name | attackmate.json | Technique name text | GROUND TRUTH (label text) | scenario_1_sudo_pam: key present: True; scenario_2_cron: key present: True; scenario_3_vnc_apt: key present: True; scenario_4: key present: True |
| parameters.metadata.action / delayed_manifestation | attackmate.json | Meaning not documented in the archive (UNVERIFIED) | unverified | scenario_1_sudo_pam: absent; scenario_2_cron: absent; scenario_3_vnc_apt: {'action': 17, 'delayed_manifestation': 1}; scenario_4: absent |
| parameters.hostname / username / creates_session | attackmate.json | Target host / account / session of SSH-type steps (where present) | metadata | scenario_1_sudo_pam: hostname in 7 steps; scenario_2_cron: hostname in 3 steps; scenario_3_vnc_apt: hostname in 38 steps; scenario_4: hostname in 24 steps |
| rule.id, rule.level, rule.description | wazuh/logs/alerts/alerts.json | Wazuh rule that fired (detector output, not attack ground truth) | metadata (detector output) | scenario_1_sudo_pam: 500/500 alerts have rule.id; scenario_2_cron: 500/500 alerts have rule.id; scenario_3_vnc_apt: 661/661 alerts have rule.id; scenario_4: 598/598 alerts have rule.id |
| rule.mitre.id / tactic / technique | wazuh/logs/alerts/alerts.json | ATT&CK mapping attached by Wazuh rules; present on a subset; NOT the AttackMate truth | metadata (detector-derived label) | scenario_1_sudo_pam: 3/500 alerts; scenario_2_cron: 3/500 alerts; scenario_3_vnc_apt: 64/661 alerts; scenario_4: 103/598 alerts |
| timestamp, agent.name, location, full_log, data | wazuh alerts.json | Alert time (ISO 8601, +0000), source agent, log origin, raw log line | metadata | scenario_1_sudo_pam: agents ['atb-wazuh-image-2025-06-02t10-01-35z']; scenario_2_cron: agents ['atb-wazuh-image-2025-06-02t10-01-35z']; scenario_3_vnc_apt: agents ['wazuh', 'inetfw']; scenario_4: agents ['wazuh', 'inetfw'] |
| msg=audit(epoch:serial), type, syscall, AUID, UID ... | <host>/logs/log/audit/audit.log | Linux audit records (epoch UTC) | metadata | scenario_1_sudo_pam: records {'videoserver': 76306, 'inetfw': 26167, 'corpdns': 18118}; scenario_2_cron: records {'videoserver': 23649, 'inetfw': 26988, 'corpdns': 17022}; scenario_3_vnc_apt: records {'inetfw': 27385, 'linuxshare': 59917, 'corpdns': 14955, 'reposerver': 59869}; scenario_4: records {'inetfw': 29772, 'linuxshare': 18645, 'corpdns': 17203, 'reposerver': 62266} |
| [YYYY-MM-DD HH:MM:SS] + epoch metric lines | <host>/logs/log/collectd/collectd.log | collectd metric dump; no ground truth | metadata | scenario_1_sudo_pam: hosts ['corpdns', 'inetfw', 'videoserver']; scenario_2_cron: hosts ['corpdns', 'inetfw', 'videoserver']; scenario_3_vnc_apt: hosts ['corpdns', 'inetfw', 'linuxshare', 'reposerver']; scenario_4: hosts ['corpdns', 'inetfw', 'linuxshare', 'reposerver'] |
| journal entries (realtime in header/entry) | <host>/logs/log/journal/*.journal | Binary systemd journal; entry fields not decoded (UNVERIFIED) | metadata (unverified fields) | scenario_1_sudo_pam: hosts ['attacker', 'corpdns', 'inetfw', 'videoserver']; scenario_2_cron: hosts ['attacker', 'corpdns', 'inetfw', 'videoserver']; scenario_3_vnc_apt: hosts ['attacker', 'corpdns', 'inetfw', 'linuxshare', 'reposerver']; scenario_4: hosts ['attacker', 'corpdns', 'inetfw', 'linuxshare', 'reposerver'] |
| ISO timestamp, host, process | attacker/logs/log/auth.log, syslog | Attacker host text logs (ISO 8601 +00:00) | metadata | scenario_1_sudo_pam: ['auth.log', 'syslog']; scenario_2_cron: ['auth.log', 'syslog']; scenario_3_vnc_apt: ['auth.log', 'syslog']; scenario_4: ['auth.log', 'syslog'] |
| C3-style fields (threat score, priority, CTI confidence, freshness, asset criticality) | searched: attackmate.json keys, Wazuh alert top-level + rule.* keys | Not found by key-name search | absent (within the searched scope) | regex over parsed JSON key names; journal/audit/collectd text not searched for these names |

## 6. Unverified / open items

- Journal entry fields (`MESSAGE`, `_HOSTNAME`, ...) were not decoded; only header time ranges and uncompressed message strings were read.
- Meaning of `metadata.action` / `delayed_manifestation` is not documented in the archives.
- Whether each archive holds exactly one run: see per-scenario run identification; no explicit run ID was found in any README/placeholder.
- Mapping of AttackMate steps to individual host log events has not been done.

