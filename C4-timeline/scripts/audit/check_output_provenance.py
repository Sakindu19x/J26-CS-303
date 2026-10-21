#!/usr/bin/env python3
"""scripts/audit/check_output_provenance.py (Rule G4).

Verifies that output log files under reports/audit produced in Prompt 16
(and future runs) were created via scripts/audit/run_logged.py with the
standardized AUDIT LOG HEADER.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "reports" / "audit"

EXPECTED_HEADER_LINES = [
    "================================================================================",
    "AUDIT LOG HEADER",
]


def check_file(path: Path) -> list[str]:
    errors = []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(lines) < 8:
        return [f"{path.name}: File has fewer than 8 lines; cannot contain valid audit header"]

    if lines[0] != EXPECTED_HEADER_LINES[0]:
        errors.append(f"{path.name}: Line 1 must be '{EXPECTED_HEADER_LINES[0]}', got '{lines[0]}'")
    if lines[1] != EXPECTED_HEADER_LINES[1]:
        errors.append(f"{path.name}: Line 2 must be '{EXPECTED_HEADER_LINES[1]}', got '{lines[1]}'")

    header_text = "\n".join(lines[:8])
    for required_field in ["Command    :", "Exit Code  :", "Git HEAD   :", "UTC Start  :", "UTC End    :"]:
        if required_field not in header_text:
            errors.append(f"{path.name}: Header missing required field '{required_field}'")

    return errors


def main() -> int:
    # Check all files matching q16_*_output*.txt directly under reports/audit
    s_output_files = sorted(AUDIT_DIR.glob("q16_*_output*.txt"))
    if not s_output_files:
        print("[FAIL] No q16_*_output*.txt files found in reports/audit!")
        return 1

    all_errors = []
    for f in s_output_files:
        errs = check_file(f)
        if errs:
            all_errors.extend(errs)
        else:
            print(f"[PASS] Verified provenance header: {f.name}")

    if all_errors:
        print("\n[FAIL] Provenance check failed:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"\n[PASS] All {len(s_output_files)} Prompt 16 output files verified with valid run_logged headers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
