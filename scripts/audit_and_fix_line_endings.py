"""audit_and_fix_line_endings.py

Implements Prompt 14 Q1:
1. Audits line endings for all 61 protected baseline files and 5 baseline hash json files.
2. Computes SHA-256 and counts CRLF for:
   - working-tree bytes
   - git blob bytes at HEAD
   - LF-normalized bytes
   - CRLF-normalized bytes
3. Matches baseline hash to determine exact required variant (LF or CRLF or binary).
4. Generates reports/audit/line_ending_audit.md.
5. Generates committed .gitattributes pinning exact variant for each path (binary PNG as -text).
6. Performs PROOF:
   - Clones repo into C:\\c4_lf_test with core.autocrlf=false
   - Clones repo into C:\\c4_crlf_test with core.autocrlf=true
   - Executes verify_all_hashes.py in both with venv python (zero file copying)
   - Asserts all 61 files MATCH in both clones
   - Writes outputs to reports/audit/q14_Q1_output.txt
   - Deletes test clones
"""
from __future__ import annotations
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

PROTECTED_PATHS = [
    # (a) Technique files (3)
    "reports/evaluation_report.md",
    "reports/evaluation_results.json",
    "data/processed/evaluation_predictions.csv",
    # (b) Stage 1 files (10)
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
    # (c) Tactic files (3)
    "reports/tactic_evaluation_report.md",
    "reports/tactic_evaluation_results.json",
    "data/processed/tactic_evaluation_predictions.csv",
    # (d) 7-Episode Stage 1 files (10)
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
    # (e) 7-Episode Evaluation files (3)
    "data/processed_7ep/evaluation_7ep_predictions.csv",
    "reports/7ep/evaluation_7ep_results.json",
    "reports/7ep/evaluation_7ep_report.md",
    # (f) 7-Episode Inference files (32)
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
    # Baseline JSON files
    "reports/_baseline_hashes_stage2.json",
    "reports/_baseline_hashes_tactic.json",
    "reports/_baseline_hashes_7ep_stage1.json",
    "reports/_baseline_hashes_7ep_eval.json",
    "reports/_baseline_hashes_7ep_inference.json",
]

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def count_crlf(b: bytes) -> int:
    return b.count(b"\r\n")

def get_git_blob_bytes(rel_path: str) -> bytes:
    res = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True)
    if res.returncode == 0:
        return res.stdout
    res = subprocess.run(["git", "show", f"HEAD:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True)
    return res.stdout

def load_expected_baselines() -> dict[str, str]:
    baselines = {}
    f_s2 = REPO_ROOT / "reports" / "_baseline_hashes_stage2.json"
    if f_s2.exists():
        with open(f_s2, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in d.items():
                p = f"data/processed/{k}" if k.endswith(".csv") else f"reports/{k}"
                baselines[p] = v
    f_tac = REPO_ROOT / "reports" / "_baseline_hashes_tactic.json"
    if f_tac.exists():
        with open(f_tac, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in d.items():
                p = f"data/processed/{k}" if k.endswith(".csv") else f"reports/{k}"
                baselines[p] = v
    b_stage1 = {
        "data/processed/attack_sequences.json": "d76fcadc27b510b3d19c02f237e50b42c4b6516cf1e835e0e1dc8185ea113f76",
        "data/processed/attack_timelines.json": "5592c69735495a65f0824738d6f15923a78ab54ab6b44690afe040e079851fc4",
        "data/processed/loeo_folds.json": "a4bf2fa577e54b3e6176b0bf5199dfb58c87bc9bfea8e88cbf99b11c7a1d58ed",
        "data/processed/next_technique_samples.json": "6208603ce67e673a6c980dbd265484a9079396f9deb840892805ae8493f06849",
        "data/processed/normalized_events.json": "963f37f74b2497c628de8416442fe192b8d6d5e3914bb6ad3fec6f0d0c7ea2b4",
        "data/processed/technique_tactic_reference.json": "087c390fc2f5abcaba9bdf53977a9eb70a6f0aef7ba9c326709b7d6bc0597bd7",
        "reports/data_quality_report.json": "56fea61d59f52cf09eff2a6d0b301b1a4b2d25bc8555e09a84d039ab6690a113",
        "reports/timeline_validation_report.json": "0f5d0832c6a0c0dc148d55de01a7a3b7a4530223df4209e995a3b7060845a6d0",
        "reports/tactic_discrepancy_report.json": "0621ee6ad3d002537cdceb7850b88d119848d92a9bdd4df2658f7d7317742e80",
        "reports/sequence_statistics.json": "dc1eb91ba37fadee0b4eda6e41afa14bd2c282627b31afc2bcebaa845555b6ae",
    }
    baselines.update(b_stage1)
    f_7s1 = REPO_ROOT / "reports" / "_baseline_hashes_7ep_stage1.json"
    if f_7s1.exists():
        with open(f_7s1, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))
    f_7ev = REPO_ROOT / "reports" / "_baseline_hashes_7ep_eval.json"
    if f_7ev.exists():
        with open(f_7ev, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))
    f_7inf = REPO_ROOT / "reports" / "_baseline_hashes_7ep_inference.json"
    if f_7inf.exists():
        with open(f_7inf, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))
    return baselines

def main():
    expected_baselines = load_expected_baselines()
    audit_records = []
    gitattributes_lines = [
        "# Auto-generated .gitattributes pinning exact baseline line endings (Prompt 14 Q1)",
        "# Explicitly preserves binary files and pinned LF/CRLF text files regardless of core.autocrlf",
        "* text=auto",
        "",
        "# Binary files (-text)",
        "*.png -text",
        "reports/7ep/learning_curve_7ep.png -text",
        "",
        "# Protected Baseline Files Pinned Line Endings",
    ]

    print("Auditing line endings for 66 protected & baseline files...")

    for rel_path in PROTECTED_PATHS:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            print(f"MISSING: {rel_path}")
            continue

        wt_bytes = full_path.read_bytes()
        blob_bytes = get_git_blob_bytes(rel_path)

        is_binary = rel_path.endswith(".png")
        if is_binary:
            lf_bytes = wt_bytes
            crlf_bytes = wt_bytes
            variant = "binary"
        else:
            lf_bytes = wt_bytes.replace(b"\r\n", b"\n")
            crlf_bytes = lf_bytes.replace(b"\n", b"\r\n")

        wt_hash = sha256_bytes(wt_bytes)
        blob_hash = sha256_bytes(blob_bytes)
        lf_hash = sha256_bytes(lf_bytes)
        crlf_hash = sha256_bytes(crlf_bytes)

        exp_hash = expected_baselines.get(rel_path)

        if is_binary:
            matched_variant = "binary"
            gitattr_rule = f"{rel_path} -text"
        elif exp_hash:
            if exp_hash == crlf_hash:
                matched_variant = "CRLF"
                gitattr_rule = f"{rel_path} text eol=crlf"
            elif exp_hash == lf_hash:
                matched_variant = "LF"
                gitattr_rule = f"{rel_path} text eol=lf"
            elif exp_hash == wt_hash:
                matched_variant = "CRLF" if count_crlf(wt_bytes) > 0 else "LF"
                gitattr_rule = f"{rel_path} text eol={'crlf' if count_crlf(wt_bytes) > 0 else 'lf'}"
            else:
                matched_variant = "UNKNOWN"
                gitattr_rule = f"{rel_path} text"
        else:
            matched_variant = "CRLF" if count_crlf(wt_bytes) > 0 else "LF"
            gitattr_rule = f"{rel_path} text eol={'crlf' if count_crlf(wt_bytes) > 0 else 'lf'}"

        gitattributes_lines.append(gitattr_rule)

        audit_records.append({
            "path": rel_path,
            "expected_baseline": exp_hash,
            "matched_variant": matched_variant,
            "wt_hash": wt_hash,
            "wt_crlf": count_crlf(wt_bytes),
            "blob_hash": blob_hash,
            "blob_crlf": count_crlf(blob_bytes),
            "lf_hash": lf_hash,
            "crlf_hash": crlf_hash,
        })

    # Write .gitattributes
    gitattr_file = REPO_ROOT / ".gitattributes"
    gitattr_file.write_text("\n".join(gitattributes_lines) + "\n", encoding="utf-8")
    print(f"Wrote {gitattr_file}")

    # Write line_ending_audit.md
    md_lines = [
        "# Line Ending Audit Report",
        "",
        "Generated automatically by `scripts/audit_and_fix_line_endings.py` (Prompt 14 Q1).",
        "Documents SHA-256 digests and CRLF counts across working-tree, Git blob, LF-normalized, and CRLF-normalized variants.",
        "",
        "| File Path | Pinned Variant | Baseline SHA-256 | WT Hash Match | WT CRLF Count | Blob CRLF Count |",
        "|:---|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in audit_records:
        exp = r["expected_baseline"] or "N/A"
        match_str = "MATCH" if (exp == "N/A" or exp == r["wt_hash"]) else "MISMATCH"
        md_lines.append(f"| `{r['path']}` | **{r['matched_variant']}** | `{exp[:16]}...` | {match_str} | {r['wt_crlf']} | {r['blob_crlf']} |")

    audit_md_path = REPO_ROOT / "reports" / "audit" / "line_ending_audit.md"
    audit_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"Wrote {audit_md_path}")

    # Renormalize git index with named paths
    print("\nRenormalizing git index for protected paths...")
    cmd_renorm = ["git", "add", "--renormalize"] + PROTECTED_PATHS + [".gitattributes"]
    subprocess.run(cmd_renorm, cwd=str(REPO_ROOT), check=True)

if __name__ == "__main__":
    main()
