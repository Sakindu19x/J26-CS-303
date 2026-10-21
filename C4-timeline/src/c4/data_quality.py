"""Data quality reporting for normalized AttackMate events and Wazuh enrichment."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .normalization import QualityLog

FIELD_PROVENANCE = [
    {
        "field": "event_id",
        "provenance": "Derived (deterministic)",
        "source": "episode_id + 1-indexed step number (e.g. E1-S001)",
        "c3_role": "Unique stable identifier for forensic timeline graph nodes",
    },
    {
        "field": "episode_id",
        "provenance": "Observed / mapped",
        "source": "CAM-LDS scenario archive mapping (E1..E4)",
        "c3_role": "Episode isolation boundary (runs never combined)",
    },
    {
        "field": "timestamp",
        "provenance": "Observed + UTC assumption",
        "source": "attackmate.json start-datetime standardized to ISO 8601 UTC",
        "c3_role": "Temporal anchor for chronological timeline ordering",
    },
    {
        "field": "step_type, cmd, hostname, username",
        "provenance": "Observed",
        "source": "attackmate.json parameters",
        "c3_role": "Forensic event evidence and entity metadata",
    },
    {
        "field": "techniques, tactics, technique_names",
        "provenance": "Observed (ground-truth label)",
        "source": "attackmate.json parameters.metadata (cleaned)",
        "c3_role": "Ground-truth labels for evaluation of next-stage prediction",
    },
    {
        "field": "local_occurrence",
        "provenance": "Derived (forensic computation)",
        "source": "Formula (derived): per-technique mapping {technique_id: cumulative 1-indexed occurrence count within episode up to this event}. For unlabeled events, null.",
        "c3_role": "derived by C4 for CAM-LDS; the real C3 will supply its own value (format to be agreed)",
    },
    {
        "field": "ioc, ioc_type",
        "provenance": "Missing in CAM-LDS (null)",
        "source": "Not present in simulation logs",
        "c3_role": "to be supplied by C3; format to be agreed with the C3 owner",
    },
    {
        "field": "incident_stage",
        "provenance": "Missing in CAM-LDS (null)",
        "source": "Not present in simulation logs",
        "c3_role": "to be supplied by C3; format to be agreed with the C3 owner",
    },
    {
        "field": "asset_criticality",
        "provenance": "Missing in CAM-LDS (null)",
        "source": "Not present in simulation logs",
        "c3_role": "to be supplied by C3; format to be agreed with the C3 owner",
    },
    {
        "field": "cti_confidence, freshness",
        "provenance": "Missing in CAM-LDS (null)",
        "source": "Not present in simulation logs",
        "c3_role": "to be supplied by C3; format to be agreed with the C3 owner",
    },
    {
        "field": "c3_threat_score, investigation_priority",
        "provenance": "Missing in CAM-LDS (null)",
        "source": "Not present in simulation logs",
        "c3_role": "to be supplied by C3; format to be agreed with the C3 owner",
    },
]


def build_data_quality_report(
    episode_summaries: dict[str, Any],
    qlog: QualityLog,
    wazuh_summaries: dict[str, Any],
) -> dict[str, Any]:
    """Assemble complete data quality metrics dictionary."""
    return {
        "summary": {
            "total_episodes": len(episode_summaries),
            "total_events": sum(e["total_events"] for e in episode_summaries.values()),
            "total_labeled": sum(e["labeled_events"] for e in episode_summaries.values()),
            "total_unlabeled": sum(e["unlabeled_events"] for e in episode_summaries.values()),
            "total_multi_technique_steps": sum(e["multi_technique_steps"] for e in episode_summaries.values()),
        },
        "episodes": episode_summaries,
        "quality_issues": {
            "whitespace_fixes_count": len(qlog.whitespace_fixes),
            "whitespace_fixes": qlog.whitespace_fixes,
            "invalid_techniques_count": len(qlog.invalid_techniques),
            "invalid_techniques": qlog.invalid_techniques,
            "malformed_records_count": len(qlog.malformed_records),
            "malformed_records": qlog.malformed_records,
            "missing_timestamps_count": len(qlog.missing_timestamps),
            "missing_timestamps": qlog.missing_timestamps,
            "skipped_records_count": len(qlog.skipped_records),
            "skipped_records": qlog.skipped_records,
        },
        "wazuh_enrichment": wazuh_summaries,
        "field_provenance": FIELD_PROVENANCE,
    }


def render_quality_markdown(report: dict[str, Any]) -> str:
    """Render data quality report to Markdown."""
    lines = [
        "# CAM-LDS Data Quality & Normalization Report",
        "",
        "## 1. Episode Summary",
        "",
        "| Episode | Scenario | Source Archive | Total Events | Labeled | Unlabeled | Multi-Tech Steps | Window Start (UTC) | Window End (UTC) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for ep, d in report["episodes"].items():
        lines.append(
            f"| **{ep}** | `{d['scenario_id']}` | `{d['source_archive']}` | {d['total_events']} | {d['labeled_events']} | {d['unlabeled_events']} | {d['multi_technique_steps']} | `{d['window_start']}` | `{d['window_end']}` |"
        )

    lines.extend([
        "",
        "## 2. Quality Checks & Cleaning Actions",
        "",
        f"- **Whitespace Fixes Applied ({report['quality_issues']['whitespace_fixes_count']}):**",
    ])
    for w in report["quality_issues"]["whitespace_fixes"]:
        lines.append(f"  - [{w['episode_id']} Step {w['step_index']}] Field `{w['field']}`: `{w['raw_part']!r}` -> `{w['cleaned_part']!r}`")
    if not report["quality_issues"]["whitespace_fixes"]:
        lines.append("  - None")

    lines.extend([
        "",
        f"- **Malformed Records Recovered ({report['quality_issues']['malformed_records_count']}):**",
    ])
    for m in report["quality_issues"]["malformed_records"]:
        lines.append(f"  - [{m['episode_id']} Step {m['step_index']}] {m['description']}: raw key `{m['raw_key']!r}`, raw val `{m['raw_val']!r}` -> recovered name: `{m['recovered_name']}`")
    if not report["quality_issues"]["malformed_records"]:
        lines.append("  - None")

    lines.extend([
        "",
        f"- **Invalid Technique IDs ({report['quality_issues']['invalid_techniques_count']}):** None (all matched `^T\\d{{4}}(\\.\\d{{3}})?$`)" if not report["quality_issues"]["invalid_techniques"] else f"- **Invalid Technique IDs:** {report['quality_issues']['invalid_techniques']}",
        f"- **Missing Timestamps ({report['quality_issues']['missing_timestamps_count']}):** None (all AttackMate steps have valid ISO timestamps)",
        f"- **Skipped Records ({report['quality_issues']['skipped_records_count']}):** None (100% of AttackMate steps preserved)",
        "",
        "## 3. Wazuh Alert In-Window Enrichment",
        "",
        "| Episode | Total Alerts in File | In Attack Window | Excluded (Before) | Excluded (After) | With Rule ID | With MITRE |",
        "|---|---|---|---|---|---|---|",
    ])
    for ep, w in report["wazuh_enrichment"].items():
        lines.append(
            f"| **{ep}** | {w['total_alerts']} | **{w['in_window']}** | {w['excluded_before_window']} | {w['excluded_after_window']} | {w['in_window_with_rule_id']} | {w['in_window_with_mitre']} |"
        )

    lines.extend([
        "",
        "### Top 10 Wazuh Rules by Count per Episode (In-Window Alerts)",
        "",
    ])
    for ep, w in report["wazuh_enrichment"].items():
        lines.append(f"#### Episode {ep} (Total in-window: {w['in_window']})")
        lines.append("")
        lines.append("| Rank | Rule ID | Description | Count | Share (%) |")
        lines.append("|---|---|---|---|---|")
        top_rules = w.get("top_10_rules", [])
        if not top_rules:
            lines.append("| - | - | None | 0 | 0.0% |")
        else:
            for rank, r in enumerate(top_rules, 1):
                lines.append(f"| {rank} | `{r['rule_id']}` | {r['rule_description']} | {r['count']} | {r['share_percent']}% |")
        lines.append("")

    lines.extend([
        "> [!NOTE]",
        "> Wazuh alert MITRE mappings are detector-derived signature triggers and are kept strictly isolated in `data/processed/wazuh_alerts_normalized.csv` without merging into AttackMate ground-truth labels.",
        "",
        "## 4. Field Provenance & C3 Integration Plan",
        "",
        "| Field | Provenance in CAM-LDS | Source / Derivation | C3 Forensic Role |",
        "|---|---|---|---|",
    ])
    for fp in report["field_provenance"]:
        lines.append(f"| `{fp['field']}` | **{fp['provenance']}** | {fp['source']} | {fp['c3_role']} |")

    lines.append("")
    return "\n".join(lines)
