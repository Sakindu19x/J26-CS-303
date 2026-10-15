"""test_overnight_summary.py

Pytest suite for reports/overnight_summary.md (Prompt 14 Q6).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_overnight_summary import verify_overnight_summary


def test_verify_overnight_summary_independent_verifier():
    """Verify that overnight summary passes independent verification."""
    verify_overnight_summary()


def test_overnight_summary_contains_required_sections():
    """Verify that all 4 required sections and ledger/decisions are present."""
    text = (REPO_ROOT / "reports" / "overnight_summary.md").read_text(encoding="utf-8")
    assert "## 1. Executive Summary" in text
    assert "## 2. Overnight Execution Ledger" in text
    assert "## 3. Overnight Decisions Register" in text
    assert "## 4. Verification & Audit Sign-Off" in text
    assert "P2 (Correction)" in text
    assert "Prompt 13 final chat message blocks with contradictions" in text
