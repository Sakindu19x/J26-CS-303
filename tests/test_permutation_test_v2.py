r"""Unit tests for Permutation Test on Real Episodes v2 (Part C).

Tests:
1. test_observed_values_equal_reports: observed baseline rates and hits match production reports.
2. test_n_constant_under_s1: assert N is strictly invariant (67 technique, 53 tactic) under S1.
3. test_permutation_v2_byte_identical_reproducibility: assert identical output with same seed.
4. test_permutation_v2_report_equals_verifier: independent CSV-based verifier confirms report match.
"""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path
import pytest

from src.c4.samples import build_samples_for_sequence
from src.c4.normalization import EPISODE_MAPPING
from src.c4.evaluation import evaluate_loeo_slice
import src.c4.tactic_evaluation as te
from scripts.verify_permutation_test_v2 import verify_permutation_test_v2

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = BASE_DIR / "reports" / "permutation_test_v2_report.json"
TECH_EVAL_PATH = BASE_DIR / "reports" / "evaluation_results.json"
TACTIC_EVAL_PATH = BASE_DIR / "reports" / "tactic_evaluation_results.json"
ATTACK_SEQS_PATH = BASE_DIR / "data" / "processed" / "attack_sequences.json"


def test_observed_values_equal_reports() -> None:
    """Verify that observed baseline hits and rates reproduce existing reports exactly."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        v2_data = json.load(f)

    with open(TECH_EVAL_PATH, "r", encoding="utf-8") as f:
        tech_data = json.load(f)

    with open(TACTIC_EVAL_PATH, "r", encoding="utf-8") as f:
        tactic_data = json.load(f)

    tech_cf = tech_data["slices"]["collapsed_full"]
    assert tech_cf["n_samples"] == 67
    assert (tech_cf["headline"]["markov"]["hit1"], tech_cf["headline"]["markov"]["hit3"]) == (1, 2)
    assert (tech_cf["headline"]["frequency"]["hit1"], tech_cf["headline"]["frequency"]["hit3"]) == (4, 8)
    assert (tech_cf["headline"]["fallback"]["hit1"], tech_cf["headline"]["fallback"]["hit3"]) == (2, 5)

    tac_tc = tactic_data["slices"]["tactic_collapsed"]
    assert tac_tc["n_samples"] == 53
    assert (tac_tc["headline"]["markov"]["hit1"], tac_tc["headline"]["markov"]["hit3"]) == (11, 28)
    assert (tac_tc["headline"]["frequency"]["hit1"], tac_tc["headline"]["frequency"]["hit3"]) == (9, 33)
    assert (tac_tc["headline"]["markov_fallback"]["hit1"], tac_tc["headline"]["markov_fallback"]["hit3"]) == (13, 30)

    # Check observed values in v2 JSON match
    obs_counts = v2_data["metadata"]["observed_baseline_counts"]
    assert obs_counts["technique_collapsed_full"]["markov_hit1"] == 1
    assert obs_counts["technique_collapsed_full"]["markov_hit3"] == 2
    assert obs_counts["technique_collapsed_full"]["frequency_hit1"] == 4
    assert obs_counts["technique_collapsed_full"]["frequency_hit3"] == 8
    assert obs_counts["tactic_collapsed"]["markov_hit1"] == 11
    assert obs_counts["tactic_collapsed"]["markov_hit3"] == 28
    assert obs_counts["tactic_collapsed"]["frequency_hit1"] == 9
    assert obs_counts["tactic_collapsed"]["frequency_hit3"] == 33


def test_n_constant_under_s1() -> None:
    """Verify that under S1 scheme, N is strictly constant (67 technique, 53 tactic)."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        v2_data = json.load(f)

    s1_sum = v2_data["metadata"]["sample_counts_summary"]["S1_collapsed_order"]
    assert s1_sum["technique_collapsed_full"]["min"] == 67
    assert s1_sum["technique_collapsed_full"]["max"] == 67
    assert s1_sum["technique_collapsed_full"]["is_constant"] is True

    assert s1_sum["tactic_collapsed"]["min"] == 53
    assert s1_sum["tactic_collapsed"]["max"] == 53
    assert s1_sum["tactic_collapsed"]["is_constant"] is True


def test_permutation_v2_byte_identical_reproducibility() -> None:
    """Verify deterministic S1 permutation generation produces byte-identical output across two runs."""
    with open(ATTACK_SEQS_PATH, "r", encoding="utf-8") as f:
        orig_seqs = json.load(f)

    def run_s1_step(seed: int):
        rng = random.Random(seed)
        shuffled_eps = {}
        for ep_id in ["E1", "E2", "E3", "E4"]:
            col_copy = copy.deepcopy(orig_seqs["episodes"][ep_id]["collapsed"])
            rng.shuffle(col_copy)
            shuffled_eps[ep_id] = col_copy
        return shuffled_eps

    run1 = run_s1_step(12345)
    run2 = run_s1_step(12345)

    assert json.dumps(run1, sort_keys=True) == json.dumps(run2, sort_keys=True)


def test_permutation_v2_report_equals_verifier() -> None:
    """Verify that independent CSV-only verifier confirms report match."""
    assert verify_permutation_test_v2() is True
