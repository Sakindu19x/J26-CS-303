"""Script to generate docs/process/cleanup_map.md and docs/PROJECT_MAP.md (Rule G2).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def generate_cleanup_map() -> None:
    # 10 embedded scripts required by G6/S2
    EMBEDDED_SCRIPTS = {
        "scripts/build_prediction_records.py": "KEPT - name embedded in output (reports/7ep/requirements_trace.md)",
        "scripts/build_requirements_trace.py": "KEPT - name embedded in output (reports/7ep/requirements_trace.md)",
        "scripts/measure_nfr1.py": "KEPT - name embedded in output (reports/7ep/requirements_trace.md)",
        "scripts/mutation_sweep.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/run_holm_claim_rule.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/run_permutation_test_7ep.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/run_permutation_test_v2.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/verify_evaluation.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/verify_permutation_7ep.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
        "scripts/verify_permutation_test_v2.py": "KEPT - name embedded in output (reports/prereg_7episode_design.md)",
    }

    # Other scripts preserved in scripts/ root
    OTHER_KEPT_SCRIPTS = {
        "scripts/check_regression_gate.py": "KEPT - used by tests/test_evaluation_7ep.py",
        "scripts/mutation_sweep_requirements_trace.py": "KEPT - used for requirements trace mutation testing",
        "scripts/reproduce_all.py": "KEPT - canonical reproduction & verification harness",
        "scripts/run_planted_realscale.py": "KEPT - used by tests/test_planted_realscale.py",
        "scripts/run_planted_structure.py": "KEPT - used by tests/test_planted_structure.py",
        "scripts/run_q7_gates.py": "KEPT - used by reports/viva/claims.json (CLAIM-10, CLAIM-11)",
    }

    # Query git diff against b4e9635
    cmd = ["git", "diff", "--name-status", "b4e9635"]
    res = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True)
    lines = res.stdout.strip().splitlines()

    entries = []

    # Add embedded scripts
    for path, reason in sorted(EMBEDDED_SCRIPTS.items()):
        entries.append((path, path, "KEPT", reason))

    # Add other kept scripts
    for path, reason in sorted(OTHER_KEPT_SCRIPTS.items()):
        entries.append((path, path, "KEPT", reason))

    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R"):
            old_path = parts[1]
            new_path = parts[2]
            if old_path.startswith("scripts/"):
                if "pipeline" in new_path:
                    reason = "Standardized pipeline stage script"
                elif "verify" in new_path:
                    reason = "Reorganized into dedicated verifier directory"
                elif "audit" in new_path:
                    reason = "Reorganized into audit tool directory"
                elif "dashboard" in new_path:
                    reason = "Reorganized into dashboard runner directory"
                else:
                    reason = "Organized into subsystem folder"
            elif old_path.startswith("tests/"):
                reason = "Renamed to descriptive test name without prompt number"
            elif old_path.startswith("docs/prompts/"):
                reason = "Reorganized into docs/process/prompts/"
            elif old_path.startswith("reports/audit/q"):
                reason = "Archived legacy un-cited prompt run log"
            else:
                reason = "Reorganized"
            entries.append((old_path, new_path, "MOVED", reason))
        elif status == "D":
            old_path = parts[1]
            if old_path.startswith("scripts/"):
                reason = "Obsolete one-off prompt runner removed (recoverable from pre-cleanup-v3)"
                entries.append((old_path, "-", "REMOVED", reason))

    # Sort entries by old path
    entries.sort(key=lambda x: x[0])

    content = [
        "# Workspace Clean-up and Reorganisation Map (Part S2)",
        "",
        "This document maps all file reorganisations, removals, and retentions executed during Part S2 clean-up.",
        "Per Rule G6, scripts embedded in protected baselines are preserved in-place.",
        "",
        "| Original Path | Target Path / Status | Action | Rationale |",
        "|:---|:---|:---|:---|",
    ]

    for old_p, new_p, act, rat in entries:
        content.append(f"| `{old_p}` | `{new_p}` | **{act}** | {rat} |")

    content.append("")
    out_file = REPO_ROOT / "docs" / "process" / "cleanup_map.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(content), encoding="utf-8")
    print(f"Wrote {out_file} ({len(entries)} entries)")


def generate_project_map() -> None:
    top_level_items = sorted(REPO_ROOT.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    
    FOLDER_DESCRIPTIONS = {
        ".git": "Git repository metadata and version history",
        ".github": "GitHub repository configuration and CI workflows",
        ".streamlit": "Streamlit configuration and UI theme settings",
        "data": "Dataset archives, raw logs, and processed pipeline artifacts",
        "docs": "System architecture, specifications, requirements, and process logs",
        "reports": "Pre-registered experimental reports, baseline hashes, audit ledgers, and viva pack",
        "scripts": "Executable pipeline stages, verification harnesses, audit tools, and dashboard scripts",
        "src": "Production Python package (c4: data loading, models, evaluation, dashboard)",
        "tests": "Automated regression, integrity, model invariant, and property tests",
        "viva_pack": "Viva pack presentation slides, worked examples, and reproduction guide",
    }

    SCRIPT_DESCRIPTIONS = {
        "scripts/build_prediction_records.py": "Stage runner generating explainable prediction JSON records (embedded in requirements trace)",
        "scripts/build_requirements_trace.py": "Stage runner generating requirements trace matrix (embedded in requirements trace)",
        "scripts/check_regression_gate.py": "Pre-registered regression gate validator for LOEO evaluation",
        "scripts/measure_nfr1.py": "NFR1 dashboard warm render latency benchmark harness (embedded in requirements trace)",
        "scripts/mutation_sweep.py": "Mutation testing harness validating verifier sensitivity (embedded in prereg design)",
        "scripts/mutation_sweep_requirements_trace.py": "Mutation testing harness validating requirements trace verifier",
        "scripts/reproduce_all.py": "Canonical full reproduction and verify-only entrypoint",
        "scripts/run_holm_claim_rule.py": "Stage runner executing Holm-Bonferroni family-wise error control (embedded in prereg design)",
        "scripts/run_permutation_test_7ep.py": "Stage runner executing 7-episode order permutation test (embedded in prereg design)",
        "scripts/run_permutation_test_v2.py": "Stage runner executing 4-episode order permutation test (embedded in prereg design)",
        "scripts/run_planted_realscale.py": "Planted structure power analysis validation runner",
        "scripts/run_planted_structure.py": "Planted Markov transition structure power test runner",
        "scripts/run_q7_gates.py": "Gate verification script supporting CLAIM-10 and CLAIM-11 in claims map",
        "scripts/verify_evaluation.py": "Independent verifier for 4-episode LOEO evaluation (embedded in prereg design)",
        "scripts/verify_permutation_7ep.py": "Independent verifier for 7-episode permutation test (embedded in prereg design)",
        "scripts/verify_permutation_test_v2.py": "Independent verifier for 4-episode permutation test (embedded in prereg design)",
    }

    SUBFOLDER_DESCRIPTIONS = {
        "scripts/audit": "Audit provenance, hash coverage, baseline changes, and ledger verification scripts",
        "scripts/dashboard": "Streamlit dashboard launch scripts and automated browser screenshot capture tools",
        "scripts/pipeline": "Numbered sequential pipeline stages (s01 to s20) executing end-to-end data processing and evaluation",
        "scripts/verify": "Independent single-purpose verifier scripts checking baseline outputs and reports",
    }

    lines = [
        "# C4 Project Map",
        "",
        "This document describes every top-level folder, script subdirectory, and root script in the C4 repository.",
        "Derived directly from repository filesystem structure.",
        "",
        "## Top-Level Directories and Root Files",
        "",
    ]

    for item in top_level_items:
        if item.name.startswith(".") and item.name not in [".streamlit", ".github"]:
            continue
        rel = item.name
        if item.is_dir():
            desc = FOLDER_DESCRIPTIONS.get(rel, "Workspace directory")
            lines.append(f"- [`{rel}/`](file:///{item.as_posix()}): {desc}")
        else:
            lines.append(f"- [`{rel}`](file:///{item.as_posix()}): Root project file")

    lines.append("")
    lines.append("## Scripts Subsystems (`scripts/`)")
    lines.append("")
    
    scripts_dir = REPO_ROOT / "scripts"
    for sub in sorted(scripts_dir.iterdir()):
        if sub.is_dir() and not sub.name.startswith("__"):
            rel_sub = f"scripts/{sub.name}"
            desc = SUBFOLDER_DESCRIPTIONS.get(rel_sub, "Scripts subdirectory")
            lines.append(f"- [`{rel_sub}/`](file:///{sub.as_posix()}): {desc}")

    lines.append("")
    lines.append("## Root Scripts (`scripts/*.py`)")
    lines.append("")
    for item in sorted(scripts_dir.glob("*.py")):
        rel = f"scripts/{item.name}"
        desc = SCRIPT_DESCRIPTIONS.get(rel, "Executable utility script")
        lines.append(f"- [`{rel}`](file:///{item.as_posix()}): {desc}")

    lines.append("")
    out_file = REPO_ROOT / "docs" / "PROJECT_MAP.md"
    out_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_file}")


if __name__ == "__main__":
    generate_cleanup_map()
    generate_project_map()
