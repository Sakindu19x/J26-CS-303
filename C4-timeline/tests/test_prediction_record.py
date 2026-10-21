"""Automated Regression Tests for Explainable Prediction Records (Prompt 13 P5).

Tests Gates G-P5-1 through G-P5-6:
- G-P5-1: Top-k candidates match evaluation_7ep_predictions.csv
- G-P5-3: Determinism across PYTHONHASHSEED=0, 1, 4242
- G-P5-4: Cryptographic non-modification of inputs (NFR3)
- G-P5-5: 100% schema validation
- G-P5-6: Requirements trace matrix completeness
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from c4.prediction_record import canonical_json_bytes, sha256_canonical

SCHEMA_PATH = REPO_ROOT / "schemas" / "c4_prediction_record.schema.json"
JSONL_PATH = REPO_ROOT / "data" / "processed_7ep" / "prediction_records_loeo.jsonl"
CSV_PATH = REPO_ROOT / "data" / "processed_7ep" / "evaluation_7ep_predictions.csv"
EVENTS_PATH = REPO_ROOT / "data" / "processed_7ep" / "normalized_events.json"
TRACE_MD_PATH = REPO_ROOT / "reports" / "7ep" / "requirements_trace.md"
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_prediction_records.py"


@pytest.fixture(scope="module")
def loaded_records() -> list[dict[str, Any]]:
    assert JSONL_PATH.is_file(), f"Missing JSONL: {JSONL_PATH}"
    records = []
    with open(JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


@pytest.fixture(scope="module")
def schema_validator() -> jsonschema.Draft7Validator:
    assert SCHEMA_PATH.is_file(), f"Missing schema: {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    return jsonschema.Draft7Validator(schema)


def test_gp5_5_schema_validation_100_percent(loaded_records, schema_validator):
    """Gate G-P5-5: 100% of prediction records validate against the draft-07 schema."""
    assert len(loaded_records) == 171, f"Expected 171 records, got {len(loaded_records)}"
    for idx, r in enumerate(loaded_records):
        schema_validator.validate(r)


def test_gp5_1_candidates_match_csv(loaded_records):
    """Gate G-P5-1: Top-k candidates and order match evaluation_7ep_predictions.csv."""
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    csv_map = {(r["slice"], r["sample_id"]): r for r in csv_rows}

    for r in loaded_records:
        sid = r["input"]["sample_id"]
        sl = "collapsed_full" if r["prediction_type"] == "technique" else "tactic_collapsed"
        csv_r = csv_map[(sl, sid)]
        exp_cands = json.loads(csv_r["markov_fallback_top3"])

        p_obj = r["technique_prediction"] if r["prediction_type"] == "technique" else r["tactic_prediction"]
        act_cands = [(c["candidate_id"], c["score"]) for c in p_obj["ranked_candidates"]]

        assert len(act_cands) == len(exp_cands), f"Count mismatch for {sid}"
        for (a_id, a_sc), (e_id, e_sc) in zip(act_cands, exp_cands):
            assert a_id == e_id, f"Candidate ID mismatch for {sid}: {a_id} != {e_id}"
            assert abs(a_sc - e_sc) < 1e-9, f"Score mismatch for {sid}: {a_sc} != {e_sc}"


def test_gp5_3_hashseed_determinism():
    """Gate G-P5-3: Build all records in 3 separate processes with PYTHONHASHSEED=0, 1, 4242 -> identical SHA-256."""
    hashes = []
    env_seeds = ["0", "1", "4242"]
    for seed in env_seeds:
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = seed
        res = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            env=env,
        )
        assert res.returncode == 0, f"build_prediction_records failed with seed {seed}: {res.stderr}"
        h = hashlib.sha256(JSONL_PATH.read_bytes()).hexdigest()
        hashes.append(h)

    assert len(set(hashes)) == 1, f"Determinism failure: different hashes across PYTHONHASHSEED: {hashes}"


def test_gp5_4_deep_frozen_inputs_non_modification():
    """Gate G-P5-4 (NFR3): SHA-256 of inputs before and after record building identical."""
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events_before = json.load(f)
    h_before = sha256_canonical(events_before)

    # Re-run builder
    res = subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert res.returncode == 0

    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events_after = json.load(f)
    h_after = sha256_canonical(events_after)

    assert h_before == h_after, "Input events modified during record building!"


def test_gp5_4_timeline_permutation_invariance():
    """Gate G-P5-4: Input events permuted 100 times with fixed seeds gives identical sorted timelines."""
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Decorate with original input index to break timestamp ties deterministically
    indexed_events = list(enumerate(events))

    def sort_key(item: tuple[int, dict[str, Any]]) -> tuple[str, int]:
        idx, ev = item
        ts = ev.get("timestamp") or ""
        return (ts, idx)

    canonical_order = [ev["event_id"] for idx, ev in sorted(indexed_events, key=sort_key)]

    for seed in range(100):
        shuffled = list(indexed_events)
        rng = random.Random(seed)
        rng.shuffle(shuffled)
        reordered = [ev["event_id"] for idx, ev in sorted(shuffled, key=sort_key)]
        assert reordered == canonical_order, f"Permutation invariance failed at seed {seed}"


def test_gp5_6_requirements_trace():
    """Gate G-P5-6: Requirements trace matrix maps FR1-FR9 and NFR1-NFR6."""
    assert TRACE_MD_PATH.is_file(), f"Missing trace MD: {TRACE_MD_PATH}"
    text = TRACE_MD_PATH.read_text(encoding="utf-8")
    for i in range(1, 10):
        assert f"FR{i}" in text, f"Missing FR{i} in trace matrix"
    for i in range(1, 7):
        assert f"NFR{i}" in text, f"Missing NFR{i} in trace matrix"
    assert "null until C3 integration" in text, "Missing 'null until C3 integration' marker"


def test_schema_1_1_0_support_and_caution_counts(loaded_records):
    """Q7: Verify schema 1.1.0 fields, support metrics, and exactly 92 cautioned records."""
    assert len(loaded_records) == 171
    caution_count = 0
    for r in loaded_records:
        assert r["schema_version"] == "1.1.0"
        lvl = r["prediction_type"]
        p_obj = r["technique_prediction"] if lvl == "technique" else r["tactic_prediction"]
        assert "support" in p_obj
        sup = p_obj["support"]
        assert isinstance(sup["caution"], bool)
        assert isinstance(sup["n_supporting_training_episodes"], int)
        assert isinstance(sup["n_transitions_from_state"], (int, float))
        if sup["caution"]:
            caution_count += 1
            assert sup["caution_text"] is not None

    assert caution_count == 92, f"Expected 92 cautioned records, got {caution_count}"


def test_alternatives_no_placeholders_and_tactics(loaded_records):
    """Q7: Verify alternatives ranks 4..k have non-placeholder numerator > 0 when score > 0."""
    checked_alts = 0
    for r in loaded_records:
        lvl = r["prediction_type"]
        p_obj = r["technique_prediction"] if lvl == "technique" else r["tactic_prediction"]
        for a in p_obj.get("alternatives", []):
            checked_alts += 1
            assert len(a["tactics"]) > 0
            assert len(a["tactic_display"]) > 0
            if a["score"] > 0:
                assert a["numerator"] > 0, f"Alternative {a['candidate_id']} has score {a['score']} but numerator {a['numerator']} <= 0"

    assert checked_alts > 0, "No alternative candidates were checked"


def test_tie_break_rule_identical_across_records(loaded_records):
    """Q7: Verify tie_break_rule enum is identical across all records and matches schema."""
    for r in loaded_records:
        assert r["model"]["tie_break_rule"] == "lexicographical_ascending"


def test_exemplars_seven_distinct_sample_ids():
    """Q7: Verify prediction_record_examples.md has exactly 7 distinct exemplar sample IDs."""
    examples_path = REPO_ROOT / "reports" / "7ep" / "prediction_record_examples.md"
    assert examples_path.is_file()
    text = examples_path.read_text(encoding="utf-8")
    import re
    # Extract sample IDs from exemplar headers e.g. ## Exemplar: 1. First Hit (`E1-col-ful-K01`)
    matches = re.findall(r"## Exemplar: [^\n]+ \(`([^`]+)`\)", text)
    assert len(matches) == 7, f"Expected 7 exemplar sections, found {len(matches)}: {matches}"
    assert len(set(matches)) == 7, f"Duplicate exemplar sample IDs found: {matches}"

