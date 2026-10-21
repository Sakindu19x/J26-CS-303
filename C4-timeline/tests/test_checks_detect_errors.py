"""Non-tautology proof: asserts that consistency check functions detect wrong numbers.

For at least 6 representative check functions:
1. Headline counts (Section 2)
2. Headline percentages (Section 2)
3. 2x2 paired comparison (Section 4)
4. Frequency-only split by Markov status (Section 4)
5. Tie diagnostic table & sentence (Section 6)
6. Markov vs Frequency sensitivity ordering sentence (Section 8.3)

Each test verifies that the check function PASSES on authentic report text,
then mutates ONE number in an in-memory copy (without writing to disk),
and asserts that the check FAILS with an AssertionError.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.verify.verify_tactic_evaluation import recompute_from_csv
from tests.test_tactic_evaluation_consistency import (
    check_headline_counts,
    check_headline_percentages,
    check_paired_2x2,
    check_frequency_only_split,
    check_tie_diagnostic,
    check_sensitivity_sentence,
)

BASE_DIR = Path(__file__).resolve().parents[1]
MD_PATH = BASE_DIR / "reports" / "tactic_evaluation_report.md"


@pytest.fixture(scope="module")
def report_text() -> str:
    return MD_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def recomputed():
    return recompute_from_csv()


def test_headline_counts_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating one count causes check_headline_counts to fail."""
    # Authentic report passes
    check_headline_counts(report_text, recomputed)

    # Mutate Top-1 hits from 11 to 99 for tactic_collapsed markov
    mutated = report_text.replace(
        "| `tactic_collapsed` | markov | 53 | 11 |",
        "| `tactic_collapsed` | markov | 53 | 99 |",
        1,
    )
    assert mutated != report_text

    with pytest.raises(AssertionError, match="Top-1 hits mismatch"):
        check_headline_counts(mutated, recomputed)


def test_headline_percentages_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating one percentage causes check_headline_percentages to fail."""
    # Authentic report passes
    check_headline_percentages(report_text, recomputed)

    # Mutate Top-1 rate from 20.75% to 99.99% for tactic_collapsed markov
    mutated = report_text.replace("20.75%", "99.99%", 1)
    assert mutated != report_text

    with pytest.raises(AssertionError, match="Top-1 rate mismatch"):
        check_headline_percentages(mutated, recomputed)


def test_paired_2x2_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating one cell causes check_paired_2x2 to fail."""
    # Authentic report passes
    check_paired_2x2(report_text, recomputed)

    # Mutate Both hit from 2 to 99 for tactic_collapsed k=1
    mutated = report_text.replace(
        "| `tactic_collapsed` | 1 | 2 | 9 | 7 | 35 |",
        "| `tactic_collapsed` | 1 | 99 | 9 | 7 | 35 |",
        1,
    )
    assert mutated != report_text

    with pytest.raises(AssertionError):
        check_paired_2x2(mutated, recomputed)


def test_frequency_only_split_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating one count causes check_frequency_only_split to fail."""
    # Authentic report passes
    check_frequency_only_split(report_text, recomputed)

    # Mutate Frequency-only hits from 7 to 99 for tactic_collapsed k=1
    mutated = report_text.replace(
        "| `tactic_collapsed` | 1 | 7 | 5 | 2 | 0 |",
        "| `tactic_collapsed` | 1 | 99 | 5 | 2 | 0 |",
        1,
    )
    assert mutated != report_text

    with pytest.raises(AssertionError):
        check_frequency_only_split(mutated, recomputed)


def test_tie_diagnostic_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating one number causes check_tie_diagnostic to fail."""
    # Authentic report passes
    check_tie_diagnostic(report_text, recomputed)

    # Mutate 8 of 50 to 99 of 50 in sentence
    mutated = report_text.replace("8 of 50 Markov predictions", "99 of 50 Markov predictions", 1)
    assert mutated != report_text

    with pytest.raises(AssertionError, match="Missing tie sentence"):
        check_tie_diagnostic(mutated, recomputed)


def test_sensitivity_sentence_detects_error(report_text: str, recomputed) -> None:
    """Authentic report passes; mutating ordering status causes check_sensitivity_sentence to fail."""
    # Authentic report passes
    check_sensitivity_sentence(report_text, recomputed)

    # Mutate **different** to **the same** for tactic_collapsed k=1 ordering sentence
    target_sentence = (
        "- For `tactic_collapsed` at k=1: under official tactics Markov (11) is above Frequency (9), "
        "and under dataset tactics Markov (7) is below Frequency (12); "
        "the Markov-vs-Frequency ordering is **different**."
    )
    corrupted_sentence = (
        "- For `tactic_collapsed` at k=1: under official tactics Markov (11) is above Frequency (9), "
        "and under dataset tactics Markov (7) is below Frequency (12); "
        "the Markov-vs-Frequency ordering is **the same**."
    )
    mutated = report_text.replace(target_sentence, corrupted_sentence, 1)
    assert mutated != report_text

    with pytest.raises(AssertionError, match="Missing ordering sentence"):
        check_sensitivity_sentence(mutated, recomputed)
