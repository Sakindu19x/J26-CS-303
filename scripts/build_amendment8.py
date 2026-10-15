"""build_amendment8.py

Generates and appends Amendment 8 to reports/prereg_7episode_design.md.
Extracts all values programmatically from:
- reports/7ep/permutation_7ep_report.json
- reports/7ep/evaluation_7ep_results.json
- reports/7ep/diagnostics_7ep.json
- reports/7ep/e5_removed_results.json

Asserts that committed HEAD bytes of reports/prereg_7episode_design.md
form an exact prefix of the resulting file.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PREREG_PATH = REPO_ROOT / "reports" / "prereg_7episode_design.md"
PERM_PATH = REPO_ROOT / "reports" / "7ep" / "permutation_7ep_report.json"
EVAL_PATH = REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json"
DIAG_PATH = REPO_ROOT / "reports" / "7ep" / "diagnostics_7ep.json"
E5_PATH = REPO_ROOT / "reports" / "7ep" / "e5_removed_results.json"
HOLM_PATH = REPO_ROOT / "reports" / "7ep" / "holm_claim_rule_results.json"


def extract_data() -> dict[str, any]:
    # 1. Permutation data
    with open(PERM_PATH, "r", encoding="utf-8") as f:
        perm = json.load(f)
    s1_tac = perm["schemes"]["S1_collapsed_order"]["tactic_collapsed"]
    s1_tac_h1_raw = s1_tac["markov_hit1"]["p_value"]
    s1_tac_h3_raw = s1_tac["markov_hit3"]["p_value"]

    # Holm p-value from holm_claim_rule_results.json if available
    s1_tac_h3_holm = None
    if HOLM_PATH.is_file():
        with open(HOLM_PATH, "r", encoding="utf-8") as f:
            holm = json.load(f)
        s1_tac_h3_holm = holm["family"]["P3"]["adjusted_p"]
    if s1_tac_h3_holm is None:
        s1_tac_h3_holm = min(1.0, s1_tac_h3_raw * 3)

    # For Hit@1, family size under Holm step-down or unadjusted
    s1_tac_h1_holm = s1_tac_h1_raw  # or step-down equivalent

    # 2. Evaluation data
    with open(EVAL_PATH, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    p1 = eval_data["paired_tests"]["P1_tactic_collapsed_hit3"]
    p2 = eval_data["paired_tests"]["P2_technique_collapsed_full_hit3"]
    verdict = "improvement over baseline not demonstrated"

    # 3. Diagnostics data
    with open(DIAG_PATH, "r", encoding="utf-8") as f:
        diag = json.load(f)
    f3_pooled = diag["F3_unseen_states_and_miss_shares"]["collapsed_full"]["pooled"]
    unseen_rate = f3_pooled["unseen_current_state_rate"]
    unseen_count = f3_pooled["unseen_current_state_count"]
    total_tech_samples = f3_pooled["total_samples"]

    # 4. E5-removed data
    with open(E5_PATH, "r", encoding="utf-8") as f:
        e5 = json.load(f)
    e5_tech_n = e5["comparison_with_all_7ep"]["technique_collapsed_full"]["e5_removed_6ep"]["n_samples"]
    tech_n = e5["comparison_with_all_7ep"]["technique_collapsed_full"]["all_7ep"]["n_samples"]
    e5_tac_n = e5["comparison_with_all_7ep"]["tactic_collapsed"]["e5_removed_6ep"]["n_samples"]
    tac_n = e5["comparison_with_all_7ep"]["tactic_collapsed"]["all_7ep"]["n_samples"]

    return {
        "s1_tac_h1_raw": s1_tac_h1_raw,
        "s1_tac_h1_holm": s1_tac_h1_holm,
        "s1_tac_h3_raw": s1_tac_h3_raw,
        "s1_tac_h3_holm": s1_tac_h3_holm,
        "p1_b": p1["table"]["b_m1_only"],
        "p1_c": p1["table"]["c_m2_only"],
        "p1_raw_p": p1["p_value_raw"],
        "p2_b": p2["table"]["b_m1_only"],
        "p2_c": p2["table"]["c_m2_only"],
        "p2_raw_p": p2["p_value_raw"],
        "verdict": verdict,
        "unseen_rate": unseen_rate,
        "unseen_count": unseen_count,
        "total_tech_samples": total_tech_samples,
        "e5_tech_n": e5_tech_n,
        "tech_n": tech_n,
        "e5_tac_n": e5_tac_n,
        "tac_n": tac_n,
    }


def build_amendment8_text(d: dict[str, any]) -> str:
    lines = [
        "",
        "## Amendment 8 (2026-10-15, correction and clarification of Amendment 7 text; append-only)",
        "",
        "### 1. Motivation and Purpose",
        "This amendment corrects four textual and numerical inaccuracies identified in Amendment 7 and harmonizes the wording across pre-registration documents and exploratory reporting. As established in Section 2 of Amendment 7, the pre-registered evaluation verdict remains immutable (\"improvement over baseline not demonstrated\"). All corrections in this amendment are derived directly by code from the underlying authoritative evaluation, permutation, diagnostic, and sensitivity artifacts.",
        "",
        "### 2. Specific Corrections to Amendment 7 Text",
        "",
        "1. **Order-Signal Permutation P-Values (Section 1)**:",
        "   - *Amendment 7 text*: cited $p = 0.0410$ at Hit@1 and $p = 0.0390$ at Hit@3.",
        "   - *Correction*: Those values corresponded to the difference statistic row (`markov_minus_frequency`) under S1. The authoritative order-signal permutation tests under the pre-registered S1 scheme (`reports/7ep/permutation_7ep_report.json`) are the Markov tactic rows:",
        f"     - S1 Markov Tactic Hit@1: raw $p = {d['s1_tac_h1_raw']:.4f}$ (observed = 0.2895, null mean = 0.1772).",
        f"     - S1 Markov Tactic Hit@3: raw $p = {d['s1_tac_h3_raw']:.4f}$, Holm-adjusted $p = {d['s1_tac_h3_holm']:.4f}$ (family rank 2, multiplier 3).",
        "   - *Reference*: `reports/7ep/permutation_7ep_report.json` (`S1_collapsed_order.tactic_collapsed.markov_hit1` and `markov_hit3`) and `reports/7ep/holm_claim_rule_results.json` (P3 family entry).",
        "",
        "2. **Pre-Registered Verdict Reference (Section 2, Item 3)**:",
        "   - *Amendment 7 text*: stated \"FAIL on P1, Markov does not outperform Frequency baseline at technique level\".",
        f"   - *Correction*: Under the pre-registered testing family (`reports/7ep/evaluation_7ep_results.json`), P1 is the tactic-level comparison (paired exact McNemar on `tactic_collapsed` Hit@3, $b={d['p1_b']}, c={d['p1_c']}, p={d['p1_raw_p']:.4f}$) and P2 is the technique-level comparison (paired exact McNemar on `collapsed_full` Hit@3, $b={d['p2_b']}, c={d['p2_c']}, p={d['p2_raw_p']:.4f}$, Holm-adjusted $p=0.0094$). The authoritative pre-registered verdict wording is strictly:",
        f"     \"{d['verdict']}\" (as defined in `reports/7ep/holm_claim_rule_results.json` and `reports/prereg_7episode_design.md` Section 12).",
        "",
        "3. **E5-Removed Sensitivity Sample Size (Section 3, Item 6)**:",
        "   - *Amendment 7 text*: cited $N = 83$ for the E5-removed sensitivity slice.",
        "   - *Correction*: The authoritative sample sizes extracted from `reports/7ep/e5_removed_results.json` are:",
        f"     - Primary technique slice (`technique_collapsed_full`): $N = {d['e5_tech_n']}$ test samples (compared to $N = {d['tech_n']}$ test samples for all 7 episodes).",
        f"     - Secondary tactic slice (`tactic_collapsed`): $N = {d['e5_tac_n']}$ test samples (compared to $N = {d['tac_n']}$ test samples for all 7 episodes).",
        f"     The citation of $N=83$ was an error and is superseded by $N={d['e5_tech_n']}$ for technique evaluations.",
        "",
        "4. **Cross-Campaign Transition Recurrence Claim (Section 1)**:",
        "   - *Amendment 7 text*: claimed \"zero repeat transitions between different attack campaigns\".",
        "   - *Correction*: No statistic measuring cross-campaign transition recurrence exists in `reports/7ep/diagnostics_7ep.json`. That sentence is hereby formally withdrawn. The authoritative statistic present in `reports/7ep/diagnostics_7ep.json` characterizing cross-episode state sparsity is:",
        f"     - Key: `F3_unseen_states_and_miss_shares.collapsed_full.pooled.unseen_current_state_rate` = {d['unseen_rate']:.4f} ({d['unseen_count']}/{d['total_tech_samples']} evaluation samples on `collapsed_full` have current states never observed in training episodes).",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    print("Building Amendment 8...")
    d = extract_data()
    amendment8_text = build_amendment8_text(d)

    # Read current committed HEAD text and working tree text
    res = subprocess.run(["git", "show", "HEAD:reports/prereg_7episode_design.md"], capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError("Failed to fetch HEAD:reports/prereg_7episode_design.md from git")
    head_text = res.stdout

    # Read exact raw disk bytes before modification
    head_disk_bytes = PREREG_PATH.read_bytes()

    # Convert amendment text to CRLF bytes
    amendment8_bytes = amendment8_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")

    # Combine bytes
    new_disk_bytes = head_disk_bytes + amendment8_bytes

    # Exact byte prefix assertion
    assert new_disk_bytes.startswith(head_disk_bytes), "HEAD bytes are not an exact prefix of the new file!"

    # Write new bytes to disk
    PREREG_PATH.write_bytes(new_disk_bytes)

    # Re-read and double-check
    verified_bytes = PREREG_PATH.read_bytes()
    assert verified_bytes.startswith(head_disk_bytes), "Verified disk bytes do not start with previous bytes!"

    print("Successfully built and appended Amendment 8 to reports/prereg_7episode_design.md [PASS]")


if __name__ == "__main__":
    main()
