"""Tests for next-step samples, MITRE reference, LOEO folds, and sequence statistics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from c4.attack_sequence import collapse_sequence
from c4.data_loading import RAW_DIR
from c4.mitre_reference import to_parent_technique, to_parent_technique_set
from c4.samples import build_samples_for_sequence, generate_all_samples
from c4.sequence_statistics import compute_sequence_statistics


# ---------------------------------------------------------------------------
# Synthetic Unit Tests (Labelled synthetic)
# ---------------------------------------------------------------------------


def test_prefix_target_alignment_synthetic():
    """Synthetic test: sequence of length 4 yields 3 samples with strict prefix/target alignment."""
    synthetic_items = [
        {"event_id": "S1", "techniques": ["T1059.001"], "tactics": ["Execution"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "S2", "techniques": ["T1078"], "tactics": ["Defense Evasion"], "unlabeled_steps_skipped_before": 1},
        {"event_id": "S3", "techniques": ["T1105"], "tactics": ["Command and Control"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "S4", "techniques": ["T1082"], "tactics": ["Discovery"], "unlabeled_steps_skipped_before": 2},
    ]

    samples = build_samples_for_sequence(
        items=synthetic_items,
        episode_id="E_SYNTH",
        scenario_id="scenario_synth",
        variant="raw",
        granularity="full",
        min_prefix_length=1,
    )

    assert len(samples) == 3

    # Sample 0 (k=1): input=[S1], target=S2
    assert samples[0]["prefix_length"] == 1
    assert samples[0]["input_item_event_ids"] == ["S1"]
    assert samples[0]["current_technique_set"] == ["T1059.001"]
    assert samples[0]["target_event_id"] == "S2"
    assert samples[0]["target_technique_set"] == ["T1078"]
    assert samples[0]["unlabeled_steps_skipped_before_target"] == 1

    # Sample 1 (k=2): input=[S1, S2], target=S3
    assert samples[1]["prefix_length"] == 2
    assert samples[1]["input_item_event_ids"] == ["S1", "S2"]
    assert samples[1]["current_technique_set"] == ["T1078"]
    assert samples[1]["target_event_id"] == "S3"
    assert samples[1]["target_technique_set"] == ["T1105"]
    assert samples[1]["unlabeled_steps_skipped_before_target"] == 0

    # Sample 2 (k=3): input=[S1, S2, S3], target=S4
    assert samples[2]["prefix_length"] == 3
    assert samples[2]["input_item_event_ids"] == ["S1", "S2", "S3"]
    assert samples[2]["current_technique_set"] == ["T1105"]
    assert samples[2]["target_event_id"] == "S4"
    assert samples[2]["target_technique_set"] == ["T1082"]
    assert samples[2]["unlabeled_steps_skipped_before_target"] == 2


def test_no_cross_episode_samples_synthetic():
    """Synthetic test: samples never cross episode boundaries."""
    synthetic_sequences_data = {
        "episodes": {
            "E1": {
                "raw": [
                    {"event_id": "E1-S1", "techniques": ["T1059"], "tactics": [], "unlabeled_steps_skipped_before": 0},
                    {"event_id": "E1-S2", "techniques": ["T1078"], "tactics": [], "unlabeled_steps_skipped_before": 0},
                ],
                "collapsed": [],
            },
            "E2": {
                "raw": [
                    {"event_id": "E2-S1", "techniques": ["T1105"], "tactics": [], "unlabeled_steps_skipped_before": 0},
                    {"event_id": "E2-S2", "techniques": ["T1082"], "tactics": [], "unlabeled_steps_skipped_before": 0},
                ],
                "collapsed": [],
            },
        }
    }

    samples = generate_all_samples(synthetic_sequences_data, min_prefix_length=1)
    e1_samples = [s for s in samples if s["episode_id"] == "E1" and s["variant"] == "raw" and s["granularity"] == "full"]
    e2_samples = [s for s in samples if s["episode_id"] == "E2" and s["variant"] == "raw" and s["granularity"] == "full"]

    assert len(e1_samples) == 1
    assert len(e2_samples) == 1

    # Verify E1 sample contains exclusively E1 events
    assert e1_samples[0]["input_item_event_ids"] == ["E1-S1"]
    assert e1_samples[0]["target_event_id"] == "E1-S2"

    # Verify E2 sample contains exclusively E2 events
    assert e2_samples[0]["input_item_event_ids"] == ["E2-S1"]
    assert e2_samples[0]["target_event_id"] == "E2-S2"


def test_parent_granularity_mapping_synthetic():
    """Synthetic test: parent technique mapping converts subtechniques to parent ID."""
    assert to_parent_technique("T1059.006") == "T1059"
    assert to_parent_technique("T1059.001") == "T1059"
    assert to_parent_technique("T1105") == "T1105"
    assert to_parent_technique("T1548.003") == "T1548"

    tech_set = ["T1059.006", "T1059.001", "T1105"]
    parent_set = to_parent_technique_set(tech_set)
    assert parent_set == ["T1059", "T1105"]


def test_multi_technique_inputs_targets_kept_as_sets_synthetic():
    """Synthetic test: multi-technique steps remain sets without being split into separate items."""
    synthetic_items = [
        {"event_id": "S1", "techniques": ["T1105", "T1556.003"], "tactics": ["C2", "Persistence"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "S2", "techniques": ["T1036.005", "T1564.001"], "tactics": ["Defense Evasion"], "unlabeled_steps_skipped_before": 0},
    ]

    samples = build_samples_for_sequence(
        items=synthetic_items,
        episode_id="E_SYNTH",
        scenario_id="scenario_synth",
        variant="raw",
        granularity="full",
    )

    assert len(samples) == 1
    sample = samples[0]

    assert sample["current_technique_set"] == ["T1105", "T1556.003"]
    assert sample["target_technique_set"] == ["T1036.005", "T1564.001"]
    assert sample["flags"]["is_multi_technique_input"] is True
    assert sample["flags"]["is_multi_technique_target"] is True


def test_fold_construction_never_leaks_test_episode_synthetic():
    """Synthetic test: LOEO fold computation isolates test episode completely from training set."""
    synthetic_seq_data = {
        "episodes": {
            "E1": {"raw": [{"techniques": ["T1001"]}, {"techniques": ["T1002"]}], "collapsed": []},
            "E2": {"raw": [{"techniques": ["T2001"]}, {"techniques": ["T2002"]}], "collapsed": []},
            "E3": {"raw": [{"techniques": ["T3001"]}, {"techniques": ["T3002"]}], "collapsed": []},
            "E4": {"raw": [{"techniques": ["T4001"]}, {"techniques": ["T4002"]}], "collapsed": []},
        }
    }

    samples = generate_all_samples(synthetic_seq_data, min_prefix_length=1)
    stats = compute_sequence_statistics(samples, synthetic_seq_data)

    folds = stats["slices"]["raw_full"]["loeo_folds"]
    assert len(folds) == 4

    for fold in folds:
        test_ep = fold["test_episode"]
        train_eps = fold["train_episodes"]

        assert test_ep not in train_eps
        assert len(train_eps) == 3


def test_collapsed_gaps_list_synthetic():
    """Synthetic test: collapsed items store per-merge gaps list (unlabeled_steps_skipped_between)."""
    synthetic_raw_seq = [
        {"event_id": "S1", "timestamp": "2025-01-01T10:00:00", "techniques": ["T1059"], "tactics": ["Exec"], "unlabeled_steps_skipped_before": 2},
        {"event_id": "S2", "timestamp": "2025-01-01T10:01:00", "techniques": ["T1059"], "tactics": ["Exec"], "unlabeled_steps_skipped_before": 3},
        {"event_id": "S3", "timestamp": "2025-01-01T10:02:00", "techniques": ["T1059"], "tactics": ["Exec"], "unlabeled_steps_skipped_before": 1},
        {"event_id": "S4", "techniques": ["T1082"], "timestamp": "2025-01-01T10:03:00", "tactics": ["Disc"], "unlabeled_steps_skipped_before": 0},
    ]

    collapsed = collapse_sequence(synthetic_raw_seq)
    assert len(collapsed) == 2

    # Merged item S1 + S2 + S3
    block1 = collapsed[0]
    assert block1["repeat_count"] == 3
    assert block1["event_ids"] == ["S1", "S2", "S3"]
    assert block1["unlabeled_steps_skipped_before"] == 2
    assert block1["unlabeled_steps_skipped_between"] == [3, 1]

    # Non-merged item S4
    block2 = collapsed[1]
    assert block2["repeat_count"] == 1
    assert block2["event_ids"] == ["S4"]
    assert block2["unlabeled_steps_skipped_before"] == 0
    assert block2["unlabeled_steps_skipped_between"] == []


# ---------------------------------------------------------------------------
# Real Data Sample Counts Assertion
# ---------------------------------------------------------------------------


def test_real_data_total_sample_counts():
    """Assert real data total samples: 95 raw and 67 collapsed at granularity full ID."""
    processed_dir = Path(__file__).resolve().parents[1] / "data" / "processed"
    samples_json_path = processed_dir / "next_technique_samples.json"

    if not samples_json_path.is_file():
        pytest.skip("next_technique_samples.json not found")

    with open(samples_json_path, encoding="utf-8") as f:
        samples = json.load(f)

    raw_full = [s for s in samples if s["variant"] == "raw" and s["granularity"] == "full"]
    col_full = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]
    raw_par = [s for s in samples if s["variant"] == "raw" and s["granularity"] == "parent"]
    col_par = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "parent"]

    # Assert expected sample counts: 95 raw, 67 collapsed
    assert len(raw_full) == 95, f"Expected 95 raw (full) samples, got {len(raw_full)}"
    assert len(col_full) == 67, f"Expected 67 collapsed (full) samples, got {len(col_full)}"
    assert len(raw_par) == 95, f"Expected 95 raw (parent) samples, got {len(raw_par)}"
    assert len(col_par) == 67, f"Expected 67 collapsed (parent) samples, got {len(col_par)}"

    # Per-episode count assertions for raw full
    raw_ep_counts = {}
    for s in raw_full:
        raw_ep_counts[s["episode_id"]] = raw_ep_counts.get(s["episode_id"], 0) + 1
    assert raw_ep_counts == {"E1": 26, "E2": 20, "E3": 28, "E4": 21}

    # Per-episode count assertions for collapsed full
    col_ep_counts = {}
    for s in col_full:
        col_ep_counts[s["episode_id"]] = col_ep_counts.get(s["episode_id"], 0) + 1
    assert col_ep_counts == {"E1": 18, "E2": 19, "E3": 20, "E4": 10}
