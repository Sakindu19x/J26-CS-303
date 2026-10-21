# NFR1 Timing & Response Time Verification Report

> [!NOTE]
> **Measurement Standard**: Evaluated according to declared engineering defaults documented in `reports/nfr_criteria.md`:
> Warm end-to-end median $\le$ 2.00 s, warm p95 $\le$ 5.00 s, process-level cold-start latency $\le$ 10.00 s.
> In-process first-record latency and Streamlit server ready time are INFORMATIONAL (no proposal threshold).

---

## 1. Executive Summary & Verdict

| Criterion | Target Threshold | Measured Value | Result |
|:---|:---:|:---:|:---:|
| **Warm End-to-End Latency (Median)** | $\le$ 2.00 s | **0.0014 s** | **PASS** |
| **Warm End-to-End Latency (p95)** | $\le$ 5.00 s | **0.0026 s** | **PASS** |
| **Process-Level Cold Start (Parent-Timed)** | $\le$ 10.00 s | **0.2013 s** | **PASS** |
| **In-Process First-Record Latency** | Informational (None) | **0.1383 s** | **INFORMATIONAL** |
| **Streamlit Server Ready Time (Port 8765)** | Informational (None) | **1.8590 s** | **INFORMATIONAL** |
| **Overall NFR1 Compliance** | All Gated Criteria Satisfied | — | **PASS** |

---

## 2. Timed Region Definitions

Formal timing boundaries implemented in measurement code:

- **Warm End-to-End Pipeline Latency**: Ingestion of raw events via C3 adapter, chronological timeline reconstruction, sequence extraction, production Markov technique and tactic inference, and explainable prediction record generation over 30 repetitions following 3 warm-ups.
- **Process-Level Cold Start (Parent-Timed)**: Fresh Python subprocess invocation from parent process, complete interpreter initialization, package imports, model deserialization from disk, and emission of first explainable prediction record, timed externally by the parent.
- **In-Process First-Record Latency**: Elapsed duration within an initialized Python environment to load production models into memory and emit the first prediction record (informational).
- **Streamlit Server Ready Time**: Duration from launching `python -m streamlit run` headless on port 8765 to receiving HTTP 200 OK from the `/_stcore/health` endpoint (informational).
- **Synthetic Scaling Stress Benchmark**: Throughput and latency scaling under synthetic 1x, 10x, and 100x event volume expansion on the longest observed episode (informational).

---

## 3. Per-Episode Latency Breakdown (30 Repetitions / Episode)

End-to-end pipeline execution includes C3 adapter ingestion, timeline reconstruction, sequence extraction, Markov technique and tactic inference, and full explainable prediction record serialization.

| Episode | Raw Events | Median Latency | p95 Latency | Mean Latency | [Min, Max] Range |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `E1` | 38 | 0.0014 s | 0.0016 s | 0.0014 s | [0.0013, 0.0017] s |
| `E2` | 29 | 0.0010 s | 0.0017 s | 0.0011 s | [0.0010, 0.0018] s |
| `E3` | 77 | 0.0026 s | 0.0029 s | 0.0027 s | [0.0025, 0.0031] s |
| `E4` | 46 | 0.0016 s | 0.0020 s | 0.0016 s | [0.0015, 0.0022] s |
| `E5` | 7 | 0.0003 s | 0.0004 s | 0.0003 s | [0.0002, 0.0005] s |
| `E6` | 51 | 0.0017 s | 0.0021 s | 0.0018 s | [0.0016, 0.0024] s |
| `E7` | 26 | 0.0009 s | 0.0010 s | 0.0009 s | [0.0009, 0.0011] s |

---

## 4. Scaling Benchmark (Informational)

Synthetic volume stress testing derived from the longest observed episode (`E3`, 77 raw events) across $1\times$, $10\times$, and $100\times$ event multipliers:

| Scaling Factor | Ingested Events | Valid Timeline Events | Elapsed Time | Processing Throughput |
|:---:|:---:|:---:|:---:|:---:|
| 1x | 77 | 77 | 0.0082 s | 9349.4 events/s |
| 10x | 770 | 770 | 0.0333 s | 23096.3 events/s |
| 100x | 7700 | 7700 | 0.3316 s | 23220.9 events/s |

---

## 5. Platform and Environment Telemetry

- **Processor**: `13th Gen Intel(R) Core(TM) i5-13420H` (AMD64)
- **Operating System**: `Windows 11 (10.0.26300)`
- **Python Runtime**: `3.12.10` (`C:\Users\Lenovo\OneDrive - EGUARDIAN\Documents\Dataset\.venv\Scripts\python.exe`)
- **Core Dependencies**:
  - `numpy`: `2.5.3`
  - `pandas`: `3.0.6`
  - `streamlit`: `1.65.0`
  - `pytest`: `9.1.1`
  - `jsonschema`: `4.26.0`

---
*Report Generated: Deterministic Execution via `scripts/measure_nfr1.py`*
