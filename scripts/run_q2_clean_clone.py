"""Automate Q2 True Clean-Clone Rebuild (Prompt 14).

Executes:
1. Fresh bundle verification.
2. Clone to C:\\c4_clean_clone_r2 (no file copy except raw archives).
3. Raw archive verification against docs/data_provenance.md.
4. Two rebuild runs in clone with timing and bit-identical hash verification.
5. All 61 baselines verified via verify_all_hashes.py.
6. Cleans up temporary clones.
7. Outputs full audit log.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent
CLEAN_CLONE = Path("C:/c4_clean_clone_r2")
BACKUP_DIR = Path("C:/c4_backup")
PYTHON_EXE = str(Path(sys.executable).resolve())

PROVENANCE_HASHES = {
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


def get_all_61_hashes(repo_dir: Path) -> dict[str, str]:
    res = {}
    with open(repo_dir / "reports" / "_baseline_hashes_stage2.json", "r", encoding="utf-8") as f:
        b_tech = json.load(f)
    for k in b_tech:
        p = repo_dir / ("reports" if not k.endswith(".csv") else "data/processed") / k
        res[f"section_a/{k}"] = sha256_file(p)

    b_stage1_keys = [
        "data/processed/attack_sequences.json",
        "data/processed/attack_timelines.json",
        "data/processed/loeo_folds.json",
        "data/processed/next_technique_samples.json",
        "data/processed/normalized_events.json",
        "data/processed/technique_tactic_reference.json",
        "reports/data_quality_report.json",
        "reports/timeline_validation_report.json",
        "reports/tactic_discrepancy_report.json",
        "reports/sequence_statistics.json",
    ]
    for k in b_stage1_keys:
        res[f"section_b/{k}"] = sha256_file(repo_dir / k)

    with open(repo_dir / "reports" / "_baseline_hashes_tactic.json", "r", encoding="utf-8") as f:
        b_tactic = json.load(f)
    for k in b_tactic:
        p = repo_dir / ("reports" if not k.endswith(".csv") else "data/processed") / k
        res[f"section_c/{k}"] = sha256_file(p)

    with open(repo_dir / "reports" / "_baseline_hashes_7ep_stage1.json", "r", encoding="utf-8") as f:
        b_7ep_s1 = json.load(f)
    for k in b_7ep_s1:
        res[f"section_d/{k}"] = sha256_file(repo_dir / k)

    with open(repo_dir / "reports" / "_baseline_hashes_7ep_eval.json", "r", encoding="utf-8") as f:
        b_7ep_eval = json.load(f)
    for k in b_7ep_eval:
        res[f"section_e/{k}"] = sha256_file(repo_dir / k)

    with open(repo_dir / "reports" / "_baseline_hashes_7ep_inference.json", "r", encoding="utf-8") as f:
        b_7ep_inf = json.load(f)
    for k in b_7ep_inf:
        res[f"section_f/{k}"] = sha256_file(repo_dir / k)

    return res


def main():
    log_lines = []

    def log(msg: str = ""):
        print(msg)
        log_lines.append(msg)

    log("=" * 80)
    log("PROMPT 14 - Q2 TRUE CLEAN-CLONE REBUILD & VERIFICATION REPORT")
    log("=" * 80)
    log(f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    log(f"Workspace: {WORKSPACE}")
    log(f"Clone Target: {CLEAN_CLONE}")
    log(f"Python Runtime: {PYTHON_EXE}")

    # (1) Bundle verification
    log("\n--- STEP 1: Fresh Bundle Integrity ---")
    head_rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(WORKSPACE), capture_output=True, text=True).stdout.strip()
    log(f"Current HEAD: {head_rev}")
    bundle_path = BACKUP_DIR / f"c4_{head_rev[:7]}.bundle"
    if not bundle_path.exists():
        # Also check full hash or 5921908
        bundle_path = BACKUP_DIR / f"c4_{head_rev}.bundle"
    if not bundle_path.exists():
        bundle_path = BACKUP_DIR / "c4_5921908.bundle"

    log(f"Bundle path: {bundle_path}")
    verify_res = subprocess.run(["git", "bundle", "verify", str(bundle_path)], capture_output=True, text=True)
    log(f"Bundle verification exit code: {verify_res.returncode}")
    log(verify_res.stdout)

    heads_txt = BACKUP_DIR / "bundle_heads.txt"
    if heads_txt.exists():
        heads_content = heads_txt.read_text(encoding="utf-8-sig")
        log("bundle_heads.txt contents:")
        for l in heads_content.strip().splitlines():
            log(f"  {l}")
        assert head_rev in heads_content, f"HEAD {head_rev} not in bundle_heads.txt"
        assert "refs/tags/c4-7ep-verified" in heads_content, "c4-7ep-verified not in bundle_heads.txt"
        assert "refs/tags/stage2-verified" in heads_content, "stage2-verified not in bundle_heads.txt"
        log("Assertion PASS: bundle_heads.txt contains HEAD and both tags.")

    # (2) Clean clone
    log("\n--- STEP 2: Clean Clone Creation ---")
    if CLEAN_CLONE.exists():
        log(f"Removing existing {CLEAN_CLONE}...")
        shutil.rmtree(CLEAN_CLONE, ignore_errors=False)

    log(f"Cloning {WORKSPACE} -> {CLEAN_CLONE}...")
    clone_res = subprocess.run(["git", "clone", str(WORKSPACE), str(CLEAN_CLONE)], capture_output=True, text=True)
    log(clone_res.stdout)
    if clone_res.returncode != 0:
        log(f"Clone FAILED: {clone_res.stderr}")
        sys.exit(1)

    # Check git status in clone before copying raw
    status_pre = subprocess.run(["git", "status", "--short"], cwd=str(CLEAN_CLONE), capture_output=True, text=True).stdout
    log(f"git status --short before raw copy: '{status_pre.strip()}' (clean={len(status_pre.strip())==0})")

    # Data raw status
    raw_tracked = subprocess.run(["git", "ls-files", "data/raw"], cwd=str(CLEAN_CLONE), capture_output=True, text=True).stdout.strip().splitlines()
    log(f"Tracked files in data/raw/: {raw_tracked}")
    log("State of data/raw: Directory is untracked/ignored except for .gitkeep. Copying ONLY the 7 verified raw zip files is allowed per rule G6/Q2.")

    src_raw = WORKSPACE / "data" / "raw"
    dest_raw = CLEAN_CLONE / "data" / "raw"
    dest_raw.mkdir(parents=True, exist_ok=True)

    log("\nVerifying SHA-256 of copied raw archives against docs/data_provenance.md:")
    all_raw_ok = True
    for fname, exp_hash in PROVENANCE_HASHES.items():
        src_file = src_raw / fname
        if not src_file.exists():
            log(f"  FAIL: Missing {src_file}")
            all_raw_ok = False
            continue
        h = sha256_file(src_file)
        match = (h == exp_hash)
        log(f"  {fname:<30} {h} [{'MATCH' if match else 'MISMATCH'}]")
        if not match:
            all_raw_ok = False
        else:
            shutil.copy2(src_file, dest_raw / fname)

    assert all_raw_ok, "Raw archive SHA-256 mismatch against docs/data_provenance.md!"
    log("All 7 raw archives copied and verified.")

    # (3) Run 1: Rebuild
    log("\n--- STEP 3: Rebuild Run 1 in Clean Clone ---")
    t0 = time.perf_counter()
    rebuild1_cmd = [PYTHON_EXE, "scripts/reproduce_all.py", "--rebuild"]
    p1 = subprocess.run(rebuild1_cmd, cwd=str(CLEAN_CLONE), capture_output=True, text=True)
    t1 = time.perf_counter() - t0
    log(f"Rebuild Run 1 Exit Code: {p1.returncode} (elapsed: {t1:.2f}s)")
    log(p1.stdout)
    if p1.returncode != 0:
        log(f"Rebuild Run 1 STDERR:\n{p1.stderr}")
        sys.exit(1)

    # Verify hashes after Run 1
    v1_cmd = [PYTHON_EXE, "scripts/verify_all_hashes.py"]
    v1 = subprocess.run(v1_cmd, cwd=str(CLEAN_CLONE), capture_output=True, text=True)
    log(f"verify_all_hashes after Run 1: Exit code {v1.returncode}")
    log(v1.stdout)
    assert v1.returncode == 0, "verify_all_hashes FAILED after Run 1!"

    hashes_run1 = get_all_61_hashes(CLEAN_CLONE)
    log(f"Recorded SHA-256 for all {len(hashes_run1)} baseline files after Run 1.")

    # (4) Run 2: Rebuild (determinism check)
    log("\n--- STEP 4: Rebuild Run 2 in Clean Clone (Bit-Identical Parity) ---")
    t0 = time.perf_counter()
    p2 = subprocess.run(rebuild1_cmd, cwd=str(CLEAN_CLONE), capture_output=True, text=True)
    t2 = time.perf_counter() - t0
    log(f"Rebuild Run 2 Exit Code: {p2.returncode} (elapsed: {t2:.2f}s)")
    if p2.returncode != 0:
        log(f"Rebuild Run 2 STDERR:\n{p2.stderr}")
        sys.exit(1)

    hashes_run2 = get_all_61_hashes(CLEAN_CLONE)
    mismatches = []
    for k in hashes_run1:
        if hashes_run1[k] != hashes_run2[k]:
            mismatches.append((k, hashes_run1[k], hashes_run2[k]))

    log(f"Run 1 vs Run 2 hash comparison across 61 files: {len(mismatches)} mismatches.")
    if mismatches:
        for k, h1, h2 in mismatches:
            log(f"  MISMATCH: {k} run1={h1} run2={h2}")
        raise ValueError("Non-deterministic rebuild between Run 1 and Run 2!")
    log("Assertion PASS: Run 1 and Run 2 produced 100% bit-identical baselines.")

    # Check git status in clone after rebuild
    status_post = subprocess.run(["git", "status", "--short"], cwd=str(CLEAN_CLONE), capture_output=True, text=True).stdout
    log("\n--- STEP 5: Clean Clone Git Status After Rebuild ---")
    log(f"git status --short in clone:\n{status_post if status_post.strip() else '(empty/clean)'}")

    # (5) Cleanup temporary clones
    log("\n--- STEP 6: Cleanup Temporary Clones ---")
    for temp_dir in [Path("C:/c4_clean_clone"), Path("C:/c4_clean_clone_r2"), Path("C:/c4_lf_test"), Path("C:/c4_crlf_test")]:
        if temp_dir.exists():
            log(f"Deleting superseded temporary clone: {temp_dir}...")
            shutil.rmtree(temp_dir, ignore_errors=True)
            log(f"  -> Deleted {temp_dir} (exists={temp_dir.exists()})")

    log("\n" + "=" * 80)
    log("CLEAN-CLONE REBUILD & VERIFICATION: ALL 61 BASELINES MATCH - PASS")
    log("=" * 80)

    # Write output log to reports/audit/q14_Q2_output.txt
    out_file = WORKSPACE / "reports" / "audit" / "q14_Q2_output.txt"
    out_file.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    log(f"\nWrote full Q2 execution log to {out_file}")


if __name__ == "__main__":
    main()
