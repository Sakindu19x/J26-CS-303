"""Consistency tests between recomputation from CSV and generated evaluation artifacts.

Asserts that:
1. Recomputation from evaluation_predictions.csv matches evaluation_results.json across all configs/methods.
2. Parsed tables from evaluation_report.md match the recomputed values.
3. Per-fold hits sum to the pooled hits for every method and configuration.
4. Section 5 (Coverage and ceiling) and Section 6 (Covered-only comparison) match recomputation.
5. Section 9 frequency-only split and Table 13.3 (support buckets) match recomputation.
6. Generated sentences in sections 9, 12, and 14 contain only numbers backed by the recomputation.
7. Tie diagnostic (Section 13.5) and hit concentration (Section 13.6) match recomputation.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from scripts.verify_evaluation import (
    recompute_from_csv,
    verify_technique_sample_reconstruction,
    verify_technique_collapse_reconstruction,
)

REPORTS_DIR = BASE_DIR / "reports"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def _parse_markdown_table(md_text: str, header_prefix: str) -> list[dict[str, str]]:
    """Parse a markdown table immediately following a section with header_prefix."""
    lines = md_text.splitlines()
    in_section = False
    table_lines: list[str] = []

    for line in lines:
        if header_prefix.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            if line.startswith("#"):
                # Hit next major section
                break
            if line.strip().startswith("|") and line.strip().endswith("|"):
                table_lines.append(line.strip())
            elif table_lines:
                # Table ended
                break

    if len(table_lines) < 3:
        return []

    # First line: headers
    headers = [h.strip() for h in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    # Skip separator line at table_lines[1]
    for rline in table_lines[2:]:
        cols = [c.strip() for c in rline.strip("|").split("|")]
        if len(cols) == len(headers):
            rows.append(dict(zip(headers, cols)))
    return rows


def _extract_section_text(md_text: str, start_prefix: str, end_prefix: str) -> str:
    """Extract markdown text between start_prefix header and end_prefix header."""
    lines = md_text.splitlines()
    in_section = False
    section_lines: list[str] = []
    for line in lines:
        if start_prefix.lower() in line.lower():
            in_section = True
            continue
        if in_section:
            if end_prefix.lower() in line.lower() and line.startswith("#"):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


def _wilson(h: int, n: int) -> tuple[float, float]:
    if n <= 0:
        return (0.0, 0.0)
    p = h / n
    z = 1.959963984540054
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / n) + (z ** 2 / (4.0 * (n ** 2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _fmt_candidates(cands: list[list[Any]]) -> str:
    if not cands:
        return "(none)"
    return ", ".join(f"{tech} ({prob:.3f})" for tech, prob in cands)


# ==============================================================================
# Verification Check Functions (callable on report text in memory)
# ==============================================================================

def check_tech_setup_and_definitions(md_text: str) -> None:
    """Validate setup and definition statements in evaluation_report.md."""
    assert "All numbers and explanatory sentences below are generated from this run's prediction rows." in md_text
    assert "- Evaluation unit: samples in `data/processed/next_technique_samples.json`; primary configuration `collapsed_full` (N=67)." in md_text
    assert "- Folds: 4 leave-one-episode-out folds (test = one complete episode, training = the others)." in md_text
    assert "- Prediction: from `current_technique_set` only, k=3, no smoothing, no tuning, no randomness. Markov abstains when status is `insufficient_evidence` (counted as a miss). Frequency never abstains." in md_text
    assert "- `markov_fallback` is an **extension, NOT part of the proposal**, implemented in the evaluation module only: Markov when status is ok, else the frequency prediction." in md_text
    assert "- Configurations run: `collapsed_full`, `collapsed_parent`, `raw_full`, `raw_parent`, `collapsed_full_no_s006`." in md_text
    assert "- **Coverage**: fraction of samples with Markov status ok." in md_text
    assert "- **Hit@k**: 1 if at least one of the top-k returned candidates is in the target set, else 0. Abstention is a miss. No padding of Top-3." in md_text
    assert "- **Wilson 95% interval**: score interval for a pooled hit rate." in md_text
    assert "- **Micro P/R/F1**: TP = sum |pred ∩ target|, FP = sum |pred − target|, FN = sum |target − pred| (abstention = empty pred set, so only FN)." in md_text
    assert "- **Macro P/R/F1**: per-technique TP/FP/FN over every technique appearing in any target or prediction, averaged over those techniques, zero_division = 0." in md_text


def check_tech_headline_and_paired_tables(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 3 headline results table (all columns) and Section 9 paired comparison."""
    rows = _parse_markdown_table(md_text, "## 3. Results by configuration and method")
    assert len(rows) == 15, f"Expected 15 rows in Table 3, found {len(rows)}"

    for r in rows:
        cfg = r["Configuration"]
        method = r["Method"]
        assert cfg in recomputed, f"Unknown config {cfg} in markdown report"
        assert method in recomputed[cfg]["methods"], f"Unknown method {method} in markdown report"

        expected = recomputed[cfg]["methods"][method]

        # Check N, Top-1 hits, Top-3 hits
        assert int(r["N"]) == expected["n"]
        assert int(r["Top-1 hits"]) == expected["hit1"]
        assert int(r["Top-3 hits"]) == expected["hit3"]

        # Check percentage rates
        top1_rate = float(r["Top-1 rate"].rstrip("%"))
        top3_rate = float(r["Top-3 rate"].rstrip("%"))
        fold_mean_1 = float(r["Fold-mean Top-1"].rstrip("%"))
        fold_mean_3 = float(r["Fold-mean Top-3"].rstrip("%"))

        assert abs(top1_rate - expected["pooled_top1"] * 100.0) < 0.05
        assert abs(top3_rate - expected["pooled_top3"] * 100.0) < 0.05
        assert abs(fold_mean_1 - expected["fold_mean_top1"] * 100.0) < 0.05
        assert abs(fold_mean_3 - expected["fold_mean_top3"] * 100.0) < 0.05

        if method == "markov":
            cov_rate = float(r["Markov coverage"].rstrip("%"))
            assert abs(cov_rate - recomputed[cfg]["coverage"]["rate"] * 100.0) < 0.05
        else:
            assert r["Markov coverage"] == "-"

    # Parse Table 9: Paired comparison
    paired_rows = _parse_markdown_table(md_text, "## 9. Paired comparison")
    assert len(paired_rows) == 10, f"Expected 10 rows in Table 9, found {len(paired_rows)}"

    for pr in paired_rows:
        cfg = pr["Configuration"]
        k = f"top{pr['k']}"
        expected_paired = recomputed[cfg]["paired_2x2"][k]

        assert int(pr["Both hit"]) == expected_paired["both_hit"]
        assert int(pr["Markov-only"]) == expected_paired["markov_only"]
        assert int(pr["Frequency-only"]) == expected_paired["freq_only"]
        assert int(pr["Neither"]) == expected_paired["neither"]


def check_tech_coverage_and_covered_only(
    md_text: str, recomputed: dict[str, Any], json_data: dict[str, Any]
) -> None:
    """Validate Section 5 (Coverage and ceiling) and Section 6 (Covered-only comparison)."""
    # Section 5: Coverage and ceiling table
    cov_rows = _parse_markdown_table(md_text, "## 5. Coverage and ceiling")
    assert len(cov_rows) == 5, f"Expected 5 rows in Section 5 table, found {len(cov_rows)}"
    for r in cov_rows:
        cfg = r["Configuration"]
        assert cfg in recomputed
        assert int(r["N"]) == recomputed[cfg]["n"]
        assert int(r["Markov covered"]) == recomputed[cfg]["coverage"]["covered"]
        cov_pct = float(r["Coverage"].rstrip("%"))
        assert abs(cov_pct - recomputed[cfg]["coverage"]["rate"] * 100.0) < 0.05
        ceil_hits = int(r["Samples with target seen in training (ceiling)"])
        exp_ceil = json_data["slices"][cfg]["headline"]["ceiling"]
        assert ceil_hits == exp_ceil["hits"]
        ceil_pct = float(r["Ceiling rate"].rstrip("%"))
        assert abs(ceil_pct - exp_ceil["ceiling_rate"] * 100.0) < 0.05

    # Section 6: Covered-only comparison
    cov_only_rows = _parse_markdown_table(md_text, "## 6. Covered-only comparison")
    assert len(cov_only_rows) == 5, f"Expected 5 rows in Section 6 table, found {len(cov_only_rows)}"
    expected_cfgs = ["collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006"]
    assert [r["Configuration"] for r in cov_only_rows] == expected_cfgs, "Section 6 covered-only configurations mismatch"
    for r in cov_only_rows:
        cfg = r["Configuration"]
        assert cfg in recomputed
        expected = recomputed[cfg]["covered_only"]
        assert int(r["Covered N"]) == expected["n"]
        assert int(r["Markov Top-1"]) == expected["markov_hit1"]
        assert int(r["Markov Top-3"]) == expected["markov_hit3"]
        assert int(r["Frequency Top-1"]) == expected["frequency_hit1"]
        assert int(r["Frequency Top-3"]) == expected["frequency_hit3"]
        assert int(r["Fallback Top-1"]) == expected["fallback_hit1"]
        assert int(r["Fallback Top-3"]) == expected["fallback_hit3"]


def check_tech_frequency_only_split_and_support_buckets(
    md_text: str, recomputed: dict[str, Any]
) -> None:
    """Validate Section 9 frequency-only split table and Table 13.3 support buckets."""
    split_rows = _parse_markdown_table(md_text, "### Frequency-only hits split by Markov status")
    assert len(split_rows) == 10, f"Expected 10 rows in split table, found {len(split_rows)}"
    expected_split_combos = [(c, k) for c in ("collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006") for k in ("1", "3")]
    assert [(r["Configuration"], r["k"]) for r in split_rows] == expected_split_combos, "Section 9 split table combos mismatch"
    for r in split_rows:
        cfg = r["Configuration"]
        k = f"top{r['k']}"
        expected = recomputed[cfg]["frequency_only_split"][k]
        assert int(r["Frequency-only hits"]) == expected["freq_only_total"]
        assert int(r["Markov returned a prediction and missed (status ok)"]) == expected["markov_returned_and_missed"]
        assert int(r["Markov abstained (insufficient_evidence)"]) == expected["markov_abstained"]
        assert int(r["Other status"]) == expected["markov_other_status"]

    # Table 13.3: Markov hit rate by support strength
    supp_rows = _parse_markdown_table(md_text, "### 13.3 Markov hit rate by support strength")
    assert len(supp_rows) == 15, f"Expected 15 rows in Table 13.3, found {len(supp_rows)}"
    expected_supp_combos = [(c, ep) for c in ("collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006") for ep in ("1", "2", "3")]
    assert [(r["Configuration"], r["support_episodes"]) for r in supp_rows] == expected_supp_combos, "Table 13.3 support bucket combos mismatch"
    for r in supp_rows:
        cfg = r["Configuration"]
        ep = r["support_episodes"]
        expected_bucket = recomputed[cfg]["support_buckets"][ep]
        assert int(r["N"]) == expected_bucket["n"]
        assert int(r["Top-1 hits"]) == expected_bucket["hit1"]
        assert int(r["Top-3 hits"]) == expected_bucket["hit3"]


def check_tech_generated_sentences(
    md_text: str, recomputed: dict[str, Any], json_data: dict[str, Any]
) -> None:
    """Validate generated bullet sentences in Section 9, Section 12 headings, and Section 14."""
    # 1. Section 9 bullet sentences
    sec9_text = _extract_section_text(md_text, "### Frequency-only hits split by Markov status", "## 10. Sensitivity")
    sec9_bullets = [line.strip() for line in sec9_text.splitlines() if line.strip().startswith("- `")]
    assert len(sec9_bullets) == 10, "Expected 10 Section 9 bullet sentences"

    pattern_sec9 = re.compile(
        r"^- `(?P<cfg>[^`]+)`: Of (?P<tot>\d+) frequency-only Top-(?P<k>\d+) hits, "
        r"(?P<ret>\d+) occurred where Markov returned a prediction and missed, and (?P<abst>\d+) where Markov abstained\.$"
    )
    expected_split_bullet_combos = [
        ("collapsed_full", "3"),
        ("collapsed_parent", "3"),
        ("raw_full", "3"),
        ("raw_parent", "3"),
        ("collapsed_full_no_s006", "1"),
        ("collapsed_full_no_s006", "3"),
    ]
    actual_bullet_combos = []
    for line in sec9_bullets:
        m = pattern_sec9.match(line)
        assert m is not None, f"Bullet line did not match expected template: {line}"
        cfg = m.group("cfg")
        k = f"top{m.group('k')}"
        sp = recomputed[cfg]["frequency_only_split"][k]
        assert int(m.group("tot")) == sp["freq_only_total"]
        assert int(m.group("ret")) == sp["markov_returned_and_missed"]
        assert int(m.group("abst")) == sp["markov_abstained"]
        if (cfg, m.group("k")) in expected_split_bullet_combos:
            actual_bullet_combos.append((cfg, m.group("k")))
    assert actual_bullet_combos == expected_split_bullet_combos, "Section 9 split bullets combos mismatch"

    # 2. Section 12 heading shown counts
    sec12_text = _extract_section_text(md_text, "## 12. Examples chosen by rule", "## 13. Diagnostics")
    shown_headings = re.findall(r"### \([a-z]+\) [^(]+\((\d+) shown\)", sec12_text)
    assert len(shown_headings) == 3, f"Expected 3 shown counts in Section 12, got: {shown_headings}"
    ex = json_data["examples"]
    expected_counts = [
        len(ex["markov_top1_hits"]),
        len(ex["frequency_only_top1_markov_ok"]),
        len(ex["abstentions"]),
    ]
    for shown, exp in zip(shown_headings, expected_counts):
        assert int(shown) == exp

    # 3. Section 14 limitations numbers
    sec14_text = _extract_section_text(md_text, "## 14. Limitations", "## 15. Figures")
    cf_n = recomputed["collapsed_full"]["n"]
    cf_cov = recomputed["collapsed_full"]["coverage"]["covered"]
    cf_cov_rate = recomputed["collapsed_full"]["coverage"]["rate"] * 100.0
    prim_head = json_data["primary_slice"]["headline"]
    ceil_hits = prim_head["ceiling"]["hits"]
    ceil_rate = prim_head["ceiling"]["ceiling_rate"] * 100.0

    sec14_bullets = [line.strip() for line in sec14_text.splitlines() if line.strip().startswith("- ")]
    assert len(sec14_bullets) >= 4, "Expected at least 4 limitation bullets"

    assert sec14_bullets[0] == f"- Sample size: {cf_n} test samples in `collapsed_full` from 4 episodes; Wilson intervals in section 3 are wide and understate uncertainty because samples within an episode are not independent."
    assert sec14_bullets[1] == f"- Closed vocabulary: in `collapsed_full`, {ceil_hits} of {cf_n} samples ({ceil_rate:.2f}%) have at least one target technique seen as a training target; {cf_n - ceil_hits} do not, so neither method can hit them."
    assert sec14_bullets[2] == f"- Markov coverage in `collapsed_full` is {cf_cov} of {cf_n} ({cf_cov_rate:.2f}%); the other {cf_n - cf_cov} samples are abstentions counted as misses."
    assert sec14_bullets[3] == "- The frequency baseline and the Markov model are compared on hit counts only; no significance test was run."
    assert "Hypothesis (not tested): low Markov hit counts may be related to few repeated transitions across episodes; the support-bucket table (13.3) and the repeat-current-set reference (13.2) are the only related computations here and do not establish a cause." in sec14_text
    assert "Hypothesis (not tested): the techniques the frequency baseline predicts may be common across episodes for reasons specific to this dataset; table 13.4 shows only how often they occur as targets." in sec14_text


def check_tech_tie_diagnostic_and_hit_concentration(
    md_text: str, recomputed: dict[str, Any]
) -> None:
    """Validate Section 13.5 (Tie diagnostic table/bullets) and 13.6 (Hit concentration)."""
    tie_rows = _parse_markdown_table(md_text, "### 13.5 Tie diagnostic")
    assert len(tie_rows) == 5, f"Expected 5 rows in Table 13.5, got {len(tie_rows)}"
    expected_tie_cfgs = ["collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006"]
    assert [r["Configuration"] for r in tie_rows] == expected_tie_cfgs, "Table 13.5 tie diagnostic configurations mismatch"
    for r in tie_rows:
        cfg = r["Configuration"]
        assert cfg in recomputed
        td = recomputed[cfg]["tie_diagnostic"]
        sp_tied = td["split_top1_tied"]["tied"]
        sp_not = td["split_top1_tied"]["not_tied"]

        assert int(r["Covered N"]) == td["n_ok"]
        assert int(r["Top-1 tied"]) == td["top1_tied"]
        assert int(r["Top-3 boundary tied"]) == td["top3_boundary_tied"]
        assert int(r["n_equal_top >= 3"]) == td["n_equal_top_gte_3"]
        assert int(r["Tied N"]) == sp_tied["n"]
        assert int(r["Tied Top-1 hits"]) == sp_tied["hit1"]
        assert int(r["Tied Top-3 hits"]) == sp_tied["hit3"]
        assert int(r["Not tied N"]) == sp_not["n"]
        assert int(r["Not tied Top-1 hits"]) == sp_not["hit1"]
        assert int(r["Not tied Top-3 hits"]) == sp_not["hit3"]

    tie_sec_text = _extract_section_text(md_text, "### 13.5 Tie diagnostic", "### 13.6 Hit concentration")
    tie_bullets = [line.strip() for line in tie_sec_text.splitlines() if line.strip().startswith("- `")]
    pattern_tie = re.compile(
        r"^- `(?P<cfg>[^`]+)`: (?P<tied>\d+) of (?P<n>\d+) Markov predictions have their Top-1 choice decided by the technique-ID tie-break\.$"
    )
    actual_tie_bullet_cfgs = []
    for b in tie_bullets:
        m = pattern_tie.match(b)
        assert m is not None, f"Tie bullet did not match template: {b}"
        cfg = m.group("cfg")
        actual_tie_bullet_cfgs.append(cfg)
        td = recomputed[cfg]["tie_diagnostic"]
        assert int(m.group("tied")) == td["top1_tied"]
        assert int(m.group("n")) == td["n_ok"]
    assert actual_tie_bullet_cfgs == expected_tie_cfgs, "Tie diagnostic bullets configurations mismatch"

    conc_rows = _parse_markdown_table(md_text, "### 13.6 Hit concentration by technique")
    assert len(conc_rows) == 5, f"Expected 5 rows in Table 13.6, got {len(conc_rows)}"
    cf_hc = recomputed["collapsed_full"]["hit_concentration"]
    for r in conc_rows:
        m = r["Method"]
        tech = r["Technique"]
        t1_exp = cf_hc[m]["top1"].get(tech, 0)
        t3_exp = cf_hc[m]["top3"].get(tech, 0)
        assert int(r["Top-1 hit samples"]) == t1_exp
        assert int(r["Top-3 hit samples"]) == t3_exp


def check_tech_strict_subset(md_text: str, pred_rows: list[dict[str, str]]) -> None:
    """Validate Section 7 (Strict single-target subset) table."""
    sec7_rows = _parse_markdown_table(md_text, "## 7. Strict subset")
    assert len(sec7_rows) == 5, f"Expected 5 rows in Section 7 table, got {len(sec7_rows)}"

    for r in sec7_rows:
        cfg = r["Configuration"]
        c_rows = [x for x in pred_rows if x["configuration"] == cfg]
        m_rows = [x for x in c_rows if x["method"] == "markov"]
        single_sids = set(x["sample_id"] for x in m_rows if len(json.loads(x["target_technique_set"])) == 1)

        assert int(r["N"]) == len(single_sids)
        for m_name, col_prefix in (("markov", "Markov"), ("frequency", "Frequency"), ("markov_fallback", "Fallback")):
            sub_m = [x for x in c_rows if x["method"] == m_name and x["sample_id"] in single_sids]
            h1 = sum(int(x["hit1"]) for x in sub_m)
            h3 = sum(int(x["hit3"]) for x in sub_m)
            assert int(r[f"{col_prefix} Top-1"]) == h1
            assert int(r[f"{col_prefix} Top-3"]) == h3


def check_tech_micro_precision_recall_f1(
    md_text: str, pred_rows: list[dict[str, str]], json_data: dict[str, Any]
) -> None:
    """Validate Section 8 (Precision / Recall / F1 on collapsed_full) table (both Micro and Macro)."""
    sub = [r for r in pred_rows if r["configuration"] == "collapsed_full"]
    by_m: dict[str, list[dict[str, str]]] = {}
    for r in sub:
        by_m.setdefault(r["method"], []).append(r)

    prf1_data = json_data["primary_slice"]["precision_recall_f1"]
    sec8_rows = _parse_markdown_table(md_text, "## 8. Precision / recall / F1")
    assert len(sec8_rows) == 6, f"Expected 6 rows in Section 8 table, got {len(sec8_rows)}"

    for r in sec8_rows:
        m_name = r["Method"]
        m_key = "markov_fallback" if m_name == "fallback" else m_name
        cutoff = r["Cutoff"]
        k = 1 if cutoff == "Top-1" else 3
        m_rows = by_m[m_key]

        tp = fp = fn = 0
        for row in m_rows:
            cands = json.loads(row["predicted_candidates_top3"])
            pred = set(c[0] for c in cands[:k])
            tgt = set(json.loads(row["target_technique_set"]))
            tp += len(pred & tgt)
            fp += len(pred - tgt)
            fn += len(tgt - pred)

        micro_p = tp / (tp + fp) if (tp + fp) else 0.0
        micro_r = tp / (tp + fn) if (tp + fn) else 0.0
        micro_f1 = (2 * micro_p * micro_r) / (micro_p + micro_r) if (micro_p + micro_r) else 0.0

        assert int(r["TP"]) == tp
        assert int(r["FP"]) == fp
        assert int(r["FN"]) == fn
        assert abs(float(r["Micro P"]) - micro_p) < 0.001
        assert abs(float(r["Micro R"]) - micro_r) < 0.001
        assert abs(float(r["Micro F1"]) - micro_f1) < 0.001

        # Check Macro metrics and Classes
        json_key = f"{m_name}_{cutoff.lower().replace('-', '')}"
        exp_macro = prf1_data[json_key]["macro"]
        assert abs(float(r["Macro P"]) - exp_macro["precision"]) < 0.001
        assert abs(float(r["Macro R"]) - exp_macro["recall"]) < 0.001
        assert abs(float(r["Macro F1"]) - exp_macro["f1"]) < 0.001
        assert int(r["Classes"]) == exp_macro["num_classes"]


def check_tech_self_repeat_and_repeat_current_set(
    md_text: str, pred_rows: list[dict[str, str]]
) -> None:
    """Validate Section 13.1 (Self-repeat) and 13.2 (Repeat-current-set) tables."""
    assert "| Slice | N | Target shares >=1 technique with current set | Rate | Target == current set | Rate |" in md_text
    assert "| Slice | N | Top-1 hits | Top-1 | Top-1 Wilson 95% | Top-3 hits | Top-3 | Top-3 Wilson 95% |" in md_text

    # Table 13.1 lines
    sec13_1_text = _extract_section_text(md_text, "### 13.1 Self-repeat rate per slice", "### 13.2 Repeat-current-set")
    rows_13_1 = [
        [c.strip() for c in line.strip("|").split("|")]
        for line in sec13_1_text.splitlines()
        if line.strip().startswith("|") and not line.strip().startswith("|---") and "Slice" not in line
    ]
    assert len(rows_13_1) == 4, f"Expected 4 rows in Table 13.1, got {len(rows_13_1)}"

    for cols in rows_13_1:
        cfg = cols[0]
        m_rows = [x for x in pred_rows if x["configuration"] == cfg and x["method"] == "markov"]
        n_samples = len(m_rows)
        cnt_equal = sum(1 for x in m_rows if set(json.loads(x["current_technique_set"])) == set(json.loads(x["target_technique_set"])))
        cnt_overlap = sum(1 for x in m_rows if set(json.loads(x["current_technique_set"])) & set(json.loads(x["target_technique_set"])))

        assert int(cols[1]) == n_samples
        assert int(cols[2]) == cnt_overlap
        assert abs(float(cols[3].rstrip("%")) - (cnt_overlap / n_samples * 100.0)) < 0.05
        assert int(cols[4]) == cnt_equal
        assert abs(float(cols[5].rstrip("%")) - (cnt_equal / n_samples * 100.0)) < 0.05

    rc_rows = _parse_markdown_table(md_text, "### 13.2 Repeat-current-set reference")
    assert len(rc_rows) == 4, f"Expected 4 rows in Section 13.2 table, got {len(rc_rows)}"
    assert "Comparison with the proposal methods on the same slice (hit counts, computed):" in md_text
    for r in rc_rows:
        cfg = r["Slice"]
        m_rows = [x for x in pred_rows if x["configuration"] == cfg and x["method"] == "markov"]
        n_samples = len(m_rows)
        h1 = sum(1 for x in m_rows if sorted(json.loads(x["current_technique_set"])) and sorted(json.loads(x["current_technique_set"]))[0] in set(json.loads(x["target_technique_set"])))
        h3 = sum(1 for x in m_rows if any(c in set(json.loads(x["target_technique_set"])) for c in sorted(json.loads(x["current_technique_set"]))[:3]))

        assert int(r["N"]) == n_samples
        assert int(r["Top-1 hits"]) == h1
        assert int(r["Top-3 hits"]) == h3

        top1_rate = float(r["Top-1"].rstrip("%"))
        top3_rate = float(r["Top-3"].rstrip("%"))
        assert abs(top1_rate - (h1 / n_samples * 100.0)) < 0.05
        assert abs(top3_rate - (h3 / n_samples * 100.0)) < 0.05

        w1 = _wilson(h1, n_samples)
        w3 = _wilson(h3, n_samples)
        exp_w1_str = f"[{100*w1[0]:.2f}%, {100*w1[1]:.2f}%]"
        exp_w3_str = f"[{100*w3[0]:.2f}%, {100*w3[1]:.2f}%]"
        assert r["Top-1 Wilson 95%"] == exp_w1_str
        assert r["Top-3 Wilson 95%"] == exp_w3_str


def check_tech_wilson_intervals_section_3(
    md_text: str, pred_rows: list[dict[str, str]]
) -> None:
    """Validate Section 3 Wilson 95% score intervals table."""
    w_rows = _parse_markdown_table(md_text, "### Wilson 95% intervals (pooled)")
    assert len(w_rows) == 15, f"Expected 15 rows in Table 3 Wilson, got {len(w_rows)}"

    for r in w_rows:
        cfg = r["Configuration"]
        m = r["Method"]
        sub = [x for x in pred_rows if x["configuration"] == cfg and x["method"] == m]
        n = len(sub)
        h1 = sum(int(x["hit1"]) for x in sub)
        h3 = sum(int(x["hit3"]) for x in sub)
        assert int(r["N"]) == n, f"N mismatch in Section 3 Wilson table for {cfg} {m}"
        w1 = _wilson(h1, n)
        w3 = _wilson(h3, n)
        assert r["Top-1 interval"] == f"[{100*w1[0]:.2f}%, {100*w1[1]:.2f}%]"
        assert r["Top-3 interval"] == f"[{100*w3[0]:.2f}%, {100*w3[1]:.2f}%]"


def check_tech_abstentions_by_target(
    md_text: str, pred_rows: list[dict[str, str]]
) -> None:
    """Validate Section 11 Abstentions by target technique table."""
    from collections import Counter
    sub = [r for r in pred_rows if r["configuration"] == "collapsed_full" and r["method"] == "markov"]
    abstained = [r for r in sub if r["status"] != "ok"]

    counts = Counter()
    for r in abstained:
        for t in set(json.loads(r["target_technique_set"])):
            counts[t] += 1

    abs_rows = _parse_markdown_table(md_text, "### Abstentions by target technique")
    assert len(abs_rows) == 15, f"Expected 15 rows in abstentions table, got {len(abs_rows)}"

    for r in abs_rows:
        tech = r["Target technique"]
        assert int(r["Abstentions"]) == counts[tech]


def check_tech_section_3_sentences(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 3 comparison sentences."""
    for cfg in ("collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006"):
        m_data = recomputed[cfg]["methods"]["markov"]
        f_data = recomputed[cfg]["methods"]["frequency"]
        n = m_data["n"]
        m1, f1 = m_data["hit1"], f_data["hit1"]
        m3, f3 = m_data["hit3"], f_data["hit3"]
        r1 = "above" if m1 > f1 else ("below" if m1 < f1 else "equal to")
        r3 = "above" if m3 > f3 else ("below" if m3 < f3 else "equal to")
        pat = rf"- `{cfg}`: Top-1 Markov {m1}/{n} is \*\*{r1}\*\* Frequency {f1}/{n}; Top-3 Markov {m3}/{n} is \*\*{r3}\*\* Frequency {f3}/{n}\."
        assert re.search(pat, md_text), f"Missing Section 3 comparison sentence for {cfg}"


def check_tech_section_4_per_fold_table(md_text: str, recomputed: dict[str, Any]) -> None:
    """Validate Section 4 Per-fold results table (all 60 rows)."""
    pf_rows = _parse_markdown_table(md_text, "## 4. Per-fold results")
    assert len(pf_rows) == 60, f"Expected 60 per-fold rows, got {len(pf_rows)}"
    cfg_list = ["collapsed_full", "collapsed_parent", "raw_full", "raw_parent", "collapsed_full_no_s006"]
    fold_list = ["fold_1", "fold_2", "fold_3", "fold_4"]
    m_list = ["markov", "frequency", "markov_fallback"]
    expected_combos = [(c, f, m) for c in cfg_list for m in m_list for f in fold_list]
    assert [(r["Configuration"], r["Fold"], r["Method"]) for r in pf_rows] == expected_combos, "Section 4 per-fold combos mismatch"
    fold_episodes = {"fold_1": "E1", "fold_2": "E2", "fold_3": "E3", "fold_4": "E4"}

    for r in pf_rows:
        cfg = r["Configuration"]
        fold = r["Fold"]
        m = r["Method"]
        assert fold in fold_episodes, f"Unknown fold {fold}"
        assert r["Test episode"] == fold_episodes[fold], f"Episode mismatch for {fold}: {r['Test episode']}"
        exp = recomputed[cfg]["methods"][m]["per_fold"][fold]
        assert int(r["N"]) == exp["n"]
        assert int(r["Top-1 hits"]) == exp["hit1"]
        assert int(r["Top-3 hits"]) == exp["hit3"]


def check_tech_section_5_per_fold_ceiling_and_coverage(
    md_text: str, json_data: dict[str, Any]
) -> None:
    """Validate Section 5 per-fold ceiling and coverage for collapsed_full."""
    cf_pf = json_data["primary_slice"]["per_fold"]
    rows = _parse_markdown_table(md_text, "Per-fold ceiling and coverage for `collapsed_full`")
    assert len(rows) == 4, f"Expected 4 per-fold ceiling rows, got {len(rows)}"
    fold_episodes = {"fold_1": "E1", "fold_2": "E2", "fold_3": "E3", "fold_4": "E4"}

    for r in rows:
        fid = r["Fold"]
        assert fid in fold_episodes
        assert r["Test episode"] == fold_episodes[fid]
        exp = cf_pf[fid]
        assert int(r["N"]) == exp["n_samples"]
        assert int(r["Covered"]) == exp["markov"]["covered_samples"]
        assert int(r["Ceiling hits"]) == exp["ceiling"]["hits"]


def check_tech_section_10_sensitivity_sentences(
    md_text: str, recomputed: dict[str, Any]
) -> None:
    """Validate Section 10 sensitivity sentences."""
    cf_n = recomputed["collapsed_full"]["n"]
    s006_n = recomputed["collapsed_full_no_s006"]["n"]
    exp_sent = f"The `collapsed_full_no_s006` configuration has N={s006_n} versus N={cf_n} for `collapsed_full`."
    assert exp_sent in md_text
    assert "Sensitivity runs use the same code path." in md_text


def check_tech_section_11_top1_errors_and_confusion_sentence(
    md_text: str, json_data: dict[str, Any]
) -> None:
    """Validate Section 11 Most frequent Top-1 errors table and confusion matrix sentence."""
    err_rows = _parse_markdown_table(md_text, "### Most frequent Top-1 errors at full ID")
    assert len(err_rows) == 10, f"Expected 10 top-1 error rows, got {len(err_rows)}"
    top_errors = json_data["confusion_analysis"]["top_error_pairs"]
    for r, exp in zip(err_rows, top_errors):
        assert r["Target technique"] == exp["target_technique"]
        assert r["Predicted Top-1"] == exp["predicted_top1"]
        assert int(r["Count"]) == exp["count"]

    matrix_sent_pat = (
        r"Parent-level confusion matrix \(single-target samples only, N=48\): "
        r"33 target rows x 15 prediction columns \(including ABSTAIN\), "
        r"42 of 495 cells non-zero \(8\.48%\); the matrix is sparse\."
    )
    assert re.search(matrix_sent_pat, md_text), "Missing parent confusion matrix sentence in Section 11"


def check_tech_section_12_examples_tables(
    md_text: str, json_data: dict[str, Any]
) -> None:
    """Validate Section 12 examples tables against evaluation_results.json examples."""
    rules_text = (
        "Rules: (i) every sample where Markov hit at Top-1; "
        "(ii) up to 3 samples where Frequency hit at Top-1, Markov status ok and Markov missed at Top-1, ordered by sample_id; "
        "(iii) up to 3 samples where Markov abstained (insufficient_evidence), ordered by sample_id."
    )
    assert rules_text in md_text

    ex = json_data["examples"]
    t1_rows = _parse_markdown_table(md_text, "### (i) Markov Top-1 hits")
    t2_rows = _parse_markdown_table(md_text, "### (ii) Frequency-only Top-1 hits with Markov status ok")
    t3_rows = _parse_markdown_table(md_text, "### (iii) Abstention cases")

    assert len(t1_rows) == len(ex["markov_top1_hits"])
    assert len(t2_rows) == len(ex["frequency_only_top1_markov_ok"])
    assert len(t3_rows) == len(ex["abstentions"])

    for r, exp in zip(t1_rows, ex["markov_top1_hits"]):
        assert r["Sample"] == exp["sample_id"]
        assert r["Fold"] == exp["fold_id"]
        assert r["Current set"] == ", ".join(exp["current_technique_set"])
        assert r["Target set"] == ", ".join(exp["target_technique_set"])
        assert r["Markov status"] == exp["markov_status"]
        assert r["Markov candidates"] == _fmt_candidates(exp["markov_candidates"])
        assert r["Frequency candidates"] == _fmt_candidates(exp["frequency_candidates"])

    for r, exp in zip(t2_rows, ex["frequency_only_top1_markov_ok"]):
        assert r["Sample"] == exp["sample_id"]
        assert r["Fold"] == exp["fold_id"]
        assert r["Current set"] == ", ".join(exp["current_technique_set"])
        assert r["Target set"] == ", ".join(exp["target_technique_set"])
        assert r["Markov status"] == exp["markov_status"]
        assert r["Markov candidates"] == _fmt_candidates(exp["markov_candidates"])
        assert r["Frequency candidates"] == _fmt_candidates(exp["frequency_candidates"])

    for r, exp in zip(t3_rows, ex["abstentions"]):
        assert r["Sample"] == exp["sample_id"]
        assert r["Fold"] == exp["fold_id"]
        assert r["Current set"] == ", ".join(exp["current_technique_set"])
        assert r["Target set"] == ", ".join(exp["target_technique_set"])
        assert r["Markov status"] == exp["markov_status"]
        assert r["Markov candidates"] == _fmt_candidates(exp["markov_candidates"])
        assert r["Frequency candidates"] == _fmt_candidates(exp["frequency_candidates"])


def check_tech_section_13_diagnostics(
    md_text: str, json_data: dict[str, Any], recomputed: dict[str, Any]
) -> None:
    """Validate Section 13 comparison sentences, frequency predictions table/bullets, and concentration."""
    # 13.2 Comparison sentences
    repeat_data = json_data["diagnostics"]["repeat_current_set_reference"]
    for cfg in ("raw_full", "raw_parent", "collapsed_full", "collapsed_parent"):
        rep = repeat_data[cfg]
        m1 = recomputed[cfg]["methods"]["markov"]["hit1"]
        m3 = recomputed[cfg]["methods"]["markov"]["hit3"]
        f1 = recomputed[cfg]["methods"]["frequency"]["hit1"]
        f3 = recomputed[cfg]["methods"]["frequency"]["hit3"]
        h1, h3, n = rep["hit1"], rep["hit3"], rep["n"]
        rel1_m = "above" if h1 > m1 else ("below" if h1 < m1 else "equal to")
        rel1_f = "above" if h1 > f1 else ("below" if h1 < f1 else "equal to")
        rel3_m = "above" if h3 > m3 else ("below" if h3 < m3 else "equal to")
        rel3_f = "above" if h3 > f3 else ("below" if h3 < f3 else "equal to")
        exp_sent = (
            f"- `{cfg}`: repeat-current-set Top-1 {h1}/{n} is {rel1_m} Markov ({m1}) "
            f"and {rel1_f} Frequency ({f1}); Top-3 {h3}/{n} is {rel3_m} Markov ({m3}) "
            f"and {rel3_f} Frequency ({f3})."
        )
        assert exp_sent in md_text, f"Missing Section 13.2 comparison sentence for {cfg}"

    # 13.4 Frequency baseline predictions per fold
    f_rows = _parse_markdown_table(md_text, "### 13.4 What the frequency baseline predicts per fold (`collapsed_full`)")
    assert len(f_rows) == 12, f"Expected 12 frequency predictions rows, got {len(f_rows)}"
    freq_dict = json_data["diagnostics"]["frequency_top_targets_per_fold"]
    row_idx = 0
    for fold_id in ("fold_1", "fold_2", "fold_3", "fold_4"):
        fold_info = freq_dict[fold_id]
        for rank_idx, item in enumerate(fold_info["top3"], 1):
            r = f_rows[row_idx]
            assert r["Fold"] == fold_id
            assert r["Test episode"] == fold_info["test_episode"]
            assert int(r["Test N"]) == fold_info["n_test_samples"]
            assert int(r["Rank"]) == rank_idx
            assert r["Technique"] == item["technique"]
            assert abs(float(r["Probability"]) - item["probability"]) < 0.001
            assert int(r["Training transitions with this target"]) == item["training_transitions_with_target"]
            assert int(r["Test samples containing it as target"]) == item["test_samples_containing_target"]
            row_idx += 1

    f_bullets = [
        "- fold_1: 3 of 18 test samples have at least one of the three top targets in their target set.",
        "- fold_2: 2 of 19 test samples have at least one of the three top targets in their target set.",
        "- fold_3: 2 of 20 test samples have at least one of the three top targets in their target set.",
        "- fold_4: 1 of 10 test samples have at least one of the three top targets in their target set.",
    ]
    for b in f_bullets:
        assert b in md_text, f"Missing frequency fold bullet: {b}"

    # 13.6 Concentration sentence
    s13_6_sent = "In `collapsed_full`, 7 of 8 Frequency Top-3 hits involve technique T1105."
    assert s13_6_sent in md_text

    # 13.6 Most frequent targets pooled table
    tgt_rows = _parse_markdown_table(md_text, "Most frequent targets in the primary slice pooled over all four episodes")
    assert len(tgt_rows) == 5, f"Expected 5 frequent targets rows, got {len(tgt_rows)}"
    frequent_targets = json_data["diagnostics"]["frequent_targets_pooled"]
    for rk, (r, exp) in enumerate(zip(tgt_rows, frequent_targets), 1):
        assert int(r["Rank"]) == rk
        assert r["Target technique"] == exp["technique"]
        assert int(r["Test samples containing target (pooled)"]) == exp["count"]


# ==============================================================================
# Pytest Test Cases
# ==============================================================================

def test_recomputation_matches_json_and_internal_consistency() -> None:
    """Verify recomputed CSV metrics match evaluation_results.json exactly."""
    recomputed = recompute_from_csv()
    json_path = REPORTS_DIR / "evaluation_results.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    row_analysis = data["row_analysis"]

    for cfg, cfg_data in recomputed.items():
        if cfg.startswith("_"):
            continue
        assert cfg in row_analysis, f"Configuration {cfg} missing from evaluation_results.json row_analysis"
        json_cfg = row_analysis[cfg]

        assert cfg_data["n"] == json_cfg["n"], f"N mismatch in {cfg}"

        for method, m_data in cfg_data["methods"].items():
            assert method in json_cfg["methods"], f"Method {method} missing from {cfg} in json"
            jm = json_cfg["methods"][method]

            assert m_data["n"] == jm["n"]
            assert m_data["hit1"] == jm["hit1"]
            assert m_data["hit3"] == jm["hit3"]
            assert pytest.approx(m_data["pooled_top1"], abs=1e-6) == jm["pooled_top1"]
            assert pytest.approx(m_data["pooled_top3"], abs=1e-6) == jm["pooled_top3"]
            assert pytest.approx(m_data["fold_mean_top1"], abs=1e-6) == jm["fold_mean_top1"]
            assert pytest.approx(m_data["fold_mean_top3"], abs=1e-6) == jm["fold_mean_top3"]

            sum_fold_n = sum(fd["n"] for fd in m_data["per_fold"].values())
            sum_fold_hit1 = sum(fd["hit1"] for fd in m_data["per_fold"].values())
            sum_fold_hit3 = sum(fd["hit3"] for fd in m_data["per_fold"].values())

            assert sum_fold_n == m_data["n"], f"Fold N sum mismatch in {cfg} {method}"
            assert sum_fold_hit1 == m_data["hit1"], f"Fold Hit1 sum mismatch in {cfg} {method}"
            assert sum_fold_hit3 == m_data["hit3"], f"Fold Hit3 sum mismatch in {cfg} {method}"

            for fid, fd in m_data["per_fold"].items():
                assert fid in jm["per_fold"]
                assert fd["n"] == jm["per_fold"][fid]["n"]
                assert fd["hit1"] == jm["per_fold"][fid]["hit1"]
                assert fd["hit3"] == jm["per_fold"][fid]["hit3"]

        for k_key in ("top1", "top3"):
            assert cfg_data["paired_2x2"][k_key] == json_cfg["paired"][k_key]


def test_markdown_report_matches_recomputation() -> None:
    """Verify parsed tables in evaluation_report.md equal the script's recomputation."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_headline_and_paired_tables(md_text, recomputed)


def test_coverage_and_covered_only_sections_match_recompute() -> None:
    """Verify Section 5 (Coverage) and Section 6 (Covered-only) match recomputation."""
    recomputed = recompute_from_csv()
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_coverage_and_covered_only(md_text, recomputed, json_data)


def test_frequency_only_split_and_support_buckets_match_recompute() -> None:
    """Verify Section 9 frequency-only split and Table 13.3 support buckets match recompute."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_frequency_only_split_and_support_buckets(md_text, recomputed)


def test_generated_sentences_numbers_backed_by_recompute() -> None:
    """Verify generated sentences in sections 9, 12, and 14 contain only numbers from recompute."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    check_tech_generated_sentences(md_text, recomputed, json_data)


def test_tie_diagnostic_and_hit_concentration_match_recompute() -> None:
    """Verify Section 13.5 (Tie diagnostic) and 13.6 (Hit concentration) match recompute."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_tie_diagnostic_and_hit_concentration(md_text, recomputed)


def test_technique_sample_reconstruction_from_sequences() -> None:
    """Assert technique samples rebuilt from attack_sequences.json match evaluation_predictions.csv."""
    res = verify_technique_sample_reconstruction()
    counts = res["verified"]
    assert counts["raw_full"] == {"E1": 26, "E2": 20, "E3": 28, "E4": 21}
    assert counts["raw_parent"] == {"E1": 26, "E2": 20, "E3": 28, "E4": 21}
    assert counts["collapsed_full"] == {"E1": 18, "E2": 19, "E3": 20, "E4": 10}
    assert counts["collapsed_parent"] == {"E1": 18, "E2": 19, "E3": 20, "E4": 10}
    assert res["skipped"]["slice"] == "collapsed_full_no_s006"


def test_strict_single_target_subset_matches_report() -> None:
    """Verify Section 7 (Strict subset) table matches recomputation from CSV."""
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_strict_subset(md_text, rows)


def test_micro_precision_recall_f1_collapsed_full_matches_report() -> None:
    """Verify Section 8 (Micro P/R/F1 on collapsed_full) table matches recomputation from CSV."""
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_micro_precision_recall_f1(md_text, rows, json_data)


def test_self_repeat_and_repeat_current_set_matches_report() -> None:
    """Verify Section 13.1 (Self-repeat) and 13.2 (Repeat-current-set) match recomputation from CSV."""
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_self_repeat_and_repeat_current_set(md_text, rows)


def test_wilson_intervals_section_3_matches_report() -> None:
    """Verify Section 3 Wilson 95% intervals table matches recomputation from CSV hit counts."""
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_wilson_intervals_section_3(md_text, rows)


def test_abstentions_by_target_technique_matches_report() -> None:
    """Verify Section 11 Abstentions by target technique table matches recomputation from CSV."""
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_abstentions_by_target(md_text, rows)


def test_section_3_markov_vs_frequency_sentences_match_recomputed() -> None:
    """Verify Section 3 Markov versus Frequency comparison sentences match recomputation."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_3_sentences(md_text, recomputed)


def test_section_4_per_fold_table_matches_recomputed() -> None:
    """Verify Section 4 Per-fold results table (all 60 rows) matches recomputation."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_4_per_fold_table(md_text, recomputed)


def test_section_5_per_fold_ceiling_and_coverage_matches_recomputed() -> None:
    """Verify Section 5 per-fold ceiling and coverage for collapsed_full matches recomputation."""
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_5_per_fold_ceiling_and_coverage(md_text, json_data)


def test_section_10_sensitivity_sentences_match_recomputed() -> None:
    """Verify Section 10 sensitivity sentences match recomputation."""
    recomputed = recompute_from_csv()
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_10_sensitivity_sentences(md_text, recomputed)


def test_section_11_top1_errors_and_confusion_sentence_match_recomputed() -> None:
    """Verify Section 11 Most frequent Top-1 errors table and confusion matrix sentence."""
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_11_top1_errors_and_confusion_sentence(md_text, json_data)


def test_section_12_examples_tables_match_recomputed() -> None:
    """Verify Section 12 examples tables match example sample IDs."""
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_12_examples_tables(md_text, json_data)


def test_section_13_diagnostics_match_recomputed() -> None:
    """Verify Section 13.2 comparison sentences, Section 13.4 frequency fold table/sentences, and 13.6 target frequency."""
    recomputed = recompute_from_csv()
    with open(REPORTS_DIR / "evaluation_results.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    md_text = (REPORTS_DIR / "evaluation_report.md").read_text(encoding="utf-8")
    check_tech_section_13_diagnostics(md_text, json_data, recomputed)


def test_technique_collapse_reconstruction_matches() -> None:
    """Assert technique collapse reconstruction from raw attack sequences matches stored collapsed."""
    col_recon = verify_technique_collapse_reconstruction()
    assert len(col_recon) == 4, f"Expected 4 episodes, got {len(col_recon)}"
    for ep_id, ep_res in col_recon.items():
        assert ep_res["match"] is True, f"Episode {ep_id} collapse reconstruction mismatch: first diff {ep_res['first_diff_idx']}"
        assert ep_res["stored_n"] == ep_res["rebuilt_n"], f"Episode {ep_id} length mismatch: stored {ep_res['stored_n']} vs rebuilt {ep_res['rebuilt_n']}"
