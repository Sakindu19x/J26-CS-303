"""Timeline reconstruction for C4 forensic investigation."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from c4.mitre_reference import get_official_tactics

UTC = timezone.utc

C3_FIELDS = [
    "ioc",
    "ioc_type",
    "incident_stage",
    "asset_criticality",
    "cti_confidence",
    "freshness",
    "c3_threat_score",
    "investigation_priority",
]

TIMELINE_COLUMNS = [
    "event_id",
    "episode_id",
    "timestamp",
    "seconds_since_episode_start",
    "seconds_since_previous_event",
    "step_type",
    "cmd",
    "hostname",
    "username",
    "techniques",
    "tactics",
    "official_tactics",
    "is_labeled",
    "label_status",
    "local_occurrence",
    *C3_FIELDS,
]


def reconstruct_episode_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build chronological timeline for a single episode.

    Sorts deterministically by UTC timestamp, ties broken by original step index,
    missing timestamps flagged and sorted last.
    Computes seconds_since_episode_start and seconds_since_previous_event.
    """
    if not events:
        return []

    # Sort deterministically
    def sort_key(e: dict[str, Any]):
        is_missing = bool(e.get("timestamp_missing") or not e.get("timestamp"))
        ts_val = e.get("timestamp") or ""
        step_idx = e.get("source_line_or_step_index", 0)
        return (is_missing, ts_val, step_idx)

    sorted_events = sorted(events, key=sort_key)

    # Find first valid timestamp in this episode
    valid_dts = []
    for e in sorted_events:
        ts_str = e.get("timestamp")
        if ts_str:
            try:
                valid_dts.append(datetime.fromisoformat(ts_str))
            except ValueError:
                pass

    ep_start_dt = valid_dts[0] if valid_dts else None

    timeline = []
    prev_dt: datetime | None = None

    for ev in sorted_events:
        ts_str = ev.get("timestamp")
        dt: datetime | None = None
        if ts_str:
            try:
                dt = datetime.fromisoformat(ts_str)
            except ValueError:
                dt = None

        if dt is not None and ep_start_dt is not None:
            sec_start = round((dt - ep_start_dt).total_seconds(), 3)
            sec_prev = round((dt - prev_dt).total_seconds(), 3) if prev_dt is not None else 0.0
            prev_dt = dt
        else:
            sec_start = None
            sec_prev = None

        has_techs = bool(ev.get("techniques"))
        is_labeled = bool(ev.get("is_labeled") and has_techs)
        label_status = "ground_truth" if is_labeled else "unlabeled"

        tech_list = ev.get("techniques") if isinstance(ev.get("techniques"), list) else []
        item = {
            "event_id": ev.get("event_id"),
            "episode_id": ev.get("episode_id"),
            "timestamp": ts_str,
            "seconds_since_episode_start": sec_start,
            "seconds_since_previous_event": sec_prev,
            "step_type": ev.get("step_type"),
            "cmd": ev.get("cmd"),
            "hostname": ev.get("hostname"),
            "username": ev.get("username"),
            "techniques": tech_list,
            "tactics": ev.get("tactics") if isinstance(ev.get("tactics"), list) else [],
            "official_tactics": get_official_tactics(tech_list) if is_labeled else [],
            "is_labeled": is_labeled,
            "label_status": label_status,
            "local_occurrence": ev.get("local_occurrence"),
        }
        for f in C3_FIELDS:
            item[f] = ev.get(f, None)

        timeline.append(item)

    return timeline


def reconstruct_all_timelines(events_by_episode: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """Reconstruct timelines across all episodes without merging."""
    timelines: dict[str, list[dict[str, Any]]] = {}
    for ep_id, ep_events in events_by_episode.items():
        timelines[ep_id] = reconstruct_episode_timeline(ep_events)
    return timelines


def filter_timeline(
    events: list[dict[str, Any]],
    episode_id: str | None = None,
    start_time: str | datetime | None = None,
    end_time: str | datetime | None = None,
    hostname: str | None = None,
    technique: str | None = None,
    tactic: str | None = None,
    label_status: str | None = None,
) -> list[dict[str, Any]]:
    """Filter timeline events gracefully handling empty, None, and missing fields."""
    if not events:
        return []

    # Parse time boundaries
    st_dt: datetime | None = None
    if start_time:
        if isinstance(start_time, datetime):
            st_dt = start_time if start_time.tzinfo else start_time.replace(tzinfo=UTC)
        else:
            try:
                st_dt = datetime.fromisoformat(str(start_time))
                if st_dt.tzinfo is None:
                    st_dt = st_dt.replace(tzinfo=UTC)
            except Exception:
                st_dt = None

    et_dt: datetime | None = None
    if end_time:
        if isinstance(end_time, datetime):
            et_dt = end_time if end_time.tzinfo else end_time.replace(tzinfo=UTC)
        else:
            try:
                et_dt = datetime.fromisoformat(str(end_time))
                if et_dt.tzinfo is None:
                    et_dt = et_dt.replace(tzinfo=UTC)
            except Exception:
                et_dt = None

    filtered = []
    for ev in events:
        # Filter by episode
        if episode_id is not None and ev.get("episode_id") != episode_id:
            continue

        # Filter by label_status
        if label_status is not None and ev.get("label_status") != label_status:
            continue

        # Filter by hostname
        if hostname is not None:
            ev_host = ev.get("hostname")
            if not ev_host or ev_host.lower() != hostname.lower():
                continue

        # Filter by technique
        if technique is not None:
            target_t = technique.strip().upper()
            ev_techs = [t.upper() for t in ev.get("techniques", [])]
            if target_t not in ev_techs:
                continue

        # Filter by tactic
        if tactic is not None:
            target_tac = tactic.strip().lower()
            ev_tacs = [t.lower() for t in ev.get("tactics", [])]
            if target_tac not in ev_tacs:
                continue

        # Filter by time range
        if st_dt is not None or et_dt is not None:
            ts_str = ev.get("timestamp")
            if not ts_str:
                continue
            try:
                ev_dt = datetime.fromisoformat(ts_str)
                if ev_dt.tzinfo is None:
                    ev_dt = ev_dt.replace(tzinfo=UTC)
            except Exception:
                continue

            if st_dt is not None and ev_dt < st_dt:
                continue
            if et_dt is not None and ev_dt > et_dt:
                continue

        filtered.append(ev)

    return filtered


def export_timelines(
    timelines: dict[str, list[dict[str, Any]]],
    output_json_path: Path,
    output_csv_path: Path,
) -> None:
    """Export reconstructed timelines to JSON and CSV formats."""
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten for CSV while keeping per-episode isolation in JSON
    all_rows: list[dict[str, Any]] = []
    for ep_id, rows in timelines.items():
        all_rows.extend(rows)

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(timelines, f, indent=2, ensure_ascii=False)

    df = pd.DataFrame(all_rows)
    for col in ["techniques", "tactics", "official_tactics", "local_occurrence"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
    df.to_csv(output_csv_path, index=False, encoding="utf-8", lineterminator="\n")


# Backward-compatibility helper for test_basic.py
def build_timeline(run_events: pd.DataFrame) -> pd.DataFrame:
    """Chronological order; rows with missing timestamps are kept at the end, flagged."""
    df = run_events.copy()
    ts_col = "timestamp_utc" if "timestamp_utc" in df.columns else "timestamp"
    df["timestamp_missing"] = df[ts_col].isna()
    return df.sort_values(["timestamp_missing", ts_col], kind="stable").reset_index(drop=True)
