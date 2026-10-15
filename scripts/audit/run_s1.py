"""run_s1.py (Prompt 16 S1 Audit Execution Script).

Runs full S1 verification checks:
1. Baseline hash verification (61/61 protected files).
2. Pre-registration append-only verification across all commits.
3. S1 deliverables recheck (R2, R3, R4 deliverables).
4. Hash coverage audit with exact path matching.
5. Known limitations validation.
6. Overnight summary verification.
7. Full pytest suite.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_cmd(step_name: str, cmd_args: list[str]) -> None:
    print("=" * 80)
    print(f"STEP: {step_name}")
    print("COMMAND:", " ".join(cmd_args))
    print("=" * 80)
    res = subprocess.run(cmd_args, cwd=str(REPO_ROOT))
    if res.returncode != 0:
        print(f"\n[FAIL] Step '{step_name}' exited with code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)
    print(f"[PASS] Step '{step_name}' completed successfully.\n")


def main() -> None:
    py = sys.executable
    run_cmd("1. Verify All Hashes (61/61)", [py, "scripts/verify_all_hashes.py"])
    run_cmd("2. Verify Prereg Append-Only", [py, "scripts/verify/verify_prereg_append_only.py"])
    run_cmd("3. Recheck S1 Deliverables (R2/R3/R4)", [py, "scripts/verify/recheck_s1.py"])
    run_cmd("4. Audit Hash Coverage (Exact Path Matching)", [py, "scripts/audit_hash_coverage.py"])
    run_cmd("5. Known Limitations Verification", [py, "scripts/build_known_limitations.py"])
    run_cmd("6. Overnight Summary Verification", [py, "scripts/verify_overnight_summary.py"])
    run_cmd("7. Full Pytest Regression Suite", [py, "-m", "pytest", "-q"])
    print("=" * 80)
    print("ALL S1 AUDIT CHECKS PASSED SUCCESSFULLY (Exit 0)")
    print("=" * 80)


if __name__ == "__main__":
    main()
