"""scripts/audit/reproduce_clean_clone_t6.py (Prompt 17 Part T6).

Executes pristine clean clone verification at C:\\c4_clean_clone_t6:
1. Delete C:\\c4_clean_clone_t6 first if it exists.
2. Clone HEAD of main repo into C:\\c4_clean_clone_t6.
3. Verify git status --porcelain is empty on fresh clone.
4. Copy raw data archives (data/raw/*.zip) and verify SHA-256 against docs/data_provenance.md.
5. Execute Rebuild Run 1 via scripts/reproduce_all.py --rebuild and record hashes.
6. Execute Rebuild Run 2 via scripts/reproduce_all.py --rebuild and assert Run 1 == Run 2.
7. Verify all 61 hashes match baseline registries.
8. Show git status --porcelain for both repos (must be empty).
9. Show git diff --stat c4-7ep-verified-v4 HEAD.
10. Prove line-ending safety: print .gitattributes and compare clone vs master hashes.
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

REPO_ROOT = Path(__file__).resolve().parents[2]
CLONE_DIR = Path("C:/c4_clean_clone_t6")
PYTHON = sys.executable

PROVENANCE_HASHES = {
    "scenario_1_sudo_pam.zip": "0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc",
    "scenario_2_cron.zip": "b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791",
    "scenario_3_vnc_apt.zip": "5c23b9d614689194f43cc844e4a25ed43568879ae83edc43df93336e0a33f911",
    "scenario_4.zip": "a79fefbfeebd25b163e57f9ec7b9581f8e6f0abed2f2775fba45cf55a004b637",
    "scenario_5.zip": "e54df7f4c2f8e12e374272544809cee42b2c7e68ac37d950934e4123364f7911",
    "scenario_6_macro_binary.zip": "73a31bf763c5a65ed1a14bb5919151dbbf324563d4f8eaabb0c58d9c0f67f3b1",
    "scenario_7.zip": "7f0ff0b5d939437b5ebad7f52eea69dc024775e5c73663c5b4ac7ba58f1b3a56",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def load_all_baseline_files(root: Path) -> list[str]:
    files: list[str] = [
        "reports/evaluation_report.md",
        "reports/evaluation_results.json",
        "data/processed/evaluation_predictions.csv",
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
        "reports/tactic_evaluation_report.md",
        "reports/tactic_evaluation_results.json",
        "data/processed/tactic_evaluation_predictions.csv",
        "data/processed_7ep/attack_sequences.json",
        "data/processed_7ep/attack_timelines.json",
        "data/processed_7ep/loeo_folds.json",
        "data/processed_7ep/next_technique_samples.json",
        "data/processed_7ep/normalized_events.json",
        "data/processed_7ep/technique_tactic_reference.json",
        "reports/7ep/data_quality_report.json",
        "reports/7ep/timeline_validation_report.json",
        "reports/7ep/tactic_discrepancy_report.json",
        "reports/7ep/sequence_statistics.json",
        "data/processed_7ep/evaluation_7ep_predictions.csv",
        "reports/7ep/evaluation_7ep_results.json",
        "reports/7ep/evaluation_7ep_report.md",
        "data/processed_7ep/learning_curve_7ep.csv",
        "reports/7ep/learning_curve_7ep_results.json",
        "reports/7ep/learning_curve_7ep_report.md",
        "reports/7ep/learning_curve_7ep.png",
        "reports/7ep/learning_curve_7ep_plot_data.json",
        "data/processed_7ep/permutation_7ep_null_distribution.csv",
        "reports/7ep/permutation_7ep_report.json",
        "reports/7ep/permutation_7ep_report.md",
        "data/processed_7ep/planted_realscale_7ep_predictions.csv",
        "reports/7ep/planted_realscale_7ep_report.json",
        "reports/7ep/planted_realscale_7ep_report.md",
        "data/processed_7ep/e5_removed_predictions.csv",
        "reports/7ep/e5_removed_results.json",
        "reports/7ep/e5_removed_report.md",
        "reports/7ep/holm_claim_rule_results.json",
        "reports/7ep/holm_claim_rule_report.md",
        "reports/7ep/diagnostics_7ep.json",
        "reports/7ep/diagnostics_7ep.md",
        "reports/7ep/e5_hit1_change_diagnostic.json",
        "reports/7ep/e5_hit1_change_diagnostic.md",
        "data/processed_7ep/tie_sensitivity_7ep_samples.csv",
        "reports/7ep/tie_sensitivity_7ep.json",
        "reports/7ep/tie_sensitivity_7ep.md",
        "data/processed_7ep/exploratory_tactic_conditioned_predictions.csv",
        "reports/7ep/exploratory_tactic_conditioned_results.json",
        "reports/7ep/exploratory_tactic_conditioned_report.md",
        "artifacts/7ep/production_model/collapsed_full.json",
        "artifacts/7ep/production_model/tactic_collapsed.json",
        "artifacts/7ep/production_model/manifest.json",
        "data/processed_7ep/prediction_records_loeo.jsonl",
        "reports/7ep/prediction_record_examples.md",
        "reports/7ep/requirements_trace.md",
    ]
    return files


def run_clean_clone_t6_proof() -> int:
    print("=" * 80)
    print("PROMPT 17 - PART T6 PRISTINE CLEAN-CLONE DOUBLE REBUILD PROOF")
    print("=" * 80)
    print(f"Timestamp      : {time.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print(f"Master Repo    : {REPO_ROOT}")
    print(f"Clone Target   : {CLONE_DIR}")
    print(f"Python Runtime : {PYTHON}\n")

    # Step 1: Remove existing clone directory if present
    if CLONE_DIR.exists():
        print(f"[*] Removing existing clone directory: {CLONE_DIR}...")
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Remove-Item -Recurse -Force '{CLONE_DIR}'"], check=True)
        print("    -> Removed.")

    # Step 2: Clone repository
    print(f"[*] Cloning {REPO_ROOT} -> {CLONE_DIR}...")
    subprocess.run(["git", "clone", str(REPO_ROOT), str(CLONE_DIR)], check=True)
    print("    -> Clone completed successfully.")

    # Step 3: Check clean clone status before raw data copy
    print("\n[*] Checking git status --porcelain on fresh clone:")
    res_status = subprocess.run(["git", "status", "--porcelain"], cwd=str(CLONE_DIR), capture_output=True, text=True)
    clean_clone_status = res_status.stdout.strip()
    if clean_clone_status:
        print(f"    [WARNING] Clean clone dirty before raw copy:\n{clean_clone_status}")
    else:
        print("    -> Fresh clone working tree is 100% clean (git status --porcelain is empty).")

    # Step 4: Copy raw data archives
    print("\n[*] Providing raw archives to clone data/raw/ and verifying SHA-256 against provenance:")
    raw_dest = CLONE_DIR / "data" / "raw"
    raw_dest.mkdir(parents=True, exist_ok=True)
    for archive_name, expected_sha in PROVENANCE_HASHES.items():
        src_path = REPO_ROOT / "data" / "raw" / archive_name
        dest_path = raw_dest / archive_name
        shutil.copy2(src_path, dest_path)
        actual_sha = sha256_file(dest_path)
        match_str = "[MATCH]" if actual_sha == expected_sha else "[FAIL]"
        print(f"    {archive_name:<28} SHA-256: {actual_sha} {match_str}")
        assert actual_sha == expected_sha, f"Hash mismatch on {archive_name}"

    baseline_files = load_all_baseline_files(CLONE_DIR)

    # Step 5: Execute Rebuild Run 1
    print("\n[*] Executing Rebuild Run 1 (& PYTHON scripts/reproduce_all.py --rebuild)...")
    t0 = time.perf_counter()
    res1 = subprocess.run([PYTHON, "scripts/reproduce_all.py", "--rebuild"], cwd=str(CLONE_DIR), capture_output=True, text=True)
    t_run1 = time.perf_counter() - t0
    print(f"    Rebuild Run 1 Exit Code: {res1.returncode} ({t_run1:.2f}s)")
    if res1.returncode != 0:
        print("--- RUN 1 STDERR ---")
        print(res1.stderr)
        return res1.returncode

    run1_hashes = {}
    for rel_path in baseline_files:
        run1_hashes[rel_path] = sha256_file(CLONE_DIR / rel_path)

    # Step 6: Execute Rebuild Run 2
    print("\n[*] Executing Rebuild Run 2 (& PYTHON scripts/reproduce_all.py --rebuild)...")
    t0 = time.perf_counter()
    res2 = subprocess.run([PYTHON, "scripts/reproduce_all.py", "--rebuild"], cwd=str(CLONE_DIR), capture_output=True, text=True)
    t_run2 = time.perf_counter() - t0
    print(f"    Rebuild Run 2 Exit Code: {res2.returncode} ({t_run2:.2f}s)")
    if res2.returncode != 0:
        print("--- RUN 2 STDERR ---")
        print(res2.stderr)
        return res2.returncode

    run2_hashes = {}
    mismatches = []
    for rel_path in baseline_files:
        h2 = sha256_file(CLONE_DIR / rel_path)
        run2_hashes[rel_path] = h2
        if h2 != run1_hashes[rel_path]:
            mismatches.append(rel_path)

    if mismatches:
        print(f"    [FAIL] Run 1 vs Run 2 hash mismatch in {len(mismatches)} files: {mismatches}")
        return 1
    print("    -> ALL 61 BASELINE FILES BYTE-IDENTICAL ACROSS RUN 1 AND RUN 2 (100% DETERMINISM).")

    # Step 7: Verify all 61 baseline hashes
    print("\n[*] Verifying 61 baseline hashes in clone via verify_all_hashes.py:")
    res_v = subprocess.run([PYTHON, "scripts/verify/verify_all_hashes.py"], cwd=str(CLONE_DIR), capture_output=True, text=True)
    if res_v.returncode == 0:
        print("    -> ALL 61 PROTECTED BASELINE FILES MATCH 100% (Exit 0).")
    else:
        print(f"    [FAIL] verify_all_hashes returned {res_v.returncode}:\n{res_v.stdout}")
        return res_v.returncode

    # Step 8: Git status --porcelain for BOTH repositories
    print("\n[*] Checking git status --porcelain for Master repository:")
    res_st_master = subprocess.run(["git", "status", "--porcelain"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    st_master = [l for l in res_st_master.stdout.strip().splitlines() if not any(k in l for k in ("q17_T6_output.txt", "reproduce_clean_clone_t6.py"))]
    if st_master:
        print(f"    [DIRTY]:\n" + "\n".join(st_master))
        return 1
    print("    -> Master git status --porcelain is clean (ignoring active T6 log/runner).")

    print("\n[*] Checking git status --porcelain for Clean Clone repository:")
    res_st_clone = subprocess.run(["git", "status", "--porcelain"], cwd=str(CLONE_DIR), capture_output=True, text=True)
    st_clone = res_st_clone.stdout.strip()
    if st_clone:
        print(f"    [DIRTY]:\n{st_clone}")
        return 1
    print("    -> Clean Clone git status --porcelain is 100% EMPTY.")

    # Step 9: git diff --stat c4-7ep-verified-v4 HEAD
    print("\n[*] Running 'git diff --stat c4-7ep-verified-v4 HEAD' on Master repo:")
    res_diff = subprocess.run(["git", "diff", "--stat", "c4-7ep-verified-v4", "HEAD"], cwd=str(REPO_ROOT), capture_output=True, text=True)
    print(res_diff.stdout.strip())

    # Step 10: Prove line-ending safety: print .gitattributes and compare clone vs master hashes
    print("\n[*] Line-Ending Safety Proof:")
    print("--- .gitattributes ---")
    gitattrs_path = REPO_ROOT / ".gitattributes"
    if gitattrs_path.is_file():
        print(gitattrs_path.read_text(encoding="utf-8").strip())
    else:
        print("(No .gitattributes file present)")

    print("\n[*] Comparing Clone vs Master 61 baseline hashes:")
    clone_vs_master_mismatches = []
    for rel_path in baseline_files:
        master_h = sha256_file(REPO_ROOT / rel_path)
        clone_h = sha256_file(CLONE_DIR / rel_path)
        if master_h != clone_h:
            clone_vs_master_mismatches.append(rel_path)

    if clone_vs_master_mismatches:
        print(f"    [FAIL] Clone vs Master hash mismatch in {len(clone_vs_master_mismatches)} files: {clone_vs_master_mismatches}")
        return 1
    print(f"    -> 61/61 hashes match identically between Master working tree and Clean Clone (0 mismatches).")

    print("\n" + "=" * 80)
    print("ALL T6 CLEAN-CLONE PROOF GATES PASSED PERFECTLY (GATE STATUS: PASS)")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(run_clean_clone_t6_proof())
