"""append_q6_corrections.py

Appends:
1. Dated correction entry to reports/overnight_decisions.md fixing P2 tie-break description.
2. Note to reports/overnight_ledger.md listing incorrect Prompt 13 final-message blocks (by block name only).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECISIONS_MD = REPO_ROOT / "reports" / "overnight_decisions.md"
LEDGER_MD = REPO_ROOT / "reports" / "overnight_ledger.md"


def append_corrections() -> None:
    # 1. Append to overnight_decisions.md
    decisions_text = DECISIONS_MD.read_text(encoding="utf-8")
    if "P2 (Correction)" not in decisions_text:
        correction_entry = (
            "\n## Prompt 14 Decisions & Corrections (2026-10-15)\n\n"
            "| Part | Decision / Correction | Technical Rationale |\n"
            "|:---|:---|:---|\n"
            "| P2 (Correction) | Exact expectation under uniform random tie-breaking, plus best/worst case bounds (Bound A and Bound B); not 1000 trials. | The tie-sensitivity evaluation computes the exact combinatorial expectation and extreme analytical bounds across candidate score permutations rather than Monte Carlo empirical trials. |\n"
        )
        DECISIONS_MD.write_text(decisions_text.rstrip() + "\n" + correction_entry, encoding="utf-8")
        print(f"Appended P2 correction entry to {DECISIONS_MD}")

    # 2. Append to overnight_ledger.md
    ledger_text = LEDGER_MD.read_text(encoding="utf-8")
    if "Prompt 13 final chat message blocks with contradictions" not in ledger_text:
        ledger_note = (
            "\nNote: Prompt 13 final chat message blocks with contradictions vs generated files (by block name only):\n"
            "- Exploratory Variant Block\n"
            "- Hypothesis Test P2 / Tie Counts Block\n"
            "- NFR1 Performance / CPU Telemetry Block\n"
            "- Claims Map Block\n"
            "- Requirements Trace Block\n"
            "- Prediction Records Block\n"
            "- Clean-Clone Verification Block\n"
        )
        LEDGER_MD.write_text(ledger_text.rstrip() + "\n" + ledger_note, encoding="utf-8")
        print(f"Appended erroneous blocks note to {LEDGER_MD}")


if __name__ == "__main__":
    append_corrections()
