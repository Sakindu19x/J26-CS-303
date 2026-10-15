"""Automated Regression Tests for Component 3 Telemetry Adapter (Prompt 13 P6).

Satisfies FR8 and NFR5:
- Preserves unknown extra fields
- Original event immutable deep copy with SHA-256 (NFR3)
- Deterministic UTC timestamp parsing with original string retained
- Deterministic tie-breaking on identical timestamps via input index
- Strict episodic segmentation (FR2)
- Duplicate event detection and audit reporting
- Unlabeled telemetry handling (retained on timeline, excluded from sequence)
- Rejection of malformed events with structured error codes
- Validation against schemas/c3_event.schema.json
- Round-trip gate: serialise Stage 1 events, adapt, match attack_sequences.json exactly (6.3)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent

from c4.c3_adapter import (
    C3AdapterError,
    adapt_c3_event,
    adapt_c3_stream,
    export_normalized_events_to_c3,
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "c3_event.schema.json"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "c3"
NORM_EVENTS_PATH = REPO_ROOT / "data" / "processed_7ep" / "normalized_events.json"
GOLD_SEQS_PATH = REPO_ROOT / "data" / "processed_7ep" / "attack_sequences.json"


@pytest.fixture(scope="module")
def c3_schema_validator() -> jsonschema.Draft7Validator:
    assert SCHEMA_PATH.is_file(), f"Missing schema: {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return jsonschema.Draft7Validator(schema)


def test_schema_valid_fixture(c3_schema_validator):
    """Verify standard C3 fixture complies with c3_event.schema.json."""
    with open(FIXTURES_DIR / "valid_event.json", "r", encoding="utf-8") as f:
        ev = json.load(f)
    c3_schema_validator.validate(ev)


def test_unknown_extra_fields_preserved():
    """Rule 1: Unknown extra fields preserved under 'extra', never dropped."""
    raw = {
        "event_id": "EV-EXTRA",
        "episode_id": "E1",
        "timestamp": "2025-09-22T13:48:45Z",
        "technique": ["T1059.004"],
        "custom_siem_rule_id": "RULE-9994",
        "nested_meta": {"cloud_region": "us-east-1", "az": "us-east-1a"},
    }
    adapted = adapt_c3_event(raw, input_index=0)
    assert "custom_siem_rule_id" in adapted["extra"]
    assert adapted["extra"]["custom_siem_rule_id"] == "RULE-9994"
    assert adapted["extra"]["nested_meta"]["cloud_region"] == "us-east-1"


def test_original_event_deep_copy_and_hash():
    """Rule 2: Original event kept as deep copy with cryptographic SHA-256 (NFR3)."""
    raw = {
        "event_id": "EV-PROV",
        "episode_id": "E1",
        "timestamp": "2025-09-22T13:48:45Z",
        "technique": ["T1059.004"],
    }
    adapted = adapt_c3_event(raw, input_index=5)
    assert "c3_event_sha256" in adapted
    assert len(adapted["c3_event_sha256"]) == 64
    assert adapted["original_event_copy"] == raw

    # Mutate raw input dictionary to verify deep copy immutability
    raw["technique"].append("MUTATED")
    assert adapted["original_event_copy"]["technique"] == ["T1059.004"]


def test_timestamp_parsed_to_utc_with_original_kept():
    """Rule 3: Timestamps parsed to UTC with original string retained."""
    raw_str = "2025-09-22T09:48:45.123456-04:00"  # UTC-4 (13:48:45 UTC)
    raw = {
        "event_id": "EV-TS",
        "episode_id": "E2",
        "timestamp": raw_str,
        "technique": ["T1082"],
    }
    adapted = adapt_c3_event(raw, input_index=1)
    assert adapted["original_timestamp"] == raw_str
    assert "+00:00" in adapted["timestamp"] or adapted["timestamp"].endswith("Z")
    assert "13:48:45.123456" in adapted["timestamp"]


def test_same_timestamp_ties_broken_by_input_index():
    """Rule 4: Same-timestamp ties broken deterministically by input index."""
    same_ts = "2025-09-22T13:00:00Z"
    events = [
        {"event_id": "EV-A", "episode_id": "E1", "timestamp": same_ts, "technique": ["T1016"]},
        {"event_id": "EV-B", "episode_id": "E1", "timestamp": same_ts, "technique": ["T1082"]},
        {"event_id": "EV-C", "episode_id": "E1", "timestamp": same_ts, "technique": ["T1033"]},
    ]
    res = adapt_c3_stream(events)
    timeline = res["episodes"]["E1"]["timeline"]
    order = [e["event_id"] for e in timeline]
    assert order == ["EV-A", "EV-B", "EV-C"]


def test_mixed_episodes_separated_never_combined():
    """Rule 5: Mixed episodes separated into isolated timelines, never combined (FR2)."""
    events = [
        {"event_id": "EV-1", "episode_id": "E1", "timestamp": "2025-09-22T10:00:00Z", "technique": ["T1059.004"]},
        {"event_id": "EV-2", "episode_id": "E2", "timestamp": "2025-09-22T10:05:00Z", "technique": ["T1082"]},
        {"event_id": "EV-3", "episode_id": "E1", "timestamp": "2025-09-22T10:10:00Z", "technique": ["T1016"]},
    ]
    res = adapt_c3_stream(events)
    assert set(res["episodes"].keys()) == {"E1", "E2"}
    e1_events = [e["event_id"] for e in res["episodes"]["E1"]["timeline"]]
    e2_events = [e["event_id"] for e in res["episodes"]["E2"]["timeline"]]
    assert e1_events == ["EV-1", "EV-3"]
    assert e2_events == ["EV-2"]


def test_duplicates_detected_and_reported():
    """Rule 6: Duplicate events detected and reported, not silently dropped."""
    ev = {"event_id": "EV-DUP", "episode_id": "E1", "timestamp": "2025-09-22T10:00:00Z", "technique": ["T1059.004"]}
    events = [ev, copy.deepcopy(ev)]
    res = adapt_c3_stream(events)
    assert len(res["duplicates"]) == 1
    dup_report = res["duplicates"][0]
    assert dup_report["reason_code"] == "DUPLICATE_EVENT"
    assert dup_report["input_index"] == 1
    # Both remain on the timeline, but the second is flagged
    assert len(res["episodes"]["E1"]["timeline"]) == 2
    assert res["episodes"]["E1"]["timeline"][1]["duplicate_flag"] is True


def test_unlabeled_event_stays_on_timeline_excluded_from_sequence():
    """Rule 7: Event with no technique stays on timeline, excluded from sequence with reason code UNLABELED_STEP."""
    events = [
        {"event_id": "EV-LABELED-1", "episode_id": "E1", "timestamp": "2025-09-22T10:00:00Z", "technique": ["T1059.004"]},
        {"event_id": "EV-UNLABELED", "episode_id": "E1", "timestamp": "2025-09-22T10:05:00Z", "technique": []},
        {"event_id": "EV-LABELED-2", "episode_id": "E1", "timestamp": "2025-09-22T10:10:00Z", "technique": ["T1082"]},
    ]
    res = adapt_c3_stream(events)
    timeline = res["episodes"]["E1"]["timeline"]
    assert len(timeline) == 3
    unlabeled_item = timeline[1]
    assert unlabeled_item["is_labeled"] is False
    assert unlabeled_item["inclusion_status"] == "EXCLUDED_FROM_SEQUENCE"
    assert unlabeled_item["exclusion_reason"] == "UNLABELED_STEP"

    # Sequence has only the 2 labeled events
    raw_seq = res["episodes"]["E1"]["raw"]
    assert len(raw_seq) == 2
    assert [x["event_id"] for x in raw_seq] == ["EV-LABELED-1", "EV-LABELED-2"]


def test_malformed_events_rejected_with_error_codes():
    """Rule 8: Malformed events rejected with error codes."""
    # Missing required episode_id
    with pytest.raises(C3AdapterError) as exc_ep:
        adapt_c3_event({"timestamp": "2025-09-22T10:00:00Z", "technique": ["T1082"]})
    assert exc_ep.value.code == "ERR_MISSING_REQUIRED_FIELD"

    # Missing required timestamp
    with pytest.raises(C3AdapterError) as exc_ts:
        adapt_c3_event({"episode_id": "E1", "technique": ["T1082"]})
    assert exc_ts.value.code == "ERR_MISSING_REQUIRED_FIELD"

    # Invalid timestamp format
    with pytest.raises(C3AdapterError) as exc_inv_ts:
        adapt_c3_event({"episode_id": "E1", "timestamp": "not-a-timestamp", "technique": ["T1082"]})
    assert exc_inv_ts.value.code == "ERR_INVALID_TIMESTAMP"


def test_priority_outside_enum_rejected():
    """Rule 9: Priority outside enum rejected with ERR_INVALID_PRIORITY_ENUM."""
    with pytest.raises(C3AdapterError) as exc:
        adapt_c3_event({
            "episode_id": "E1",
            "timestamp": "2025-09-22T10:00:00Z",
            "technique": ["T1082"],
            "investigation_priority": "ImmediateEmergency",
        })
    assert exc.value.code == "ERR_INVALID_PRIORITY_ENUM"


def test_round_trip_gate_matches_attack_sequences_7ep():
    """Section 6.3 Round-trip Gate: Serialise Stage 1 normalized_events for E1-E7 as C3 events,

    run adapter, assert produced sequences equal data/processed_7ep/attack_sequences.json exactly.
    """
    assert NORM_EVENTS_PATH.is_file(), f"Missing normalized_events.json: {NORM_EVENTS_PATH}"
    assert GOLD_SEQS_PATH.is_file(), f"Missing attack_sequences.json: {GOLD_SEQS_PATH}"

    with open(NORM_EVENTS_PATH, "r", encoding="utf-8") as f:
        norm_events = json.load(f)
    with open(GOLD_SEQS_PATH, "r", encoding="utf-8") as f:
        gold_seqs = json.load(f)

    # 1. Serialise to C3 events
    c3_events = export_normalized_events_to_c3(norm_events)
    assert len(c3_events) == len(norm_events) == 274

    # 2. Run C3 adapter stream
    stream_res = adapt_c3_stream(c3_events)
    episodes = stream_res["episodes"]

    # 3. Assert equality across all 7 episodes (E1-E7)
    expected_eps = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
    assert sorted(episodes.keys()) == expected_eps

    for ep_id in expected_eps:
        # Check raw sequences
        act_raw = episodes[ep_id]["raw"]
        exp_raw = gold_seqs["episodes"][ep_id]["raw"]
        assert len(act_raw) == len(exp_raw), f"Episode {ep_id}: raw length mismatch ({len(act_raw)} vs {len(exp_raw)})"
        for idx, (a, e) in enumerate(zip(act_raw, exp_raw)):
            assert a["event_id"] == e["event_id"], f"{ep_id} raw #{idx} event_id mismatch"
            assert sorted(a["techniques"]) == sorted(e["techniques"]), f"{ep_id} raw #{idx} techniques mismatch"

        # Check collapsed sequences
        act_col = episodes[ep_id]["collapsed"]
        exp_col = gold_seqs["episodes"][ep_id]["collapsed"]
        assert len(act_col) == len(exp_col), f"Episode {ep_id}: collapsed length mismatch ({len(act_col)} vs {len(exp_col)})"
        for idx, (a, e) in enumerate(zip(act_col, exp_col)):
            assert a["event_ids"] == e["event_ids"], f"{ep_id} collapsed #{idx} event_ids mismatch"
            assert sorted(a["techniques"]) == sorted(e["techniques"]), f"{ep_id} collapsed #{idx} techniques mismatch"
