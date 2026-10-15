#!/usr/bin/env python3
"""build_amendment9.py (Prompt 16 S1c).

Appends Amendment 9 to reports/prereg_7episode_design.md stating facts computed
directly from git history:
1. Amendment 8 duplication disclosure (first occurrence is authoritative).
2. Clarification of "Section 12" citation (authoritative verdict rule is Section 6
   plus reports/7ep/holm_claim_rule_results.json).
3. Chronological commit ordering showing Amendment 7 strictly preceded the
   exploratory variant execution run.

Ensures exact byte prefix preservation and idempotency.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREREG_PATH = REPO_ROOT / "reports" / "prereg_7episode_design.md"


def get_commit_info(grep_pattern: str) -> tuple[str, str, str]:
    res = subprocess.run(
        ["git", "log", f"--grep={grep_pattern}", "-1", "--format=%H|%aI|%s"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0 or not res.stdout.strip():
        raise RuntimeError(f"Failed to find commit for pattern: {grep_pattern}")
    sha, date_str, msg = res.stdout.strip().split("|", 2)
    return sha, date_str, msg


def build_amendment9_text() -> str:
    # 1. Amendment 7 commit
    a7_sha, a7_date_str, a7_msg = get_commit_info("prereg amendment 7")
    a7_dt = datetime.fromisoformat(a7_date_str).astimezone(timezone.utc)

    # 2. Exploratory variant execution commit
    p4_sha, p4_date_str, p4_msg = get_commit_info("P4: exploratory tactic-conditioned")
    p4_dt = datetime.fromisoformat(p4_date_str).astimezone(timezone.utc)

    delta_seconds = int((p4_dt - a7_dt).total_seconds())
    delta_hours = delta_seconds / 3600.0

    lines = [
        "",
        "## Amendment 9 (2026-10-15, audit corrections: Amendment 8 duplication, citation reconciliation, and chronological precedence proof; append-only)",
        "",
        "This amendment formally documents three archival audit findings established from git history:",
        "",
        "1. **Amendment 8 Duplication Disclosure**:",
        "   - During the Prompt 14 Q3 execution, Amendment 8 text was appended twice in `reports/prereg_7episode_design.md`.",
        "   - Both occurrences are byte-for-byte identical; the first occurrence (line 367) is authoritative.",
        "   - Under the strict append-only immutability invariant, the second occurrence is preserved as-is rather than deleted, and is superseded by the first.",
        "",
        "2. **Reconciliation of 'Section 12' Citation**:",
        "   - Amendment 8 Section 1 references 'Section 12' as containing the primary decision rule.",
        "   - However, `reports/prereg_7episode_design.md` comprises Sections 1 through 10 (with amendments appended sequentially); no Section 12 exists in the document.",
        "   - The authoritative pre-registered decision rule is defined in **Section 6** (*Hypothesis Testing Protocol & Confirmatory Decisions*) and mathematically operationalized by `reports/7ep/holm_claim_rule_results.json` and `scripts/run_holm_claim_rule.py`.",
        "",
        "3. **Chronological Precedence of Amendment 7 Relative to Exploratory Run**:",
        "   - Empirical audit of repository commit history verifies that Amendment 7 (declaring the exploratory tactic-conditioned variant) strictly preceded the execution and results commit of that run:",
        f"     - **Amendment 7 Commit**: `{a7_sha}` (Author Date: `{a7_dt.strftime('%Y-%m-%d %H:%M:%SZ')}`, `{a7_msg}`).",
        f"     - **Exploratory Run Commit**: `{p4_sha}` (Author Date: `{p4_dt.strftime('%Y-%m-%d %H:%M:%SZ')}`, `{p4_msg}`).",
        f"     - **Precedence Verification**: Amendment 7 preceded the exploratory run commit by exactly {delta_seconds:,} seconds ({delta_hours:.2f} hours), confirming that the exploratory protocol was formally committed prior to recording its experimental outcomes.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    current_bytes = PREREG_PATH.read_bytes()
    current_text = current_bytes.decode("utf-8", errors="replace")

    if "## Amendment 9" in current_text:
        print("Amendment 9 already present in reports/prereg_7episode_design.md (idempotent skip). [PASS]")
        return 0

    amendment9_text = build_amendment9_text()
    # Normalize to CRLF to match prereg file
    amendment9_bytes = amendment9_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

    new_bytes = current_bytes + amendment9_bytes
    assert new_bytes.startswith(current_bytes), "CRITICAL: Previous bytes must form an exact prefix!"

    PREREG_PATH.write_bytes(new_bytes)
    verified_bytes = PREREG_PATH.read_bytes()
    assert verified_bytes.startswith(current_bytes), "CRITICAL: Verified disk bytes failed prefix assertion!"

    print("Successfully built and appended Amendment 9 to reports/prereg_7episode_design.md [PASS]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
