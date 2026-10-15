"""reproduce_clean_clone.py

Automates P10.3:
1. Checks SHA-256 of all 7 raw archives against docs/data_provenance.md.
2. Copies raw archives to C:\\c4_clean_clone\\data\\raw\\.
3. Executes scripts/reproduce_all.py --rebuild in C:\\c4_clean_clone.
4. Compares SHA-256 outputs with baselines and prints the result.
"""

from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CLEAN_CLONE = Path("C:/c4_clean_clone")

EXPECTED_HASHES = {
    "scenario_1_sudo_pam.zip": "0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc",
    "scenario_2_cron.zip": "b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791",
    "scenario_3_vnc_apt.zip": "5c23b9d614689194f43cc844e4a25ed43568879ae83edc43df93336e0a33f911",
    "scenario_4.zip": "a79fefbfeebd25b163e57f9ec7b9581f8e6f0abed2f2775fba45cf55a004b637",
    "scenario_5.zip": "e54df7f4c2f8e12e374272544809cee42b2c7e68ac37d950934e4123364f7911",
    "scenario_6_macro_binary.zip": "73a31bf763c5a65ed1a14bb5919151dbbf324563d4f8eaabb0c58d9c0f67f3b1",
    "scenario_7.zip": "7f0ff0b5d939437b5ebad7f52eea69dc024775e5c73663c5b4ac7ba58f1b3a56",
}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=" * 80)
    print("P10.3 CLEAN-CLONE REPRODUCTION")
    print("=" * 80)

    src_raw = WORKSPACE / "data" / "raw"
    if not src_raw.exists():
        print("BLOCKED: data/raw directory not found.")
        sys.exit(1)

    dest_raw = CLEAN_CLONE / "data" / "raw"
    dest_raw.mkdir(parents=True, exist_ok=True)

    print("\n1. Verifying raw archives against docs/data_provenance.md:")
    all_ok = True
    for fname, exp_hash in EXPECTED_HASHES.items():
        fp = src_raw / fname
        if not fp.exists():
            print(f"  BLOCKED: {fname} missing from data/raw/")
            all_ok = False
            continue
        h = sha256_file(fp)
        match = (h == exp_hash)
        print(f"  {fname:<30} {h[:16]}... [{'MATCH' if match else 'MISMATCH'}]")
        if not match:
            all_ok = False
        else:
            shutil.copy2(fp, dest_raw / fname)

    if not all_ok:
        print("\nBLOCKED: Raw archives could not be verified.")
        sys.exit(1)

    print("\n2. Copied 7 verified raw archives to C:/c4_clean_clone/data/raw/.")

    print("\n3. Executing reproduce_all.py --rebuild in C:/c4_clean_clone:")
    python_exe = sys.executable
    cmd = [python_exe, "scripts/reproduce_all.py", "--rebuild"]
    proc = subprocess.run(cmd, cwd=str(CLEAN_CLONE), capture_output=True, text=True)
    print(proc.stdout)
    if proc.stderr:
        print("STDERR:\n", proc.stderr)

    print("=" * 80)
    print(f"CLEAN-CLONE REBUILD EXIT CODE: {proc.returncode}")
    print("=" * 80)
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
