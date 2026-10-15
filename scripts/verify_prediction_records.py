#!/usr/bin/env python3
"""Independent Verifier for Explainable Prediction Records (G-P5-1, G-P5-2, G-P5-5).

Strictly does NOT import src/c4.
Directly parses data/processed_7ep/attack_sequences.json,
recounts training transitions independently,
validates schema compliance using jsonschema,
and verifies mathematical exactness to within 1e-9.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import jsonschema

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent

SEQS_PATH = REPO_ROOT / "data" / "processed_7ep" / "attack_sequences.json"
CSV_PATH = REPO_ROOT / "data" / "processed_7ep" / "evaluation_7ep_predictions.csv"
JSONL_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"
SCHEMA_PATH = REPO_ROOT / "schemas" / "c4_prediction_record.schema.json"
EXAMPLES_MD_PATH = REPO_ROOT / "reports" / "7ep" / "prediction_record_examples.md"


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_canonical(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def recount_technique_transitions(
    episodes_dict: dict[str, Any],
    training_episodes: list[str],
    current_set: list[str],
) -> tuple[dict[str, float], float]:
    """Independently recount transitions from attack_sequences.json without src/c4."""
    counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for ep_id in training_episodes:
        items = episodes_dict[ep_id].get("collapsed", [])
        for i in range(len(items) - 1):
            cur_s = items[i].get("techniques", [])
            nxt_s = items[i + 1].get("techniques", [])
            m = len(cur_s)
            n = len(nxt_s)
            if m > 0 and n > 0:
                w = 1.0 / (m * n)
                for a in cur_s:
                    for b in nxt_s:
                        counts[a][b] += w

    # Compute P(b|current_set)
    members_used = [a for a in current_set if a in counts and len(counts[a]) > 0]
    if not members_used:
        return {}, 0.0

    combined_probs: dict[str, float] = defaultdict(float)
    w_mem = 1.0 / len(members_used)
    for a in members_used:
        tot_a = sum(counts[a].values())
        if tot_a > 0:
            for b, c in counts[a].items():
                combined_probs[b] += w_mem * (c / tot_a)

    return combined_probs, float(sum(sum(counts[a].values()) for a in counts))


def recount_tactic_transitions(
    episodes_dict: dict[str, Any],
    training_episodes: list[str],
    current_set: list[str],
) -> tuple[dict[str, float], float]:
    """Independently recount tactic transitions from attack_sequences.json."""
    counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for ep_id in training_episodes:
        raw_items = episodes_dict[ep_id].get("raw", [])
        col_tacs: list[list[str]] = []
        for ev in raw_items:
            t_list = ev.get("official_tactics") or ev.get("tactics", [])
            s_tacs = sorted(list(set(t.lower().replace(" ", "-").replace("_", "-") for t in t_list if t)))
            if not col_tacs or col_tacs[-1] != s_tacs:
                col_tacs.append(s_tacs)

        for i in range(len(col_tacs) - 1):
            c_t = col_tacs[i]
            n_t = col_tacs[i + 1]
            m = len(c_t)
            n = len(n_t)
            if m > 0 and n > 0:
                w = 1.0 / (m * n)
                for a in c_t:
                    for b in n_t:
                        counts[a][b] += w

    members_used = [a for a in current_set if a in counts and len(counts[a]) > 0]
    if not members_used:
        return {}, 0.0

    combined_probs = defaultdict(float)
    w_mem = 1.0 / len(members_used)
    for a in members_used:
        tot_a = sum(counts[a].values())
        if tot_a > 0:
            for b, c in counts[a].items():
                combined_probs[b] += w_mem * (c / tot_a)

    return combined_probs, float(sum(sum(counts[a].values()) for a in counts))


def verify_prediction_records() -> bool:
    print("=" * 80)
    print("INDEPENDENT PREDICTION RECORDS VERIFICATION (G-P5-1, G-P5-2, G-P5-5)")
    print("=" * 80)

    # 1. Load schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    validator = jsonschema.Draft7Validator(schema_data)
    print(f"[Step 1] Loaded JSON schema ({SCHEMA_PATH.name}) [PASS]")

    # 2. Load records
    records = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if line.strip():
                records.append(json.loads(line))
    assert len(records) == 171, f"Expected 171 records in JSONL, got {len(records)}"
    print(f"[Step 2] Read {len(records)} prediction records from JSONL [PASS]")

    # 3. Gate G-P5-5: Schema validation for 100% of records
    for idx, r in enumerate(records):
        try:
            validator.validate(r)
        except jsonschema.ValidationError as exc:
            raise AssertionError(f"Record {idx} ({r['input']['sample_id']}) failed schema validation: {exc}")
    print(f"[Step 3] Gate G-P5-5: 100% (171/171) records validate against schema [PASS]")

    # 4. Canonical Hash Integrity
    for idx, r in enumerate(records):
        rec_copy = dict(r)
        stored_hash = rec_copy.pop("record_sha256")
        comp_hash = sha256_canonical(rec_copy)
        assert stored_hash == comp_hash, f"Record {idx} hash mismatch: {stored_hash} != {comp_hash}"
    print(f"[Step 4] Canonical SHA-256 record hashes verified for all 171 records [PASS]")

    # 5. Gate G-P5-1: Candidate lists match evaluation_7ep_predictions.csv
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    csv_map = {(r["slice"], r["sample_id"]): r for r in csv_rows}

    for idx, r in enumerate(records):
        sid = r["input"]["sample_id"]
        sl = "collapsed_full" if r["prediction_type"] == "technique" else "tactic_collapsed"
        csv_r = csv_map[(sl, sid)]
        exp_cands = json.loads(csv_r["markov_fallback_top3"])

        p_obj = r["technique_prediction"] if r["prediction_type"] == "technique" else r["tactic_prediction"]
        act_cands = [(c["candidate_id"], c["score"]) for c in p_obj["ranked_candidates"]]

        assert len(act_cands) == len(exp_cands), f"Record {sid}: count mismatch ({len(act_cands)} vs {len(exp_cands)})"
        for (a_id, a_sc), (e_id, e_sc) in zip(act_cands, exp_cands):
            assert a_id == e_id, f"Record {sid}: candidate ID mismatch ({a_id} != {e_id})"
            assert abs(a_sc - e_sc) < 1e-9, f"Record {sid}: score mismatch ({a_sc} != {e_sc})"

    print(f"[Step 5] Gate G-P5-1: All 171 records match evaluation_7ep_predictions.csv exactly [PASS]")

    # 6. Gate G-P5-2: Independent transition recount without src/c4
    with open(SEQS_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    episodes_dict = seqs_data["episodes"]

    for idx, r in enumerate(records):
        sid = r["input"]["sample_id"]
        lvl = r["prediction_type"]
        train_eps = r["model"]["training_episodes"]
        p_obj = r["technique_prediction"] if lvl == "technique" else r["tactic_prediction"]

        if p_obj["status"] == "ok":
            cur_set = r["input"]["current_technique_set"] if lvl == "technique" else r["input"]["current_tactic_set"]
            if lvl == "technique":
                recounted_probs, _ = recount_technique_transitions(episodes_dict, train_eps, cur_set)
            else:
                recounted_probs, _ = recount_tactic_transitions(episodes_dict, train_eps, cur_set)

            for c in p_obj["ranked_candidates"]:
                cid = c["candidate_id"]
                prob = c["score"]
                exp_prob = recounted_probs.get(cid, 0.0)
                assert abs(prob - exp_prob) < 1e-9, f"Record {sid} ({cid}): recounted {exp_prob} != {prob}"

    print(f"[Step 6] Gate G-P5-2: Independent transition recount matched all probabilities within 1e-9 [PASS]")

    # 7. Examples Markdown verification
    md_text = EXAMPLES_MD_PATH.read_text(encoding="utf-8")
    assert "# Explainable Prediction Record Worked Examples (7 Episodes)" in md_text
    assert "## Exemplar: 1. First Hit" in md_text
    assert "## Exemplar: 2. First Miss" in md_text
    assert "## Exemplar: 3. First Fallback" in md_text
    assert "## Exemplar: 4. First Unseen State" in md_text
    assert "## Exemplar: 5. First Tied Boundary" in md_text
    print(f"[Step 7] Worked examples report structure verified [PASS]")

    print("\n" + "=" * 80)
    print("ALL PREDICTION RECORD VERIFICATIONS PASSED SUCCESSFULLY (Exit 0)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        ok = verify_prediction_records()
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print(f"VERIFICATION FAILURE: {exc}", file=sys.stderr)
        sys.exit(1)
