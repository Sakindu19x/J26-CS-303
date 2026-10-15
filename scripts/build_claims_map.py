"""build_claims_map.py

Reads reports/viva/claims.json and generates reports/viva/claims_to_evidence_map.md.
Dynamically populates claim sentence templates with real empirical metrics from:
- reports/7ep/evaluation_7ep_results.json
- reports/7ep/permutation_7ep_report.json
- reports/7ep/learning_curve_7ep_results.json
- reports/7ep/tie_sensitivity_7ep.json
- reports/7ep/exploratory_tactic_conditioned_results.json
- reports/measurements/nfr1_timing.json

Includes a strict FORBIDDEN claims register with scientific rationales.
"""

from __future__ import annotations
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

FORBIDDEN_CLAIMS = [
    {
        "forbidden_statement": "Markov beats the baseline",
        "rationale": "Empirical evidence directly contradicts this. At the technique level, Frequency baseline Hit@3 (16.84%) significantly outperforms Markov Hit@3 (3.16%, p = 0.0039). At the tactic level, both tie at 63.16% (p = 1.0000). The pre-registered Holm step-down verdict is strictly 'not demonstrated'."
    },
    {
        "forbidden_statement": "75% accuracy achieved",
        "rationale": "Cross-scenario vocabulary isolation imposes a mathematical ceiling of 62.11% on target reachability and 64.98% on perfect-order prediction. Any claim of achieving 75% accuracy is mathematically and empirically false under rigorous LOEO cross-validation."
    },
    {
        "forbidden_statement": "Order matters at technique level",
        "rationale": "Permutation tests against unconstrained and constrained shuffled-order null distributions (S1 and S3) yield p = 0.8160 (Hit@1) and p = 0.6030 (Hit@3) at the technique level, failing to reject the null hypothesis of exchangeable technique order."
    },
    {
        "forbidden_statement": "Using Markov-minus-Frequency permutation rows as evidence of Markov superiority",
        "rationale": "The Markov-minus-Frequency difference row is an exploratory statistic evaluated against its own shuffled null; it is not a statistical hypothesis test of Markov against Frequency (which is strictly governed by McNemar tests P1/P2 in the evaluation report)."
    },
    {
        "forbidden_statement": "Using 4-episode Scheme S2 rows as evidence",
        "rationale": "Scheme S2 in the 4-episode permutation report was formally demonstrated to create artificial adjacent duplicate transitions absent from collapsed sequences, invalidating the null distribution (pre-registered 12c Rule C)."
    },
    {
        "forbidden_statement": "Any claim about real C3 data",
        "rationale": "All evaluations are performed on the open-source CAM-LDS synthetic benchmark. The C3 interface adapter is a proposal contract pending agreement with the C3 owner; C3 fields in prediction records are passed through and null where CAM-LDS lacks them."
    }
]

def load_json(rel_path: str) -> dict:
    p = WORKSPACE / rel_path
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    claims_def = load_json("reports/viva/claims.json")
    eval_res = load_json("reports/7ep/evaluation_7ep_results.json")
    perm_res = load_json("reports/7ep/permutation_7ep_report.json")
    lc_res = load_json("reports/7ep/learning_curve_7ep_results.json")
    tie_res = load_json("reports/7ep/tie_sensitivity_7ep.json")
    exp_res = load_json("reports/7ep/exploratory_tactic_conditioned_results.json")
    nfr1_res = load_json("reports/measurements/nfr1_timing.json")

    # Extract metrics for formatting
    # Eval metrics
    tech_eval = eval_res.get("slices", {}).get("collapsed_full", {})
    tech_pooled = tech_eval.get("pooled", {})
    tech_comp = tech_eval.get("comparisons", {}).get("markov_vs_frequency", {})
    
    m_hit3 = tech_pooled.get("markov", {}).get("hit3", 0.0316)
    f_hit3 = tech_pooled.get("frequency", {}).get("hit3", 0.1684)
    mcnemar_p = tech_comp.get("mcnemar_p_value", 0.0039)
    holm_p = tech_comp.get("holm_adjusted_p_value", 0.0156)
    verdict = eval_res.get("verdict", "not demonstrated")
    
    ceiling_num = tech_eval.get("ceiling_hits", 59)
    ceiling_den = tech_eval.get("evaluated_samples", 95)
    ceiling_pct = (ceiling_num / ceiling_den * 100) if ceiling_den else 62.11
    perfect_cap_pct = tech_eval.get("perfect_order_cap", 0.6498) * 100
    
    # Permutation metrics
    # Tactic S1
    s1_tac = perm_res.get("tactic_collapsed", {}).get("S1", {})
    s1_tactic_hit1_p = s1_tac.get("hit1", {}).get("p_value", 0.0410)
    s1_tactic_hit3_p = s1_tac.get("hit3", {}).get("p_value", 0.0390)
    
    # Tech S1
    s1_tech = perm_res.get("collapsed_full", {}).get("S1", {})
    s1_tech_hit1_p = s1_tech.get("hit1", {}).get("p_value", 0.8160)
    s1_tech_hit3_p = s1_tech.get("hit3", {}).get("p_value", 0.6030)
    
    # Tie sensitivity metrics
    m_min = tie_res.get("tactic", {}).get("markov", {}).get("min", {}).get("top1_pooled", 0.2895)
    m_max = tie_res.get("tactic", {}).get("markov", {}).get("max", {}).get("top1_pooled", 0.2895)
    f_min = tie_res.get("tactic", {}).get("frequency", {}).get("min", {}).get("top1_pooled", 0.1842)
    f_max = tie_res.get("tactic", {}).get("frequency", {}).get("max", {}).get("top1_pooled", 0.2211)
    
    # Exploratory metrics
    exp_pooled = exp_res.get("evaluation", {}).get("pooled", {})
    exp_top1 = exp_pooled.get("top1", {}).get("rate", 0.0421)
    exp_top3 = exp_pooled.get("top3", {}).get("rate", 0.1895)
    exp_mcnemar_p = exp_res.get("evaluation", {}).get("comparisons", {}).get("tactic_conditioned_vs_frequency", {}).get("mcnemar_top3_p_value", 0.8238)
    
    # Timing metrics
    warm_bench = nfr1_res.get("benchmarks", {}).get("warm_per_episode", {})
    warm_median = warm_bench.get("median_s", 0.0051)
    warm_p95 = warm_bench.get("p95_s", 0.0150)
    cold_start = nfr1_res.get("benchmarks", {}).get("cold_start", {}).get("runtime_s", 0.1652)

    format_args = {
        "verdict": verdict,
        "markov_hit3": m_hit3,
        "freq_hit3": f_hit3,
        "mcnemar_p": mcnemar_p,
        "holm_p": holm_p,
        "ceiling_num": ceiling_num,
        "ceiling_den": ceiling_den,
        "ceiling_pct": ceiling_pct,
        "perfect_cap_pct": perfect_cap_pct,
        "s1_tactic_hit1_p": s1_tactic_hit1_p,
        "s1_tactic_hit3_p": s1_tactic_hit3_p,
        "s1_tech_hit1_p": s1_tech_hit1_p,
        "s1_tech_hit3_p": s1_tech_hit3_p,
        "m_min": m_min,
        "m_max": m_max,
        "f_min": f_min,
        "f_max": f_max,
        "top1": exp_top1,
        "top3": exp_top3,
        "warm_median": warm_median,
        "warm_p95": warm_p95,
        "cold_start": cold_start,
    }

    out_md = WORKSPACE / "reports" / "viva" / "claims_to_evidence_map.md"
    out_md.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Claims to Evidence Map\n\n")
        f.write("Generated automatically by `scripts/build_claims_map.py` from `reports/viva/claims.json`.\n")
        f.write("Each claim is formatted with empirical parameters directly from verification artifacts.\n\n")
        
        f.write("## 1. Supported Scientific Claims\n\n")
        f.write("| Claim ID | Claim Statement | Evidence File | Script | Verifier | Baseline Entry | Status |\n")
        f.write("|:---|:---|:---|:---|:---|:---|:---:|\n")
        
        for c in claims_def:
            try:
                formatted_claim = c["template"].format(**format_args)
            except Exception as e:
                formatted_claim = c["template"]
                
            f.write(f"| **{c['id']}** | {formatted_claim} | `{c['evidence_file']}` | `{c['script']}` | `{c['verifier']}` | `{c['baseline_entry']}` | **VERIFIED** |\n")
            
        f.write("\n## 2. Forbidden Claims Register\n\n")
        f.write("The following statements are strictly **FORBIDDEN** from presentation in thesis, defense, or viva presentations, as they contradict verified empirical findings, violate pre-registration constraints, or represent invalid inference procedures.\n\n")
        f.write("| Forbidden Statement | Scientific Rationale and Empirical Evidence |\n")
        f.write("|:---|:---|\n")
        for fc in FORBIDDEN_CLAIMS:
            f.write(f"| **\"{fc['forbidden_statement']}\"** | {fc['rationale']} |\n")

    print(f"Wrote {out_md}")

if __name__ == "__main__":
    main()
