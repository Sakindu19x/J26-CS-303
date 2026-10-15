#!/usr/bin/env python3
"""Run S0 baseline status checks."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    print("================================================================================")
    print("PROMPT 16 - S0 INITIAL REPOSITORY AND TEST SUITE AUDIT")
    print("================================================================================")

    # 1. Git Status
    print("\n--- 1. Git Status ---")
    st = subprocess.run(["git", "status"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(st.stdout)

    # 2. verify_all_hashes
    print("\n--- 2. Hash Verification (verify_all_hashes.py) ---")
    vh = subprocess.run([sys.executable, "scripts/verify_all_hashes.py"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(vh.stdout)
    if vh.stderr:
        print("STDERR:\n" + vh.stderr)

    # 3. Full pytest count
    print("\n--- 3. Full Pytest Suite ---")
    pt = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(pt.stdout)
    if pt.stderr:
        print("STDERR:\n" + pt.stderr)

    code = 0 if (vh.returncode == 0 and pt.returncode == 0) else 1
    print(f"\nS0 Overall Status: {'PASS' if code == 0 else 'FAIL'}")
    return code


if __name__ == "__main__":
    sys.exit(main())
