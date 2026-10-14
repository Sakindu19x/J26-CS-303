#!/usr/bin/env python3
"""Print a file with line numbers for Prompt 13 verbatim output compliance."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Print a file with line numbers.")
    parser.add_argument("file", type=str, help="Path to the file to print")
    parser.add_argument("--start", type=int, default=1, help="Starting line (1-based, inclusive)")
    parser.add_argument("--end", type=int, default=None, help="Ending line (1-based, inclusive)")
    args = parser.parse_args()

    p = Path(args.file)
    if not p.is_file():
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()

    start = max(1, args.start)
    end = min(len(lines), args.end) if args.end is not None else len(lines)

    for i in range(start, end + 1):
        print(f"{i:5d} | {lines[i - 1]}")


if __name__ == "__main__":
    main()
