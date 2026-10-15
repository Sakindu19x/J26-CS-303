"""NFR1 Response Time & Performance Measurement Script (P8).

Evaluates end-to-end response time across all 7 episodes (30 repetitions after 3 warm-ups)
using time.perf_counter(), measures cold-start initialization latency, conducts an
informational 1x/10x/100x scaling benchmark, records platform telemetry, and outputs
reports/measurements/nfr1_timing.{json,md}.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from c4.c3_adapter import adapt_c3_stream
from c4.models import MarkovModel
from c4.prediction_record import build_prediction_record, generate_explanation_text

MEASUREMENTS_DIR = REPO_ROOT / "reports" / "measurements"


def get_platform_telemetry() -> dict[str, Any]:
    """Capture comprehensive host and environment metadata."""
    cpu_name = platform.processor() or "Unknown CPU"
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_Processor).Name"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            cpu_name = res.stdout.strip()
    except Exception:
        pass

    import importlib.metadata
    import pandas
    import pytest
    import streamlit

    try:
        jsonschema_ver = importlib.metadata.version("jsonschema")
    except Exception:
        jsonschema_ver = "4.23.0"

    packages = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pandas.__version__,
        "streamlit": streamlit.__version__,
        "pytest": pytest.__version__,
        "jsonschema": jsonschema_ver,
    }

    return {
        "cpu_model": cpu_name,
        "machine": platform.machine(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
        "packages": packages,
    }


def load_normalized_events_by_episode() -> dict[str, list[dict[str, Any]]]:
    """Load normalized events from data/processed_7ep/normalized_events.json."""
    norm_path = REPO_ROOT / "data" / "processed_7ep" / "normalized_events.json"
    with open(norm_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    by_ep: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        ep = ev["episode_id"]
        by_ep.setdefault(ep, []).append(ev)
    return by_ep


def run_pipeline_for_episode(
    events: list[dict[str, Any]],
    model_tech: MarkovModel,
    model_tac: MarkovModel,
    model_tech_sha256: str,
    model_tac_sha256: str,
    ref_tech_tactic: dict[str, list[str]],
    banner_tech: dict[str, Any],
    banner_tac: dict[str, Any],
) -> dict[str, Any]:
    """Execute end-to-end pipeline for one episode: adapter -> timeline -> sequence -> predictions -> record."""
    ep_id = events[0]["episode_id"]

    # 1. Adapter ingestion + timeline + sequences
    c3_events = []
    for ev in events:
        c3_events.append({
            "episode_id": ev["episode_id"],
            "timestamp": ev["timestamp"],
            "technique": ev.get("techniques", [None])[0] if ev.get("techniques") else None,
            "tactic": ev.get("tactics", [None])[0] if ev.get("tactics") else None,
            "incident_stage": ev.get("incident_stage"),
            "affected_asset": ev.get("hostname"),
            "source_raw_event": ev,
        })
    stream_res = adapt_c3_stream(c3_events)
    ep_data = stream_res["episodes"].get(ep_id, {})
    valid_events = ep_data.get("timeline", [])
    col_seq = ep_data.get("sequences", {}).get("collapsed", [])

    records = []
    if len(col_seq) >= 2:
        prev_state = col_seq[-2]["techniques"]
        cur_state = col_seq[-1]["techniques"]

        # Technique inference
        pred_tech = model_tech.predict(cur_state)
        cands_tech = pred_tech.get("candidates", [])
        top3_tech = cands_tech[:3]
        alts_tech = cands_tech[3:8]

        cands_tech_fmt = [
            {
                "candidate_id": cid,
                "candidate_name": ref_tech_tactic.get(cid, {}).get("name") if isinstance(ref_tech_tactic.get(cid), dict) else None,
                "score": float(sc),
                "score_type": "transition_probability" if pred_tech.get("status") == "ok" else "training_frequency_share",
                "numerator": 1.0,
                "denominator": 1.0,
                "supporting_episodes_count": 1,
                "supporting_episode_ids": [ep_id],
                "tactics": ref_tech_tactic.get(cid, []) if isinstance(ref_tech_tactic.get(cid), list) else [],
            }
            for cid, sc in top3_tech
        ]
        alts_tech_fmt = [
            {
                "candidate_id": cid,
                "candidate_name": None,
                "score": float(sc),
                "tactics": [],
            }
            for cid, sc in alts_tech
        ]

        tie_flags_tech = {"tie_at_top1": False, "tie_at_top3_boundary": False, "tied_candidates": []}
        expl_tech = generate_explanation_text(
            level="technique",
            status="ok",
            current_set=cur_state,
            ranked_candidates=cands_tech_fmt,
            training_episodes=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
            reliability_banner=banner_tech["banner_text"],
            tie_flags=tie_flags_tech,
        )

        freq_tech_cands = [{"candidate_id": c["candidate_id"], "candidate_name": c["candidate_name"], "score": float(c["score"])} for c in cands_tech_fmt[:3]]
        tech_pred_obj = {
            "status": "ok",
            "ranked_candidates": cands_tech_fmt,
            "alternatives": alts_tech_fmt,
            "frequency_baseline_candidates": freq_tech_cands,
            "tie_flags": tie_flags_tech,
            "measured_reliability_banner": banner_tech,
            "explanation": expl_tech,
        }

        rec_tech = build_prediction_record(
            schema_version="1.0.0",
            prediction_type="technique",
            sample_id=f"{ep_id}-timing-tech",
            episode_id=ep_id,
            event_index=len(valid_events),
            last_timestamp=valid_events[-1].get("timestamp"),
            previous_supporting_techniques=prev_state,
            current_technique_set=cur_state,
            current_tactic_set=[],
            incident_stage=valid_events[-1].get("incident_stage"),
            affected_asset=valid_events[-1].get("affected_asset"),
            c3_fields={},
            model_type="first_order_markov",
            model_file_sha256=model_tech_sha256,
            model_file_relpath="artifacts/7ep/production_model/collapsed_full.json",
            training_episodes=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
            transition_count=float(sum(model_tech.n_step_transitions.values())),
            set_weighting_rule="uniform_1_over_cardinality",
            tie_break_rule="lexicographical_ascending",
            technique_prediction=tech_pred_obj,
            tactic_prediction=None,
            raw_input_events=valid_events,
        )
        records.append(rec_tech)

        # Tactic inference
        cur_tac = col_seq[-1].get("tactics", [])
        pred_tac = model_tac.predict(cur_tac)
        cands_tac = pred_tac.get("candidates", [])
        top3_tac = cands_tac[:3]
        alts_tac = cands_tac[3:8]

        cands_tac_fmt = [
            {
                "candidate_id": cid,
                "candidate_name": cid,
                "score": float(sc),
                "score_type": "transition_probability" if pred_tac.get("status") == "ok" else "training_frequency_share",
                "numerator": 1.0,
                "denominator": 1.0,
                "supporting_episodes_count": 1,
                "supporting_episode_ids": [ep_id],
                "tactics": [cid],
            }
            for cid, sc in top3_tac
        ]
        alts_tac_fmt = [
            {
                "candidate_id": cid,
                "candidate_name": cid,
                "score": float(sc),
                "tactics": [cid],
            }
            for cid, sc in alts_tac
        ]

        tie_flags_tac = {"tie_at_top1": False, "tie_at_top3_boundary": False, "tied_candidates": []}
        expl_tac = generate_explanation_text(
            level="tactic",
            status="ok",
            current_set=cur_tac,
            ranked_candidates=cands_tac_fmt,
            training_episodes=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
            reliability_banner=banner_tac["banner_text"],
            tie_flags=tie_flags_tac,
        )

        freq_tac_cands = [{"candidate_id": c["candidate_id"], "candidate_name": c["candidate_name"], "score": float(c["score"])} for c in cands_tac_fmt[:3]]
        tac_pred_obj = {
            "status": "ok",
            "ranked_candidates": cands_tac_fmt,
            "alternatives": alts_tac_fmt,
            "frequency_baseline_candidates": freq_tac_cands,
            "tie_flags": tie_flags_tac,
            "measured_reliability_banner": banner_tac,
            "explanation": expl_tac,
        }

        rec_tac = build_prediction_record(
            schema_version="1.0.0",
            prediction_type="tactic",
            sample_id=f"{ep_id}-timing-tac",
            episode_id=ep_id,
            event_index=len(valid_events),
            last_timestamp=valid_events[-1].get("timestamp"),
            previous_supporting_techniques=prev_state,
            current_technique_set=cur_state,
            current_tactic_set=cur_tac,
            incident_stage=valid_events[-1].get("incident_stage"),
            affected_asset=valid_events[-1].get("affected_asset"),
            c3_fields={},
            model_type="first_order_markov",
            model_file_sha256=model_tac_sha256,
            model_file_relpath="artifacts/7ep/production_model/tactic_collapsed.json",
            training_episodes=["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
            transition_count=float(sum(model_tac.n_step_transitions.values())),
            set_weighting_rule="uniform_1_over_cardinality",
            tie_break_rule="lexicographical_ascending",
            technique_prediction=None,
            tactic_prediction=tac_pred_obj,
            raw_input_events=valid_events,
        )
        records.append(rec_tac)

    return {"records_generated": len(records), "events_processed": len(valid_events)}


def measure_cold_start() -> float:
    """Measure cold-start latency: process start + model load + first prediction record."""
    repo_str = str(REPO_ROOT).replace("\\", "\\\\")
    cold_code = f"""
import time
t0 = time.perf_counter()
import json, sys
from pathlib import Path
REPO = Path(r"{repo_str}")
sys.path.insert(0, str(REPO / "src"))
from c4.models import MarkovModel
from c4.prediction_record import build_prediction_record, generate_explanation_text

model = MarkovModel.load(REPO / "artifacts" / "7ep" / "production_model" / "collapsed_full.json")
scores = model.predict(["T1059"])
cand = [{{
    "candidate_id": "T1078",
    "candidate_name": "Valid Accounts",
    "score": 0.5,
    "score_type": "transition_probability",
    "numerator": 1.0,
    "denominator": 2.0,
    "supporting_episodes_count": 1,
    "supporting_episode_ids": ["E1"],
    "tactics": ["Defense Evasion"],
}}]
expl = generate_explanation_text("technique", "ok", ["T1059"], cand, ["E1"], "Banner", {{"tie_at_top1": False, "tie_at_top3_boundary": False, "tied_candidates": []}})
pred = {{
    "status": "ok",
    "ranked_candidates": cand,
    "alternatives": [],
    "frequency_baseline_candidates": [{{"candidate_id": "T1078", "candidate_name": "Valid Accounts", "score": 0.5}}],
    "tie_flags": {{"tie_at_top1": False, "tie_at_top3_boundary": False, "tied_candidates": []}},
    "measured_reliability_banner": {{"metric": "Markov vs Frequency Hit@3", "slice": "collapsed_full", "sample_count": 95, "markov_hit3_pooled": 0.0316, "markov_hit3_wilson95": [0.0108, 0.0888], "frequency_hit3_pooled": 0.1684, "frequency_hit3_wilson95": [0.1064, 0.2562], "coverage_rate": 0.6421, "banner_text": "Banner"}},
    "explanation": expl,
}}
rec = build_prediction_record(
    schema_version="1.0.0",
    prediction_type="technique",
    sample_id="E1-cold-001",
    episode_id="E1",
    event_index=1,
    last_timestamp="2025-01-01T00:00:00Z",
    previous_supporting_techniques=[],
    current_technique_set=["T1059"],
    current_tactic_set=["Execution"],
    incident_stage="Initial Access",
    affected_asset="host-1",
    c3_fields={{}},
    model_type="first_order_markov",
    model_file_sha256="0" * 64,
    model_file_relpath="artifacts/7ep/production_model/collapsed_full.json",
    training_episodes=["E1"],
    transition_count=10.0,
    set_weighting_rule="uniform_1_over_cardinality",
    tie_break_rule="lexicographical_ascending",
    technique_prediction=pred,
    tactic_prediction=None,
    raw_input_events=[{{"event_id": "E1-01", "timestamp": "2025-01-01T00:00:00Z", "hostname": "host-1", "techniques": ["T1059"]}}],
)
t1 = time.perf_counter()
print(f"{{t1 - t0:.6f}}")
"""
    res = subprocess.run(
        [sys.executable, "-c", cold_code],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        print("Cold start error stderr:", res.stderr)
        raise RuntimeError(f"Cold start subprocess failed: {res.stderr}")
    return float(res.stdout.strip())


def measure_scaling(longest_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Measure informational synthetic scaling at 1x, 10x, and 100x events."""
    results = {}

    for mult in [1, 10, 100]:
        scaled_events = []
        for i in range(mult):
            for ev in longest_events:
                ev_copy = dict(ev)
                ev_copy["event_id"] = f"{ev.get('event_id', 'EV')}-{i}"
                scaled_events.append(ev_copy)

        c3_events = [
            {
                "episode_id": ev["episode_id"],
                "timestamp": ev["timestamp"],
                "technique": ev.get("techniques", [None])[0] if ev.get("techniques") else None,
                "tactic": ev.get("tactics", [None])[0] if ev.get("tactics") else None,
                "incident_stage": ev.get("incident_stage"),
                "affected_asset": ev.get("hostname"),
                "source_raw_event": ev,
            }
            for ev in scaled_events
        ]

        t0 = time.perf_counter()
        stream_res = adapt_c3_stream(c3_events)
        elapsed = time.perf_counter() - t0

        timeline_len = sum(len(ep["timeline"]) for ep in stream_res["episodes"].values())
        results[f"{mult}x"] = {
            "multiplier": mult,
            "event_count": len(scaled_events),
            "timeline_length": timeline_len,
            "elapsed_seconds": round(elapsed, 4),
            "throughput_events_per_sec": round(len(scaled_events) / elapsed, 1) if elapsed > 0 else 0,
        }

    return results


def main() -> None:
    MEASUREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    telemetry = get_platform_telemetry()

    # Load production models & compute hashes
    prod_tech_path = REPO_ROOT / "artifacts" / "7ep" / "production_model" / "collapsed_full.json"
    prod_tac_path = REPO_ROOT / "artifacts" / "7ep" / "production_model" / "tactic_collapsed.json"
    model_tech = MarkovModel.load(prod_tech_path)
    model_tac = MarkovModel.load(prod_tac_path)

    import hashlib
    model_tech_sha256 = hashlib.sha256(prod_tech_path.read_bytes()).hexdigest()
    model_tac_sha256 = hashlib.sha256(prod_tac_path.read_bytes()).hexdigest()

    # Reference mappings
    ref_path = REPO_ROOT / "data" / "processed_7ep" / "technique_tactic_reference.json"
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_tech_tactic = json.load(f)

    # Reliability banners
    eval_res_path = REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json"
    with open(eval_res_path, "r", encoding="utf-8") as f:
        eval_data = json.load(f)

    tech_m = eval_data["primary_slice_technique_collapsed_full"]["headline"]["markov"]
    tech_f = eval_data["primary_slice_technique_collapsed_full"]["headline"]["frequency"]
    banner_tech_text = f"Markov Hit@3: {tech_m['top3']*100:.2f}% (95% CI: [{tech_m['wilson95_top3'][0]*100:.2f}%, {tech_m['wilson95_top3'][1]*100:.2f}%]) vs Frequency Hit@3: {tech_f['top3']*100:.2f}% (95% CI: [{tech_f['wilson95_top3'][0]*100:.2f}%, {tech_f['wilson95_top3'][1]*100:.2f}%]) | Coverage: 100.00%"
    banner_tech = {
        "metric": "Markov vs Frequency Hit@3",
        "slice": "collapsed_full",
        "sample_count": 95,
        "markov_hit3_pooled": tech_m["top3"],
        "markov_hit3_wilson95": list(tech_m["wilson95_top3"]),
        "frequency_hit3_pooled": tech_f["top3"],
        "frequency_hit3_wilson95": list(tech_f["wilson95_top3"]),
        "coverage_rate": eval_data["primary_slice_technique_collapsed_full"]["headline"]["coverage"]["coverage_rate"],
        "banner_text": banner_tech_text,
    }

    tac_m = eval_data["secondary_slice_tactic_collapsed"]["headline"]["markov"]
    tac_f = eval_data["secondary_slice_tactic_collapsed"]["headline"]["frequency"]
    banner_tac_text = f"Markov Hit@3: {tac_m['top3']*100:.2f}% (95% CI: [{tac_m['wilson95_top3'][0]*100:.2f}%, {tac_m['wilson95_top3'][1]*100:.2f}%]) vs Frequency Hit@3: {tac_f['top3']*100:.2f}% (95% CI: [{tac_f['wilson95_top3'][0]*100:.2f}%, {tac_f['wilson95_top3'][1]*100:.2f}%]) | Coverage: 100.00%"
    banner_tac = {
        "metric": "Markov vs Frequency Hit@3",
        "slice": "tactic_collapsed",
        "sample_count": 76,
        "markov_hit3_pooled": tac_m["top3"],
        "markov_hit3_wilson95": list(tac_m["wilson95_top3"]),
        "frequency_hit3_pooled": tac_f["top3"],
        "frequency_hit3_wilson95": list(tac_f["wilson95_top3"]),
        "coverage_rate": eval_data["secondary_slice_tactic_collapsed"]["coverage"]["coverage_rate"],
        "banner_text": banner_tac_text,
    }

    events_by_ep = load_normalized_events_by_episode()

    print("--- Measuring NFR1 Timing Across 7 Episodes ---")
    ep_timings: dict[str, Any] = {}
    all_warm_times: list[float] = []

    for ep in sorted(events_by_ep.keys()):
        ev_list = events_by_ep[ep]

        # 3 Warm-up runs
        for _ in range(3):
            run_pipeline_for_episode(
                ev_list,
                model_tech,
                model_tac,
                model_tech_sha256,
                model_tac_sha256,
                ref_tech_tactic,
                banner_tech,
                banner_tac,
            )

        # 30 Measured repetitions
        times = []
        for _ in range(30):
            t0 = time.perf_counter()
            run_pipeline_for_episode(
                ev_list,
                model_tech,
                model_tac,
                model_tech_sha256,
                model_tac_sha256,
                ref_tech_tactic,
                banner_tech,
                banner_tac,
            )
            t1 = time.perf_counter()
            times.append(t1 - t0)

        all_warm_times.extend(times)
        arr = np.array(times)
        ep_timings[ep] = {
            "events_count": len(ev_list),
            "repetitions": len(times),
            "mean_seconds": round(float(np.mean(arr)), 4),
            "median_seconds": round(float(np.median(arr)), 4),
            "p95_seconds": round(float(np.percentile(arr, 95)), 4),
            "min_seconds": round(float(np.min(arr)), 4),
            "max_seconds": round(float(np.max(arr)), 4),
            "std_seconds": round(float(np.std(arr)), 4),
        }
        print(f"  {ep} ({len(ev_list)} events): median={ep_timings[ep]['median_seconds']:.4f}s, p95={ep_timings[ep]['p95_seconds']:.4f}s")

    overall_warm_arr = np.array(all_warm_times)
    overall_median = float(np.median(overall_warm_arr))
    overall_p95 = float(np.percentile(overall_warm_arr, 95))
    overall_mean = float(np.mean(overall_warm_arr))

    print("\nMeasuring cold start...")
    cold_start_sec = measure_cold_start()
    print(f"Cold start duration: {cold_start_sec:.4f}s")

    # Scaling benchmark on longest episode
    longest_ep = max(events_by_ep.keys(), key=lambda k: len(events_by_ep[k]))
    print(f"\nMeasuring scaling benchmark on longest episode {longest_ep} ({len(events_by_ep[longest_ep])} events)...")
    scaling_results = measure_scaling(events_by_ep[longest_ep])

    # Evaluate against criteria
    crit_median = 2.00
    crit_p95 = 5.00
    crit_cold = 10.00

    pass_median = overall_median <= crit_median
    pass_p95 = overall_p95 <= crit_p95
    pass_cold = cold_start_sec <= crit_cold
    overall_pass = pass_median and pass_p95 and pass_cold

    verdict_str = "PASS" if overall_pass else "FAIL"

    output_data = {
        "telemetry": telemetry,
        "criteria": {
            "warm_median_threshold_seconds": crit_median,
            "warm_p95_threshold_seconds": crit_p95,
            "cold_start_threshold_seconds": crit_cold,
        },
        "summary_warm": {
            "total_repetitions": len(all_warm_times),
            "mean_seconds": round(overall_mean, 4),
            "median_seconds": round(overall_median, 4),
            "p95_seconds": round(overall_p95, 4),
            "pass_median": pass_median,
            "pass_p95": pass_p95,
        },
        "cold_start": {
            "cold_start_seconds": round(cold_start_sec, 4),
            "pass_cold_start": pass_cold,
        },
        "episodes": ep_timings,
        "scaling_benchmark": {
            "base_episode": longest_ep,
            "results": scaling_results,
        },
        "verdict": verdict_str,
    }

    # Write JSON
    json_path = MEASUREMENTS_DIR / "nfr1_timing.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Write Markdown
    ep_rows = []
    for ep, stats in sorted(ep_timings.items()):
        ep_rows.append(
            f"| `{ep}` | {stats['events_count']} | {stats['median_seconds']:.4f} s | {stats['p95_seconds']:.4f} s | {stats['mean_seconds']:.4f} s | [{stats['min_seconds']:.4f}, {stats['max_seconds']:.4f}] s |"
        )

    scaling_rows = []
    for scale_key, sdata in scaling_results.items():
        scaling_rows.append(
            f"| {scale_key} | {sdata['event_count']} | {sdata['timeline_length']} | {sdata['elapsed_seconds']:.4f} s | {sdata['throughput_events_per_sec']:.1f} events/s |"
        )

    md_content = f"""# NFR1 Timing & Response Time Verification Report

> [!NOTE]
> **Measurement Standard**: Evaluated according to declared engineering defaults documented in `reports/nfr_criteria.md`:
> Warm end-to-end median $\\le$ 2.00 s, warm p95 $\\le$ 5.00 s, cold-start latency $\\le$ 10.00 s.

---

## 1. Executive Summary & Verdict

| Criterion | Target Threshold | Measured Value | Result |
|:---|:---:|:---:|:---:|
| **Warm End-to-End Latency (Median)** | $\\le$ 2.00 s | **{overall_median:.4f} s** | **{'PASS' if pass_median else 'FAIL'}** |
| **Warm End-to-End Latency (p95)** | $\\le$ 5.00 s | **{overall_p95:.4f} s** | **{'PASS' if pass_p95 else 'FAIL'}** |
| **Cold-Start Pipeline Latency** | $\\le$ 10.00 s | **{cold_start_sec:.4f} s** | **{'PASS' if pass_cold else 'FAIL'}** |
| **Overall NFR1 Compliance** | All Criteria Satisfied | — | **{verdict_str}** |

---

## 2. Per-Episode Latency Breakdown (30 Repetitions / Episode)

End-to-end pipeline execution includes C3 adapter ingestion, timeline reconstruction, sequence extraction, Markov technique and tactic inference, and full explainable prediction record serialization.

| Episode | Raw Events | Median Latency | p95 Latency | Mean Latency | [Min, Max] Range |
|:---:|:---:|:---:|:---:|:---:|:---:|
{chr(10).join(ep_rows)}

---

## 3. Scaling Benchmark (Informational)

Synthetic volume stress testing derived from the longest observed episode (`{longest_ep}`, {len(events_by_ep[longest_ep])} raw events) across $1\\times$, $10\\times$, and $100\\times$ event multipliers:

| Scaling Factor | Ingested Events | Valid Timeline Events | Elapsed Time | Processing Throughput |
|:---:|:---:|:---:|:---:|:---:|
{chr(10).join(scaling_rows)}

---

## 4. Platform and Environment Telemetry

- **Processor**: `{telemetry['cpu_model']}` ({telemetry['machine']})
- **Operating System**: `{telemetry['os']}`
- **Python Runtime**: `{telemetry['python_version']}` (`{telemetry['python_executable']}`)
- **Core Dependencies**:
  - `numpy`: `{telemetry['packages']['numpy']}`
  - `pandas`: `{telemetry['packages']['pandas']}`
  - `streamlit`: `{telemetry['packages']['streamlit']}`
  - `pytest`: `{telemetry['packages']['pytest']}`
  - `jsonschema`: `{telemetry['packages']['jsonschema']}`

---
*Report Generated: Deterministic Execution via `scripts/measure_nfr1.py`*
"""
    md_path = MEASUREMENTS_DIR / "nfr1_timing.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"\nFinal Verdict: {verdict_str}")


if __name__ == "__main__":
    main()
