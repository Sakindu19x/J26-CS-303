#!/usr/bin/env python3
"""Automate Prompt 15 - R7 FINALISE.

Execution Order:
1. Re-run all verifiers and mutation sweeps -> reports/audit/q15_R7_sweeps.txt
2. Pytest through update_ledger.py R7 -> appends R7 to reports/overnight_ledger.md
3. reproduce_all.py --verify-only -> reports/audit/q15_R7_output.txt
4. Rebuild viva_pack (reads duration from q15_R7_output.txt) and verify
5. Rebuild overnight_summary (reads updated ledger) and verify
6. Run audit_hash_coverage.py -> reports/audit/hash_coverage_exceptions.md
7. Record git log and tags to reports/audit/q15_R7_git.txt
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = str(Path(sys.executable).resolve())


def run_cmd(cmd: list[str], desc: str) -> tuple[int, str]:
    print(f"[*] Running: {desc}...")
    t0 = time.perf_counter()
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    elapsed = time.perf_counter() - t0
    out = res.stdout + ("\n--- STDERR ---\n" + res.stderr if res.stderr else "")
    status = "PASS" if res.returncode == 0 else f"FAIL (exit {res.returncode})"
    print(f"    -> [{status}] ({elapsed:.2f}s)")
    if res.returncode != 0:
        print(out[-1000:] if len(out) > 1000 else out)
    return res.returncode, out


def main() -> int:
    print("=" * 80)
    print("PROMPT 15 - R7 FINALISE AUTOMATION")
    print("=" * 80)

    sweeps_log: list[str] = [
        "=" * 80,
        "PROMPT 15 - R7 VERIFIERS AND MUTATION SWEEPS AUDIT LOG",
        f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        "=" * 80,
    ]

    # 1. Mutation sweeps
    mutation_scripts = [
        ("Base Mutation Sweep", [PYTHON, "scripts/mutation_sweep.py"]),
        ("Claims Map Mutation Sweep", [PYTHON, "scripts/mutation_sweep_claims_map.py"]),
        ("Requirements Trace Mutation Sweep", [PYTHON, "scripts/mutation_sweep_requirements_trace.py"]),
        ("Overnight Summary Mutation Sweep", [PYTHON, "scripts/mutation_sweep_overnight_summary.py"]),
    ]

    for desc, cmd in mutation_scripts:
        code, out = run_cmd(cmd, desc)
        sweeps_log.append(f"\n--- {desc} (Exit {code}) ---\n{out}")
        if code != 0:
            print(f"CRITICAL: {desc} failed!")
            return 1

    # 2. Verifiers
    from reproduce_all import VERIFIERS
    for name, cmd in VERIFIERS:
        code, out = run_cmd(cmd, f"Verifier: {name}")
        sweeps_log.append(f"\n--- Verifier: {name} (Exit {code}) ---\n{out}")
        if code != 0:
            print(f"CRITICAL: Verifier {name} failed!")
            return 1

    sweeps_file = REPO_ROOT / "reports" / "audit" / "q15_R7_sweeps.txt"
    sweeps_file.write_text("\n".join(sweeps_log) + "\n", encoding="utf-8")
    print(f"\nWrote full sweeps and verifiers log to {sweeps_file}")

    # 3. Pytest through update_ledger.py R7
    code, out = run_cmd([PYTHON, "scripts/update_ledger.py", "R7"], "Update Overnight Ledger (R7)")
    print(out)
    if code != 0:
        print("CRITICAL: update_ledger.py R7 failed!")
        return 1

    # 4. reproduce_all.py --verify-only -> reports/audit/q15_R7_output.txt
    print("\n[*] Executing reproduce_all.py --verify-only for q15_R7_output.txt...")
    res_v = subprocess.run([PYTHON, "scripts/reproduce_all.py", "--verify-only"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    r7_out_file = REPO_ROOT / "reports" / "audit" / "q15_R7_output.txt"
    r7_out_file.write_text(res_v.stdout, encoding="utf-8")
    print(f"    -> Exit code {res_v.returncode}")
    print(f"Wrote {r7_out_file}")
    if res_v.returncode != 0:
        print(res_v.stderr)
        return 1

    # 5. Rebuild viva_pack and verify (reads duration from q15_R7_output.txt)
    code, _ = run_cmd([PYTHON, "scripts/build_viva_pack.py"], "Rebuild Viva Pack")
    if code != 0:
        return 1
    code, _ = run_cmd([PYTHON, "scripts/verify_viva_pack.py"], "Verify Viva Pack")
    if code != 0:
        return 1

    # 6. Rebuild overnight_summary and verify (reads updated ledger)
    code, _ = run_cmd([PYTHON, "scripts/build_overnight_summary.py"], "Rebuild Overnight Summary")
    if code != 0:
        return 1
    code, _ = run_cmd([PYTHON, "scripts/verify_overnight_summary.py"], "Verify Overnight Summary")
    if code != 0:
        return 1

    # 7. audit_hash_coverage
    code, out = run_cmd([PYTHON, "scripts/audit_hash_coverage.py"], "Audit Hash Coverage")
    print(out)
    if code != 0:
        return 1

    # 8. Record git log and tags to reports/audit/q15_R7_git.txt
    git_log_res = subprocess.run(["git", "log", "--oneline", "-n", "25"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    git_tag_res = subprocess.run(["git", "tag", "-n"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    git_txt = (
        "================================================================================\n"
        "GIT LOG (Latest 25 Commits):\n"
        "================================================================================\n"
        + git_log_res.stdout +
        "\n================================================================================\n"
        "GIT TAGS:\n"
        "================================================================================\n"
        + git_tag_res.stdout + "\n"
    )
    git_out_file = REPO_ROOT / "reports" / "audit" / "q15_R7_git.txt"
    git_out_file.write_text(git_txt, encoding="utf-8")
    print(f"Wrote {git_out_file}")

    print("\n" + "=" * 80)
    print("PROMPT 15 - R7 FINALISE PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
