"""Tests for secondary next-tactic LOEO evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from c4.tactic_evaluation import (
    ENTERPRISE_TACTICS_14,
    FRAMING_TEXT,
    TacticFrequencyBaseline,
    TacticMarkovModel,
    evaluate_derived_tactics,
    random_guess_expected_hit,
    run_full_tactic_evaluation,
)

BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"


def _hash_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_framing_text_verbatim() -> None:
    """Verify required framing sentence appears verbatim at the top of the report."""
    md_path = REPORTS_DIR / "tactic_evaluation_report.md"
    assert md_path.exists(), "tactic_evaluation_report.md must exist"
    first_line = md_path.read_text(encoding="utf-8").splitlines()[0].strip()
    assert first_line == FRAMING_TEXT


def test_tactic_sample_counts() -> None:
    """Verify exact sample counts per slice and episode."""
    json_path = REPORTS_DIR / "tactic_evaluation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_s = data["slices"]["tactic_raw"]
    col_s = data["slices"]["tactic_collapsed"]
    col_ds = data["slices"]["tactic_collapsed_dataset_tactics"]

    # Raw: N=95 (26, 20, 28, 21)
    assert raw_s["n_samples"] == 95
    assert raw_s["per_fold"]["fold_1"]["n_samples"] == 26
    assert raw_s["per_fold"]["fold_2"]["n_samples"] == 20
    assert raw_s["per_fold"]["fold_3"]["n_samples"] == 28
    assert raw_s["per_fold"]["fold_4"]["n_samples"] == 21

    # Collapsed: N=53 (13, 15, 15, 10)
    assert col_s["n_samples"] == 53
    assert col_s["per_fold"]["fold_1"]["n_samples"] == 13
    assert col_s["per_fold"]["fold_2"]["n_samples"] == 15
    assert col_s["per_fold"]["fold_3"]["n_samples"] == 15
    assert col_s["per_fold"]["fold_4"]["n_samples"] == 10

    # Dataset tactics sensitivity: N=52
    assert col_ds["n_samples"] == 52


def test_tactic_models_synthetic_hand_computed() -> None:
    """Hand-computed synthetic test for TacticMarkovModel and TacticFrequencyBaseline."""
    ep_seqs = {
        "EP1": [
            {"event_id": "1", "tactics": ["initial-access"]},
            {"event_id": "2", "tactics": ["execution", "persistence"]},
            {"event_id": "3", "tactics": ["defense-evasion"]},
        ]
    }
    m = TacticMarkovModel().fit(ep_seqs, ["EP1"])
    f = TacticFrequencyBaseline().fit(ep_seqs, ["EP1"])

    # From initial-access: goes to execution (0.5) and persistence (0.5)
    pred_ia = m.predict(["initial-access"], k=3)
    assert pred_ia["status"] == "ok"
    assert len(pred_ia["candidates"]) == 2
    # Tie broken alphabetically: execution before persistence
    assert pred_ia["candidates"][0][0] == "execution"
    assert pred_ia["candidates"][1][0] == "persistence"
    assert pytest.approx(pred_ia["candidates"][0][1]) == 0.5

    # Abstain on unseen
    pred_unseen = m.predict(["discovery"])
    assert pred_unseen["status"] == "insufficient_evidence"

    # Frequency baseline
    f_pred = f.predict(k=3)
    assert f_pred["status"] == "ok"
    # Transition 1 -> 2: weight 0.5 on execution, 0.5 on persistence
    # Transition 2 -> 3: weight 1.0 on defense-evasion
    # Total weight = 2.0. P(defense-evasion) = 0.5, P(execution) = 0.25, P(persistence) = 0.25
    assert f_pred["candidates"][0][0] == "defense-evasion"
    assert pytest.approx(f_pred["candidates"][0][1]) == 0.5


def test_random_guess_hypergeometric() -> None:
    """Verify random-guess expected hit formula against combinatorial definition."""
    # |T| = 1: P(hit) = 1/14
    assert pytest.approx(random_guess_expected_hit({"initial-access"}, 1)) == 1.0 / 14.0
    # |T| = 1, k=3: P(hit) = 3/14
    assert pytest.approx(random_guess_expected_hit({"initial-access"}, 3)) == 3.0 / 14.0
    # |T| = 2, k=1: P(hit) = 2/14
    assert pytest.approx(random_guess_expected_hit({"initial-access", "execution"}, 1)) == 2.0 / 14.0


def test_tactic_evaluation_outputs_byte_identical_across_two_runs() -> None:
    """Verify deterministic idempotency across two evaluation runs."""
    h_csv_1 = _hash_file(PROCESSED_DIR / "tactic_evaluation_predictions.csv")
    h_json_1 = _hash_file(REPORTS_DIR / "tactic_evaluation_results.json")
    h_md_1 = _hash_file(REPORTS_DIR / "tactic_evaluation_report.md")

    # Run again
    run_full_tactic_evaluation()

    h_csv_2 = _hash_file(PROCESSED_DIR / "tactic_evaluation_predictions.csv")
    h_json_2 = _hash_file(REPORTS_DIR / "tactic_evaluation_results.json")
    h_md_2 = _hash_file(REPORTS_DIR / "tactic_evaluation_report.md")

    assert h_csv_1 == h_csv_2, "tactic_evaluation_predictions.csv is not byte-identical!"
    assert h_json_1 == h_json_2, "tactic_evaluation_results.json is not byte-identical!"
    assert h_md_1 == h_md_2, "tactic_evaluation_report.md is not byte-identical!"
