r"""Unit tests for Exploratory Tactic-Conditioned Technique Prediction (Amendment 7)."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

from scripts.verify.verify_exploratory_tactic_conditioned import (
    verify_exploratory_tactic_conditioned,
    wilson_interval,
    exact_mcnemar,
)

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "exploratory_tactic_conditioned_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "exploratory_tactic_conditioned_results.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "exploratory_tactic_conditioned_report.md"


def test_exploratory_predictions_count() -> None:
    assert CSV_PATH.is_file()
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 95
    eps = set(r["test_episode"] for r in rows)
    assert eps == {"E1", "E2", "E3", "E4", "E5", "E6", "E7"}


def test_exploratory_hit_derivation() -> None:
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        cands = json.loads(r["predicted_candidates_top3"])
        tgt = set(json.loads(r["target_set"]))
        exp_h1 = 1 if (cands and cands[0] in tgt) else 0
        exp_h3 = 1 if any(c in tgt for c in cands[:3]) else 0
        assert int(r["variant_hit1"]) == exp_h1
        assert int(r["variant_hit3"]) == exp_h3


def test_exploratory_mcnemar_and_wilson() -> None:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    r7 = data["runs"]["7ep"]
    assert r7["models"]["variant"]["hit1"] == 5
    assert r7["models"]["variant"]["hit3"] == 8
    assert r7["models"]["frequency"]["hit1"] == 7
    assert r7["models"]["frequency"]["hit3"] == 16
    assert r7["models"]["markov"]["hit1"] == 3
    assert r7["models"]["markov"]["hit3"] == 3

    # McNemar p-value check
    assert r7["mcnemar_vs_frequency"]["top1"]["b"] == 5
    assert r7["mcnemar_vs_frequency"]["top1"]["c"] == 7
    assert abs(r7["mcnemar_vs_frequency"]["top1"]["p_value"] - exact_mcnemar(5, 7)) < 1e-9


def test_exploratory_verifier_passes() -> None:
    assert verify_exploratory_tactic_conditioned() is True


def test_exploratory_disclaimer_and_verdict() -> None:
    md_text = MD_PATH.read_text(encoding="utf-8")
    assert "EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT" in md_text
    assert 'The pre-registered primary evaluation verdict ("improvement over baseline not demonstrated") is finalized and cannot be modified or overturned by this exploratory variant.' in md_text

