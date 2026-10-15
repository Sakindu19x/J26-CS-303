"""run_q6_summary.py

Runs Q6 summary and decisions rebuild, verification, and mutation sweep.
Writes output to reports/audit/q14_Q6_output.txt.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "reports" / "audit" / "q14_Q6_output.txt"


def run_q6() -> None:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"Q6 OVERNIGHT SUMMARY & DECISIONS REBUILD ({datetime.now(timezone.utc).isoformat()})")
    lines.append("=" * 80)

    # 1. Append corrections
    lines.append("\n--- [Step 1] Running scripts/append_q6_corrections.py ---")
    res_a = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "append_q6_corrections.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_a.stdout.strip())
    if res_a.returncode != 0:
        lines.append(f"ERROR: append failed:\n{res_a.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 2. Build summary
    lines.append("\n--- [Step 2] Running scripts/build_overnight_summary.py ---")
    res_b = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "build_overnight_summary.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_b.stdout.strip())
    if res_b.returncode != 0:
        lines.append(f"ERROR: build failed:\n{res_b.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 3. Verify
    lines.append("\n--- [Step 3] Running scripts/verify_overnight_summary.py ---")
    res_v = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify_overnight_summary.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_v.stdout.strip())
    if res_v.returncode != 0:
        lines.append(f"ERROR: verify failed:\n{res_v.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 4. Mutation sweep
    lines.append("\n--- [Step 4] Running scripts/mutation_sweep_overnight_summary.py ---")
    res_m = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "mutation_sweep_overnight_summary.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_m.stdout.strip())
    if res_m.returncode != 0:
        lines.append(f"ERROR: mutation sweep failed:\n{res_m.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 5. Tests
    lines.append("\n--- [Step 5] Running pytest tests/test_overnight_summary.py ---")
    res_t = subprocess.run([sys.executable, "-m", "pytest", "tests/test_overnight_summary.py", "-v"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_t.stdout.strip())
    if res_t.returncode != 0:
        lines.append(f"ERROR: tests failed:\n{res_t.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    lines.append("\n" + "=" * 80)
    lines.append("Q6 SUMMARY & DECISIONS VERIFICATION ALL PASSED (EXIT 0)")
    lines.append("=" * 80)

    report_text = "\n".join(lines) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    run_q6()
