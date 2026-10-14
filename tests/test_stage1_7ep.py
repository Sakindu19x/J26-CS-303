"""Unit tests for 7-episode Stage 1 pipeline outputs."""

import hashlib
import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_7EP = REPO_ROOT / "data" / "processed_7ep"
REPORTS_7EP = REPO_ROOT / "reports" / "7ep"


@pytest.fixture(scope="module")
def stage1_7ep_data():
    with open(PROCESSED_7EP / "attack_sequences.json", "r", encoding="utf-8") as f:
        seqs = json.load(f)
    with open(PROCESSED_7EP / "next_technique_samples.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    with open(PROCESSED_7EP / "loeo_folds.json", "r", encoding="utf-8") as f:
        folds = json.load(f)
    with open(PROCESSED_7EP / "technique_tactic_reference.json", "r", encoding="utf-8") as f:
        tech_ref = json.load(f)
    with open(PROCESSED_7EP / "normalized_events.json", "r", encoding="utf-8") as f:
        events = json.load(f)
    return {
        "seqs": seqs,
        "samples": samples,
        "folds": folds,
        "tech_ref": tech_ref,
        "events": events,
    }


def test_collapse_recomputation(stage1_7ep_data):
    """Recomputed sequence collapse from raw sequences matches stored collapsed sequences exactly."""
    seqs = stage1_7ep_data["seqs"]
    for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
        raw_items = seqs["episodes"][ep]["raw"]
        stored_collapsed = seqs["episodes"][ep]["collapsed"]

        recomputed = []
        for item in raw_items:
            item_tech_set = set(item["techniques"])
            if recomputed and set(recomputed[-1]["techniques"]) == item_tech_set:
                prev = recomputed[-1]
                prev["event_ids"].append(item["event_id"])
                prev["repeat_count"] += 1
                prev["end_timestamp"] = item["timestamp"]
            else:
                recomputed.append({
                    "event_ids": [item["event_id"]],
                    "repeat_count": 1,
                    "timestamp": item["timestamp"],
                    "end_timestamp": item["timestamp"],
                    "techniques": item["techniques"],
                })

        assert len(recomputed) == len(stored_collapsed), f"Length mismatch in {ep}"
        for idx, (rec, sto) in enumerate(zip(recomputed, stored_collapsed)):
            assert rec["event_ids"] == sto["event_ids"], f"Event IDs mismatch in {ep} at {idx}"
            assert sorted(rec["techniques"]) == sorted(sto["techniques"]), f"Tech mismatch in {ep} at {idx}"
            assert rec["repeat_count"] == sto["repeat_count"], f"Repeat count mismatch in {ep} at {idx}"


def test_sample_counts_and_bounds(stage1_7ep_data):
    """Verify collapsed_full sample counts per episode and total pooled count."""
    samples = stage1_7ep_data["samples"]
    col_full = [s for s in samples if s.get("variant") == "collapsed" and s.get("granularity") == "full"]
    assert len(col_full) == 95

    expected_per_ep = {"E1": 18, "E2": 19, "E3": 20, "E4": 10, "E5": 2, "E6": 14, "E7": 12}
    actual_per_ep = {ep: sum(1 for s in col_full if s.get("episode_id") == ep) for ep in expected_per_ep}
    assert actual_per_ep == expected_per_ep
    assert len(samples) == 452


def test_leakage_and_fold_membership(stage1_7ep_data):
    """Verify that folds have no leakage and no sample crosses episode boundaries."""
    folds = stage1_7ep_data["folds"]
    samples = stage1_7ep_data["samples"]
    events = stage1_7ep_data["events"]
    episodes = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]

    # Fold leakage
    assert len(folds) == 7
    seen_tests = set()
    for f in folds:
        test_ep = f["test_episode"]
        train_eps = f["training_episodes"]
        assert test_ep not in train_eps, f"Leakage: {test_ep} in training episodes!"
        assert len(train_eps) == 6
        assert set(train_eps) | {test_ep} == set(episodes)
        seen_tests.add(test_ep)
    assert seen_tests == set(episodes)

    # Sample leakage
    events_by_ep = {ep: {e["event_id"] for e in events if e.get("episode_id") == ep} for ep in episodes}
    for s in samples:
        ep = s["episode_id"]
        valid_evs = events_by_ep[ep]
        for inp_item in s["input_item_event_ids"]:
            if isinstance(inp_item, list):
                for ev_id in inp_item:
                    assert ev_id in valid_evs
            else:
                assert inp_item in valid_evs
        tgt = s["target_event_id"]
        if isinstance(tgt, list):
            for ev_id in tgt:
                assert ev_id in valid_evs
        else:
            assert tgt in valid_evs


def test_counting_bounds_reproduction(stage1_7ep_data):
    """Recomputed counting bounds match pre-registered values (covered=61, ceiling=59)."""
    seqs = stage1_7ep_data["seqs"]
    folds = stage1_7ep_data["folds"]
    episodes = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
    ep_collapsed = {ep: seqs["episodes"][ep]["collapsed"] for ep in episodes}

    tot_cov = 0
    tot_ceil = 0
    tot_n = 0
    for f in folds:
        test_ep = f["test_episode"]
        train_eps = f["training_episodes"]
        train_input_pool = set()
        train_target_pool = set()
        for tr in train_eps:
            items = ep_collapsed[tr]
            for i in range(len(items) - 1):
                train_input_pool.update(items[i]["techniques"])
                train_target_pool.update(items[i + 1]["techniques"])
        test_items = ep_collapsed[test_ep]
        n_s = max(0, len(test_items) - 1)
        tot_n += n_s
        for k in range(n_s):
            cur_t = set(test_items[k]["techniques"])
            tgt_t = set(test_items[k + 1]["techniques"])
            if cur_t & train_input_pool:
                tot_cov += 1
            if tgt_t & train_target_pool:
                tot_ceil += 1

    assert tot_n == 95
    assert tot_cov == 61
    assert tot_ceil == 59


def test_baseline_hashes_7ep():
    """Verify SHA-256 hashes against reports/_baseline_hashes_7ep_stage1.json."""
    hash_file = REPO_ROOT / "reports" / "_baseline_hashes_7ep_stage1.json"
    assert hash_file.is_file(), "Baseline hashes file missing!"
    with open(hash_file, "r", encoding="utf-8") as f:
        exp_hashes = json.load(f)

    for rel_path, exp_hash in exp_hashes.items():
        p = REPO_ROOT / rel_path
        assert p.is_file(), f"Stage 1 file missing: {rel_path}"
        actual_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual_hash == exp_hash, f"Hash mismatch in {rel_path}"
