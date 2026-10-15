#!/usr/bin/env python3
"""Run command and log output with standardized audit header (Rule G4).

Header structure:
================================================================================
AUDIT LOG HEADER
Command    : <command>
Exit Code  : <exit_code>
Git HEAD   : <git_head>
UTC Start  : <utc_start>
UTC End    : <utc_end>
================================================================================
<output>
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def get_git_head() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else "UNKNOWN"


def main() -> int:
    # Accept either:
    # run_logged.py <output_file> <command...>
    # or run_logged.py --output <output_file> -- <command...>
    if len(sys.argv) < 3:
        print("Usage: run_logged.py <output_path> <cmd...>", file=sys.stderr)
        print("   or: run_logged.py --output <output_path> -- <cmd...>", file=sys.stderr)
        return 2

    if sys.argv[1] == "--output":
        output_path = Path(sys.argv[2])
        cmd = sys.argv[4:] if sys.argv[3] == "--" else sys.argv[3:]
    else:
        output_path = Path(sys.argv[1])
        cmd = sys.argv[2:]

    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    git_head = get_git_head()
    utc_start = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    cmd_str = " ".join(cmd)
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    utc_end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    header = (
        "================================================================================\n"
        "AUDIT LOG HEADER\n"
        f"Command    : {cmd_str}\n"
        f"Exit Code  : {res.returncode}\n"
        f"Git HEAD   : {git_head}\n"
        f"UTC Start  : {utc_start}\n"
        f"UTC End    : {utc_end}\n"
        "================================================================================\n"
    )

    full_log = header + res.stdout
    if res.stderr:
        if not full_log.endswith("\n"):
            full_log += "\n"
        full_log += "--- STDERR ---\n" + res.stderr

    output_path.write_text(full_log, encoding="utf-8")
    print(f"[run_logged] Wrote {output_path} (Exit {res.returncode})")
    print(res.stdout, end="")
    if res.stderr:
        print(res.stderr, file=sys.stderr, end="")

    return res.returncode


if __name__ == "__main__":
    sys.exit(main())
