#!/usr/bin/env python3
"""Independent verifier for 7-episode Stage 1 data pipeline.

Reads ONLY the 7-episode JSON artifacts in data/processed_7ep/ and reports/7ep/.
Verifies:
1. Recomputed collapse from raw sequences matches stored collapsed sequences exactly.
2. Recomputed sample counts from attack_sequences match stored next_technique_samples.
3. No sample crosses an episode boundary (leakage check).
4. Fold membership: 7 folds, LOEO, no test episode in training set, complete coverage.
5. Counting bounds: 95 collapsed samples, 61 covered (64.21%), 59 ceiling (62.11%).
6. Technique validity against ATT&CK v16.1 reference.
"""

import json
import sys
from pathlib import Path


def verify_stage1_7ep(base_dir: Path | None = None) -> bool:
    if base_dir is None:
        base_dir = Path(__file__).resolve().parents[2]

    processed_dir = base_dir / "data" / "processed_7ep"
    reports_dir = base_dir / "reports" / "7ep"

    print("=" * 80)
    print("VERIFYING 7-EPISODE STAGE 1 ARTIFACTS (INDEPENDENT VERIFIER)")
    print("=" * 80)

    # 1. Load files
    with open(processed_dir / "attack_sequences.json", "r", encoding="utf-8") as f:
        seqs = json.load(f)
    with open(processed_dir / "next_technique_samples.json", "r", encoding="utf-8") as f:
        samples = json.load(f)
    with open(processed_dir / "loeo_folds.json", "r", encoding="utf-8") as f:
        folds = json.load(f)
    with open(processed_dir / "technique_tactic_reference.json", "r", encoding="utf-8") as f:
        tech_ref = json.load(f)
    with open(processed_dir / "normalized_events.json", "r", encoding="utf-8") as f:
        events = json.load(f)

    episodes = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
    assert set(seqs["episodes"].keys()) == set(episodes), "Mismatch in episode set!"

    # 2. Collapse from raw verification
    print("\n[Check 1] Recomputing sequence collapse from raw sequences...")
    for ep in episodes:
        raw_items = seqs["episodes"][ep]["raw"]
        stored_collapsed = seqs["episodes"][ep]["collapsed"]

        # Independent collapse algorithm: group adjacent items with identical set of techniques
        recomputed_collapsed = []
        for item in raw_items:
            item_tech_set = set(item["techniques"])
            if recomputed_collapsed and set(recomputed_collapsed[-1]["techniques"]) == item_tech_set:
                prev = recomputed_collapsed[-1]
                prev["event_ids"].append(item["event_id"])
                prev["repeat_count"] += 1
                prev["end_timestamp"] = item["timestamp"]
            else:
                recomputed_collapsed.append({
                    "event_ids": [item["event_id"]],
                    "repeat_count": 1,
                    "timestamp": item["timestamp"],
                    "end_timestamp": item["timestamp"],
                    "techniques": item["techniques"],
                })

        assert len(recomputed_collapsed) == len(stored_collapsed), (
            f"Episode {ep} collapsed length mismatch: {len(recomputed_collapsed)} vs {len(stored_collapsed)}"
        )
        for idx, (rec, sto) in enumerate(zip(recomputed_collapsed, stored_collapsed)):
            assert rec["event_ids"] == sto["event_ids"], f"Event IDs mismatch in {ep} at {idx}"
            assert sorted(rec["techniques"]) == sorted(sto["techniques"]), f"Techniques mismatch in {ep} at {idx}"
            assert rec["repeat_count"] == sto["repeat_count"], f"Repeat count mismatch in {ep} at {idx}"
        print(f"  {ep}: raw={len(raw_items)} -> collapsed={len(stored_collapsed)} [MATCH]")

    # 3. Sample counts recomputation
    print("\n[Check 2] Recomputing sample counts from sequences...")
    for ep in episodes:
        raw_len = len(seqs["episodes"][ep]["raw"])
        col_len = len(seqs["episodes"][ep]["collapsed"])
        exp_raw_samples = max(0, raw_len - 1)
        exp_col_samples = max(0, col_len - 1)

        ep_samps = [s for s in samples if s.get("episode_id") == ep]
        rf = sum(1 for s in ep_samps if s.get("variant") == "raw" and s.get("granularity") == "full")
        rp = sum(1 for s in ep_samps if s.get("variant") == "raw" and s.get("granularity") == "parent")
        cf = sum(1 for s in ep_samps if s.get("variant") == "collapsed" and s.get("granularity") == "full")
        cp = sum(1 for s in ep_samps if s.get("variant") == "collapsed" and s.get("granularity") == "parent")

        assert rf == exp_raw_samples, f"Mismatch raw_full in {ep}: {rf} vs {exp_raw_samples}"
        assert rp == exp_raw_samples, f"Mismatch raw_parent in {ep}: {rp} vs {exp_raw_samples}"
        assert cf == exp_col_samples, f"Mismatch col_full in {ep}: {cf} vs {exp_col_samples}"
        assert cp == exp_col_samples, f"Mismatch col_parent in {ep}: {cp} vs {exp_col_samples}"
        print(f"  {ep}: raw samples = {rf}, collapsed samples = {cf} [MATCH]")

    assert len(samples) == 452, f"Total samples count mismatch: {len(samples)} vs 452"
    print("  Total samples across all variants/slices: 452 [MATCH]")

    # 4. Leakage & Boundary Check
    print("\n[Check 3] Sample boundary and episode leakage check...")
    events_by_ep = {ep: {e["event_id"] for e in events if e.get("episode_id") == ep} for ep in episodes}
    for s in samples:
        ep = s["episode_id"]
        valid_evs = events_by_ep[ep]
        for inp_item in s["input_item_event_ids"]:
            if isinstance(inp_item, list):
                for ev_id in inp_item:
                    assert ev_id in valid_evs, f"Leakage: input event {ev_id} not in episode {ep}"
            else:
                assert inp_item in valid_evs, f"Leakage: input event {inp_item} not in episode {ep}"
        tgt = s["target_event_id"]
        if isinstance(tgt, list):
            for ev_id in tgt:
                assert ev_id in valid_evs, f"Leakage: target event {ev_id} not in episode {ep}"
        else:
            assert tgt in valid_evs, f"Leakage: target event {tgt} not in episode {ep}"
    print("  All 452 samples strictly respect episode boundaries: [PASS]")

    # 5. Fold membership
    print("\n[Check 4] 7-fold LOEO structure and leakage verification...")
    assert len(folds) == 7, f"Expected 7 folds, got {len(folds)}"
    seen_test_eps = set()
    for f in folds:
        test_ep = f["test_episode"]
        train_eps = f["training_episodes"]
        assert test_ep in episodes, f"Unknown test episode: {test_ep}"
        assert test_ep not in train_eps, f"Data leakage! Test episode {test_ep} in training episodes!"
        assert len(train_eps) == 6, f"Expected 6 training episodes, got {len(train_eps)}"
        assert set(train_eps) | {test_ep} == set(episodes), "Folds do not partition all 7 episodes!"
        seen_test_eps.add(test_ep)
    assert seen_test_eps == set(episodes), "Not all episodes appear as test episode!"
    print("  7-fold LOEO design: 7 folds, 6 train / 1 test, zero leakage: [PASS]")

    # 6. Counting Bounds Recomputation
    print("\n[Check 5] Recomputing counting bounds across 7 folds...")
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

    assert tot_n == 95, f"Expected 95 pooled samples, got {tot_n}"
    assert tot_cov == 61, f"Expected 61 covered, got {tot_cov}"
    assert tot_ceil == 59, f"Expected 59 ceiling hits, got {tot_ceil}"
    print(f"  Pooled N = {tot_n}, Covered = {tot_cov} ({tot_cov/tot_n*100:.2f}%), Ceiling = {tot_ceil} ({tot_ceil/tot_n*100:.2f}%) [PASS]")

    # 7. Technique reference validity
    print("\n[Check 6] Technique vocabulary validity check...")
    all_techs = set()
    for ep in episodes:
        for item in seqs["episodes"][ep]["raw"]:
            all_techs.update(item["techniques"])
    for t in all_techs:
        assert t in tech_ref, f"Technique {t} missing from reference!"
        assert not tech_ref[t].get("revoked", False), f"Technique {t} is revoked!"
        assert not tech_ref[t].get("deprecated", False), f"Technique {t} is deprecated!"
    print(f"  All {len(all_techs)} distinct techniques are valid ATT&CK v16.1 enterprise techniques [PASS]")

    print("\n" + "=" * 80)
    print("ALL 7-EPISODE STAGE 1 CHECKS PASSED PERFECTLY")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = verify_stage1_7ep()
    sys.exit(0 if success else 1)
