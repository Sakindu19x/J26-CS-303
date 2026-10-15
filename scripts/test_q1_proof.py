"""test_q1_proof.py

Tests cloning into C:\\c4_lf_test and C:\\c4_crlf_test and running verify_all_hashes.py.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

lf_clone = Path("C:/c4_lf_test")
crlf_clone = Path("C:/c4_crlf_test")

def remove_dir(p: Path):
    if p.exists():
        subprocess.run(["powershell", "-NoProfile", "-Command", f"if (Test-Path '{p}') {{ Remove-Item -Recurse -Force '{p}' }}"], check=False)

remove_dir(lf_clone)
remove_dir(crlf_clone)

proof_output = []

print("1. Cloning into C:\\c4_lf_test (autocrlf=false)...")
cmd_lf = ["git", "-c", "core.autocrlf=false", "clone", str(REPO_ROOT), str(lf_clone)]
res_c_lf = subprocess.run(cmd_lf, capture_output=True, text=True)
proof_output.append(f"1. Git Clone (core.autocrlf=false) Exit Code: {res_c_lf.returncode}")

print("2. Cloning into C:\\c4_crlf_test (autocrlf=true)...")
cmd_crlf = ["git", "-c", "core.autocrlf=true", "clone", str(REPO_ROOT), str(crlf_clone)]
res_c_crlf = subprocess.run(cmd_crlf, capture_output=True, text=True)
proof_output.append(f"2. Git Clone (core.autocrlf=true) Exit Code: {res_c_crlf.returncode}")

print("3. Running verify_all_hashes.py in C:\\c4_lf_test...")
res_lf = subprocess.run([PYTHON, "scripts/verify_all_hashes.py"], cwd=str(lf_clone), capture_output=True, text=True)
print(f"LF Exit code: {res_lf.returncode}")
proof_output.append(f"3. verify_all_hashes.py in C:\\c4_lf_test Exit Code: {res_lf.returncode}")
proof_output.append(res_lf.stdout.strip())
if res_lf.stderr:
    proof_output.append("STDERR:\n" + res_lf.stderr.strip())

print("4. Running verify_all_hashes.py in C:\\c4_crlf_test...")
res_crlf = subprocess.run([PYTHON, "scripts/verify_all_hashes.py"], cwd=str(crlf_clone), capture_output=True, text=True)
print(f"CRLF Exit code: {res_crlf.returncode}")
proof_output.append(f"4. verify_all_hashes.py in C:\\c4_crlf_test Exit Code: {res_crlf.returncode}")
proof_output.append(res_crlf.stdout.strip())
if res_crlf.stderr:
    proof_output.append("STDERR:\n" + res_crlf.stderr.strip())

lf_ok = (res_lf.returncode == 0) and ("ALL BASELINE FILES BYTE-IDENTICAL AND FULLY VERIFIED" in res_lf.stdout)
crlf_ok = (res_crlf.returncode == 0) and ("ALL BASELINE FILES BYTE-IDENTICAL AND FULLY VERIFIED" in res_crlf.stdout)

proof_output.append("\n" + "=" * 80)
proof_output.append(f"OVERALL Q1 PROOF RESULT: {'PASS' if (lf_ok and crlf_ok) else 'FAIL'}")
proof_output.append(f"  C:\\c4_lf_test all 61 MATCH: {lf_ok}")
proof_output.append(f"  C:\\c4_crlf_test all 61 MATCH: {crlf_ok}")
proof_output.append("=" * 80)

out_text = "\n".join(proof_output) + "\n"
out_path = REPO_ROOT / "reports" / "audit" / "q14_Q1_output.txt"
out_path.write_text(out_text, encoding="utf-8")
print(f"Wrote {out_path}")

remove_dir(lf_clone)
remove_dir(crlf_clone)
print("Cleaned up test clones.")

if not (lf_ok and crlf_ok):
    print("FAILED")
    sys.exit(1)
else:
    print("SUCCESS: BOTH CLONES VERIFIED ALL 61 BASELINE HASHES EXACTLY!")
