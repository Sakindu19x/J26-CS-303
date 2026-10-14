#!/usr/bin/env python3
"""Update overnight ledger for Prompt 13 (G7 compliance)."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_PATH = REPO_ROOT / "reports" / "overnight_ledger.md"


def get_git_head() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    if res.returncode != 0:
        return "UNKNOWN_COMMIT"
    return res.stdout.strip()


def run_verify_hashes() -> int:
    script = REPO_ROOT / "scripts" / "verify_all_hashes.py"
    res = subprocess.run([sys.executable, str(script)], cwd=str(REPO_ROOT), capture_output=True, text=True)
    return res.returncode


def run_pytest_counts() -> tuple[int, int]:
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = res.stdout + "\n" + res.stderr
    # Look for patterns like "151 passed" or "149 passed, 2 failed"
    m_pass = re.search(r"(\d+)\s+passed", out)
    m_fail = re.search(r"(\d+)\s+failed", out)
    passed = int(m_pass.group(1)) if m_pass else 0
    failed = int(m_fail.group(1)) if m_fail else 0
    return passed, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="Update overnight ledger.")
    parser.add_argument("part", type=str, help="Part ID (e.g., P0, P1, P2...)")
    parser.add_argument("--blocked", type=str, default=None, help="If blocked, exact error message")
    parser.add_argument("--hashes-exit", type=int, default=None, help="Override verify_all_hashes exit code")
    parser.add_argument("--pytest-passed", type=int, default=None, help="Override pytest passed count")
    parser.add_argument("--pytest-failed", type=int, default=None, help="Override pytest failed count")
    args = parser.parse_args()

    head = get_git_head()
    utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if args.blocked:
        hashes_code = args.hashes_exit if args.hashes_exit is not None else 1
        passed = args.pytest_passed if args.pytest_passed is not None else 0
        failed = args.pytest_failed if args.pytest_failed is not None else 1
        status_str = f"BLOCKED: {args.blocked}"
    else:
        hashes_code = args.hashes_exit if args.hashes_exit is not None else run_verify_hashes()
        if args.pytest_passed is not None and args.pytest_failed is not None:
            passed, failed = args.pytest_passed, args.pytest_failed
        else:
            passed, failed = run_pytest_counts()
        status_str = "PASS" if hashes_code == 0 and failed == 0 else f"FAIL (hashes={hashes_code}, failed={failed})"

    # Ensure ledger file exists
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not LEDGER_PATH.exists():
        header = (
            "# Overnight Execution Ledger\n\n"
            "| Part | Git HEAD (SHA) | verify_all_hashes Exit | Pytest Passed | Pytest Failed | Status | UTC Timestamp |\n"
            "|:---|:---|:---:|:---:|:---:|:---|:---:|\n"
        )
        LEDGER_PATH.write_text(header, encoding="utf-8")

    row = f"| {args.part} | `{head}` | {hashes_code} | {passed} | {failed} | {status_str} | {utc_time} |\n"
    with open(LEDGER_PATH, "a", encoding="utf-8") as f:
        f.write(row)

    print(f"Updated ledger for {args.part}:")
    print(f"  HEAD: {head}")
    print(f"  verify_all_hashes exit: {hashes_code}")
    print(f"  pytest passed/failed: {passed} / {failed}")
    print(f"  status: {status_str}")
    print(f"  UTC: {utc_time}")


if __name__ == "__main__":
    main()
