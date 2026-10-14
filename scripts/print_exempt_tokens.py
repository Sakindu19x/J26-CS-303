#!/usr/bin/env python3
"""Print exempt tokens and lines 1-30 classification for Prompt 13 P1.3."""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.mutation_sweep import (
    get_check_suites_7ep_inference,
    is_exempt_diagnostics_7ep,
    is_exempt_e5_hit1_diagnostic,
    is_exempt_e5_removed,
    is_exempt_holm_claim_rule,
    is_exempt_learning_curve_7ep,
    is_exempt_permutation_7ep,
    is_exempt_planted_realscale_7ep,
    mutate_numeric_token,
    sweep_report_numeric,
)


def main() -> None:
    print("=" * 80)
    print("EXEMPT TOKENS AND INTRO CLASSIFICATION AUDIT (1.3)")
    print("=" * 80)

    suites = get_check_suites_7ep_inference()
    reports = [
        ("learning_curve_7ep_report.md", suites[0], is_exempt_learning_curve_7ep),
        ("permutation_7ep_report.md", suites[1], is_exempt_permutation_7ep),
        ("planted_realscale_7ep_report.md", suites[2], is_exempt_planted_realscale_7ep),
        ("e5_removed_report.md", suites[3], is_exempt_e5_removed),
        ("holm_claim_rule_report.md", suites[4], is_exempt_holm_claim_rule),
        ("diagnostics_7ep.md", suites[5], is_exempt_diagnostics_7ep),
        ("e5_hit1_change_diagnostic.md", suites[6], is_exempt_e5_hit1_diagnostic),
    ]

    for name, chks, exempt_fn in reports:
        p = REPO_ROOT / "reports" / "7ep" / name
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8")
        lines = text.splitlines()
        res = sweep_report_numeric(name, p, chks, exempt_fn)

        print(f"\n--- REPORT: {name} ---")
        print(f"File SHA-256: {sha}")
        print(f"Total Lines: {len(lines)}")
        tested = res.get("tested_total", res.get("total_tested", 0))
        exempt = res.get("exempt_total", 0)
        tot = tested + exempt
        print(f"Total Tokens: {tot} | Exempt: {exempt} | Tested: {tested} | Detected: {res['detected']} | Undetected: {res['undetected']}")
        print(f"Exempt Tokens List:")
        for item in res["exempt_items"]:
            # disk line text
            disk_line = lines[item["line_number"] - 1]
            print(f"  {name}:{item['line_number']}:{item['token']} [{item['rule']}] -> {disk_line}")

    # Per-line classification for lines 1-30 of learning_curve_7ep_report.md
    lc_p = REPO_ROOT / "reports" / "7ep" / "learning_curve_7ep_report.md"
    lc_text = lc_p.read_text(encoding="utf-8")
    lc_lines = lc_text.splitlines()
    lc_checks = suites[0]

    print("\n" + "=" * 80)
    print("PER-LINE CLASSIFICATION FOR learning_curve_7ep_report.md (Lines 1-30)")
    print("=" * 80)

    pos = 0
    not_covered_tokens = []
    for line_no in range(1, min(31, len(lc_lines) + 1)):
        line = lc_lines[line_no - 1]
        tokens = list(re.finditer(r"\d+(?:\.\d+)?%?", line))
        if not tokens:
            print(f"Line {line_no:2d}: (no numeric tokens) | {line}")
        else:
            token_classes = []
            for m in tokens:
                tok = m.group()
                start = pos + m.start()
                end = pos + m.end()
                is_ex, reason = is_exempt_learning_curve_7ep(line, line_no, tok, m.start(), m.end())
                if is_ex:
                    token_classes.append(f"[{tok} -> exempt: {reason}]")
                else:
                    mut = mutate_numeric_token(tok)
                    mut_text = lc_text[:start] + mut + lc_text[end:]
                    detected = False
                    for chk in lc_checks:
                        try:
                            chk(mut_text)
                        except Exception:
                            detected = True
                            break
                    if detected:
                        token_classes.append(f"[{tok} -> verified]")
                    else:
                        token_classes.append(f"[{tok} -> NOT COVERED]")
                        not_covered_tokens.append((line_no, tok, line))
            print(f"Line {line_no:2d}: {' '.join(token_classes)} | {line}")
        pos += len(line) + 1

    print("\n" + "-" * 80)
    print(f"Total not covered tokens in lines 1-30: {len(not_covered_tokens)}")
    if not_covered_tokens:
        for lno, tk, lt in not_covered_tokens:
            print(f"  Line {lno} [{tk}]: {lt}")
    else:
        print("All intro numbers (6, 15, 20, 42, 105, 140, 441, 882 ...) are fully verified/covered.")


if __name__ == "__main__":
    main()
