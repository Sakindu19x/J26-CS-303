"""tests/test_import_integrity.py

Automated regression gate verifying AST-parsed local import integrity.
Gate introduced in Prompt 17 Part T5.
"""
from __future__ import annotations

from scripts.audit.check_imports import check_all_imports


def test_import_integrity_gate() -> None:
    """Assert all local imports and symbol references resolve cleanly."""
    assert check_all_imports() == 0
