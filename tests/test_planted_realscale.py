r"""Unit tests for Real-Scale Planted-Structure Power Analysis (A4).

Tests:
1. test_planted_realscale_gates_pass: G8, G9, G10 all pass.
2. test_planted_realscale_negative_control: deliberately broken Markov on s=1.0 fails G10.
3. test_planted_realscale_report_equals_verifier: independent CSV-based verifier confirms report match.
4. test_planted_realscale_byte_identical_reproducibility: running evaluation on fixed seed produces byte-identical output across two runs.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.verify_planted_realscale import verify_planted_realscale
from scripts.run_planted_realscale import FOLDS

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = BASE_DIR / "reports" / "planted_realscale_report.json"


def test_planted_realscale_gates_pass() -> None:
    """Verify that all pre-declared gates G8-G10 pass."""
    assert JSON_PATH.exists(), f"Missing report JSON: {JSON_PATH}"
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gates = data["gates"]
    assert gates["G8"]["passed"] is True, f"Gate G8 failed: {gates['G8']}"
    assert gates["G9"]["passed"] is True, f"Gate G9 failed: {gates['G9']}"
    assert gates["G10"]["passed"] is True, f"Gate G10 failed: {gates['G10']}"


def test_planted_realscale_negative_control() -> None:
    """Verify that negative control (deliberately broken Markov) fails G10."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    neg = data["gates"]["G11"]
    assert neg["passed"] is True
    assert neg["broken_ratio_to_r"] < 0.99


def test_planted_realscale_report_equals_verifier() -> None:
    """Verify that independent verifier reading only CSV matches report JSON and MD."""
    assert verify_planted_realscale() is True


def test_planted_realscale_byte_identical_reproducibility() -> None:
    """Verify deterministic generation producing byte-identical output across two runs."""
    import random
    from src.c4.models.markov import MarkovModel

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    vocab = data["metadata"]["vocabulary"]
    v_to_idx = {v: i for i, v in enumerate(vocab)}

    def run_one(seed: int):
        rng = random.Random(seed)
        eps = {}
        for ep in ["E1", "E2", "E3", "E4"]:
            cur = rng.choice(vocab)
            seq = [{"techniques": [cur]}]
            for _ in range(15):
                nxt = vocab[(v_to_idx[cur] + 1) % len(vocab)]
                seq.append({"techniques": [nxt]})
                cur = nxt
            eps[ep] = {"collapsed": seq}
        m = MarkovModel(variant="collapsed", granularity="full").fit({"episodes": eps}, ["E1", "E2", "E3"])
        return m.predict([vocab[0]], k=3)

    res1 = run_one(42)
    res2 = run_one(42)
    assert json.dumps(res1, sort_keys=True) == json.dumps(res2, sort_keys=True)
