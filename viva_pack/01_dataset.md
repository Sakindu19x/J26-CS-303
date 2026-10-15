# 01. CAM-LDS Dataset & Stage 1 Forensic Preprocessing

> [!NOTE]
> **Zenodo Reference**: Zenodo Record **18390560**  
> **Licence Status**: licence text not found locally - student to confirm

---

## 1. Raw CAM-LDS Simulation Archives

Component 4 evaluates forensic timeline reconstruction across seven attack simulation episodes ($E1$ through $E7$).
All seven raw archives reside in `data/raw/` with verified cryptographic SHA-256 checksums:

| Episode | Archive Filename | Size (Bytes) | SHA-256 Checksum | Scenario Description |
|:---:|:---|:---:|:---|:---|
| **E1** | `scenario_1_sudo_pam.zip` | 175,337,707 | `0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc` | Sudo PAM authentication bypass |
| **E2** | `scenario_2_cron.zip` | 160,486,494 | `b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791` | Scheduled cron job persistence |
| **E3** | `scenario_3_vnc_apt.zip` | 206,560,146 | `5c23b9d614689194f43cc844e4a25ed43568879ae83edc43df93336e0a33f911` | VNC remote access & APT package abuse |
| **E4** | `scenario_4.zip` | 201,474,676 | `a79fefbfeebd25b163e57f9ec7b9581f8e6f0abed2f2775fba45cf55a004b637` | Lateral movement & credential dumping |
| **E5** | `scenario_5.zip` | 202,788,200 | `e54df7f4c2f8e12e374272544809cee42b2c7e68ac37d950934e4123364f7911` | Multi-host pivoting & web exploit |
| **E6** | `scenario_6_macro_binary.zip` | 202,319,131 | `73a31bf763c5a65ed1a14bb5919151dbbf324563d4f8eaabb0c58d9c0f67f3b1` | Document macro & staged binary execution |
| **E7** | `scenario_7.zip` | 160,106,901 | `7f0ff0b5d939437b5ebad7f52eea69dc024775e5c73663c5b4ac7ba58f1b3a56` | Cloud API credential access & exfiltration |

---

## 2. Stage 1 Ingestion & Sample Counts

| Stage 1 Artifact | Tracked Path | Verified SHA-256 Checksum | Description / Sample Counts |
|:---|:---|:---|:---|
| **Normalized Events** | `data/processed_7ep/normalized_events.json` | `346919e2d23dd2937043de5f906e9e973a5b0860a85c99916a96cdc57ea6a9cd` | 274 total forensic events (190 labeled attack actions, 84 unlabeled system events) |
| **Attack Timelines** | `data/processed_7ep/attack_timelines.json` | `81f1e68e4c896cc31d5b16eba00c2c89be317887165d50e653635330d8a76e53` | 7 chronologically sorted episode timelines; zero cross-episode interleaving (FR2) |
| **Attack Sequences** | `data/processed_7ep/attack_sequences.json` | `f835cee2c0272fd0fcf1b17c0bb72bd1396059fb108a1bbce0bcbad40a959d82` | Raw and collapsed multi-technique attack steps per episode |
| **LOEO Prediction Samples** | `data/processed_7ep/next_technique_samples.json` | `a5b779f64904a4aeac5b1393e28f1b613756dc8f1d68fd2d9b30f30a11af9d24` | 95 collapsed-technique samples, 109 raw-technique samples, 76 collapsed-tactic samples |
