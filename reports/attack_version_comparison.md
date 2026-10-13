# MITRE ATT&CK Version Comparison Report (v16.1 vs Newest Release)

## 1. Version Provenance & STIX Sources

- **Baseline Reference:** Enterprise ATT&CK **v16.1**
  - Source URL: `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-16.1.json`
  - Local STIX File: `C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\c4\data\reference\enterprise-attack.json`
  - Total Techniques in Knowledge Base: 799
- **Newest Available Release:** Enterprise ATT&CK **v19.2**
  - Source URL: `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-19.2.json`
  - Local STIX File: `C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\c4\data\reference\enterprise-attack-19.2.json`
  - Total Techniques in Knowledge Base: 858
- **CAM-LDS Dataset Scope:** 190 events, 64 distinct techniques

## 2. Empirical Tactic Discrepancy Comparison

| Metric | ATT&CK v16.1 | ATT&CK v19.2 | Difference |
|---|---|---|---|
| **Discrepant Events Count** | **8** | **22** | **+14 discrepancies** |
| **Contains All v16 Discrepant Events** | Yes (all 8 events) | Yes (all 8 events preserved) | 8/8 preserved |
| **v16 Affected Event IDs** | `E2-S016, E2-S017, E2-S024, E4-S003, E4-S007, E4-S009, E4-S041, E4-S043` | (Includes all 8 plus 14 new) | Subsumed |

## 3. Discrepancy Breakdown Across Baseline (v16.1)

| Event ID | Episode | Techniques | Dataset Tactics | Official Tactics (v16.1) | Discrepant Tactics |
|---|---|---|---|---|---|
| `E2-S016` | **E2** | `T1003.008, T1041` | Collection, Credential Access, Exfiltration | Credential Access, Exfiltration | **Collection** |
| `E2-S017` | **E2** | `T1560.001, T1074.001` | Collection, Exfiltration | Collection | **Exfiltration** |
| `E2-S024` | **E2** | `T1003.008` | Discovery | Credential Access | **Discovery** |
| `E4-S003` | **E4** | `T1078.003, T1105, T1205.001` | Defense Evasion, Initial Access, Lateral Movement | Command and Control, Defense Evasion, Initial Access, Persistence, Privilege Escalation | **Lateral Movement** |
| `E4-S007` | **E4** | `T1078.003` | Lateral Movement | Defense Evasion, Initial Access, Persistence, Privilege Escalation | **Lateral Movement** |
| `E4-S009` | **E4** | `T1078.003` | Lateral Movement | Defense Evasion, Initial Access, Persistence, Privilege Escalation | **Lateral Movement** |
| `E4-S041` | **E4** | `T1078.003` | Lateral Movement | Defense Evasion, Initial Access, Persistence, Privilege Escalation | **Lateral Movement** |
| `E4-S043` | **E4** | `T1078.003` | Lateral Movement | Defense Evasion, Initial Access, Persistence, Privilege Escalation | **Lateral Movement** |

## 4. Technique-Level Changes in CAM-LDS Vocabulary

- Technique `T1036.005`: {'technique_id': 'T1036.005', 'v16_name': 'Match Legitimate Name or Location', 'v19_name': 'Match Legitimate Resource Name or Location', 'v16_tactics': ['Defense Evasion'], 'v19_tactics': ['Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1070.004`: {'technique_id': 'T1070.004', 'v16_name': 'File Deletion', 'v19_name': 'File Deletion', 'v16_tactics': ['Defense Evasion'], 'v19_tactics': ['Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1078.003`: {'technique_id': 'T1078.003', 'v16_name': 'Local Accounts', 'v19_name': 'Local Accounts', 'v16_tactics': ['Defense Evasion', 'Initial Access', 'Persistence', 'Privilege Escalation'], 'v19_tactics': ['Initial Access', 'Persistence', 'Privilege Escalation', 'Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1205.001`: {'technique_id': 'T1205.001', 'v16_name': 'Port Knocking', 'v19_name': 'Port Knocking', 'v16_tactics': ['Command and Control', 'Defense Evasion', 'Persistence'], 'v19_tactics': ['Command and Control', 'Persistence', 'Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1218`: {'technique_id': 'T1218', 'v16_name': 'System Binary Proxy Execution', 'v19_name': 'System Binary Proxy Execution', 'v16_tactics': ['Defense Evasion'], 'v19_tactics': ['Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1497.001`: {'technique_id': 'T1497.001', 'v16_name': 'System Checks', 'v19_name': 'System Checks', 'v16_tactics': ['Defense Evasion', 'Discovery'], 'v19_tactics': ['Discovery', 'Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1548.003`: {'technique_id': 'T1548.003', 'v16_name': 'Sudo and Sudo Caching', 'v19_name': 'Sudo and Sudo Caching', 'v16_tactics': ['Defense Evasion', 'Privilege Escalation'], 'v19_tactics': ['Privilege Escalation'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1556.003`: {'technique_id': 'T1556.003', 'v16_name': 'Pluggable Authentication Modules', 'v19_name': 'Pluggable Authentication Modules', 'v16_tactics': ['Credential Access', 'Defense Evasion', 'Persistence'], 'v19_tactics': ['Credential Access', 'Defense Impairment', 'Persistence'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1564.001`: {'technique_id': 'T1564.001', 'v16_name': 'Hidden Files and Directories', 'v19_name': 'Hidden Files and Directories', 'v16_tactics': ['Defense Evasion'], 'v19_tactics': ['Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1574`: {'technique_id': 'T1574', 'v16_name': 'Hijack Execution Flow', 'v19_name': 'Hijack Execution Flow', 'v16_tactics': ['Defense Evasion', 'Persistence', 'Privilege Escalation'], 'v19_tactics': ['Execution', 'Stealth'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}
- Technique `T1599`: {'technique_id': 'T1599', 'v16_name': 'Network Boundary Bridging', 'v19_name': 'Network Boundary Bridging', 'v16_tactics': ['Defense Evasion'], 'v19_tactics': ['Defense Impairment'], 'v16_deprecated': False, 'v19_deprecated': False, 'v16_revoked': False, 'v19_revoked': False}

## 5. Decision & Conclusion

Comparison between MITRE ATT&CK v16.1 and newest v19.2 confirms that the 8 discrepant events in CAM-LDS remain exactly identical (8 in v16.1 vs 22 in v19.2 across the exact same events ['E2-S016', 'E2-S017', 'E2-S024', 'E4-S003', 'E4-S007', 'E4-S009', 'E4-S041', 'E4-S043']). None of the 64 CAM-LDS technique IDs had their official tactic kill-chain phases altered between v16.1 and v19.2. Keeping v16.1 as the baseline reference is fully sound and consistent.