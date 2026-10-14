#!/usr/bin/env python3
"""Acceptance gates for 7-episode Stage 1 against reports/new_episodes_intake_audit.json."""

import json
import sys
from pathlib import Path


def run_acceptance_gates() -> bool:
    repo_root = Path(__file__).resolve().parent.parent

    with open(repo_root / "reports/new_episodes_intake_audit.json", "r", encoding="utf-8") as f:
        audit = json.load(f)

    with open(repo_root / "data/processed_7ep/attack_sequences.json", "r", encoding="utf-8") as f:
        seqs = json.load(f)

    with open(repo_root / "data/processed_7ep/next_technique_samples.json", "r", encoding="utf-8") as f:
        samples = json.load(f)

    with open(repo_root / "data/processed_7ep/technique_tactic_reference.json", "r", encoding="utf-8") as f:
        tech_ref = json.load(f)

    print("=== PART 3c: ACCEPTANCE GATES AGAINST reports/new_episodes_intake_audit.json ===")
    all_gates_pass = True

    episodes = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]
    audit_profile = audit["episodes_profile"]

    # Gate 1: collapsed_full samples per episode
    expected_samples = {ep: audit_profile[ep]["next_technique_samples_collapsed"] for ep in episodes}
    expected_total_samples = audit["counting_bounds_designs"]["design_b_7episodes"]["pooled"]["n_samples"]

    col_samples = [
        s for s in samples
        if s.get("variant") == "collapsed" and s.get("granularity") == "full"
    ]
    actual_samples = {ep: sum(1 for s in col_samples if s.get("episode_id") == ep) for ep in episodes}
    actual_total_samples = len(col_samples)

    g1_pass = (actual_samples == expected_samples) and (actual_total_samples == expected_total_samples)
    status_str = "PASS" if g1_pass else "FAIL"
    print(f"Gate 1 (collapsed_full samples per episode): {status_str}")
    print(f"  Expected: {expected_samples} (N={expected_total_samples})")
    print(f"  Actual:   {actual_samples} (N={actual_total_samples})")
    if not g1_pass:
        all_gates_pass = False

    # Gate 2: Counting bounds on 7-fold design
    ep_collapsed = {ep: seqs["episodes"][ep]["collapsed"] for ep in episodes}
    tot_cov = 0
    tot_ceil = 0
    tot_n = 0
    for ep in episodes:
        train_eps = [x for x in episodes if x != ep]
        train_input_pool = set()
        train_target_pool = set()
        for tr in train_eps:
            items = ep_collapsed[tr]
            for i in range(len(items) - 1):
                train_input_pool.update(items[i]["techniques"])
                train_target_pool.update(items[i + 1]["techniques"])
        test_items = ep_collapsed[ep]
        n_s = max(0, len(test_items) - 1)
        tot_n += n_s
        for k in range(n_s):
            cur_t = set(test_items[k]["techniques"])
            tgt_t = set(test_items[k + 1]["techniques"])
            if cur_t & train_input_pool:
                tot_cov += 1
            if tgt_t & train_target_pool:
                tot_ceil += 1

    exp_bounds = audit["counting_bounds_designs"]["design_b_7episodes"]["pooled"]
    exp_cov = exp_bounds["covered"]
    exp_cov_pct = exp_bounds["coverage_rate"] * 100
    exp_ceil = exp_bounds["ceiling_hits"]
    exp_ceil_pct = exp_bounds["ceiling_rate"] * 100

    act_cov_pct = (tot_cov / tot_n) * 100 if tot_n > 0 else 0.0
    act_ceil_pct = (tot_ceil / tot_n) * 100 if tot_n > 0 else 0.0

    g2_pass = (tot_cov == exp_cov) and (tot_ceil == exp_ceil) and (tot_n == exp_bounds["n_samples"])
    status_str = "PASS" if g2_pass else "FAIL"
    print(f"Gate 2 (counting bounds on 7-fold design): {status_str}")
    print(f"  Expected: covered={exp_cov} ({exp_cov_pct:.2f}%), ceiling={exp_ceil} ({exp_ceil_pct:.2f}%)")
    print(f"  Actual:   covered={tot_cov} ({act_cov_pct:.2f}%), ceiling={tot_ceil} ({act_ceil_pct:.2f}%)")
    if not g2_pass:
        all_gates_pass = False

    # Gate 3: Distinct technique counts per episode as in audit
    expected_distinct = {ep: audit_profile[ep]["distinct_techniques_full"] for ep in episodes}
    actual_distinct = {}
    for ep in episodes:
        distinct_set = set()
        for step in seqs["episodes"][ep]["raw"]:
            distinct_set.update(step["techniques"])
        actual_distinct[ep] = sorted(list(distinct_set))

    g3_pass = True
    for ep in episodes:
        if actual_distinct[ep] != expected_distinct[ep]:
            g3_pass = False
            print(f"  Mismatch in {ep}: expected {len(expected_distinct[ep])}, got {len(actual_distinct[ep])}")
    status_str = "PASS" if g3_pass else "FAIL"
    print(f"Gate 3 (distinct technique counts per episode): {status_str}")
    for ep in episodes:
        print(f"  {ep}: {len(actual_distinct[ep])} techniques (expected {len(expected_distinct[ep])})")
    if not g3_pass:
        all_gates_pass = False

    # Gate 4: All technique IDs valid in ATT&CK v16.1
    all_tech_ids = set()
    for ep in episodes:
        all_tech_ids.update(actual_distinct[ep])

    invalid_techs = [
        t for t in all_tech_ids
        if t not in tech_ref or tech_ref[t].get("revoked") or tech_ref[t].get("deprecated")
    ]
    g4_pass = (len(invalid_techs) == 0)
    status_str = "PASS" if g4_pass else "FAIL"
    print(f"Gate 4 (all technique IDs valid in ATT&CK v16.1): {status_str}")
    print(f"  Total unique techniques across E1-E7: {len(all_tech_ids)}")
    print(f"  Invalid / revoked / deprecated: {invalid_techs}")
    if not g4_pass:
        all_gates_pass = False

    overall_status = "PASS" if all_gates_pass else "STOP / FAIL"
    print(f"\nOVERALL ACCEPTANCE GATES: {overall_status}")
    return all_gates_pass


if __name__ == "__main__":
    success = run_acceptance_gates()
    sys.exit(0 if success else 1)
