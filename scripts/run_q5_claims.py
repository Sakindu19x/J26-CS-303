"""run_q5_claims.py

Runs Q5 claims map rebuild, independent verification, mutation sweep, and tests.
Writes output to reports/audit/q14_Q5_output.txt.
"""
from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "reports" / "audit" / "q14_Q5_output.txt"


def run_q5() -> None:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append(f"Q5 CLAIMS MAP REBUILD & VERIFICATION ({datetime.now(timezone.utc).isoformat()})")
    lines.append("=" * 80)

    # 1. Build
    lines.append("\n--- [Step 1] Running scripts/build_claims_map.py ---")
    res_b = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "build_claims_map.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_b.stdout.strip())
    if res_b.returncode != 0:
        lines.append(f"ERROR: build failed:\n{res_b.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 2. Verify
    lines.append("\n--- [Step 2] Running scripts/verify_claims_map.py ---")
    res_v = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "verify_claims_map.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_v.stdout.strip())
    if res_v.returncode != 0:
        lines.append(f"ERROR: verify failed:\n{res_v.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 3. Mutation sweep
    lines.append("\n--- [Step 3] Running scripts/mutation_sweep_claims_map.py ---")
    res_m = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "mutation_sweep_claims_map.py")], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_m.stdout.strip())
    if res_m.returncode != 0:
        lines.append(f"ERROR: mutation sweep failed:\n{res_m.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    # 4. Tests
    lines.append("\n--- [Step 4] Running pytest tests/test_claims_map.py ---")
    res_t = subprocess.run([sys.executable, "-m", "pytest", "tests/test_claims_map.py", "-v"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(res_t.stdout.strip())
    if res_t.returncode != 0:
        lines.append(f"ERROR: tests failed:\n{res_t.stderr}")
        OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        sys.exit(1)

    lines.append("\n" + "=" * 80)
    lines.append("Q5 CLAIMS MAP VERIFICATION & MUTATION SWEEPS ALL PASSED (EXIT 0)")
    lines.append("=" * 80)

    report_text = "\n".join(lines) + "\n"
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(report_text, encoding="utf-8")
    print(report_text)


if __name__ == "__main__":
    run_q5()
