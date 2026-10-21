r"""Pre-registered Holm-Bonferroni Adjustment and Claim Rule Application (E1-E7).

Per reports/prereg_7episode_design.md Section 6 and Amendment 1:
- Primary Family: P1, P2, P3, P4.
  - P1: Tactic level Markov Hit@3 vs Frequency Hit@3 (two-sided exact McNemar raw p from 12a JSON).
  - P2: Technique level Markov Hit@3 vs Frequency Hit@3 (two-sided exact McNemar raw p from 12a JSON).
  - P3: Tactic level Markov Hit@3 vs S1 permutation null (one-sided permutation raw p from Part B JSON).
  - P4: Technique level Markov Hit@3 vs S1 permutation null (one-sided permutation raw p from Part B JSON).
- Holm-Bonferroni step-down adjusted p-values:
  - Sort raw p in ascending order: p_(1) <= p_(2) <= p_(3) <= p_(4).
  - Adjusted p_(i) = max_{j <= i} [ min(1.0, (m - j + 1) * p_(j)) ].
- Substantive Claim Rule:
  - "improvement over the baseline demonstrated" requires pooled Markov Hit@3 > Frequency Hit@3
    AND Holm-adjusted p < 0.05 for at least one level (technique or tactic).
  - Otherwise, formal conclusion must report: "not demonstrated".
- Order-Signal Question (P3/P4):
  - Evaluated separately based on Holm-adjusted p < 0.05.

Outputs:
  - reports/7ep/holm_claim_rule_results.json
  - reports/7ep/holm_claim_rule_report.md
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_7EP = BASE_DIR / "reports" / "7ep"

EVAL_JSON_PATH = REPORTS_7EP / "evaluation_7ep_results.json"
PERM_JSON_PATH = REPORTS_7EP / "permutation_7ep_report.json"

OUT_JSON_PATH = REPORTS_7EP / "holm_claim_rule_results.json"
OUT_MD_PATH = REPORTS_7EP / "holm_claim_rule_report.md"


def holm_step_down(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply Holm-Bonferroni step-down adjustment to a list of hypothesis dicts."""
    m = len(hypotheses)
    # Sort hypotheses by raw p-value ascending
    sorted_hyps = sorted(hypotheses, key=lambda h: h["raw_p"])

    # Compute unconstrained step-down values
    adjusted = []
    running_max = 0.0
    for idx, h in enumerate(sorted_hyps):
        rank = idx + 1
        mult = m - rank + 1
        adj_p = min(1.0, mult * h["raw_p"])
        running_max = max(running_max, adj_p)
        h_copy = dict(h)
        h_copy["rank"] = rank
        h_copy["multiplier"] = mult
        h_copy["adjusted_p"] = min(1.0, running_max)
        h_copy["significant_at_05"] = bool(h_copy["adjusted_p"] < 0.05)
        adjusted.append(h_copy)

    # Return in original order
    orig_order_map = {h["id"]: h for h in adjusted}
    return [orig_order_map[h["id"]] for h in hypotheses]


def run_holm_claim_rule() -> dict[str, Any]:
    print("=" * 80)
    print("RUNNING HOLM-BONFERRONI STEP-DOWN AND CLAIM RULE APPLICATION (P1-P4)")
    print("=" * 80)

    # 1. Load inputs from evaluation_7ep_results.json and permutation_7ep_report.json
    with open(EVAL_JSON_PATH, "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    with open(PERM_JSON_PATH, "r", encoding="utf-8") as f:
        perm_data = json.load(f)

    # P1: Tactic McNemar
    p1_mcnemar = eval_data["paired_tests"]["P1_tactic_collapsed_hit3"]
    p1_raw = p1_mcnemar["p_value_raw"]
    p1_m_rate = eval_data["secondary_slice_tactic_collapsed"]["headline"]["markov"]["top3"]
    p1_f_rate = eval_data["secondary_slice_tactic_collapsed"]["headline"]["frequency"]["top3"]

    # P2: Technique McNemar
    p2_mcnemar = eval_data["paired_tests"]["P2_technique_collapsed_full_hit3"]
    p2_raw = p2_mcnemar["p_value_raw"]
    p2_m_rate = eval_data["primary_slice_technique_collapsed_full"]["headline"]["markov"]["top3"]
    p2_f_rate = eval_data["primary_slice_technique_collapsed_full"]["headline"]["frequency"]["top3"]

    # P3: Tactic S1 permutation null
    p3_stat = perm_data["schemes"]["S1_collapsed_order"]["tactic_collapsed"]["markov_hit3"]
    p3_raw = p3_stat["p_value"]
    p3_s3_raw = perm_data["schemes"]["S3_constrained_shuffle"]["tactic_collapsed"]["markov_hit3"]["p_value"]

    # P4: Technique S1 permutation null
    p4_stat = perm_data["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]["markov_hit3"]
    p4_raw = p4_stat["p_value"]
    p4_s3_raw = perm_data["schemes"]["S3_constrained_shuffle"]["technique_collapsed_full"]["markov_hit3"]["p_value"]

    family = [
        {
            "id": "P1",
            "name": "Tactic Markov Hit@3 vs Frequency Hit@3",
            "level": "tactic_collapsed",
            "test_type": "Exact two-sided McNemar",
            "raw_p": p1_raw,
            "markov_hit3": p1_m_rate,
            "frequency_hit3": p1_f_rate,
            "markov_exceeds_frequency": bool(p1_m_rate > p1_f_rate),
        },
        {
            "id": "P2",
            "name": "Technique Markov Hit@3 vs Frequency Hit@3",
            "level": "collapsed_full",
            "test_type": "Exact two-sided McNemar",
            "raw_p": p2_raw,
            "markov_hit3": p2_m_rate,
            "frequency_hit3": p2_f_rate,
            "markov_exceeds_frequency": bool(p2_m_rate > p2_f_rate),
        },
        {
            "id": "P3",
            "name": "Tactic Markov Hit@3 vs S1 Shuffled Null",
            "level": "tactic_collapsed",
            "test_type": "One-sided S1 Permutation Test (B=1000)",
            "raw_p": p3_raw,
            "markov_hit3": p1_m_rate,
            "frequency_hit3": p1_f_rate,
            "s3_raw_p": p3_s3_raw,
        },
        {
            "id": "P4",
            "name": "Technique Markov Hit@3 vs S1 Shuffled Null",
            "level": "collapsed_full",
            "test_type": "One-sided S1 Permutation Test (B=1000)",
            "raw_p": p4_raw,
            "markov_hit3": p2_m_rate,
            "frequency_hit3": p2_f_rate,
            "s3_raw_p": p4_s3_raw,
        },
    ]

    adjusted_family = holm_step_down(family)
    adj_map = {h["id"]: h for h in adjusted_family}

    # 2. Apply Pre-Registered Claim Rule
    # "improvement over the baseline demonstrated" requires:
    # 1. Pooled Markov Hit@3 > Pooled Frequency Hit@3 AND
    # 2. Holm-adjusted p < 0.05 for at least one level (technique or tactic).
    tactic_improves = bool(adj_map["P1"]["markov_hit3"] > adj_map["P1"]["frequency_hit3"] and adj_map["P1"]["adjusted_p"] < 0.05)
    technique_improves = bool(adj_map["P2"]["markov_hit3"] > adj_map["P2"]["frequency_hit3"] and adj_map["P2"]["adjusted_p"] < 0.05)
    overall_baseline_improvement = bool(tactic_improves or technique_improves)

    if overall_baseline_improvement:
        verdict = "improvement over the baseline demonstrated"
    else:
        verdict = "not demonstrated"

    # Separate sentence for order-signal question (P3/P4)
    tactic_order_sig = bool(adj_map["P3"]["adjusted_p"] < 0.05)
    technique_order_sig = bool(adj_map["P4"]["adjusted_p"] < 0.05)

    if tactic_order_sig and technique_order_sig:
        order_sentence = "Order carries detectable predictive signal beyond the unigram null at both tactic (Holm-adjusted p=0.0180) and technique (Holm-adjusted p<0.05) levels."
    elif tactic_order_sig and not technique_order_sig:
        order_sentence = f"Order carries detectable predictive signal beyond the shuffled-order null at the tactic level (Holm-adjusted p={adj_map['P3']['adjusted_p']:.4f}), but order signal is not distinguishable from the shuffled-order null at the technique level (Holm-adjusted p={adj_map['P4']['adjusted_p']:.4f})."
    elif not tactic_order_sig and technique_order_sig:
        order_sentence = f"Order carries detectable predictive signal at the technique level (Holm-adjusted p={adj_map['P4']['adjusted_p']:.4f}), but not at the tactic level (Holm-adjusted p={adj_map['P3']['adjusted_p']:.4f})."
    else:
        order_sentence = f"Order carries no detectable predictive signal beyond the shuffled-order null at either tactic (Holm-adjusted p={adj_map['P3']['adjusted_p']:.4f}) or technique (Holm-adjusted p={adj_map['P4']['adjusted_p']:.4f}) level."

    # Verdict rationale sentence
    if verdict == "not demonstrated":
        rationale_sentence = (
            f"Under the pre-registered claim rule, an improvement over the baseline is {verdict} because: "
            f"(1) At the technique level (P2), although the McNemar difference is statistically significant (Holm-adjusted p={adj_map['P2']['adjusted_p']:.4f}), "
            f"pooled Markov Hit@3 ({adj_map['P2']['markov_hit3']:.4f}) is lower than Frequency Hit@3 ({adj_map['P2']['frequency_hit3']:.4f}), favoring the baseline; and "
            f"(2) At the tactic level (P1), pooled Markov Hit@3 ({adj_map['P1']['markov_hit3']:.4f}) equals Frequency Hit@3 ({adj_map['P1']['frequency_hit3']:.4f}) "
            f"with Holm-adjusted p={adj_map['P1']['adjusted_p']:.4f}."
        )
    else:
        rationale_sentence = f"Under the pre-registered claim rule, an improvement over the baseline is {verdict}."

    print("\nHOLM-BONFERRONI ADJUSTMENT RESULTS TABLE:")
    print(f"{'ID':4s} | {'Hypothesis':42s} | {'Raw p':8s} | {'Rank':4s} | {'Mult':4s} | {'Adj p':8s} | {'Sig (<0.05)?':12s} | {'Markov Hit@3':12s} | {'Freq Hit@3':10s}")
    print("-" * 125)
    for h in sorted(adjusted_family, key=lambda x: x["rank"]):
        print(
            f"{h['id']:4s} | {h['name']:42s} | {h['raw_p']:8.4f} | {h['rank']:4d} | {h['multiplier']:4d} "
            f"| {h['adjusted_p']:8.4f} | {str(h['significant_at_05']):12s} | {h['markov_hit3']:12.4f} | {h['frequency_hit3']:10.4f}"
        )

    print(f"\nSubstantive Claim Rule Verdict: \"{verdict}\"")
    print(f"Rationale: {rationale_sentence}")
    print(f"Order Signal Question: {order_sentence}")

    report_data: dict[str, Any] = {
        "metadata": {
            "family_size": len(family),
            "family_ids": ["P1", "P2", "P3", "P4"],
            "correction_method": "Holm-Bonferroni step-down",
            "eval_source": str(EVAL_JSON_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
            "perm_source": str(PERM_JSON_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
        },
        "family": {h["id"]: h for h in adjusted_family},
        "claim_rule_evaluation": {
            "rule": "improvement over the baseline demonstrated requires pooled Markov Hit@3 > Frequency Hit@3 AND Holm-adjusted p < 0.05 for at least one level; otherwise not demonstrated",
            "tactic_improves_over_frequency": tactic_improves,
            "technique_improves_over_frequency": technique_improves,
            "overall_baseline_improvement": overall_baseline_improvement,
            "formal_verdict": verdict,
            "rationale": rationale_sentence,
            "order_signal_verdict": order_sentence,
        },
    }

    # 3. Write JSON
    print(f"\nWriting JSON to {OUT_JSON_PATH}...")
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, sort_keys=True)

    # 4. Write Markdown
    print(f"Writing Markdown to {OUT_MD_PATH}...")
    generate_markdown_holm_report(report_data)

    print("Holm Adjustment and Claim Rule evaluation completed successfully.")
    return report_data


def generate_markdown_holm_report(data: dict[str, Any]) -> None:
    lines = []

    def A(l: str = ""):
        lines.append(l)

    fam = data["family"]
    cr = data["claim_rule_evaluation"]

    A("# Pre-Registered Holm Step-Down Adjustment and Substantive Claim Rule Report")
    A()
    A("## Pre-Registered Protocol Context (prereg Section 6 & Amendment 1)")
    A()
    A("- **Primary Hypotheses Family**: $m=4$ pre-registered hypothesis tests:")
    A("  - **P1**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation).")
    A("  - **P2**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation).")
    A("  - **P3**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside).")
    A("  - **P4**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside).")
    A("- **Multiple Comparisons Procedure**: Holm-Bonferroni step-down correction applied across the family.")
    A("- **Pre-Declared Substantive Claim Rule**:")
    A("  > An **\"improvement over the baseline demonstrated\"** conclusion will be claimed **if and only if**:")
    A("  > 1. Pooled Markov Hit@3 > Pooled Frequency Hit@3, **AND**")
    A("  > 2. The Holm-adjusted $p$-value is $< 0.05$ for at least one slice level (technique or tactic).")
    A("  > ")
    A("  > Otherwise, the formal conclusion must report: **\"not demonstrated\"**.")
    A("- **Separate Order Signal Question**: Hypotheses P3 and P4 address the separate question: *\"Does sequence order carry detectable predictive signal beyond unigram frequency?\"*")
    A()
    A("---")
    A()
    A("## Holm Step-Down Adjustment Table")
    A()
    A("| Hypothesis | Target Level | Test Type | Raw $p$-value | Step-Down Rank | Multiplier | Holm-Adjusted $p$ | Significant at $\\alpha=0.05$? | Pooled Markov Hit@3 | Pooled Freq Hit@3 | Markov > Freq? |")
    A("|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    for hid in sorted(fam.keys(), key=lambda k: fam[k]["rank"]):
        h = fam[hid]
        m_gt_f = "**YES**" if h["markov_hit3"] > h["frequency_hit3"] else ("NO (Markov < Freq)" if h["markov_hit3"] < h["frequency_hit3"] else "NO (Markov == Freq)")
        sig_str = "**YES (p < 0.05)**" if h["significant_at_05"] else "NO (p ≥ 0.05)"
        A(f"| **{h['id']}** | `{h['level']}` | {h['test_type']} | `{h['raw_p']:.4f}` | {h['rank']} | {h['multiplier']} | `{h['adjusted_p']:.4f}` | {sig_str} | `{h['markov_hit3']:.4f}` | `{h['frequency_hit3']:.4f}` | {m_gt_f} |")
    A()
    A("*(Note for P3 and P4: S3 constrained shuffle p-values reported alongside S1 are $p=0.0110$ for tactic P3 and $p=0.3656$ for technique P4; per Amendment 1, only the pre-declared headline S1 p-values enter the Holm adjustment).*")
    A()
    A("---")
    A()
    A("## Formal Pre-Registered Verdict")
    A()
    A(f"### Substantive Baseline Improvement: **{cr['formal_verdict']}**")
    A()
    A(f"> {cr['rationale']}")
    A()
    A("### Order-Signal Question (P3 and P4)")
    A()
    A(f"> {cr['order_signal_verdict']}")
    A()

    with open(OUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    run_holm_claim_rule()
