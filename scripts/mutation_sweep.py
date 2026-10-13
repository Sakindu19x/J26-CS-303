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
    lines.append("=" * 80)
    return "\n".join(lines)


# ==============================================================================
# Main Runner Functions
# ==============================================================================

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
    """Backward-compatible entry point returning numeric mutation results."""
    tactic_checks, tech_checks = get_check_suites()
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
    return {"tactic": tactic_res, "technique": tech_res}


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

    numeric_results = {"tactic": num_tactic, "technique": num_tech}

    # Print Part A Exempt list
    print("\n" + "=" * 80)
    print("PART A: EXEMPT TOKENS LIST (EVERY EXEMPT TOKEN PRINTED VERBATIM)")
    print("=" * 80)
    for key, res in numeric_results.items():
        print(f"\n--- REPORT: {res['report']} (Exempt: {res['exempt_total']} tokens) ---")
        for item in res["exempt_items"]:
            print(f"{item['report']}:{item['line_number']} [{item['token']}] ({item['rule']}) -> {item['line_text']}")

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
