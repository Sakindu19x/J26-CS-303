"""record_q14_decision.py

Appends a timestamped decision entry to reports/audit/q14_decisions.md.
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DECISIONS_PATH = REPO_ROOT / "reports" / "audit" / "q14_decisions.md"

def record_decision(part: str, decision: str, reason: str) -> None:
    DECISIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DECISIONS_PATH.exists():
        header = (
            "# Prompt 14 Decisions Register\n\n"
            "| UTC Timestamp | Part | Decision | Reason |\n"
            "|:---|:---|:---|:---|\n"
        )
        DECISIONS_PATH.write_text(header, encoding="utf-8")
    
    utc_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    row = f"| {utc_time} | {part} | {decision} | {reason} |\n"
    with open(DECISIONS_PATH, "a", encoding="utf-8") as f:
        f.write(row)
    print(f"Recorded decision for {part}: {decision}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python record_q14_decision.py <part> <decision> <reason>")
        sys.exit(1)
    record_decision(sys.argv[1], sys.argv[2], sys.argv[3])
