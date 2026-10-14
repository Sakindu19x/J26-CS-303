r"""Unit tests for Permutation Test on Real Episodes (Part B).

Tests:
1. test_observed_values_reproduce_reports: observed hits match production evaluation reports.
2. test_permutation_report_equals_verifier: independent CSV-only verifier confirms report matches CSV.
3. test_shuffling_changes_sequences: asserts that shuffling within an episode changes the event sequence.
4. test_permutation_byte_identical_reproducibility: asserts deterministic reproducibility given fixed seed.
"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path
import pytest

from src.c4.attack_sequence import collapse_sequence
from src.c4.evaluation import evaluate_loeo_slice
from src.c4.tactic_evaluation import evaluate_tactic_slice
from scripts.verify_permutation_test import verify_permutation_test

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = BASE_DIR / "reports" / "archive" / "permutation_test_report_v1_counts_superseded.json"
ATTACK_SEQS_PATH = BASE_DIR / "data" / "processed" / "attack_sequences.json"


def test_observed_values_reproduce_reports() -> None:
    """Verify that observed baseline hits reproduce existing production reports exactly."""
    tech_res, _ = evaluate_loeo_slice(variant="collapsed", granularity="full", save_fold_models=False)
    m_h1 = tech_res["headline"]["markov"]["hit1"]
    m_h3 = tech_res["headline"]["markov"]["hit3"]
    f_h1 = tech_res["headline"]["frequency"]["hit1"]
    f_h3 = tech_res["headline"]["frequency"]["hit3"]

    assert (m_h1, m_h3) == (1, 2), f"Technique Markov expected (1, 2), got ({m_h1}, {m_h3})"
    assert (f_h1, f_h3) == (4, 8), f"Technique Frequency expected (4, 8), got ({f_h1}, {f_h3})"

    tac_res, _ = evaluate_tactic_slice(variant="tactic_collapsed", use_dataset_tactics=False)
    tm_h1 = tac_res["headline"]["markov"]["hit1"]
    tm_h3 = tac_res["headline"]["markov"]["hit3"]
    tf_h1 = tac_res["headline"]["frequency"]["hit1"]
    tf_h3 = tac_res["headline"]["frequency"]["hit3"]

    assert (tm_h1, tm_h3) == (11, 28), f"Tactic Markov expected (11, 28), got ({tm_h1}, {tm_h3})"
    assert (tf_h1, tf_h3) == (9, 33), f"Tactic Frequency expected (9, 33), got ({tf_h1}, {tf_h3})"


def test_permutation_report_equals_verifier() -> None:
    """Verify that independent verifier reading only CSV matches report JSON and MD."""
    assert verify_permutation_test() is True


def test_shuffling_changes_sequences() -> None:
    """Verify that shuffling raw labeled events changes the collapsed sequence order."""
    with open(ATTACK_SEQS_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)

    e1_raw = seqs_data["episodes"]["E1"]["raw"]
    orig_order = [ev["event_id"] for ev in e1_raw]

    rng = random.Random(42)
    shuffled_raw = copy.deepcopy(e1_raw)
    rng.shuffle(shuffled_raw)
    shuffled_order = [ev["event_id"] for ev in shuffled_raw]

    assert shuffled_order != orig_order, "Shuffling should change event order"

    orig_col = seqs_data["episodes"]["E1"]["collapsed"]
    orig_col_techs = [item["techniques"] for item in orig_col]

    shuffled_col = collapse_sequence(shuffled_raw)
    shuffled_col_techs = [item["techniques"] for item in shuffled_col]

    assert shuffled_col_techs != orig_col_techs, "Collapsed sequence of techniques must differ from original"


def test_permutation_byte_identical_reproducibility() -> None:
    """Verify that running a permutation with the same seed produces identical results."""
    with open(ATTACK_SEQS_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)

    def run_one_perm(seed: int):
        rng = random.Random(seed)
        perm = {}
        for ep_id in ["E1", "E2", "E3", "E4"]:
            raw_copy = copy.deepcopy(seqs_data["episodes"][ep_id]["raw"])
            rng.shuffle(raw_copy)
            col_copy = collapse_sequence(raw_copy)
            perm[ep_id] = {"raw": raw_copy, "collapsed": col_copy}
        return perm

    p1 = run_one_perm(123)
    p2 = run_one_perm(123)

    assert json.dumps(p1, sort_keys=True) == json.dumps(p2, sort_keys=True)


def test_permutation_numeric_mutation_zero_undetected() -> None:
    """Verify that mechanical numeric mutation sweep detects 100% of tested tokens (0 undetected)."""
    from scripts.mutation_sweep import run_mutation_sweep

    results = run_mutation_sweep()
    perm_res = results["permutation_test"]
    assert perm_res["undetected"] == 0, f"Undetected tokens: {perm_res['undetected_items']}"
    assert perm_res["detected"] == perm_res["tested_total"]
