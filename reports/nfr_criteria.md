# NFR1 Response Time & Performance Criteria (Component 4)

> [!NOTE]
> **Regulatory and Design Context**: The original research proposal specifies NFR1 qualitatively as achieving an
> *"acceptable response time"* for digital forensic analysis and automated decision support during live or post-incident investigations.
> Because the proposal did not fix numerical latency thresholds, this document formally declares default quantitative performance criteria
> against which empirical measurements are evaluated.
> **Notice**: These are our declared engineering defaults and may be revised or calibrated by the student / project owner.

---

## 1. Declared Default Criteria

The following numerical thresholds are established as formal acceptance criteria for NFR1:

| Evaluation Dimension | Scope & Workload | Latency Threshold | Rationale |
|:---|:---|:---:|:---|
| **Warm End-to-End Execution (Median)** | Single attack episode through complete pipeline: C3 adapter ingestion, chronological timeline reconstruction, sequence derivation, technique prediction, tactic prediction, and LOEO explainable prediction record generation. | **Median $\le$ 2.00 s** | Ensures near-instantaneous interactive triage responsiveness for digital forensic incident responders in interactive dashboards and automated queues. |
| **Warm End-to-End Execution (95th Percentile)** | Single attack episode through complete pipeline (same as above), 95th percentile over 30 repetitions across all episodes. | **p95 $\le$ 5.00 s** | Limits tail latency to maintain analyst engagement and avoid UI unresponsiveness even under bursty forensic ingest. |
| **Cold-Start Pipeline Initialization** | Cold process launch, production Markov model deserialization and validation, ingestion of first attack event, and generation of first prediction record. | **Cold start $\le$ 10.00 s** | Guarantees rapid cold boot when spawned dynamically in microservice or CLI forensic environments. |

---

## 2. Experimental Measurement Protocol

1. **Repetitions and Warm-Up**:
   - Each of the 7 attack simulation episodes ($E1$ through $E7$) is measured across **30 consecutive repetitions** following **3 discardable warm-up runs** to eliminate initial disk/JIT caching artifacts.
   - High-resolution timing is captured using Python's monotonic high-precision timer (`time.perf_counter()`).

2. **Workload Definition**:
   For each episode, an end-to-end repetition executes:
   - Ingestion of raw normalized events via `C3EventAdapter`.
   - Chronological timeline reconstruction and validation (`reconstruct_timeline`).
   - Attack sequence extraction (`extract_sequences`).
   - Production / LOEO model state lookup and top-$k$ transition probability inference (technique and tactic).
   - Generation and verification of the canonical explainable prediction record (`generate_prediction_record`).

3. **Scaling Benchmark (Informational)**:
   - Synthetic scaling workloads at $1\times$, $10\times$, and $100\times$ event counts of the longest observed episode are measured to characterize algorithmic complexity and memory stability under high-volume log ingestion.
   - The scaling benchmark is reported for empirical characterization and does not gate acceptance.

---

## 3. Platform Characterization

Performance measurements are recorded alongside full host environment telemetry:
- Processor model, physical/logical core count, and architecture.
- Host Operating System and kernel version.
- Python runtime environment, interpreter version, and key library dependencies.
- Monotonic timing timestamp.

---

## 4. Refined Cold-Start and Informational Latency Specifications (Prompt 14 Q9a)

As clarified under Prompt 14 Q9a, performance criteria are formally delineated between gated thresholds and informational telemetry:

1. **Process-Level Cold Start (Gated Acceptance Threshold)**:
   - **Definition**: Cold process execution comprising fresh Python subprocess invocation, interpreter initialization, all required module imports, production model deserialization, and generation of the first explainable prediction record.
   - **Timing Scope**: Monotonically timed by the parent process from `subprocess.Popen` / `subprocess.run` dispatch to child process termination.
   - **Acceptance Threshold**: **$\le$ 10.0 s** (Existing threshold unchanged).

2. **In-Process First-Record Latency (Informational Telemetry)**:
   - **Definition**: Time elapsed within an existing Python process to load production models into memory and emit the first prediction record.
   - **Threshold**: **INFORMATIONAL** (no threshold; research proposal specifies none).

3. **Streamlit Server Ready Time (Informational Telemetry)**:
   - **Definition**: Time elapsed from spawning the Streamlit web application process (`python -m streamlit run ... --server.port 8765 --server.headless true`) until the health endpoint `/_stcore/health` returns HTTP 200 OK.
   - **Threshold**: **INFORMATIONAL** (no threshold; research proposal specifies none).

---

*Declared Criteria Version: 1.1.0 (Prompt 14 Q9a, October 2026)*
