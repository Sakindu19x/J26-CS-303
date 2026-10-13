"""Pytest wrappers for mechanical in-memory mutation sweeps across evaluation reports.

1. test_summary_printer_with_fake_undetected:
   Verifies that summary printer computes numbers dynamically and does NOT say 100.00%
   when undetected > 0.
2. test_mutation_sweep_numeric_zero_undetected:
   Asserts 100% detection sensitivity for numeric tokens (0 undetected outside exempt list).
3. test_mutation_sweep_labels_zero_undetected:
   Asserts 100% detection sensitivity for data-bearing labels (0 undetected outside headings).
"""
from __future__ import annotations

import pytest
from scripts.mutation_sweep import (
    format_summary_block,
    run_label_mutation_sweep,
    run_mutation_sweep,
)


def test_summary_printer_with_fake_undetected() -> None:
    """Assert format_summary_block computes percentages dynamically and does not say 100.00% when undetected > 0."""
    fake_results = {
        "tactic": {"detected": 900, "tested_total": 980, "undetected": 80},
        "technique": {"detected": 1400, "tested_total": 1483, "undetected": 83},
    }
    rendered = format_summary_block(fake_results, "TEST SUMMARY")
    assert "100.00%" not in rendered
    assert "900/980" in rendered
    assert "80 undetected" in rendered
    assert "1400/1483" in rendered
    assert "83 undetected" in rendered
    assert "91.84%" in rendered
    assert "94.40%" in rendered


def test_mutation_sweep_numeric_zero_undetected() -> None:
    """Assert 100% detection sensitivity for numeric tokens (0 undetected outside exempt list)."""
    results = run_mutation_sweep()

    tactic_res = results["tactic"]
    assert tactic_res["undetected"] == 0, (
        f"Tactic report had {tactic_res['undetected']} undetected tokens: {tactic_res['undetected_items']}"
    )
    assert tactic_res["detected"] == tactic_res["tested_total"]

    tech_res = results["technique"]
    assert tech_res["undetected"] == 0, (
        f"Technique report had {tech_res['undetected']} undetected tokens: {tech_res['undetected_items']}"
    )
    assert tech_res["detected"] == tech_res["tested_total"]


def test_mutation_sweep_labels_zero_undetected() -> None:
    """Assert 100% detection sensitivity for data-bearing labels (0 undetected outside headings)."""
    results = run_label_mutation_sweep()

    tactic_res = results["tactic"]
    assert tactic_res["undetected"] == 0, (
        f"Tactic report had {tactic_res['undetected']} undetected label tokens: {tactic_res['undetected_items']}"
    )
    assert tactic_res["detected"] == tactic_res["total_tested"]

    tech_res = results["technique"]
    assert tech_res["undetected"] == 0, (
        f"Technique report had {tech_res['undetected']} undetected label tokens: {tech_res['undetected_items']}"
    )
    assert tech_res["detected"] == tech_res["total_tested"]
