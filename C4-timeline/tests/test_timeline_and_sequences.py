"""Comprehensive tests for C4 Part 0 (d), Part 1, Part 2, Part 3, and Part 5.

Includes:
- Real data regression tests (skipped if data/raw archives missing):
  190 events, labeled 27/21/29/22, unlabeled 11/8/48/24, 4 whitespace fixes.
- Double-run hash comparison proving stable event IDs.
- EpisodeManager isolation and API.
- Timeline ordering with ties and missing timestamps sorted last.
- Unlabeled steps kept in timeline but excluded from sequences.
- Collapsed sequence variant merging only identical consecutive technique sets.
- Robust filtering handling empty results and edge cases.
- Unlabeled steps skipped before gap tracking.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from c4.attack_sequence import (
    build_all_sequences,
    build_episode_sequences,
    build_raw_sequence,
    collapse_sequence,
)
from c4.data_loading import RAW_DIR
from c4.episodes import EpisodeManager
from c4.normalization import (
    EPISODE_MAPPING,
    QualityLog,
    normalize_episode_steps,
)
from c4.timeline import (
    filter_timeline,
    reconstruct_episode_timeline,
)

ARCHIVES = [
    RAW_DIR / "scenario_1_sudo_pam.zip",
    RAW_DIR / "scenario_2_cron.zip",
    RAW_DIR / "scenario_3_vnc_apt.zip",
    RAW_DIR / "scenario_4.zip",
]
ALL_RAW_EXIST = all(p.is_file() for p in ARCHIVES)


# ---------------------------------------------------------------------------
# Part 0 (d) - Real Archives Regression & Hash Stability Tests
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not ALL_RAW_EXIST, reason="Raw scenario archives missing in data/raw")
def test_real_archives_regression():
    """Assert 190 events, labeled 27/21/29/22, unlabeled 11/8/48/24, and 4 whitespace fixes."""
    qlog = QualityLog()
    counts = {}

    for scenario_id, episode_id in EPISODE_MAPPING.items():
        archive_path = RAW_DIR / f"{scenario_id}.zip"
        with zipfile.ZipFile(archive_path, "r") as zf:
            am_members = [n for n in zf.namelist() if n.endswith("attacker/logs/attackmate.json")]
            assert len(am_members) == 1, f"Expected 1 attackmate.json in {archive_path.name}"
            raw_steps = []
            with zf.open(am_members[0]) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        raw_steps.append(json.loads(line))

            norm = normalize_episode_steps(
                raw_steps=raw_steps,
                episode_id=episode_id,
                scenario_id=scenario_id,
                source_archive=archive_path.name,
                source_file=am_members[0],
                qlog=qlog,
            )
            labeled = sum(1 for e in norm if e["is_labeled"])
            unlabeled = len(norm) - labeled
            counts[episode_id] = {
                "total": len(norm),
                "labeled": labeled,
                "unlabeled": unlabeled,
            }

    # Total events assertion
    total_events = sum(c["total"] for c in counts.values())
    assert total_events == 190, f"Expected 190 total events, got {total_events}"

    # Labeled counts per episode assertion: 27, 21, 29, 22
    assert counts["E1"]["labeled"] == 27
    assert counts["E2"]["labeled"] == 21
    assert counts["E3"]["labeled"] == 29
    assert counts["E4"]["labeled"] == 22

    # Unlabeled counts per episode assertion: 11, 8, 48, 24
    assert counts["E1"]["unlabeled"] == 11
    assert counts["E2"]["unlabeled"] == 8
    assert counts["E3"]["unlabeled"] == 48
    assert counts["E4"]["unlabeled"] == 24

    # The 4 whitespace fixes assertion
    assert len(qlog.whitespace_fixes) == 4, f"Expected 4 whitespace fixes, got {len(qlog.whitespace_fixes)}"
    ws_tuples = [
        (f["episode_id"], f["step_index"], f["field"], f["raw_part"], f["cleaned_part"])
        for f in qlog.whitespace_fixes
    ]
    assert ("E1", 36, "tactics", " Discovery", "Discovery") in ws_tuples
    assert ("E3", 5, "tactics", " Lateral Movement", "Lateral Movement") in ws_tuples
    assert ("E3", 38, "techniques", "T1564.001 ", "T1564.001") in ws_tuples
    assert ("E3", 47, "techniques", "T1071.001 ", "T1071.001") in ws_tuples


@pytest.mark.skipif(not ALL_RAW_EXIST, reason="Raw scenario archives missing in data/raw")
def test_pipeline_hash_stability_double_run():
    """Runs normalization twice on real archives and asserts identical SHA-256 hashes."""
    hashes = []
    for _ in range(2):
        qlog = QualityLog()
        run_events = []
        for scenario_id, episode_id in EPISODE_MAPPING.items():
            archive_path = RAW_DIR / f"{scenario_id}.zip"
            with zipfile.ZipFile(archive_path, "r") as zf:
                am_member = [n for n in zf.namelist() if n.endswith("attacker/logs/attackmate.json")][0]
                with zf.open(am_member) as fh:
                    raw_steps = [json.loads(line.strip()) for line in fh if line.strip()]
                norm = normalize_episode_steps(
                    raw_steps=raw_steps,
                    episode_id=episode_id,
                    scenario_id=scenario_id,
                    source_archive=archive_path.name,
                    source_file=am_member,
                    qlog=qlog,
                )
                run_events.extend(norm)

        # Compute SHA-256 hash of canonical JSON serialization
        canonical_str = json.dumps(run_events, sort_keys=True, ensure_ascii=False)
        hasher = hashlib.sha256(canonical_str.encode("utf-8"))
        hashes.append(hasher.hexdigest())

    assert hashes[0] == hashes[1], "Pipeline output is not deterministic across runs!"


# ---------------------------------------------------------------------------
# Part 1 - Episode Manager
# ---------------------------------------------------------------------------


def test_episode_manager_synthetic():
    """Test EpisodeManager isolates episodes, computes metadata, and provides get/list API."""
    synthetic_events = [
        {"episode_id": "E1", "scenario_id": "s1", "source_archive": "s1.zip", "timestamp": "2025-01-01T00:00:00+00:00", "is_labeled": True},
        {"episode_id": "E1", "scenario_id": "s1", "source_archive": "s1.zip", "timestamp": "2025-01-01T00:10:00+00:00", "is_labeled": False},
        {"episode_id": "E2", "scenario_id": "s2", "source_archive": "s2.zip", "timestamp": "2025-01-02T00:00:00+00:00", "is_labeled": True},
    ]
    mgr = EpisodeManager(synthetic_events)
    episodes = mgr.list_episodes()
    assert len(episodes) == 2

    e1 = mgr.get_episode("E1")
    assert e1 is not None
    assert e1.episode_id == "E1"
    assert e1.event_count == 2
    assert e1.labeled_count == 1
    assert e1.unlabeled_count == 1
    assert e1.window_start == "2025-01-01T00:00:00+00:00"
    assert e1.window_end == "2025-01-01T00:10:00+00:00"

    e2 = mgr.get_episode("E2")
    assert e2 is not None
    assert e2.episode_id == "E2"
    assert e2.event_count == 1

    assert mgr.get_episode("E_NONEXISTENT") is None


# ---------------------------------------------------------------------------
# Part 2 & Part 5 - Timeline Reconstruction, Ties, Missing Timestamps, Filters
# ---------------------------------------------------------------------------


def test_timeline_ordering_ties_and_missing_timestamps():
    """Ties sorted by original step index, missing timestamps flagged and placed last."""
    synthetic_events = [
        {"event_id": "E1-S003", "source_line_or_step_index": 2, "timestamp": "2025-01-01T12:00:00+00:00", "timestamp_missing": False, "is_labeled": True, "techniques": ["T1059.001"]},
        {"event_id": "E1-S004", "source_line_or_step_index": 3, "timestamp": None, "timestamp_missing": True, "is_labeled": False, "techniques": []},
        {"event_id": "E1-S002", "source_line_or_step_index": 1, "timestamp": "2025-01-01T12:00:00+00:00", "timestamp_missing": False, "is_labeled": True, "techniques": ["T1059.001"]},
        {"event_id": "E1-S001", "source_line_or_step_index": 0, "timestamp": "2025-01-01T11:59:00+00:00", "timestamp_missing": False, "is_labeled": True, "techniques": ["T1078"]},
    ]

    timeline = reconstruct_episode_timeline(synthetic_events)

    # Expected order:
    # 1. E1-S001 (11:59:00, step_idx 0)
    # 2. E1-S002 (12:00:00, step_idx 1 - tie winner over step_idx 2)
    # 3. E1-S003 (12:00:00, step_idx 2)
    # 4. E1-S004 (None, step_idx 3 - missing timestamp placed last)
    assert [row["event_id"] for row in timeline] == ["E1-S001", "E1-S002", "E1-S003", "E1-S004"]
    assert timeline[0]["seconds_since_episode_start"] == 0.0
    assert timeline[0]["seconds_since_previous_event"] == 0.0
    assert timeline[1]["seconds_since_episode_start"] == 60.0
    assert timeline[1]["seconds_since_previous_event"] == 60.0
    assert timeline[2]["seconds_since_episode_start"] == 60.0
    assert timeline[2]["seconds_since_previous_event"] == 0.0
    assert timeline[3]["seconds_since_episode_start"] is None
    assert timeline[3]["seconds_since_previous_event"] is None


def test_unlabeled_steps_in_timeline_and_label_status():
    """Timeline retains unlabeled steps and assigns 'ground_truth' vs 'unlabeled'."""
    synthetic_events = [
        {"event_id": "E1-S001", "timestamp": "2025-01-01T12:00:00+00:00", "is_labeled": True, "techniques": ["T1059"], "source_line_or_step_index": 0},
        {"event_id": "E1-S002", "timestamp": "2025-01-01T12:01:00+00:00", "is_labeled": False, "techniques": [], "source_line_or_step_index": 1},
    ]
    timeline = reconstruct_episode_timeline(synthetic_events)
    assert len(timeline) == 2
    assert timeline[0]["label_status"] == "ground_truth"
    assert timeline[1]["label_status"] == "unlabeled"


def test_timeline_filters_including_empty_and_invalid():
    """Verify filter_timeline with episode, time range, hostname, technique, tactic, label_status."""
    synthetic_timeline = [
        {
            "event_id": "E1-S001", "episode_id": "E1", "timestamp": "2025-01-01T10:00:00+00:00",
            "hostname": "victim-srv", "techniques": ["T1059.001"], "tactics": ["Execution"],
            "label_status": "ground_truth",
        },
        {
            "event_id": "E1-S002", "episode_id": "E1", "timestamp": "2025-01-01T10:05:00+00:00",
            "hostname": "victim-srv", "techniques": [], "tactics": [],
            "label_status": "unlabeled",
        },
        {
            "event_id": "E2-S001", "episode_id": "E2", "timestamp": "2025-01-02T10:00:00+00:00",
            "hostname": "db-srv", "techniques": ["T1078"], "tactics": ["Defense Evasion"],
            "label_status": "ground_truth",
        },
    ]

    # Filter by episode
    res = filter_timeline(synthetic_timeline, episode_id="E1")
    assert len(res) == 2

    # Filter by label_status
    res = filter_timeline(synthetic_timeline, label_status="unlabeled")
    assert len(res) == 1
    assert res[0]["event_id"] == "E1-S002"

    # Filter by hostname (case-insensitive)
    res = filter_timeline(synthetic_timeline, hostname="DB-SRV")
    assert len(res) == 1
    assert res[0]["event_id"] == "E2-S001"

    # Filter by technique
    res = filter_timeline(synthetic_timeline, technique="t1059.001")
    assert len(res) == 1
    assert res[0]["event_id"] == "E1-S001"

    # Filter by tactic
    res = filter_timeline(synthetic_timeline, tactic="Execution")
    assert len(res) == 1

    # Filter by time range
    res = filter_timeline(synthetic_timeline, start_time="2025-01-01T09:00:00+00:00", end_time="2025-01-01T10:02:00+00:00")
    assert len(res) == 1
    assert res[0]["event_id"] == "E1-S001"

    # Non-existent filter returns empty list gracefully
    res_empty = filter_timeline(synthetic_timeline, technique="T9999")
    assert res_empty == []

    # Invalid time string handled gracefully without crash
    res_invalid_time = filter_timeline(synthetic_timeline, start_time="invalid-date")
    assert len(res_invalid_time) == 3


# ---------------------------------------------------------------------------
# Part 3 & Part 5 - ATT&CK Sequences, Collapsing, Gaps & Episode Isolation
# ---------------------------------------------------------------------------


def test_events_from_different_episodes_never_in_one_sequence():
    """Assert build_all_sequences keeps episodes completely separated."""
    events_by_episode = {
        "E1": [
            {"event_id": "E1-S001", "timestamp": "2025-01-01T10:00:00+00:00", "is_labeled": True, "techniques": ["T1059.001"], "tactics": ["Execution"]},
        ],
        "E2": [
            {"event_id": "E2-S001", "timestamp": "2025-01-02T10:00:00+00:00", "is_labeled": True, "techniques": ["T1078"], "tactics": ["Defense Evasion"]},
        ],
    }
    all_seqs = build_all_sequences(events_by_episode)
    assert "E1" in all_seqs["episodes"]
    assert "E2" in all_seqs["episodes"]

    e1_raw_ids = [item["event_id"] for item in all_seqs["episodes"]["E1"]["raw"]]
    e2_raw_ids = [item["event_id"] for item in all_seqs["episodes"]["E2"]["raw"]]
    assert e1_raw_ids == ["E1-S001"]
    assert e2_raw_ids == ["E2-S001"]
    assert set(e1_raw_ids).isdisjoint(set(e2_raw_ids))


def test_unlabeled_steps_excluded_from_sequences():
    """Unlabeled events in timeline must be strictly excluded from sequence items."""
    synthetic_timeline = [
        {"event_id": "E1-S001", "timestamp": "2025-01-01T10:00:00+00:00", "is_labeled": True, "techniques": ["T1059.001"], "tactics": []},
        {"event_id": "E1-S002", "timestamp": "2025-01-01T10:01:00+00:00", "is_labeled": False, "techniques": [], "tactics": []},
        {"event_id": "E1-S003", "timestamp": "2025-01-01T10:02:00+00:00", "is_labeled": True, "techniques": ["T1078"], "tactics": []},
    ]
    raw_seq = build_raw_sequence(synthetic_timeline)
    assert len(raw_seq) == 2
    assert [item["event_id"] for item in raw_seq] == ["E1-S001", "E1-S003"]


def test_collapsed_variant_merges_only_identical_consecutive_sets():
    """Collapsed variant merges only identical consecutive technique sets."""
    # Synthetic fixture labelled synthetic
    synthetic_raw_seq = [
        {"event_id": "E1-S001", "timestamp": "2025-01-01T10:00:00+00:00", "techniques": ["T1059.001"], "tactics": ["Execution"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "E1-S002", "timestamp": "2025-01-01T10:01:00+00:00", "techniques": ["T1059.001"], "tactics": ["Execution"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "E1-S003", "timestamp": "2025-01-01T10:02:00+00:00", "techniques": ["T1059.001", "T1078"], "tactics": ["Execution", "Defense Evasion"], "unlabeled_steps_skipped_before": 1},
        {"event_id": "E1-S004", "timestamp": "2025-01-01T10:03:00+00:00", "techniques": ["T1078", "T1059.001"], "tactics": ["Defense Evasion"], "unlabeled_steps_skipped_before": 0},
        {"event_id": "E1-S005", "timestamp": "2025-01-01T10:04:00+00:00", "techniques": ["T1059.001"], "tactics": ["Execution"], "unlabeled_steps_skipped_before": 0},
    ]
    collapsed = collapse_sequence(synthetic_raw_seq)

    # Block 1: S001 and S002 merged -> repeat_count = 2
    # Block 2: S003 and S004 merged (same technique set {T1059.001, T1078}) -> repeat_count = 2
    # Block 3: S005 -> repeat_count = 1
    assert len(collapsed) == 3
    assert collapsed[0]["repeat_count"] == 2
    assert collapsed[0]["event_ids"] == ["E1-S001", "E1-S002"]
    assert collapsed[0]["techniques"] == ["T1059.001"]

    assert collapsed[1]["repeat_count"] == 2
    assert collapsed[1]["event_ids"] == ["E1-S003", "E1-S004"]
    assert set(collapsed[1]["techniques"]) == {"T1059.001", "T1078"}

    assert collapsed[2]["repeat_count"] == 1
    assert collapsed[2]["event_ids"] == ["E1-S005"]
    assert collapsed[2]["techniques"] == ["T1059.001"]


def test_unlabeled_steps_skipped_before_tracking():
    """Assert unlabeled_steps_skipped_before accurately counts intervening unlabeled steps."""
    synthetic_timeline = [
        {"event_id": "E1-S001", "timestamp": "2025-01-01T10:00:00+00:00", "is_labeled": True, "techniques": ["T1059"], "tactics": []},
        {"event_id": "E1-S002", "timestamp": "2025-01-01T10:01:00+00:00", "is_labeled": False, "techniques": [], "tactics": []},
        {"event_id": "E1-S003", "timestamp": "2025-01-01T10:02:00+00:00", "is_labeled": False, "techniques": [], "tactics": []},
        {"event_id": "E1-S004", "timestamp": "2025-01-01T10:03:00+00:00", "is_labeled": False, "techniques": [], "tactics": []},
        {"event_id": "E1-S005", "timestamp": "2025-01-01T10:04:00+00:00", "is_labeled": True, "techniques": ["T1078"], "tactics": []},
        {"event_id": "E1-S006", "timestamp": "2025-01-01T10:05:00+00:00", "is_labeled": True, "techniques": ["T1082"], "tactics": []},
    ]

    raw_seq = build_raw_sequence(synthetic_timeline)
    assert len(raw_seq) == 3

    # S001 is first labeled -> 0 skipped before
    assert raw_seq[0]["event_id"] == "E1-S001"
    assert raw_seq[0]["unlabeled_steps_skipped_before"] == 0

    # S005 follows 3 unlabeled steps (S002, S003, S004) -> 3 skipped before
    assert raw_seq[1]["event_id"] == "E1-S005"
    assert raw_seq[1]["unlabeled_steps_skipped_before"] == 3

    # S006 immediately follows S005 (0 unlabeled between them) -> 0 skipped before
    assert raw_seq[2]["event_id"] == "E1-S006"
    assert raw_seq[2]["unlabeled_steps_skipped_before"] == 0
