"""Generate reports/step_type_summary.json and reports/step_type_summary.md.

Per episode analysis of AttackMate step types (labeled vs unlabeled counts),
composite steps inspection (loop, include, etc.), and double-counting analysis.
"""
from __future__ import annotations

import json
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"

SCENARIOS = {
    "E1": "scenario_1_sudo_pam.zip",
    "E2": "scenario_2_cron.zip",
    "E3": "scenario_3_vnc_apt.zip",
    "E4": "scenario_4.zip",
}


def analyze_step_types() -> dict[str, Any]:
    norm_path = PROCESSED_DIR / "normalized_events.json"
    with open(norm_path, encoding="utf-8") as f:
        events = json.load(f)

    events_by_ep = defaultdict(list)
    for e in events:
        events_by_ep[e["episode_id"]].append(e)

    summary_episodes: dict[str, Any] = {}

    for ep, zip_name in SCENARIOS.items():
        zpath = RAW_DIR / zip_name
        with zipfile.ZipFile(zpath, "r") as zf:
            am_name = [n for n in zf.namelist() if n.endswith("attacker/logs/attackmate.json")][0]
            with zf.open(am_name) as fh:
                raw_steps = [json.loads(line.strip()) for line in fh if line.strip()]

        ep_events = events_by_ep[ep]

        type_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "labeled": 0, "unlabeled": 0})
        for e in ep_events:
            stype = e.get("step_type") or "unknown"
            type_counts[stype]["total"] += 1
            if e.get("is_labeled"):
                type_counts[stype]["labeled"] += 1
            else:
                type_counts[stype]["unlabeled"] += 1

        # Inspect composite steps
        composite_steps = []
        for idx, ev in enumerate(ep_events):
            step_idx = ev.get("source_line_or_step_index", idx)
            raw_s = raw_steps[step_idx] if step_idx < len(raw_steps) else {}
            stype = raw_s.get("type", ev.get("step_type", ""))
            params = raw_s.get("parameters", {}) if isinstance(raw_s.get("parameters"), dict) else {}
            is_composite = stype in {"loop", "include"} or "commands" in params

            if is_composite:
                techniques = ev.get("techniques", [])
                is_labeled = ev.get("is_labeled", False)
                nested_commands = params.get("commands", [])

                # Check subsequent events that fall within the execution context or overlap techniques
                overlapping_subsequent_events = []
                if is_labeled and techniques:
                    for later_ev in ep_events[idx + 1: idx + 15]:
                        later_techs = later_ev.get("techniques", [])
                        overlap = set(techniques) & set(later_techs)
                        if overlap:
                            overlapping_subsequent_events.append({
                                "event_id": later_ev["event_id"],
                                "timestamp": later_ev["timestamp"],
                                "step_type": later_ev.get("step_type"),
                                "techniques": later_techs,
                                "overlapping_techniques": sorted(list(overlap)),
                            })

                composite_steps.append({
                    "step_index": step_idx,
                    "event_id": ev["event_id"],
                    "step_type": stype,
                    "is_labeled": is_labeled,
                    "techniques": techniques,
                    "timestamp": ev["timestamp"],
                    "cmd": ev.get("cmd", ""),
                    "nested_commands_count": len(nested_commands),
                    "overlapping_subsequent_events": overlapping_subsequent_events,
                })

        summary_episodes[ep] = {
            "archive": zip_name,
            "total_events": len(ep_events),
            "step_types": dict(sorted(type_counts.items())),
            "composite_steps": composite_steps,
        }

    report = {
        "episodes": summary_episodes,
        "double_counting_analysis": (
            "Double-Counting Assessment of Composite Steps:\n"
            "In CAM-LDS, composite container step E3-S006 (type 'loop', cmd 'items(LISTA)') in Episode 3 is labeled with "
            "MITRE ATT&CK techniques (['T1110.001', 'T1021.005'] for VNC password guessing). Inspection of its raw parameters "
            "shows a loop count of 3 with a single nested template command ('vnc move') iterating over password variable '$LOOP_ITEM'.\n"
            "The subsequent execution steps (E3-S007, E3-S009, E3-S011, E3-S013 of type 'vnc') are independently recorded top-level lines "
            "in attackmate.json with differing commands ('click', 'type', 'key', 'type'), labeled with ['T1021.005']. Whether these "
            "subsequent steps represent runtime iterations emitted by the loop execution or are separate sequential log entries in the "
            "AttackMate playbook cannot be definitively determined from the log structure alone and is unconfirmed.\n"
            "Consequence in Sequences:\n"
            "1. Raw Variant: Technique T1021.005 is represented in E3-S006 and then immediately repeated in individual VNC interaction "
            "steps (E3-S007, E3-S009, E3-S013), causing repeated consecutive entries of the same technique.\n"
            "2. Collapsed Variant: Because E3-S006 carries a multi-technique set {T1021.005, T1110.001} while the subsequent steps carry {T1021.005}, "
            "the merge condition (identical consecutive sets) does not merge the container with its subsequent steps. Consequently, the collapsed sequence "
            "contains a transition from {T1021.005, T1110.001} -> {T1021.005}.\n"
            "3. Recommendation: The sequences remain unmodified as specified by protocol to preserve fidelity to raw AttackMate ground truth, "
            "but modeling and evaluation must note that transitions out of E3-S006 may reflect composite step container boundaries."
        ),
    }

    # Save JSON
    json_path = REPORTS_DIR / "step_type_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"Saved {json_path}")

    # Save Markdown
    md_path = REPORTS_DIR / "step_type_summary.md"
    md_content = render_step_type_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved {md_path}")

    return report


def render_step_type_markdown(rep: dict[str, Any]) -> str:
    lines = [
        "# AttackMate Step Type & Composite Step Analysis",
        "",
        "## 1. Step Type Distribution Per Episode",
        "",
        "| Episode | Step Type | Total Steps | Labeled Steps | Unlabeled Steps | Description / Role |",
        "|---|---|---|---|---|---|",
    ]

    for ep, d in rep["episodes"].items():
        for stype, counts in d["step_types"].items():
            lines.append(f"| **{ep}** | `{stype}` | {counts['total']} | {counts['labeled']} | {counts['unlabeled']} | Attack command / action |")

    lines.extend([
        "",
        "## 2. Composite Steps Breakdown",
        "",
        "| Episode | Event ID | Step Type | Labeled? | Techniques | Nested Commands | Overlapping Child/Subsequent Steps |",
        "|---|---|---|---|---|---|---|",
    ])

    found_any = False
    for ep, d in rep["episodes"].items():
        for cs in d["composite_steps"]:
            found_any = True
            tech_str = ", ".join(cs["techniques"]) if cs["techniques"] else "*(None)*"
            ov_events = [f"`{o['event_id']}` ({', '.join(o['overlapping_techniques'])})" for o in cs["overlapping_subsequent_events"]]
            ov_str = "<br>".join(ov_events) if ov_events else "None"
            lines.append(
                f"| **{ep}** | `{cs['event_id']}` | `{cs['step_type']}` | {cs['is_labeled']} | `{tech_str}` | {cs['nested_commands_count']} | {ov_str} |"
            )

    if not found_any:
        lines.append("| - | None | - | - | - | - | - |")

    lines.extend([
        "",
        "## 3. Double-Counting Assessment",
        "",
        rep["double_counting_analysis"],
    ])

    return "\n".join(lines)


if __name__ == "__main__":
    analyze_step_types()
