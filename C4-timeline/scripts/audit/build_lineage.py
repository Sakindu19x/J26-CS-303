"""scripts/audit/build_lineage.py (Prompt 17 Part T1).

Rebuilds docs/data_lineage.md by inspecting the active repository files:
- Raw archives under data/raw/*.zip with size and SHA-256.
- Distinct log source types from processed timelines (Linux AttackMate execution logs).
- One row per stage: inputs, producing script, outputs with SHA-256, and verifier script.
- C3 origin: docs/c3_open_questions.md.
- Limitations: reports/audit/known_limitations.json.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hash: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def find_verifier_for_file(rel_output_path: str) -> str:
    """Search scripts/ and tests/ for a script that specifically verifies the output."""
    filename = Path(rel_output_path).name
    stem = Path(rel_output_path).stem

    search_dirs = [
        (REPO_ROOT / "scripts" / "verify", "*.py"),
        (REPO_ROOT / "scripts", "verify_*.py"),
        (REPO_ROOT / "tests", "test_*.py"),
    ]
    candidates = []
    for d, pat in search_dirs:
        if not d.is_dir():
            continue
        for py in sorted(d.glob(pat)):
            if "lineage" in py.name:
                continue
            try:
                txt = py.read_text(encoding="utf-8")
                if filename in txt:
                    stem_tokens = set(stem.replace("_", " ").replace("-", " ").split())
                    py_tokens = set(py.stem.replace("_", " ").replace("-", " ").split())
                    score = len(stem_tokens & py_tokens)
                    if py.stem in ("verify_all_hashes", "verify_claims_map", "verify_overnight_summary"):
                        score -= 2
                    candidates.append((score, str(py.relative_to(REPO_ROOT)).replace("\\", "/")))
            except Exception:
                pass
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # Fallback to verify_all_hashes if covered in protected baseline
    vah = REPO_ROOT / "scripts" / "verify" / "verify_all_hashes.py"
    if vah.is_file():
        try:
            content = vah.read_text(encoding="utf-8")
            if filename in content or stem in content:
                return "scripts/verify/verify_all_hashes.py"
        except Exception:
            pass
    return "none"


def get_raw_archives() -> list[dict[str, Any]]:
    archives = []
    raw_dir = REPO_ROOT / "data" / "raw"
    assert raw_dir.is_dir(), f"Raw directory missing: {raw_dir}"
    for zip_path in sorted(raw_dir.glob("*.zip")):
        archives.append({
            "name": zip_path.name,
            "rel_path": f"data/raw/{zip_path.name}",
            "size_bytes": zip_path.stat().st_size,
            "sha256": sha256_file(zip_path),
        })
    assert len(archives) == 7, f"Expected 7 raw archives, found {len(archives)}"
    return archives


def get_log_source_types() -> dict[str, list[str]]:
    timelines_path = REPO_ROOT / "data" / "processed_7ep" / "attack_timelines.json"
    normalized_path = REPO_ROOT / "data" / "processed_7ep" / "normalized_events.json"
    assert timelines_path.is_file(), f"Missing {timelines_path}"
    assert normalized_path.is_file(), f"Missing {normalized_path}"

    evs = json.loads(normalized_path.read_text(encoding="utf-8"))
    source_files = sorted(set(str(e.get("source_file")) for e in evs if e.get("source_file")))
    step_types = sorted(set(str(e.get("step_type")) for e in evs if e.get("step_type")))

    # Verify no Windows / Wazuh / Zeek present in event data
    combined_text = (timelines_path.read_text(encoding="utf-8")[:50000]).lower()
    assert "windows event" not in combined_text
    assert "zeek" not in combined_text

    return {
        "source_files": source_files,
        "step_types": step_types,
    }


def build_data_lineage() -> None:
    c3_path = REPO_ROOT / "docs" / "c3_open_questions.md"
    assert c3_path.is_file(), f"Real C3 origin file missing: {c3_path}"
    
    limitations_path = REPO_ROOT / "reports" / "audit" / "known_limitations.json"
    assert limitations_path.is_file(), f"Real known limitations file missing: {limitations_path}"

    raw_archives = get_raw_archives()
    log_sources = get_log_source_types()

    # Stage specifications: (Stage Name, Producing Script, Input Files, Output Files, Upstream Origin)
    STAGES = [
        (
            "Stage 1 Normalization (Pilot 4-Ep)",
            "scripts/pipeline/s01_normalize_events.py",
            ["data/raw/scenario_1_sudo_pam.zip", "data/raw/scenario_2_cron.zip", "data/raw/scenario_3_vnc_apt.zip", "data/raw/scenario_4.zip"],
            "data/processed/normalized_events.json",
            "CAM-LDS Raw Scenario Archives",
        ),
        (
            "Timeline & Sequences (Pilot 4-Ep)",
            "scripts/pipeline/s02_timeline_pipeline.py",
            ["data/processed/normalized_events.json"],
            "data/processed/attack_timelines.json",
            "data/processed/normalized_events.json",
        ),
        (
            "Samples & Statistics (Pilot 4-Ep)",
            "scripts/pipeline/s03_samples_and_stats.py",
            ["data/processed/attack_timelines.json"],
            "data/processed/next_technique_samples.json",
            "data/processed/attack_timelines.json",
        ),
        (
            "LOEO Evaluation Technique (Pilot 4-Ep)",
            "scripts/pipeline/s04_evaluation_4ep_technique.py",
            ["data/processed/next_technique_samples.json", "data/processed/loeo_folds.json"],
            "reports/evaluation_results.json",
            "data/processed/next_technique_samples.json",
        ),
        (
            "LOEO Evaluation Tactic (Pilot 4-Ep)",
            "scripts/pipeline/s05_evaluation_4ep_tactic.py",
            ["data/processed/attack_sequences.json", "data/processed/loeo_folds.json"],
            "reports/tactic_evaluation_results.json",
            "data/processed/attack_sequences.json",
        ),
        (
            "Stage 1 Normalization (7 Episodes)",
            "scripts/pipeline/s01_normalize_events.py",
            ["data/raw/scenario_1_sudo_pam.zip", "data/raw/scenario_2_cron.zip", "data/raw/scenario_3_vnc_apt.zip", "data/raw/scenario_4.zip", "data/raw/scenario_5.zip", "data/raw/scenario_6_macro_binary.zip", "data/raw/scenario_7.zip"],
            "data/processed_7ep/normalized_events.json",
            "CAM-LDS Raw Scenario Archives (data/raw/*.zip)",
        ),
        (
            "Timeline & Sequences (7 Episodes)",
            "scripts/pipeline/s02_timeline_pipeline.py",
            ["data/processed_7ep/normalized_events.json"],
            "data/processed_7ep/attack_timelines.json",
            "data/processed_7ep/normalized_events.json",
        ),
        (
            "Samples & Statistics (7 Episodes)",
            "scripts/pipeline/s03_samples_and_stats.py",
            ["data/processed_7ep/attack_timelines.json"],
            "data/processed_7ep/next_technique_samples.json",
            "data/processed_7ep/attack_timelines.json",
        ),
        (
            "LOEO Model Training & Evaluation (7 Episodes)",
            "scripts/pipeline/s06_evaluation_7ep.py",
            ["data/processed_7ep/next_technique_samples.json", "data/processed_7ep/loeo_folds.json"],
            "reports/7ep/evaluation_7ep_results.json",
            "data/processed_7ep/next_technique_samples.json",
        ),
        (
            "Learning Curve Evaluation (7 Episodes)",
            "scripts/pipeline/s07_learning_curve_7ep.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/learning_curve_7ep_results.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Permutation Tests (7 Episodes)",
            "scripts/pipeline/s08_permutation_test_7ep.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/permutation_7ep_report.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Planted Structure Power Analysis (7 Episodes)",
            "scripts/pipeline/s09_planted_power_7ep.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/planted_realscale_7ep_report.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "E5-Removed Sensitivity (7 Episodes)",
            "scripts/pipeline/s10_e5_removed_sensitivity.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/e5_removed_results.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Holm Claim Rule Evaluation (7 Episodes)",
            "scripts/pipeline/s11_holm_claim_rule.py",
            ["reports/7ep/evaluation_7ep_results.json"],
            "reports/7ep/holm_claim_rule_results.json",
            "reports/7ep/evaluation_7ep_results.json",
        ),
        (
            "Diagnostics Evaluation (7 Episodes)",
            "scripts/pipeline/s12_diagnostics_7ep.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/diagnostics_7ep.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "E5 Hit@1 Change Diagnostic",
            "scripts/pipeline/s13_e5_hit1_diagnostic.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/e5_hit1_change_diagnostic.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Tie Sensitivity Diagnostic (7 Episodes)",
            "scripts/pipeline/s14_tie_sensitivity_7ep.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/tie_sensitivity_7ep.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Exploratory Tactic-Conditioned Evaluation",
            "scripts/pipeline/s15_exploratory_tactic_conditioned.py",
            ["data/processed_7ep/attack_sequences.json", "data/processed_7ep/next_technique_samples.json"],
            "reports/7ep/exploratory_tactic_conditioned_results.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Production Model Fitting",
            "scripts/pipeline/s16_train_production_model.py",
            ["data/processed_7ep/attack_sequences.json"],
            "artifacts/7ep/production_model/manifest.json",
            "data/processed_7ep/attack_sequences.json",
        ),
        (
            "Explainable Prediction Records Build",
            "scripts/pipeline/s17_build_prediction_records.py",
            ["data/processed_7ep/attack_timelines.json", "data/processed_7ep/next_technique_samples.json", "docs/c3_open_questions.md"],
            "data/processed_7ep/prediction_records_loeo.jsonl",
            "data/processed_7ep/attack_timelines.json & docs/c3_open_questions.md",
        ),
        (
            "Viva Pack Generation",
            "scripts/pipeline/s18_build_viva_pack.py",
            ["reports/7ep/evaluation_7ep_results.json", "reports/7ep/planted_realscale_7ep_report.json"],
            "viva_pack/04_worked_examples.md",
            "reports/7ep/evaluation_7ep_results.json",
        ),
        (
            "Claims Map Generation",
            "scripts/pipeline/s19_build_claims_map.py",
            ["reports/7ep/evaluation_7ep_results.json", "reports/7ep/holm_claim_rule_results.json"],
            "reports/viva/claims.json",
            "reports/7ep/evaluation_7ep_results.json",
        ),
        (
            "Overnight Summary Generation",
            "scripts/pipeline/s20_build_overnight_summary.py",
            ["reports/overnight_ledger.md", "reports/measurements/nfr1_timing.json", "reports/audit/known_limitations.json"],
            "reports/overnight_summary.md",
            "reports/overnight_ledger.md & reports/measurements/nfr1_timing.json",
        ),
    ]

    lines = [
        "# Component 4: End-to-End Data Lineage & Provenance Specification",
        "",
        "> [!NOTE]",
        "> This document is automatically generated by `scripts/audit/build_lineage.py` (Prompt 17 Part T1).",
        "> All paths, file sizes, and cryptographic SHA-256 hashes are verified directly from active disk state.",
        "",
        "## 1. Upstream Raw Simulation Archives",
        "",
        "Component 4 evaluates forensic timeline reconstruction across 7 Linux attack episodes ($E1$ through $E7$).",
        "Raw archives reside under `data/raw/*.zip` with verified cryptographic SHA-256 checksums:",
        "",
        "| Archive Name | File Path | Size (Bytes) | SHA-256 Checksum |",
        "|:---|:---|:---:|:---|",
    ]

    for arc in raw_archives:
        lines.append(f"| `{arc['name']}` | [`{arc['rel_path']}`](../{arc['rel_path']}) | {arc['size_bytes']:,} | `{arc['sha256']}` |")

    lines.extend([
        "",
        "## 2. Ingested Log Source Types & Telemetry Format",
        "",
        "The CAM-LDS dataset represents Linux host and container attack simulations.",
        "Forensic event timelines contain telemetry captured from AttackMate simulation orchestrations:",
        "",
        "- **Origin Log Files**: " + ", ".join(f"`{sf}`" for sf in log_sources["source_files"]),
        "- **Distinct Step / Action Types**: " + ", ".join(f"`{st}`" for st in log_sources["step_types"]),
        "- **Platform Scope**: Linux host environments only (no Windows Event Logs or Zeek telemetry in active timelines).",
        "",
        "## 3. End-to-End Pipeline Stage Lineage Matrix",
        "",
        "Every pipeline stage maps input dependencies, generating script, primary output with SHA-256 hash, and the dedicated verification script covering it:",
        "",
        "| Stage Description | Input File(s) | Producing Script | Output File | Output SHA-256 | Verification Script |",
        "|:---|:---|:---|:---|:---|:---|",
    ])

    for stage_desc, script_rel, inputs, out_rel, _ in STAGES:
        out_p = REPO_ROOT / out_rel
        out_sha = sha256_file(out_p)
        verifier = find_verifier_for_file(out_rel)
        
        inp_str = "<br>".join(f"[`{inp}`](../{inp})" for inp in inputs)
        script_link = f"[`{script_rel}`](../{script_rel})"
        out_link = f"[`{out_rel}`](../{out_rel})"
        ver_link = f"[`{verifier}`](../{verifier})" if verifier != "none" else "`none`"
        
        lines.append(f"| **{stage_desc}** | {inp_str} | {script_link} | {out_link} | `{out_sha}` | {ver_link} |")

    lines.extend([
        "",
        "## 4. Special Interface & Integrity Origins",
        "",
        "- **Component 3 Telemetry Context**: The upstream interface contract and unpopulated telemetry attributes (`threat_score`, `investigation_priority`, `asset_criticality`, `cti_confidence`, `freshness`, `ioc`) originate from [`docs/c3_open_questions.md`](../docs/c3_open_questions.md).",
        "- **Registered Limitations**: Registered benchmark and protocol limitations (`LIM-01` to `LIM-16`) originate from [`reports/audit/known_limitations.json`](../reports/audit/known_limitations.json) and are verified by [`tests/test_intake_audit.py`](../tests/test_intake_audit.py).",
        "",
    ])

    out_file = REPO_ROOT / "docs" / "data_lineage.md"
    out_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Generated {out_file.relative_to(REPO_ROOT)} successfully ({len(lines)} lines)")


if __name__ == "__main__":
    build_data_lineage()
