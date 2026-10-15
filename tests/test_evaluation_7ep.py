"""Tests for 7-Episode Pre-Registered Evaluation (E1-E7).

Tests:
1. Regression gate on 4-episode data against frozen baseline files.
2. Split disjointness across all 7 folds (no test episode in training fold).
3. McNemar exact two-sided test on hand-computed examples.
4. Byte-identical reproduction: running evaluation runner twice produces identical SHA-256 for CSV, JSON, MD.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

from scripts.check_regression_gate import run_regression_gate
from scripts.pipeline.s06_evaluation_7ep import exact_mcnemar, run_evaluation_7ep


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_regression_gate_4ep():
    """Verify that running evaluation runner logic on 4-episode data reproduces frozen baseline."""
    assert run_regression_gate() is True


def test_split_disjointness_7ep():
    """Verify that each fold in loeo_folds.json is completely disjoint from test episode."""
    folds_path = BASE_DIR / "data" / "processed_7ep" / "loeo_folds.json"
    with open(folds_path, "r", encoding="utf-8") as f:
        folds = json.load(f)

    assert len(folds) == 7
    all_eps = {f"E{i}" for i in range(1, 8)}

    for fold in folds:
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        assert test_ep not in train_eps, f"Leakage: {test_ep} in {train_eps}"
        assert len(train_eps) == 6
        assert set(train_eps) | {test_ep} == all_eps


def test_mcnemar_hand_computed_examples():
    """Verify exact two-sided McNemar on hand-computed binomial examples."""
    # Example 1: b=0, c=0 -> p = 1.0
    assert exact_mcnemar(0, 0) == 1.0

    # Example 2: b=3, c=3 -> symmetric, p = 1.0
    assert exact_mcnemar(3, 3) == 1.0

    # Example 3: b=1, c=5 -> n=6, k=1.
    # Pr(X <= 1) = (comb(6,0) + comb(6,1)) / 2^6 = (1 + 6) / 64 = 7/64 = 0.109375
    # Two-sided p = 2 * 7/64 = 14/64 = 0.21875
    p3 = exact_mcnemar(1, 5)
    assert abs(p3 - 0.21875) < 1e-9

    # Example 4: b=0, c=4 -> n=4, k=0.
    # Pr(X = 0) = 1 / 16 = 0.0625. Two-sided p = 2 * 0.0625 = 0.125
    p4 = exact_mcnemar(0, 4)
    assert abs(p4 - 0.125) < 1e-9

    # Symmetry: exact_mcnemar(b, c) == exact_mcnemar(c, b)
    assert exact_mcnemar(5, 1) == exact_mcnemar(1, 5)
    assert exact_mcnemar(4, 0) == exact_mcnemar(0, 4)


def test_byte_identical_rerun(tmp_path):
    """Verify that running the evaluation produces deterministic byte-identical files."""
    csv_path = BASE_DIR / "data" / "processed_7ep" / "evaluation_7ep_predictions.csv"
    json_path = BASE_DIR / "reports" / "7ep" / "evaluation_7ep_results.json"
    md_path = BASE_DIR / "reports" / "7ep" / "evaluation_7ep_report.md"

    # Capture initial hashes
    h_csv_1 = sha256_file(csv_path)
    h_json_1 = sha256_file(json_path)
    h_md_1 = sha256_file(md_path)

    # Re-run evaluation
    run_evaluation_7ep()

    # Capture re-run hashes
    h_csv_2 = sha256_file(csv_path)
    h_json_2 = sha256_file(json_path)
    h_md_2 = sha256_file(md_path)

    assert h_csv_1 == h_csv_2, "Predictions CSV changed on re-run!"
    assert h_json_1 == h_json_2, "Results JSON changed on re-run!"
    assert h_md_1 == h_md_2, "Report Markdown changed on re-run!"
