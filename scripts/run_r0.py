"""Run R0 setup and audit output generation for Prompt 15."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

def main():
    lines = []
    lines.append("=" * 80)
    lines.append("PROMPT 15 - R0 INITIAL AUDIT")
    lines.append("=" * 80)

    # HEAD
    res_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    head = res_head.stdout.strip()
    lines.append(f"HEAD at start: {head}")

    # git status
    res_status = subprocess.run(["git", "status", "--short"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append("\ngit status --short:")
    lines.append(res_status.stdout if res_status.stdout.strip() else "(clean)")

    # verify_all_hashes
    res_v = subprocess.run([PYTHON, "scripts/verify_all_hashes.py"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    lines.append(f"\nverify_all_hashes exit code: {res_v.returncode}")
    lines.append(res_v.stdout.strip())

    # pytest count
    res_pt = subprocess.run([PYTHON, "-m", "pytest", "--collect-only", "-q"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    collect_lines = [l for l in res_pt.stdout.splitlines() if "collected" in l or "test" in l]
    lines.append(f"\npytest collection:")
    lines.append("\n".join(collect_lines))

    out_file = REPO_ROOT / "reports" / "audit" / "q15_R0_output.txt"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_file}")

if __name__ == "__main__":
    main()
