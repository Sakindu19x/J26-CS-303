r"""Mechanical Mutation Sweep for C4 Evaluation Reports (Numeric & Label Mutations).

For each of the two markdown reports:
- reports/tactic_evaluation_report.md
- reports/evaluation_report.md

Performs two mutation sweeps:
1. NUMERIC MUTATION SWEEP:
   Extracts EVERY numeric token matching regex r"\d+(?:\.\d+)?%?".
   Mutates each tested token in memory, runs consistency checks, and asserts detection.
   Tracks explicit EXEMPT rules and exception types (AssertionError vs others).

2. LABEL MUTATION SWEEP:
   Identifies data-bearing vocabulary items outside headings:
   - method names: markov, frequency, markov_fallback
   - configuration names: every configuration/slice name appearing in reports
   - fold names: fold_1..fold_4
   - episode IDs: E1..E4
   - comparison words: above, below, equal to, different, the same
   - status words: ok, abstained, insufficient_evidence
   Replaces each occurrence with a different item from the same vocabulary group,
   runs consistency checks, and asserts detection.
"""
from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import tactic recompute & check functions
from scripts.verify_tactic_evaluation import recompute_from_csv as recompute_tactic
from tests.test_tactic_evaluation_consistency import (
    check_headline_counts,
    check_headline_percentages,
    check_wilson_intervals_table as check_tac_wilson_table,
    check_per_fold_breakdown as check_tac_per_fold,
    check_reference_baselines as check_tac_ref_baselines,
    check_paired_2x2 as check_tac_paired_2x2,
    check_frequency_only_split as check_tac_freq_split,
    check_tie_diagnostic as check_tac_tie_diag,
    check_sensitivity_sentence as check_tac_sensitivity_sent,
    check_hit_concentration as check_tac_hit_concentration,
    check_dataset_tactics_sensitivity_table as check_tac_ds_sensitivity_table,
    check_derived_tactics_table as check_tac_derived_table,
    check_sample_counts_table as check_tac_sample_counts,
    check_covered_only_table as check_tac_covered_only,
    check_self_repeat_and_strict_single_tactic as check_tac_self_repeat,
    check_discrepancy_table_and_counts as check_tac_discrepancy,
)

# Import technique recompute & check functions
from scripts.verify_evaluation import recompute_from_csv as recompute_technique
from tests.test_evaluation_consistency import (
    check_tech_setup_and_definitions,
    check_tech_headline_and_paired_tables,
    check_tech_coverage_and_covered_only,
    check_tech_frequency_only_split_and_support_buckets,
    check_tech_generated_sentences,
    check_tech_tie_diagnostic_and_hit_concentration,
    check_tech_strict_subset,
    check_tech_micro_precision_recall_f1,
    check_tech_self_repeat_and_repeat_current_set,
    check_tech_wilson_intervals_section_3,
    check_tech_abstentions_by_target,
    check_tech_section_3_sentences,
    check_tech_section_4_per_fold_table,
    check_tech_section_5_per_fold_ceiling_and_coverage,
    check_tech_section_10_sensitivity_sentences,
    check_tech_section_11_top1_errors_and_confusion_sentence,
    check_tech_section_12_examples_tables,
    check_tech_section_13_diagnostics,
)

REPORTS_DIR = BASE_DIR / "reports"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


# ==============================================================================
# Numeric Token Mutation and Exemption Rules
# ==============================================================================

def mutate_numeric_token(tok: str) -> str:
    """Mutate a numeric token in memory to an invalid value."""
    if tok.endswith("%"):
        val = float(tok[:-1])
        return f"{val + 5.0:.2f}%"
    elif "." in tok:
        val = float(tok)
        return f"{val + 1.0:.2f}"
    else:
        val = int(tok)
        return str(val + 1).zfill(len(tok))


def is_exempt_tactic(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for tactic_evaluation_report.md."""
    # Rule 1: Heading outline numbers (e.g. ## 1., ### 2.2, etc.)
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: ATT&CK ontology version identifier (v16.1)
    if "v16.1" in line and tok == "16.1":
        return True, "MITRE ATT&CK ontology version string (v16.1)"

    # Rule 3: Table separator lines
    if line.strip().startswith("|---") or line.strip().startswith("| ---"):
        return True, "Table delimiter row syntax"

    return False, ""


def is_exempt_technique(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for evaluation_report.md."""
    # Rule 1: Heading outline numbers
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: Section cross-references in explanatory prose
    if "sections 3-9" in line and tok in ("3", "9"):
        return True, "Section cross-reference range in explanatory prose"
    if "section 3 are computed" in line and tok == "3":
        return True, "Section cross-reference in explanatory prose"
    if "section 3 are wide" in line and tok == "3":
        return True, "Section cross-reference in explanatory prose"
    if "table (13.3)" in line and tok == "13.3":
        return True, "Table cross-reference in explanatory prose"
    if "(13.2)" in line and tok == "13.2":
        return True, "Table cross-reference in explanatory prose"
    if "table 13.4" in line and tok == "13.4":
        return True, "Table cross-reference in explanatory prose"

    # Rule 3: Statistical heuristic threshold disclaimer
    if "fewer than 30 samples" in line and tok == "30":
        return True, "Statistical heuristic sample-size threshold (CLT N>=30 rule of thumb)"

    # Rule 4: Table separator lines
    if line.strip().startswith("|---") or line.strip().startswith("| ---"):
        return True, "Table delimiter row syntax"

    return False, ""


def is_exempt_planted(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for planted_structure_report.md."""
    # Rule 1: Heading lines
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: Table delimiter rows
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"

    # Rule 3: ATT&CK technique ID strings
    if "T1003" in line or "T1016" in line or "T1041" in line:
        return True, "MITRE ATT&CK technique ID string"

    # Rule 4: Table column header labels
    if "| Signal Level" in line or "| Gate |" in line:
        return True, "Table column header label"

    # Rule 5: Mathematical formulation definition strings
    if "pi(t_i)" in line or "c(x)" in line:
        return True, "Mathematical permutation index formula syntax"

    # Rule 6: A2 design history appendix narrative (disclosing historical scratch exploratory runs)
    if line_no >= 72:
        return True, "A2 design history appendix narrative (disclosing historical scratch exploratory runs)"

    return False, ""


def is_exempt_perm_v2(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for permutation_test_v2_report.md."""
    # Rule 1: Heading lines
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: Table delimiter rows
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"

    # Rule 3: Table column header labels
    if "| Statistic" in line or "| Scheme" in line:
        return True, "Table column header label"

    # Rule 4: S3 max tries parameter description
    if "Max Tries Allowed Per Episode" in line and tok == "10000":
        return True, "Pre-declared S3 rejection sampling maximum tries parameter"
    if "up to 10,000 tries" in line and tok == "10000":
        return True, "Pre-declared S3 rejection sampling maximum tries parameter"

    return False, ""


def is_exempt_planted_realscale(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for planted_realscale_report.md."""
    # Rule 1: Heading lines
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: Table delimiter rows
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"

    # Rule 3: Table column header labels
    if "| Signal" in line or "| Gate" in line:
        return True, "Table column header label"

    # Rule 4: Mathematical formula definition syntax
    if r"\pi(t_i)" in line or "1/(V - 1)" in line:
        return True, "Mathematical formula definition syntax"

    return False, ""



def sweep_report_numeric(
    report_name: str,
    file_path: Path,
    checks: list[Callable[[str], None]],
    exempt_fn: Callable[[str, int, str, int, int], tuple[bool, str]],
) -> dict[str, Any]:
    full_text = file_path.read_text(encoding="utf-8")

    # Assert baseline authentic text passes all checks first
    for chk in checks:
        chk(full_text)

    lines = full_text.splitlines()
    total_tokens = 0
    exempt_items: list[dict[str, Any]] = []
    exempt_rules_counter: Counter[str] = Counter()
    detected_count = 0
    undetected: list[dict[str, Any]] = []
    exception_classes_counter: Counter[str] = Counter()
    non_assertion_detections: list[dict[str, Any]] = []

    current_heading = "Header"
    pos = 0
    for line_no, line in enumerate(lines, 1):
        if line.startswith("#"):
            current_heading = line.strip()

        for m in re.finditer(r"\d+(?:\.\d+)?%?", line):
            total_tokens += 1
            tok = m.group()
            start = pos + m.start()
            end = pos + m.end()

            is_ex, reason = exempt_fn(line, line_no, tok, m.start(), m.end())
            if is_ex:
                exempt_rules_counter[reason] += 1
                exempt_items.append({
                    "report": report_name,
                    "line_number": line_no,
                    "line_text": line,
                    "token": tok,
                    "rule": reason,
                })
                continue

            mut = mutate_numeric_token(tok)
            mut_text = full_text[:start] + mut + full_text[end:]

            detected = False
            exc_found: Exception | None = None
            for chk in checks:
                try:
                    chk(mut_text)
                except Exception as ex:
                    detected = True
                    exc_found = ex
                    break

            if detected and exc_found is not None:
                detected_count += 1
                exc_class = exc_found.__class__.__name__
                exception_classes_counter[exc_class] += 1
                if exc_class != "AssertionError":
                    non_assertion_detections.append({
                        "report": report_name,
                        "line_number": line_no,
                        "token": tok,
                        "exception_class": exc_class,
                        "message": str(exc_found),
                    })
            else:
                undetected.append({
                    "report": report_name,
                    "line_number": line_no,
                    "section_heading": current_heading,
                    "line_text": line,
                    "token": tok,
                })

        pos += len(line) + 1  # +1 for newline character

    exempt_total = len(exempt_items)
    tested_total = total_tokens - exempt_total

    return {
        "report": report_name,
        "total_tokens": total_tokens,
        "exempt_total": exempt_total,
        "exempt_items": exempt_items,
        "exempt_rules": dict(exempt_rules_counter),
        "tested_total": tested_total,
        "detected": detected_count,
        "undetected": len(undetected),
        "undetected_items": undetected,
        "exception_classes": dict(exception_classes_counter),
        "non_assertion_detections": non_assertion_detections,
    }


# ==============================================================================
# Label Mutation Sweep Vocabulary and Replacements
# ==============================================================================

LABEL_VOCABULARY: dict[str, list[str]] = {
    "method": ["markov_fallback", "markov", "frequency"],
    "configuration": [
        "tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics",
        "collapsed_full_no_s006", "collapsed_parent", "collapsed_full",
        "raw_parent", "raw_full", "tactic_collapsed", "tactic_raw",
    ],
    "fold": ["fold_1", "fold_2", "fold_3", "fold_4"],
    "episode": ["E1", "E2", "E3", "E4"],
    "comparison": ["equal to", "the same", "different", "above", "below"],
    "status": ["insufficient_evidence", "abstained", "abstain", "ok"],
}

LABEL_REPLACEMENTS: dict[str, dict[str, str]] = {
    "method": {
        "markov": "frequency", "Markov": "Frequency",
        "frequency": "markov", "Frequency": "Markov",
        "markov_fallback": "markov", "Markov_fallback": "Markov",
    },
    "configuration": {
        "collapsed_full": "collapsed_parent",
        "collapsed_parent": "collapsed_full",
        "raw_full": "raw_parent",
        "raw_parent": "raw_full",
        "collapsed_full_no_s006": "collapsed_full",
        "tactic_collapsed": "tactic_raw",
        "tactic_raw": "tactic_collapsed",
        "tactic_collapsed_dataset_tactics": "tactic_raw_dataset_tactics",
        "tactic_raw_dataset_tactics": "tactic_collapsed_dataset_tactics",
    },
    "fold": {
        "fold_1": "fold_2", "fold_2": "fold_1",
        "fold_3": "fold_4", "fold_4": "fold_3",
        "Fold_1": "Fold_2", "Fold_2": "Fold_1",
        "Fold_3": "Fold_4", "Fold_4": "Fold_3",
    },
    "episode": {
        "E1": "E2", "E2": "E1", "E3": "E4", "E4": "E3",
    },
    "comparison": {
        "above": "below", "Above": "Below",
        "below": "above", "Below": "Above",
        "equal to": "different", "Equal to": "Different",
        "different": "the same", "Different": "The same",
        "the same": "different", "The same": "Different",
    },
    "status": {
        "ok": "abstained", "OK": "ABSTAIN",
        "abstained": "ok", "Abstained": "Ok",
        "insufficient_evidence": "ok", "Insufficient_evidence": "Ok",
        "abstain": "ok", "ABSTAIN": "OK",
    },
}

VOCAB_SCAN_ORDER = [
    ("configuration", LABEL_VOCABULARY["configuration"]),
    ("method", LABEL_VOCABULARY["method"]),
    ("fold", LABEL_VOCABULARY["fold"]),
    ("episode", LABEL_VOCABULARY["episode"]),
    ("comparison", LABEL_VOCABULARY["comparison"]),
    ("status", LABEL_VOCABULARY["status"]),
]


def sweep_report_labels(
    report_name: str,
    file_path: Path,
    checks: list[Callable[[str], None]],
) -> dict[str, Any]:
    full_text = file_path.read_text(encoding="utf-8")

    # Baseline authentic text passes
    for chk in checks:
        chk(full_text)

    lines = full_text.splitlines()
    detected_count = 0
    undetected: list[dict[str, Any]] = []
    exception_classes_counter: Counter[str] = Counter()
    non_assertion_detections: list[dict[str, Any]] = []
    group_counts: Counter[str] = Counter()

    pos = 0
    for line_no, line in enumerate(lines, 1):
        if line.startswith("#") or line.strip().startswith("|---"):
            pos += len(line) + 1
            continue

        # Extract non-overlapping spans of vocabulary items in this line
        line_matches: list[tuple[int, int, str, str]] = []
        for grp, items in VOCAB_SCAN_ORDER:
            for item in items:
                flags = re.I if grp not in ("episode", "fold") else 0
                pat = rf"\b{re.escape(item)}\b"
                for m in re.finditer(pat, line, flags):
                    line_matches.append((m.start(), m.end(), grp, m.group()))

        # Deduplicate overlapping matches preferring longer matches first
        line_matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        filtered_matches: list[tuple[int, int, str, str]] = []
        last_end = -1
        for s, e, grp, val in line_matches:
            if s >= last_end:
                filtered_matches.append((s, e, grp, val))
                last_end = e

        for s, e, grp, orig in filtered_matches:
            rep_map = LABEL_REPLACEMENTS[grp]
            repl = rep_map.get(orig, rep_map.get(orig.lower(), None))
            if not repl:
                continue

            group_counts[grp] += 1
            abs_start = pos + s
            abs_end = pos + e
            mut_text = full_text[:abs_start] + repl + full_text[abs_end:]

            detected = False
            exc_found: Exception | None = None
            for chk in checks:
                try:
                    chk(mut_text)
                except Exception as ex:
                    detected = True
                    exc_found = ex
                    break

            if detected and exc_found is not None:
                detected_count += 1
                exc_class = exc_found.__class__.__name__
                exception_classes_counter[exc_class] += 1
                if exc_class != "AssertionError":
                    non_assertion_detections.append({
                        "report": report_name,
                        "line_number": line_no,
                        "group": grp,
                        "original": orig,
                        "replacement": repl,
                        "exception_class": exc_class,
                        "message": str(exc_found),
                    })
            else:
                undetected.append({
                    "report": report_name,
                    "line_number": line_no,
                    "group": grp,
                    "original": orig,
                    "replacement": repl,
                    "line_text": line,
                })

        pos += len(line) + 1

    total_tested = sum(group_counts.values())

    return {
        "report": report_name,
        "total_tested": total_tested,
        "group_counts": dict(group_counts),
        "detected": detected_count,
        "undetected": len(undetected),
        "undetected_items": undetected,
        "exception_classes": dict(exception_classes_counter),
        "non_assertion_detections": non_assertion_detections,
    }


# ==============================================================================
# Summary Formatting
# ==============================================================================

def format_summary_line(label: str, res: dict[str, Any]) -> str:
    """Format one summary line computing values directly from result dictionary."""
    detected = res["detected"]
    tested_total = res["tested_total"] if "tested_total" in res else res["total_tested"]
    undetected = res["undetected"]
    pct = (detected / tested_total * 100.0) if tested_total > 0 else 0.0
    return f"  {label:<11}: {detected}/{tested_total} detected ({pct:.2f}%, {undetected} undetected)"


def format_summary_block(results: dict[str, dict[str, Any]], title: str = "MUTATION SWEEP SUMMARY") -> str:
    """Format summary block computing all values from result dictionaries."""
    lines = ["=" * 80, f"{title}:"]
    if "tactic" in results:
        lines.append(format_summary_line("Tactic", results["tactic"]))
    if "technique" in results:
        lines.append(format_summary_line("Technique", results["technique"]))
    if "planted_structure" in results:
        lines.append(format_summary_line("PlantedStruct", results["planted_structure"]))
    if "permutation_test" in results and "permutation_test_v2" not in results:
        lines.append(format_summary_line("Permutation", results["permutation_test"]))
    if "permutation_test_v2" in results:
        lines.append(format_summary_line("PermutationV2", results["permutation_test_v2"]))
    if "planted_realscale" in results:
        lines.append(format_summary_line("PlantedRealscale", results["planted_realscale"]))
    lines.append("=" * 80)
    return "\n".join(lines)


# ==============================================================================
# Main Runner Functions
# ==============================================================================

def get_validation_check_suites() -> tuple[list[Callable[[str], None]], list[Callable[[str], None]], list[Callable[[str], None]]]:
    """Check suites for planted-structure, permutation test v2, and realscale power analysis reports."""
    planted_json = json.loads((REPORTS_DIR / "planted_structure_report.json").read_text(encoding="utf-8"))
    perm_v2_json = json.loads((REPORTS_DIR / "permutation_test_v2_report.json").read_text(encoding="utf-8"))
    realscale_json = json.loads((REPORTS_DIR / "planted_realscale_report.json").read_text(encoding="utf-8"))

    def check_planted_setup(md: str) -> None:
        assert f"- **Vocabulary (V)**: 12 techniques (the 12 smallest sorted distinct technique IDs from E1–E4 collapsed sequences):" in md
        assert "seeds 0..19" in md
        assert f"Episode length: {planted_json['episode_length']} items; {planted_json['n_episodes']} episodes per replicate dataset; {planted_json['n_replicates']} replicate datasets per signal level." in md
        assert f"- **Evaluation Code**: Production `MarkovModel` and `FrequencyBaseline` evaluated under 8-fold Leave-One-Episode-Out cross-validation." in md
        assert f"- **Theoretical Closed Forms**: Oracle Top-1 = `s + (1-s)/(V-1)`; Chance Top-1 = `1/(V-1) = 1/11 = {planted_json['chance_top1']:.6f}`." in md
        sigs = ", ".join(f"{s:.2f}" for s in planted_json["signal_levels"])
        assert f"- **Signal Levels (s)**: `{sigs}`." in md

    def check_planted_gates(md: str) -> None:
        g = planted_json["gates"]
        assert f"| **G1** | A1, s=1.0: Markov Top-1 >= 0.98 | `{g['G1']['measured']:.4f}` | `>= 0.9800` |" in md
        assert f"| **G2** | A1, s=0.0: |Markov Top-1 - chance| <= max(0.02, 3*SE) | `{g['G2']['measured']:.4f}` | `<= {g['G2']['threshold']:.4f}` |" in md
        traj_str = str([round(x, 4) for x in g['G3']['measured_trajectory']])
        assert f"| **G3** | A1: Markov Top-1 non-decreasing across s | `{traj_str}` |" in md
        assert f"| **G4** | A1, s >= 0.25: Markov within 0.05 of oracle | Max diff: `{g['G4']['max_difference']:.4f}` | `<= 0.0500` |" in md
        assert f"| **G5** | A1, s >= 0.5: Markov exceeds Freq by >= 0.20 | Min excess: `{g['G5']['min_excess']:.4f}` | `>= 0.2000` |" in md
        assert f"| **G6** | A2: |Markov Top-1 - Frequency Top-1| <= 0.03 (no order) | `{g['G6']['difference']:.4f}` | `<= 0.0300` |" in md
        assert f"| **G7** | A3, s=1.0: Markov Top-1 >= 0.98 and non-decreasing | s=1.0: `{g['G7']['s_1_measured']:.4f}` | `>= 0.9800 & non-decreasing` |" in md
        assert f"| **NegCtrl** | Negative control: broken Markov fails G1 | `{g['Negative_Control']['broken_markov_top1']:.4f}` | `< 0.9800 (must fail G1)` | **PASS (Failed G1 as expected)** |" in md

    def check_planted_a1_table(md: str) -> None:
        for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
            row = planted_json["A1"][s_str]
            m_f_diff = row["markov_top1_mean"] - row["frequency_top1_mean"]
            line = f"| {float(s_str):.2f} | {row['oracle_top1']:.4f} | {row['markov_top1_mean']:.4f} | {row['markov_top1_se']:.4f} | {row['frequency_top1_mean']:.4f} | {row['diff_from_oracle']:.4f} | {m_f_diff:+.4f} |"
            assert line in md, f"Missing A1 row: {line}"

    def check_planted_a2_section(md: str) -> None:
        a2 = planted_json["A2"]
        nom = a2["dominant_nominal_probability"]
        emp = a2["dominant_post_collapse_frequency"]
        other_nom = a2["dominant_uniform_other_nominal"]
        expected_line = (
            f"Evaluates i.i.d. draws with one dominant technique having nominal probability {nom:.2f} "
            f"(empirical post-collapse frequency {emp:.4f}) and the remaining 11 techniques uniform "
            f"(`(1 - {nom:.2f})/11 = {other_nom:.4f}`):"
        )
        assert expected_line in md, f"Missing or corrupted A2 dominant line: {expected_line}"
        assert f"- **Markov Top-1 Mean**: `{a2['markov_top1_mean']:.4f}`" in md
        assert f"- **Frequency Baseline Top-1 Mean**: `{a2['frequency_top1_mean']:.4f}`" in md
        assert f"- **Absolute Difference**: `{a2['difference']:.4f}` (Gate G6 requires `<= 0.0300`)" in md

    def check_planted_a3_table(md: str) -> None:
        for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
            row = planted_json["A3"][s_str]
            line = f"| {float(s_str):.2f} | {row['markov_top1_mean']:.4f} | {row['frequency_top1_mean']:.4f} |"
            assert line in md, f"Missing A3 row: {line}"

    def check_planted_neg_ctrl(md: str) -> None:
        assert f"- Broken Markov Top-1 at s=1.0: `{planted_json['negative_control']['broken_markov_top1']:.4f}`" in md
        assert "- Gate G1 threshold: `>= 0.9800`" in md
        assert "- Verdict: **G1 FAILS as expected**, proving that the test gate has non-trivial discriminating power." in md

    planted_checks: list[Callable[[str], None]] = [
        check_planted_setup,
        check_planted_gates,
        check_planted_a1_table,
        check_planted_a2_section,
        check_planted_a3_table,
        check_planted_neg_ctrl,
    ]

    def check_perm_v2_setup(md: str) -> None:
        meta = perm_v2_json["metadata"]
        assert "- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines in real telemetry episodes E1–E4." in md
        assert "- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: The items of the stored collapsed sequence for each episode are shuffled strictly within the episode. Sample counts $N$ are strictly invariant ($N=67$ for technique, $N=53$ for tactic in every permutation). Headline decisions are made under S1." in md
        assert "- **Constrained Scheme (S3 - Adjacency-Constrained Shuffle)**: Shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items have identical technique sets (technique level) or identical tactic sets (tactic level), using rejection sampling with up to 10,000 tries per episode. Added after the S1 and S2 results to remove an artifact (adjacent identical items introduced by unconstrained shuffling that are absent in real collapsed data). S1 remains the pre-declared headline; S3 is reported alongside it, and if S1 and S3 disagree, both are reported." in md
        assert "- **Sensitivity Scheme (S2 - Raw-Shuffle Rate-Based)**: Raw labeled events are shuffled within each episode and re-collapsed, yielding variable sample counts ($N \\in [82, 95]$ technique, $N \\in [74, 90]$ tactic). Evaluated as hit rate (hits / $N_{perm}$) compared against observed hit rate." in md
        assert f"- **Null Replicates**: B={meta['b_permutations']} permutations (stdlib `random.Random` seeds 0..{meta['b_permutations'] - 1})." in md
        assert f"- **One-Sided p-value Formula**: `{meta['p_value_formula']}`." in md
        assert "- **Pre-Declared Decision Rule**: `p < 0.05` under S1/S3. Sensitivity scheme S2 is documented alongside S1 and S3 for methodological completeness." in md
        assert "- **Conclusion Text Generation Rule**: Every conclusion sentence is generated strictly by code from the p-value: if $p < 0.05$, *'observed exceeds the shuffled-order null (p=...)'*; else *'not distinguishable from the shuffled-order null at this sample size (this is not proof of absence)'*. No causal inferences are asserted." in md

    def check_perm_v2_scheme_validity(md: str) -> None:
        assert "## Scheme Validity Check (Order-Free Frequency Statistics)" in md
        assert "A valid order-only null permutation must not perturb the performance of an **order-free** model (FrequencyBaseline). If an order-free statistic exhibits $p < 0.05$" in md
        stat_labels = {"frequency_hit1": "Frequency Hit@1", "frequency_hit3": "Frequency Hit@3"}
        for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)"), ("S2_raw_shuffle_rate", "S2 (Raw-Shuffle)")]:
            for lvl, lvl_label in [("technique_collapsed_full", "Technique"), ("tactic_collapsed", "Tactic")]:
                for st in ["frequency_hit1", "frequency_hit3"]:
                    row = perm_v2_json["schemes"][sc][lvl][st]
                    lbl = stat_labels[st]
                    status_str = "**FLAG (p < 0.05)**" if row["p_value"] < 0.05 else "PASS (Valid)"
                    line = f"| {sc_label} | {lvl_label} | {lbl} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['p_value']:.4f} | {status_str} |"
                    assert line in md, f"Missing validity table row: {line}"
        assert "- **S1 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \\ge 0.05$)." in md
        assert "- **S3 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \\ge 0.05$)." in md
        warn_msg = perm_v2_json["scheme_validity_check"]["S2_raw_shuffle_rate"]["warning"]
        assert f"> **Scheme Validity Warning (S2)**: {warn_msg}" in md

    def check_perm_v2_sample_counts(md: str) -> None:
        sc = perm_v2_json["metadata"]["sample_counts_summary"]
        s1_t = sc["S1_collapsed_order"]["technique_collapsed_full"]
        s1_tac = sc["S1_collapsed_order"]["tactic_collapsed"]
        s3_t = sc["S3_constrained_shuffle"]["technique_collapsed_full"]
        s3_tac = sc["S3_constrained_shuffle"]["tactic_collapsed"]
        s2_t = sc["S2_raw_shuffle_rate"]["technique_collapsed_full"]
        s2_tac = sc["S2_raw_shuffle_rate"]["tactic_collapsed"]

        assert f"| S1 (Collapsed-Order) | Technique (collapsed_full) | 67 | {s1_t['min']} | {s1_t['mean']:.2f} | {s1_t['max']} | **YES (Constant)** |" in md
        assert f"| S1 (Collapsed-Order) | Tactic (tactic_collapsed) | 53 | {s1_tac['min']} | {s1_tac['mean']:.2f} | {s1_tac['max']} | **YES (Constant)** |" in md
        assert f"| S3 (Constrained Shuffle) | Technique (collapsed_full) | 67 | {s3_t['min']} | {s3_t['mean']:.2f} | {s3_t['max']} | **YES (Constant)** |" in md
        assert f"| S3 (Constrained Shuffle) | Tactic (tactic_collapsed) | 53 | {s3_tac['min']} | {s3_tac['mean']:.2f} | {s3_tac['max']} | **YES (Constant)** |" in md
        assert f"| S2 (Raw-Shuffle) | Technique (collapsed_full) | 67 | {s2_t['min']} | {s2_t['mean']:.2f} | {s2_t['max']} | NO (Variable) |" in md
        assert f"| S2 (Raw-Shuffle) | Tactic (tactic_collapsed) | 53 | {s2_tac['min']} | {s2_tac['mean']:.2f} | {s2_tac['max']} | NO (Variable) |" in md

        s3_m = perm_v2_json["metadata"]["s3_rejection_sampling_summary"]
        assert f"- **Technique Level**: Excluded Permutations = {s3_m['technique_collapsed_full']['excluded_permutations']}, Min Tries = {s3_m['technique_collapsed_full']['min_total_tries']}, Mean Tries = {s3_m['technique_collapsed_full']['mean_total_tries']:.2f}, Max Tries = {s3_m['technique_collapsed_full']['max_total_tries']}" in md
        assert f"- **Tactic Level**: Excluded Permutations = {s3_m['tactic_collapsed']['excluded_permutations']}, Min Tries = {s3_m['tactic_collapsed']['min_total_tries']}, Mean Tries = {s3_m['tactic_collapsed']['mean_total_tries']:.2f}, Max Tries = {s3_m['tactic_collapsed']['max_total_tries']}" in md

    def check_perm_v2_s1_tables(md: str) -> None:
        s1 = perm_v2_json["schemes"]["S1_collapsed_order"]
        obs_counts = perm_v2_json["metadata"]["observed_baseline_counts"]
        stat_map = [
            ("markov_hit1", "Markov Hit@1"),
            ("markov_hit3", "Markov Hit@3"),
            ("frequency_hit1", "Frequency Hit@1"),
            ("frequency_hit3", "Frequency Hit@3"),
            ("markov_fallback_hit1", "Markov Fallback Hit@1"),
            ("markov_fallback_hit3", "Markov Fallback Hit@3"),
            ("markov_minus_frequency_hit1", "Markov - Frequency Hit@1"),
            ("markov_minus_frequency_hit3", "Markov - Frequency Hit@3"),
        ]
        for stat_key, s_name in stat_map:
            row_tech = s1["technique_collapsed_full"][stat_key]
            cnt_tech = obs_counts["technique_collapsed_full"][stat_key]
            h_str_tech = f"{cnt_tech:+d} / 67" if "minus" in stat_key else f"{cnt_tech} / 67"
            line_tech = (
                f"| {s_name:26s} | {row_tech['observed']:+.4f} | {h_str_tech:9s} | "
                f"{row_tech['null_mean']:+.4f} | {row_tech['null_sd']:.4f} | {row_tech['null_p2_5']:+.4f} | "
                f"{row_tech['null_p97_5']:+.4f} | {row_tech['p_value']:.4f} | {row_tech['conclusion']} |"
            )
            assert line_tech in md, f"Missing S1 tech row: {line_tech}"

            row_tac = s1["tactic_collapsed"][stat_key]
            cnt_tac = obs_counts["tactic_collapsed"][stat_key]
            h_str_tac = f"{cnt_tac:+d} / 53" if "minus" in stat_key else f"{cnt_tac} / 53"
            line_tac = (
                f"| {s_name:26s} | {row_tac['observed']:+.4f} | {h_str_tac:9s} | "
                f"{row_tac['null_mean']:+.4f} | {row_tac['null_sd']:.4f} | {row_tac['null_p2_5']:+.4f} | "
                f"{row_tac['null_p97_5']:+.4f} | {row_tac['p_value']:.4f} | {row_tac['conclusion']} |"
            )
            assert line_tac in md, f"Missing S1 tac row: {line_tac}"

    def check_perm_v2_s3_tables(md: str) -> None:
        s3 = perm_v2_json["schemes"]["S3_constrained_shuffle"]
        obs_counts = perm_v2_json["metadata"]["observed_baseline_counts"]
        stat_map = [
            ("markov_hit1", "Markov Hit@1"),
            ("markov_hit3", "Markov Hit@3"),
            ("frequency_hit1", "Frequency Hit@1"),
            ("frequency_hit3", "Frequency Hit@3"),
            ("markov_fallback_hit1", "Markov Fallback Hit@1"),
            ("markov_fallback_hit3", "Markov Fallback Hit@3"),
            ("markov_minus_frequency_hit1", "Markov - Frequency Hit@1"),
            ("markov_minus_frequency_hit3", "Markov - Frequency Hit@3"),
        ]
        for stat_key, s_name in stat_map:
            row_tech = s3["technique_collapsed_full"][stat_key]
            cnt_tech = obs_counts["technique_collapsed_full"][stat_key]
            h_str_tech = f"{cnt_tech:+d} / 67" if "minus" in stat_key else f"{cnt_tech} / 67"
            line_tech = (
                f"| {s_name:26s} | {row_tech['observed']:+.4f} | {h_str_tech:9s} | "
                f"{row_tech['null_mean']:+.4f} | {row_tech['null_sd']:.4f} | {row_tech['null_p2_5']:+.4f} | "
                f"{row_tech['null_p97_5']:+.4f} | {row_tech['p_value']:.4f} | {row_tech['conclusion']} |"
            )
            assert line_tech in md, f"Missing S3 tech row: {line_tech}"

            row_tac = s3["tactic_collapsed"][stat_key]
            cnt_tac = obs_counts["tactic_collapsed"][stat_key]
            h_str_tac = f"{cnt_tac:+d} / 53" if "minus" in stat_key else f"{cnt_tac} / 53"
            line_tac = (
                f"| {s_name:26s} | {row_tac['observed']:+.4f} | {h_str_tac:9s} | "
                f"{row_tac['null_mean']:+.4f} | {row_tac['null_sd']:.4f} | {row_tac['null_p2_5']:+.4f} | "
                f"{row_tac['null_p97_5']:+.4f} | {row_tac['p_value']:.4f} | {row_tac['conclusion']} |"
            )
            assert line_tac in md, f"Missing S3 tac row: {line_tac}"

    def check_perm_v2_s2_tables(md: str) -> None:
        s2 = perm_v2_json["schemes"]["S2_raw_shuffle_rate"]
        stat_map = [
            ("markov_hit1", "Markov Hit@1"),
            ("markov_hit3", "Markov Hit@3"),
            ("frequency_hit1", "Frequency Hit@1"),
            ("frequency_hit3", "Frequency Hit@3"),
            ("markov_fallback_hit1", "Markov Fallback Hit@1"),
            ("markov_fallback_hit3", "Markov Fallback Hit@3"),
            ("markov_minus_frequency_hit1", "Markov - Frequency Hit@1"),
            ("markov_minus_frequency_hit3", "Markov - Frequency Hit@3"),
        ]
        for stat_key, s_name in stat_map:
            row_tech = s2["technique_collapsed_full"][stat_key]
            line_tech = (
                f"| {s_name:<26} | {row_tech['observed']:+.4f} | {row_tech['null_mean']:+.4f} | "
                f"{row_tech['null_sd']:.4f} | {row_tech['null_p2_5']:+.4f} | "
                f"{row_tech['null_p97_5']:+.4f} | {row_tech['p_value']:.4f} | {row_tech['conclusion']} |"
            )
            assert line_tech in md, f"Missing S2 tech row: {line_tech}"

            row_tac = s2["tactic_collapsed"][stat_key]
            line_tac = (
                f"| {s_name:<26} | {row_tac['observed']:+.4f} | {row_tac['null_mean']:+.4f} | "
                f"{row_tac['null_sd']:.4f} | {row_tac['null_p2_5']:+.4f} | "
                f"{row_tac['null_p97_5']:+.4f} | {row_tac['p_value']:.4f} | {row_tac['conclusion']} |"
            )
            assert line_tac in md, f"Missing S2 tac row: {line_tac}"


    def check_perm_v2_monte_carlo(md: str) -> None:
        assert "### S1 vs S3 Monte Carlo Consistency" in md
        assert (
            "Monte Carlo permutation standard errors are given by $\\text{SE}_{\\text{MC}}(p) = \\sqrt{p(1-p)/B}$ ($B=1000$). "
            "S1 and S3 p-values differing by less than two Monte Carlo standard errors are statistically consistent:"
        ) in md
        stat_map = [
            ("markov_hit1", "Markov Hit@1"),
            ("markov_hit3", "Markov Hit@3"),
            ("frequency_hit1", "Frequency Hit@1"),
            ("frequency_hit3", "Frequency Hit@3"),
            ("markov_fallback_hit1", "Markov Fallback Hit@1"),
            ("markov_fallback_hit3", "Markov Fallback Hit@3"),
            ("markov_minus_frequency_hit1", "Markov - Frequency Hit@1"),
            ("markov_minus_frequency_hit3", "Markov - Frequency Hit@3"),
        ]
        for lvl in ["technique_collapsed_full", "tactic_collapsed"]:
            for st, lbl in stat_map:
                p1 = perm_v2_json["schemes"]["S1_collapsed_order"][lvl][st]["p_value"]
                p3 = perm_v2_json["schemes"]["S3_constrained_shuffle"][lvl][st]["p_value"]
                se1 = math.sqrt(p1 * (1.0 - p1) / 1000.0)
                se3 = math.sqrt(p3 * (1.0 - p3) / 1000.0)
                diff = abs(p1 - p3)
                combined_2se = 2.0 * math.sqrt(se1**2 + se3**2)
                if diff <= combined_2se:
                    verdict = f"is less than two combined Monte Carlo standard errors ({combined_2se:.4f}), confirming S1 and S3 are consistent."
                else:
                    verdict = f"exceeds two combined Monte Carlo standard errors ({combined_2se:.4f}), reflecting sensitivity to the adjacency constraint on collapsed sequences."
                expected_line = f"- **{lbl}**: S1 $p = {p1:.4f}$ (MC SE $= {se1:.4f}$), S3 $p = {p3:.4f}$ (MC SE $= {se3:.4f}$); difference $|p_{{S1}} - p_{{S3}}| = {diff:.4f}$ {verdict}"
                assert expected_line in md, f"Missing MC line: {expected_line}"

    def check_perm_v2_what_this_cannot_show(md: str) -> None:
        assert "$N=67$ transition samples, and the tactic evaluation contains only $N=53$ transition samples across four episodes." in md
        assert "models are trained on only three episodes per fold, limiting transition coverage across a large technique vocabulary ($V=64$)." in md
        assert "failure to reject the shuffled-order null ($p \\ge 0.05$) does not constitute proof of absence" in md
        assert "limited statistical power achievable with three training episodes on this dataset." in md
        assert "accompanying real-scale planted-structure power analysis (A4 in `reports/planted_realscale_report.md`)" in md

    perm_v2_checks: list[Callable[[str], None]] = [
        check_perm_v2_setup,
        check_perm_v2_scheme_validity,
        check_perm_v2_sample_counts,
        check_perm_v2_s1_tables,
        check_perm_v2_s3_tables,
        check_perm_v2_monte_carlo,
        check_perm_v2_s2_tables,
        check_perm_v2_what_this_cannot_show,
    ]

    realscale_json = json.loads((REPORTS_DIR / "planted_realscale_report.json").read_text(encoding="utf-8"))

    def check_realscale_setup(md: str) -> None:
        c = realscale_json["metadata"]
        assert f"- **Vocabulary (V)**: All {c['vocabulary_size']} distinct MITRE ATT&CK technique IDs in real collapsed sequences E1–E4 (read at runtime, $V={c['vocabulary_size']}$)." in md
        assert r"- **Planted Successor Permutation (pi)**: Cyclic permutation $\pi(t_i) = t_{(i+1) \% V}$ over the sorted vocabulary without fixed points." in md
        assert f"- **Episode Lengths**: Real collapsed lengths of E1–E4 (19, 20, 21, 11), yielding {c['total_samples_per_replicate']} evaluated transition samples per replicate dataset." in md
        assert f"- **Evaluation Protocol**: {c['n_episodes']}-episode Leave-One-Episode-Out cross-validation using production `MarkovModel` and `FrequencyBaseline`." in md
        assert f"- **Signal Levels (s)**: `0.00, 0.25, 0.50, 0.75, 1.00` ({c['n_replicates']} replicates per signal level, seeds 0..{c['n_replicates'] - 1})." in md
        assert f"- **Chance Top-1**: $1/(V - 1) = 1/63 = {c['chance_top1']:.6f}$." in md

    def check_realscale_gates(md: str) -> None:
        g = realscale_json["gates"]
        assert f"| **G8** | s=0.0: |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE) | `{g['G8']['measured_diff']:.4f}` | `<= {g['G8']['threshold']:.4f}` | **PASS** |" in md
        traj_str = str([round(x, 4) for x in g['G9']['measured_trajectory']])
        assert f"| **G9** | Markov Top-1 non-decreasing across s | `{traj_str}` | Non-decreasing | **PASS** |" in md
        assert f"| **G10** | s=1.0: Markov Top-1 <= R and mean Markov >= 0.99 * mean R | Ratio: `{g['G10']['mean_ratio_m1_to_r']:.4f}` | All <= R & Ratio >= 0.9900 | **PASS** |" in md
        assert f"| **G11** | Negative Control: broken Markov fails G10 | Ratio: `{g['G11']['broken_ratio_to_r']:.4f}` | `< 0.9900 (must fail G10)` | **PASS (Failed G10 as expected)** |" in md

    def check_realscale_table(md: str) -> None:
        for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
            row = realscale_json["results_by_signal"][s_str]
            s = float(s_str)
            diff = row["markov_top1_mean"] - row["frequency_top1_mean"]
            sig_str = (
                f"**YES** (diff = {diff:+.4f})"
                if row["exceeds_2_combined_se"]
                else f"NO (diff = {diff:+.4f})"
            )
            line = (
                f"| {s:.2f} | {row['markov_top1_mean']:.4f} ± {row['markov_top1_se']:.4f} | "
                f"{row['markov_top3_mean']:.4f} ± {row['markov_top3_se']:.4f} | "
                f"{row['frequency_top1_mean']:.4f} ± {row['frequency_top1_se']:.4f} | "
                f"{row['frequency_top3_mean']:.4f} | {row['reachable_fraction_mean']:.4f} | {sig_str} |"
            )
            assert line in md, f"Missing realscale table row: {line}"

        real_obs = realscale_json["metadata"]["real_data_reference"]
        assert f"| *Real Data* | `{real_obs['markov_top1']:.4f}` | `{real_obs['markov_top3']:.4f}` | `{real_obs['frequency_top1']:.4f}` | `{real_obs['frequency_top3']:.4f}` | — | *real data, different generator, shown for scale only* |" in md
        assert f"**Smallest signal $s$ at which Markov Top-1 exceeds Frequency Top-1 by > 2 combined SE**: `s = {realscale_json['metadata']['smallest_s_exceeding_2_combined_se']:.2f}`." in md


    def check_realscale_insights(md: str) -> None:
        assert "1. **The Reachability Ceiling at Real Scale**: Even under a 100% deterministic sequential process ($s=1.00$), Leave-One-Episode-Out cross-validation on four episodes with lengths 19, 20, 21, and 11 over a 64-technique vocabulary only achieves a maximum reachable transition coverage of $\\approx 60.16\\%$ ($R=0.6016$). The remaining $\\approx 39.84\\%$ of test transitions never appeared in the three training episodes of that fold." in md
        assert "2. **Markov Optimality**: At $s=1.00$, the production Markov model achieves an empirical Top-1 accuracy of exactly $0.6016$, matching the reachable fraction $R$ in every replicate. It captures 100% of reachable signal and nothing unobserved." in md
        assert "3. **Statistical Power**: At $s=0.25$, Markov Top-1 ($0.0399$) already exceeds Frequency Top-1 ($0.0123$) by more than 2 combined standard errors. This establishes that the experimental setup has sufficient power to detect modest sequential structure ($s \\ge 0.25$) when present across independent folds." in md


    realscale_checks: list[Callable[[str], None]] = [
        check_realscale_setup,
        check_realscale_gates,
        check_realscale_table,
        check_realscale_insights,
    ]

    return planted_checks, perm_v2_checks, realscale_checks


def get_check_suites() -> tuple[list[Callable[[str], None]], list[Callable[[str], None]]]:
    """Precompute and cache recomputed datasets once for fast sweep execution."""
    recomputed_tactic = recompute_tactic()
    tactic_checks: list[Callable[[str], None]] = [
        lambda md: check_tac_sample_counts(md, recomputed_tactic),
        lambda md: check_headline_counts(md, recomputed_tactic),
        lambda md: check_headline_percentages(md, recomputed_tactic),
        lambda md: check_tac_wilson_table(md, recomputed_tactic),
        lambda md: check_tac_per_fold(md, recomputed_tactic),
        lambda md: check_tac_ref_baselines(md, recomputed_tactic),
        lambda md: check_tac_self_repeat(md, recomputed_tactic),
        lambda md: check_tac_paired_2x2(md, recomputed_tactic),
        lambda md: check_tac_freq_split(md, recomputed_tactic),
        lambda md: check_tac_covered_only(md, recomputed_tactic),
        lambda md: check_tac_tie_diag(md, recomputed_tactic),
        lambda md: check_tac_hit_concentration(md, recomputed_tactic),
        lambda md: check_tac_discrepancy(md, recomputed_tactic),
        lambda md: check_tac_ds_sensitivity_table(md, recomputed_tactic),
        lambda md: check_tac_sensitivity_sent(md, recomputed_tactic),
        lambda md: check_tac_derived_table(md, recomputed_tactic),
    ]

    recomputed_tech = recompute_technique()
    tech_json = json.loads((REPORTS_DIR / "evaluation_results.json").read_text(encoding="utf-8"))
    with open(PROCESSED_DIR / "evaluation_predictions.csv", "r", encoding="utf-8") as f:
        pred_rows = list(csv.DictReader(f))

    tech_checks: list[Callable[[str], None]] = [
        lambda md: check_tech_setup_and_definitions(md),
        lambda md: check_tech_headline_and_paired_tables(md, recomputed_tech),
        lambda md: check_tech_coverage_and_covered_only(md, recomputed_tech, tech_json),
        lambda md: check_tech_frequency_only_split_and_support_buckets(md, recomputed_tech),
        lambda md: check_tech_generated_sentences(md, recomputed_tech, tech_json),
        lambda md: check_tech_tie_diagnostic_and_hit_concentration(md, recomputed_tech),
        lambda md: check_tech_strict_subset(md, pred_rows),
        lambda md: check_tech_micro_precision_recall_f1(md, pred_rows, tech_json),
        lambda md: check_tech_self_repeat_and_repeat_current_set(md, pred_rows),
        lambda md: check_tech_wilson_intervals_section_3(md, pred_rows),
        lambda md: check_tech_abstentions_by_target(md, pred_rows),
        lambda md: check_tech_section_3_sentences(md, recomputed_tech),
        lambda md: check_tech_section_4_per_fold_table(md, recomputed_tech),
        lambda md: check_tech_section_5_per_fold_ceiling_and_coverage(md, tech_json),
        lambda md: check_tech_section_10_sensitivity_sentences(md, recomputed_tech),
        lambda md: check_tech_section_11_top1_errors_and_confusion_sentence(md, tech_json),
        lambda md: check_tech_section_12_examples_tables(md, tech_json),
        lambda md: check_tech_section_13_diagnostics(md, tech_json, recomputed_tech),
    ]

    return tactic_checks, tech_checks


def run_mutation_sweep() -> dict[str, dict[str, Any]]:
    """Backward-compatible entry point returning numeric mutation results for all reports."""
    tactic_checks, tech_checks = get_check_suites()
    planted_checks, perm_v2_checks, realscale_checks = get_validation_check_suites()

    tactic_res = sweep_report_numeric(
        "tactic_evaluation_report.md",
        REPORTS_DIR / "tactic_evaluation_report.md",
        tactic_checks,
        is_exempt_tactic,
    )
    tech_res = sweep_report_numeric(
        "evaluation_report.md",
        REPORTS_DIR / "evaluation_report.md",
        tech_checks,
        is_exempt_technique,
    )
    planted_res = sweep_report_numeric(
        "planted_structure_report.md",
        REPORTS_DIR / "planted_structure_report.md",
        planted_checks,
        is_exempt_planted,
    )
    perm_v2_res = sweep_report_numeric(
        "permutation_test_v2_report.md",
        REPORTS_DIR / "permutation_test_v2_report.md",
        perm_v2_checks,
        is_exempt_perm_v2,
    )
    realscale_res = sweep_report_numeric(
        "planted_realscale_report.md",
        REPORTS_DIR / "planted_realscale_report.md",
        realscale_checks,
        is_exempt_planted_realscale,
    )
    return {
        "tactic": tactic_res,
        "technique": tech_res,
        "planted_structure": planted_res,
        "permutation_test": perm_v2_res,
        "permutation_test_v2": perm_v2_res,
        "planted_realscale": realscale_res,
    }


def run_label_mutation_sweep() -> dict[str, dict[str, Any]]:
    """Run label mutation sweep returning results dictionary."""
    tactic_checks, tech_checks = get_check_suites()
    tactic_res = sweep_report_labels(
        "tactic_evaluation_report.md",
        REPORTS_DIR / "tactic_evaluation_report.md",
        tactic_checks,
    )
    tech_res = sweep_report_labels(
        "evaluation_report.md",
        REPORTS_DIR / "evaluation_report.md",
        tech_checks,
    )
    return {"tactic": tactic_res, "technique": tech_res}


def run_all_mutation_sweeps() -> None:
    tactic_checks, tech_checks = get_check_suites()
    planted_checks, perm_v2_checks, realscale_checks = get_validation_check_suites()

    # =========================================================================
    # PART A & B: Numeric Mutation Sweep
    # =========================================================================
    print("=" * 80)
    print("PART A & B: MECHANICAL NUMERIC MUTATION SWEEP")
    print("=" * 80)

    num_tactic = sweep_report_numeric(
        "tactic_evaluation_report.md",
        REPORTS_DIR / "tactic_evaluation_report.md",
        tactic_checks,
        is_exempt_tactic,
    )
    num_tech = sweep_report_numeric(
        "evaluation_report.md",
        REPORTS_DIR / "evaluation_report.md",
        tech_checks,
        is_exempt_technique,
    )
    num_planted = sweep_report_numeric(
        "planted_structure_report.md",
        REPORTS_DIR / "planted_structure_report.md",
        planted_checks,
        is_exempt_planted,
    )
    num_perm_v2 = sweep_report_numeric(
        "permutation_test_v2_report.md",
        REPORTS_DIR / "permutation_test_v2_report.md",
        perm_v2_checks,
        is_exempt_perm_v2,
    )
    num_realscale = sweep_report_numeric(
        "planted_realscale_report.md",
        REPORTS_DIR / "planted_realscale_report.md",
        realscale_checks,
        is_exempt_planted_realscale,
    )

    numeric_results = {
        "tactic": num_tactic,
        "technique": num_tech,
        "planted_structure": num_planted,
        "permutation_test_v2": num_perm_v2,
        "planted_realscale": num_realscale,
    }

    # Print Part A Exempt list
    print("\n" + "=" * 80)
    print("PART A: EXEMPT TOKENS LIST (EVERY EXEMPT TOKEN PRINTED VERBATIM)")
    print("=" * 80)
    for key, res in numeric_results.items():
        print(f"\n--- REPORT: {res['report']} (Exempt: {res['exempt_total']} tokens) ---")
        for item in res["exempt_items"]:
            print(f"{item['report']}:{item['line_number']} [{item['token']}] ({item['rule']}) -> {item['line_text']}")

    print("\n" + "=" * 80)
    print("EXCLUDED FROM ACTIVE MUTATION SWEEP:")
    print("  - reports/archive/permutation_test_report_v1_counts_superseded.md (v1 permutation test report superseded due to sample-count confound; archived per Prompt 10b)")
    print("=" * 80)

    # Print Part B Exception types reporting
    print("\n" + "=" * 80)
    print("PART B: DETECTION TYPES REPORT (AssertionError vs Other Exception Classes)")
    print("=" * 80)
    print(f"\n| Report | Detected Total | AssertionError | Other (KeyError) |")
    print(f"|---|---|---|---|")
    for key, res in numeric_results.items():
        ass_cnt = res["exception_classes"].get("AssertionError", 0)
        oth_cnt = sum(cnt for c, cnt in res["exception_classes"].items() if c != "AssertionError")
        print(f"| {res['report']} | {res['detected']} | {ass_cnt} | {oth_cnt} |")

    print("\nNon-AssertionError Detections (Line by Line):")
    for key, res in numeric_results.items():
        if res["non_assertion_detections"]:
            print(f"\n--- Report: {res['report']} ({len(res['non_assertion_detections'])} non-assertion detections) ---")
            for item in res["non_assertion_detections"]:
                print(f"  Line {item['line_number']} [{item['token']}]: {item['exception_class']} -> {item['message']}")

    # Print Part F Summary
    print("\n" + format_summary_block(numeric_results, "NUMERIC MUTATION SWEEP SUMMARY"))

    # =========================================================================
    # PART G: Label Mutation Sweep
    # =========================================================================
    print("\n" + "=" * 80)
    print("PART G: MECHANICAL DATA-BEARING LABEL MUTATION SWEEP")
    print("=" * 80)
    print("\nEXPLICIT VOCABULARY DEFINITION:")
    for grp, items in LABEL_VOCABULARY.items():
        print(f"  - {grp:<13} ({len(items)} items): {', '.join(items)}")

    label_tactic = sweep_report_labels(
        "tactic_evaluation_report.md",
        REPORTS_DIR / "tactic_evaluation_report.md",
        tactic_checks,
    )
    label_tech = sweep_report_labels(
        "evaluation_report.md",
        REPORTS_DIR / "evaluation_report.md",
        tech_checks,
    )
    label_results = {"tactic": label_tactic, "technique": label_tech}

    for key, res in label_results.items():
        print(f"\n--- REPORT: {res['report']} ---")
        print(f"  Tested total:  {res['total_tested']}")
        print(f"  DETECTED:      {res['detected']} ({res['detected'] / res['total_tested'] * 100:.2f}%)")
        print(f"  UNDETECTED:    {res['undetected']}")
        print(f"  By Group:      {res['group_counts']}")
        print(f"  Exceptions:    {res['exception_classes']}")

        if res["undetected_items"]:
            print("  UNDETECTED LIST:")
            for u in res["undetected_items"]:
                print(f"    Line {u['line_number']} [{u['group']}] {u['original']} -> {u['replacement']}: {u['line_text']}")
        else:
            print("  All tested label mutations successfully DETECTED (0 undetected).")

    print("\n" + format_summary_block(label_results, "LABEL MUTATION SWEEP SUMMARY"))


if __name__ == "__main__":
    run_all_mutation_sweeps()

