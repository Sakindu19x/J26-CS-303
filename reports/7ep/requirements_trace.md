# Component 4 Requirements Traceability Matrix

> [!IMPORTANT]
> **SYSTEM REQUIREMENTS VERIFICATION AUDIT (G-P5-6)**
> Generated on: 2026-10-15T00:00:00Z
> This document maps every functional requirement (FR1-FR9) and non-functional
> requirement (NFR1-NFR6) to its implementation scripts, explainable prediction record
> fields, and automated regression tests.

## 1. Functional Requirements Matrix (FR1 - FR9)

| ID | Title | Scope | Implementation | Record Field | Automated Verification | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **FR1** | Raw Telemetry Ingestion and Normalization | CAM-LDS audit logs to normalized events | `src/c4/normalization.py`, `scripts/build_stage1_7ep.py` | `input_events_sha256`, `input.event_index`, `input.last_timestamp` | `tests/test_normalization.py`, `tests/test_stage1_7ep.py` | **PASS** |
| **FR2** | Chronological Episode Segmentation | Split audit stream by scenario episodes without cross-contamination | `src/c4/episodes.py`, `src/c4/timeline.py` | `input.episode_id`, `model.training_episodes` | `tests/test_timeline_and_sequences.py`, `tests/test_samples_and_stats.py` | **PASS** |
| **FR3** | MITRE ATT&CK Mapping & Reference Catalog | Technique and tactic reference standardization | `src/c4/mitre_reference.py`, `data/processed_7ep/technique_tactic_reference.json` | `input.current_technique_set`, `input.current_tactic_set`, `candidate.tactics` | `tests/test_intake_audit.py`, `tests/test_tactic_evaluation.py` | **PASS** |
| **FR4** | Ranked Candidate Predictions | Next-step technique and tactic candidate ranking | `src/c4/models/markov.py`, `src/c4/models/frequency.py`, `src/c4/prediction_record.py` | `ranked_candidates[].candidate_id`, `ranked_candidates[].score` | `tests/test_models.py`, `tests/test_evaluation_7ep.py`, `tests/test_prediction_record.py` | **PASS** |
| **FR5** | Empirical Evidence Basis | Transition counts, denominators, and supporting episodes | `src/c4/prediction_record.py`, `scripts/build_prediction_records.py` | `ranked_candidates[].numerator`, `denominator`, `supporting_episodes_count`, `supporting_episode_ids` | `tests/test_prediction_record.py`, `scripts/verify_prediction_records.py` | **PASS** |
| **FR6** | Explainability Surface & Tie Handling | Alternative candidates, tie flags, and deterministic template explanations | `src/c4/prediction_record.py` | `alternatives`, `tie_flags.tie_at_top1`, `tie_flags.tie_at_top3_boundary`, `explanation` | `tests/test_prediction_record.py` | **PASS** |
| **FR7** | Confidence Calibration & Reliability Banner | Score labeling and empirical reliability context | `src/c4/prediction_record.py` | `ranked_candidates[].score_type`, `measured_reliability_banner` | `tests/test_prediction_record.py` | **PASS** |
| **FR8** | C3 Telemetry Ingestion Interface | C3 event adapter, priority levels, and triage interface | `schemas/c3_event.schema.json`, `src/c4/c3_adapter.py` | `input.c3_fields.*` | `tests/test_c3_adapter.py` | *null until C3 integration* |
| **FR9** | Analyst Interface & Feedback Surface | Prediction display panel and analyst evaluation form | `src/c4/dashboard.py`, `docs/analyst_feedback_form.md` | Rendered from `prediction_records_loeo.jsonl` | `tests/test_dashboard.py` | *null until C3 integration* |

## 2. Non-Functional Requirements Matrix (NFR1 - NFR6)

| ID | Title | Scope | Implementation | Record Field | Automated Verification | Status |
|:---|:---|:---|:---|:---|:---|:---:|
| **NFR1** | Performance and Execution Latency | Median <= 2.0s, P95 <= 5.0s warm; <= 10s cold start | `scripts/measure_nfr1.py` | Benchmarked end-to-end record generation latency | `scripts/measure_nfr1.py` | **PASS** |
| **NFR2** | Deterministic Reproducibility | Identical output across executions, platforms, and random seeds | `scripts/build_prediction_records.py` | `record_id`, `record_sha256`, `input_events_sha256` | `tests/test_prediction_record.py` | **PASS** |
| **NFR3** | Cryptographic Integrity and Non-Modification | Raw inputs and telemetry deep-frozen; cryptographic provenance hashes | `scripts/verify_all_hashes.py`, `src/c4/prediction_record.py` | `model.model_file_sha256`, `input_events_sha256`, `record_sha256` | `tests/test_prediction_record.py`, `scripts/verify_all_hashes.py` | **PASS** |
| **NFR4** | Usability and Interpretability for Analysts | Clear evidence, explanations, and feedback mechanism | `docs/analyst_feedback_form.md`, `reports/7ep/prediction_record_examples.md` | `explanation`, `measured_reliability_banner` | `tests/test_prediction_record.py` | **PASS** |
| **NFR5** | Modularity and Loose Coupling | Decoupled C3-C4 interface with alias table and contract | `docs/c3_c4_interface_contract.md`, `src/c4/c3_adapter.py` | `input.c3_fields` | `tests/test_c3_adapter.py` | **PASS** |
| **NFR6** | Schema Compliance and Validation | Formal JSON Schema specification and automated validation | `schemas/c4_prediction_record.schema.json` | `schema_version` | `tests/test_prediction_record.py`, `scripts/verify_prediction_records.py` | **PASS** |

## 3. Requirement Details and Trace Notes

### FR1: Raw Telemetry Ingestion and Normalization

- **Requirement ID**: `FR1`
- **Scope**: CAM-LDS audit logs to normalized events
- **Implementation**: `src/c4/normalization.py`, `scripts/build_stage1_7ep.py`
- **Prediction Record Field(s)**: `input_events_sha256`, `input.event_index`, `input.last_timestamp`
- **Automated Verification**: `tests/test_normalization.py`, `tests/test_stage1_7ep.py`
- **Status**: **PASS**
- **Audit Notes**: Ingests 274 events across 7 episodes with zero schema errors.

### FR2: Chronological Episode Segmentation

- **Requirement ID**: `FR2`
- **Scope**: Split audit stream by scenario episodes without cross-contamination
- **Implementation**: `src/c4/episodes.py`, `src/c4/timeline.py`
- **Prediction Record Field(s)**: `input.episode_id`, `model.training_episodes`
- **Automated Verification**: `tests/test_timeline_and_sequences.py`, `tests/test_samples_and_stats.py`
- **Status**: **PASS**
- **Audit Notes**: Strict within-episode ordering; zero cross-episode transition leakage verified.

### FR3: MITRE ATT&CK Mapping & Reference Catalog

- **Requirement ID**: `FR3`
- **Scope**: Technique and tactic reference standardization
- **Implementation**: `src/c4/mitre_reference.py`, `data/processed_7ep/technique_tactic_reference.json`
- **Prediction Record Field(s)**: `input.current_technique_set`, `input.current_tactic_set`, `candidate.tactics`
- **Automated Verification**: `tests/test_intake_audit.py`, `tests/test_tactic_evaluation.py`
- **Status**: **PASS**
- **Audit Notes**: Maps 100% of labeled techniques to official ATT&CK tactics.

### FR4: Ranked Candidate Predictions

- **Requirement ID**: `FR4`
- **Scope**: Next-step technique and tactic candidate ranking
- **Implementation**: `src/c4/models/markov.py`, `src/c4/models/frequency.py`, `src/c4/prediction_record.py`
- **Prediction Record Field(s)**: `ranked_candidates[].candidate_id`, `ranked_candidates[].score`
- **Automated Verification**: `tests/test_models.py`, `tests/test_evaluation_7ep.py`, `tests/test_prediction_record.py`
- **Status**: **PASS**
- **Audit Notes**: Top-k candidates and order equal evaluation_7ep_predictions.csv (Gate G-P5-1).

### FR5: Empirical Evidence Basis

- **Requirement ID**: `FR5`
- **Scope**: Transition counts, denominators, and supporting episodes
- **Implementation**: `src/c4/prediction_record.py`, `scripts/build_prediction_records.py`
- **Prediction Record Field(s)**: `ranked_candidates[].numerator`, `denominator`, `supporting_episodes_count`, `supporting_episode_ids`
- **Automated Verification**: `tests/test_prediction_record.py`, `scripts/verify_prediction_records.py`
- **Status**: **PASS**
- **Audit Notes**: Transition weights independently recounted and verified to within 1e-9 (Gate G-P5-2).

### FR6: Explainability Surface & Tie Handling

- **Requirement ID**: `FR6`
- **Scope**: Alternative candidates, tie flags, and deterministic template explanations
- **Implementation**: `src/c4/prediction_record.py`
- **Prediction Record Field(s)**: `alternatives`, `tie_flags.tie_at_top1`, `tie_flags.tie_at_top3_boundary`, `explanation`
- **Automated Verification**: `tests/test_prediction_record.py`
- **Status**: **PASS**
- **Audit Notes**: Surfaces ranks 4..k alternatives, boundary tie flags, and human-readable rationale.

### FR7: Confidence Calibration & Reliability Banner

- **Requirement ID**: `FR7`
- **Scope**: Score labeling and empirical reliability context
- **Implementation**: `src/c4/prediction_record.py`
- **Prediction Record Field(s)**: `ranked_candidates[].score_type`, `measured_reliability_banner`
- **Automated Verification**: `tests/test_prediction_record.py`
- **Status**: **PASS**
- **Audit Notes**: Fallback labeled as training_frequency_share; reliability banner includes Wilson 95% CIs.

### FR8: C3 Telemetry Ingestion Interface

- **Requirement ID**: `FR8`
- **Scope**: C3 event adapter, priority levels, and triage interface
- **Implementation**: `schemas/c3_event.schema.json`, `src/c4/c3_adapter.py`
- **Prediction Record Field(s)**: `input.c3_fields.*`
- **Automated Verification**: `tests/test_c3_adapter.py`
- **Status**: **null until C3 integration**
- **Audit Notes**: Contract specified; C3 fields passed through as null in historical CAM-LDS data.

### FR9: Analyst Interface & Feedback Surface

- **Requirement ID**: `FR9`
- **Scope**: Prediction display panel and analyst evaluation form
- **Implementation**: `src/c4/dashboard.py`, `docs/analyst_feedback_form.md`
- **Prediction Record Field(s)**: Rendered from `prediction_records_loeo.jsonl`
- **Automated Verification**: `tests/test_dashboard.py`
- **Status**: **null until C3 integration**
- **Audit Notes**: Dashboard displays prediction records in demo mode; live feedback queue awaiting C3.

### NFR1: Performance and Execution Latency

- **Requirement ID**: `NFR1`
- **Scope**: Median <= 2.0s, P95 <= 5.0s warm; <= 10s cold start
- **Implementation**: `scripts/measure_nfr1.py`
- **Prediction Record Field(s)**: Benchmarked end-to-end record generation latency
- **Automated Verification**: `scripts/measure_nfr1.py`
- **Status**: **PASS**
- **Audit Notes**: Execution timing benchmarked across 7 episodes with 30 warm repetitions.

### NFR2: Deterministic Reproducibility

- **Requirement ID**: `NFR2`
- **Scope**: Identical output across executions, platforms, and random seeds
- **Implementation**: `scripts/build_prediction_records.py`
- **Prediction Record Field(s)**: `record_id`, `record_sha256`, `input_events_sha256`
- **Automated Verification**: `tests/test_prediction_record.py`
- **Status**: **PASS**
- **Audit Notes**: Gate G-P5-3: byte-identical JSONL across PYTHONHASHSEED=0, 1, 4242.

### NFR3: Cryptographic Integrity and Non-Modification

- **Requirement ID**: `NFR3`
- **Scope**: Raw inputs and telemetry deep-frozen; cryptographic provenance hashes
- **Implementation**: `scripts/verify_all_hashes.py`, `src/c4/prediction_record.py`
- **Prediction Record Field(s)**: `model.model_file_sha256`, `input_events_sha256`, `record_sha256`
- **Automated Verification**: `tests/test_prediction_record.py`, `scripts/verify_all_hashes.py`
- **Status**: **PASS**
- **Audit Notes**: Gate G-P5-4: deep-frozen inputs non-modification verified.

### NFR4: Usability and Interpretability for Analysts

- **Requirement ID**: `NFR4`
- **Scope**: Clear evidence, explanations, and feedback mechanism
- **Implementation**: `docs/analyst_feedback_form.md`, `reports/7ep/prediction_record_examples.md`
- **Prediction Record Field(s)**: `explanation`, `measured_reliability_banner`
- **Automated Verification**: `tests/test_prediction_record.py`
- **Status**: **PASS**
- **Audit Notes**: Exemplars report and 8-question feedback form documented.

### NFR5: Modularity and Loose Coupling

- **Requirement ID**: `NFR5`
- **Scope**: Decoupled C3-C4 interface with alias table and contract
- **Implementation**: `docs/c3_c4_interface_contract.md`, `src/c4/c3_adapter.py`
- **Prediction Record Field(s)**: `input.c3_fields`
- **Automated Verification**: `tests/test_c3_adapter.py`
- **Status**: **PASS**
- **Audit Notes**: Field alias table isolates C4 from upstream telemetry rename changes.

### NFR6: Schema Compliance and Validation

- **Requirement ID**: `NFR6`
- **Scope**: Formal JSON Schema specification and automated validation
- **Implementation**: `schemas/c4_prediction_record.schema.json`
- **Prediction Record Field(s)**: `schema_version`
- **Automated Verification**: `tests/test_prediction_record.py`, `scripts/verify_prediction_records.py`
- **Status**: **PASS**
- **Audit Notes**: Gate G-P5-5: 100% of prediction records validate against draft-07 schema.

