#!/usr/bin/env python3
"""Audit prereg strings, headings, amendment hashes, and append-only diffs for Prompt 13 P1.4."""
from __future__ import annotations

import difflib
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREREG_PATH = REPO_ROOT / "reports" / "prereg_7episode_design.md"


def get_git_file(commit: str, rel_path: str) -> str:
    res = subprocess.run(["git", "show", f"{commit}:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Failed to read {commit}:{rel_path}: {res.stderr}")
    return res.stdout


def main() -> None:
    print("=" * 80)
    print("PREREG STRINGS AND APPEND-ONLY HISTORY AUDIT (1.4)")
    print("=" * 80)

    # 1. git log -S for the 6 strings
    search_strings = [
        "Stage 1 Data Build Directory and Processed Files",
        "Primary Evaluation Protocol",
        "Model Execution Rules",
        "Reporting Rules",
        "Episodes and Scenario Mapping",
        "returning 0 matches",
    ]

    print("\n--- git log --all -S<string> Across History ---")
    for s in search_strings:
        cmd = ["git", "log", "--all", "--format=%h %s", f"-S{s}", "--name-only"]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")
        out = res.stdout.strip()
        print(f"\n[Search String]: \"{s}\"")
        if out:
            print(out)
        else:
            print("  (0 commits found)")

    # 2. Working tree occurrences of the strings with line numbers and enclosing "## " heading
    print("\n--- Working-Tree Occurrences in reports/prereg_7episode_design.md ---")
    prereg_text = PREREG_PATH.read_text(encoding="utf-8")
    prereg_lines = prereg_text.splitlines()

    current_h2 = "(before any ## heading)"
    line_h2_map = {}
    for idx, l in enumerate(prereg_lines, 1):
        if l.startswith("## "):
            current_h2 = l.strip()
        line_h2_map[idx] = current_h2

    for s in search_strings:
        found = False
        print(f"\nOccurrences of \"{s}\":")
        for idx, l in enumerate(prereg_lines, 1):
            if s in l:
                found = True
                print(f"  Line {idx} [{line_h2_map[idx]}]: {l}")
        if not found:
            print("  (None found in working tree)")

    # 3. grep -n "^## " of the prereg
    print("\n--- grep -n \"^## \" reports/prereg_7episode_design.md ---")
    h2_positions = []
    for idx, l in enumerate(prereg_lines, 1):
        if l.startswith("## "):
            print(f"  {idx:4d}: {l}")
            h2_positions.append((idx, l.strip()))

    # 4. SHA-256 of each Amendment block (1-5)
    print("\n--- SHA-256 of Amendment Blocks (1 through 5) ---")
    # Find start and end of each amendment block
    # Headings look like: "## Amendment 1 ...", "## Amendment 2 ...", etc.
    amend_blocks = {}
    for i, (l_no, h_title) in enumerate(h2_positions):
        if "Amendment" in h_title:
            # find end: next h2 line or end of file
            next_l_no = h2_positions[i + 1][0] if i + 1 < len(h2_positions) else len(prereg_lines) + 1
            # lines [l_no - 1 : next_l_no - 1]
            block_text = "\n".join(prereg_lines[l_no - 1 : next_l_no - 1]).strip() + "\n"
            sha = hashlib.sha256(block_text.encode("utf-8")).hexdigest()
            print(f"| {h_title[:45]} | Lines {l_no}-{next_l_no-1} | SHA-256: `{sha}` |")

    # 5. Re-run append-only table for consecutive pairs:
    # 2cf7786, 340c788, 3a6b306, b9ab249, fdc9b17, 88c26ba, 4e9d663, 42e941a
    commits_series = ["2cf7786", "340c788", "3a6b306", "b9ab249", "fdc9b17", "88c26ba", "4e9d663", "42e941a"]
    print("\n--- Consecutive Pair Append-Only Audit Across All 8 Commits ---")
    print(f"| Commit Pair | Added Lines | Removed/Changed Lines | Status |")
    print(f"|:---|:---:|:---:|:---:|")

    for i in range(len(commits_series) - 1):
        c1, c2 = commits_series[i], commits_series[i + 1]
        t1 = get_git_file(c1, "reports/prereg_7episode_design.md").splitlines()
        t2 = get_git_file(c2, "reports/prereg_7episode_design.md").splitlines()

        diff = list(difflib.ndiff(t1, t2))
        added = sum(1 for line in diff if line.startswith("+ "))
        removed = sum(1 for line in diff if line.startswith("- "))

        status = "APPEND-ONLY" if removed == 0 else f"VIOLATION ({removed} removed)"
        print(f"| `{c1}` -> `{c2}` | {added} | {removed} | **{status}** |")


if __name__ == "__main__":
    main()
