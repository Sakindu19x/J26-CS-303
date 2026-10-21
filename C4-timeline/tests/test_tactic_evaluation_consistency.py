"""Consistency tests for secondary next-tactic LOEO cross-validation evaluation.

Validates that every table and every generated numerical sentence in reports/tactic_evaluation_report.md
matches independent recomputation from CSV:
1. Headline rows: ALL columns (N, hit1, hit3, Top-1 %, Top-3 %, fold-mean Top-1/Top-3 %, coverage %, ceiling %).
2. Wilson 95% score intervals table for all methods and slices.
3. Per-fold performance breakdown (all 48 rows across 4 configurations, 4 folds, 3 methods).
4. Reference baselines: repeat-current-set (counts, percentages, Wilson intervals) and random-guess expected hit rates.
5. Self-repeat rates table across slices.
6. Strict single-tactic target subset table.
7. 2x2 paired comparison table (Markov vs Frequency) at k=1 and k=3.
8. Frequency-only hits split by Markov status (status ok vs abstained) at k=1 and k=3.
9. Covered-only subset table (Markov status ok).
10. Tie diagnostics table (top-1 tied, top-3 boundary tied, n_equal_top >= 3, tied vs not-tied hit split) and generated sentences.
11. Hit concentration table and pooled target frequency table.
12. Sensitivity: discrepancy classification summary, discrepant events breakdown table, dataset-tactics sensitivity table,
    and generated Markov-vs-Frequency ordering comparison sentences (recomputed from CSV).
13. Derived-tactic evaluation: every column (N, hit1, hit3, Top-1 %, Top-3 %, Wilson intervals, coverage %) and mean official tactics table.
14. reports/tactic_evaluation_results.json matches independent recomputation.
15. Tactic models strictly respect LOEO fold isolation (no leakage of test episodes).
16. Technique-level artifacts remain strictly byte-identical to reports/_baseline_hashes_stage2.json.
17. Sample reconstruction from attack_sequences.json matches CSV predictions.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import pytest

from scripts.verify.verify_tactic_evaluation import (
    recompute_from_csv,
    verify_tactic_sample_reconstruction,
    wilson_interval,
)
from c4.tactic_evaluation import (
    build_tactic_sequences,
    TacticMarkovModel,
    TacticFrequencyBaseline,
)

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

MD_PATH = REPORTS_DIR / "tactic_evaluation_report.md"
JSON_PATH = REPORTS_DIR / "tactic_evaluation_results.json"
BASELINE_HASHES_PATH = REPORTS_DIR / "_baseline_hashes_stage2.json"
LOEO_FOLDS_PATH = PROCESSED_DIR / "loeo_folds.json"
ATTACK_SEQUENCES_PATH = PROCESSED_DIR / "attack_sequences.json"


@pytest.fixture(scope="module")
def recomputed():
    """Independent recomputation fixture."""
    return recompute_from_csv()


def parse_markdown_table(md_text: str, header_prefix: str) -> list[dict[str, str]]:
    """Parse a markdown table immediately following a section header."""
    lines = md_text.splitlines()
    in_section = False
    table_lines: list[str] = []
    for line in lines:
        if header_prefix.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            if line.startswith("#"):
                break
            if line.strip().startswith("|") and line.strip().endswith("|"):
                table_lines.append(line.strip())
            elif table_lines:
                break
    if len(table_lines) < 3:
        return []
    headers = [h.strip() for h in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for rline in table_lines[2:]:
        cols = [c.strip() for c in rline.strip("|").split("|")]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))
    return rows


# ==============================================================================
# Helper Verification Functions (Exported for test_checks_detect_errors.py)
# ==============================================================================

def check_headline_counts(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate headline counts (N, hit1, hit3) in Section 2."""
    rows = parse_markdown_table(md_text, "## 2. Headline Results (Official ATT&CK Tactics)")
    assert len(rows) == 6, f"Expected 6 headline rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        m = r["Method"]
        exp = recomputed[cfg]["methods"][m]
        assert int(r["N"]) == exp["n"], f"N mismatch for {cfg} {m}"
        assert int(r["Top-1 hits"]) == exp["hit1"], f"Top-1 hits mismatch for {cfg} {m}"
        assert int(r["Top-3 hits"]) == exp["hit3"], f"Top-3 hits mismatch for {cfg} {m}"


def check_headline_percentages(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate headline percentage columns in Section 2."""
    rows = parse_markdown_table(md_text, "## 2. Headline Results (Official ATT&CK Tactics)")
    assert len(rows) == 6, f"Expected 6 headline rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        m = r["Method"]
        exp = recomputed[cfg]["methods"][m]
        top1_pct = float(r["Top-1 rate"].rstrip("%"))
        top3_pct = float(r["Top-3 rate"].rstrip("%"))
        fm1_pct = float(r["Fold-mean Top-1"].rstrip("%"))
        fm3_pct = float(r["Fold-mean Top-3"].rstrip("%"))
        assert abs(top1_pct - exp["pooled_top1"] * 100.0) < 0.05, f"Top-1 rate mismatch {cfg} {m}"
        assert abs(top3_pct - exp["pooled_top3"] * 100.0) < 0.05, f"Top-3 rate mismatch {cfg} {m}"
        assert abs(fm1_pct - exp["fold_mean_top1"] * 100.0) < 0.05, f"Fold-mean Top-1 mismatch {cfg} {m}"
        assert abs(fm3_pct - exp["fold_mean_top3"] * 100.0) < 0.05, f"Fold-mean Top-3 mismatch {cfg} {m}"
        if m == "markov":
            cov_pct = float(r["Coverage"].rstrip("%"))
            assert abs(cov_pct - exp["coverage_rate"] * 100.0) < 0.05, f"Coverage mismatch {cfg} {m}"
        else:
            assert r["Coverage"] == "-"
        ceil_pct = float(r["Ceiling"].rstrip("%"))
        exp_ceil = recomputed[cfg]["ceiling"]["rate"] * 100.0
        assert abs(ceil_pct - exp_ceil) < 0.05, f"Ceiling mismatch {cfg} {m}"


def check_reference_baselines(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate repeat-current-set percentages/Wilson intervals and random-guess expected rates."""
    rows = parse_markdown_table(md_text, "### Reference Baselines (Repeat-Current-Set and Random-Guess)")
    assert len(rows) == 4, f"Expected 4 baseline rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        base_name = r["Reference Baseline"]
        if "Repeat-current-set" in base_name:
            rep = recomputed[cfg]["reference_baselines"]["repeat_current_set"]
            assert f"({rep['hit1']}/{rep['n']} t1, {rep['hit3']}/{rep['n']} t3)" in base_name
            t1_pct = float(r["Top-1"].rstrip("%"))
            t3_pct = float(r["Top-3"].rstrip("%"))
            assert abs(t1_pct - rep["top1"] * 100.0) < 0.05
            assert abs(t3_pct - rep["top3"] * 100.0) < 0.05
            w1_str = f"[{100*rep['wilson95_top1'][0]:.2f}%, {100*rep['wilson95_top1'][1]:.2f}%]"
            w3_str = f"[{100*rep['wilson95_top3'][0]:.2f}%, {100*rep['wilson95_top3'][1]:.2f}%]"
            assert r["Wilson 95% Top-1"] == w1_str
            assert r["Wilson 95% Top-3"] == w3_str
        elif "Random-guess" in base_name:
            assert base_name == "Random-guess (uniform from 14)"
            rg = recomputed[cfg]["reference_baselines"]["random_guess"]
            t1_pct = float(r["Top-1"].rstrip("%"))
            t3_pct = float(r["Top-3"].rstrip("%"))
            assert abs(t1_pct - rg["mean_p_hit1"] * 100.0) < 0.05
            assert abs(t3_pct - rg["mean_p_hit3"] * 100.0) < 0.05
            assert r["Wilson 95% Top-1"] == "-"
            assert r["Wilson 95% Top-3"] == "-"



def check_paired_2x2(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate 2x2 paired comparison table in Section 4."""
    rows = parse_markdown_table(md_text, "### 2x2 Paired Tables (Markov vs Frequency)")
    assert len(rows) == 4, f"Expected 4 paired 2x2 rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        k = f"top{r['k']}"
        exp = recomputed[cfg]["paired_2x2"][k]
        assert int(r["Both hit"]) == exp["both_hit"]
        assert int(r["Markov-only"]) == exp["markov_only"]
        assert int(r["Frequency-only"]) == exp["freq_only"]
        assert int(r["Neither"]) == exp["neither"]


def check_frequency_only_split(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Frequency-only hits split by Markov status table in Section 4."""
    rows = parse_markdown_table(md_text, "### Frequency-Only Hits Split by Markov Status")
    assert len(rows) == 4, f"Expected 4 split rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        k = f"top{r['k']}"
        exp = recomputed[cfg]["frequency_only_split"][k]
        assert int(r["Frequency-only hits"]) == exp["freq_only_total"]
        assert int(r["Markov returned a prediction and missed (status ok)"]) == exp["markov_returned_and_missed"]
        assert int(r["Markov abstained (insufficient_evidence)"]) == exp["markov_abstained"]
        assert int(r["Other status"]) == exp["markov_other_status"]


def check_tie_diagnostic(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate tie diagnostic table and bullet sentences in Section 6."""
    rows = parse_markdown_table(md_text, "## 6. Tie Diagnostic (Markov predictions with status ok)")
    assert len(rows) == 2, f"Expected 2 tie diagnostic rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        td = recomputed[cfg]["tie_diagnostic"]
        sp_tied = td["split_top1_tied"]["tied"]
        sp_not = td["split_top1_tied"]["not_tied"]
        assert int(r["Covered N"]) == td["n_ok"]
        assert int(r["Top-1 tied"]) == td["top1_tied"]
        assert int(r["Top-3 boundary tied"]) == td["top3_boundary_tied"]
        assert int(r["n_equal_top >= 3"]) == td["n_equal_top_gte_3"]
        assert int(r["Tied N"]) == sp_tied["n"]
        assert int(r["Tied Top-1"]) == sp_tied["hit1"]
        assert int(r["Tied Top-3"]) == sp_tied["hit3"]
        assert int(r["Not tied N"]) == sp_not["n"]
        assert int(r["Not tied Top-1"]) == sp_not["hit1"]
        assert int(r["Not tied Top-3"]) == sp_not["hit3"]
    # Check bullet sentences
    for cfg in ("tactic_collapsed", "tactic_raw"):
        td = recomputed[cfg]["tie_diagnostic"]
        exp_sent = f"- `{cfg}`: {td['top1_tied']} of {td['n_ok']} Markov predictions have their Top-1 choice decided by the tactic-name tie-break."
        assert exp_sent in md_text, f"Missing tie sentence for {cfg}"


def check_sensitivity_sentence(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 8.3 Markov-vs-Frequency ordering comparison sentences and recomputed change count."""
    ordering_changes = 0
    checks = [
        ("tactic_collapsed", "tactic_collapsed_dataset_tactics", 1, "top1", "hit1"),
        ("tactic_collapsed", "tactic_collapsed_dataset_tactics", 3, "top3", "hit3"),
        ("tactic_raw", "tactic_raw_dataset_tactics", 1, "top1", "hit1"),
        ("tactic_raw", "tactic_raw_dataset_tactics", 3, "top3", "hit3"),
    ]
    for off_cfg, ds_cfg, k, k_key, hit_col in checks:
        off_m = recomputed[off_cfg]["methods"]["markov"][hit_col]
        off_f = recomputed[off_cfg]["methods"]["frequency"][hit_col]
        ds_m = recomputed[ds_cfg]["methods"]["markov"][hit_col]
        ds_f = recomputed[ds_cfg]["methods"]["frequency"][hit_col]

        off_rel = "above" if off_m > off_f else ("below" if off_m < off_f else "equal to")
        ds_rel = "above" if ds_m > ds_f else ("below" if ds_m < ds_f else "equal to")

        changed = (off_rel != ds_rel)
        if changed:
            ordering_changes += 1
        expected_status = "**different**" if changed else "**the same**"

        expected_sent = (
            f"- For `{off_cfg}` at k={k}: under official tactics Markov ({off_m}) is {off_rel} Frequency ({off_f}), "
            f"and under dataset tactics Markov ({ds_m}) is {ds_rel} Frequency ({ds_f}); "
            f"the Markov-vs-Frequency ordering is {expected_status}."
        )
        assert expected_sent in md_text, f"Missing ordering sentence: {expected_sent}"

    assert ordering_changes == 2, f"Expected 2 ordering changes, got {ordering_changes}"


def check_hit_concentration(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 7 Hit Concentration table."""
    rows = parse_markdown_table(md_text, "## 7. Hit Concentration by Tactic (`tactic_collapsed`)")
    assert len(rows) > 0, "No hit concentration rows found"
    expected_m_tac = [
        ("markov", "defense-evasion"),
        ("markov", "discovery"),
        ("markov", "credential-access"),
        ("markov", "collection"),
        ("markov", "command-and-control"),
        ("markov", "persistence"),
        ("markov", "execution"),
        ("frequency", "defense-evasion"),
        ("frequency", "discovery"),
        ("frequency", "credential-access"),
        ("frequency", "execution"),
        ("markov_fallback", "defense-evasion"),
        ("markov_fallback", "discovery"),
        ("markov_fallback", "credential-access"),
        ("markov_fallback", "collection"),
        ("markov_fallback", "command-and-control"),
        ("markov_fallback", "persistence"),
        ("markov_fallback", "execution"),
    ]
    assert [(r["Method"], r["Tactic"]) for r in rows] == expected_m_tac, "Hit concentration (method, tactic) pairs mismatch"
    exp_conc = recomputed["tactic_collapsed"]["hit_concentration"]
    for r in rows:
        m = r["Method"]
        tac = r["Tactic"]
        exp_t1 = exp_conc[m]["top1"].get(tac, 0)
        exp_t3 = exp_conc[m]["top3"].get(tac, 0)
        assert int(r["Top-1 hit samples"]) == exp_t1
        assert int(r["Top-3 hit samples"]) == exp_t3

    # Table 7.2: Most frequent target tactics pooled
    tgt_rows = parse_markdown_table(md_text, "Most frequent target tactics pooled over all four episodes")
    assert len(tgt_rows) == 5, f"Expected 5 frequent target tactics rows, found {len(tgt_rows)}"
    expected_top5 = [
        ("1", "defense-evasion", 17),
        ("2", "discovery", 14),
        ("3", "persistence", 12),
        ("4", "privilege-escalation", 10),
        ("5", "command-and-control", 9),
    ]
    for r, (rk, tac, cnt) in zip(tgt_rows, expected_top5):
        assert r["Rank"] == rk
        assert r["Target Tactic"] == tac
        assert int(r["Test samples containing target (pooled)"]) == cnt


def check_dataset_tactics_sensitivity_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 8.2 Sensitivity Results (Dataset Tactics) table."""
    rows = parse_markdown_table(md_text, "### Sensitivity Results (Dataset Tactics)")
    assert len(rows) == 6, f"Expected 6 sensitivity rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        m = r["Method"]
        exp = recomputed[cfg]["methods"][m]
        assert int(r["N"]) == exp["n"]
        assert int(r["Top-1 hits"]) == exp["hit1"]
        assert int(r["Top-3 hits"]) == exp["hit3"]
        top1_pct = float(r["Top-1 rate"].rstrip("%"))
        top3_pct = float(r["Top-3 rate"].rstrip("%"))
        fm1_pct = float(r["Fold-mean Top-1"].rstrip("%"))
        fm3_pct = float(r["Fold-mean Top-3"].rstrip("%"))
        assert abs(top1_pct - exp["pooled_top1"] * 100.0) < 0.05
        assert abs(top3_pct - exp["pooled_top3"] * 100.0) < 0.05
        assert abs(fm1_pct - exp["fold_mean_top1"] * 100.0) < 0.05
        assert abs(fm3_pct - exp["fold_mean_top3"] * 100.0) < 0.05


def check_derived_tactics_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 9 Derived-Tactic table (every column) and mean tactics table."""
    rows = parse_markdown_table(md_text, "## 9. Derived-Tactic Evaluation from Technique-Level Predictions")
    assert len(rows) == 6, f"Expected 6 derived rows, found {len(rows)}"
    der_exp = recomputed["_derived_tactics"]
    for r in rows:
        cfg = r["Technique Configuration"].strip("`")
        m = r["Method"]
        exp = der_exp[cfg][m]
        assert int(r["N"]) == exp["n"]
        assert int(r["Top-1 hits"]) == exp["hit1"]
        assert int(r["Top-3 hits"]) == exp["hit3"]
        top1_pct = float(r["Top-1 rate"].rstrip("%"))
        top3_pct = float(r["Top-3 rate"].rstrip("%"))
        assert abs(top1_pct - exp["top1"] * 100.0) < 0.05
        assert abs(top3_pct - exp["top3"] * 100.0) < 0.05
        cov_pct = float(r["Coverage"].rstrip("%"))
        assert abs(cov_pct - exp["coverage_rate"] * 100.0) < 0.05
        w1_str = f"[{100*exp['wilson95_top1'][0]:.2f}%, {100*exp['wilson95_top1'][1]:.2f}%]"
        w3_str = f"[{100*exp['wilson95_top3'][0]:.2f}%, {100*exp['wilson95_top3'][1]:.2f}%]"
        assert r["Wilson 95% Top-1"] == w1_str
        assert r["Wilson 95% Top-3"] == w3_str

    # Table 9.2: Mean official tactics
    mean_rows = parse_markdown_table(md_text, "### Mean Official Tactics per Top-1 Predicted Technique")
    assert len(mean_rows) == 6, f"Expected 6 mean tactics rows, found {len(mean_rows)}"
    exp_means = recomputed["_mean_tactics_per_top1"]
    for r in mean_rows:
        cfg = r["Technique Configuration"].strip("`")
        m = r["Method"]
        exp_m = exp_means[cfg][m]
        assert int(r["Evaluated Predictions N"]) == exp_m["n_predicted"]
        assert abs(float(r["Mean Official Tactics per Top-1 Prediction"]) - exp_m["mean_tactics_per_top1"]) < 0.02

    exp_callout = (
        "> Derived scoring uses any-overlap between the tactic set of the predicted technique(s) "
        "and the target tactic set; one technique can map to several tactics so derived Top-1 covers "
        "a tactic set, not a single tactic; the derived table uses technique slices (N=67 and N=95) "
        "while the direct table uses tactic slices (N=53 and N=95); therefore the two tables are not "
        "directly comparable."
    )
    assert exp_callout in md_text


def check_sample_counts_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 1 Setup and Sample Counts table (Table 1.1) and setup constants."""
    assert "This report evaluates next-tactic prediction across the 14 MITRE ATT&CK Enterprise tactics." in md_text
    assert "- **Tactic Universe**: 14 ATT&CK Enterprise v16.1 tactics" in md_text
    assert "- **Folds**: 4 leave-one-episode-out folds" in md_text
    rows = parse_markdown_table(md_text, "## 1. Setup and Sample Counts")
    assert len(rows) == 2, f"Expected 2 setup rows, got {len(rows)}"
    expected = {
        "tactic_collapsed": {"Total N": "53", "E1": "13", "E2": "15", "E3": "15", "E4": "10"},
        "tactic_raw": {"Total N": "95", "E1": "26", "E2": "20", "E3": "28", "E4": "21"},
    }
    for r in rows:
        cfg = r["Slice"].strip("`")
        exp = expected[cfg]
        for k, v in exp.items():
            assert r[k] == v, f"Mismatch in setup table {cfg} {k}: {r[k]} vs {v}"


def check_covered_only_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 5 Covered-Only Comparison table (Table 5.1)."""
    rows = parse_markdown_table(md_text, "## 5. Covered-Only Comparison (Markov Status ok)")
    assert len(rows) == 2, f"Expected 2 covered-only rows, got {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        co = recomputed[cfg]["covered_only"]
        assert int(r["Covered N"]) == co["n"]
        assert int(r["Markov Top-1"]) == co["markov_hit1"]
        assert int(r["Markov Top-3"]) == co["markov_hit3"]
        assert int(r["Frequency Top-1"]) == co["frequency_hit1"]
        assert int(r["Frequency Top-3"]) == co["frequency_hit3"]
        assert int(r["Fallback Top-1"]) == co["fallback_hit1"]
        assert int(r["Fallback Top-3"]) == co["fallback_hit3"]


def check_self_repeat_and_strict_single_tactic(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 3 Self-Repeat and Strict Single-Tactic tables."""
    # Table 3.2: Self-repeat table
    sr_rows = parse_markdown_table(md_text, "### Self-Repeat Rates Across Slices")
    assert len(sr_rows) == 2, f"Expected 2 self-repeat rows, got {len(sr_rows)}"
    for r in sr_rows:
        cfg = r["Slice"].strip("`")
        sr = recomputed[cfg]["self_repeat"]
        assert int(r["N"]) == sr["n"]
        assert int(r["Target == Current Set (count)"]) == sr["equal"]
        assert abs(float(r["Target == Current Set (rate)"].rstrip("%")) - sr["equal_rate"] * 100.0) < 0.05
        assert int(r["Target Shares >=1 Tactic (count)"]) == sr["overlap"]
        assert abs(float(r["Target Shares >=1 Tactic (rate)"].rstrip("%")) - sr["overlap_rate"] * 100.0) < 0.05

    # Table 3.3: Strict single-tactic table
    st_rows = parse_markdown_table(md_text, "### Strict Single-Tactic Target Subset")
    assert len(st_rows) == 2, f"Expected 2 strict single-tactic rows, got {len(st_rows)}"
    for r in st_rows:
        cfg = r["Slice"].strip("`")
        st = recomputed[cfg]["strict_single_tactic"]
        assert int(r["Single-Tactic N"]) == st["n"]
        assert int(r["Markov Top-1"]) == st["markov_hit1"]
        assert int(r["Markov Top-3"]) == st["markov_hit3"]
        assert int(r["Frequency Top-1"]) == st["frequency_hit1"]
        assert int(r["Frequency Top-3"]) == st["frequency_hit3"]
        assert int(r["Fallback Top-1"]) == st["fallback_hit1"]
        assert int(r["Fallback Top-3"]) == st["fallback_hit3"]
        assert int(r["Repeat Top-1"]) == st["repeat_hit1"]
        assert int(r["Repeat Top-3"]) == st["repeat_hit3"]


def check_discrepancy_table_and_counts(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 8 discrepancy counts, event lists, and breakdown table."""
    r_disc = recomputed["_discrepancies"]
    assert f"**{r_disc['total_count']}**" in md_text
    exp_a_events = ", ".join(d["event_id"] for d in r_disc["events"] if d["classification"] == "a")
    exp_b_events = ", ".join(d["event_id"] for d in r_disc["events"] if d["classification"] == "b")
    assert f"- **Type (a)** (dataset contains a tactic NOT in official MITRE set): **{r_disc['type_a_count']} events** ({exp_a_events})." in md_text
    assert f"- **Type (b)** (dataset tactic set is a strict subset of official MITRE set): **{r_disc['type_b_count']} events** ({exp_b_events})." in md_text

    disc_rows = parse_markdown_table(md_text, "### Discrepant Events Breakdown")
    assert len(disc_rows) == r_disc["total_count"], f"Expected {r_disc['total_count']} discrepant rows"
    disc_map = {d["event_id"]: d for d in r_disc["events"]}
    for r in disc_rows:
        eid = r["Event ID"]
        assert eid in disc_map
        d_info = disc_map[eid]
        assert r["Episode"] == d_info["episode_id"]
        assert r["Class"] == f"Type ({d_info['classification']})"
        assert r["Techniques"] == ", ".join(d_info["techniques"])
        assert r["Dataset tactics"] == ", ".join(d_info["dataset_tactics"])
        assert r["Official MITRE tactics"] == ", ".join(d_info["official_tactics"])


def check_per_fold_breakdown(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 2.3 Per-Fold Performance Breakdown table (48 rows)."""
    rows = parse_markdown_table(md_text, "### Per-Fold Performance Breakdown (All Configurations)")
    assert len(rows) == 48, f"Expected 48 per-fold rows, found {len(rows)}"
    expected_combos = [
        (cfg, fid, m)
        for cfg in ("tactic_collapsed", "tactic_raw", "tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics")
        for fid in ("fold_1", "fold_2", "fold_3", "fold_4")
        for m in ("markov", "frequency", "markov_fallback")
    ]
    actual_combos = [(r["Configuration"].strip("`"), r["Fold"], r["Method"]) for r in rows]
    assert actual_combos == expected_combos, "Per-fold combinations mismatch"
    fold_episodes = {"fold_1": "E1", "fold_2": "E2", "fold_3": "E3", "fold_4": "E4"}
    for r in rows:
        cfg = r["Configuration"].strip("`")
        fid = r["Fold"]
        m = r["Method"]
        assert fid in fold_episodes, f"Unknown fold {fid}"
        assert r["Test Episode"] == fold_episodes[fid], f"Episode mismatch for {fid}: {r['Test Episode']}"
        exp_f = recomputed[cfg]["methods"][m]["per_fold"][fid]
        assert int(r["N"]) == exp_f["n"]
        assert int(r["Top-1 hits"]) == exp_f["hit1"]
        assert int(r["Top-3 hits"]) == exp_f["hit3"]
        t1_pct = float(r["Top-1 rate"].rstrip("%"))
        t3_pct = float(r["Top-3 rate"].rstrip("%"))
        exp_t1 = (exp_f["hit1"] / exp_f["n"] * 100.0) if exp_f["n"] else 0.0
        exp_t3 = (exp_f["hit3"] / exp_f["n"] * 100.0) if exp_f["n"] else 0.0
        assert abs(t1_pct - exp_t1) < 0.05
        assert abs(t3_pct - exp_t3) < 0.05


def check_wilson_intervals_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 2.2 Wilson 95% Score Intervals table."""
    rows = parse_markdown_table(md_text, "### Wilson 95% Score Intervals (Pooled)")
    assert len(rows) == 6, f"Expected 6 Wilson interval rows, found {len(rows)}"
    for r in rows:
        cfg = r["Slice"].strip("`")
        m = r["Method"]
        exp = recomputed[cfg]["methods"][m]
        n = exp["n"]
        assert int(r["N"]) == n, f"N mismatch in Wilson table for {cfg} {m}"
        h1 = exp["hit1"]
        h3 = exp["hit3"]
        w1 = wilson_interval(h1, n)
        w3 = wilson_interval(h3, n)
        assert r["Top-1 interval"] == f"[{100*w1[0]:.2f}%, {100*w1[1]:.2f}%]"
        assert r["Top-3 interval"] == f"[{100*w3[0]:.2f}%, {100*w3[1]:.2f}%]"



# ==============================================================================
# Pytest Test Cases
# ==============================================================================

def test_technique_level_outputs_strictly_unchanged():
    """Assert SHA-256 of Stage 2 technique-level evaluation artifacts are strictly unchanged."""
    assert BASELINE_HASHES_PATH.exists(), f"Missing baseline hashes file: {BASELINE_HASHES_PATH}"
    with open(BASELINE_HASHES_PATH, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    file_map = {
        "evaluation_report.md": REPORTS_DIR / "evaluation_report.md",
        "evaluation_results.json": REPORTS_DIR / "evaluation_results.json",
        "evaluation_predictions.csv": PROCESSED_DIR / "evaluation_predictions.csv",
    }

    for name, path in file_map.items():
        assert path.exists(), f"Protected file missing: {path}"
        current_hash = hashlib.sha256(path.read_bytes()).hexdigest()
        assert current_hash == baseline[name], (
            f"BYTE MISMATCH: {name} was modified!\n"
            f"Expected: {baseline[name]}\n"
            f"Current:  {current_hash}"
        )


def test_tactic_sample_counts_per_episode(recomputed):
    """Assert sample counts per slice and episode match expected specifications."""
    expected_counts = {
        "tactic_collapsed": {"fold_1": 13, "fold_2": 15, "fold_3": 15, "fold_4": 10, "total": 53},
        "tactic_raw": {"fold_1": 26, "fold_2": 20, "fold_3": 28, "fold_4": 21, "total": 95},
        "tactic_collapsed_dataset_tactics": {"fold_1": 13, "fold_2": 13, "fold_3": 15, "fold_4": 11, "total": 52},
        "tactic_raw_dataset_tactics": {"fold_1": 26, "fold_2": 20, "fold_3": 28, "fold_4": 21, "total": 95},
    }

    for cfg, exp in expected_counts.items():
        cfg_data = recomputed[cfg]
        assert cfg_data["n"] == exp["total"]
        m_pf = cfg_data["methods"]["markov"]["per_fold"]
        for fid in ("fold_1", "fold_2", "fold_3", "fold_4"):
            assert m_pf[fid]["n"] == exp[fid], f"Mismatch in {cfg} {fid}: {m_pf[fid]['n']} vs {exp[fid]}"


def test_tactic_models_leakage_isolation():
    """Assert training fold models contain zero evidence referencing the test episode."""
    with open(ATTACK_SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seq_data = json.load(f)
    with open(LOEO_FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)

    for use_ds in (False, True):
        seqs = build_tactic_sequences(seq_data, use_dataset_tactics=use_ds)
        for variant in ("tactic_collapsed", "tactic_raw"):
            ep_seqs = {ep_id: seqs[ep_id][variant] for ep_id in seqs}
            for fold in folds_data:
                test_ep = fold["test_episode"]
                train_eps = fold["training_episodes"]

                assert test_ep not in train_eps
                m_model = TacticMarkovModel().fit(ep_seqs, train_eps)
                f_model = TacticFrequencyBaseline().fit(ep_seqs, train_eps)

                assert test_ep not in m_model.training_episodes
                assert test_ep not in f_model.training_episodes

                for a, tgts in m_model.supporting_evidence.items():
                    for b, evs in tgts.items():
                        for ev in evs:
                            assert ev[0] != test_ep, f"Leak: Markov transition {a}->{b} references test ep {test_ep}"

                for b, evs in f_model.supporting_evidence.items():
                    for ev in evs:
                        assert ev[0] != test_ep, f"Leak: Frequency evidence {b} references test ep {test_ep}"


def test_results_json_matches_recomputed(recomputed):
    """Assert reports/tactic_evaluation_results.json matches independent recomputation."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    for cfg in ("tactic_collapsed", "tactic_raw", "tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics"):
        j_slice = json_data["slices"][cfg]
        r_slice = recomputed[cfg]

        assert j_slice["n_samples"] == r_slice["n"]
        assert j_slice["coverage"]["covered_samples"] == r_slice["coverage"]["covered"]
        assert j_slice["ceiling"]["hits"] == r_slice["ceiling"]["hits"]

        for m_key, m_name in (("markov", "markov"), ("frequency", "frequency"), ("markov_fallback", "markov_fallback")):
            jh = j_slice["headline"][m_key]
            rh = r_slice["methods"][m_name]
            assert jh["hit1"] == rh["hit1"]
            assert jh["hit3"] == rh["hit3"]
            assert pytest.approx(jh["top1"], abs=1e-6) == rh["pooled_top1"]
            assert pytest.approx(jh["top3"], abs=1e-6) == rh["pooled_top3"]
            assert pytest.approx(jh["fold_mean_top1"], abs=1e-6) == rh["fold_mean_top1"]
            assert pytest.approx(jh["fold_mean_top3"], abs=1e-6) == rh["fold_mean_top3"]

    # Derived tactics check
    d_methods = json_data["derived_tactics"]["methods"]
    r_methods = recomputed["_derived_tactics"]
    for cfg in ("collapsed_full", "raw_full"):
        for m in ("markov", "frequency", "markov_fallback"):
            jd = d_methods[cfg][m]
            rd = r_methods[cfg][m]
            assert jd["n"] == rd["n"]
            assert jd["hit1"] == rd["hit1"]
            assert jd["hit3"] == rd["hit3"]
            assert jd["covered"] == rd["covered"]

    # Discrepancies check
    j_disc = json_data["discrepant_events_sensitivity"]
    r_disc = recomputed["_discrepancies"]
    assert j_disc["discrepant_events_count"] == r_disc["total_count"]
    assert j_disc["type_a_count"] == r_disc["type_a_count"]
    assert j_disc["type_b_count"] == r_disc["type_b_count"]
    assert j_disc["type_a_event_ids"] == r_disc["type_a_ids"]
    assert j_disc["type_b_event_ids"] == r_disc["type_b_ids"]


def test_headline_rows_and_percentages_match_recomputed(recomputed):
    """Part B.1: Assert headline rows and all columns match independent recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_headline_counts(text, recomputed)
    check_headline_percentages(text, recomputed)


def test_reference_baselines_match_recomputed(recomputed):
    """Part B.2: Assert random-guess expected hit rates and repeat-current-set percentages match."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_reference_baselines(text, recomputed)


def test_paired_2x2_and_frequency_only_split_match_recomputed(recomputed):
    """Part B.3: Assert 2x2 paired table and frequency-only split table match recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_paired_2x2(text, recomputed)
    check_frequency_only_split(text, recomputed)


def test_tie_diagnostic_matches_recomputed(recomputed):
    """Part B.4: Assert tie diagnostic table and sentences match recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_tie_diagnostic(text, recomputed)


def test_hit_concentration_matches_recomputed(recomputed):
    """Part B.5: Assert hit concentration table matches recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_hit_concentration(text, recomputed)


def test_dataset_tactics_sensitivity_and_ordering_match_recomputed(recomputed):
    """Part B.6: Assert dataset-tactics sensitivity table and recomputed ordering sentence match."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_dataset_tactics_sensitivity_table(text, recomputed)
    check_sensitivity_sentence(text, recomputed)


def test_derived_tactics_table_matches_recomputed(recomputed):
    """Part B.7: Assert derived-tactic table (every column) and mean official tactics match."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_derived_tactics_table(text, recomputed)


def test_per_fold_breakdown_matches_recomputed(recomputed):
    """Assert per-fold performance breakdown table (48 rows) matches recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_per_fold_breakdown(text, recomputed)


def test_wilson_intervals_matches_recomputed(recomputed):
    """Assert Wilson 95% score intervals table matches recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_wilson_intervals_table(text, recomputed)


def test_self_repeat_and_strict_single_tactic_match_recomputed(recomputed):
    """Assert self-repeat and strict single-tactic target tables match recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_self_repeat_and_strict_single_tactic(text, recomputed)


def test_discrepancy_table_and_counts_match_recomputed(recomputed):
    """Assert Section 8 discrepancy counts and breakdown table match recomputation."""
    text = MD_PATH.read_text(encoding="utf-8")
    check_discrepancy_table_and_counts(text, recomputed)


def test_tactic_sample_reconstruction_from_sequences():
    """Assert tactic samples rebuilt from attack_sequences.json exactly match CSV rows."""
    counts = verify_tactic_sample_reconstruction()
    assert counts["tactic_raw"] == {"E1": 26, "E2": 20, "E3": 28, "E4": 21}
    assert counts["tactic_collapsed"] == {"E1": 13, "E2": 15, "E3": 15, "E4": 10}
    assert counts["tactic_raw_dataset_tactics"] == {"E1": 26, "E2": 20, "E3": 28, "E4": 21}
    assert counts["tactic_collapsed_dataset_tactics"] == {"E1": 13, "E2": 13, "E3": 15, "E4": 11}
