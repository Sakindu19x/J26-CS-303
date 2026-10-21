# Component 3 Interface: Open Questions for Component Owner

> [!NOTE]
> This document logs the open questions and assumptions formulated by Component 4 regarding
> upstream telemetry ingestion from Component 3. These items will be finalized during joint integration.

---

### Question 1: Incident / Episode Boundary Identification in Live Telemetry (FR2)
- **Current C4 Assumption**: In CAM-LDS datasets, episodes are explicitly partitioned by scenario folder (`scenario_1_sudo_pam`, etc.) and designated as `E1` through `E7`.
- **Question for C3 Owner**: In live production SIEM / EDR streaming, how does Component 3 identify the boundary of an incident or attack episode? Does C3 provide an explicit `episode_id`, `incident_id`, or `alert_cluster_id`, or is C4 expected to apply a sessionization timeout (e.g. 30 minutes of inactivity)?

---

### Question 2: Field Naming Conventions and Alias Table Agreement (NFR5)
- **Current C4 Assumption**: C4 uses proposal Section 4.3 names (`timestamp`, `technique`, `tactic`, `incident_stage`, `affected_asset`, `ioc`, `ioc_type`, `local_occurrence`, `cti_confidence`, `freshness`, `threat_score`, `investigation_priority`).
- **Question for C3 Owner**: Does Component 3 conform to these exact snake_case field names, or does C3 adhere to an existing industry schema (such as Elastic Common Schema - ECS, or Open Cybersecurity Schema Framework - OCSF)? If different, are our documented aliases sufficient?

---

### Question 3: Timestamp Time Zones and Sub-Second Precision
- **Current C4 Assumption**: Timestamps in CAM-LDS are in UTC or local time with known UTC correlation within 0.33s. C4 converts all parsed strings to UTC ISO-8601 while preserving the raw string.
- **Question for C3 Owner**: Are all timestamps emitted by C3 guaranteed to include an explicit time-zone offset (e.g., `+00:00` or `Z`), or can local timestamps without timezone offsets be received? What is the expected clock skew between distributed agents?

---

### Question 4: Null Semantics vs Missing Keys
- **Current C4 Assumption**: When an indicator, asset criticality, or CTI confidence is unavailable, C3 explicitly transmits `null` or omits the key. Both are treated equivalently by C4 as missing information without synthesizing values.
- **Question for C3 Owner**: Does C3 differentiate between an attribute that was *evaluated and confirmed absent* (e.g., no known IoC) versus *not evaluated / unknown*?

---

### Question 5: Threat Score Numerical Range and Scaling
- **Current C4 Assumption**: `threat_score` is a continuous floating-point score, defaulting to normalized $[0.0, 1.0]$ or $[0, 100]$.
- **Question for C3 Owner**: What is the exact mathematical range and distribution of `threat_score` emitted by C3? Is it bounded, and are higher values strictly indicative of higher malicious confidence?

---

### Question 6: Investigation Priority Categorical Levels (FR-04)
- **Current C4 Assumption**: Per proposal C3 FR-04, priority values are strictly categorical: `"Low"`, `"Medium"`, `"High"`, `"Critical"`.
- **Question for C3 Owner**: Are there any additional priority buckets (e.g., `"Informational"` or `"Emergency"`), and are priorities guaranteed to use Title Case?

---

### Question 7: Duplicate Telemetry Handling Policy
- **Authoritative C4 Implementation (`src/c4/c3_adapter.py`)**: Events sharing identical `(episode_id, timestamp, sorted(techniques))` are detected, recorded in the `duplicates` return list with reason code `DUPLICATE_EVENT`, and flagged with `duplicate_flag = True`. They are retained on the chronological timeline and in raw sequences; during collapsing, consecutive identical technique sets are merged into a single state with aggregated `event_ids`. Duplicate events are never dropped or quarantined.
- **Question for C3 Owner**: When duplicate events arrive with differing `threat_score` or C3 contextual values, should C4 retain the first observation, the last observation, or merge contextual metadata?

---

### Question 8: Multi-Technique Event Splitting
- **Current C4 Assumption**: In CAM-LDS, certain atomic actions invoke multiple ATT&CK techniques simultaneously (e.g., `T1590.002` and `T1591` in a single command). C4 treats these as a set-valued transition step.
- **Question for C3 Owner**: Does C3 emit one event per detected technique, or can a single event object contain a list of techniques?
