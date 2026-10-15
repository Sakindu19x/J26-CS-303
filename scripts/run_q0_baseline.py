"""run_q0_baseline.py

Executes Q0 baseline audit:
1. Git HEAD
2. Git status
3. verify_all_hashes exit code
4. Pytest count (executed directly)
5. git config --show-origin --get-all core.autocrlf
6. Whether .gitattributes exists
7. git tag -n
8. Untracked and ignored directories
9. Whether data/raw is tracked

Writes output to reports/audit/q14_Q0_output.txt.
"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def run_cmd(cmd: list[str]) -> tuple[int, str]:
    res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
    out = (res.stdout + "\n" + res.stderr).strip()
    return res.returncode, out

def main():
    lines = []
    lines.append("=" * 80)
    lines.append("Q0 BASELINE AUDIT OUTPUT")
    lines.append("=" * 80)

    # 1. HEAD
    _, head = run_cmd(["git", "rev-parse", "HEAD"])
    lines.append(f"\n1. Git HEAD:\n{head}")

    # 2. Git status
    _, status = run_cmd(["git", "status"])
    lines.append(f"\n2. Git Status:\n{status}")

    # 3. verify_all_hashes exit code
    v_code, v_out = run_cmd([sys.executable, "scripts/verify_all_hashes.py"])
    lines.append(f"\n3. verify_all_hashes.py Exit Code: {v_code}")
    lines.append(f"Output snippet:\n{v_out[-300:] if len(v_out) > 300 else v_out}")

    # 4. Pytest count
    p_code, p_out = run_cmd([sys.executable, "-m", "pytest", "tests/", "-q"])
    lines.append(f"\n4. Pytest Exit Code: {p_code}")
    lines.append(f"Pytest summary line:\n{p_out.splitlines()[-1] if p_out.splitlines() else ''}")

    # 5. core.autocrlf
    _, autocrlf = run_cmd(["git", "config", "--show-origin", "--get-all", "core.autocrlf"])
    lines.append(f"\n5. git config core.autocrlf:\n{autocrlf}")

    # 6. .gitattributes exists
    gitattr_path = REPO_ROOT / ".gitattributes"
    lines.append(f"\n6. .gitattributes exists: {gitattr_path.exists()}")

    # 7. git tag -n
    _, tags = run_cmd(["git", "tag", "-n"])
    lines.append(f"\n7. git tag -n:\n{tags}")

    # 8. Untracked and ignored dirs
    _, other_dirs = run_cmd(["git", "status", "--ignored", "--short"])
    lines.append(f"\n8. Untracked / Ignored Files and Dirs:\n{other_dirs}")

    # 9. Is data/raw tracked?
    _, raw_files = run_cmd(["git", "ls-files", "data/raw"])
    is_tracked = bool(raw_files.strip())
    lines.append(f"\n9. Is data/raw tracked?: {is_tracked}")
    if is_tracked:
        lines.append(f"Tracked data/raw files:\n{raw_files}")
    else:
        lines.append("data/raw is NOT tracked in git index.")

    out_text = "\n".join(lines) + "\n"
    out_path = REPO_ROOT / "reports" / "audit" / "q14_Q0_output.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_text, encoding="utf-8")
    print(f"Wrote {out_path}")
    print(out_text)

if __name__ == "__main__":
    main()
