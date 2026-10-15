# C3-C4 Telemetry Ingestion Interface Contract (FR8, NFR5)

> [!IMPORTANT]
> **STATUS: PROPOSED BY C4, PENDING C3 OWNER AGREEMENT**
> This interface contract defines the telemetry boundary between Component 3 (Investigation Prioritization)
> and Component 4 (Next-Step Attack Pattern Forecasting). All specifications here reflect C4's
> proposed requirements and remain subject to final agreement with the Component 3 owner.

---

## 1. Context and Architectural Boundaries

Component 3 ingests raw security signals and outputs a ranked investigation queue.
Component 4 consumes this structured telemetry to reconstruct incident progression timelines
and forecast the next ATT&CK techniques and tactics with explainable evidence.

- **Primary Source of Truth**: Proposal Section 4.3 input list.
- **Priority Domain (C3 FR-04)**: Categorical priority rankings restricted strictly to:
  `["Low", "Medium", "High", "Critical"]`.
- **Output Queue Specification (C3 FR-07)**: Structured JSON array representing chronological or prioritized event envelopes.

---

## 2. Field Specification and Proposed Alias Mapping

To ensure strict modularity and loose coupling (NFR5), C4 isolates field names via an **alias table**.
If Component 3 adopts alternate field names during upstream integration, updating the alias mapping in C4 is a single-line configuration change.

| Proposal Canonical Field (C4 Internal) | Proposed C3 Input Field | Accepted Alias(es) | Data Type | Nullable | Description / Semantics |
|:---|:---|:---|:---:|:---:|:---|
| `event_id` | `event_id` | `id`, `uuid` | string | No (auto-generated if absent) | Unique telemetry event identifier |
| `episode_id` | `episode_id` | `scenario_id`, `incident_id` | string | No | Episode boundary required for FR2 chronological segmentation |
| `timestamp` | `timestamp` | `time`, `datetime`, `observed_at` | string | No | ISO-8601 timestamp (parsed to UTC; original preserved) |
| `technique` | `technique` | `techniques`, `technique_id` | string \| list[string] | Yes | MITRE ATT&CK technique ID(s) (e.g. `T1059.004`) |
| `tactic` | `tactic` | `tactics`, `tactic_name` | string \| list[string] | Yes | MITRE ATT&CK tactic name(s) (e.g. `Execution`) |
| `incident_stage` | `incident_stage` | `stage`, `kill_chain_phase` | string | Yes | High-level attack progression stage |
| `affected_asset` | `affected_asset` | `host`, `hostname`, `asset` | string | Yes | Impacted endpoint, host, or resource |
| `asset_criticality` | `asset_criticality` | `criticality`, `host_criticality` | string | Yes | Business impact rating of asset |
| `ioc` | `ioc` | `indicator`, `observable` | string | Yes | Observable Indicator of Compromise (IP, hash, URI) |
| `ioc_type` | `ioc_type` | `indicator_type`, `observable_type` | string | Yes | Classification of the indicator |
| `local_occurrence` | `local_occurrence` | `count`, `frequency` | int \| dict | Yes | Local endpoint observation count |
| `cti_confidence` | `cti_confidence` | `confidence`, `threat_intel_confidence` | float | Yes | External threat intelligence score [0.0, 1.0] |
| `freshness` | `freshness` | `age_seconds`, `recency` | float | Yes | Time elapsed since indicator discovery |
| `threat_score` | `threat_score` | `c3_threat_score`, `score` | float | Yes | C3 automated threat assessment score |
| `investigation_priority`| `investigation_priority`| `priority`, `triage_priority` | string | Yes | C3 triage priority (`Low`, `Medium`, `High`, `Critical`) |

---

## 3. Mandatory Behavioral Rules (C4 Adapter Engine)

1. **Preservation of Unknown Extra Fields**: Any key present in an incoming C3 event that does not match the canonical schema is preserved under an `extra` dictionary. No telemetry attributes are ever silently dropped.
2. **Cryptographic Provenance (NFR3)**: Every incoming event is retained as an immutable deep copy, and its canonical SHA-256 digest is stored as `c3_event_sha256`.
3. **Deterministic Timestamp Parsing**: All timestamps are converted to ISO-8601 UTC. The exact raw string received is retained under `original_timestamp`.
4. **Deterministic Tie-Breaking**: When multiple events share the exact same timestamp, chronological ordering is broken deterministically by their original input stream index.
5. **Episode Isolation (FR2)**: Events belonging to distinct `episode_id` values are grouped strictly into isolated episodic timelines. Telemetry from separate episodes is never merged or cross-contaminated.
6. **Duplicate Telemetry Handling**: Events sharing identical `(episode_id, timestamp, sorted(techniques))` are detected, recorded in the `duplicates` return list with reason code `DUPLICATE_EVENT`, and flagged on the adapted event with `duplicate_flag = True`. Duplicate events are not quarantined or dropped; they are preserved on the chronological timeline and included in raw sequences. During sequence collapsing, consecutive events with identical technique sets are merged into a single transition state, with their event IDs aggregated in `event_ids` without information loss.
7. **Unlabeled Telemetry Handling**: Events lacking MITRE ATT&CK technique labels remain on the incident timeline for chronological fidelity, but are cleanly excluded from transition sequences with reason code `UNLABELED_STEP`.
8. **Rejection with Structured Error Codes**: Malformed events (missing required fields, unparseable timestamps, priority values outside the enum) are rejected with deterministic error codes:
   - `ERR_MISSING_REQUIRED_FIELD`
   - `ERR_INVALID_TIMESTAMP`
   - `ERR_INVALID_PRIORITY_ENUM`
   - `ERR_SCHEMA_VALIDATION_FAILURE`
