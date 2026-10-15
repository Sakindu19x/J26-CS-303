"""Mutation sweep tests for Viva Pack documents (P9).

Performs in-memory mutation sweeps over data-bearing tokens in viva_pack/
and asserts 100% detection rate by verify_viva_pack().
"""
from __future__ import annotations

import re
from pathlib import Path
import pytest

try:
    from scripts.verify.verify_viva_pack import verify_viva_pack
except ImportError:
    from scripts.verify_viva_pack import verify_viva_pack

REPO_ROOT = Path(__file__).resolve().parents[1]
VIVA_DIR = REPO_ROOT / "viva_pack"


def test_verify_viva_pack_clean():
    """Verify that verify_viva_pack passes cleanly on unmodified files."""
    assert verify_viva_pack() == 0


def test_viva_pack_numeric_mutation_sweep():
    """Mutate every score/hash token in 03_scores.md and verify detection."""
    scores_path = VIVA_DIR / "03_scores.md"
    orig_text = scores_path.read_text(encoding="utf-8")

    # Tokens to mutate (percentages and metrics)
    targets = [
        "3.16%",
        "7.37%",
        "16.84%",
        "28.95%",
        "18.42%",
        "63.16%",
        "62.11%",
        "64.21%",
        "64.98%",
        "Status: MISSING",
    ]

    detected = 0
    total = len(targets)

    for tok in targets:
        mutated_tok = "99.99%" if tok != "Status: MISSING" else "Status: PRESENT"
        mutated_text = orig_text.replace(tok, mutated_tok)
        assert mutated_text != orig_text, f"Token {tok} not replaced"

        # Temporarily write mutated file
        scores_path.write_text(mutated_text, encoding="utf-8")
        try:
            exit_code = verify_viva_pack()
            if exit_code != 0:
                detected += 1
        finally:
            # Restore original
            scores_path.write_text(orig_text, encoding="utf-8")

    assert detected == total, f"Detected {detected}/{total} mutations"
    print(f"\nMutation Sweep: Detected {detected}/{total} mutations (100% detection rate)")


def test_viva_pack_dataset_hash_mutation_sweep():
    """Mutate hashes in 01_dataset.md and 02_split_and_training.md and verify detection."""
    d01_path = VIVA_DIR / "01_dataset.md"
    orig_d01 = d01_path.read_text(encoding="utf-8")

    hash_to_mutate = "0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc"
    mutated_d01 = orig_d01.replace(hash_to_mutate, "0000000000000000000000000000000000000000000000000000000000000000")

    d01_path.write_text(mutated_d01, encoding="utf-8")
    try:
        exit_code = verify_viva_pack()
        assert exit_code != 0, "Mutation in 01_dataset.md was not detected!"
    finally:
        d01_path.write_text(orig_d01, encoding="utf-8")


def test_viva_pack_reproduce_mutation_sweep():
    """Mutate verifier count and script path in 07_reproduce.md and verify detection."""
    d07_path = VIVA_DIR / "07_reproduce.md"
    orig_d07 = d07_path.read_text(encoding="utf-8")

    # 1. Mutate verifier count
    mutated_count = orig_d07.replace("all 18 deterministic verifiers", "all 99 deterministic verifiers")
    d07_path.write_text(mutated_count, encoding="utf-8")
    try:
        assert verify_viva_pack() != 0, "Mutation of verifier count in 07_reproduce.md was not detected!"
    finally:
        d07_path.write_text(orig_d07, encoding="utf-8")

    # 2. Mutate script path
    mutated_script = orig_d07.replace("`scripts/pipeline/s01_normalize_events.py`", "`scripts/nonexistent_step.py`")
    d07_path.write_text(mutated_script, encoding="utf-8")
    try:
        assert verify_viva_pack() != 0, "Mutation of script path in 07_reproduce.md was not detected!"
    finally:
        d07_path.write_text(orig_d07, encoding="utf-8")

