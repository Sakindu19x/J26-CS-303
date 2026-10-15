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
    assert row_map["FR2"]["status"] == "IMPLEMENTED_DEMONSTRATED_ON_DATASET", "Rule violation: FR2 must be IMPLEMENTED_DEMONSTRATED_ON_DATASET"
    assert row_map["NFR5"]["status"] == "PARTIAL", "Rule violation: NFR5 must be PARTIAL"

    assert "dataset labels" in row_map["FR2"]["limits"], "Rule violation: FR2 must state whether episodes come from dataset labels or an algorithm"
    assert "verified by test tests/test_timeline_and_sequences.py::test_events_from_different_episodes_never_in_one_sequence" in row_map["FR2"]["limits"], "Rule violation: FR2 must state verified by test <node_id>"
    assert "cryptographically verified" not in row_map["FR2"]["limits"], "Rule violation: FR2 must not state cryptographically verified"

    assert "format proposed by c4, not agreed by c3" in row_map["NFR5"]["limits"].lower(), "Rule violation: NFR5 must state format proposed by C4, not agreed by C3"
    assert "adapter tested only against c4's own fixtures" in row_map["NFR5"]["limits"].lower(), "Rule violation: NFR5 must state adapter tested only against C4's own fixtures"
    assert "declared by C4, proposal has none" in row_map["NFR1"]["limits"], "Rule violation: NFR1 must state declared by C4, proposal has none"

    assert "Hit@3" in row_map["FR4"]["limits"], "Rule violation: FR4 must cite Hit@3 verdict"
    assert "Hit@1" not in row_map["FR4"]["limits"], "Rule violation: FR4 must not cite Hit@1"

    # 4. JSON pointer resolution and verification of matrix numbers
    def resolve_json_pointer(file_rel: str, pointer: str, transform: str | None = None) -> Any:
        target_path = REPO_ROOT / file_rel
        assert target_path.is_file(), f"JSON pointer target file does not exist: {target_path}"
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        parts = [p.replace("~1", "/").replace("~0", "~") for p in pointer.strip("/").split("/")]
        curr = data
        for p in parts:
            if isinstance(curr, list):
                curr = curr[int(p)]
            else:
                curr = curr[p]
        if transform in {"length", "len"}:
            return len(curr)
        return curr

    ptrs = proposal_data.get("named_json_pointers", {})
    assert ptrs, "Missing named_json_pointers in docs/proposal_requirements.json"

    fr4_episodes = resolve_json_pointer(ptrs["fr4_episodes"]["file"], ptrs["fr4_episodes"]["pointer"], ptrs["fr4_episodes"].get("type"))
    fr4_tech_samples = resolve_json_pointer(ptrs["fr4_technique_samples"]["file"], ptrs["fr4_technique_samples"]["pointer"])
    fr4_tactic_samples = resolve_json_pointer(ptrs["fr4_tactic_samples"]["file"], ptrs["fr4_tactic_samples"]["pointer"])
    fr4_p2_markov = resolve_json_pointer(ptrs["fr4_p2_markov_hit3"]["file"], ptrs["fr4_p2_markov_hit3"]["pointer"])
    fr4_p2_freq = resolve_json_pointer(ptrs["fr4_p2_frequency_hit3"]["file"], ptrs["fr4_p2_frequency_hit3"]["pointer"])
    fr4_p2_adj_p = f"{resolve_json_pointer(ptrs['fr4_p2_adjusted_p']['file'], ptrs['fr4_p2_adjusted_p']['pointer']):.4f}"
    fr4_p1_markov = resolve_json_pointer(ptrs["fr4_p1_markov_hit3"]["file"], ptrs["fr4_p1_markov_hit3"]["pointer"])
    fr4_p1_freq = resolve_json_pointer(ptrs["fr4_p1_frequency_hit3"]["file"], ptrs["fr4_p1_frequency_hit3"]["pointer"])
    fr4_p1_adj_p = f"{resolve_json_pointer(ptrs['fr4_p1_adjusted_p']['file'], ptrs['fr4_p1_adjusted_p']['pointer']):.4f}"
    fr4_verdict = resolve_json_pointer(ptrs["fr4_formal_verdict"]["file"], ptrs["fr4_formal_verdict"]["pointer"])

    fr7_total = resolve_json_pointer(ptrs["fr7_total_records"]["file"], ptrs["fr7_total_records"]["pointer"])
    fr7_cautioned = resolve_json_pointer(ptrs["fr7_cautioned_records"]["file"], ptrs["fr7_cautioned_records"]["pointer"])

    nfr1_warm_median = f"{resolve_json_pointer(ptrs['nfr1_warm_median']['file'], ptrs['nfr1_warm_median']['pointer']):.2f}"
    nfr1_warm_p95 = f"{resolve_json_pointer(ptrs['nfr1_warm_p95']['file'], ptrs['nfr1_warm_p95']['pointer']):.2f}"
    nfr1_cold_start = f"{resolve_json_pointer(ptrs['nfr1_cold_start']['file'], ptrs['nfr1_cold_start']['pointer']):.2f}"

    # Verify numbers in FR4 limits
    fr4_limits = row_map["FR4"]["limits"]
    assert f"all {fr4_episodes} episodes" in fr4_limits, f"FR4 missing episodes count {fr4_episodes}"
    assert f"({fr4_tech_samples} technique, {fr4_tactic_samples} tactic evaluation samples)" in fr4_limits, "FR4 sample counts mismatch"
    assert fr4_verdict in fr4_limits, f"FR4 missing formal verdict {fr4_verdict}"
    assert f"Hit@3 technique P2: {fr4_p2_markov}/{fr4_tech_samples} vs {fr4_p2_freq}/{fr4_tech_samples}, Holm p = {fr4_p2_adj_p}" in fr4_limits
    assert f"Hit@3 tactic P1: {fr4_p1_markov}/{fr4_tactic_samples} ties {fr4_p1_freq}/{fr4_tactic_samples}, Holm p = {fr4_p1_adj_p}" in fr4_limits

    # Verify numbers in FR7 and FR9 limits
    assert f"({fr7_cautioned}/{fr7_total} records flagged with low support)" in row_map["FR7"]["limits"]
    assert f"all {fr7_total} offline LOEO records" in row_map["FR9"]["limits"]

    # Verify numbers in NFR1 limits
    nfr1_limits = row_map["NFR1"]["limits"]
    assert f"warm median latency <= {nfr1_warm_median} s" in nfr1_limits
    assert f"warm p95 <= {nfr1_warm_p95} s" in nfr1_limits
    assert f"parent-timed process cold start <= {nfr1_cold_start} s" in nfr1_limits

    # 5. Rule: IMPLEMENTED_AND_TESTED requires at least one cited test file containing
    #    the name of an implementing module or evidence file name (grep check)
    for row in rows:
        if row["status"] == "IMPLEMENTED_AND_TESTED":
            # Extract test files cited in Evidence
            evidence_items = re.findall(r"`([^`]+)`", row["evidence"])
            test_files = [item.split("::")[0].strip() for item in evidence_items if item.startswith("tests/")]
            assert len(test_files) > 0, f"Row {row['id']} marked IMPLEMENTED_AND_TESTED has no test file cited"

            module_items = re.findall(r"`([^`]+)`", row["modules"])
            mod_names = {Path(m.strip()).name for m in module_items}
            mod_stems = {Path(m.strip()).stem for m in module_items}

            non_test_evidence = [item.strip() for item in evidence_items if not item.startswith("tests/")]
            ev_names = {Path(e).name for e in non_test_evidence}
            ev_stems = {Path(e).stem for e in non_test_evidence}

            search_tokens = mod_names | mod_stems | ev_names | ev_stems

            match_found = False
            for tf in test_files:
                tf_path = REPO_ROOT / tf
                assert tf_path.is_file(), f"Test file {tf} does not exist for {row['id']}"
                tf_text = tf_path.read_text(encoding="utf-8")
                if any(token in tf_text for token in search_tokens):
                    match_found = True
                    break

            assert match_found, (
                f"Rule violation for {row['id']}: marked IMPLEMENTED_AND_TESTED but cited test files {test_files} "
                f"do not contain any module or evidence name from {search_tokens}"
            )

    # 6. Path and test existence checks
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
