"""verify_requirements_trace.py

Independent verifier for reports/7ep/requirements_trace.md (Prompt 14 Q4).
Asserts:
1. Every proposal title in requirements_trace.md matches docs/proposal_requirements.json.
2. Every file path in Implementing Modules and Evidence exists on disk.
3. Every test node id in Evidence collects in `pytest --collect-only`.
4. Every status is in the fixed enum {IMPLEMENTED_AND_TESTED, IMPLEMENTED_DEMONSTRATED_ON_DATASET, PARTIAL, NOT_TESTABLE_UNTIL_C3, PENDING_HUMAN_EVIDENCE}.
5. Rule assertions:
   - NFR4 == PENDING_HUMAN_EVIDENCE
   - FR8 and FR9 != IMPLEMENTED_AND_TESTED
   - FR2 limits state whether episodes come from dataset labels or an algorithm
   - NFR1 limits declare thresholds by C4 and that proposal has none.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROPOSAL_JSON_PATH = REPO_ROOT / "docs" / "proposal_requirements.json"
TRACE_MD_PATH = REPO_ROOT / "reports" / "7ep" / "requirements_trace.md"

VALID_STATUSES = {
    "IMPLEMENTED_AND_TESTED",
    "IMPLEMENTED_DEMONSTRATED_ON_DATASET",
    "PARTIAL",
    "NOT_TESTABLE_UNTIL_C3",
    "PENDING_HUMAN_EVIDENCE",
}

_CACHED_COLLECTED_TESTS: set[str] | None = None


def parse_trace_table(md_text: str) -> list[dict[str, str]]:
    rows = []
    # Match markdown table rows: | **ID** | Title | Modules | Evidence | `Status` | Limits |
    pattern = re.compile(
        r"^\|\s*\*\*([A-Z0-9]+)\*\*\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*`([^`]+)`\s*\|\s*([^|]+)\|",
        re.MULTILINE,
    )
    for m in pattern.finditer(md_text):
        rows.append({
            "id": m.group(1).strip(),
            "title": m.group(2).strip(),
            "modules": m.group(3).strip(),
            "evidence": m.group(4).strip(),
            "status": m.group(5).strip(),
            "limits": m.group(6).strip(),
        })
    return rows


def verify_requirements_trace(md_text_override: str | None = None) -> None:
    if md_text_override is not None:
        md_text = md_text_override
    else:
        assert TRACE_MD_PATH.is_file(), f"Missing trace markdown: {TRACE_MD_PATH}"
        md_text = TRACE_MD_PATH.read_text(encoding="utf-8")

    assert PROPOSAL_JSON_PATH.is_file(), f"Missing proposal JSON: {PROPOSAL_JSON_PATH}"
    with open(PROPOSAL_JSON_PATH, "r", encoding="utf-8") as f:
        proposal_data = json.load(f)

    expected_reqs = {r["id"]: r["proposal_title"] for r in proposal_data["requirements"]}
    rows = parse_trace_table(md_text)

    assert len(rows) == len(expected_reqs), f"Row count mismatch: expected {len(expected_reqs)}, got {len(rows)}"

    # 1. Title matching
    for row in rows:
        rid = row["id"]
        assert rid in expected_reqs, f"Unexpected requirement ID in markdown: {rid}"
        exp_title = expected_reqs[rid]
        assert row["title"] == exp_title, f"Title mismatch for {rid}: expected '{exp_title}', got '{row['title']}'"

    # 2. Status enum checking
    for row in rows:
        st = row["status"]
        assert st in VALID_STATUSES, f"Invalid status '{st}' for {row['id']}"

    # 3. Rule assertions
    row_map = {r["id"]: r for r in rows}

    assert row_map["NFR4"]["status"] == "PENDING_HUMAN_EVIDENCE", "Rule violation: NFR4 must be PENDING_HUMAN_EVIDENCE"
    assert row_map["FR8"]["status"] != "IMPLEMENTED_AND_TESTED", "Rule violation: FR8 cannot be IMPLEMENTED_AND_TESTED"
    assert row_map["FR9"]["status"] != "IMPLEMENTED_AND_TESTED", "Rule violation: FR9 cannot be IMPLEMENTED_AND_TESTED"
    assert "dataset labels" in row_map["FR2"]["limits"], "Rule violation: FR2 must state whether episodes come from dataset labels or an algorithm"
    assert "declared by C4, proposal has none" in row_map["NFR1"]["limits"], "Rule violation: NFR1 must state declared by C4, proposal has none"

    # 4. Path and test existence checks
    global _CACHED_COLLECTED_TESTS
    if _CACHED_COLLECTED_TESTS is None:
        res = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=str(REPO_ROOT), capture_output=True, text=True)
        assert res.returncode == 0, f"pytest --collect-only failed:\n{res.stderr}"
        _CACHED_COLLECTED_TESTS = set(res.stdout.splitlines())

    collected_tests = _CACHED_COLLECTED_TESTS

    for row in rows:
        # Check modules
        for path_str in re.findall(r"`([^`]+)`", row["modules"]):
            p = REPO_ROOT / path_str.strip()
            assert p.exists(), f"Implementing module path does not exist for {row['id']}: {path_str}"

        # Check evidence
        for item in re.findall(r"`([^`]+)`", row["evidence"]):
            clean_item = item.strip()
            if "::" in clean_item:
                # Test node id
                assert clean_item in collected_tests, f"Test node ID not collected for {row['id']}: {clean_item}"
            else:
                # File path
                p = REPO_ROOT / clean_item
                assert p.exists(), f"Evidence file path does not exist for {row['id']}: {clean_item}"

    print(f"Independent verification of requirements trace PASSED ({len(rows)} requirements verified)")


if __name__ == "__main__":
    verify_requirements_trace()
