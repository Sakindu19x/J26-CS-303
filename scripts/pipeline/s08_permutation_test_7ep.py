#!/usr/bin/env python3
"""Stage 8: Permutation Test (7 Episodes, B=1000).

Canonical implementation preserved at scripts/run_permutation_test_7ep.py
(name embedded in pre-registration protocol reports/prereg_7episode_design.md).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "scripts" / "run_permutation_test_7ep.py"

if __name__ == "__main__":
    res = subprocess.run([sys.executable, str(TARGET)] + sys.argv[1:], cwd=str(REPO_ROOT))
    sys.exit(res.returncode)
