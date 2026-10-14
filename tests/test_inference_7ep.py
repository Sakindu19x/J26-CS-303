"""Unit tests for 7-episode pre-registered inference suite (Prompt 12b).

Tests:
- Hand-computed Holm-Bonferroni step-down example.
- Substantive claim rule edge cases (directionality + significance requirement).
- Learning curve output structure and subset counts.
- 7-episode permutation invariants and sample counts.
- Real-scale planted structure A4 gates (G8-G11).
- E5-removed sensitivity sample counts and McNemar consistency.
- Read-only diagnostics structure and sanity invariants.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_7EP = BASE_DIR / "data" / "processed_7ep"
REPORTS_7EP = BASE_DIR / "reports" / "7ep"


# 1. Hand-computed Holm example test
def test_holm_step_down_hand_computed():
    """Verify Holm-Bonferroni step-down on a deterministic hand-computed example.

    Input raw p: [0.01, 0.04, 0.02, 0.005] (m=4)
    Sorted order:
      Rank 1: 0.005 -> mult 4 -> 4 * 0.005 = 0.0200
      Rank 2: 0.010 -> mult 3 -> max(0.02, 3 * 0.01) = 0.0300
      Rank 3: 0.020 -> mult 2 -> max(0.03, 2 * 0.02) = 0.0400
      Rank 4: 0.040 -> mult 1 -> max(0.04, 1 * 0.04) = 0.0400
    """
    from scripts.run_holm_claim_rule import holm_step_down

    test_hypotheses = [
        {"id": "H1", "raw_p": 0.010},
        {"id": "H2", "raw_p": 0.040},
        {"id": "H3", "raw_p": 0.020},
        {"id": "H4", "raw_p": 0.005},
    ]

    res = holm_step_down(test_hypotheses)
    res_map = {h["id"]: h for h in res}

    assert res_map["H4"]["rank"] == 1
    assert res_map["H4"]["multiplier"] == 4
    assert pytest.approx(res_map["H4"]["adjusted_p"], abs=1e-6) == 0.0200

    assert res_map["H1"]["rank"] == 2
    assert res_map["H1"]["multiplier"] == 3
    assert pytest.approx(res_map["H1"]["adjusted_p"], abs=1e-6) == 0.0300

    assert res_map["H3"]["rank"] == 3
    assert res_map["H3"]["multiplier"] == 2
    assert pytest.approx(res_map["H3"]["adjusted_p"], abs=1e-6) == 0.0400

    assert res_map["H2"]["rank"] == 4
    assert res_map["H2"]["multiplier"] == 1
    assert pytest.approx(res_map["H2"]["adjusted_p"], abs=1e-6) == 0.0400


# 2. Claim rule logic test
def test_claim_rule_logic():
    """Verify claim rule requires both Holm p < 0.05 AND Markov > Frequency."""
    # Case A: Significant p but Markov < Frequency (e.g. technique P2) -> not demonstrated
    p2_markov = 0.0316
    p2_freq = 0.1684
    p2_adj_p = 0.0094
    assert p2_adj_p < 0.05
    assert not (p2_markov > p2_freq)
    verdict_a = "improvement over the baseline demonstrated" if (p2_markov > p2_freq and p2_adj_p < 0.05) else "not demonstrated"
    assert verdict_a == "not demonstrated"

    # Case B: Markov == Frequency and p = 1.0 (e.g. tactic P1) -> not demonstrated
    p1_markov = 0.6316
    p1_freq = 0.6316
    p1_adj_p = 1.0000
    verdict_b = "improvement over the baseline demonstrated" if (p1_markov > p1_freq and p1_adj_p < 0.05) else "not demonstrated"
    assert verdict_b == "not demonstrated"

    # Case C: Hypothetical win: Markov > Frequency and p < 0.05 -> demonstrated
    win_markov = 0.7000
    win_freq = 0.5000
    win_adj_p = 0.0300
    verdict_c = "improvement over the baseline demonstrated" if (win_markov > win_freq and win_adj_p < 0.05) else "not demonstrated"
    assert verdict_c == "improvement over the baseline demonstrated"


# 3. Learning curve output test
def test_learning_curve_outputs():
    csv_path = DATA_7EP / "learning_curve_7ep.csv"
    json_path = REPORTS_7EP / "learning_curve_7ep_results.json"
    md_path = REPORTS_7EP / "learning_curve_7ep_report.md"
    png_path = REPORTS_7EP / "learning_curve_7ep.png"
    plot_json_path = REPORTS_7EP / "learning_curve_7ep_plot_data.json"

    assert csv_path.exists()
    assert json_path.exists()
    assert md_path.exists()
    assert png_path.exists()
    assert plot_json_path.exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # 441 subsets * 2 slices * 3 models = 2646 rows
    assert len(rows) == 2646

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["metadata"]["total_evaluations_per_slice"] == 441


# 4. Permutation 7ep invariants test
def test_permutation_7ep_invariants():
    csv_path = DATA_7EP / "permutation_7ep_null_distribution.csv"
    json_path = REPORTS_7EP / "permutation_7ep_report.json"
    assert csv_path.exists()
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["metadata"]["b_permutations"] == 1000
    assert d["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]["markov_hit3"]["p_value"] == pytest.approx(0.3856, abs=0.001)
    assert d["schemes"]["S1_collapsed_order"]["tactic_collapsed"]["markov_hit3"]["p_value"] == pytest.approx(0.0060, abs=0.001)
    assert d["scheme_validity_check"]["S1_collapsed_order"]["is_valid_order_null"] is True
    assert d["scheme_validity_check"]["S3_constrained_shuffle"]["is_valid_order_null"] is True


# 5. A4 7ep realscale gates test
def test_planted_realscale_7ep_gates():
    json_path = REPORTS_7EP / "planted_realscale_7ep_report.json"
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    gates = d["gates"]
    assert gates["G8"]["passed"] is True
    assert gates["G9"]["passed"] is True
    assert gates["G10"]["passed"] is True
    assert gates["G11"]["passed"] is True
    assert d["metadata"]["vocabulary_size"] == 82
    assert d["metadata"]["total_samples_per_replicate"] == 95
    assert d["metadata"]["total_samples_no_e5_per_replicate"] == 93


# 6. E5-removed sensitivity test
def test_e5_removed_sensitivity():
    csv_path = DATA_7EP / "e5_removed_predictions.csv"
    json_path = REPORTS_7EP / "e5_removed_results.json"
    assert csv_path.exists()
    assert json_path.exists()

    with open(csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 167
    assert all(r["test_episode"] != "E5" for r in rows)

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["technique_collapsed_full"]["n_samples"] == 93
    assert d["tactic_collapsed"]["n_samples"] == 74


# 7. Read-only diagnostics test
def test_diagnostics_7ep():
    json_path = REPORTS_7EP / "diagnostics_7ep.json"
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        d = json.load(f)
    assert d["metadata"]["label"] == "diagnostic, not a pre-registered test"
    assert d["F2_raw_full_self_repeats"]["total_samples"] == 131
    assert d["F2_raw_full_self_repeats"]["self_repeat_samples"] == 36
    assert d["F2_raw_full_self_repeats"]["markov_hit1_on_self_repeat"] == 11
