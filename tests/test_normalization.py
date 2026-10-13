"""Unit tests for AttackMate normalization and quality checks using synthetic fixtures."""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from c4.normalization import (
    QualityLog,
    clean_tactics,
    clean_techniques,
    extract_technique_names,
    normalize_episode_steps,
    normalize_step,
    parse_step_timestamp,
)


def test_timestamp_parsing_and_utc_assumption():
    # Synthetic naive ISO timestamp
    iso_utc, orig_str, is_missing = parse_step_timestamp("2025-09-22T13:48:30.907163")
    assert iso_utc == "2025-09-22T13:48:30.907163+00:00"
    assert orig_str == "2025-09-22T13:48:30.907163"
    assert not is_missing

    # Synthetic missing / invalid timestamp
    iso_none, orig_none, is_missing_none = parse_step_timestamp(None)
    assert iso_none is None
    assert is_missing_none

    iso_inv, orig_inv, is_missing_inv = parse_step_timestamp("not-a-timestamp")
    assert iso_inv is None
    assert orig_inv == "not-a-timestamp"
    assert is_missing_inv


def test_whitespace_cleaning():
    qlog = QualityLog()
    # Synthetic whitespace in technique: "T1564.001 "
    valid, invalid = clean_techniques("T1564.001 , T1071.001 ", step_idx=0, episode_id="E_SYNTH", qlog=qlog)
    assert valid == ["T1564.001", "T1071.001"]
    assert invalid == []
    assert len(qlog.whitespace_fixes) == 2

    # Synthetic whitespace in tactics: " Discovery"
    cleaned_t = clean_tactics("Defense Evasion,  Discovery", step_idx=0, episode_id="E_SYNTH", qlog=qlog)
    assert cleaned_t == ["Defense Evasion", "Discovery"]
    assert len(qlog.whitespace_fixes) == 3


def test_invalid_technique_id():
    qlog = QualityLog()
    valid, invalid = clean_techniques("T1059.001, NOT_A_TECH, T99999", step_idx=1, episode_id="E_SYNTH", qlog=qlog)
    assert valid == ["T1059.001"]
    assert invalid == ["NOT_A_TECH", "T99999"]
    assert len(qlog.invalid_techniques) == 2
    assert qlog.invalid_techniques[0]["invalid_value"] == "NOT_A_TECH"


def test_multi_technique_step_kept_as_one_event():
    qlog = QualityLog()
    synthetic_raw = {
        "start-datetime": "2025-01-01T00:00:00",
        "type": "shell",
        "cmd": "whoami",
        "parameters": {
            "metadata": {
                "techniques": "T1105,T1556.003",
                "tactics": "Command and Control,Persistence",
            }
        },
    }
    event = normalize_step(synthetic_raw, 0, "E1", "scenario_synth", "synth.zip", "attackmate.json", qlog)
    assert event["is_labeled"] is True
    assert event["n_techniques"] == 2
    assert event["techniques"] == ["T1105", "T1556.003"]
    assert isinstance(event["techniques"], list)


def test_unlabeled_step_preserved():
    qlog = QualityLog()
    synthetic_unlabeled = {
        "start-datetime": "2025-01-01T00:01:00",
        "type": "sleep",
        "cmd": "sleep 10",
        "parameters": {"metadata": None},
    }
    event = normalize_step(synthetic_unlabeled, 1, "E1", "scenario_synth", "synth.zip", "attackmate.json", qlog)
    assert event["is_labeled"] is False
    assert event["n_techniques"] == 0
    assert event["techniques"] == []
    assert event["step_type"] == "sleep"


def test_episode_separation():
    qlog = QualityLog()
    e1_steps = [{"start-datetime": "2025-01-01T00:00:00", "type": "shell", "cmd": "cmd1", "parameters": {}}]
    e2_steps = [{"start-datetime": "2025-01-02T00:00:00", "type": "shell", "cmd": "cmd2", "parameters": {}}]

    events_e1 = normalize_episode_steps(e1_steps, "E1", "scen_1", "s1.zip", "am.json", qlog)
    events_e2 = normalize_episode_steps(e2_steps, "E2", "scen_2", "s2.zip", "am.json", qlog)

    assert len(events_e1) == 1
    assert len(events_e2) == 1
    assert events_e1[0]["episode_id"] == "E1"
    assert events_e2[0]["episode_id"] == "E2"
    assert events_e1[0]["event_id"] == "E1-S001"
    assert events_e2[0]["event_id"] == "E2-S001"


def test_timestamp_tie_ordering_and_missing_last():
    qlog = QualityLog()
    synthetic_steps = [
        {"start-datetime": "2025-01-01T00:05:00", "type": "step_b", "cmd": "b", "parameters": {}},  # idx 0
        {"start-datetime": None, "type": "step_missing", "cmd": "missing", "parameters": {}},          # idx 1
        {"start-datetime": "2025-01-01T00:05:00", "type": "step_c", "cmd": "c", "parameters": {}},  # idx 2 (tie with idx 0)
        {"start-datetime": "2025-01-01T00:01:00", "type": "step_a", "cmd": "a", "parameters": {}},  # idx 3 (earliest)
    ]
    sorted_events = normalize_episode_steps(synthetic_steps, "E1", "scen_1", "s1.zip", "am.json", qlog)

    # Expected order:
    # 1. idx 3 (00:01:00)
    # 2. idx 0 (00:05:00, tie break by original idx 0)
    # 3. idx 2 (00:05:00, tie break by original idx 2)
    # 4. idx 1 (missing timestamp ordered last)
    assert [e["source_line_or_step_index"] for e in sorted_events] == [3, 0, 2, 1]
    assert sorted_events[-1]["timestamp_missing"] is True


def test_stable_event_ids_across_runs():
    qlog1 = QualityLog()
    qlog2 = QualityLog()
    synthetic_steps = [
        {"start-datetime": "2025-01-01T00:00:00", "type": "a", "cmd": "a", "parameters": {}},
        {"start-datetime": "2025-01-01T00:01:00", "type": "b", "cmd": "b", "parameters": {}},
    ]
    run1 = normalize_episode_steps(synthetic_steps, "E1", "s1", "s1.zip", "am.json", qlog1)
    run2 = normalize_episode_steps(synthetic_steps, "E1", "s1", "s1.zip", "am.json", qlog2)

    ids1 = [e["event_id"] for e in run1]
    ids2 = [e["event_id"] for e in run2]
    assert ids1 == ids2 == ["E1-S001", "E1-S002"]


def test_malformed_key_case():
    qlog = QualityLog()
    synthetic_metadata = {
        "techniques": "T1105,T1556.003",
        'technique_name:"Ingress Tool Transfer,Modify Authentication Process': 'Pluggable Authentication Modules"',
    }
    recovered = extract_technique_names(synthetic_metadata, step_idx=23, episode_id="E1", qlog=qlog)
    assert len(recovered) == 1
    assert "Ingress Tool Transfer,Modify Authentication Process" in recovered[0]
    assert "Pluggable Authentication Modules" in recovered[0]
    assert len(qlog.malformed_records) == 1
    assert qlog.malformed_records[0]["episode_id"] == "E1"
