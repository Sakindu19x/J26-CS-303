#!/usr/bin/env python3
"""Stage 17: Explainable Prediction Records Generation.

Canonical implementation preserved at scripts/build_prediction_records.py
(name embedded in reports/7ep/requirements_trace.md).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "scripts" / "build_prediction_records.py"

if __name__ == "__main__":
    res = subprocess.run([sys.executable, str(TARGET)] + sys.argv[1:], cwd=str(REPO_ROOT))
    sys.exit(res.returncode)
