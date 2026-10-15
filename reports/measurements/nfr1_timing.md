# NFR1 Timing & Response Time Verification Report

> [!NOTE]
> **Measurement Standard**: Evaluated according to declared engineering defaults documented in `reports/nfr_criteria.md`:
> Warm end-to-end median $\le$ 2.00 s, warm p95 $\le$ 5.00 s, cold-start latency $\le$ 10.00 s.

---

## 1. Executive Summary & Verdict

| Criterion | Target Threshold | Measured Value | Result |
|:---|:---:|:---:|:---:|
| **Warm End-to-End Latency (Median)** | $\le$ 2.00 s | **0.0043 s** | **PASS** |
| **Warm End-to-End Latency (p95)** | $\le$ 5.00 s | **0.0131 s** | **PASS** |
| **Cold-Start Pipeline Latency** | $\le$ 10.00 s | **0.1649 s** | **PASS** |
| **Overall NFR1 Compliance** | All Criteria Satisfied | — | **PASS** |

---

## 2. Per-Episode Latency Breakdown (30 Repetitions / Episode)

End-to-end pipeline execution includes C3 adapter ingestion, timeline reconstruction, sequence extraction, Markov technique and tactic inference, and full explainable prediction record serialization.

| Episode | Raw Events | Median Latency | p95 Latency | Mean Latency | [Min, Max] Range |
|:---:|:---:|:---:|:---:|:---:|:---:|
| `E1` | 38 | 0.0013 s | 0.0014 s | 0.0013 s | [0.0013, 0.0020] s |
| `E2` | 29 | 0.0038 s | 0.0054 s | 0.0031 s | [0.0010, 0.0058] s |
| `E3` | 77 | 0.0126 s | 0.0177 s | 0.0131 s | [0.0105, 0.0188] s |
| `E4` | 46 | 0.0072 s | 0.0089 s | 0.0074 s | [0.0062, 0.0094] s |
| `E5` | 7 | 0.0010 s | 0.0018 s | 0.0011 s | [0.0009, 0.0021] s |
| `E6` | 51 | 0.0074 s | 0.0093 s | 0.0075 s | [0.0044, 0.0096] s |
| `E7` | 26 | 0.0036 s | 0.0050 s | 0.0038 s | [0.0026, 0.0053] s |

---

## 3. Scaling Benchmark (Informational)

Synthetic volume stress testing derived from the longest observed episode (`E3`, 77 raw events) across $1\times$, $10\times$, and $100\times$ event multipliers:

| Scaling Factor | Ingested Events | Valid Timeline Events | Elapsed Time | Processing Throughput |
|:---:|:---:|:---:|:---:|:---:|
| 1x | 77 | 77 | 0.0065 s | 11825.8 events/s |
| 10x | 770 | 770 | 0.1347 s | 5718.4 events/s |
| 100x | 7700 | 7700 | 1.4925 s | 5159.0 events/s |

---

## 4. Platform and Environment Telemetry

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
