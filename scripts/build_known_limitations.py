"""build_known_limitations.py (Prompt 16 S1g).

Reads reports/audit/known_limitations.json, validates constraints, and generates reports/audit/known_limitations.md.
Rules:
- Allowed statuses: OPEN, MITIGATED, EXPLAINED, CLOSED.
- CLOSED only if a named evidence file exists and is checked by code.
- LIM-03: reads E5-removed sample counts (N=93 technique, N=74 tactic) from reports/7ep/e5_removed_results.json.
- LIM-12: checks that reports/measurements/live_capture_log.txt and live_*.png exist, else OPEN.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = REPO_ROOT / "reports" / "audit" / "known_limitations.json"
MD_PATH = REPO_ROOT / "reports" / "audit" / "known_limitations.md"
ALLOWED_STATUSES = {"OPEN", "MITIGATED", "EXPLAINED", "CLOSED"}


def validate_and_build() -> None:
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        limitations = json.load(f)

    # 1. Check LIM-03 exact numbers from e5_removed_results.json
    e5_results_path = REPO_ROOT / "reports" / "7ep" / "e5_removed_results.json"
    assert e5_results_path.is_file(), f"Missing {e5_results_path}"
    with open(e5_results_path, "r", encoding="utf-8") as f:
        e5_data = json.load(f)
    tech_n = e5_data["comparison_with_all_7ep"]["technique_collapsed_full"]["e5_removed_6ep"]["n_samples"]
    tac_n = e5_data["comparison_with_all_7ep"]["tactic_collapsed"]["e5_removed_6ep"]["n_samples"]
    assert tech_n == 93, f"Expected 93 technique samples, got {tech_n}"
    assert tac_n == 74, f"Expected 74 tactic samples, got {tac_n}"

    # 2. Check LIM-12 live capture files
    live_log = REPO_ROOT / "reports" / "measurements" / "live_capture_log.txt"
    live_pngs = list((REPO_ROOT / "reports" / "measurements").glob("live_*.png"))
    has_live_evidence = live_log.is_file() and len(live_pngs) > 0

    validated = []
    for item in limitations:
        lid = item["id"]
        status = item["status"]
        assert status in ALLOWED_STATUSES, f"{lid}: invalid status '{status}' (allowed: {ALLOWED_STATUSES})"

        if lid == "LIM-03":
            assert f"N={tech_n} technique and {tac_n} tactic" in item["resolution"], (
                f"LIM-03 resolution text must cite exact N={tech_n} and {tac_n}"
            )

        if lid == "LIM-02":
            assert "zero repeat transitions" not in item["description"], (
                "LIM-02 must not contain withdrawn 'zero repeat transitions' wording"
            )

        if lid == "LIM-12":
            if not has_live_evidence:
                item["status"] = "OPEN"
                item["evidence_file"] = None
            else:
                item["status"] = "CLOSED"
                item["evidence_file"] = "reports/measurements/live_capture_log.txt"

        if lid == "LIM-14":
            assert item["status"] == "MITIGATED", f"LIM-14 must have status MITIGATED, got {item['status']}"

        if lid == "LIM-16":
            assert "verified zero access" not in item["resolution"], (
                "LIM-16 must not contain 'verified zero access' wording"
            )

        # Enforce rule: CLOSED only if evidence_file exists on disk
        if item["status"] == "CLOSED":
            ev_file = item.get("evidence_file")
            assert ev_file, f"{lid}: status is CLOSED but no evidence_file is specified"
            ev_path = REPO_ROOT / ev_file
            assert ev_path.is_file(), f"{lid}: status is CLOSED but evidence_file does not exist: {ev_path}"

        validated.append(item)

    # Write validated JSON back
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Render Markdown
    closed_count = sum(1 for item in validated if item["status"] == "CLOSED")
    mitigated_count = sum(1 for item in validated if item["status"] == "MITIGATED")
    explained_count = sum(1 for item in validated if item["status"] == "EXPLAINED")
    open_count = sum(1 for item in validated if item["status"] == "OPEN")

    lines = [
        "# Known Limitations Register",
        "",
        "Generated automatically by `scripts/build_known_limitations.py` from `reports/audit/known_limitations.json`.",
        "Documents all identified project limitations, tracking resolution status across development phases.",
        "",
        f"**Summary**: {len(validated)} total limitations recorded "
        f"({closed_count} CLOSED, {mitigated_count} MITIGATED, {explained_count} EXPLAINED, {open_count} OPEN).",
        "",
        "## 1. Limitations Summary Table",
        "",
        "| ID | Title | Category | Status | Evidence File / Target Phase |",
        "|:---|:---|:---|:---:|:---|",
    ]

    for item in validated:
        st = item["status"]
        if st == "CLOSED":
            badge = "**CLOSED**"
            target = f"`{item['evidence_file']}`"
        elif st == "MITIGATED":
            badge = "**MITIGATED**"
            target = f"`{item.get('evidence_file', 'data constraints')}`"
        elif st == "EXPLAINED":
            badge = "*EXPLAINED*"
            target = f"`{item.get('evidence_file', 'theoretical analysis')}`"
        else:
            badge = "*OPEN*"
            target = "Pending C3 / Live Deploy"

        lines.append(f"| **{item['id']}** | {item['title']} | {item['category']} | {badge} | {target} |")

    lines.extend([
        "",
        "## 2. Detailed Register Entries",
        "",
    ])

    for item in validated:
        lines.extend([
            f"### {item['id']}: {item['title']}",
            "",
            f"- **Category**: {item['category']}",
            f"- **Status**: `{item['status']}`",
        ])
        if item.get("evidence_file"):
            lines.append(f"- **Evidence File**: `{item['evidence_file']}`")
        if item.get("resolution_commit"):
            lines.append(f"- **Resolution Commit**: `{item['resolution_commit']}`")
        lines.extend([
            f"- **Description**: {item['description']}",
            f"- **Resolution / Mitigation**: {item['resolution']}",
            "",
        ])

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated {MD_PATH} successfully ({len(validated)} items checked).")


if __name__ == "__main__":
    validate_and_build()
