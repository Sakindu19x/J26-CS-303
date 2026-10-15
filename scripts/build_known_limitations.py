"""build_known_limitations.py

Reads reports/audit/known_limitations.json and generates reports/audit/known_limitations.md.
Formats each limitation with ID, Title, Category, Status (CLOSED/OPEN), Commit/Resolution, and Description.
"""

from __future__ import annotations
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent.parent

def main():
    json_path = WORKSPACE / "reports" / "audit" / "known_limitations.json"
    with open(json_path, "r", encoding="utf-8") as f:
        limitations = json.load(f)

    md_path = WORKSPACE / "reports" / "audit" / "known_limitations.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Known Limitations Register\n\n")
        f.write("Generated automatically by `scripts/build_known_limitations.py` from `reports/audit/known_limitations.json`.\n")
        f.write("Documents all identified project limitations, tracking resolution status across development phases.\n\n")

        closed_count = sum(1 for item in limitations if item["status"] == "CLOSED")
        open_count = sum(1 for item in limitations if item["status"] == "OPEN")

        f.write(f"**Summary**: {len(limitations)} total limitations recorded ({closed_count} CLOSED, {open_count} OPEN).\n\n")

        f.write("## 1. Limitations Summary Table\n\n")
        f.write("| ID | Title | Category | Status | Resolution / Target Phase |\n")
        f.write("|:---|:---|:---|:---:|:---|\n")

        for item in limitations:
            commit_str = f"`{item['resolution_commit']}`" if item["resolution_commit"] else "Pending C3 / Live Deploy"
            status_str = f"**{item['status']}**" if item['status'] == 'CLOSED' else f"*{item['status']}*"
            f.write(f"| **{item['id']}** | {item['title']} | {item['category']} | {status_str} | {commit_str} |\n")

        f.write("\n## 2. Detailed Register Entries\n\n")

        for item in limitations:
            f.write(f"### {item['id']}: {item['title']}\n\n")
            f.write(f"- **Category**: {item['category']}\n")
            f.write(f"- **Status**: `{item['status']}`\n")
            if item["resolution_commit"]:
                f.write(f"- **Resolution Commit**: `{item['resolution_commit']}`\n")
            f.write(f"- **Description**: {item['description']}\n")
            f.write(f"- **Resolution / Mitigation**: {item['resolution']}\n\n")

    print(f"Wrote {md_path}")

if __name__ == "__main__":
    main()
