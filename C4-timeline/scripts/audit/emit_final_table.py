#!/usr/bin/env python3
"""Emit Final Execution Table for Prompt 16 (Rule G1).

Reads reports/overnight_ledger.md and outputs ONLY the markdown table.
Never hardcodes or retypes any number or hash.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_PATH = REPO_ROOT / "reports" / "overnight_ledger.md"


def main() -> None:
    if not LEDGER_PATH.is_file():
        sys.exit(f"Ledger file not found: {LEDGER_PATH}")

    content = LEDGER_PATH.read_text(encoding="utf-8")
    table_lines: list[str] = []
    in_table = False

    for line in content.splitlines():
        trimmed = line.strip()
        if trimmed.startswith("|") and ("Part" in trimmed or "---" in trimmed or "**" in trimmed):
            in_table = True
            table_lines.append(trimmed)
        elif in_table and not trimmed.startswith("|"):
            break

    if not table_lines:
        sys.exit("No markdown table found in ledger.")

    print("\n".join(table_lines))


if __name__ == "__main__":
    main()
