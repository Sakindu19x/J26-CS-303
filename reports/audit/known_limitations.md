# Known Limitations Register

Generated automatically by `scripts/build_known_limitations.py` from `reports/audit/known_limitations.json`.
Documents all identified project limitations, tracking resolution status across development phases.

**Summary**: 10 total limitations recorded (7 CLOSED, 3 OPEN).

## 1. Limitations Summary Table

| ID | Title | Category | Status | Resolution / Target Phase |
|:---|:---|:---|:---:|:---|
| **LIM-01** | Small Initial Sample Size (4 Episodes) | Dataset Scope | **CLOSED** | `2cf7786` |
| **LIM-02** | Cross-Scenario Technique Vocabulary Isolation | Domain Generalization | **CLOSED** | `d6f3764` |
| **LIM-03** | Episode E5 Sample Imbalance | Data Quality | **CLOSED** | `3a6b306` |
| **LIM-04** | Artificial Duplicates in Permutation Scheme S2 | Statistical Methodology | **CLOSED** | `14f3b89` |
| **LIM-05** | Speculative Wording in Permutation Test Scripts | Reporting Neutrality | **CLOSED** | `14f3b89` |
| **LIM-06** | Synthetic Planted Structure Gate G8 Bound Sensitivity | Simulation Validation | **CLOSED** | `14f3b89` |
| **LIM-07** | Historical Intermediary A2 Scratch Run Reproducibility | Provenance Integrity | **CLOSED** | `d4557f4` |
| **LIM-08** | Absence of Live Operational C3 Metadata in CAM-LDS | Interface Contract | *OPEN* | Pending C3 / Live Deploy |
| **LIM-09** | Real-Time Streaming Ingestion and Dynamic Episode Demarcation | Operational Deployment | *OPEN* | Pending C3 / Live Deploy |
| **LIM-10** | Higher-Order Context Memory ($k \ge 2$ Markov Dynamics) | Model Expressiveness | *OPEN* | Pending C3 / Live Deploy |

## 2. Detailed Register Entries

### LIM-01: Small Initial Sample Size (4 Episodes)

- **Category**: Dataset Scope
- **Status**: `CLOSED`
- **Resolution Commit**: `2cf7786`
- **Description**: The initial 4-episode evaluation (N=67) had limited statistical power to differentiate fine-grained sequence dynamics.
- **Resolution / Mitigation**: Expanded to 7 episodes (E1-E7, N=95) with formal pre-registration, LOEO cross-validation, and power analysis.

### LIM-02: Cross-Scenario Technique Vocabulary Isolation

- **Category**: Domain Generalization
- **Status**: `CLOSED`
- **Resolution Commit**: `d6f3764`
- **Description**: Technique-level attack patterns exhibit zero repeat transitions across disparate campaigns, causing severe coverage and reachability bottlenecks.
- **Resolution / Mitigation**: Quantified via Target Reachability Ceiling (62.11%) and Perfect-Order Prediction Cap (64.98%), formally explaining the performance gap.

### LIM-03: Episode E5 Sample Imbalance

- **Category**: Data Quality
- **Status**: `CLOSED`
- **Resolution Commit**: `3a6b306`
- **Description**: Episode E5 contains only 3 labeled events (2 collapsed transitions), resulting in zero coverage under LOEO cross-validation.
- **Resolution / Mitigation**: Conducted full side-by-side sensitivity analysis with E5 removed (6-fold LOEO, N=83) confirming all conclusions hold independently of E5.

### LIM-04: Artificial Duplicates in Permutation Scheme S2

- **Category**: Statistical Methodology
- **Status**: `CLOSED`
- **Resolution Commit**: `14f3b89`
- **Description**: Unconstrained adjacent shuffling in Scheme S2 generated consecutive identical transitions that never occur in collapsed empirical sequences.
- **Resolution / Mitigation**: Formally excluded S2 from 7-episode design in pre-registration; adopted Scheme S1 (headline) and Scheme S3 (rejection-sampled constrained shuffle).

### LIM-05: Speculative Wording in Permutation Test Scripts

- **Category**: Reporting Neutrality
- **Status**: `CLOSED`
- **Resolution Commit**: `14f3b89`
- **Description**: Reporting scripts included causal speculation regarding adjacency constraints and ambiguous wording on Markov-minus-Frequency rows.
- **Resolution / Mitigation**: Neutralized under Amendment 6 to factual difference statistic descriptions and explicit disclaimers regarding hypothesis test boundaries.

### LIM-06: Synthetic Planted Structure Gate G8 Bound Sensitivity

- **Category**: Simulation Validation
- **Status**: `CLOSED`
- **Resolution Commit**: `14f3b89`
- **Description**: At small sample sizes with V=82, estimator recovery bound for G8 was loose relative to large-sample asymptotics.
- **Resolution / Mitigation**: Documented in planted real-scale report; G9 (monotonicity) and G10 (reachability recovery) passed unconditionally.

### LIM-07: Historical Intermediary A2 Scratch Run Reproducibility

- **Category**: Provenance Integrity
- **Status**: `CLOSED`
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

