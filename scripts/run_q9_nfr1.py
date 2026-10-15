"""run_q9_nfr1.py

Executes Q9b NFR1 timing measurement and verification:
- scripts/measure_nfr1.py
- scripts/verify_nfr1.py
Writes output to reports/audit/q14_Q9_output.txt.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "reports" / "audit" / "q14_Q9_output.txt"


def run_q9() -> None:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"Q9 NFR1 MEASUREMENT AND VERIFICATION RUN ({datetime.now(timezone.utc).isoformat()})")
    lines.append("=" * 80)

    # 1. Run measure_nfr1.py
    lines.append("\n--- [Step 1] Running scripts/measure_nfr1.py ---")
    res_measure = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "measure_nfr1.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_measure.stdout.strip())
    if res_measure.returncode != 0:
        lines.append(f"ERROR: measure_nfr1.py failed:\n{res_measure.stderr}")
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 2. Run verify_nfr1.py
    lines.append("\n--- [Step 2] Running scripts/verify_nfr1.py ---")
    res_verify = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify_nfr1.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_verify.stdout.strip())
    if res_verify.returncode != 0:
        lines.append(f"ERROR: verify_nfr1.py failed:\n{res_verify.stderr}")
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    lines.append("\n" + "=" * 80)
    lines.append("Q9 NFR1 RUN COMPLETED SUCCESSFULLY (ALL CRITERIA SATISFIED)")
    lines.append("=" * 80)

    report_text = "\n".join(lines) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    run_q9()
