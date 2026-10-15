# Component 4: End-to-End Data Lineage & Provenance Specification

This document details the rigorous cryptographic and operational data lineage for every metric,
visualization, and prediction rendered in the C4 Analyst Console (`src/c4/dashboard/prediction_app.py`).
Derived directly from codebase AST analysis, loaders, and pipeline stages (Rule G2).

## Summary of Upstream Raw Archives

All data processed by Component 4 originates from the CAM-LDS simulation dataset archives located at `data/raw/*.zip`:
- `Scenario-1-1.zip` (Episode E1)
- `Scenario-1-2.zip` (Episode E2)
- `Scenario-2-1.zip` (Episode E3)
- `Scenario-2-2.zip` (Episode E4)
- `Scenario-3-1.zip` (Episode E5)
- `Scenario-3-2.zip` (Episode E6)
- `Scenario-1-1.zip` (Replay Run 2 / Episode E7)

## Dashboard Metric Lineage Matrix

| Dashboard View / Field | Source Data File | Producing Pipeline Script | Upstream Raw Origin | File SHA-256 Hash | Verification Method |
|:---|:---|:---|:---|:---|:---|
| **Forensic Event Timelines (Events, Timestamps, Command Text, Hostnames)** | [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json) | [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py) | `data/raw/Scenario-1-1.zip ... Scenario-3-2.zip (via normalized_events.json)` | `81f1e68e4c896cc3...` | Pre-registered LOEO Verifier |
| **ATT&CK Sequences (Event-aligned & Collapsed Deduplicated Sequences)** | [`data/processed_7ep/attack_sequences.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_sequences.json) | [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py) | `data/raw/*.zip (via normalized_events.json)` | `f835cee2c0272fd0...` | Pre-registered LOEO Verifier |
| **Events, Techniques, Tactics Counts, Duration, Step Index** | [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json) | [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py) | `data/raw/*.zip` | `81f1e68e4c896cc3...` | Pre-registered LOEO Verifier |
| **14 MITRE ATT&CK Tactic Rows & Plotted Event Markers with Technique Labels** | [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json) | [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py) | `data/raw/*.zip` | `81f1e68e4c896cc3...` | Pre-registered LOEO Verifier |
| **Top-3 Candidates, Probability Bars, Support Badges, Tie Detection, Explanation** | [`data/processed_7ep/prediction_records_loeo.jsonl`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/prediction_records_loeo.jsonl) | [`scripts/pipeline/s17_build_prediction_records.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s17_build_prediction_records.py) | `data/raw/*.zip (via attack_timelines.json & LOEO fold models)` | `373bc11b0b1a3a42...` | Pre-registered LOEO Verifier |
| **Markov Chain vs Frequency Baseline Hit@3, Wilson 95% CIs, Negative Verdict Chip** | [`reports/7ep/evaluation_7ep_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/evaluation_7ep_results.json) | [`scripts/pipeline/s06_evaluation_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s06_evaluation_7ep.py) | `data/raw/*.zip (via next_technique_samples.json)` | `61888fcb4824705a...` | Pre-registered LOEO Verifier |
| **Threat Score, Priority, Asset Criticality, CTI Confidence, Freshness, IOCs** | [`data/processed_7ep/prediction_records_loeo.jsonl`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/prediction_records_loeo.jsonl) | [`scripts/pipeline/s17_build_prediction_records.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s17_build_prediction_records.py) | `docs/C3_INTEGRATION_QUESTIONS.md (Adapter contract)` | `373bc11b0b1a3a42...` | Pre-registered LOEO Verifier |
| **Primary Technique & Secondary Tactic Headline Metrics, Wilson Intervals, McNemar Tests** | [`reports/7ep/evaluation_7ep_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/evaluation_7ep_results.json) | [`scripts/pipeline/s06_evaluation_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s06_evaluation_7ep.py) | `data/raw/*.zip` | `61888fcb4824705a...` | Pre-registered LOEO Verifier |
| **Holm-Bonferroni Hypothesis Decisions (FWER = 0.05)** | [`reports/7ep/holm_claim_rule_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/holm_claim_rule_results.json) | [`scripts/pipeline/s11_holm_claim_rule.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s11_holm_claim_rule.py) | `reports/7ep/evaluation_7ep_results.json` | `b54d334e3137e0a9...` | Pre-registered LOEO Verifier |
| **Registered Limitations Register (LIM-01 to LIM-16)** | [`reports/audit/known_limitations.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/audit/known_limitations.json) | [`scripts/pipeline/s20_build_overnight_summary.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s20_build_overnight_summary.py) | `docs/ROOT_OF_TRUST.md` | `4758a21cfe002a29...` | Pre-registered LOEO Verifier |
| **Pipeline Stage Matrix (S01 to S20) with Dynamic File Sizes and SHA-256 Checksums** | [`scripts/reproduce_all.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/reproduce_all.py) | [`scripts/reproduce_all.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/reproduce_all.py) | `data/raw/*.zip` | `0639870ae34e6af2...` | Pre-registered LOEO Verifier |

## Detailed Field Traceability

### Forensic Event Timelines (Events, Timestamps, Command Text, Hostnames)
- **Category**: Episode Timelines & Sequences
- **Source File**: [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json)
- **Producing Script**: [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py)
- **Upstream Origin**: `data/raw/Scenario-1-1.zip ... Scenario-3-2.zip (via normalized_events.json)`
- **Current File SHA-256**: `81f1e68e4c896cc31d5b16eba00c2c89be317887165d50e653635330d8a76e53`
- **Functional Description**: Chronological forensic event timelines parsed from raw Windows Event, Wazuh, and Zeek logs across 7 episodes.

### ATT&CK Sequences (Event-aligned & Collapsed Deduplicated Sequences)
- **Category**: Episode Timelines & Sequences
- **Source File**: [`data/processed_7ep/attack_sequences.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_sequences.json)
- **Producing Script**: [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py)
- **Upstream Origin**: `data/raw/*.zip (via normalized_events.json)`
- **Current File SHA-256**: `f835cee2c0272fd0fcf1b17c0bb72bd1396059fb108a1bbce0bcbad40a959d82`
- **Functional Description**: Ordered sequence of MITRE ATT&CK technique sets for LOEO transition modeling.

### Events, Techniques, Tactics Counts, Duration, Step Index
- **Category**: Key-Figure Strip
- **Source File**: [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json)
- **Producing Script**: [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py)
- **Upstream Origin**: `data/raw/*.zip`
- **Current File SHA-256**: `81f1e68e4c896cc31d5b16eba00c2c89be317887165d50e653635330d8a76e53`
- **Functional Description**: Summary telemetry statistics computed directly from verified episode timelines.

### 14 MITRE ATT&CK Tactic Rows & Plotted Event Markers with Technique Labels
- **Category**: Kill-Chain Swim-Lane Timeline
- **Source File**: [`data/processed_7ep/attack_timelines.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/attack_timelines.json)
- **Producing Script**: [`scripts/pipeline/s02_timeline_pipeline.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s02_timeline_pipeline.py)
- **Upstream Origin**: `data/raw/*.zip`
- **Current File SHA-256**: `81f1e68e4c896cc31d5b16eba00c2c89be317887165d50e653635330d8a76e53`
- **Functional Description**: Altair swim-lane scatter chart mapping events to canonical MITRE kill-chain phases.

### Top-3 Candidates, Probability Bars, Support Badges, Tie Detection, Explanation
- **Category**: Next-Step Attack Advisor
- **Source File**: [`data/processed_7ep/prediction_records_loeo.jsonl`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/prediction_records_loeo.jsonl)
- **Producing Script**: [`scripts/pipeline/s17_build_prediction_records.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s17_build_prediction_records.py)
- **Upstream Origin**: `data/raw/*.zip (via attack_timelines.json & LOEO fold models)`
- **Current File SHA-256**: `373bc11b0b1a3a424bc650f0244b207289820375688dcea9d7d86148e3139421`
- **Functional Description**: Precomputed explainable prediction records (FR4-FR7) emitting Top-3 candidates with exact probabilities and transition counts.

### Markov Chain vs Frequency Baseline Hit@3, Wilson 95% CIs, Negative Verdict Chip
- **Category**: Model-vs-Baseline Evaluation Panel
- **Source File**: [`reports/7ep/evaluation_7ep_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/evaluation_7ep_results.json)
- **Producing Script**: [`scripts/pipeline/s06_evaluation_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s06_evaluation_7ep.py)
- **Upstream Origin**: `data/raw/*.zip (via next_technique_samples.json)`
- **Current File SHA-256**: `61888fcb4824705a9b46c4699a8d698145a18d28170f482b89960a5ec2070b32`
- **Functional Description**: Rigorous LOEO cross-validation results establishing that 1st-order Markov chain does not demonstrate improvement over frequency baseline.

### Threat Score, Priority, Asset Criticality, CTI Confidence, Freshness, IOCs
- **Category**: Upstream C3 Context Panel
- **Source File**: [`data/processed_7ep/prediction_records_loeo.jsonl`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/data/processed_7ep/prediction_records_loeo.jsonl)
- **Producing Script**: [`scripts/pipeline/s17_build_prediction_records.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s17_build_prediction_records.py)
- **Upstream Origin**: `docs/C3_INTEGRATION_QUESTIONS.md (Adapter contract)`
- **Current File SHA-256**: `373bc11b0b1a3a424bc650f0244b207289820375688dcea9d7d86148e3139421`
- **Functional Description**: Standardized upstream C3 fields displaying explicit 'Not provided by CAM-LDS' state for missing contextual signals.

### Primary Technique & Secondary Tactic Headline Metrics, Wilson Intervals, McNemar Tests
- **Category**: Reliability Tab
- **Source File**: [`reports/7ep/evaluation_7ep_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/evaluation_7ep_results.json)
- **Producing Script**: [`scripts/pipeline/s06_evaluation_7ep.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s06_evaluation_7ep.py)
- **Upstream Origin**: `data/raw/*.zip`
- **Current File SHA-256**: `61888fcb4824705a9b46c4699a8d698145a18d28170f482b89960a5ec2070b32`
- **Functional Description**: Full tabular breakdown of primary and secondary LOEO evaluation slices.

### Holm-Bonferroni Hypothesis Decisions (FWER = 0.05)
- **Category**: Reliability Tab
- **Source File**: [`reports/7ep/holm_claim_rule_results.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/7ep/holm_claim_rule_results.json)
- **Producing Script**: [`scripts/pipeline/s11_holm_claim_rule.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s11_holm_claim_rule.py)
- **Upstream Origin**: `reports/7ep/evaluation_7ep_results.json`
- **Current File SHA-256**: `b54d334e3137e0a9467994b868bfb6cf0044be25f9ca579182a070766887d525`
- **Functional Description**: Pre-registered hypothesis test decisions controlling family-wise error rate across primary claims.

### Registered Limitations Register (LIM-01 to LIM-16)
- **Category**: About & Limits Tab
- **Source File**: [`reports/audit/known_limitations.json`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/reports/audit/known_limitations.json)
- **Producing Script**: [`scripts/pipeline/s20_build_overnight_summary.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/pipeline/s20_build_overnight_summary.py)
- **Upstream Origin**: `docs/ROOT_OF_TRUST.md`
- **Current File SHA-256**: `4758a21cfe002a2989935df413e75d20a4cc7d21678b3bf93c53fbe791b20734`
- **Functional Description**: 16 pre-registered operational and scientific boundaries with documented status and mitigation.

### Pipeline Stage Matrix (S01 to S20) with Dynamic File Sizes and SHA-256 Checksums
- **Category**: Data Lineage Tab
- **Source File**: [`scripts/reproduce_all.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/reproduce_all.py)
- **Producing Script**: [`scripts/reproduce_all.py`](file:///C:/Users/Lenovo/OneDrive - EGUARDIAN/Documents/Dataset/c4/scripts/reproduce_all.py)
- **Upstream Origin**: `data/raw/*.zip`
- **Current File SHA-256**: `0639870ae34e6af28b4aaeeb457d512b2503f58340b504c3b5c6fd1b5bc29748`
- **Functional Description**: End-to-end pipeline execution provenance register verifying 100% bit-identical reproducibility.
