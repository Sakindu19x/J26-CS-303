"""run_q8_dashboard.py

Runs Q8 dashboard screenshot re-capture, verification, and tests.
Writes output to reports/audit/q14_Q8_output.txt.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "reports" / "audit" / "q14_Q8_output.txt"


def run_q8() -> None:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"Q8 DASHBOARD SCRIPTS & RE-CAPTURE ({datetime.now(timezone.utc).isoformat()})")
    lines.append("=" * 80)

    # 1. Run capture
    lines.append("\n--- [Step 1] Running scripts/capture_dashboard_screenshots.py ---")
    res_c = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "capture_dashboard_screenshots.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_c.stdout.strip())
    if res_c.returncode != 0:
        lines.append(f"ERROR: capture failed:\n{res_c.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 2. Run tests
    lines.append("\n--- [Step 2] Running pytest tests/test_dashboard_q8.py ---")
    res_t = subprocess.run([sys.executable, "-m", "pytest", "tests/test_dashboard_q8.py", "-v"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_t.stdout.strip())
    if res_t.returncode != 0:
        lines.append(f"ERROR: tests failed:\n{res_t.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    lines.append("\n" + "=" * 80)
    lines.append("Q8 DASHBOARD VERIFICATION & RE-CAPTURE ALL PASSED (EXIT 0)")
    lines.append("=" * 80)

    report_text = "\n".join(lines) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    run_q8()
