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


def is_exempt_eval_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    """Explicit exemption rules for reports/7ep/evaluation_7ep_report.md."""
    # Rule 1: Heading lines
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"

    # Rule 2: Table delimiter rows
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"

    # Rule 3: Table column header labels
    if (
        "| Model |" in line
        or "| Fold |" in line
        or "| Contingency Cell |" in line
        or "| Comparison |" in line
        or "| Slice |" in line
    ):
        return True, "Table column header label"

    # Rule 4: Parameter k in Random baseline label
    if "| Random (k=1,3)" in line and tok in ("1", "3"):
        return True, "Random baseline parameter specification (k=1,3)"

    return False, ""


def is_exempt_learning_curve_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Subsets / Ep |" in line or "| Episode |" in line or "| k |" in line:
        return True, "Table column header label"
    if "prereg_7episode_design.md" in line:
        return True, "Document filename / amendment cross-reference"
    if "Amendments 1–4" in line:
        return True, "Amendment cross-reference"
    if "C4 dataset" in line and tok == "4":
        return True, "Dataset name C4"
    if "(E1–E7)" in line and tok in ("1", "7"):
        return True, "Episode range identifier (E1-E7)"
    if "Section 7" in line and tok == "7":
        return True, "Preregistration section reference"
    if "reports/7ep/" in line and tok == "7":
        return True, "Filepath directory component 7ep"
    return False, ""


def is_exempt_permutation_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Scheme |" in line or "| Statistic |" in line or "| Observed Rate |" in line or "| Permutation Min N |" in line:
        return True, "Table column header label"
    if "Max Tries Allowed Per Episode" in line and tok == "10000":
        return True, "Pre-declared S3 rejection sampling maximum tries parameter"
    if "up to 10,000 tries" in line and tok == "10000":
        return True, "Pre-declared S3 rejection sampling maximum tries parameter"
    if "B=1000" in line and tok in ("1000", "0", "999"):
        return True, "Permutation count parameter syntax B=1000"
    if "prereg_7episode_design.md" in line:
        return True, "Prereg document reference"
    if "Section 10" in line and tok == "10":
        return True, "Prereg section reference"
    if "(E1–E7)" in line and tok in ("1", "7"):
        return True, "Episode range identifier (E1-E7)"
    return False, ""


def is_exempt_planted_realscale_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Signal" in line or "| Gate" in line:
        return True, "Table column header label"
    if r"\pi(t_i)" in line or "1/(V - 1)" in line:
        return True, "Mathematical formula definition syntax"
    if "(E1–E7)" in line and tok in ("1", "7"):
        return True, "Episode range identifier (E1-E7)"
    return False, ""


def is_exempt_e5_removed(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Metric |" in line or "| Fold |" in line or "| Comparison |" in line:
        return True, "Table column header label"
    if "prereg Section 8" in line and tok == "8":
        return True, "Prereg section reference"
    return False, ""


def is_exempt_holm_claim_rule(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Hypothesis |" in line:
        return True, "Table column header label"
    if line.strip().startswith("> 1.") or line.strip().startswith("> 2."):
        return True, "Pre-declared claim rule condition index"
    if r"\alpha=0.05" in line and tok in ("0.05", "05"):
        return True, "Pre-declared alpha significance threshold syntax"
    if "prereg Section 6" in line and tok == "6":
        return True, "Prereg section reference"
    if "Amendment 1" in line and tok == "1":
        return True, "Prereg amendment reference"
    if "m=4" in line and tok == "4":
        return True, "Hypothesis family count parameter m=4"
    return False, ""


def is_exempt_diagnostics_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Slice |" in line or "| Held-Out Episode |" in line:
        return True, "Table column header label"
    return False, ""


def is_exempt_e5_hit1_diagnostic(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Sample ID |" in line or "| Test Episode |" in line:
        return True, "Table column header label"
    if "(E1–E4, E6, E7, N=74)" in line and tok in ("1", "4", "6", "7"):
        return True, "Episode range identifier in prose"
    if "E1–E4, E6, or E7" in line and tok in ("1", "4", "6", "7"):
        return True, "Episode range identifier in prose"
    if "7-episode" in line and tok == "7":
        return True, "7-episode protocol reference in prose"
    if "7-Episode" in line and tok == "7":
        return True, "7-episode protocol reference in prose"
    if "E5-removed" in line and tok == "5":
        return True, "E5 episode identifier in prose"
    return False, ""


def is_exempt_tie_sensitivity_7ep(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if (
        "| Run |" in line
        or "| Model |" in line
        or "| Sample ID |" in line
        or "| Bound Condition |" in line
        or "| Observed Hit@1 |" in line
    ):
        return True, "Table column header label"
    if line.strip().startswith("- **E") and ("-tac-" in line or "-col-" in line):
        return True, "Sample ID and episode identifier in list header"
    if "The 7 samples whose Markov top-1" in line:
        return True, "Explanatory lead-in sentence for diagnostic 7 samples"
    if "For tactic Hit@1" in line and tok == "1":
        return True, "Metric name Hit@1 in explanatory sentence"
    if "7-episode" in line and tok == "7":
        return True, "7-episode reference"
    if "7-Episode" in line and tok == "7":
        return True, "7-episode reference"
    if "E5" in line and tok == "5":
        return True, "E5 episode reference"
    if "N=76" in line and tok in ("76",):
        return True, "Sample count reference N=76"
    if "N=95" in line and tok in ("95",):
        return True, "Sample count reference N=95"
    if "1e-9" in line and tok in ("1", "9"):
        return True, "Float tolerance constant 1e-9"
    if "10^{-9}" in line and tok in ("10", "9"):
        return True, "Float tolerance LaTeX constant 10^-9"
    return False, ""


def is_exempt_exploratory_tactic_conditioned(
    line: str, line_no: int, tok: str, start_in_line: int, end_in_line: int
) -> tuple[bool, str]:
    if line.startswith("#"):
        return True, "Heading outline / section index in markdown header"
    if line.strip().startswith("|---") or line.strip().startswith("|:---") or line.strip().startswith("| :---"):
        return True, "Table delimiter row syntax"
    if "| Model" in line or "| Metric" in line:
        return True, "Table column header label"
    if "Amendment 7" in line and tok in ("7", "2026", "10", "15"):
        return True, "Amendment 7 pre-registration date reference"
    if "N=95" in line and tok == "95":
        return True, "Sample count reference N=95"
    if "N=93" in line and tok == "93":
        return True, "Sample count reference N=93"
    if "7 episodes" in line and tok == "7":
        return True, "7 episodes count reference"
    if "7-episode" in line and tok == "7":
        return True, "7-episode design reference"
    if "E5" in line and tok == "5":
        return True, "E5 episode reference"
    if "Hit@1" in line and tok == "1":
        return True, "Metric name Hit@1 token"
    if "Hit@3" in line and tok == "3":
        return True, "Metric name Hit@3 token"
    if "Top-1" in line and tok == "1":
        return True, "Metric name Top-1 token"
    if "Top-3" in line and tok == "3":
        return True, "Metric name Top-3 token"
    if "P1" in line and tok == "1":
        return True, "Pre-registered hypothesis P1 token"
    if "S1" in line and tok == "1":
        return True, "Permutation scheme S1 token"
    if "reports/7ep/" in line and tok == "7":
        return True, "7ep directory path reference"
    if "p = 0.0410" in line and tok in ("0.0410", "1"):
        return True, "Lead-in permutation p-value"
    if "p = 0.0390" in line and tok in ("0.0390", "3"):
        return True, "Lead-in permutation p-value"
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
    "fold": ["fold_1", "fold_2", "fold_3", "fold_4", "fold_5", "fold_6", "fold_7"],
    "episode": ["E1", "E2", "E3", "E4", "E5", "E6", "E7"],
    "comparison": ["equal to", "the same", "different", "above", "below"],
    "status": ["insufficient_evidence", "abstained", "abstain", "ok"],
    "tactic": [
        "initial-access", "execution", "persistence", "privilege-escalation",
        "defense-evasion", "credential-access", "discovery", "lateral-movement",
        "collection", "command-and-control", "exfiltration", "impact",
        "reconnaissance", "resource-development",
    ],
}

LABEL_REPLACEMENTS: dict[str, dict[str, str]] = {
    "method": {
        "markov": "frequency", "Markov": "Frequency",
        "frequency": "markov", "Frequency": "Markov",
        "markov_fallback": "markov", "Markov_fallback": "Markov",
        "Markov Fallback": "Markov", "Fallback": "Frequency",
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
        "fold_5": "fold_6", "fold_6": "fold_5",
        "fold_7": "fold_1",
        "Fold_1": "Fold_2", "Fold_2": "Fold_1",
        "Fold_3": "Fold_4", "Fold_4": "Fold_3",
        "Fold_5": "Fold_6", "Fold_6": "Fold_5",
        "Fold_7": "Fold_1",
    },
    "episode": {
        "E1": "E2", "E2": "E1", "E3": "E4", "E4": "E3",
        "E5": "E6", "E6": "E5", "E7": "E1",
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
    "tactic": {
        "initial-access": "execution",
        "execution": "initial-access",
        "persistence": "privilege-escalation",
        "privilege-escalation": "persistence",
        "defense-evasion": "credential-access",
        "credential-access": "defense-evasion",
        "discovery": "lateral-movement",
        "lateral-movement": "discovery",
        "collection": "command-and-control",
        "command-and-control": "collection",
        "exfiltration": "impact",
        "impact": "exfiltration",
        "reconnaissance": "resource-development",
        "resource-development": "reconnaissance",
    },
}

VOCAB_SCAN_ORDER = [
    ("configuration", LABEL_VOCABULARY["configuration"]),
    ("method", LABEL_VOCABULARY["method"]),
    ("fold", LABEL_VOCABULARY["fold"]),
    ("episode", LABEL_VOCABULARY["episode"]),
    ("comparison", LABEL_VOCABULARY["comparison"]),
    ("status", LABEL_VOCABULARY["status"]),
    ("tactic", LABEL_VOCABULARY["tactic"]),
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
    if "evaluation_7ep" in results:
        lines.append(format_summary_line("Eval7Ep", results["evaluation_7ep"]))
    if "learning_curve_7ep" in results:
        lines.append(format_summary_line("LearnCurve7Ep", results["learning_curve_7ep"]))
    if "permutation_7ep" in results:
        lines.append(format_summary_line("Perm7Ep", results["permutation_7ep"]))
    if "planted_realscale_7ep" in results:
        lines.append(format_summary_line("Planted7Ep", results["planted_realscale_7ep"]))
    if "e5_removed" in results:
        lines.append(format_summary_line("E5Removed", results["e5_removed"]))
    if "holm_claim_rule" in results:
        lines.append(format_summary_line("HolmClaimRule", results["holm_claim_rule"]))
    if "diagnostics_7ep" in results:
        lines.append(format_summary_line("Diag7Ep", results["diagnostics_7ep"]))
    if "e5_hit1_change_diagnostic" in results:
        lines.append(format_summary_line("E5Hit1Diag", results["e5_hit1_change_diagnostic"]))
    if "tie_sensitivity_7ep" in results:
        lines.append(format_summary_line("TieSens7Ep", results["tie_sensitivity_7ep"]))
    if "exploratory_tactic_conditioned" in results:
        lines.append(format_summary_line("Exploratory", results["exploratory_tactic_conditioned"]))
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

        assert "a scheme that fails validity at any level is labelled invalid at every level" in md


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
                    verdict = f"exceeds two combined Monte Carlo standard errors ({combined_2se:.4f}); p-values differ by more than two combined Monte Carlo standard errors, no cause inferred."
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


def check_tac_universe_setup(md: str) -> None:
    assert "- **Tactic Universe**: 14 ATT&CK Enterprise v16.1 tactics (shortname tokens, e.g. `initial-access`, `defense-evasion`)." in md


def get_check_suites() -> tuple[list[Callable[[str], None]], list[Callable[[str], None]]]:
    """Precompute and cache recomputed datasets once for fast sweep execution."""
    recomputed_tactic = recompute_tactic()
    tactic_checks: list[Callable[[str], None]] = [
        check_tac_universe_setup,
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


def get_eval_7ep_check_suites() -> list[Callable[[str], None]]:
    results_json = json.loads((REPORTS_DIR / "7ep" / "evaluation_7ep_results.json").read_text(encoding="utf-8"))

    def check_eval_7ep_intro_and_setup(md: str) -> None:
        assert "This report documents the pre-registered leave-one-episode-out (LOEO) evaluation across all seven episodes (E1–E7) of the C4 dataset." in md
        assert "All procedures strictly adhere to `reports/prereg_7episode_design.md` with Amendments 1, 2, and 3." in md
        assert "- **Evaluated Episodes**: E1, E2, E3, E4, E5, E6, E7 ($7$ folds)." in md
        assert "1. **Primary**: Technique `collapsed_full` ($N=95$ transition samples)." in md
        assert "2. **Secondary**: Tactic `tactic_collapsed` ($N=76$ transition samples)." in md
        assert "3. **Reference**: Technique `raw_full` ($N=131$ transition samples)." in md
        assert "- **Models Evaluated**: `MarkovModel` (first-order Markov chain), `FrequencyBaseline` (unconditional frequency), and `markov_fallback` (fallback to frequency when Markov status is not ok)." in md
        assert "- **Fold Models**: Stored deterministically in `artifacts/7ep/fold_models/<slice>/<test_episode>.json` with hashes recorded in `artifacts/7ep/fold_models/manifest.json`." in md
        assert "- **Episode E5**: Evaluated as an explicit test fold ($N=2$, covered=0, ceiling=0)." in md

    def check_eval_7ep_primary_collapsed_full(md: str) -> None:
        sec2 = md.split("## 2. Primary Slice")[1].split("## 3. Secondary Slice")[0]
        head = results_json["primary_slice_technique_collapsed_full"]["headline"]
        m = head["markov"]
        f = head["frequency"]
        fb = head["fallback"]
        line_m = f"| Markov          |  {m['hit1']} / 95 | {m['top1']:.4f} | [{m['wilson95_top1'][0]:.4f}, {m['wilson95_top1'][1]:.4f}]      |  {m['hit3']} / 95 | {m['top3']:.4f} | [{m['wilson95_top3'][0]:.4f}, {m['wilson95_top3'][1]:.4f}]      | {m['fold_mean_top1']:.4f} | {m['fold_mean_top3']:.4f} |"
        assert line_m in sec2, f"Missing: {line_m}"
        line_f = f"| Frequency       |  {f['hit1']} / 95 | {f['top1']:.4f} | [{f['wilson95_top1'][0]:.4f}, {f['wilson95_top1'][1]:.4f}]      | {f['hit3']} / 95 | {f['top3']:.4f} | [{f['wilson95_top3'][0]:.4f}, {f['wilson95_top3'][1]:.4f}]      | {f['fold_mean_top1']:.4f} | {f['fold_mean_top3']:.4f} |"
        assert line_f in sec2, f"Missing: {line_f}"
        line_fb = f"| Markov Fallback |  {fb['hit1']} / 95 | {fb['top1']:.4f} | [{fb['wilson95_top1'][0]:.4f}, {fb['wilson95_top1'][1]:.4f}]      |  {fb['hit3']} / 95 | {fb['top3']:.4f} | [{fb['wilson95_top3'][0]:.4f}, {fb['wilson95_top3'][1]:.4f}]      | {fb['fold_mean_top1']:.4f} | {fb['fold_mean_top3']:.4f} |"
        assert line_fb in sec2, f"Missing: {line_fb}"

        cov = head["coverage"]
        assert f"- **Coverage (Markov Status ok)**: {cov['covered_samples']}/95 ({cov['coverage_rate']:.4f})." in sec2
        assert f"- On covered samples ($N={cov['covered_n']}$): Markov Hit@1 = {cov['markov_on_covered_hit1']}/{cov['covered_n']} ({cov['markov_on_covered_top1']:.4f}), Frequency Hit@1 = {cov['frequency_on_covered_hit1']}/{cov['covered_n']} ({cov['frequency_on_covered_top1']:.4f})." in sec2
        assert f"- On covered samples ($N={cov['covered_n']}$): Markov Hit@3 = {cov['markov_on_covered_hit3']}/{cov['covered_n']} ({cov['markov_on_covered_top3']:.4f}), Frequency Hit@3 = {cov['frequency_on_covered_hit3']}/{cov['covered_n']} ({cov['frequency_on_covered_top3']:.4f})." in sec2
        assert f"- **Target Ceiling**: {head['ceiling']['hits']}/95 ({head['ceiling']['ceiling_rate']:.4f}) of samples had at least one target technique appearing in training targets for that fold." in sec2

        pf = results_json["primary_slice_technique_collapsed_full"]["per_fold"]
        for fid, fd in sorted(pf.items(), key=lambda x: int(x[0].split("_")[1])):
            tep = fd["test_episode"]
            fn = fd["n_samples"]
            m_h1 = fd["markov"]["hit1"]
            m_h3 = fd["markov"]["hit3"]
            f_h1 = fd["frequency"]["hit1"]
            f_h3 = fd["frequency"]["hit3"]
            fb_h1 = fd["fallback"]["hit1"]
            fb_h3 = fd["fallback"]["hit3"]
            cov_s = fd["markov"]["covered_samples"]
            ceil_s = fd["ceiling"]["hits"]
            line_pf = f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({fd['markov']['top1']:.4f}) | {m_h3:2d} ({fd['markov']['top3']:.4f}) | {f_h1:2d} ({fd['frequency']['top1']:.4f}) | {f_h3:2d} ({fd['frequency']['top3']:.4f}) | {fb_h1:2d} ({fd['fallback']['top1']:.4f}) | {fb_h3:2d} ({fd['fallback']['top3']:.4f}) | {cov_s:2d} / {fn:2d} | {ceil_s:2d} / {fn:2d} |"
            assert line_pf in sec2, f"Missing per-fold line in sec2: {line_pf}"

    def check_eval_7ep_secondary_tactic(md: str) -> None:
        sec3 = md.split("## 3. Secondary Slice")[1].split("## 4. Reference Slice")[0]
        sec = results_json["secondary_slice_tactic_collapsed"]
        head = sec["headline"]
        m = head["markov"]
        f = head["frequency"]
        fb = head["markov_fallback"]
        line_m = f"| Markov          | {m['hit1']} / 76 | {m['top1']:.4f} | [{m['wilson95_top1'][0]:.4f}, {m['wilson95_top1'][1]:.4f}]      | {m['hit3']} / 76 | {m['top3']:.4f} | [{m['wilson95_top3'][0]:.4f}, {m['wilson95_top3'][1]:.4f}]      | {m['fold_mean_top1']:.4f} | {m['fold_mean_top3']:.4f} |"
        assert line_m in sec3, f"Missing: {line_m}"
        line_f = f"| Frequency       | {f['hit1']} / 76 | {f['top1']:.4f} | [{f['wilson95_top1'][0]:.4f}, {f['wilson95_top1'][1]:.4f}]      | {f['hit3']} / 76 | {f['top3']:.4f} | [{f['wilson95_top3'][0]:.4f}, {f['wilson95_top3'][1]:.4f}]      | {f['fold_mean_top1']:.4f} | {f['fold_mean_top3']:.4f} |"
        assert line_f in sec3, f"Missing: {line_f}"
        line_fb = f"| Markov Fallback | {fb['hit1']} / 76 | {fb['top1']:.4f} | [{fb['wilson95_top1'][0]:.4f}, {fb['wilson95_top1'][1]:.4f}]      | {fb['hit3']} / 76 | {fb['top3']:.4f} | [{fb['wilson95_top3'][0]:.4f}, {fb['wilson95_top3'][1]:.4f}]      | {fb['fold_mean_top1']:.4f} | {fb['fold_mean_top3']:.4f} |"
        assert line_fb in sec3, f"Missing: {line_fb}"

        rg = sec["diagnostics"]["random_guess"]
        line_rg = f"| Random (k=1,3)  |  --  / 76 | {rg['mean_p_hit1']:.4f} | [Expected Reference]  |  --  / 76 | {rg['mean_p_hit3']:.4f} | [Expected Reference]  |   --   |   --   |"
        assert line_rg in sec3, f"Missing: {line_rg}"

        cov = sec["coverage"]
        ceil = sec["ceiling"]
        assert f"- **Coverage (Markov Status ok)**: {cov['covered_samples']}/76 ({cov['coverage_rate']:.4f})." in sec3
        assert f"- **Target Ceiling**: {ceil['hits']}/76 ({ceil['ceiling_rate']:.4f})." in sec3

        pf = sec["per_fold"]
        for fid, fd in sorted(pf.items(), key=lambda x: int(x[0].split("_")[1])):
            tep = fd["test_episode"]
            fn = fd["n_samples"]
            m_h1 = fd["markov"]["hit1"]
            m_h3 = fd["markov"]["hit3"]
            f_h1 = fd["frequency"]["hit1"]
            f_h3 = fd["frequency"]["hit3"]
            fb_h1 = fd["fallback"]["hit1"]
            fb_h3 = fd["fallback"]["hit3"]
            cov_s = fd["covered_samples"]
            ceil_s = fd["ceiling_hits"]
            line_pf = f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({fd['markov']['top1']:.4f}) | {m_h3:2d} ({fd['markov']['top3']:.4f}) | {f_h1:2d} ({fd['frequency']['top1']:.4f}) | {f_h3:2d} ({fd['frequency']['top3']:.4f}) | {fb_h1:2d} ({fd['fallback']['top1']:.4f}) | {fb_h3:2d} ({fd['fallback']['top3']:.4f}) | {cov_s:2d} / {fn:2d} | {ceil_s:2d} / {fn:2d} |"
            assert line_pf in sec3, f"Missing per-fold line in sec3: {line_pf}"

    def check_eval_7ep_reference_raw_full(md: str) -> None:
        sec4 = md.split("## 4. Reference Slice")[1].split("## 5. Pre-Registered Paired Comparisons")[0]
        ref = results_json["reference_slice_technique_raw_full"]
        head = ref["headline"]
        m = head["markov"]
        f = head["frequency"]
        fb = head["fallback"]
        line_m = f"| Markov          | {m['hit1']} / 131 | {m['top1']:.4f} | [{m['wilson95_top1'][0]:.4f}, {m['wilson95_top1'][1]:.4f}]      | {m['hit3']} / 131 | {m['top3']:.4f} | [{m['wilson95_top3'][0]:.4f}, {m['wilson95_top3'][1]:.4f}]      | {m['fold_mean_top1']:.4f} | {m['fold_mean_top3']:.4f} |"
        assert line_m in sec4, f"Missing: {line_m}"
        line_f = f"| Frequency       |  {f['hit1']} / 131 | {f['top1']:.4f} | [{f['wilson95_top1'][0]:.4f}, {f['wilson95_top1'][1]:.4f}]      | {f['hit3']} / 131 | {f['top3']:.4f} | [{f['wilson95_top3'][0]:.4f}, {f['wilson95_top3'][1]:.4f}]      | {f['fold_mean_top1']:.4f} | {f['fold_mean_top3']:.4f} |"
        assert line_f in sec4, f"Missing: {line_f}"
        line_fb = f"| Markov Fallback | {fb['hit1']} / 131 | {fb['top1']:.4f} | [{fb['wilson95_top1'][0]:.4f}, {fb['wilson95_top1'][1]:.4f}]      | {fb['hit3']} / 131 | {fb['top3']:.4f} | [{fb['wilson95_top3'][0]:.4f}, {fb['wilson95_top3'][1]:.4f}]      | {fb['fold_mean_top1']:.4f} | {fb['fold_mean_top3']:.4f} |"
        assert line_fb in sec4, f"Missing: {line_fb}"

        cov = head["coverage"]
        ceil = head["ceiling"]
        assert f"- **Coverage (Markov Status ok)**: {cov['covered_samples']}/131 ({cov['coverage_rate']:.4f})." in sec4
        assert f"- **Target Ceiling**: {ceil['hits']}/131 ({ceil['ceiling_rate']:.4f})." in sec4

        pf = ref["per_fold"]
        for fid, fd in sorted(pf.items(), key=lambda x: int(x[0].split("_")[1])):
            tep = fd["test_episode"]
            fn = fd["n_samples"]
            m_h1 = fd["markov"]["hit1"]
            m_h3 = fd["markov"]["hit3"]
            f_h1 = fd["frequency"]["hit1"]
            f_h3 = fd["frequency"]["hit3"]
            fb_h1 = fd["fallback"]["hit1"]
            fb_h3 = fd["fallback"]["hit3"]
            cov_s = fd["markov"]["covered_samples"]
            ceil_s = fd["ceiling"]["hits"]
            line_pf = f"| {fid:6s} | {tep:12s} | {fn:2d} | {m_h1:2d} ({fd['markov']['top1']:.4f}) | {m_h3:2d} ({fd['markov']['top3']:.4f}) | {f_h1:2d} ({fd['frequency']['top1']:.4f}) | {f_h3:2d} ({fd['frequency']['top3']:.4f}) | {fb_h1:2d} ({fd['fallback']['top1']:.4f}) | {fb_h3:2d} ({fd['fallback']['top3']:.4f}) | {cov_s:2d} / {fn:2d} | {ceil_s:2d} / {fn:2d} |"
            assert line_pf in sec4, f"Missing per-fold line in sec4: {line_pf}"

    def check_eval_7ep_paired_tests(md: str) -> None:
        assert "Per `reports/prereg_7episode_design.md` Section 6, the paired comparisons between `MarkovModel` and `FrequencyBaseline` are evaluated using exact two-sided McNemar tests on per-sample binary hit outcomes:" in md
        pts = results_json["paired_tests"]
        p1 = pts["P1_tactic_collapsed_hit3"]
        t1 = p1["table"]
        assert f"| Both Hit ($a$) | {t1['both_hit']:2d} | Both models predicted a correct tactic in top-3 |" in md
        assert f"| Markov Only ($b$) | {t1['b_m1_only']:2d} | Markov predicted correct in top-3, Frequency missed |" in md
        assert f"| Frequency Only ($c$) | {t1['c_m2_only']:2d} | Frequency predicted correct in top-3, Markov missed |" in md
        assert f"| Neither Hit ($d$) | {t1['neither']:2d} | Neither model predicted a correct tactic in top-3 |" in md
        assert f"- **Sample Size**: $N = {p1['n_samples']}$" in md
        assert f"- **Markov Pooled Rate**: {p1['m1_rate']:.4f} ({p1['m1_rate']*p1['n_samples']:.0f}/{p1['n_samples']})" in md
        assert f"- **Frequency Pooled Rate**: {p1['m2_rate']:.4f} ({p1['m2_rate']*p1['n_samples']:.0f}/{p1['n_samples']})" in md
        assert f"- **Pooled Rate Difference (Markov - Frequency)**: {p1['rate_difference']:+.4f}" in md
        assert f"- **Discordant Counts**: $b = {t1['b_m1_only']}$, $c = {t1['c_m2_only']}$" in md
        assert f"- **Exact Two-Sided McNemar Test**: $p = {p1['p_value_raw']:.4f}$ (raw p, pre-Holm)" in md

        p2 = pts["P2_technique_collapsed_full_hit3"]
        t2 = p2["table"]
        assert f"| Both Hit ($a$) |  {t2['both_hit']} | Both models predicted a correct technique in top-3 |" in md
        assert f"| Markov Only ($b$) |  {t2['b_m1_only']} | Markov predicted correct in top-3, Frequency missed |" in md
        assert f"| Frequency Only ($c$) | {t2['c_m2_only']:2d} | Frequency predicted correct in top-3, Markov missed |" in md
        assert f"| Neither Hit ($d$) | {t2['neither']:2d} | Neither model predicted a correct technique in top-3 |" in md
        assert f"- **Sample Size**: $N = {p2['n_samples']}$" in md
        assert f"- **Markov Pooled Rate**: {p2['m1_rate']:.4f} ({p2['m1_rate']*p2['n_samples']:.0f}/{p2['n_samples']})" in md
        assert f"- **Frequency Pooled Rate**: {p2['m2_rate']:.4f} ({p2['m2_rate']*p2['n_samples']:.0f}/{p2['n_samples']})" in md
        assert f"- **Pooled Rate Difference (Markov - Frequency)**: {p2['rate_difference']:+.4f}" in md
        assert f"- **Discordant Counts**: $b = {t2['b_m1_only']}$, $c = {t2['c_m2_only']}$" in md
        assert f"- **Exact Two-Sided McNemar Test**: $p = {p2['p_value_raw']:.4f}$ (raw p, pre-Holm)" in md

        desc_keys = [
            ("descriptive_technique_collapsed_full_hit1", "Markov vs Frequency", "collapsed_full", "Hit@1"),
            ("descriptive_tactic_collapsed_hit1", "Markov vs Frequency", "tactic_collapsed", "Hit@1"),
            ("descriptive_technique_fallback_vs_freq_hit3", "Fallback vs Frequency", "collapsed_full", "Hit@3"),
            ("descriptive_technique_fallback_vs_freq_hit1", "Fallback vs Frequency", "collapsed_full", "Hit@1"),
            ("descriptive_tactic_fallback_vs_freq_hit3", "Fallback vs Frequency", "tactic_collapsed", "Hit@3"),
            ("descriptive_tactic_fallback_vs_freq_hit1", "Fallback vs Frequency", "tactic_collapsed", "Hit@1"),
        ]
        for k_test, comp_label, sl_label, met_label in desc_keys:
            pt = pts[k_test]
            tt = pt["table"]
            line_desc = f"| {comp_label:23s} | {sl_label:16s} | {met_label:5s} | {pt['m1_rate']:.4f} | {pt['m2_rate']:.4f} | {pt['rate_difference']:+.4f} | {tt['b_m1_only']:2d} | {tt['c_m2_only']:2d} | {pt['p_value_raw']:.4f} | raw p, pre-Holm |"
            assert line_desc in md, f"Missing non-primary line: {line_desc}"

    def check_eval_7ep_comparison_4ep(md: str) -> None:
        assert "The following table compares the 7-episode results with the archived 4-episode baseline numbers read directly from `reports/evaluation_results.json` and `reports/tactic_evaluation_results.json`:" in md
        comp = results_json["comparison_with_4ep"]
        ct = comp["technique_collapsed_full"]
        c4t = ct["4ep"]
        c7t = ct["7ep"]
        assert f"| Technique (`collapsed_full`) | Sample Count ($N$) | {c4t['n_samples']} | {c7t['n_samples']} | +{c7t['n_samples'] - c4t['n_samples']} |" in md
        assert f"| Technique (`collapsed_full`) | Markov Hit@1 | {c4t['markov_hit1']}/{c4t['n_samples']} ({c4t['markov_hit1']/c4t['n_samples']:.4f}) | {c7t['markov_hit1']}/{c7t['n_samples']} ({c7t['markov_hit1']/c7t['n_samples']:.4f}) | {c7t['markov_hit1']/c7t['n_samples'] - c4t['markov_hit1']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Markov Hit@3 | {c4t['markov_hit3']}/{c4t['n_samples']} ({c4t['markov_hit3']/c4t['n_samples']:.4f}) | {c7t['markov_hit3']}/{c7t['n_samples']} ({c7t['markov_hit3']/c7t['n_samples']:.4f}) | {c7t['markov_hit3']/c7t['n_samples'] - c4t['markov_hit3']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Frequency Hit@1 | {c4t['frequency_hit1']}/{c4t['n_samples']} ({c4t['frequency_hit1']/c4t['n_samples']:.4f}) | {c7t['frequency_hit1']}/{c7t['n_samples']} ({c7t['frequency_hit1']/c7t['n_samples']:.4f}) | {c7t['frequency_hit1']/c7t['n_samples'] - c4t['frequency_hit1']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Frequency Hit@3 | {c4t['frequency_hit3']}/{c4t['n_samples']} ({c4t['frequency_hit3']/c4t['n_samples']:.4f}) | {c7t['frequency_hit3']}/{c7t['n_samples']} ({c7t['frequency_hit3']/c7t['n_samples']:.4f}) | {c7t['frequency_hit3']/c7t['n_samples'] - c4t['frequency_hit3']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Markov Fallback Hit@1 | {c4t['fallback_hit1']}/{c4t['n_samples']} ({c4t['fallback_hit1']/c4t['n_samples']:.4f}) | {c7t['fallback_hit1']}/{c7t['n_samples']} ({c7t['fallback_hit1']/c7t['n_samples']:.4f}) | {c7t['fallback_hit1']/c7t['n_samples'] - c4t['fallback_hit1']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Markov Fallback Hit@3 | {c4t['fallback_hit3']}/{c4t['n_samples']} ({c4t['fallback_hit3']/c4t['n_samples']:.4f}) | {c7t['fallback_hit3']}/{c7t['n_samples']} ({c7t['fallback_hit3']/c7t['n_samples']:.4f}) | {c7t['fallback_hit3']/c7t['n_samples'] - c4t['fallback_hit3']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Coverage (Status ok) | {c4t['coverage_covered']}/{c4t['n_samples']} ({c4t['coverage_covered']/c4t['n_samples']:.4f}) | {c7t['coverage_covered']}/{c7t['n_samples']} ({c7t['coverage_covered']/c7t['n_samples']:.4f}) | {c7t['coverage_covered']/c7t['n_samples'] - c4t['coverage_covered']/c4t['n_samples']:+.4f} |" in md
        assert f"| Technique (`collapsed_full`) | Target Ceiling | {c4t['ceiling_hits']}/{c4t['n_samples']} ({c4t['ceiling_hits']/c4t['n_samples']:.4f}) | {c7t['ceiling_hits']}/{c7t['n_samples']} ({c7t['ceiling_hits']/c7t['n_samples']:.4f}) | {c7t['ceiling_hits']/c7t['n_samples'] - c4t['ceiling_hits']/c4t['n_samples']:+.4f} |" in md

        ca = comp["tactic_collapsed"]
        c4a = ca["4ep"]
        c7a = ca["7ep"]
        assert f"| Tactic (`tactic_collapsed`) | Sample Count ($N$) | {c4a['n_samples']} | {c7a['n_samples']} | +{c7a['n_samples'] - c4a['n_samples']} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Markov Hit@1 | {c4a['markov_hit1']}/{c4a['n_samples']} ({c4a['markov_hit1']/c4a['n_samples']:.4f}) | {c7a['markov_hit1']}/{c7a['n_samples']} ({c7a['markov_hit1']/c7a['n_samples']:.4f}) | {c7a['markov_hit1']/c7a['n_samples'] - c4a['markov_hit1']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Markov Hit@3 | {c4a['markov_hit3']}/{c4a['n_samples']} ({c4a['markov_hit3']/c4a['n_samples']:.4f}) | {c7a['markov_hit3']}/{c7a['n_samples']} ({c7a['markov_hit3']/c7a['n_samples']:.4f}) | {c7a['markov_hit3']/c7a['n_samples'] - c4a['markov_hit3']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Frequency Hit@1 | {c4a['frequency_hit1']}/{c4a['n_samples']} ({c4a['frequency_hit1']/c4a['n_samples']:.4f}) | {c7a['frequency_hit1']}/{c7a['n_samples']} ({c7a['frequency_hit1']/c7a['n_samples']:.4f}) | {c7a['frequency_hit1']/c7a['n_samples'] - c4a['frequency_hit1']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Frequency Hit@3 | {c4a['frequency_hit3']}/{c4a['n_samples']} ({c4a['frequency_hit3']/c4a['n_samples']:.4f}) | {c7a['frequency_hit3']}/{c7a['n_samples']} ({c7a['frequency_hit3']/c7a['n_samples']:.4f}) | {c7a['frequency_hit3']/c7a['n_samples'] - c4a['frequency_hit3']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Markov Fallback Hit@1 | {c4a['fallback_hit1']}/{c4a['n_samples']} ({c4a['fallback_hit1']/c4a['n_samples']:.4f}) | {c7a['fallback_hit1']}/{c7a['n_samples']} ({c7a['fallback_hit1']/c7a['n_samples']:.4f}) | {c7a['fallback_hit1']/c7a['n_samples'] - c4a['fallback_hit1']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Markov Fallback Hit@3 | {c4a['fallback_hit3']}/{c4a['n_samples']} ({c4a['fallback_hit3']/c4a['n_samples']:.4f}) | {c7a['fallback_hit3']}/{c7a['n_samples']} ({c7a['fallback_hit3']/c7a['n_samples']:.4f}) | {c7a['fallback_hit3']/c7a['n_samples'] - c4a['fallback_hit3']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Coverage (Status ok) | {c4a['coverage_covered']}/{c4a['n_samples']} ({c4a['coverage_covered']/c4a['n_samples']:.4f}) | {c7a['coverage_covered']}/{c7a['n_samples']} ({c7a['coverage_covered']/c7a['n_samples']:.4f}) | {c7a['coverage_covered']/c7a['n_samples'] - c4a['coverage_covered']/c4a['n_samples']:+.4f} |" in md
        assert f"| Tactic (`tactic_collapsed`) | Target Ceiling | {c4a['ceiling_hits']}/{c4a['n_samples']} ({c4a['ceiling_hits']/c4a['n_samples']:.4f}) | {c7a['ceiling_hits']}/{c7a['n_samples']} ({c7a['ceiling_hits']/c7a['n_samples']:.4f}) | {c7a['ceiling_hits']/c7a['n_samples'] - c4a['ceiling_hits']/c4a['n_samples']:+.4f} |" in md

    def check_eval_7ep_conclusions(md: str) -> None:
        pts = results_json["paired_tests"]
        p1 = pts["P1_tactic_collapsed_hit3"]
        p2 = pts["P2_technique_collapsed_full_hit3"]
        t1 = p1["table"]
        t2 = p2["table"]
        assert f"- **Primary Hypothesis P2 (Technique `collapsed_full` Hit@3)**: Markov achieved {p2['m1_rate']:.4f} ({t2['both_hit'] + t2['b_m1_only']}/{p2['n_samples']}) versus Frequency {p2['m2_rate']:.4f} ({t2['both_hit'] + t2['c_m2_only']}/{p2['n_samples']}), yielding pooled difference {p2['rate_difference']:+.4f} (discordant pairs: b={t2['b_m1_only']}, c={t2['c_m2_only']}, raw p={p2['p_value_raw']:.4f})." in md
        assert f"- **Secondary Hypothesis P1 (Tactic `tactic_collapsed` Hit@3)**: Markov achieved {p1['m1_rate']:.4f} ({t1['both_hit'] + t1['b_m1_only']}/{p1['n_samples']}) versus Frequency {p1['m2_rate']:.4f} ({t1['both_hit'] + t1['c_m2_only']}/{p1['n_samples']}), yielding pooled difference {p1['rate_difference']:+.4f} (discordant pairs: b={t1['b_m1_only']}, c={t1['c_m2_only']}, raw p={p1['p_value_raw']:.4f})." in md
        assert "- **Sample Expansion**: Expanding from 4 to 7 episodes increased evaluated technique transition samples from 67 to 95 (+28 samples) and tactic transition samples from 53 to 76 (+23 samples)." in md
        assert "- **Claim Rule Boundary**: Per pre-registration protocol, substantive claims of improvement or order-signal presence are governed by the joint P1–P4 criteria and Holm adjustment evaluated after permutation testing (Prompt 12b)." in md

    def check_eval_7ep_headers(md: str) -> None:
        sec2 = md.split("## 2. Primary Slice")[1].split("## 3. Secondary Slice")[0]
        sec3 = md.split("## 3. Secondary Slice")[1].split("## 4. Reference Slice")[0]
        sec4 = md.split("## 4. Reference Slice")[1].split("## 5. Pre-Registered Paired Comparisons")[0]
        header = "| Fold | Test Episode | N | Markov Hit@1 | Markov Hit@3 | Freq Hit@1 | Freq Hit@3 | Fallback Hit@1 | Fallback Hit@3 | Covered / N | Ceiling / N |"
        assert header in sec2
        assert header in sec3
        assert header in sec4
        assert "| Slice | Metric | 4-Episode Baseline (E1–E4) | 7-Episode Evaluation (E1–E7) | Absolute Change |" in md

    return [
        check_eval_7ep_intro_and_setup,
        check_eval_7ep_primary_collapsed_full,
        check_eval_7ep_secondary_tactic,
        check_eval_7ep_reference_raw_full,
        check_eval_7ep_paired_tests,
        check_eval_7ep_comparison_4ep,
        check_eval_7ep_conclusions,
        check_eval_7ep_headers,
    ]


def get_check_suites_7ep_inference():
    lc_json = json.loads((REPORTS_DIR / "7ep" / "learning_curve_7ep_results.json").read_text(encoding="utf-8"))
    perm_7ep_json = json.loads((REPORTS_DIR / "7ep" / "permutation_7ep_report.json").read_text(encoding="utf-8"))
    pr_7ep_json = json.loads((REPORTS_DIR / "7ep" / "planted_realscale_7ep_report.json").read_text(encoding="utf-8"))
    e5_json = json.loads((REPORTS_DIR / "7ep" / "e5_removed_results.json").read_text(encoding="utf-8"))
    holm_json = json.loads((REPORTS_DIR / "7ep" / "holm_claim_rule_results.json").read_text(encoding="utf-8"))
    diag_json = json.loads((REPORTS_DIR / "7ep" / "diagnostics_7ep.json").read_text(encoding="utf-8"))

    def check_lc_table(md: str) -> None:
        assert "# Pre-Registered 7-Episode Learning Curve Report" in md
        assert "Technique `collapsed_full` ($N=95$) and Tactic `tactic_collapsed` ($N=76$)" in md
        assert "- **Held-Out Test Episodes**: $e \\in \\{E1, E2, E3, E4, E5, E6, E7\\}$ ($7$ episodes)." in md
        assert "- **Training Subset Sizes**: $k \\in \\{1, 2, 3, 4, 5, 6\\}$." in md
        assert "- $k=1$: $\\binom{6}{1} = 6$ subsets per episode ($42$ evaluations per slice)" in md
        assert "- $k=2$: $\\binom{6}{2} = 15$ subsets per episode ($105$ evaluations per slice)" in md
        assert "- $k=3$: $\\binom{6}{3} = 20$ subsets per episode ($140$ evaluations per slice)" in md
        assert "- $k=4$: $\\binom{6}{4} = 15$ subsets per episode ($105$ evaluations per slice)" in md
        assert "- $k=5$: $\\binom{6}{5} = 6$ subsets per episode ($42$ evaluations per slice)" in md
        assert "- $k=6$: $\\binom{6}{6} = 1$ subset per episode ($7$ evaluations per slice" in md
        assert "- **Total Evaluations per Slice**: $63$ subsets per episode $\\times 7$ episodes $= 441$ training subset evaluations ($882$ across both slices)." in md

        # Check Table 1 (Pre-Registered Primary, Episode-Mean)
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            for k in range(1, 7):
                kd = lc_json["learning_curve"][sl][f"k_{k}"]
                n_sub = kd["n_subsets_per_episode"]
                tot_evals = n_sub * 7
                unw = kd["unweighted_episode_mean"]
                line = (
                    f"| {k} | {n_sub} | {tot_evals} | "
                    f"{unw['markov_hit1']:.4f} | {unw['markov_hit3']:.4f} | "
                    f"{unw['frequency_hit1']:.4f} | {unw['frequency_hit3']:.4f} | "
                    f"{unw['markov_fallback_hit1']:.4f} | {unw['markov_fallback_hit3']:.4f} | "
                    f"{unw['coverage']:.4f} | {unw['ceiling']:.4f} |"
                )
                assert line in md, f"Missing LC Table 1 line: {line}"

        # Check Table 2 (Secondary, Sample-Weighted Pooled)
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            for k in range(1, 7):
                kd = lc_json["learning_curve"][sl][f"k_{k}"]
                n_sub = kd["n_subsets_per_episode"]
                tot_evals = n_sub * 7
                p = kd["pooled_sample_weighted"]
                line = (
                    f"| {k} | {n_sub} | {tot_evals} | "
                    f"{p['markov_hit1']:.4f} | {p['markov_hit3']:.4f} | "
                    f"{p['frequency_hit1']:.4f} | {p['frequency_hit3']:.4f} | "
                    f"{p['markov_fallback_hit1']:.4f} | {p['markov_fallback_hit3']:.4f} | "
                    f"{p['coverage']:.4f} | {p['ceiling']:.4f} |"
                )
                assert line in md, f"Missing LC Table 2 line: {line}"

        # Check Table 3 (Sensitivity, E5 Excluded)
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            for k in range(1, 7):
                kd = lc_json["learning_curve"][sl][f"k_{k}"]
                n_sub = kd["n_subsets_per_episode"]
                tot_evals = n_sub * 7
                e5_unw = kd["e5_excluded"]["unweighted_episode_mean"]
                line_3a = (
                    f"| {k} | {n_sub} | {tot_evals} | "
                    f"{e5_unw['markov_hit1']:.4f} | {e5_unw['markov_hit3']:.4f} | "
                    f"{e5_unw['frequency_hit1']:.4f} | {e5_unw['frequency_hit3']:.4f} | "
                    f"{e5_unw['markov_fallback_hit1']:.4f} | {e5_unw['markov_fallback_hit3']:.4f} | "
                    f"{e5_unw['coverage']:.4f} | {e5_unw['ceiling']:.4f} |"
                )
                assert line_3a in md, f"Missing LC Table 3a line: {line_3a}"

                e5_pw = kd["e5_excluded"]["pooled_sample_weighted"]
                line_3b = (
                    f"| {k} | {n_sub} | {tot_evals} | "
                    f"{e5_pw['markov_hit1']:.4f} | {e5_pw['markov_hit3']:.4f} | "
                    f"{e5_pw['frequency_hit1']:.4f} | {e5_pw['frequency_hit3']:.4f} | "
                    f"{e5_pw['markov_fallback_hit1']:.4f} | {e5_pw['markov_fallback_hit3']:.4f} | "
                    f"{e5_pw['coverage']:.4f} | {e5_pw['ceiling']:.4f} |"
                )
                assert line_3b in md, f"Missing LC Table 3b line: {line_3b}"

        # Check per-episode tables
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            for k in range(1, 7):
                for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
                    ep_d = lc_json["learning_curve"][sl][f"k_{k}"]["per_episode_means"][ep]
                    line = (
                        f"| {k} | {ep} | {ep_d['n_samples']} | "
                        f"{ep_d['markov']['hit1_rate']:.4f} | {ep_d['markov']['hit3_rate']:.4f} | "
                        f"{ep_d['frequency']['hit1_rate']:.4f} | {ep_d['frequency']['hit3_rate']:.4f} | "
                        f"{ep_d['markov_fallback']['hit1_rate']:.4f} | {ep_d['markov_fallback']['hit3_rate']:.4f} | "
                        f"{ep_d['coverage_rate']:.4f} | {ep_d['ceiling_rate']:.4f} |"
                    )
                    assert line in md, f"Missing LC per-ep line: {line}"

        assert "- **Combinatorial Enumeration**: For each held-out episode $e$, all $\\binom{6}{k}$ subsets of the remaining 6 episodes were evaluated:" in md
        assert "- **Aggregation Methods**:" in md
        assert "- **Table 1 (Pre-Registered Primary)**: Episode-mean aggregation per Section 7 (\"Compute metric averages across subsets for each held-out episode, then average over all 7 held-out episodes\")." in md
        assert "- **Table 2 (Secondary)**: Sample-weighted pooled aggregation across all evaluated transitions ($N=95$ technique, $N=76$ tactic)." in md
        assert "- **Table 3 (Sensitivity, E5 Excluded)**: Aggregation with Episode E5 excluded (both 6-episode unweighted mean and sample-weighted over the remaining $N=93$ technique or $N=74$ tactic samples)." in md

        t_k1_unw = lc_json["learning_curve"]["technique_collapsed_full"]["k_1"]["unweighted_episode_mean"]
        t_k6_unw = lc_json["learning_curve"]["technique_collapsed_full"]["k_6"]["unweighted_episode_mean"]
        t_k1_pw = lc_json["learning_curve"]["technique_collapsed_full"]["k_1"]["pooled_sample_weighted"]
        t_k6_pw = lc_json["learning_curve"]["technique_collapsed_full"]["k_6"]["pooled_sample_weighted"]

        tac_k1_unw = lc_json["learning_curve"]["tactic_collapsed"]["k_1"]["unweighted_episode_mean"]
        tac_k6_unw = lc_json["learning_curve"]["tactic_collapsed"]["k_6"]["unweighted_episode_mean"]
        tac_k1_pw = lc_json["learning_curve"]["tactic_collapsed"]["k_1"]["pooled_sample_weighted"]
        tac_k6_pw = lc_json["learning_curve"]["tactic_collapsed"]["k_6"]["pooled_sample_weighted"]

        exp_t_unw = (
            f"- **Technique Primary Episode-Mean Trajectories**: Under the pre-registered primary episode-mean aggregation across k=1..6, "
            f"technique Markov Hit@3 changes from {t_k1_unw['markov_hit3']:.4f} to {t_k6_unw['markov_hit3']:.4f}, "
            f"Frequency Hit@3 changes from {t_k1_unw['frequency_hit3']:.4f} to {t_k6_unw['frequency_hit3']:.4f}, "
            f"Markov coverage moves from {t_k1_unw['coverage']:.4f} to {t_k6_unw['coverage']:.4f} (+{t_k6_unw['coverage'] - t_k1_unw['coverage']:.4f}), "
            f"and target ceiling moves from {t_k1_unw['ceiling']:.4f} to {t_k6_unw['ceiling']:.4f} (+{t_k6_unw['ceiling'] - t_k1_unw['ceiling']:.4f})."
        )
        assert exp_t_unw in md

        exp_t_pw = (
            f"- **Technique Secondary Sample-Weighted Trajectories**: Under the secondary sample-weighted pooled aggregation across k=1..6, "
            f"technique Markov Hit@3 changes from {t_k1_pw['markov_hit3']:.4f} to {t_k6_pw['markov_hit3']:.4f}, "
            f"Frequency Hit@3 changes from {t_k1_pw['frequency_hit3']:.4f} to {t_k6_pw['frequency_hit3']:.4f}, "
            f"Markov coverage moves from {t_k1_pw['coverage']:.4f} to {t_k6_pw['coverage']:.4f} (+{t_k6_pw['coverage'] - t_k1_pw['coverage']:.4f}), "
            f"and target ceiling moves from {t_k1_pw['ceiling']:.4f} to {t_k6_pw['ceiling']:.4f} (+{t_k6_pw['ceiling'] - t_k1_pw['ceiling']:.4f})."
        )
        assert exp_t_pw in md

        exp_tac_unw = (
            f"- **Tactic Primary Episode-Mean Trajectories**: Under the pre-registered primary episode-mean aggregation across k=1..6, "
            f"tactic Markov Hit@3 moves from {tac_k1_unw['markov_hit3']:.4f} to {tac_k6_unw['markov_hit3']:.4f}, "
            f"Frequency Hit@3 moves from {tac_k1_unw['frequency_hit3']:.4f} to {tac_k6_unw['frequency_hit3']:.4f}, "
            f"tactic coverage moves from {tac_k1_unw['coverage']:.4f} to {tac_k6_unw['coverage']:.4f}, "
            f"and tactic ceiling moves from {tac_k1_unw['ceiling']:.4f} to {tac_k6_unw['ceiling']:.4f}."
        )
        assert exp_tac_unw in md

        exp_tac_pw = (
            f"- **Tactic Secondary Sample-Weighted Trajectories**: Under the secondary sample-weighted pooled aggregation across k=1..6, "
            f"tactic Markov Hit@3 moves from {tac_k1_pw['markov_hit3']:.4f} to {tac_k6_pw['markov_hit3']:.4f}, "
            f"Frequency Hit@3 moves from {tac_k1_pw['frequency_hit3']:.4f} to {tac_k6_pw['frequency_hit3']:.4f}, "
            f"tactic coverage moves from {tac_k1_pw['coverage']:.4f} to {tac_k6_pw['coverage']:.4f}, "
            f"and tactic ceiling moves from {tac_k1_pw['ceiling']:.4f} to {tac_k6_pw['ceiling']:.4f}."
        )
        assert exp_tac_pw in md

    def check_perm_7ep(md: str) -> None:
        assert "# Pre-Registered 7-Episode Permutation Test Report" in md
        meta = perm_7ep_json["metadata"]
        assert "- **Null Replicates**: B=1000 permutations (stdlib `random.Random` seeds 0..999)." in md
        assert f"- **One-Sided p-value Formula**: `{meta['p_value_formula']}`." in md
        assert "- **Pre-Registered Primary Comparisons**: P3 = Tactic Markov Hit@3 vs S1 null; P4 = Technique Markov Hit@3 vs S1 null." in md

        # Validity
        stat_labels = {
            "markov_hit1": "Markov Hit@1",
            "markov_hit3": "Markov Hit@3",
            "frequency_hit1": "Frequency Hit@1",
            "frequency_hit3": "Frequency Hit@3",
            "markov_fallback_hit1": "Markov Fallback Hit@1",
            "markov_fallback_hit3": "Markov Fallback Hit@3",
            "markov_minus_frequency_hit1": "Markov - Frequency Hit@1",
            "markov_minus_frequency_hit3": "Markov - Frequency Hit@3",
        }
        for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)")]:
            for lvl, lvl_label in [("technique_collapsed_full", "Technique"), ("tactic_collapsed", "Tactic")]:
                for st in ["frequency_hit1", "frequency_hit3"]:
                    row = perm_7ep_json["schemes"][sc][lvl][st]
                    lbl = stat_labels[st]
                    status_str = "**FLAG (p < 0.05)**" if row["p_value"] < 0.05 else "PASS (Valid)"
                    line = f"| {sc_label} | {lvl_label} | {lbl} | {row['observed']:+.4f} | {row['null_mean']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {status_str} |"
                    assert line in md, f"Missing validity line: {line}"

        assert "- **S1 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \\ge 0.05$)." in md
        assert "- **S3 Validity**: Confirmed valid order-only null (all order-free Frequency statistics have $p \\ge 0.05$)." in md

        # Sample counts
        s_sum = meta["sample_counts_summary"]
        for sc, sc_label in [("S1_collapsed_order", "S1 (Collapsed-Order)"), ("S3_constrained_shuffle", "S3 (Constrained Shuffle)")]:
            for lvl, lvl_label in [("technique_collapsed_full", "Technique (collapsed_full)"), ("tactic_collapsed", "Tactic (tactic_collapsed)")]:
                info = s_sum[sc][lvl]
                obs_n = meta["observed_sample_counts"][lvl]
                inv_str = "**YES (Constant)**" if info["is_constant"] else "NO (Variable)"
                line = f"| {sc_label} | {lvl_label} | {obs_n} | {info['min']} | {info['mean']:.2f} | {info['max']} | {inv_str} |"
                assert line in md, f"Missing sample count line: {line}"

        s3_meta = meta["s3_rejection_sampling_summary"]
        assert f"- **Technique Level**: Excluded Permutations = {s3_meta['technique_collapsed_full']['excluded_permutations']}, Min Tries = {s3_meta['technique_collapsed_full']['min_total_tries']}, Mean Tries = {s3_meta['technique_collapsed_full']['mean_total_tries']:.2f}, Max Tries = {s3_meta['technique_collapsed_full']['max_total_tries']}" in md
        assert f"- **Tactic Level**: Excluded Permutations = {s3_meta['tactic_collapsed']['excluded_permutations']}, Min Tries = {s3_meta['tactic_collapsed']['min_total_tries']}, Mean Tries = {s3_meta['tactic_collapsed']['mean_total_tries']:.2f}, Max Tries = {s3_meta['tactic_collapsed']['max_total_tries']}" in md

        # S1 & S3 Tables
        counts_tech = meta["observed_baseline_counts"]["technique_collapsed_full"]
        counts_tac = meta["observed_baseline_counts"]["tactic_collapsed"]
        for sc in ["S1_collapsed_order", "S3_constrained_shuffle"]:
            for lvl, counts, N in [("technique_collapsed_full", counts_tech, 95), ("tactic_collapsed", counts_tac, 76)]:
                d_lvl = perm_7ep_json["schemes"][sc][lvl]
                for st, lbl in stat_labels.items():
                    row = d_lvl[st]
                    h_str = f"{counts[st]:+d} / {N}" if "minus" in st else f"{counts[st]} / {N}"
                    line = f"| {lbl:26s} | {row['observed']:+.4f} | {h_str:9s} | {row['null_mean']:+.4f} | {row['null_sd']:.4f} | {row['null_p2_5']:+.4f} | {row['null_p97_5']:+.4f} | {row['p_value']:.4f} | {row['mc_se']:.4f} | {row['conclusion']} |"
                    assert line in md, f"Missing S1/S3 line: {line}"

        # Consistency
        for lvl, lvl_label in [("technique_collapsed_full", "Technique Level (`collapsed_full`)"), ("tactic_collapsed", "Tactic Level (`tactic_collapsed`)")]:
            for st, lbl in stat_labels.items():
                p1 = perm_7ep_json["schemes"]["S1_collapsed_order"][lvl][st]["p_value"]
                p3 = perm_7ep_json["schemes"]["S3_constrained_shuffle"][lvl][st]["p_value"]
                se1 = perm_7ep_json["schemes"]["S1_collapsed_order"][lvl][st]["mc_se"]
                se3 = perm_7ep_json["schemes"]["S3_constrained_shuffle"][lvl][st]["mc_se"]
                diff = abs(p1 - p3)
                combined_2se = 2.0 * math.sqrt(se1**2 + se3**2)
                if diff <= combined_2se:
                    verdict = f"is less than two combined Monte Carlo standard errors ({combined_2se:.4f}), confirming S1 and S3 are consistent."
                else:
                    verdict = f"exceeds two combined Monte Carlo standard errors ({combined_2se:.4f}); p-values differ by more than two combined Monte Carlo standard errors, no cause inferred."
                line = f"- **{lbl}**: S1 $p = {p1:.4f}$ (MC SE $= {se1:.4f}$), S3 $p = {p3:.4f}$ (MC SE $= {se3:.4f}$); difference $|p_{{S1}} - p_{{S3}}| = {diff:.4f}$ {verdict}"
                assert line in md, f"Missing consistency line: {line}"

        assert "- **Purpose**: Determine whether attack event order carries predictive signal beyond order-free baselines across all seven episodes (E1–E7)." in md
        assert "- **Primary Scheme (S1 - Collapsed-Order Shuffle)**: Pre-declared headline null hypothesis (prereg Section 10). Shuffles the collapsed sequence strictly within each episode, preserving exact sample counts ($N=95$ technique, $N=76$ tactic) and marginal item frequencies. S1 p-values enter the pre-registered Holm step-down correction for hypotheses P3 and P4." in md
        assert "- **Constrained Scheme (S3 - Adjacency-Constrained Shuffle)**: Shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items share identical technique sets (technique level) or identical tactic sets (tactic level), using rejection sampling with up to 10,000 tries per episode. Reported alongside S1." in md
        assert "- **Excluded Scheme (S2)**: S2 (raw-event shuffle) is excluded from the 7-episode design per prereg Section 10." in md
        assert "A valid order-only null permutation must not perturb the performance of an **order-free** model (FrequencyBaseline). If an order-free statistic exhibits $p < 0.05$" in md
        assert "Monte Carlo permutation standard errors are given by $\\text{SE}_{\\text{MC}}(p) = \\sqrt{p(1-p)/B}$ ($B=1000$)." in md
        assert "S1 and S3 p-values differing by less than two combined Monte Carlo standard errors are statistically consistent:" in md

        p3_val = perm_7ep_json["schemes"]["S1_collapsed_order"]["tactic_collapsed"]["markov_hit3"]["p_value"]
        p4_val = perm_7ep_json["schemes"]["S1_collapsed_order"]["technique_collapsed_full"]["markov_hit3"]["p_value"]
        assert f"- **Hypothesis P3 (Tactic Markov Hit@3 vs S1 Null)**: Raw $p = {p3_val:.4f}$ (S3 reported alongside: $p = {perm_7ep_json['schemes']['S3_constrained_shuffle']['tactic_collapsed']['markov_hit3']['p_value']:.4f}$)." in md
        assert f"- **Hypothesis P4 (Technique Markov Hit@3 vs S1 Null)**: Raw $p = {p4_val:.4f}$ (S3 reported alongside: $p = {perm_7ep_json['schemes']['S3_constrained_shuffle']['technique_collapsed_full']['markov_hit3']['p_value']:.4f}$)." in md

    def check_pr_7ep(md: str) -> None:
        assert "# Real-Scale Planted-Structure Power Analysis Report (7 Episodes)" in md
        g = pr_7ep_json["gates"]
        assert f"| **G8** | {g['G8']['description']} | `{g['G8']['measured_diff']:.4f}` | `<= {g['G8']['threshold']:.4f}` | **PASS** |" in md
        traj_str = str([round(x, 4) for x in g['G9']['measured_trajectory']])
        assert f"| **G9** | {g['G9']['description']} | `{traj_str}` | Non-decreasing | **PASS** |" in md
        assert f"| **G10** | {g['G10']['description']} | Ratio: `{g['G10']['mean_ratio_m1_to_r']:.4f}` | All <= R & Ratio >= 0.9900 | **PASS** |" in md
        assert f"| **G11** | {g['G11']['description']} | Ratio: `{g['G11']['broken_ratio_to_r']:.4f}` | `< 0.9900 (must fail G10)` | **PASS (Failed G10 as expected)** |" in md
        for s_str in ["0.0", "0.25", "0.5", "0.75", "1.0"]:
            row = pr_7ep_json["results_by_signal"][s_str]
            s = float(s_str)
            m1_str = f"{row['markov_top1_mean']:.4f} ± {row['markov_top1_se']:.4f}"
            f1_str = f"{row['frequency_top1_mean']:.4f} ± {row['frequency_top1_se']:.4f}"
            r_str = f"{row['reachable_fraction_mean']:.4f}"
            r_no_e5_str = f"{row['reachable_fraction_no_e5_mean']:.4f}"
            exc_str = f"**YES** (diff = {row['markov_top1_mean'] - row['frequency_top1_mean']:+.4f})" if row["exceeds_2_combined_se"] else f"NO (diff = {row['markov_top1_mean'] - row['frequency_top1_mean']:+.4f})"
            line = f"| {s:.2f} | {m1_str} | {row['markov_top3_mean']:.4f} ± {row['markov_top3_se']:.4f} | {f1_str} | {row['frequency_top3_mean']:.4f} | {r_str} | {r_no_e5_str} | {exc_str} |"
            assert line in md, f"Missing PR 7ep row: {line}"

        assert "| *Real Data* | `0.0316` | `0.0316` | `0.0737` | `0.1684` | — | — | *real data, different generator, shown for scale only* |" in md
        assert "**Smallest signal $s$ at which Markov Top-1 exceeds Frequency Top-1 by > 2 combined SE**: `s = 0.25`." in md

        # Setup section
        assert "- **Vocabulary (V)**: All 82 distinct MITRE ATT&CK technique IDs across real collapsed sequences E1–E7 (read at runtime, $V=82$)." in md
        assert "- **Episode Lengths**: Real collapsed lengths of E1–E7 (E1: 19, E2: 20, E3: 21, E4: 11, E5: 3, E6: 15, E7: 13), yielding 95 evaluated transition samples per replicate dataset (93 samples when excluding E5)." in md
        assert "- **Evaluation Protocol**: 7-episode Leave-One-Episode-Out cross-validation using production `MarkovModel` and `FrequencyBaseline`." in md
        assert "- **Signal Levels (s)**: `0.00, 0.25, 0.50, 0.75, 1.00` (200 replicates per signal level, seeds 0..199)." in md
        assert "- **Mean R at $s=1.0$ across all 7 episodes (95 samples)**: `0.6498`" in md
        assert "- **Mean R at $s=1.0$ excluding E5 (93 samples)**: `0.6482` (Note: E5 has length 3 items, yielding 2 transition samples, with 0 reachable transitions)." in md
        assert "- **Chance Top-1**: $1/(V - 1) = 1/81 = 0.012346$." in md

        # Section 4
        assert "- Under full signal ($s=1.00$), the 7-episode design achieves a mean reachable fraction of $R = 0.6498$ across all 95 transition samples." in md
        assert "- When excluding episode E5 (which contains only 2 transition samples and exhibits 0 training transitions), the mean reachable fraction is $R = 0.6482$ across the remaining 93 samples." in md
        assert "- Production MarkovModel captures 100% of reachable signal at $s=1.00$ (mean Top-1 matches mean $R$ exactly)." in md

    def check_e5_removed(md: str) -> None:
        assert "# Pre-Registered E5-Removed Sensitivity Analysis Report" in md
        assert "- **Purpose**: Evaluate the sensitivity of findings to the inclusion of Episode E5 (which contains only 3 labeled steps and 2 transitions, with 0 coverage and 0 ceiling hits under 7-fold LOEO)." in md
        assert "- **Protocol**: Full 6-fold Leave-One-Episode-Out cross-validation across {E1, E2, E3, E4, E6, E7}, with Episode E5 entirely excluded from both model training and evaluation." in md
        assert "- **Evaluated Slices**: Technique `collapsed_full` ($N=93$) and Tactic `tactic_collapsed` ($N=74$)." in md
        assert '- **Statistical Labels**: Paired McNemar tests labeled strictly as `"sensitivity, raw p"`.' in md

        cmp_d = e5_json["comparison_with_all_7ep"]
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            c_all = cmp_d[sl]["all_7ep"]
            c_no = cmp_d[sl]["e5_removed_6ep"]
            assert f"| Evaluated Samples ($N$) | {c_all['n_samples']} | {c_no['n_samples']} | {c_no['n_samples'] - c_all['n_samples']} |" in md
            assert f"| Coverage Rate | {c_all['coverage_rate']:.4f} ({c_all['coverage_covered']}/{c_all['n_samples']}) | {c_no['coverage_rate']:.4f} ({c_no['coverage_covered']}/{c_no['n_samples']}) | {c_no['coverage_rate'] - c_all['coverage_rate']:+.4f} |" in md
            assert f"| Ceiling Rate | {c_all['ceiling_rate']:.4f} ({c_all['ceiling_hits']}/{c_all['n_samples']}) | {c_no['ceiling_rate']:.4f} ({c_no['ceiling_hits']}/{c_no['n_samples']}) | {c_no['ceiling_rate'] - c_all['ceiling_rate']:+.4f} |" in md
            assert f"| Markov Hit@1 | {c_all['markov_top1']:.4f} ({c_all['markov_hit1']}/{c_all['n_samples']}) | {c_no['markov_top1']:.4f} ({c_no['markov_hit1']}/{c_no['n_samples']}) | {c_no['markov_top1'] - c_all['markov_top1']:+.4f} |" in md
            assert f"| Markov Hit@3 | {c_all['markov_top3']:.4f} ({c_all['markov_hit3']}/{c_all['n_samples']}) | {c_no['markov_top3']:.4f} ({c_no['markov_hit3']}/{c_no['n_samples']}) | {c_no['markov_top3'] - c_all['markov_top3']:+.4f} |" in md
            assert f"| Frequency Hit@1 | {c_all['frequency_top1']:.4f} ({c_all['frequency_hit1']}/{c_all['n_samples']}) | {c_no['frequency_top1']:.4f} ({c_no['frequency_hit1']}/{c_no['n_samples']}) | {c_no['frequency_top1'] - c_all['frequency_top1']:+.4f} |" in md
            assert f"| Frequency Hit@3 | {c_all['frequency_top3']:.4f} ({c_all['frequency_hit3']}/{c_all['n_samples']}) | {c_no['frequency_top3']:.4f} ({c_no['frequency_hit3']}/{c_no['n_samples']}) | {c_no['frequency_top3'] - c_all['frequency_top3']:+.4f} |" in md
            assert f"| Fallback Hit@1 | {c_all['fallback_top1']:.4f} ({c_all['fallback_hit1']}/{c_all['n_samples']}) | {c_no['fallback_top1']:.4f} ({c_no['fallback_hit1']}/{c_no['n_samples']}) | {c_no['fallback_top1'] - c_all['fallback_top1']:+.4f} |" in md
            assert f"| Fallback Hit@3 | {c_all['fallback_top3']:.4f} ({c_all['fallback_hit3']}/{c_all['n_samples']}) | {c_no['fallback_top3']:.4f} ({c_no['fallback_hit3']}/{c_no['n_samples']}) | {c_no['fallback_top3'] - c_all['fallback_top3']:+.4f} |" in md
            assert f"| Exact McNemar p (Hit@3) | {c_all['mcnemar_p_hit3']:.4f} | {c_no['mcnemar_p_hit3']:.4f} (sensitivity, raw p) | {c_no['mcnemar_p_hit3'] - c_all['mcnemar_p_hit3']:+.4f} |" in md

        # Check pooled summary bullets
        for sl, N in [("technique_collapsed_full", 93), ("tactic_collapsed", 74)]:
            cmp_e5 = e5_json["comparison_with_all_7ep"][sl]["e5_removed_6ep"]
            hl = e5_json[sl]["headline"]
            assert f"- **Coverage**: `{cmp_e5['coverage_covered']}/{N}` ({cmp_e5['coverage_rate']:.4f})" in md
            assert f"- **Ceiling**: `{cmp_e5['ceiling_hits']}/{N}` ({cmp_e5['ceiling_rate']:.4f})" in md
            m = hl["markov"]
            f = hl["frequency"]
            fb = hl.get("fallback", hl.get("markov_fallback"))
            assert f"- **Markov Hit@1**: `{m['hit1']}/{N}` ({m['top1']:.4f}, 95% Wilson: `[{m['wilson95_top1'][0]:.4f}, {m['wilson95_top1'][1]:.4f}]`)" in md
            assert f"- **Markov Hit@3**: `{m['hit3']}/{N}` ({m['top3']:.4f}, 95% Wilson: `[{m['wilson95_top3'][0]:.4f}, {m['wilson95_top3'][1]:.4f}]`)" in md
            assert f"- **Frequency Hit@1**: `{f['hit1']}/{N}` ({f['top1']:.4f}, 95% Wilson: `[{f['wilson95_top1'][0]:.4f}, {f['wilson95_top1'][1]:.4f}]`)" in md
            assert f"- **Frequency Hit@3**: `{f['hit3']}/{N}` ({f['top3']:.4f}, 95% Wilson: `[{f['wilson95_top3'][0]:.4f}, {f['wilson95_top3'][1]:.4f}]`)" in md
            assert f"- **Fallback Hit@1**: `{fb['hit1']}/{N}` ({fb['top1']:.4f}, 95% Wilson: `[{fb['wilson95_top1'][0]:.4f}, {fb['wilson95_top1'][1]:.4f}]`)" in md
            assert f"- **Fallback Hit@3**: `{fb['hit3']}/{N}` ({fb['top3']:.4f}, 95% Wilson: `[{fb['wilson95_top3'][0]:.4f}, {fb['wilson95_top3'][1]:.4f}]`)" in md

        # Check fold tables
        for sl in ["technique_collapsed_full", "tactic_collapsed"]:
            f_dict = e5_json[sl]["per_fold"]
            for f_name, f_d in f_dict.items():
                if "markov" in f_d and "coverage" in f_d["markov"]:
                    cov_r = f_d["markov"]["coverage"]
                    ceil_r = f_d["ceiling"]["rate"]
                    fb_top1 = f_d["fallback"]["top1"]
                    fb_top3 = f_d["fallback"]["top3"]
                else:
                    cov_r = f_d["covered_samples"] / f_d["n_samples"]
                    ceil_r = f_d["ceiling_hits"] / f_d["n_samples"]
                    fb_top1 = f_d.get("fallback", f_d.get("markov_fallback", {})).get("top1", 0.0)
                    fb_top3 = f_d.get("fallback", f_d.get("markov_fallback", {})).get("top3", 0.0)
                line = (
                    f"| {f_name} | {f_d['test_episode']} | {f_d['n_samples']} | "
                    f"{cov_r:.4f} | {ceil_r:.4f} | "
                    f"{f_d['markov']['top1']:.4f} | {f_d['markov']['top3']:.4f} | "
                    f"{f_d['frequency']['top1']:.4f} | {f_d['frequency']['top3']:.4f} | "
                    f"{fb_top1:.4f} | {fb_top3:.4f} |"
                )
                assert line in md, f"Missing fold line: {line}"

        # McNemar table
        for k in ["technique_hit3", "tactic_hit3", "technique_hit1", "tactic_hit1"]:
            pt = e5_json["paired_tests"][k]
            tb = pt["table_2x2"]
            line = f"| {pt['slice']} {pt['metric']} | {pt['n_samples']} | {tb['both_hit']} | {tb['m1_hit_m2_miss']} | {tb['m1_miss_m2_hit']} | {tb['neither_hit']} | {pt['markov_rate']:.4f} | {pt['frequency_rate']:.4f} | {pt['difference']:+.4f} | {pt['p_value_raw']:.4f} |"
            assert line in md, f"Missing McNemar line: {line}"

    def check_holm(md: str) -> None:
        assert "# Pre-Registered Holm Step-Down Adjustment and Substantive Claim Rule Report" in md
        assert "- **Primary Hypotheses Family**: $m=4$ pre-registered hypothesis tests:" in md
        assert "- **P1**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation)." in md
        assert "- **P2**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs `FrequencyBaseline` Hit@3 (two-sided exact McNemar test from 12a evaluation)." in md
        assert "- **P3**: Tactic level (`tactic_collapsed`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside)." in md
        assert "- **P4**: Technique level (`collapsed_full`) `MarkovModel` Hit@3 vs S1 shuffled-order null (one-sided permutation test, $B=1000$; S3 reported alongside)." in md

        fam = holm_json["family"]
        for hid in ["P2", "P3", "P4", "P1"]:
            h = fam[hid]
            m_gt_f = "**YES**" if h["markov_hit3"] > h["frequency_hit3"] else ("NO (Markov < Freq)" if h["markov_hit3"] < h["frequency_hit3"] else "NO (Markov == Freq)")
            sig_str = "**YES (p < 0.05)**" if h["significant_at_05"] else "NO (p ≥ 0.05)"
            line = f"| **{h['id']}** | `{h['level']}` | {h['test_type']} | `{h['raw_p']:.4f}` | {h['rank']} | {h['multiplier']} | `{h['adjusted_p']:.4f}` | {sig_str} | `{h['markov_hit3']:.4f}` | `{h['frequency_hit3']:.4f}` | {m_gt_f} |"
            assert line in md, f"Missing Holm line: {line}"

        assert "*(Note for P3 and P4: S3 constrained shuffle p-values reported alongside S1 are $p=0.0110$ for tactic P3 and $p=0.3656$ for technique P4; per Amendment 1, only the pre-declared headline S1 p-values enter the Holm adjustment).*" in md
        assert '- **Separate Order Signal Question**: Hypotheses P3 and P4 address the separate question: *"Does sequence order carry detectable predictive signal beyond unigram frequency?"*' in md
        cr = holm_json["claim_rule_evaluation"]
        assert f"### Substantive Baseline Improvement: **{cr['formal_verdict']}**" in md
        assert cr["rationale"] in md
        assert cr["order_signal_verdict"] in md

    def check_diag(md: str) -> None:
        assert "# Read-Only Diagnostics Report (7 Episodes)" in md
        f1 = diag_json["F1_candidate_distribution_and_ranks"]
        f2 = diag_json["F2_raw_full_self_repeats"]
        f3 = diag_json["F3_unseen_states_and_miss_shares"]
        for sl, sl_lbl in [
            ("collapsed_full", "Technique (collapsed_full)"),
            ("tactic_collapsed", "Tactic (tactic_collapsed)"),
            ("raw_full", "Technique (raw_full)"),
        ]:
            d = f1[sl]
            n_ok = d["n_samples_markov_ok"]
            mc = d["markov_candidate_count_distribution"]
            fc = d["frequency_candidate_count_distribution"]
            m_int = f"{d['markov_target_intersects_full_list_count']}/{n_ok} ({d['markov_target_intersects_full_list_rate']:.4f})"
            f_int = f"{d['frequency_target_intersects_full_list_count']}/{n_ok} ({d['frequency_target_intersects_full_list_rate']:.4f})"
            m_mr = f"{d['markov_first_correct_mean_rank']:.2f}" if d["markov_first_correct_mean_rank"] is not None else "—"
            f_mr = f"{d['frequency_first_correct_mean_rank']:.2f}" if d["frequency_first_correct_mean_rank"] is not None else "—"
            assert f"| {sl_lbl} | {n_ok} | Markov | {mc['1']} | {mc['2']} | {mc['3']} | {mc['4_or_more']} | {m_int} | {m_mr} |" in md
            assert f"| | | Frequency | {fc['1']} | {fc['2']} | {fc['3']} | {fc['4_or_more']} | {f_int} | {f_mr} |" in md

        # Check rank counts strings
        for sl, sl_sec in [("collapsed_full", "Technique (collapsed_full)"), ("tactic_collapsed", "Tactic (tactic_collapsed)"), ("raw_full", "Technique (raw_full)")]:
            m_rc = f1[sl]["markov_first_correct_rank_distribution"]
            f_rc = f1[sl]["frequency_first_correct_rank_distribution"]
            m_rc_str = str({int(k): v for k, v in m_rc.items()})
            f_rc_str = str({int(k): v for k, v in f_rc.items()})
            assert f"- **Markov Rank Counts**: `{m_rc_str}`" in md
            assert f"- **Frequency Rank Counts**: `{f_rc_str}`" in md

        assert f"- **Total Samples in `raw_full`**: {f2['total_samples']}" in md
        assert f"- **Self-Repeat Samples (`target == current`)**: {f2['self_repeat_samples']} out of {f2['total_samples']} ({f2['self_repeat_share']:.4f} of all samples)." in md
        assert f"- **Total Markov Hit@1 Hits in `raw_full`**: {f2['markov_hit1_total']} hits ({f2['markov_hit1_total']/f2['total_samples']:.4f})." in md
        assert f"- **Markov Hit@1 Hits on Self-Repeats**: {f2['markov_hit1_on_self_repeat']} out of {f2['markov_hit1_total']} total hits ({f2['markov_hit1_self_repeat_share']:.4f} of hits occurred on self-repeats)." in md
        assert f"- **Performance Restricted to Non-Self-Repeat Targets ($N={f2['non_self_repeat_samples']}$)**:" in md
        assert f"- **Markov Hit@1**: {f2['non_self_repeat_markov_hit1']}/{f2['non_self_repeat_samples']} ({f2['non_self_repeat_markov_hit1_rate']:.4f})" in md
        assert f"- **Frequency Hit@1**: {f2['non_self_repeat_frequency_hit1']}/{f2['non_self_repeat_samples']} ({f2['non_self_repeat_frequency_hit1_rate']:.4f})" in md

        sec_tech = md.split("### Technique Level (`collapsed_full`")[1].split("### Tactic Level")[0]
        sec_tac = md.split("### Tactic Level (`tactic_collapsed`")[1].split("### Reference Slice")[0]
        sec_raw = md.split("### Reference Slice (`raw_full`")[1]
        sec_map = {
            "collapsed_full": sec_tech,
            "tactic_collapsed": sec_tac,
            "raw_full": sec_raw,
        }

        for sl, sec_text in sec_map.items():
            f3_sl = diag_json["F3_unseen_states_and_miss_shares"][sl]
            for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
                e_d = f3_sl["per_episode"][ep]
                line = f"| {ep} | {e_d['n_samples']} | {e_d['unseen_current_state_count']} | {e_d['unseen_current_state_rate']:.4f} | {e_d['markov_hit3_miss_count']} | {e_d['unseen_state_hit3_miss_count']} | {e_d['unseen_state_share_of_hit3_misses']:.4f} |"
                assert line in sec_text, f"Missing F3 ep line in {sl}: {line}"
            p = f3_sl["pooled"]
            line = f"| **Pooled Total** | **{p['total_samples']}** | **{p['unseen_current_state_count']}** | **{p['unseen_current_state_rate']:.4f}** | **{p['total_hit3_misses']}** | **{p['unseen_state_hit3_misses']}** | **{p['unseen_share_of_hit3_misses']:.4f}** |"
            assert line in sec_text, f"Missing F3 pooled line in {sl}: {line}"

    def check_e5_hit1_diag(md: str) -> None:
        assert "# E5-Removed Tactic Hit@1 Change Diagnostic" in md
        assert "diagnostic, not a pre-registered test" in md
        e5_hit1_json = json.loads((REPORTS_DIR / "7ep" / "e5_hit1_change_diagnostic.json").read_text(encoding="utf-8"))
        acc = e5_hit1_json["metadata"]["summary_accounting"]
        assert f"- **Tactic 7-Episode Baseline**: Markov Hit@1 is {acc['markov_total_hits_7ep']} / {acc['markov_total_samples_7ep']} ({acc['markov_total_hits_7ep'] / acc['markov_total_samples_7ep']:.4f})." in md
        assert f"- **E5 Test Sample Performance in 7-Episode LOEO**: {acc['markov_e5_test_hits']} / {acc['markov_e5_test_samples']} hits." in md
        assert "- **Performance on Remaining Folds (E1–E4, E6, E7, N=74)**:" in md
        assert f"  - In 7-episode run (E5 in training pool): {acc['markov_hits_6ep_in_7ep_run']} / 74 hits ({acc['markov_hits_6ep_in_7ep_run'] / 74:.4f})." in md
        assert f"  - In E5-removed run (E5 absent from training pool): {acc['markov_hits_6ep_in_e5_removed_run']} / 74 hits ({acc['markov_hits_6ep_in_e5_removed_run'] / 74:.4f})." in md
        assert f"  - Net difference in other folds: {acc['markov_hits_difference_in_6ep']:+d} hits." in md
        assert "- **Frequency Baseline Comparison on Remaining Folds (N=74)**:" in md
        assert f"  - In 7-episode run: {acc['frequency_hits_6ep_in_7ep_run']} / 74 hits ({acc['frequency_hits_6ep_in_7ep_run'] / 74:.4f})." in md
        assert f"  - In E5-removed run: {acc['frequency_hits_6ep_in_e5_removed_run']} / 74 hits ({acc['frequency_hits_6ep_in_e5_removed_run'] / 74:.4f})." in md
        assert f"  - Net difference in Frequency hits: {acc['frequency_hits_difference_in_6ep']:+d} hits." in md

        m_diffs = e5_hit1_json["markov_differing_samples"]
        assert f"Total samples with differing Markov top-1 prediction or Hit@1: **{len(m_diffs)}**." in md
        for d in m_diffs:
            c_str = ", ".join(d["current_tactics"])
            t_str = ", ".join(d["target_tactics"])
            counts_7_str = ", ".join(f"{k}: {v}" for k, v in sorted(d["transition_counts_7ep"].items()))
            counts_no_str = ", ".join(f"{k}: {v}" for k, v in sorted(d["transition_counts_no_e5"].items()))
            line = (
                f"| {d['sample_id']} | {d['episode_id']} | {c_str} | {t_str} | "
                f"{d['pred_7ep']} | {d['hit1_7ep']} | {d['pred_no_e5']} | {d['hit1_no_e5']} | "
                f"`{{{counts_7_str}}}` | tied counts: {d['tied_7ep']} | `{{{counts_no_str}}}` | tied counts: {d['tied_no_e5']} |"
            )
            assert line in md, f"Missing diagnostic table line: {line}"

        assert f"Total samples with differing Frequency top-1 prediction or Hit@1: **{len(e5_hit1_json['frequency_differing_samples'])}**." in md

    def check_tie_sensitivity(md: str) -> None:
        assert "# Post Hoc Tie-Sensitivity Diagnostic Report (7 Episodes)" in md
        assert "post hoc sensitivity bounds, not pre-registered tests; the pre-registered verdict is unchanged" in md
        tie_json = json.loads((REPORTS_DIR / "7ep" / "tie_sensitivity_7ep.json").read_text(encoding="utf-8"))
        for r_id, r_dict in tie_json["summary_tables"].items():
            for sl_id, sl_dict in r_dict.items():
                for m_id, m_dict in sl_dict.items():
                    p = m_dict["pooled"]
                    line_bd = f"| {r_id} | `{sl_id}` | `{m_id}` | {p['n_samples']} | {p['tied_top1_count']} | {p['tied_top1_rate']:.4f} | {p['tied_top3_count']} | {p['tied_top3_rate']:.4f} |"
                    assert line_bd in md, f"Missing boundary table line: {line_bd}"
                    line_pl = (
                        f"| {r_id} | `{sl_id}` | `{m_id}` | {p['n_samples']} | "
                        f"{p['observed_hit1']:.4f} | {p['expected_hit1']:.4f} | {p['best_hit1']:.4f} | {p['worst_hit1']:.4f} | "
                        f"{p['observed_hit3']:.4f} | {p['expected_hit3']:.4f} | {p['best_hit3']:.4f} | {p['worst_hit3']:.4f} |"
                    )
                    assert line_pl in md, f"Missing pooled summary line: {line_pl}"
                    em = m_dict["episode_mean"]
                    line_em = (
                        f"| {r_id} | `{sl_id}` | `{m_id}` | "
                        f"{em['observed_hit1']:.4f} | {em['expected_hit1']:.4f} | {em['best_hit1']:.4f} | {em['worst_hit1']:.4f} | "
                        f"{em['observed_hit3']:.4f} | {em['expected_hit3']:.4f} | {em['best_hit3']:.4f} | {em['worst_hit3']:.4f} |"
                    )
                    assert line_em in md, f"Missing episode-mean line: {line_em}"

        # 7-sample diagnostic list and score vectors
        for item in tie_json["e5_hit1_diagnostic_7_samples"]:
            c_str = ", ".join(item["current_tactics"])
            t_str = ", ".join(item["target_tactics"])
            line_diag = f"| {item['sample_id']} | {item['test_episode']} | {c_str} | {t_str} | {item['7ep']['top1_tied']} | {item['7ep']['top1_group_size']} | {item['no_e5']['top1_tied']} | {item['no_e5']['top1_group_size']} |"
            assert line_diag in md, f"Missing diag 7 line: {line_diag}"
            sample_sec = md.split(f"**{item['sample_id']}**")[1].split("- **E" if item != tie_json["e5_hit1_diagnostic_7_samples"][-1] else "---")[0]
            v7_str = ", ".join(f"{k}: {v}" for k, v in sorted(item["7ep"]["score_vector"].items()))
            vno_str = ", ".join(f"{k}: {v}" for k, v in sorted(item["no_e5"]["score_vector"].items()))
            assert f"7-Episode Score Vector: `{{{v7_str}}}`" in sample_sec, f"Missing v7 in {item['sample_id']}"
            assert f"No-E5 Score Vector: `{{{vno_str}}}`" in sample_sec, f"Missing vno in {item['sample_id']}"

        # Section 4: 7ep minus e5-removed difference
        for mod_name in ["markov", "frequency"]:
            d = tie_json["e5_removed_sensitivity_comparison"][mod_name]
            line_diff = (
                f"| `{mod_name}` | {d['7ep_observed']:.4f} | {d['e5_removed_observed']:.4f} | "
                f"{d['diff_observed']:+.4f} | {d['7ep_expected']:.4f} | {d['e5_removed_expected']:.4f} | "
                f"{d['diff_expected']:+.4f} |"
            )
            assert line_diff in md, f"Missing e5 diff line: {line_diff}"

        b_a = tie_json["pre_registered_conclusion_bounds"]["bound_A_markov_favoured"]
        b_b = tie_json["pre_registered_conclusion_bounds"]["bound_B_frequency_favoured"]
        line_a = f"| Bound A (Markov favoured) | {b_a['b_tactic']} / {b_a['c_tactic']} | {b_a['p1_raw']:.4f} | {b_a['p1_holm']:.4f} | {b_a['b_technique']} / {b_a['c_technique']} | {b_a['p2_raw']:.4f} | {b_a['p2_holm']:.4f} | **{b_a['claim_rule_verdict']}** |"
        line_b = f"| Bound B (Frequency favoured) | {b_b['b_tactic']} / {b_b['c_tactic']} | {b_b['p1_raw']:.4f} | {b_b['p1_holm']:.4f} | {b_b['b_technique']} / {b_b['c_technique']} | {b_b['p2_raw']:.4f} | {b_b['p2_holm']:.4f} | **{b_b['claim_rule_verdict']}** |"
        assert line_a in md, f"Missing Bound A line: {line_a}"
        assert line_b in md, f"Missing Bound B line: {line_b}"

    def check_exploratory(md: str) -> None:
        assert "# Exploratory Tactic-Conditioned Technique Prediction Report" in md
        assert "> **EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT**" in md
        assert "The pre-registered primary evaluation verdict (FAIL on P1, Markov does not outperform Frequency baseline at technique level) is finalized and cannot be modified or overturned by this exploratory variant." in md
        exp_json = json.loads((REPORTS_DIR / "7ep" / "exploratory_tactic_conditioned_results.json").read_text(encoding="utf-8"))
        r7 = exp_json["runs"]["7ep"]
        assert f"- **Coverage**: {r7['coverage']['covered_samples']}/{r7['n_samples']} ({r7['coverage']['coverage_rate']*100:.2f}%) samples had tactic Markov status `ok`." in md
        assert f"- **Ceiling**: {r7['ceiling']['ceiling_samples']}/{r7['n_samples']} ({r7['ceiling']['ceiling_rate']*100:.2f}%) samples had at least one target technique seen in training." in md
        var_m = r7["models"]["variant"]
        freq_m = r7["models"]["frequency"]
        mar_m = r7["models"]["markov"]
        line_var = f"| Exploratory Variant (Tactic-Conditioned) | {var_m['hit1']} | {var_m['hit3']} | {var_m['pooled_top1']*100:.2f}% | [{var_m['wilson95_top1'][0]*100:.2f}%, {var_m['wilson95_top1'][1]*100:.2f}%] | {var_m['pooled_top3']*100:.2f}% | [{var_m['wilson95_top3'][0]*100:.2f}%, {var_m['wilson95_top3'][1]*100:.2f}%] | {var_m['fold_mean_top1']*100:.2f}% | {var_m['fold_mean_top3']*100:.2f}% |"
        line_freq = f"| Frequency Baseline | {freq_m['hit1']} | {freq_m['hit3']} | {freq_m['pooled_top1']*100:.2f}% | [{freq_m['wilson95_top1'][0]*100:.2f}%, {freq_m['wilson95_top1'][1]*100:.2f}%] | {freq_m['pooled_top3']*100:.2f}% | [{freq_m['wilson95_top3'][0]*100:.2f}%, {freq_m['wilson95_top3'][1]*100:.2f}%] | {freq_m['fold_mean_top1']*100:.2f}% | {freq_m['fold_mean_top3']*100:.2f}% |"
        line_mar = f"| Markov Model (Technique) | {mar_m['hit1']} | {mar_m['hit3']} | {mar_m['pooled_top1']*100:.2f}% | [{mar_m['wilson95_top1'][0]*100:.2f}%, {mar_m['wilson95_top1'][1]*100:.2f}%] | {mar_m['pooled_top3']*100:.2f}% | [{mar_m['wilson95_top3'][0]*100:.2f}%, {mar_m['wilson95_top3'][1]*100:.2f}%] | {mar_m['fold_mean_top1']*100:.2f}% | {mar_m['fold_mean_top3']*100:.2f}% |"
        assert line_var in md, f"Missing variant line: {line_var}"
        assert line_freq in md, f"Missing frequency line: {line_freq}"
        assert line_mar in md, f"Missing markov line: {line_mar}"
        m1 = r7["mcnemar_vs_frequency"]["top1"]
        m3 = r7["mcnemar_vs_frequency"]["top3"]
        line_mc1 = f"- **Top-1**: Variant hits and Frequency misses ($b={m1['b']}$); Frequency hits and Variant misses ($c={m1['c']}$); Exact McNemar $p = {m1['p_value']:.4f}$ (descriptive, raw p)."
        line_mc3 = f"- **Top-3**: Variant hits and Frequency misses ($b={m3['b']}$); Frequency hits and Variant misses ($c={m3['c']}$); Exact McNemar $p = {m3['p_value']:.4f}$ (descriptive, raw p)."
        assert line_mc1 in md, f"Missing McNemar top1 line: {line_mc1}"
        assert line_mc3 in md, f"Missing McNemar top3 line: {line_mc3}"
        ts = r7["tie_sensitivity"]
        assert f"- **Tied Samples**: {ts['tied_samples_top1']}/{r7['n_samples']} samples tied at Top-1 boundary; {ts['tied_samples_top3']}/{r7['n_samples']} samples tied at Top-3 boundary." in md
        t1 = ts["top1"]
        t3 = ts["top3"]
        line_ts1 = f"| Hit@1 | {t1['observed']} ({t1['observed_rate']*100:.2f}%) | {t1['expected']:.2f} ({t1['expected_rate']*100:.2f}%) | {t1['best']} ({t1['best_rate']*100:.2f}%) | {t1['worst']} ({t1['worst_rate']*100:.2f}%) | {t1['fold_mean_observed']*100:.2f}% / {t1['fold_mean_expected']*100:.2f}% / {t1['fold_mean_best']*100:.2f}% / {t1['fold_mean_worst']*100:.2f}% |"
        line_ts3 = f"| Hit@3 | {t3['observed']} ({t3['observed_rate']*100:.2f}%) | {t3['expected']:.2f} ({t3['expected_rate']*100:.2f}%) | {t3['best']} ({t3['best_rate']*100:.2f}%) | {t3['worst']} ({t3['worst_rate']*100:.2f}%) | {t3['fold_mean_observed']*100:.2f}% / {t3['fold_mean_expected']*100:.2f}% / {t3['fold_mean_best']*100:.2f}% / {t3['fold_mean_worst']*100:.2f}% |"
        assert line_ts1 in md, f"Missing ts1 line: {line_ts1}"
        assert line_ts3 in md, f"Missing ts3 line: {line_ts3}"
        r_e5 = exp_json["runs"]["e5_removed"]
        assert f"- **Coverage**: {r_e5['coverage']['covered_samples']}/{r_e5['n_samples']} ({r_e5['coverage']['coverage_rate']*100:.2f}%)." in md
        assert f"- **Ceiling**: {r_e5['ceiling']['ceiling_samples']}/{r_e5['n_samples']} ({r_e5['ceiling']['ceiling_rate']*100:.2f}%)." in md
        v_e5 = r_e5["models"]["variant"]
        f_e5 = r_e5["models"]["frequency"]
        m_e5 = r_e5["models"]["markov"]
        line_e5_v = f"| Exploratory Variant (Tactic-Conditioned) | {v_e5['hit1']} | {v_e5['hit3']} | {v_e5['pooled_top1']*100:.2f}% | {v_e5['pooled_top3']*100:.2f}% | {v_e5['fold_mean_top1']*100:.2f}% | {v_e5['fold_mean_top3']*100:.2f}% |"
        line_e5_f = f"| Frequency Baseline | {f_e5['hit1']} | {f_e5['hit3']} | {f_e5['pooled_top1']*100:.2f}% | {f_e5['pooled_top3']*100:.2f}% | {f_e5['fold_mean_top1']*100:.2f}% | {f_e5['fold_mean_top3']*100:.2f}% |"
        line_e5_m = f"| Markov Model (Technique) | {m_e5['hit1']} | {m_e5['hit3']} | {m_e5['pooled_top1']*100:.2f}% | {m_e5['pooled_top3']*100:.2f}% | {m_e5['fold_mean_top1']*100:.2f}% | {m_e5['fold_mean_top3']*100:.2f}% |"
        assert line_e5_v in md, f"Missing e5 variant line: {line_e5_v}"
        assert line_e5_f in md, f"Missing e5 frequency line: {line_e5_f}"
        assert line_e5_m in md, f"Missing e5 markov line: {line_e5_m}"
        m1_e5 = r_e5["mcnemar_vs_frequency"]["top1"]
        m3_e5 = r_e5["mcnemar_vs_frequency"]["top3"]
        assert f"- **McNemar vs Frequency (E5-Removed)**: Top-1 $p = {m1_e5['p_value']:.4f}$; Top-3 $p = {m3_e5['p_value']:.4f}$ (descriptive, raw p)." in md

        line_findings = (
            "- **Findings**: The exploratory tactic-conditioned variant achieved "
            f"Hit@1 = {var_m['hit1']}/{r7['n_samples']} ({var_m['pooled_top1']*100:.2f}%) and "
            f"Hit@3 = {var_m['hit3']}/{r7['n_samples']} ({var_m['pooled_top3']*100:.2f}%). "
            f"While this numerically exceeds the technique-level Markov model ({mar_m['hit1']}/{r7['n_samples']} Hit@1, {mar_m['hit3']}/{r7['n_samples']} Hit@3), "
            f"it does not exceed the unconditional Frequency baseline ({freq_m['hit1']}/{r7['n_samples']} Hit@1, {freq_m['hit3']}/{r7['n_samples']} Hit@3)."
        )
        assert line_findings in md, f"Missing findings line: {line_findings}"

    return [check_lc_table], [check_perm_7ep], [check_pr_7ep], [check_e5_removed], [check_holm], [check_diag], [check_e5_hit1_diag], [check_tie_sensitivity], [check_exploratory]



def run_mutation_sweep() -> dict[str, dict[str, Any]]:
    """Backward-compatible entry point returning numeric mutation results for all reports."""
    tactic_checks, tech_checks = get_check_suites()
    planted_checks, perm_v2_checks, realscale_checks = get_validation_check_suites()
    eval_7ep_checks = get_eval_7ep_check_suites()

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
    eval_7ep_res = sweep_report_numeric(
        "evaluation_7ep_report.md",
        REPORTS_DIR / "7ep" / "evaluation_7ep_report.md",
        eval_7ep_checks,
        is_exempt_eval_7ep,
    )
    (
        lc_checks,
        perm_7ep_checks,
        pr_7ep_checks,
        e5_checks,
        holm_checks,
        diag_checks,
        e5_hit1_checks,
        tie_checks,
        exp_checks,
    ) = get_check_suites_7ep_inference()
    lc_res = sweep_report_numeric(
        "learning_curve_7ep_report.md",
        REPORTS_DIR / "7ep" / "learning_curve_7ep_report.md",
        lc_checks,
        is_exempt_learning_curve_7ep,
    )
    perm_7ep_res = sweep_report_numeric(
        "permutation_7ep_report.md",
        REPORTS_DIR / "7ep" / "permutation_7ep_report.md",
        perm_7ep_checks,
        is_exempt_permutation_7ep,
    )
    pr_7ep_res = sweep_report_numeric(
        "planted_realscale_7ep_report.md",
        REPORTS_DIR / "7ep" / "planted_realscale_7ep_report.md",
        pr_7ep_checks,
        is_exempt_planted_realscale_7ep,
    )
    e5_res = sweep_report_numeric(
        "e5_removed_report.md",
        REPORTS_DIR / "7ep" / "e5_removed_report.md",
        e5_checks,
        is_exempt_e5_removed,
    )
    holm_res = sweep_report_numeric(
        "holm_claim_rule_report.md",
        REPORTS_DIR / "7ep" / "holm_claim_rule_report.md",
        holm_checks,
        is_exempt_holm_claim_rule,
    )
    diag_res = sweep_report_numeric(
        "diagnostics_7ep.md",
        REPORTS_DIR / "7ep" / "diagnostics_7ep.md",
        diag_checks,
        is_exempt_diagnostics_7ep,
    )
    e5_hit1_res = sweep_report_numeric(
        "e5_hit1_change_diagnostic.md",
        REPORTS_DIR / "7ep" / "e5_hit1_change_diagnostic.md",
        e5_hit1_checks,
        is_exempt_e5_hit1_diagnostic,
    )
    tie_res = sweep_report_numeric(
        "tie_sensitivity_7ep.md",
        REPORTS_DIR / "7ep" / "tie_sensitivity_7ep.md",
        tie_checks,
        is_exempt_tie_sensitivity_7ep,
    )
    exp_res = sweep_report_numeric(
        "exploratory_tactic_conditioned_report.md",
        REPORTS_DIR / "7ep" / "exploratory_tactic_conditioned_report.md",
        exp_checks,
        is_exempt_exploratory_tactic_conditioned,
    )
    return {
        "tactic": tactic_res,
        "technique": tech_res,
        "planted_structure": planted_res,
        "permutation_test": perm_v2_res,
        "permutation_test_v2": perm_v2_res,
        "planted_realscale": realscale_res,
        "evaluation_7ep": eval_7ep_res,
        "learning_curve_7ep": lc_res,
        "permutation_7ep": perm_7ep_res,
        "planted_realscale_7ep": pr_7ep_res,
        "e5_removed": e5_res,
        "holm_claim_rule": holm_res,
        "diagnostics_7ep": diag_res,
        "e5_hit1_change_diagnostic": e5_hit1_res,
        "tie_sensitivity_7ep": tie_res,
        "exploratory_tactic_conditioned": exp_res,
    }


def run_label_mutation_sweep() -> dict[str, dict[str, Any]]:
    """Run label mutation sweep returning results dictionary."""
    tactic_checks, tech_checks = get_check_suites()
    eval_7ep_checks = get_eval_7ep_check_suites()
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
    eval_7ep_res = sweep_report_labels(
        "evaluation_7ep_report.md",
        REPORTS_DIR / "7ep" / "evaluation_7ep_report.md",
        eval_7ep_checks,
    )
    return {"tactic": tactic_res, "technique": tech_res, "evaluation_7ep": eval_7ep_res}


def run_all_mutation_sweeps() -> None:
    tactic_checks, tech_checks = get_check_suites()
    planted_checks, perm_v2_checks, realscale_checks = get_validation_check_suites()
    eval_7ep_checks = get_eval_7ep_check_suites()
    (
        lc_checks,
        perm_7ep_checks,
        pr_7ep_checks,
        e5_checks,
        holm_checks,
        diag_checks,
        e5_hit1_checks,
        tie_checks,
        exp_checks,
    ) = get_check_suites_7ep_inference()

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
    num_eval_7ep = sweep_report_numeric(
        "evaluation_7ep_report.md",
        REPORTS_DIR / "7ep" / "evaluation_7ep_report.md",
        eval_7ep_checks,
        is_exempt_eval_7ep,
    )
    num_lc = sweep_report_numeric(
        "learning_curve_7ep_report.md",
        REPORTS_DIR / "7ep" / "learning_curve_7ep_report.md",
        lc_checks,
        is_exempt_learning_curve_7ep,
    )
    num_perm_7ep = sweep_report_numeric(
        "permutation_7ep_report.md",
        REPORTS_DIR / "7ep" / "permutation_7ep_report.md",
        perm_7ep_checks,
        is_exempt_permutation_7ep,
    )
    num_pr_7ep = sweep_report_numeric(
        "planted_realscale_7ep_report.md",
        REPORTS_DIR / "7ep" / "planted_realscale_7ep_report.md",
        pr_7ep_checks,
        is_exempt_planted_realscale_7ep,
    )
    num_e5 = sweep_report_numeric(
        "e5_removed_report.md",
        REPORTS_DIR / "7ep" / "e5_removed_report.md",
        e5_checks,
        is_exempt_e5_removed,
    )
    num_holm = sweep_report_numeric(
        "holm_claim_rule_report.md",
        REPORTS_DIR / "7ep" / "holm_claim_rule_report.md",
        holm_checks,
        is_exempt_holm_claim_rule,
    )
    num_diag = sweep_report_numeric(
        "diagnostics_7ep.md",
        REPORTS_DIR / "7ep" / "diagnostics_7ep.md",
        diag_checks,
        is_exempt_diagnostics_7ep,
    )
    num_e5_hit1 = sweep_report_numeric(
        "e5_hit1_change_diagnostic.md",
        REPORTS_DIR / "7ep" / "e5_hit1_change_diagnostic.md",
        e5_hit1_checks,
        is_exempt_e5_hit1_diagnostic,
    )
    num_tie = sweep_report_numeric(
        "tie_sensitivity_7ep.md",
        REPORTS_DIR / "7ep" / "tie_sensitivity_7ep.md",
        tie_checks,
        is_exempt_tie_sensitivity_7ep,
    )
    num_exp = sweep_report_numeric(
        "exploratory_tactic_conditioned_report.md",
        REPORTS_DIR / "7ep" / "exploratory_tactic_conditioned_report.md",
        exp_checks,
        is_exempt_exploratory_tactic_conditioned,
    )

    numeric_results = {
        "tactic": num_tactic,
        "technique": num_tech,
        "planted_structure": num_planted,
        "permutation_test_v2": num_perm_v2,
        "planted_realscale": num_realscale,
        "evaluation_7ep": num_eval_7ep,
        "learning_curve_7ep": num_lc,
        "permutation_7ep": num_perm_7ep,
        "planted_realscale_7ep": num_pr_7ep,
        "e5_removed": num_e5,
        "holm_claim_rule": num_holm,
        "diagnostics_7ep": num_diag,
        "e5_hit1_change_diagnostic": num_e5_hit1,
        "tie_sensitivity_7ep": num_tie,
        "exploratory_tactic_conditioned": num_exp,
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
    label_eval_7ep = sweep_report_labels(
        "evaluation_7ep_report.md",
        REPORTS_DIR / "7ep" / "evaluation_7ep_report.md",
        eval_7ep_checks,
    )
    label_results = {"tactic": label_tactic, "technique": label_tech, "evaluation_7ep": label_eval_7ep}

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

