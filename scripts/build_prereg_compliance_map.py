"""build_prereg_compliance_map.py

Generates reports/audit/prereg_compliance_map.json and reports/audit/prereg_compliance_map.md.
Maps pre-registration sections 1-11 and Amendments 1-7 to:
- Output file(s)
- Script
- Verifier
- Baseline entry
- Computed status (file exists, hash matches, verifier exit code)

Also includes:
- Separate list: "analyses that are not pre-registered" (POST HOC)
- Separate list: "deviations and limits"
"""

from __future__ import annotations
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def load_all_baselines() -> dict[str, str]:
    baselines: dict[str, str] = {}
    
    # 1. Canonical Stage 1 baseline
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
    
    # 2. Stage 2 technique
    f_s2 = WORKSPACE / "reports" / "_baseline_hashes_stage2.json"
    if f_s2.is_file():
        with open(f_s2, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in d.items():
                if k.endswith(".csv"):
                    baselines[f"data/processed/{k}"] = v
                else:
                    baselines[f"reports/{k}"] = v

    # 3. Tactic
    f_tac = WORKSPACE / "reports" / "_baseline_hashes_tactic.json"
    if f_tac.is_file():
        with open(f_tac, "r", encoding="utf-8") as f:
            d = json.load(f)
            for k, v in d.items():
                if k.endswith(".csv"):
                    baselines[f"data/processed/{k}"] = v
                else:
                    baselines[f"reports/{k}"] = v

    # 4. 7ep stage 1
    f_7s1 = WORKSPACE / "reports" / "_baseline_hashes_7ep_stage1.json"
    if f_7s1.is_file():
        with open(f_7s1, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))

    # 5. 7ep eval
    f_7ev = WORKSPACE / "reports" / "_baseline_hashes_7ep_eval.json"
    if f_7ev.is_file():
        with open(f_7ev, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))

    # 6. 7ep inference
    f_7inf = WORKSPACE / "reports" / "_baseline_hashes_7ep_inference.json"
    if f_7inf.is_file():
        with open(f_7inf, "r", encoding="utf-8") as f:
            baselines.update(json.load(f))

    return baselines

def check_file(rel_path: str, baselines: dict[str, str]) -> dict:
    p = WORKSPACE / rel_path
    exists = p.exists()
    sha256 = compute_sha256(p) if exists else None
    
    norm_path = rel_path.replace("\\", "/")
    expected_sha = baselines.get(norm_path)
    hash_matches = (sha256 == expected_sha) if (exists and expected_sha) else (None if not expected_sha else False)
    
    return {
        "path": norm_path,
        "exists": exists,
        "sha256": sha256,
        "in_baseline": expected_sha is not None,
        "hash_matches": hash_matches
    }

def run_verifier(verifier_script: str | None) -> dict:
    if not verifier_script:
        return {"verifier": None, "exit_code": None, "status": "N/A"}
    
    cmd = [sys.executable, str(WORKSPACE / verifier_script)]
    try:
        proc = subprocess.run(cmd, cwd=str(WORKSPACE), capture_output=True, text=True, timeout=120)
        return {
            "verifier": verifier_script.replace("\\", "/"),
            "exit_code": proc.returncode,
            "status": "PASS" if proc.returncode == 0 else "FAIL"
        }
    except Exception as e:
        return {
            "verifier": verifier_script.replace("\\", "/"),
            "exit_code": -1,
            "error": str(e),
            "status": "ERROR"
        }

PREREG_SECTIONS = [
    {
        "id": "Section 1",
        "title": "Episodes and Archive Identification",
        "files": ["reports/raw_archive_hashes.json", "reports/raw_archive_hashes_extended.json", "docs/data_provenance.md"],
        "script": "scripts/build_data_provenance.py",
        "verifier": "scripts/verify_all_hashes.py"
    },
    {
        "id": "Section 2",
        "title": "Folds and Partitioning",
        "files": ["data/processed_7ep/attack_sequences.json", "reports/7ep/evaluation_7ep_results.json"],
        "script": "scripts/build_processed_7ep.py",
        "verifier": "scripts/verify_stage1_7ep.py"
    },
    {
        "id": "Section 3",
        "title": "Evaluation Slices",
        "files": ["data/processed_7ep/attack_sequences.json", "reports/7ep/evaluation_7ep_results.json"],
        "script": "scripts/run_evaluation_7ep.py",
        "verifier": "scripts/verify_evaluation_7ep.py"
    },
    {
        "id": "Section 4",
        "title": "Models and Tuning Constraints",
        "files": ["artifacts/7ep/production_model/manifest.json", "reports/7ep/evaluation_7ep_results.json"],
        "script": "scripts/train_production_model.py",
        "verifier": "scripts/verify_prediction_records.py"
    },
    {
        "id": "Section 5",
        "title": "Evaluation Metrics",
        "files": ["reports/7ep/evaluation_7ep_results.json", "reports/7ep/evaluation_7ep_report.md"],
        "script": "scripts/run_evaluation_7ep.py",
        "verifier": "scripts/verify_evaluation_7ep.py"
    },
    {
        "id": "Section 6",
        "title": "Primary Hypotheses and Statistical Comparisons",
        "files": ["reports/7ep/evaluation_7ep_results.json", "reports/7ep/evaluation_7ep_report.md"],
        "script": "scripts/run_evaluation_7ep.py",
        "verifier": "scripts/verify_holm_claim_rule.py"
    },
    {
        "id": "Section 7",
        "title": "Learning Curve Protocol",
        "files": ["reports/7ep/learning_curve_7ep_results.json", "reports/7ep/learning_curve_7ep_report.md"],
        "script": "scripts/run_learning_curve_7ep.py",
        "verifier": "scripts/verify_learning_curve_7ep.py"
    },
    {
        "id": "Section 8",
        "title": "Handling of Episode E5 (Sensitivity Analysis)",
        "files": ["reports/7ep/e5_removed_results.json", "reports/7ep/e5_removed_report.md"],
        "script": "scripts/run_sensitivity_analysis_e5.py",
        "verifier": "scripts/verify_e5_removed.py"
    },
    {
        "id": "Section 9",
        "title": "Real-Scale Planted Structure Power Analysis (A4 Re-Run)",
        "files": ["reports/7ep/planted_realscale_7ep_report.json", "reports/7ep/planted_realscale_7ep_report.md"],
        "script": "scripts/run_planted_realscale_7ep.py",
        "verifier": "scripts/verify_planted_realscale_7ep.py"
    },
    {
        "id": "Section 10",
        "title": "Permutation Null Hypotheses at 7 Episodes",
        "files": ["reports/7ep/permutation_7ep_report.json", "reports/7ep/permutation_7ep_report.md"],
        "script": "scripts/run_permutation_test_7ep.py",
        "verifier": "scripts/verify_permutation_7ep.py"
    },
    {
        "id": "Section 11",
        "title": "Immutability and Pre-Registration Protocol",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to 7-ep inference (commit 2cf7786)",
        "verifier": None
    }
]

AMENDMENTS = [
    {
        "id": "Amendment 1",
        "title": "Corrections to Sec 1, 4, 5, 8, 9, 6, 10 before inference",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to 7-ep inference (commit d6f3764)",
        "verifier": None
    },
    {
        "id": "Amendment 2",
        "title": "Scope & correction of scenario_6_macro_library and supersession",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to 7-ep inference (commit 3a6b306)",
        "verifier": None
    },
    {
        "id": "Amendment 3",
        "title": "Verbatim original heading titles & repository search count",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to 7-ep inference (commit ad25883)",
        "verifier": None
    },
    {
        "id": "Amendment 4",
        "title": "Retraction of informal titles & record of Amendment 1 changes",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to 7-ep inference (commit 3ffba13)",
        "verifier": None
    },
    {
        "id": "Amendment 5",
        "title": "Verification of committed repository text vs chat report",
        "files": ["reports/prereg_7episode_design.md"],
        "script": "Committed prior to result interpretation (commit 2d68ae5)",
        "verifier": None
    },
    {
        "id": "Amendment 6",
        "title": "Wording and verification only; no numbers change",
        "files": [
            "reports/7ep/permutation_7ep_report.md",
            "reports/permutation_test_v2_report.md",
            "scripts/mutation_sweep.py",
            "scripts/verify_evaluation.py"
        ],
        "script": "scripts/verify_evaluation.py",
        "verifier": "scripts/verify_evaluation.py"
    },
    {
        "id": "Amendment 7",
        "title": "Exploratory post hoc variant (Tactic-Conditioned Technique Prediction)",
        "files": [
            "reports/7ep/exploratory_tactic_conditioned_results.json",
            "reports/7ep/exploratory_tactic_conditioned_report.md",
            "data/processed_7ep/exploratory_tactic_conditioned_predictions.csv"
        ],
        "script": "scripts/run_exploratory_variant.py",
        "verifier": "scripts/verify_exploratory_tactic_conditioned.py"
    }
]

NON_PREREG_ANALYSES = [
    {
        "name": "diagnostics_7ep",
        "type": "POST HOC",
        "description": "Cross-episode vocabulary overlap and transition diagnostic analyzing zero repeat transitions between different attack campaigns.",
        "files": ["reports/7ep/diagnostics_7ep.json", "reports/7ep/diagnostics_7ep.md"],
        "script": "scripts/run_diagnostics_7ep.py",
        "verifier": "scripts/verify_all_hashes.py"
    },
    {
        "name": "e5_hit1_change_diagnostic",
        "type": "POST HOC",
        "description": "Diagnostic investigation of Episode E5 Hit@1 score behavior under LOEO cross-validation.",
        "files": ["reports/audit/e5_hit1_change_diagnostic.md"],
        "script": "scripts/run_e5_hit1_change_diagnostic.py",
        "verifier": "scripts/verify_e5_hit1_diagnostic.py"
    },
    {
        "name": "tie_sensitivity_7ep",
        "type": "POST HOC",
        "description": "Systematic tie-sensitivity analysis of Markov and Frequency predictions across all 171 LOEO prediction records under min, max, and random tie-breaking.",
        "files": ["reports/7ep/tie_sensitivity_7ep.json", "reports/7ep/tie_sensitivity_7ep.md"],
        "script": "scripts/run_tie_sensitivity_7ep.py",
        "verifier": "scripts/verify_tie_sensitivity_7ep.py"
    },
    {
        "name": "exploratory_tactic_conditioned",
        "type": "POST HOC",
        "description": "Tactic-conditioned technique prediction variant pre-declared under Amendment 7 to evaluate whether tactic order signals project onto technique candidates.",
        "files": [
            "reports/7ep/exploratory_tactic_conditioned_results.json",
            "reports/7ep/exploratory_tactic_conditioned_report.md",
            "data/processed_7ep/exploratory_tactic_conditioned_predictions.csv"
        ],
        "script": "scripts/run_exploratory_variant.py",
        "verifier": "scripts/verify_exploratory_tactic_conditioned.py"
    }
]

DEVIATIONS_AND_LIMITS = [
    {
        "id": "G8 loose",
        "category": "Pre-registration Gate Limit",
        "description": "In synthetic real-scale planted structure analysis (reports/7ep/planted_realscale_7ep_report.md), gate G8 bound |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE) was loose at small sample sizes (V=82), though recovered consistency at larger sequence lengths.",
        "impact": "Documented in planted real-scale report; G9 and G10 passed unconditionally."
    },
    {
        "id": "A2 history not reproducible",
        "category": "Historical Reproducibility Limit",
        "description": "Historical intermediary files from early 4-episode A2 exploration cannot be recreated bit-for-bit identically due to missing random seeds in initial exploratory scratch scripts. All final reports and baselines remain frozen and verified.",
        "impact": "Confined strictly to early scratch exploration history; does not affect any 4-episode or 7-episode benchmark conclusions."
    },
    {
        "id": "S2 excluded at 7 episodes",
        "category": "Null Hypothesis Protocol Modification",
        "description": "Scheme S2 (unconstrained adjacent shuffle) was excluded in the 7-episode pre-registration design because 4-episode analysis proved it produces artificial adjacent identical transitions absent in collapsed sequences. Replaced by S1 (headline) and S3 (constrained).",
        "impact": "Pre-registered and adhered to; S2 rows in 4-episode reports are marked as invalid nulls per 12c Rule C."
    },
    {
        "id": "Amendment 6 wording changes",
        "category": "Reporting Neutralization",
        "description": "Speculative causal statements in permutation test reporting scripts were neutralized to factual difference statistic statements; Markov-minus-Frequency conclusion strings updated to explicitly state they do not test Markov vs Frequency (which is P1/P2).",
        "impact": "Purely wording and verifier enhancements; zero experimental numbers or test results were modified."
    }
]

def main():
    baselines = load_all_baselines()
    
    # Process sections
    section_results = []
    for s in PREREG_SECTIONS:
        f_results = [check_file(f, baselines) for f in s["files"]]
        v_res = run_verifier(s["verifier"])
        all_files_ok = all(fr["exists"] and (fr["hash_matches"] is not False) for fr in f_results)
        verifier_ok = v_res["status"] in ("PASS", "N/A")
        overall = "COMPLIANT" if (all_files_ok and verifier_ok) else "NON_COMPLIANT"
        section_results.append({
            "section": s["id"],
            "title": s["title"],
            "files": f_results,
            "script": s["script"],
            "verifier_result": v_res,
            "status": overall
        })
        
    # Process amendments
    amendment_results = []
    for a in AMENDMENTS:
        f_results = [check_file(f, baselines) for f in a["files"]]
        v_res = run_verifier(a["verifier"])
        all_files_ok = all(fr["exists"] and (fr["hash_matches"] is not False) for fr in f_results)
        verifier_ok = v_res["status"] in ("PASS", "N/A")
        overall = "COMPLIANT" if (all_files_ok and verifier_ok) else "NON_COMPLIANT"
        amendment_results.append({
            "amendment": a["id"],
            "title": a["title"],
            "files": f_results,
            "script": a["script"],
            "verifier_result": v_res,
            "status": overall
        })
        
    # Process non-prereg analyses
    non_prereg_results = []
    for np_item in NON_PREREG_ANALYSES:
        f_results = [check_file(f, baselines) for f in np_item["files"]]
        v_res = run_verifier(np_item["verifier"])
        all_files_ok = all(fr["exists"] and (fr["hash_matches"] is not False) for fr in f_results)
        verifier_ok = v_res["status"] in ("PASS", "N/A")
        overall = "VERIFIED_POST_HOC" if (all_files_ok and verifier_ok) else "NON_COMPLIANT"
        non_prereg_results.append({
            "name": np_item["name"],
            "type": np_item["type"],
            "description": np_item["description"],
            "files": f_results,
            "script": np_item["script"],
            "verifier_result": v_res,
            "status": overall
        })
        
    compliance_data = {
        "prereg_sections": section_results,
        "amendments": amendment_results,
        "non_prereg_analyses": non_prereg_results,
        "deviations_and_limits": DEVIATIONS_AND_LIMITS
    }
    
    out_dir = WORKSPACE / "reports" / "audit"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "prereg_compliance_map.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(compliance_data, f, indent=2)
    print(f"Wrote {json_path}")
    
    # Generate Markdown
    md_path = out_dir / "prereg_compliance_map.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Pre-Registration Compliance Map\n\n")
        f.write("Generated automatically by `scripts/build_prereg_compliance_map.py`.\n")
        f.write("Maps pre-registration sections 1–11 and Amendments 1–7 to output files, scripts, verifiers, baseline entries, and computed statuses.\n\n")
        
        f.write("## 1. Pre-Registration Protocol Compliance (Sections 1–11)\n\n")
        f.write("| Section | Title | Output File(s) | Verifier | Baseline Match | Verifier Status | Overall |\n")
        f.write("|:---|:---|:---|:---|:---:|:---:|:---:|\n")
        for s in section_results:
            files_str = "<br>".join([f"`{fr['path']}`" for fr in s["files"]])
            v_name = s["verifier_result"]["verifier"] or "N/A"
            v_stat = s["verifier_result"]["status"]
            b_match = "TRUE" if all(fr["hash_matches"] is True for fr in s["files"]) else ("MIXED" if any(fr["hash_matches"] is True for fr in s["files"]) else "N/A")
            f.write(f"| **{s['section']}** | {s['title']} | {files_str} | `{v_name}` | {b_match} | {v_stat} | **{s['status']}** |\n")
            
        f.write("\n## 2. Pre-Registration Amendments (Amendments 1–7)\n\n")
        f.write("| Amendment | Title | Output File(s) | Verifier | Baseline Match | Verifier Status | Overall |\n")
        f.write("|:---|:---|:---|:---|:---:|:---:|:---:|\n")
        for a in amendment_results:
            files_str = "<br>".join([f"`{fr['path']}`" for fr in a["files"]])
            v_name = a["verifier_result"]["verifier"] or "N/A"
            v_stat = a["verifier_result"]["status"]
            b_match = "TRUE" if all(fr["hash_matches"] is True for fr in a["files"]) else ("MIXED" if any(fr["hash_matches"] is True for fr in a["files"]) else "N/A")
            f.write(f"| **{a['amendment']}** | {a['title']} | {files_str} | `{v_name}` | {b_match} | {v_stat} | **{a['status']}** |\n")
            
        f.write("\n## 3. Analyses That Are Not Pre-Registered\n\n")
        f.write("The following analyses were conceived and executed post hoc to investigate specific diagnostic findings. Each is explicitly designated **POST HOC** and does not alter the pre-registered hypothesis test verdict.\n\n")
        f.write("| Analysis Name | Classification | Description | Key Output Files | Script / Verifier |\n")
        f.write("|:---|:---:|:---|:---|:---|\n")
        for np in non_prereg_results:
            files_str = ", ".join([f"`{fr['path']}`" for fr in np["files"]])
            v_str = f"`{np['script']}` / `{np['verifier_result']['verifier'] or 'N/A'}`"
            f.write(f"| **{np['name']}** | `{np['type']}` | {np['description']} | {files_str} | {v_str} |\n")
            
        f.write("\n## 4. Deviations and Limits\n\n")
        f.write("| Deviation / Limit ID | Category | Description | Impact |\n")
        f.write("|:---|:---|:---|:---|\n")
        for d in DEVIATIONS_AND_LIMITS:
            f.write(f"| **{d['id']}** | {d['category']} | {d['description']} | {d['impact']} |\n")
            
    print(f"Wrote {md_path}")

if __name__ == "__main__":
    main()
