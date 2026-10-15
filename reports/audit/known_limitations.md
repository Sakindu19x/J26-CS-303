# Known Limitations Register

Generated automatically by `scripts/build_known_limitations.py` from `reports/audit/known_limitations.json`.
Documents all identified project limitations, tracking resolution status across development phases.

**Summary**: 16 total limitations recorded (7 CLOSED, 1 MITIGATED, 2 EXPLAINED, 6 OPEN).

## 1. Limitations Summary Table

| ID | Title | Category | Status | Evidence File / Target Phase |
|:---|:---|:---|:---:|:---|
| **LIM-01** | Small Initial Sample Size (4 Episodes) | Dataset Scope | **CLOSED** | `reports/7ep/evaluation_7ep_results.json` |
| **LIM-02** | Cross-Scenario Technique Vocabulary Isolation | Domain Generalization | *EXPLAINED* | `reports/7ep/evaluation_7ep_results.json` |
| **LIM-03** | Episode E5 Sample Imbalance | Data Quality | **CLOSED** | `reports/7ep/e5_removed_results.json` |
| **LIM-04** | Artificial Duplicates in Permutation Scheme S2 | Statistical Methodology | **CLOSED** | `reports/prereg_7episode_design.md` |
| **LIM-05** | Speculative Wording in Permutation Test Scripts | Reporting Neutrality | **CLOSED** | `reports/7ep/permutation_7ep_report.md` |
| **LIM-06** | Synthetic Planted Structure Gate G8 Bound Sensitivity | Simulation Validation | **CLOSED** | `reports/7ep/planted_realscale_7ep_report.json` |
| **LIM-07** | Historical Intermediary A2 Scratch Run Reproducibility | Provenance Integrity | **CLOSED** | `reports/audit/history/overnight_ledger_old.md` |
| **LIM-08** | Absence of Live Operational C3 Metadata in CAM-LDS | Interface Contract | *OPEN* | Pending C3 / Live Deploy |
| **LIM-09** | Real-Time Streaming Ingestion and Dynamic Episode Demarcation | Operational Deployment | *OPEN* | Pending C3 / Live Deploy |
| **LIM-10** | Higher-Order Context Memory ($k \ge 2$ Markov Dynamics) | Model Expressiveness | *OPEN* | Pending C3 / Live Deploy |
| **LIM-11** | Clean Clone Shares Parent Virtual Environment | Environment Isolation | *OPEN* | Pending C3 / Live Deploy |
| **LIM-12** | Dashboard Visual Artifacts Static Renders vs Live Captures | Visualization Telemetry | **CLOSED** | `reports/measurements/live_capture_log.txt` |
| **LIM-13** | C3 Interface Contract Unagreed by Component 3 | Integration Governance | *OPEN* | Pending C3 / Live Deploy |
| **LIM-14** | High Proportion of Low-Support Predictions (92/171 Cautioned) | Statistical Support | **MITIGATED** | `data/processed_7ep/prediction_records_loeo.jsonl` |
| **LIM-15** | Streamlit Readiness Metric Measures Health Endpoint, Not First Render | Performance Measurement | *OPEN* | Pending C3 / Live Deploy |
| **LIM-16** | Prompt 14 Unattended Agent Log Access Procedural Violation | Agentic Execution Governance | *EXPLAINED* | `docs/prompts/prompt15.md` |

## 2. Detailed Register Entries

### LIM-01: Small Initial Sample Size (4 Episodes)

- **Category**: Dataset Scope
- **Status**: `CLOSED`
- **Evidence File**: `reports/7ep/evaluation_7ep_results.json`
- **Resolution Commit**: `2cf7786`
- **Description**: The initial 4-episode evaluation (N=67) had limited statistical power to differentiate fine-grained sequence dynamics.
- **Resolution / Mitigation**: Expanded to 7 episodes (E1-E7, N=95) with formal pre-registration, LOEO cross-validation, and power analysis.

### LIM-02: Cross-Scenario Technique Vocabulary Isolation

- **Category**: Domain Generalization
- **Status**: `EXPLAINED`
- **Evidence File**: `reports/7ep/evaluation_7ep_results.json`
- **Resolution Commit**: `d6f3764`
- **Description**: Technique-level attack patterns exhibit cross-scenario vocabulary isolation across disparate campaigns, causing severe coverage and reachability bottlenecks.
- **Resolution / Mitigation**: Quantified via Target Reachability Ceiling (62.11%) and Perfect-Order Prediction Cap (64.98%), formally explaining the performance gap.

### LIM-03: Episode E5 Sample Imbalance

- **Category**: Data Quality
- **Status**: `CLOSED`
- **Evidence File**: `reports/7ep/e5_removed_results.json`
- **Resolution Commit**: `3a6b306`
- **Description**: Episode E5 contains only 3 labeled events (2 collapsed transitions), resulting in zero coverage under LOEO cross-validation.
- **Resolution / Mitigation**: Conducted full side-by-side sensitivity analysis with E5 removed (6-fold LOEO, N=93 technique and 74 tactic, read from e5_removed_results.json) confirming all conclusions hold independently of E5.

### LIM-04: Artificial Duplicates in Permutation Scheme S2

- **Category**: Statistical Methodology
- **Status**: `CLOSED`
- **Evidence File**: `reports/prereg_7episode_design.md`
- **Resolution Commit**: `14f3b89`
- **Description**: Unconstrained adjacent shuffling in Scheme S2 generated consecutive identical transitions that never occur in collapsed empirical sequences.
- **Resolution / Mitigation**: Formally excluded S2 from 7-episode design in pre-registration; adopted Scheme S1 (headline) and Scheme S3 (rejection-sampled constrained shuffle).

### LIM-05: Speculative Wording in Permutation Test Scripts

- **Category**: Reporting Neutrality
- **Status**: `CLOSED`
- **Evidence File**: `reports/7ep/permutation_7ep_report.md`
- **Resolution Commit**: `14f3b89`
- **Description**: Reporting scripts included causal speculation regarding adjacency constraints and ambiguous wording on Markov-minus-Frequency rows.
- **Resolution / Mitigation**: Neutralized under Amendment 6 to factual difference statistic descriptions and explicit disclaimers regarding hypothesis test boundaries.

### LIM-06: Synthetic Planted Structure Gate G8 Bound Sensitivity

- **Category**: Simulation Validation
- **Status**: `CLOSED`
- **Evidence File**: `reports/7ep/planted_realscale_7ep_report.json`
- **Resolution Commit**: `14f3b89`
- **Description**: At small sample sizes with V=82, estimator recovery bound for G8 was loose relative to large-sample asymptotics.
- **Resolution / Mitigation**: Documented in planted real-scale report; G9 (monotonicity) and G10 (reachability recovery) passed unconditionally.

### LIM-07: Historical Intermediary A2 Scratch Run Reproducibility

- **Category**: Provenance Integrity
- **Status**: `CLOSED`
- **Evidence File**: `reports/audit/history/overnight_ledger_old.md`
- **Resolution Commit**: `d4557f4`
- **Description**: Intermediary files from early exploratory 4-episode A2 scratch exploration lacked fixed seeds in exploratory scripts.
- **Resolution / Mitigation**: Isolated strictly to early scratch exploration history; all benchmark code, final reports, and baseline hashes are frozen and verified.

### LIM-08: Absence of Live Operational C3 Metadata in CAM-LDS

- **Category**: Interface Contract
- **Status**: `OPEN`
- **Description**: The open-source CAM-LDS benchmark lacks operational SOC telemetry fields (threat score, investigation priority, asset criticality, CTI confidence, IoCs).
- **Resolution / Mitigation**: C4 prediction record and C3 adapter support pass-through with explicit null semantics pending live integration agreement with C3 owner.

### LIM-09: Real-Time Streaming Ingestion and Dynamic Episode Demarcation

- **Category**: Operational Deployment
- **Status**: `OPEN`
- **Description**: Benchmark operates on demarcated retrospective episodes; real-time SOC deployment requires automated session boundary detection and sliding window aggregation.
- **Resolution / Mitigation**: Marked as an open research/engineering question in docs/c3_open_questions.md for Stage 3 production deployment.

### LIM-10: Higher-Order Context Memory ($k \ge 2$ Markov Dynamics)

- **Category**: Model Expressiveness
- **Status**: `OPEN`
- **Description**: First-order Markov chains only condition on the immediate previous transition state, ignoring multi-step attack history.
- **Resolution / Mitigation**: Exploratory analysis showed severe state space sparsity even at order 1; higher-order models require substantially larger cross-enterprise corpora.

### LIM-11: Clean Clone Shares Parent Virtual Environment

- **Category**: Environment Isolation
- **Status**: `OPEN`
- **Description**: Clean-clone reproduction scripts run in an isolated clone directory but execute using the parent workspace's Python virtual environment (`..\.venv\Scripts\python.exe`), rather than provisioning a fresh venv from scratch each time.
- **Resolution / Mitigation**: Environment parity is verified by comparing `pip freeze` against `requirements.lock.txt`.

### LIM-12: Dashboard Visual Artifacts Static Renders vs Live Captures

- **Category**: Visualization Telemetry
- **Status**: `CLOSED`
- **Evidence File**: `reports/measurements/live_capture_log.txt`
- **Resolution Commit**: `e33e008`
- **Description**: Headless Chrome CLI captures only the initial WebSocket SPA skeleton. Dashboard captures rely on high-fidelity static renders unless live interactive Playwright automation succeeds.
- **Resolution / Mitigation**: Prompt 15 R4(d) successfully executed interactive Playwright live capture in a dedicated venv (C:\c4_capture_venv) with channel='chrome', producing reports/measurements/live_*.png alongside static renders.

### LIM-13: C3 Interface Contract Unagreed by Component 3

- **Category**: Integration Governance
- **Status**: `OPEN`
- **Description**: The C3-C4 interface format (src/c4/c3_adapter.py, docs/c3_c4_interface_contract.md) was proposed and implemented by Component 4, but has not been formally agreed or ratified by the Component 3 team.
- **Resolution / Mitigation**: Status recorded as PARTIAL in requirements trace; adapter tested and validated against C4 internal fixtures only.

### LIM-14: High Proportion of Low-Support Predictions (92/171 Cautioned)

- **Category**: Statistical Support
- **Status**: `MITIGATED`
- **Evidence File**: `data/processed_7ep/prediction_records_loeo.jsonl`
- **Resolution Commit**: `c6efee4`
- **Description**: 92 out of 171 LOEO prediction records (53.80%) rest on low historical support (<2 supporting episodes or <3 state transitions), reflecting benchmark state space sparsity.
- **Resolution / Mitigation**: Schema v1.1.0 enforces mandatory support caution flags and narrative warnings on all 92 low-support records, preventing over-confident claims; 92/171 records remain low-support due to benchmark dataset constraints.

### LIM-15: Streamlit Readiness Metric Measures Health Endpoint, Not First Render

- **Category**: Performance Measurement
- **Status**: `OPEN`
- **Description**: Reported Streamlit startup/ready times measure HTTP 200 response latency on the `_stcore/health` endpoint rather than client-side first DOM paint or WebSocket handshake completion.
- **Resolution / Mitigation**: Clarified in measurement documentation and known limitations; AppTest used for full headless DOM and component validation.

### LIM-16: Prompt 14 Unattended Agent Log Access Procedural Violation

- **Category**: Agentic Execution Governance
- **Status**: `EXPLAINED`
- **Evidence File**: `docs/prompts/prompt15.md`
- **Resolution Commit**: `6e58efc`
- **Description**: During Prompt 14 unattended execution, the coding assistant accessed conversation transcript and task log files directly, violating procedural constraints on state contamination.
- **Resolution / Mitigation**: Incident recorded in project governance; rules for Prompt 15 and Prompt 16 strictly forbid opening conversation transcript files, task logs, or brain\ logs.
