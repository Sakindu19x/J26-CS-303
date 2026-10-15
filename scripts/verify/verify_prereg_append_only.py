#!/usr/bin/env python3
"""verify_prereg_append_only.py (Prompt 16 S1c).

Verifies that for every git commit touching reports/prereg_7episode_design.md,
the previous commit's LF-normalised content is an exact prefix of the subsequent commit's content.
Also verifies that the current working tree content begins with the latest committed content.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREREG_PATH = REPO_ROOT / "reports" / "prereg_7episode_design.md"


def get_prereg_commits() -> list[tuple[str, str, str]]:
    """Return chronological list of (commit_sha, author_date, subject)."""
    res = subprocess.run(
        ["git", "log", "--reverse", "--format=%H|%aI|%s", "--", "reports/prereg_7episode_design.md"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise RuntimeError("Failed to query git log for prereg commits")
    commits: list[tuple[str, str, str]] = []
    for line in res.stdout.strip().splitlines():
        if line and "|" in line:
            parts = line.split("|", 2)
            if len(parts) == 3:
                commits.append((parts[0], parts[1], parts[2]))
    return commits


def get_blob_lf(ref: str) -> str:
    res = subprocess.run(
        ["git", "cat-file", "-p", f"{ref}:reports/prereg_7episode_design.md"],
        cwd=str(REPO_ROOT),
        capture_output=True,
    )
    if res.returncode != 0:
        raise RuntimeError(f"Failed to fetch git blob: {ref}")
    return res.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")


def main() -> int:
    print("=" * 80)
    print("PRE-REGISTRATION APPEND-ONLY INTEGRITY VERIFIER")
    print("=" * 80)

    commits = get_prereg_commits()
    print(f"Discovered {len(commits)} commits touching reports/prereg_7episode_design.md\n")

    prev_sha: str | None = None
    prev_text: str | None = None

    for idx, (sha, date_str, msg) in enumerate(commits, start=1):
        cur_text = get_blob_lf(sha)
        if prev_text is not None:
            # Check LF-normalised prefix modulo trailing newline normalization
            prev_clean = prev_text.rstrip()
            if not cur_text.startswith(prev_clean):
                print(f"[FAIL] Step {idx}: Commit {sha[:10]} is NOT an exact append of {prev_sha[:10]}!")
                print(f"       Previous length: {len(prev_clean)} chars")
                print(f"       Current length:  {len(cur_text)} chars")
                # Find mismatch index
                for i in range(min(len(prev_clean), len(cur_text))):
                    if prev_clean[i] != cur_text[i]:
                        print(f"       First mismatch at character {i}:")
                        print(f"       Expected: {repr(prev_clean[max(0, i-20):i+20])}")
                        print(f"       Actual:   {repr(cur_text[max(0, i-20):i+20])}")
                        break
                return 1
            added_chars = len(cur_text) - len(prev_clean)
            print(f"[{idx}/{len(commits)}] {sha[:10]} ({date_str[:10]}): +{added_chars:,} chars appended -> [PASS]")
        else:
            print(f"[{idx}/{len(commits)}] {sha[:10]} ({date_str[:10]}): Initial registration ({len(cur_text):,} chars) -> [PASS]")

        prev_sha = sha
        prev_text = cur_text

    # Working tree verification
    if PREREG_PATH.is_file():
        wt_text = PREREG_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
        assert prev_text is not None
        prev_clean = prev_text.rstrip()
        if not wt_text.startswith(prev_clean):
            print(f"\n[FAIL] Working tree file is NOT an exact append of committed HEAD ({prev_sha[:10]})!")
            return 1
        added_wt = len(wt_text) - len(prev_clean)
        print(f"\n[Working Tree Check] Working tree has +{added_wt:,} chars appended relative to HEAD -> [PASS]")

    print("\n" + "=" * 80)
    print("ALL COMMITS CONFIRMED 100% APPEND-ONLY AND PREFIX-COMPLIANT")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
