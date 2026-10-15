"""test_requirements_trace.py

Tests for Requirements Traceability Matrix (Prompt 14 Q4).
Asserts:
1. docs/proposal_requirements.json exists and validates.
2. scripts/verify_requirements_trace.py passes.
3. scripts/mutation_sweep_requirements_trace.py runs with 0 undetected mutations.
4. reports/audit/exempt_requirements_trace.txt exists.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_JSON_PATH = REPO_ROOT / "docs" / "proposal_requirements.json"
TRACE_MD_PATH = REPO_ROOT / "reports" / "7ep" / "requirements_trace.md"
EXEMPT_TXT_PATH = REPO_ROOT / "reports" / "audit" / "exempt_requirements_trace.txt"


def test_proposal_requirements_json_schema():
    assert PROPOSAL_JSON_PATH.is_file(), f"Missing {PROPOSAL_JSON_PATH}"
    with open(PROPOSAL_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "_metadata" in data
    assert "requirements" in data
    assert len(data["requirements"]) == 15
    for r in data["requirements"]:
        assert "id" in r
        assert "proposal_title" in r
        assert "proposal_wording" in r


def test_verify_requirements_trace_independent_script():
    script = REPO_ROOT / "scripts" / "verify_requirements_trace.py"
    res = subprocess.run([sys.executable, str(script)], cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"verify_requirements_trace.py failed:\n{res.stdout}\n{res.stderr}"


def test_mutation_sweep_requirements_trace():
    script = REPO_ROOT / "scripts" / "mutation_sweep_requirements_trace.py"
    res = subprocess.run([sys.executable, str(script)], cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert res.returncode == 0, f"mutation_sweep_requirements_trace.py failed:\n{res.stdout}\n{res.stderr}"
    assert EXEMPT_TXT_PATH.is_file()
    assert len(EXEMPT_TXT_PATH.read_text(encoding="utf-8").strip()) > 0
