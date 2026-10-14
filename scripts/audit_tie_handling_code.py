#!/usr/bin/env python3
"""Audit tie-handling code in src/c4 and mentions of tie in prereg/eval reports (Prompt 13 P2.1)."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def grep_file(path: Path, pattern: str) -> list[tuple[int, str]]:
    results = []
    regex = re.compile(pattern, re.IGNORECASE)
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if regex.search(line):
            results.append((idx, line))
    return results


def main() -> None:
    print("=" * 80)
    print("TIE-HANDLING CODE AUDIT (2.1)")
    print("=" * 80)

    # 1. Models in src/c4: src/c4/models/markov.py, src/c4/models/frequency.py, etc.
    c4_model_files = list((REPO_ROOT / "src" / "c4" / "models").glob("*.py"))
    print("\n--- Tie-Handling Code in src/c4/models/ ---")
    pat = r"tie|sorted\(|key=|sort"
    for mf in sorted(c4_model_files):
        matches = grep_file(mf, pat)
        rel = mf.relative_to(REPO_ROOT).as_posix()
        print(f"\nFile: {rel}")
        if matches:
            for lno, text in matches:
                print(f"  {rel}:{lno}: {text}")
        else:
            print("  (no match)")

    # 2. mentions in reports/prereg_7episode_design.md
    prereg_p = REPO_ROOT / "reports" / "prereg_7episode_design.md"
    prereg_matches = grep_file(prereg_p, r"\btie|\btied|\bties|\btie-break")
    print(f"\n--- Mentions in reports/prereg_7episode_design.md ---")
    if prereg_matches:
        for lno, text in prereg_matches:
            print(f"  reports/prereg_7episode_design.md:{lno}: {text}")
    else:
        print("  no match")

    # 3. mentions in reports/evaluation_report.md
    eval_p = REPO_ROOT / "reports" / "evaluation_report.md"
    eval_matches = grep_file(eval_p, r"\btie|\btied|\bties|\btie-break")
    print(f"\n--- Mentions in reports/evaluation_report.md ---")
    if eval_matches:
        for lno, text in eval_matches:
            print(f"  reports/evaluation_report.md:{lno}: {text}")
    else:
        print("  no match")


if __name__ == "__main__":
    main()
