"""ATT&CK sequence construction from labeled timeline events."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from c4.mitre_reference import get_official_tactics

CAUSATION_DISCLAIMER = (
    "Note on Forensic Causality: Chronological ordering of attack steps reflects the temporal "
    "manifestation sequence recorded in telemetry; temporal precedence does not by itself prove causal dependency."
)


def build_raw_sequence(timeline_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build raw sequence from labeled steps only, tracking preceding unlabeled step gaps."""
    raw_sequence = []
    unlabeled_skipped = 0

    for ev in timeline_events:
        techs = ev.get("techniques") or []
        is_labeled = ev.get("is_labeled", False) and len(techs) > 0

        if not is_labeled:
            unlabeled_skipped += 1
        else:
            sorted_techs = sorted(list(set(techs)))
            raw_sequence.append({
                "event_id": ev["event_id"],
                "timestamp": ev["timestamp"],
                "techniques": sorted_techs,
                "tactics": ev.get("tactics", []),
                "official_tactics": ev.get("official_tactics") or get_official_tactics(sorted_techs),
                "unlabeled_steps_skipped_before": unlabeled_skipped,
            })
            unlabeled_skipped = 0

    return raw_sequence


def collapse_sequence(raw_sequence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse consecutive labeled steps with identical cleaned technique sets."""
    if not raw_sequence:
        return []

    collapsed = []
    for item in raw_sequence:
        item_tech_set = set(item["techniques"])
        if collapsed and set(collapsed[-1]["techniques"]) == item_tech_set:
            # Merge with previous collapsed block
            prev = collapsed[-1]
            prev["event_ids"].append(item["event_id"])
            prev["repeat_count"] += 1
            prev["end_timestamp"] = item["timestamp"]
            # Per-merge gap boundary tracking
            prev["unlabeled_steps_skipped_between"].append(item["unlabeled_steps_skipped_before"])
            # Union of tactics preserving order
            for tac in item.get("tactics", []):
                if tac not in prev["tactics"]:
                    prev["tactics"].append(tac)
            for otac in item.get("official_tactics", []):
                if otac not in prev["official_tactics"]:
                    prev["official_tactics"].append(otac)
        else:
            collapsed.append({
                "event_ids": [item["event_id"]],
                "repeat_count": 1,
                "timestamp": item["timestamp"],
                "end_timestamp": item["timestamp"],
                "techniques": item["techniques"],
                "tactics": list(item.get("tactics", [])),
                "official_tactics": list(item.get("official_tactics", [])),
                "unlabeled_steps_skipped_before": item["unlabeled_steps_skipped_before"],
                "unlabeled_steps_skipped_between": [],
            })

    return collapsed


def build_episode_sequences(timeline_events: list[dict[str, Any]]) -> dict[str, Any]:
    """Build both raw and collapsed sequence variants for a single episode."""
    raw_seq = build_raw_sequence(timeline_events)
    collapsed_seq = collapse_sequence(raw_seq)

    distinct_techs = sorted(list({t for item in raw_seq for t in item["techniques"]}))

    return {
        "raw": raw_seq,
        "collapsed": collapsed_seq,
        "raw_length": len(raw_seq),
        "collapsed_length": len(collapsed_seq),
        "distinct_techniques_count": len(distinct_techs),
        "distinct_techniques": distinct_techs,
    }


def build_all_sequences(timelines_by_episode: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Build sequence variants across all episodes with causality disclaimer."""
    result = {
        "causation_disclaimer": CAUSATION_DISCLAIMER,
        "episodes": {},
    }
    for ep_id, events in timelines_by_episode.items():
        result["episodes"][ep_id] = build_episode_sequences(events)
    return result


def export_sequences(sequences_data: dict[str, Any], output_path: Path) -> None:
    """Export attack sequences dictionary to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sequences_data, f, indent=2, ensure_ascii=False)


# Backward-compatibility helper for test_basic.py
def attack_sequence(timeline: pd.DataFrame, label_col: str = "attack_label") -> list[str]:
    """Ordered, consecutive-deduplicated labels. Unlabeled events are skipped, not guessed."""
    if label_col not in timeline:
        return []
    seq: list[str] = []
    for v in timeline[label_col].dropna():
        if not seq or seq[-1] != v:
            seq.append(v)
    return seq
