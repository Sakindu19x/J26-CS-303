"""Unit and regression tests for C4 prediction models and baselines."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from c4.models.frequency import FrequencyBaseline
from c4.models.markov import MarkovModel
from c4.models.predictor import predict_next


# --- Fixtures labeled synthetic ---

@pytest.fixture
def synthetic_single_technique_episodes():
    """Tiny hand-computed synthetic fixture with single-technique steps."""
    return {
        "EP_SYN1": {
            "collapsed": [
                {"event_ids": ["SYN-01"], "techniques": ["T1001"], "timestamp": "2025-01-01T00:00:00Z"},
                {"event_ids": ["SYN-02"], "techniques": ["T1002"], "timestamp": "2025-01-01T00:01:00Z"},
                {"event_ids": ["SYN-03"], "techniques": ["T1003"], "timestamp": "2025-01-01T00:02:00Z"},
                {"event_ids": ["SYN-04"], "techniques": ["T1002"], "timestamp": "2025-01-01T00:03:00Z"},
            ]
        },
        "EP_SYN2": {
            "collapsed": [
                {"event_ids": ["SYN-05"], "techniques": ["T1001"], "timestamp": "2025-01-01T00:10:00Z"},
                {"event_ids": ["SYN-06"], "techniques": ["T1004"], "timestamp": "2025-01-01T00:11:00Z"},
            ]
        },
    }


@pytest.fixture
def synthetic_multi_technique_episodes():
    """Synthetic fixture with multi-technique sets to test m*n weighting."""
    return {
        "EP_MULTI": {
            "collapsed": [
                {"event_ids": ["M-01"], "techniques": ["T1010", "T1020"], "timestamp": "2025-01-01T00:00:00Z"},
                {"event_ids": ["M-02"], "techniques": ["T1030", "T1040", "T1050"], "timestamp": "2025-01-01T00:01:00Z"},
            ]
        }
    }


# --- Tests for MarkovModel ---

def test_markov_hand_computed_counts_and_probabilities(synthetic_single_technique_episodes):
    """Verify hand-computed transition counts and probabilities on synthetic single-technique episodes."""
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(synthetic_single_technique_episodes)

    # From EP_SYN1: T1001 -> T1002 (1.0), T1002 -> T1003 (1.0), T1003 -> T1002 (1.0)
    # From EP_SYN2: T1001 -> T1004 (1.0)
    # Total transitions from T1001 = 2.0
    assert model.counts["T1001"]["T1002"] == 1.0
    assert model.counts["T1001"]["T1004"] == 1.0
    assert model.probabilities["T1001"]["T1002"] == 0.5
    assert model.probabilities["T1001"]["T1004"] == 0.5

    assert model.probabilities["T1002"]["T1003"] == 1.0
    assert model.probabilities["T1003"]["T1002"] == 1.0
    assert model.n_step_transitions["T1001"] == 2
    assert model.n_step_transitions["T1002"] == 1
    assert model.n_step_transitions["T1003"] == 1


def test_markov_multi_technique_weighting(synthetic_multi_technique_episodes):
    """Verify m*n split where total weight of one step transition equals exactly 1.0."""
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(synthetic_multi_technique_episodes)

    # m=2 (T1010, T1020), n=3 (T1030, T1040, T1050) -> weight = 1/6
    expected_w = 1.0 / 6.0
    for src in ["T1010", "T1020"]:
        for tgt in ["T1030", "T1040", "T1050"]:
            assert pytest.approx(model.counts[src][tgt], rel=1e-9) == expected_w

    # Total weight added across all pairs equals 1.0
    total_weight = sum(model.counts[src][tgt] for src in ["T1010", "T1020"] for tgt in ["T1030", "T1040", "T1050"])
    assert pytest.approx(total_weight, rel=1e-9) == 1.0

    # Probabilities from each source member sum to 1.0
    for src in ["T1010", "T1020"]:
        assert pytest.approx(sum(model.probabilities[src].values()), rel=1e-9) == 1.0
        for tgt in ["T1030", "T1040", "T1050"]:
            assert pytest.approx(model.probabilities[src][tgt], rel=1e-9) == 1.0 / 3.0


def test_markov_multi_technique_averaging_with_unseen_member(synthetic_single_technique_episodes):
    """Verify averaging over multi-technique current set where one member is unseen."""
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(synthetic_single_technique_episodes)

    # Input has T1001 (observed) and T9999 (unseen)
    res = model.predict(["T1001", "T9999"], k=3)
    assert res["status"] == "ok"
    assert res["members_used"] == ["T1001"]
    assert res["members_unseen"] == ["T9999"]

    # Predictions should match T1001's distribution exactly
    cand_dict = dict(res["candidates"])
    assert cand_dict["T1002"] == 0.5
    assert cand_dict["T1004"] == 0.5
    assert pytest.approx(sum(cand_dict.values()), rel=1e-9) == 1.0


def test_markov_probabilities_sum_to_one(synthetic_single_technique_episodes, synthetic_multi_technique_episodes):
    """Assert all conditional and predicted distributions sum to 1 within 1e-9."""
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(synthetic_single_technique_episodes)

    for src in model.probabilities:
        assert pytest.approx(sum(model.probabilities[src].values()), rel=1e-9) == 1.0

    pred = model.predict(["T1001", "T1002"])
    prob_sum = sum(p for _, p in pred["candidates"])
    assert pytest.approx(prob_sum, rel=1e-9) == 1.0


def test_markov_no_cross_episode_transitions():
    """Verify that transitions NEVER cross episode boundaries."""
    episodes = {
        "EP_A": {"collapsed": [{"techniques": ["T1001"]}, {"techniques": ["T1002"]}]},
        "EP_B": {"collapsed": [{"techniques": ["T1003"]}, {"techniques": ["T1004"]}]},
    }
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(episodes)

    # EP_A ends at T1002, EP_B starts at T1003. There should be NO transition T1002 -> T1003!
    assert "T1003" not in model.counts["T1002"]
    assert "T1004" not in model.counts["T1002"]


def test_markov_training_only_isolation(synthetic_single_technique_episodes):
    """Verify that fitting on training episodes subset never uses excluded test episode."""
    episodes = dict(synthetic_single_technique_episodes)
    episodes["EP_TEST"] = {
        "collapsed": [
            {"techniques": ["T8888"]},
            {"techniques": ["T9999"]},
        ]
    }

    model = MarkovModel(variant="collapsed", granularity="full")
    # Train only on EP_SYN1
    model.fit(episodes, training_episodes=["EP_SYN1"])

    assert model.training_episodes == ["EP_SYN1"]
    assert "T8888" not in model.counts
    assert "T9999" not in model.counts
    # From EP_SYN2, T1004 should also not be in model
    assert "T1004" not in model.counts["T1001"]


def test_markov_edge_cases_unseen_empty_input_empty_training():
    """Verify status codes for unseen technique, empty input, and empty training."""
    model = MarkovModel(variant="collapsed", granularity="full")

    # Empty training
    pred_empty_train = model.predict(["T1001"])
    assert pred_empty_train["status"] == "insufficient_evidence"
    assert pred_empty_train["candidates"] == []

    # Fit small data
    model.fit({"EP": [{"techniques": ["T1001"]}, {"techniques": ["T1002"]}]})

    # Empty input
    pred_empty_input = model.predict([])
    assert pred_empty_input["status"] == "empty_input"
    assert pred_empty_input["candidates"] == []

    # Unseen technique
    pred_unseen = model.predict(["T9999"])
    assert pred_unseen["status"] == "insufficient_evidence"
    assert pred_unseen["candidates"] == []
    assert pred_unseen["members_unseen"] == ["T9999"]


def test_markov_deterministic_tie_breaking(synthetic_single_technique_episodes):
    """Verify deterministic tie-breaking (equal probability -> ascending technique ID)."""
    model = MarkovModel(variant="collapsed", granularity="full")
    model.fit(synthetic_single_technique_episodes)

    # From T1001: T1002 has prob 0.5, T1004 has prob 0.5
    res = model.predict("T1001", k=2)
    cand_list = res["candidates"]
    assert len(cand_list) == 2
    assert cand_list[0] == ("T1002", 0.5)
    assert cand_list[1] == ("T1004", 0.5)


def test_markov_save_load_round_trip(synthetic_single_technique_episodes, tmp_path):
    """Verify save/load round trip gives identical predictions and byte-identical JSON."""
    model1 = MarkovModel(variant="collapsed", granularity="full")
    model1.fit(synthetic_single_technique_episodes)

    save_path = tmp_path / "markov_test.json"
    model1.save(save_path)

    # Save a second time to test bit-identical output
    save_path2 = tmp_path / "markov_test_2.json"
    model1.save(save_path2)
    assert save_path.read_bytes() == save_path2.read_bytes()

    # Load and check predictions
    model2 = MarkovModel.load(save_path)
    pred1 = model1.predict(["T1001"])
    pred2 = model2.predict(["T1001"])
    assert pred1 == pred2


# --- Tests for FrequencyBaseline ---

def test_frequency_baseline_hand_computed(synthetic_single_technique_episodes):
    """Verify hand-computed counts and probabilities for FrequencyBaseline."""
    baseline = FrequencyBaseline(variant="collapsed", granularity="full")
    baseline.fit(synthetic_single_technique_episodes)

    # Targets in EP_SYN1: T1002, T1003, T1002 (counts: T1002=2, T1003=1)
    # Targets in EP_SYN2: T1004 (count: T1004=1)
    # Total target occurrences = 4
    # P(T1002) = 2/4 = 0.5, P(T1003) = 1/4 = 0.25, P(T1004) = 1/4 = 0.25
    assert baseline.counts["T1002"] == 2.0
    assert baseline.counts["T1003"] == 1.0
    assert baseline.counts["T1004"] == 1.0
    assert baseline.probabilities["T1002"] == 0.5
    assert baseline.probabilities["T1003"] == 0.25
    assert baseline.probabilities["T1004"] == 0.25
    assert pytest.approx(sum(baseline.probabilities.values()), rel=1e-9) == 1.0

    # Prediction tie-breaking: T1003 vs T1004 both prob 0.25 -> T1003 before T1004
    pred = baseline.predict(k=3)
    assert pred["status"] == "ok"
    assert pred["candidates"] == [("T1002", 0.5), ("T1003", 0.25), ("T1004", 0.25)]


def test_frequency_baseline_empty_training():
    """Verify empty training returns empty_training status."""
    baseline = FrequencyBaseline()
    pred = baseline.predict()
    assert pred["status"] == "empty_training"
    assert pred["candidates"] == []


# --- Tests for Common Prediction Interface ---

def test_predict_next_interface(synthetic_single_technique_episodes):
    """Verify common predict_next wrapper for both Markov and Frequency models."""
    markov = MarkovModel(variant="collapsed", granularity="full")
    markov.fit(synthetic_single_technique_episodes)

    seq_items = [
        {"event_id": "EV-01", "techniques": ["T1001"], "timestamp": "2025-01-01T00:00:00Z"},
    ]

    out_m = predict_next(seq_items, model=markov, method="markov", k=2)
    assert out_m["method"] == "markov"
    assert out_m["status"] == "ok"
    assert out_m["current_techniques"] == ["T1001"]
    assert len(out_m["predicted_candidates"]) == 2
    assert out_m["predicted_candidates"][0]["technique"] == "T1002"
    assert out_m["last_observed_event_id"] == "EV-01"
    assert "Probabilities are empirical estimates" in out_m["disclaimer"]

    # Frequency baseline
    freq = FrequencyBaseline(variant="collapsed", granularity="full")
    freq.fit(synthetic_single_technique_episodes)

    out_f = predict_next(seq_items, model=freq, method="frequency", k=2)
    assert out_f["method"] == "frequency"
    assert out_f["status"] == "ok"
    assert len(out_f["predicted_candidates"]) == 2


# --- Real-Data Smoke Test ---

def test_real_data_smoke_test_all_episodes():
    """Fit Markov model on all 4 real episodes; assert it runs and probabilities normalize."""
    seq_file = Path(__file__).resolve().parents[1] / "data" / "processed" / "attack_sequences.json"
    if not seq_file.is_file():
        pytest.skip("attack_sequences.json not found")

    with open(seq_file, encoding="utf-8") as f:
        seq_data = json.load(f)

    # Fit collapsed full
    model_col_full = MarkovModel(variant="collapsed", granularity="full")
    model_col_full.fit(seq_data["episodes"])
    assert len(model_col_full.training_episodes) == 4
    assert len(model_col_full.probabilities) > 0

    for src, targets in model_col_full.probabilities.items():
        assert pytest.approx(sum(targets.values()), rel=1e-9) == 1.0

    # Fit collapsed parent
    model_col_par = MarkovModel(variant="collapsed", granularity="parent")
    model_col_par.fit(seq_data["episodes"])
    for src, targets in model_col_par.probabilities.items():
        assert pytest.approx(sum(targets.values()), rel=1e-9) == 1.0

    # Frequency baseline
    freq = FrequencyBaseline(variant="collapsed", granularity="full")
    freq.fit(seq_data["episodes"])
    assert pytest.approx(sum(freq.probabilities.values()), rel=1e-9) == 1.0
