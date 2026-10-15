"""run_q3_pipeline.py

Executes Q3 pipeline steps, runs all validations, and writes output to reports/audit/q14_Q3_output.txt.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "reports" / "audit" / "q14_Q3_output.txt"


def run_command(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = (res.stdout or "") + ("\n" + res.stderr if res.stderr else "")
    return res.returncode, out.strip()


def main() -> None:
    lines = []
    lines.append("=" * 80)
    lines.append("Q3 PIPELINE EXECUTION OUTPUT")
    lines.append("=" * 80)

    # 1. build_amendment8.py
    code, out = run_command([sys.executable, "scripts/build_amendment8.py"])
    lines.append(f"[Step 1: build_amendment8.py] Exit: {code}")
    lines.append(out)
    assert code == 0, "build_amendment8 failed"

    # 2. verify_exploratory_tactic_conditioned.py
    code, out = run_command([sys.executable, "scripts/verify_exploratory_tactic_conditioned.py"])
    lines.append(f"\n[Step 2: verify_exploratory_tactic_conditioned.py] Exit: {code}")
    lines.append(out)
    assert code == 0, "verify_exploratory_tactic_conditioned failed"

    # 3. pytest tests/test_exploratory_tactic_conditioned.py
    code, out = run_command([sys.executable, "-m", "pytest", "tests/test_exploratory_tactic_conditioned.py", "-v"])
    lines.append(f"\n[Step 3: pytest test_exploratory_tactic_conditioned.py] Exit: {code}")
    lines.append(out)
    assert code == 0, "pytest failed"

    # 4. Exploratory mutation sweep
    code, out = run_command([
        sys.executable, "-c",
        "from pathlib import Path; from scripts.mutation_sweep import sweep_report_numeric, is_exempt_exploratory_tactic_conditioned, get_check_suites_7ep_inference; "
        "_, _, _, _, _, _, _, _, exp_checks = get_check_suites_7ep_inference(); "
        "res = sweep_report_numeric('exploratory_tactic_conditioned_report.md', Path('reports/7ep/exploratory_tactic_conditioned_report.md'), exp_checks, is_exempt_exploratory_tactic_conditioned); "
        "print('Exploratory Mutation Sweep Result:', res); "
        "assert res['undetected'] == 0; assert res['detected'] == 107"
    ])
    lines.append(f"\n[Step 4: Exploratory Mutation Sweep] Exit: {code}")
    lines.append(out)
    assert code == 0, "mutation sweep failed"

    # 5. verify_all_hashes.py
    code, out = run_command([sys.executable, "scripts/verify_all_hashes.py"])
    lines.append(f"\n[Step 5: verify_all_hashes.py] Exit: {code}")
    lines.append(out)
    assert code == 0, "verify_all_hashes failed"

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Q3 pipeline finished successfully. Output written to {OUTPUT_FILE} [PASS]")


if __name__ == "__main__":
    main()
