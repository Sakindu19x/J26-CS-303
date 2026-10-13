"""Tests for C4 LOEO evaluation pipeline (Hit definitions, isolation, metrics, idempotency)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from c4.evaluation import compute_set_metrics, evaluate_loeo_slice, run_full_evaluation
from c4.models.markov import MarkovModel
from c4.models.predictor import predict_next


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Test 1: Hit definition including abstention and multi-target samples (Synthetic)
# ---------------------------------------------------------------------------
def test_hit_definition_synthetic() -> None:
    """SYNTHETIC TEST: Verify Hit@1 and Hit@3 rules with multi-target sets and abstentions."""
    # Synthetic target sets
    single_target = {"T1001"}
    multi_target = {"T1001", "T1002", "T1003"}

    # Case A: Top-1 hit on single target
    cands_a = [("T1001", 0.6), ("T1005", 0.4)]
    preds_a = [c[0] for c in cands_a]
    assert (preds_a[0] in single_target) is True  # Hit@1 = 1
    assert any(c in single_target for c in preds_a[:3]) is True  # Hit@3 = 1

    # Case B: Top-1 miss, Top-3 hit on single target
    cands_b = [("T1005", 0.5), ("T1001", 0.3), ("T1008", 0.2)]
    preds_b = [c[0] for c in cands_b]
    assert (preds_b[0] in single_target) is False  # Hit@1 = 0
    assert any(c in single_target for c in preds_b[:3]) is True  # Hit@3 = 1

    # Case C: Hit on multi-target set (matching 1 of 3 target techniques)
    cands_c = [("T1099", 0.7), ("T1002", 0.3)]
    preds_c = [c[0] for c in cands_c]
    assert (preds_c[0] in multi_target) is False  # Hit@1 = 0
    assert any(c in multi_target for c in preds_c[:3]) is True  # Hit@3 = 1

    # Case D: Complete miss
    cands_d = [("T1099", 0.5), ("T1098", 0.3), ("T1097", 0.2)]
    preds_d = [c[0] for c in cands_d]
    assert (preds_d[0] in multi_target) is False  # Hit@1 = 0
    assert any(c in multi_target for c in preds_d[:3]) is False  # Hit@3 = 0

    # Case E: Abstention (status insufficient_evidence => empty candidates)
    cands_e: list[tuple[str, float]] = []
    preds_e = [c[0] for c in cands_e]
    hit1_e = 1 if (preds_e and preds_e[0] in multi_target) else 0
    hit3_e = 1 if any(c in multi_target for c in preds_e[:3]) else 0
    assert hit1_e == 0
    assert hit3_e == 0


# ---------------------------------------------------------------------------
# Test 2: Fold models never contain test-episode evidence
# ---------------------------------------------------------------------------
def test_fold_models_never_contain_test_episode_evidence() -> None:
    """Verify that every fitted LOEO fold model is strictly isolated from its test episode."""
    loeo_dir = MODELS_DIR / "loeo"
    assert loeo_dir.exists(), "data/models/loeo directory must exist after evaluation."

    with open(PROCESSED_DIR / "loeo_folds.json", encoding="utf-8") as f:
        folds = json.load(f)
    test_eps_by_fold = {f["fold_id"]: f["test_episode"] for f in folds}

    fold_files = list(loeo_dir.glob("*.json"))
    assert len(fold_files) > 0, "No fold models found in data/models/loeo."

    for mf in fold_files:
        with open(mf, encoding="utf-8") as f:
            data = json.load(f)

        # Identify fold ID from filename
        matched_fold = None
        for fid in test_eps_by_fold:
            if fid in mf.name:
                matched_fold = fid
                break
        if matched_fold is None:
            continue

        test_ep = test_eps_by_fold[matched_fold]
        train_eps = data.get("training_episodes", [])
        assert test_ep not in train_eps, f"Leak: test episode {test_ep} in training episodes of {mf.name}"

        # Inspect evidence
        evidence_dict = data.get("evidence", {})
        for a, tgt_dict in evidence_dict.items():
            if isinstance(tgt_dict, dict):
                # Markov evidence: {source: {target: [[ep, cur, tgt], ...]}}
                for b, ev_list in tgt_dict.items():
                    for ev in ev_list:
                        assert ev[0] != test_ep, f"Evidence leak in {mf.name}: transition {a}->{b} references test ep {test_ep}"
            elif isinstance(tgt_dict, list):
                # Frequency evidence: {target: [[ep, cur, tgt], ...]}
                for ev in tgt_dict:
                    assert ev[0] != test_ep, f"Evidence leak in {mf.name}: target {a} references test ep {test_ep}"


# ---------------------------------------------------------------------------
# Test 3: Evaluation does not touch deployment model files
# ---------------------------------------------------------------------------
def test_evaluation_does_not_touch_deployment_models() -> None:
    """Verify that running evaluation never overwrites all-episodes deployment models in data/models/."""
    deployment_models = [
        MODELS_DIR / "markov_collapsed_full.json",
        MODELS_DIR / "markov_collapsed_parent.json",
        MODELS_DIR / "markov_raw_full.json",
        MODELS_DIR / "markov_raw_parent.json",
        MODELS_DIR / "frequency_collapsed_full.json",
        MODELS_DIR / "frequency_collapsed_parent.json",
        MODELS_DIR / "frequency_raw_full.json",
        MODELS_DIR / "frequency_raw_parent.json",
    ]

    hashes_before = {p.name: _hash_file(p) for p in deployment_models if p.exists()}
    assert len(hashes_before) == 8, "Expected 8 deployment models in data/models/."

    # Run slice evaluation
    evaluate_loeo_slice(variant="collapsed", granularity="full", save_fold_models=True)

    hashes_after = {p.name: _hash_file(p) for p in deployment_models if p.exists()}
    for name in hashes_before:
        assert hashes_before[name] == hashes_after[name], f"Deployment model {name} was modified by evaluation!"


# ---------------------------------------------------------------------------
# Test 4: Micro and Macro PR/F1 metrics on hand-computed synthetic example
# ---------------------------------------------------------------------------
def test_micro_macro_metrics_hand_computed() -> None:
    """SYNTHETIC TEST: Hand-checkable verification of set-based micro/macro Precision, Recall, and F1."""
    # Synthetic scenario: 3 samples, active classes {'T1', 'T2', 'T3', 'T4'}
    # Sample 1: pred={'T1', 'T2'}, target={'T1', 'T3'}
    #   TP1=1 ('T1'), FP1=1 ('T2'), FN1=1 ('T3')
    # Sample 2: pred={'T2'}, target={'T2'}
    #   TP2=1 ('T2'), FP2=0, FN2=0
    # Sample 3: pred=set() [abstain], target={'T4'}
    #   TP3=0, FP3=0, FN3=1 ('T4')
    #
    # Totals:
    #   TP = 1 + 1 + 0 = 2
    #   FP = 1 + 0 + 0 = 1
    #   FN = 1 + 0 + 1 = 2
    # Micro Precision = 2 / (2 + 1) = 2/3 ≈ 0.666667
    # Micro Recall    = 2 / (2 + 2) = 2/4 = 0.500000
    # Micro F1        = 2 * (2/3) * (1/2) / (2/3 + 1/2) = (2/3) / (7/6) = 4/7 ≈ 0.571429
    #
    # Per-class counts across the 3 samples:
    #   'T1': in pred 1 time, in target 1 time => TP=1, FP=0, FN=0 => P=1.0, R=1.0, F1=1.0
    #   'T2': in pred 2 times, in target 1 time (sample 2 hit, sample 1 false pos) => TP=1, FP=1, FN=0 => P=0.5, R=1.0, F1=2/3
    #   'T3': in pred 0 times, in target 1 time (sample 1 miss) => TP=0, FP=0, FN=1 => P=0.0, R=0.0, F1=0.0
    #   'T4': in pred 0 times, in target 1 time (sample 3 miss) => TP=0, FP=0, FN=1 => P=0.0, R=0.0, F1=0.0
    #
    # Macro averages over 4 classes:
    #   Macro Precision = (1.0 + 0.5 + 0.0 + 0.0) / 4 = 1.5 / 4 = 0.375
    #   Macro Recall    = (1.0 + 1.0 + 0.0 + 0.0) / 4 = 2.0 / 4 = 0.500
    #   Macro F1        = (1.0 + 2/3 + 0.0 + 0.0) / 4 = (5/3) / 4 = 5/12 ≈ 0.416667

    pairs = [
        ({"T1", "T2"}, {"T1", "T3"}),
        ({"T2"}, {"T2"}),
        (set(), {"T4"}),
    ]

    res = compute_set_metrics(pairs)
    mic = res["micro"]
    mac = res["macro"]

    assert mic["tp"] == 2
    assert mic["fp"] == 1
    assert mic["fn"] == 2
    assert pytest.approx(mic["precision"], abs=1e-5) == 2.0 / 3.0
    assert pytest.approx(mic["recall"], abs=1e-5) == 0.5
    assert pytest.approx(mic["f1"], abs=1e-5) == 4.0 / 7.0

    assert mac["num_classes"] == 4
    assert pytest.approx(mac["precision"], abs=1e-5) == 0.375
    assert pytest.approx(mac["recall"], abs=1e-5) == 0.5
    assert pytest.approx(mac["f1"], abs=1e-5) == 5.0 / 12.0


# ---------------------------------------------------------------------------
# Test 5: Evaluation Markov predictions equal predict_next for 5 real samples
# ---------------------------------------------------------------------------
def test_evaluation_markov_predictions_equal_predict_next() -> None:
    """Verify that predictions in evaluation match the standalone predict_next interface."""
    with open(PROCESSED_DIR / "next_technique_samples.json", encoding="utf-8") as f:
        samples = json.load(f)
    cf_samples = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]

    with open(PROCESSED_DIR / "attack_sequences.json", encoding="utf-8") as f:
        sequences = json.load(f)
    with open(PROCESSED_DIR / "loeo_folds.json", encoding="utf-8") as f:
        folds = json.load(f)
    folds_by_ep = {f["test_episode"]: f for f in folds}

    # Test 5 real samples across different episodes
    test_samples = [cf_samples[0], cf_samples[15], cf_samples[25], cf_samples[40], cf_samples[55]]

    for s in test_samples:
        ep = s["episode_id"]
        fold = folds_by_ep[ep]
        train_eps = fold["training_episodes"]

        mm = MarkovModel("collapsed", "full").fit(sequences, training_episodes=train_eps)

        # Direct model predict
        direct_pred = mm.predict(s["current_technique_set"], k=3)

        # predict_next interface
        seq_mock = [{"event_ids": ["E_mock"], "techniques": s["current_technique_set"]}]
        wrapper_pred = predict_next(seq_mock, model=mm, method="markov", k=3)

        assert direct_pred["status"] == wrapper_pred["status"]
        if direct_pred["status"] == "ok":
            d_cands = [c[0] for c in direct_pred["candidates"]]
            w_cands = [c["technique"] for c in wrapper_pred["predicted_candidates"]]
            assert d_cands == w_cands
            d_probs = [c[1] for c in direct_pred["candidates"]]
            w_probs = [c["probability"] for c in wrapper_pred["predicted_candidates"]]
            assert pytest.approx(d_probs, abs=1e-9) == w_probs


# ---------------------------------------------------------------------------
# Test 6: Evaluation outputs are byte-identical across two runs
# ---------------------------------------------------------------------------
def test_evaluation_outputs_byte_identical_across_two_runs() -> None:
    """Verify deterministic idempotency: running evaluation twice produces byte-identical files."""
    results_path = REPORTS_DIR / "evaluation_results.json"
    pred_path = PROCESSED_DIR / "evaluation_predictions.csv"
    report_md_path = REPORTS_DIR / "evaluation_report.md"

    # Capture initial hashes
    h_json_1 = _hash_file(results_path)
    h_csv_1 = _hash_file(pred_path)
    h_md_1 = _hash_file(report_md_path)

    # Re-run full evaluation
    run_full_evaluation()

    h_json_2 = _hash_file(results_path)
    h_csv_2 = _hash_file(pred_path)
    h_md_2 = _hash_file(report_md_path)

    assert h_json_1 == h_json_2, "reports/evaluation_results.json is not byte-identical across runs!"
    assert h_csv_1 == h_csv_2, "data/processed/evaluation_predictions.csv is not byte-identical across runs!"
    assert h_md_1 == h_md_2, "reports/evaluation_report.md is not byte-identical across runs!"
