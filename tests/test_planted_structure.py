r"""Unit tests for Planted-Structure Validation Experiment (Part A).

Tests:
1. test_planted_structure_gates_pass: G1-G7 all pass.
2. test_planted_structure_report_equals_verifier: independent CSV-based verifier confirms report match.
3. test_planted_structure_negative_control: deliberately broken Markov on A1 at s=1.0 fails G1.
4. test_planted_structure_byte_identical_reproducibility: running evaluation on fixed seeds produces byte-identical results.
"""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from scripts.verify_planted_structure import verify_planted_structure
from scripts.run_planted_structure import (
    generate_a1_dataset,
    evaluate_dataset_loeo,
)

BASE_DIR = Path(__file__).resolve().parents[1]
JSON_PATH = BASE_DIR / "reports" / "planted_structure_report.json"


def test_planted_structure_gates_pass() -> None:
    """Verify that all pre-declared gates G1-G7 pass."""
    assert JSON_PATH.exists(), f"Missing report JSON: {JSON_PATH}"
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gates = data["gates"]
    assert gates["G1"]["passed"] is True
    assert gates["G2"]["passed"] is True
    assert gates["G3"]["passed"] is True
    assert gates["G4"]["passed"] is True
    assert gates["G5"]["passed"] is True
    assert gates["G6"]["passed"] is True
    assert gates["G7"]["passed"] is True


def test_planted_structure_report_equals_verifier() -> None:
    """Verify that independent verifier reading only CSV matches report JSON and MD."""
    assert verify_planted_structure() is True


def test_planted_structure_negative_control() -> None:
    """Verify that negative control (broken Markov monkeypatched) fails G1."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    neg = data["negative_control"]
    assert neg["g1_failed_as_expected"] is True
    assert neg["broken_markov_top1"] < 0.98


def test_planted_structure_byte_identical_reproducibility() -> None:
    """Verify deterministic generation and LOEO evaluation produces byte-identical output across two runs."""
    eps1 = generate_a1_dataset(seed=42, s=0.5)
    eps2 = generate_a1_dataset(seed=42, s=0.5)

    assert json.dumps(eps1, sort_keys=True) == json.dumps(eps2, sort_keys=True)

    summary1, rows1 = evaluate_dataset_loeo(eps1, "A1", 0.5, replicate_id=0)
    summary2, rows2 = evaluate_dataset_loeo(eps2, "A1", 0.5, replicate_id=0)

    assert json.dumps(summary1, sort_keys=True) == json.dumps(summary2, sort_keys=True)
    assert json.dumps(rows1, sort_keys=True) == json.dumps(rows2, sort_keys=True)


def test_planted_structure_numeric_mutation_zero_undetected() -> None:
    """Verify that mechanical numeric mutation sweep detects 100% of tested tokens (0 undetected)."""
    from scripts.mutation_sweep import run_mutation_sweep

    results = run_mutation_sweep()
    planted_res = results["planted_structure"]
    assert planted_res["undetected"] == 0, f"Undetected tokens: {planted_res['undetected_items']}"
    assert planted_res["detected"] == planted_res["tested_total"]
