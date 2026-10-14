#!/usr/bin/env python3
"""Check full-B (B=1000) reproducibility of permutation test v2.1 across two complete runs."""

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "processed" / "permutation_v2_null_distribution.csv"
JSON_PATH = REPO_ROOT / "reports" / "permutation_test_v2_report.json"
MD_PATH = REPO_ROOT / "reports" / "permutation_test_v2_report.md"


def get_hashes() -> dict[str, str]:
    return {
        "csv": hashlib.sha256(CSV_PATH.read_bytes()).hexdigest(),
        "json": hashlib.sha256(JSON_PATH.read_bytes()).hexdigest(),
        "md": hashlib.sha256(MD_PATH.read_bytes()).hexdigest(),
    }


def main():
    print("=" * 80)
    print("CHECKING FULL-B (B=1000) PERMUTATION TEST v2.1 REPRODUCIBILITY")
    print("=" * 80)

    # Run 1
    print("\n--- Running Permutation Test v2.1 (Run 1) ---")
    t0 = time.time()
    res1 = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "run_permutation_test_v2.py")], capture_output=True, text=True)
    if res1.returncode != 0:
        print("Run 1 failed:\n", res1.stderr)
        sys.exit(1)
    print(f"Run 1 completed in {time.time() - t0:.2f}s.")
    hashes_run1 = get_hashes()

    # Run 2
    print("\n--- Running Permutation Test v2.1 (Run 2) ---")
    t0 = time.time()
    res2 = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "run_permutation_test_v2.py")], capture_output=True, text=True)
    if res2.returncode != 0:
        print("Run 2 failed:\n", res2.stderr)
        sys.exit(1)
    print(f"Run 2 completed in {time.time() - t0:.2f}s.")
    hashes_run2 = get_hashes()

    # Compare
    print("\n=== Full-B Reproducibility Comparison ===")
    all_pass = True
    print("| Artifact | Run 1 SHA-256 | Run 2 SHA-256 | Status |")
    print("|:---|:---|:---|:---:|")
    for name in ["csv", "json", "md"]:
        h1 = hashes_run1[name]
        h2 = hashes_run2[name]
        status = "PASS" if h1 == h2 else "FAIL"
        if h1 != h2:
            all_pass = False
        print(f"| {name.upper()} | `{h1}` | `{h2}` | **{status}** |")

    overall = "PASS" if all_pass else "FAIL"
    print(f"\nOverall Result: {overall}")
    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
