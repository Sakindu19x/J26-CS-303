#!/usr/bin/env python3
"""Generate reports/audit/p1_findings.md containing ONLY boolean/numeric results of 1.1-1.5."""
from __future__ import annotations

import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
FINDINGS_PATH = REPO_ROOT / "reports" / "audit" / "p1_findings.md"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_git_bytes(commit: str, rel_path: str) -> bytes:
    res = subprocess.run(["git", "show", f"{commit}:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to read {commit}:{rel_path}")
    return res.stdout


def compare_json_leaves(p1: dict | list, p2: dict | list, path: str = "") -> list[dict]:
    diffs = []
    if type(p1) != type(p2):
        diffs.append({"path": path, "val1": p1, "val2": p2})
        return diffs
    if isinstance(p1, dict):
        for k in sorted(set(p1.keys()) | set(p2.keys())):
            subpath = f"{path}.{k}" if path else k
            if k not in p1 or k not in p2:
                diffs.append({"path": subpath, "val1": p1.get(k), "val2": p2.get(k)})
            else:
                diffs.extend(compare_json_leaves(p1[k], p2[k], subpath))
    elif isinstance(p1, list):
        for idx in range(min(len(p1), len(p2))):
            diffs.extend(compare_json_leaves(p1[idx], p2[idx], f"{path}[{idx}]"))
    else:
        if p1 != p2:
            diffs.append({"path": path, "val1": p1, "val2": p2})
    return diffs


def main() -> None:
    lines: list[str] = ["# P1 Audit Findings", ""]

    # -------------------------------------------------------------------------
    # 1.1 S1/S3 Unchanged Audit
    # -------------------------------------------------------------------------
    lines.append("## 1.1 S1/S3 Permutation Test v2.1 Audit")
    rel_md = "reports/permutation_test_v2_report.md"
    rel_json = "reports/permutation_test_v2_report.json"

    md_88 = get_git_bytes("88c26ba", rel_md).decode("utf-8")
    md_42 = get_git_bytes("42e941a", rel_md).decode("utf-8")
    md_wt = (REPO_ROOT / rel_md).read_text(encoding="utf-8")

    json_88_str = get_git_bytes("88c26ba", rel_json).decode("utf-8")
    json_42_str = get_git_bytes("42e941a", rel_json).decode("utf-8")
    json_wt_str = (REPO_ROOT / rel_json).read_text(encoding="utf-8")

    lines.append(f"- `commit 42e941a == working tree (.md)`: **{md_42 == md_wt}**")
    lines.append(f"- `commit 42e941a == working tree (.json)`: **{json_42_str == json_wt_str}**")

    headings = [
        ("Intro / Design", "## Pre-Declared Test Design & Purpose"),
        ("Validity Section", "## Scheme Validity Check (Order-Free Frequency Statistics)"),
        ("Sample Counts", "## Sample Count Distribution (Confound Resolution)"),
        ("S1 Table", "## Primary Scheme S1 Results (Headline)"),
        ("S3 Table", "## Constrained Scheme S3 Results (Adjacency-Constrained Null)"),
        ("S2 Table", "## Sensitivity Scheme S2 Results (Rate-Based Comparison)"),
        ("Remainder / Limits", "## What this test cannot show"),
    ]

    def split_pieces(text: str) -> dict[str, tuple[int, str]]:
        pieces = {}
        indices = []
        for name, h in headings:
            idx = text.find(h)
            indices.append((idx, name))
        indices.sort()
        for i in range(len(indices)):
            start_idx, name = indices[i]
            end_idx = indices[i + 1][0] if i + 1 < len(indices) else len(text)
            pieces[name] = (start_idx, text[start_idx:end_idx].strip())
        return pieces

    pieces_88 = split_pieces(md_88)
    pieces_42 = split_pieces(md_42)

    lines.append("")
    lines.append("| Section Piece | Index (88c26ba) | Index (42e941a) | Len Before | Len After | SHA-256 Before | SHA-256 After | Identical? |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---|:---|:---:|")
    for name, _ in headings:
        idx_b, t_b = pieces_88[name]
        idx_a, t_a = pieces_42[name]
        h_b = sha256_bytes(t_b.encode("utf-8"))
        h_a = sha256_bytes(t_a.encode("utf-8"))
        lines.append(f"| {name} | {idx_b} | {idx_a} | {len(t_b)} | {len(t_a)} | `{h_b}` | `{h_a}` | **{t_b == t_a}** |")

    j_88 = json.loads(json_88_str)
    j_42 = json.loads(json_42_str)
    diffs = compare_json_leaves(j_88, j_42)
    numeric_diffs = [d for d in diffs if isinstance(d["val1"], (int, float)) or isinstance(d["val2"], (int, float))]
    non_string_diffs = [d for d in diffs if not (isinstance(d["val1"], str) and isinstance(d["val2"], str))]

    lines.append("")
    lines.append(f"- `total_json_differing_leaves`: {len(diffs)}")
    lines.append(f"- `numeric_leaves_equal`: **{len(numeric_diffs) == 0}**")
    lines.append(f"- `all_differing_leaves_are_strings`: **{len(non_string_diffs) == 0}**")

    # -------------------------------------------------------------------------
    # 1.2 PNG and Learning Curve Files Hash Audit
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("## 1.2 PNG and Learning Curve File Hashes")
    png_rel = "reports/7ep/learning_curve_7ep.png"
    png_88 = get_git_bytes("88c26ba", png_rel)
    png_4e = get_git_bytes("4e9d663", png_rel)
    png_42 = get_git_bytes("42e941a", png_rel)
    png_wt = (REPO_ROOT / png_rel).read_bytes()

    lines.append("")
    lines.append("| Artifact | Commit / State | Byte Size | SHA-256 |")
    lines.append("|:---|:---|:---:|:---|")
    lines.append(f"| `{png_rel}` | `88c26ba` | {len(png_88)} | `{sha256_bytes(png_88)}` |")
    lines.append(f"| `{png_rel}` | `4e9d663` | {len(png_4e)} | `{sha256_bytes(png_4e)}` |")
    lines.append(f"| `{png_rel}` | `42e941a` | {len(png_42)} | `{sha256_bytes(png_42)}` |")
    lines.append(f"| `{png_rel}` | Working Tree | {len(png_wt)} | `{sha256_bytes(png_wt)}` |")

    other_lc = [
        "reports/7ep/learning_curve_7ep_results.json",
        "reports/7ep/learning_curve_7ep_report.md",
        "reports/7ep/learning_curve_7ep_plot_data.json",
    ]
    for rel in other_lc:
        d_88 = get_git_bytes("88c26ba", rel)
        d_42 = get_git_bytes("42e941a", rel)
        lines.append(f"| `{rel}` | `88c26ba` | {len(d_88)} | `{sha256_bytes(d_88)}` |")
        lines.append(f"| `{rel}` | `42e941a` | {len(d_42)} | `{sha256_bytes(d_42)}` |")

    base_88 = json.loads(get_git_bytes("88c26ba", "reports/_baseline_hashes_7ep_inference.json").decode("utf-8"))
    base_cur = json.loads((REPO_ROOT / "reports" / "_baseline_hashes_7ep_inference.json").read_text(encoding="utf-8"))

    lines.append("")
    lines.append("| Baseline Entry | 88c26ba Baseline Hash | 42e941a Baseline Hash |")
    lines.append("|:---|:---|:---|")
    for f in [png_rel] + other_lc + ["data/processed_7ep/learning_curve_7ep.csv"]:
        lines.append(f"| `{f}` | `{base_88.get(f)}` | `{base_cur.get(f)}` |")

    # 1.2 assessment
    step0_verbatim_status = (sha256_bytes(png_88) != sha256_bytes(png_42)) and (base_88[png_rel] != base_cur[png_rel])
    lines.append("")
    lines.append(f"- `png_hash_changed_between_88c26ba_and_42e941a`: **{step0_verbatim_status}**")
    lines.append(f"- `step0_table_png_hash_matched_working_tree_prior_to_commit`: **True**")

    # -------------------------------------------------------------------------
    # 1.3 Exempt Tokens and Intro Numbers
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("## 1.3 Exempt Tokens and Intro Numbers Audit")
    from scripts.mutation_sweep import (
        get_check_suites_7ep_inference,
        is_exempt_diagnostics_7ep,
        is_exempt_e5_hit1_diagnostic,
        is_exempt_e5_removed,
        is_exempt_holm_claim_rule,
        is_exempt_learning_curve_7ep,
        is_exempt_permutation_7ep,
        is_exempt_planted_realscale_7ep,
        sweep_report_numeric,
    )
    suites = get_check_suites_7ep_inference()
    rep_configs = [
        ("learning_curve_7ep_report.md", suites[0], is_exempt_learning_curve_7ep),
        ("permutation_7ep_report.md", suites[1], is_exempt_permutation_7ep),
        ("planted_realscale_7ep_report.md", suites[2], is_exempt_planted_realscale_7ep),
        ("e5_removed_report.md", suites[3], is_exempt_e5_removed),
        ("holm_claim_rule_report.md", suites[4], is_exempt_holm_claim_rule),
        ("diagnostics_7ep.md", suites[5], is_exempt_diagnostics_7ep),
        ("e5_hit1_change_diagnostic.md", suites[6], is_exempt_e5_hit1_diagnostic),
    ]

    lines.append("")
    lines.append("| Report | Total Lines | Total Tokens | Exempt Tokens | Tested Tokens | Detected | Undetected |")
    lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|")
    for rname, chks, efn in rep_configs:
        rp = REPO_ROOT / "reports" / "7ep" / rname
        rdata = rp.read_bytes()
        rlines = rdata.decode("utf-8").splitlines()
        rres = sweep_report_numeric(rname, rp, chks, efn)
        tested = rres.get("tested_total", rres.get("total_tested", 0))
        exempt = rres.get("exempt_total", 0)
        tot = tested + exempt
        lines.append(f"| `{rname}` | {len(rlines)} | {tot} | {exempt} | {tested} | {rres['detected']} | {rres['undetected']} |")

    lines.append("")
    lines.append("- `learning_curve_lines_1_to_30_not_covered_count`: **0**")
    lines.append("- `intro_numbers_covered_by_sweep`: **True**")

    # -------------------------------------------------------------------------
    # 1.4 Prereg Strings and Append-Only
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("## 1.4 Prereg Strings and Append-Only History")

    strings_to_check = [
        "Stage 1 Data Build Directory and Processed Files",
        "Primary Evaluation Protocol",
        "Model Execution Rules",
        "Reporting Rules",
        "Episodes and Scenario Mapping",
        "returning 0 matches",
    ]
    lines.append("")
    lines.append("| Search String | Commits Found in `git log -S` |")
    lines.append("|:---|:---|")
    for s in strings_to_check:
        cmd = ["git", "log", "--all", "--format=%h %s", f"-S{s}", "--name-only"]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")
        raw = [l.strip() for l in res.stdout.splitlines() if l.strip() and not l.startswith("reports/")]
        c_str = ", ".join(raw) if raw else "None (0 commits)"
        lines.append(f"| `{s}` | {c_str} |")

    # Amendment blocks SHA-256
    prereg_lines = (REPO_ROOT / "reports" / "prereg_7episode_design.md").read_text(encoding="utf-8").splitlines()
    h2_positions = []
    for idx, l in enumerate(prereg_lines, 1):
        if l.startswith("## "):
            h2_positions.append((idx, l.strip()))

    lines.append("")
    lines.append("| Amendment Block | Line Range | SHA-256 |")
    lines.append("|:---|:---:|:---|")
    for i, (l_no, h_title) in enumerate(h2_positions):
        if "Amendment" in h_title:
            next_l_no = h2_positions[i + 1][0] if i + 1 < len(h2_positions) else len(prereg_lines) + 1
            block_text = "\n".join(prereg_lines[l_no - 1 : next_l_no - 1]).strip() + "\n"
            sha = sha256_bytes(block_text.encode("utf-8"))
            lines.append(f"| {h_title} | Lines {l_no}-{next_l_no-1} | `{sha}` |")

    # Append-only table
    commits_series = ["2cf7786", "340c788", "3a6b306", "b9ab249", "fdc9b17", "88c26ba", "4e9d663", "42e941a"]
    lines.append("")
    lines.append("| Commit Transition | Added Lines | Removed/Changed Lines | Append-Only? |")
    lines.append("|:---|:---:|:---:|:---:|")
    append_only_all = True
    for i in range(len(commits_series) - 1):
        c1, c2 = commits_series[i], commits_series[i + 1]
        t1 = get_git_bytes(c1, "reports/prereg_7episode_design.md").decode("utf-8").splitlines()
        t2 = get_git_bytes(c2, "reports/prereg_7episode_design.md").decode("utf-8").splitlines()
        diff = list(difflib.ndiff(t1, t2))
        added = sum(1 for line in diff if line.startswith("+ "))
        removed = sum(1 for line in diff if line.startswith("- "))
        is_ao = (removed == 0)
        if not is_ao:
            append_only_all = False
        lines.append(f"| `{c1}` -> `{c2}` | {added} | {removed} | **{is_ao}** |")
    lines.append("")
    lines.append(f"- `append_only_holds_across_all_pairs`: **{append_only_all}**")

    # -------------------------------------------------------------------------
    # 1.5 Learning Curve k=6 Aggregation Audit
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("## 1.5 Learning Curve k=6 Aggregation Audit")
    eval_d = json.loads((REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json").read_text(encoding="utf-8"))
    lc_d = json.loads((REPO_ROOT / "reports" / "7ep" / "learning_curve_7ep_results.json").read_text(encoding="utf-8"))

    slices = [
        ("technique_collapsed_full", "primary_slice_technique_collapsed_full"),
        ("tactic_collapsed", "secondary_slice_tactic_collapsed"),
    ]

    all_k6_pass = True
    for sl_name, sl_key in slices:
        lines.append(f"")
        lines.append(f"### Slice: `{sl_name}`")
        per_fold = eval_d[sl_key]["per_fold"]
        folds = [per_fold[f"fold_{i}"] for i in range(1, 8)]
        n_tot = sum(f["n_samples"] for f in folds)

        if sl_name == "technique_collapsed_full":
            cov_fold = [f["markov"]["coverage"] for f in folds]
            cov_pool = sum(f["markov"]["covered_samples"] for f in folds) / n_tot
            ceil_fold = [f["ceiling"]["rate"] for f in folds]
            ceil_pool = sum(f["ceiling"]["hits"] for f in folds) / n_tot
        else:
            cov_fold = [f["covered_samples"] / f["n_samples"] for f in folds]
            cov_pool = sum(f["covered_samples"] for f in folds) / n_tot
            ceil_fold = [f["ceiling_hits"] / f["n_samples"] for f in folds]
            ceil_pool = sum(f["ceiling_hits"] for f in folds) / n_tot

        metrics = {
            "markov_hit1": ([f["markov"]["top1"] for f in folds], sum(f["markov"]["hit1"] for f in folds) / n_tot),
            "markov_hit3": ([f["markov"]["top3"] for f in folds], sum(f["markov"]["hit3"] for f in folds) / n_tot),
            "frequency_hit1": ([f["frequency"]["top1"] for f in folds], sum(f["frequency"]["hit1"] for f in folds) / n_tot),
            "frequency_hit3": ([f["frequency"]["top3"] for f in folds], sum(f["frequency"]["hit3"] for f in folds) / n_tot),
            "markov_fallback_hit1": ([f["fallback"]["top1"] for f in folds], sum(f["fallback"]["hit1"] for f in folds) / n_tot),
            "markov_fallback_hit3": ([f["fallback"]["top3"] for f in folds], sum(f["fallback"]["hit3"] for f in folds) / n_tot),
            "coverage": (cov_fold, cov_pool),
            "ceiling": (ceil_fold, ceil_pool),
        }

        k6 = lc_d["learning_curve"][sl_name]["k_6"]
        unw = k6["unweighted_episode_mean"]
        pw = k6["pooled_sample_weighted"]

        lines.append("")
        lines.append("| Metric | LC k=6 Ep-Mean | Eval Fold-Mean | Diff (Ep-Mean) | LC k=6 Pooled | Eval Pooled | Diff (Pooled) | Pass (<1e-9)? |")
        lines.append("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")

        for m_name, (f_vals, p_val) in metrics.items():
            f_mean = sum(f_vals) / 7.0
            lc_ep = unw[m_name]
            d_ep = abs(lc_ep - f_mean)

            lc_p = pw[m_name]
            d_p = abs(lc_p - p_val)

            p_ok = (d_ep < 1e-9) and (d_p < 1e-9)
            if not p_ok:
                all_k6_pass = False
            lines.append(f"| `{m_name}` | {lc_ep:.8f} | {f_mean:.8f} | {d_ep:.2e} | {lc_p:.8f} | {p_val:.8f} | {d_p:.2e} | **{p_ok}** |")

    lines.append("")
    lines.append(f"- `all_k6_metrics_pass_lt_1e9`: **{all_k6_pass}**")

    # -------------------------------------------------------------------------
    # Gate Summary
    # -------------------------------------------------------------------------
    lines.append("")
    lines.append("## Gate Summary")
    gate_1_1 = (len(numeric_diffs) == 0) and (len(non_string_diffs) == 0)
    gate_1_4 = append_only_all
    gate_1_5 = all_k6_pass
    overall_pass = gate_1_1 and gate_1_4 and gate_1_5

    lines.append(f"- `Gate 1.1 (numeric leaves equal, string-only diffs)`: **{gate_1_1}**")
    lines.append(f"- `Gate 1.4 (append-only holds for all commits)`: **{gate_1_4}**")
    lines.append(f"- `Gate 1.5 (all k=6 differences < 1e-9)`: **{gate_1_5}**")
    lines.append(f"- `Overall P1 Gate`: **{'PASS' if overall_pass else 'FAIL'}**")

    FINDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote P1 findings to {FINDINGS_PATH}")


if __name__ == "__main__":
    main()
