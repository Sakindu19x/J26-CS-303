"""build_requirements_trace.py

Rebuilds reports/7ep/requirements_trace.md strictly using titles from docs/proposal_requirements.json.

Columns:
- ID
- Proposal Title
- Implementing Modules
- Evidence (test node ids / report paths / scripts)
- Status from fixed enum: {IMPLEMENTED_AND_TESTED, IMPLEMENTED_DEMONSTRATED_ON_DATASET, PARTIAL, NOT_TESTABLE_UNTIL_C3, PENDING_HUMAN_EVIDENCE}
- Limits (plain words)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_JSON_PATH = REPO_ROOT / "docs" / "proposal_requirements.json"
OUT_MD_PATH = REPO_ROOT / "reports" / "7ep" / "requirements_trace.md"

VALID_STATUSES = {
    "IMPLEMENTED_AND_TESTED",
    "IMPLEMENTED_DEMONSTRATED_ON_DATASET",
    "PARTIAL",
    "NOT_TESTABLE_UNTIL_C3",
    "PENDING_HUMAN_EVIDENCE",
}

def resolve_json_pointer(repo_root: Path, file_rel: str, pointer: str, transform: str | None = None) -> Any:
    target_path = repo_root / file_rel
    assert target_path.is_file(), f"JSON pointer target file does not exist: {target_path}"
    with open(target_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.strip("/").split("/")]
    curr = data
    for p in parts:
        if isinstance(curr, list):
            curr = curr[int(p)]
        else:
            curr = curr[p]
    if transform in {"length", "len"}:
        return len(curr)
    return curr


def get_trace_definitions(repo_root: Path, proposal_data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ptrs = proposal_data["named_json_pointers"]

    # Resolve values from JSON pointers
    fr4_episodes = resolve_json_pointer(repo_root, ptrs["fr4_episodes"]["file"], ptrs["fr4_episodes"]["pointer"], ptrs["fr4_episodes"].get("type"))
    fr4_tech_samples = resolve_json_pointer(repo_root, ptrs["fr4_technique_samples"]["file"], ptrs["fr4_technique_samples"]["pointer"])
    fr4_tactic_samples = resolve_json_pointer(repo_root, ptrs["fr4_tactic_samples"]["file"], ptrs["fr4_tactic_samples"]["pointer"])
    fr4_p2_markov = resolve_json_pointer(repo_root, ptrs["fr4_p2_markov_hit3"]["file"], ptrs["fr4_p2_markov_hit3"]["pointer"])
    fr4_p2_freq = resolve_json_pointer(repo_root, ptrs["fr4_p2_frequency_hit3"]["file"], ptrs["fr4_p2_frequency_hit3"]["pointer"])
    fr4_p2_adj_p = f"{resolve_json_pointer(repo_root, ptrs['fr4_p2_adjusted_p']['file'], ptrs['fr4_p2_adjusted_p']['pointer']):.4f}"
    fr4_p1_markov = resolve_json_pointer(repo_root, ptrs["fr4_p1_markov_hit3"]["file"], ptrs["fr4_p1_markov_hit3"]["pointer"])
    fr4_p1_freq = resolve_json_pointer(repo_root, ptrs["fr4_p1_frequency_hit3"]["file"], ptrs["fr4_p1_frequency_hit3"]["pointer"])
    fr4_p1_adj_p = f"{resolve_json_pointer(repo_root, ptrs['fr4_p1_adjusted_p']['file'], ptrs['fr4_p1_adjusted_p']['pointer']):.4f}"
    fr4_verdict = resolve_json_pointer(repo_root, ptrs["fr4_formal_verdict"]["file"], ptrs["fr4_formal_verdict"]["pointer"])

    fr7_total = resolve_json_pointer(repo_root, ptrs["fr7_total_records"]["file"], ptrs["fr7_total_records"]["pointer"])
    fr7_cautioned = resolve_json_pointer(repo_root, ptrs["fr7_cautioned_records"]["file"], ptrs["fr7_cautioned_records"]["pointer"])

    nfr1_warm_median = f"{resolve_json_pointer(repo_root, ptrs['nfr1_warm_median']['file'], ptrs['nfr1_warm_median']['pointer']):.2f}"
    nfr1_warm_p95 = f"{resolve_json_pointer(repo_root, ptrs['nfr1_warm_p95']['file'], ptrs['nfr1_warm_p95']['pointer']):.2f}"
    nfr1_cold_start = f"{resolve_json_pointer(repo_root, ptrs['nfr1_cold_start']['file'], ptrs['nfr1_cold_start']['pointer']):.2f}"

    return {
        "FR1": {
            "modules": "`src/c4/timeline.py`, `src/c4/c3_adapter.py`",
            "evidence": "`tests/test_timeline_and_sequences.py::test_timeline_ordering_ties_and_missing_timestamps`, `reports/7ep/timeline_validation_report.json`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Timelines ordered chronologically by UTC ISO timestamp; tied timestamps resolved deterministically by raw input index; events without timestamps placed at the end.",
        },
        "FR2": {
            "modules": "`src/c4/episodes.py`, `src/c4/timeline.py`",
            "evidence": "`tests/test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence`, `reports/7ep/data_quality_report.json`",
            "status": "IMPLEMENTED_DEMONSTRATED_ON_DATASET",
            "limits": "Episodes come from dataset labels / scenario metadata (pre-assigned episode IDs in CAM-LDS audit logs), not an algorithmic sessionization or clustering algorithm. Zero cross-episode sequence leakage is verified by test tests/test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence.",
        },
        "FR3": {
            "modules": "`src/c4/attack_sequence.py`, `src/c4/mitre_reference.py`",
            "evidence": "`tests/test_timeline_and_sequences.py::test_collapsed_variant_merges_only_identical_consecutive_sets`, `reports/7ep/sequence_statistics.json`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Consecutive identical technique/tactic multi-label sets are merged in collapsed representation; unmapped background audit events are retained on timeline but omitted from attack sequence transitions.",
        },
        "FR4": {
            "modules": "`src/c4/models/markov.py`, `src/c4/models/frequency.py`",
            "evidence": "`tests/test_models.py::test_predict_next_interface`, `reports/7ep/evaluation_7ep_report.md`",
            "status": "IMPLEMENTED_DEMONSTRATED_ON_DATASET",
            "limits": (
                f"Empirically evaluated under LOEO cross-validation across all {fr4_episodes} episodes "
                f"({fr4_tech_samples} technique, {fr4_tactic_samples} tactic evaluation samples); "
                f"pre-registered verdict established improvement over baseline {fr4_verdict} "
                f"(Hit@3 technique P2: {fr4_p2_markov}/{fr4_tech_samples} vs {fr4_p2_freq}/{fr4_tech_samples}, Holm p = {fr4_p2_adj_p}; "
                f"Hit@3 tactic P1: {fr4_p1_markov}/{fr4_tactic_samples} ties {fr4_p1_freq}/{fr4_tactic_samples}, Holm p = {fr4_p1_adj_p})."
            ),
        },
        "FR5": {
            "modules": "`src/c4/prediction_record.py`, `src/c4/models/markov.py`",
            "evidence": "`tests/test_prediction_record.py::test_gp5_1_candidates_match_csv`, `data/processed_7ep/prediction_records_loeo.jsonl`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Predictive outputs provide transition probabilities summing to 1.0; falls back to marginal training frequency distribution upon unseen historical attack states.",
        },
        "FR6": {
            "modules": "`src/c4/prediction_record.py`, `scripts/build_prediction_records.py`",
            "evidence": "`tests/test_prediction_record.py::test_alternatives_no_placeholders_and_tactics`, `reports/7ep/prediction_record_examples.md`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Provides ranked alternative predictions for ranks 4 through k with non-placeholder transition numerators, denominators, and supporting training episode IDs.",
        },
        "FR7": {
            "modules": "`src/c4/prediction_record.py`, `src/c4/dashboard/prediction_panel.py`",
            "evidence": "`tests/test_prediction_record.py::test_gp5_5_schema_validation_100_percent`, `reports/7ep/prediction_record_examples.md`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": (
                f"Generates deterministic natural language explanations with empirical transition frequencies, "
                f"Wilson score reliability intervals, and explicit support cautions "
                f"({fr7_cautioned}/{fr7_total} records flagged with low support)."
            ),
        },
        "FR8": {
            "modules": "`src/c4/c3_adapter.py`, `docs/c3_c4_interface_contract.md`",
            "evidence": "`tests/test_c3_adapter.py::test_duplicates_detected_and_reported`, `docs/c3_c4_interface_contract.md`",
            "status": "NOT_TESTABLE_UNTIL_C3",
            "limits": "Component 3 contextual intelligence fields (threat score, investigation priority, asset criticality, CTI confidence, freshness, IoCs) are null until C3 integration; contract unagreed; adapter passes nulls.",
        },
        "FR9": {
            "modules": "`src/c4/dashboard/prediction_app.py`, `src/c4/dashboard/prediction_panel.py`",
            "evidence": "`tests/test_prediction_panel.py::test_prediction_app_renders_via_apptest`, `src/c4/dashboard/prediction_app.py`",
            "status": "PARTIAL",
            "limits": (
                f"Interactive Streamlit application displays historical progression, ranked candidates, and "
                f"explanation panels for all {fr7_total} offline LOEO records; live incident ingestion from C3 "
                f"pipeline is not yet integrated."
            ),
        },
        "NFR1": {
            "modules": "`scripts/measure_nfr1.py`, `reports/measurements/nfr1_timing.md`",
            "evidence": "`tests/test_nfr1.py::test_verify_nfr1_script`, `reports/measurements/nfr1_timing.md`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": (
                f"Evaluated against engineering performance thresholds declared by C4, proposal has none: "
                f"warm median latency <= {nfr1_warm_median} s, warm p95 <= {nfr1_warm_p95} s, and parent-timed process "
                f"cold start <= {nfr1_cold_start} s."
            ),
        },
        "NFR2": {
            "modules": "`src/c4/prediction_record.py`, `scripts/build_prediction_records.py`",
            "evidence": "`tests/test_prediction_record.py::test_gp5_3_hashseed_determinism`, `reports/audit/q14_determinism_log.txt`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "100% deterministic prediction records across independent processes with PYTHONHASHSEED=0, 1, 4242 producing identical SHA-256 digests; strict lexicographical tie breaking.",
        },
        "NFR3": {
            "modules": "`src/c4/c3_adapter.py`, `src/c4/prediction_record.py`",
            "evidence": "`tests/test_prediction_record.py::test_gp5_4_deep_frozen_inputs_non_modification`, `tests/test_c3_adapter.py::test_original_event_deep_copy_and_hash`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Cryptographic non-modification of input audit logs verified by SHA-256 digest equality before and after ingestion, timeline construction, and model inference.",
        },
        "NFR4": {
            "modules": "`src/c4/dashboard/prediction_app.py`, `docs/analyst_feedback_form.md`",
            "evidence": "`docs/analyst_feedback_form.md`, `src/c4/dashboard/prediction_panel.py`",
            "status": "PENDING_HUMAN_EVIDENCE",
            "limits": "Visual interface, structured explanation templates, and analyst feedback instruments are implemented; empirical human subject usability testing with SOC analysts remains pending.",
        },
        "NFR5": {
            "modules": "`src/c4/c3_adapter.py`, `docs/c3_c4_interface_contract.md`",
            "evidence": "`tests/test_c3_adapter.py::test_schema_valid_fixture`, `docs/c3_c4_interface_contract.md`",
            "status": "PARTIAL",
            "limits": "Format proposed by C4, not agreed by C3; adapter tested only against C4's own fixtures; live stream handshake pending C3 deployment.",
        },
        "NFR6": {
            "modules": "`src/c4/prediction_record.py`, `schemas/c4_prediction_record.schema.json`",
            "evidence": "`tests/test_prediction_record.py::test_schema_1_1_0_support_and_caution_counts`, `reports/7ep/prediction_record_examples.md`",
            "status": "IMPLEMENTED_AND_TESTED",
            "limits": "Full mathematical transparency with explicit state-transition numerators and denominators, Wilson score confidence bounds, candidate tactics, and support caution flags.",
        },
    }


def build_requirements_trace() -> str:
    with open(PROPOSAL_JSON_PATH, "r", encoding="utf-8") as f:
        proposal_data = json.load(f)

    req_list = proposal_data["requirements"]
    titles_by_id = {r["id"]: r["proposal_title"] for r in req_list}
    status_by_id = {r["id"]: r.get("status") for r in req_list}
    trace_definitions = get_trace_definitions(REPO_ROOT, proposal_data)

    lines = [
        "# Requirements Traceability Matrix (Prompt 14 Q4 Rebuild)",
        "",
        "> [!NOTE]",
        "> **Proposal Alignment**: Requirement IDs and Proposal Titles are loaded directly by code from `docs/proposal_requirements.json`",
        "> (transcribed from IT23348370; confirm against PDF). Status values are restricted to the closed enum:",
        "> `IMPLEMENTED_AND_TESTED`, `IMPLEMENTED_DEMONSTRATED_ON_DATASET`, `PARTIAL`, `NOT_TESTABLE_UNTIL_C3`, `PENDING_HUMAN_EVIDENCE`.",
        "",
        "---",
        "",
        "## Traceability Matrix",
        "",
        "| ID | Proposal Title | Implementing Modules | Evidence | Status | Limits |",
        "|:---|:---|:---|:---|:---|:---|",
    ]

    for req in req_list:
        rid = req["id"]
        title = titles_by_id[rid]
        trace = trace_definitions[rid]
        status = trace["status"]
        assert status in VALID_STATUSES, f"Invalid status '{status}' for {rid}"
        if status_by_id.get(rid):
            assert status == status_by_id[rid], f"Status mismatch between json and trace for {rid}: {status_by_id[rid]} vs {status}"

        # Enforce specific constraints from prompt
        if rid == "NFR4":
            assert status == "PENDING_HUMAN_EVIDENCE", "NFR4 must be PENDING_HUMAN_EVIDENCE"
        if rid in {"FR8", "FR9", "NFR5"}:
            assert status != "IMPLEMENTED_AND_TESTED", f"{rid} cannot be IMPLEMENTED_AND_TESTED"
        if rid == "FR2":
            assert status == "IMPLEMENTED_DEMONSTRATED_ON_DATASET", "FR2 must be IMPLEMENTED_DEMONSTRATED_ON_DATASET"
            assert "dataset labels" in trace["limits"], "FR2 limits must state whether episodes come from dataset labels or an algorithm"
            assert "verified by test tests/test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence" in trace["limits"]
            assert "cryptographically verified" not in trace["limits"]
        if rid == "NFR5":
            assert status == "PARTIAL", "NFR5 status must be PARTIAL"
            assert "format proposed by c4, not agreed by c3" in trace["limits"].lower()
            assert "adapter tested only against c4's own fixtures" in trace["limits"].lower()
        if rid == "FR4":
            assert "Hit@3" in trace["limits"], "FR4 limits must cite Hit@3"
            assert "Hit@1" not in trace["limits"], "FR4 limits must NOT cite Hit@1"
        if rid == "NFR1":
            assert "declared by C4, proposal has none" in trace["limits"], "NFR1 must state declared by C4, proposal has none"

        row = f"| **{rid}** | {title} | {trace['modules']} | {trace['evidence']} | `{status}` | {trace['limits']} |"
        lines.append(row)

    lines.append("")
    lines.append("---")
    lines.append("*Trace Matrix Rebuilt: Deterministic Code Generation via `scripts/build_requirements_trace.py`*")
    lines.append("")

    content = "\r\n".join(lines)
    OUT_MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD_PATH.write_bytes(content.encode("utf-8"))
    print(f"Generated {OUT_MD_PATH} ({len(content)} bytes, {len(req_list)} requirements) [PASS]")
    return content


if __name__ == "__main__":
    build_requirements_trace()
