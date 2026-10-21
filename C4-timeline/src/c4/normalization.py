"""Normalization of AttackMate steps into C4 forensic event schema."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

TECH_RX = re.compile(r"^T\d{4}(\.\d{3})?$")
UTC = timezone.utc

EPISODE_MAPPING = {
    "scenario_1_sudo_pam": "E1",
    "scenario_2_cron": "E2",
    "scenario_3_vnc_apt": "E3",
    "scenario_4": "E4",
}

EPISODE_MAPPING_7EP = {
    "scenario_1_sudo_pam": "E1",
    "scenario_2_cron": "E2",
    "scenario_3_vnc_apt": "E3",
    "scenario_4": "E4",
    "scenario_5": "E5",
    "scenario_6_macro_binary": "E6",
    "scenario_7": "E7",
}

TIMESTAMP_ASSUMPTIONS = {
    "E1": "UTC (verified via host audit log correlation within 0.33s)",
    "E2": "UTC (inconclusive direct audit match, but consistent with host /etc/timezone Etc/UTC)",
    "E3": "UTC (inconclusive direct audit match, but consistent with host /etc/timezone Etc/UTC)",
    "E4": "UTC (verified via host audit log correlation within 0.89s)",
}

NORMALIZED_COLUMNS = [
    "event_id",
    "episode_id",
    "scenario_id",
    "source_archive",
    "source_file",
    "source_line_or_step_index",
    "timestamp",
    "original_timestamp",
    "timestamp_assumption",
    "timestamp_missing",
    "step_type",
    "cmd",
    "hostname",
    "username",
    "is_labeled",
    "techniques",
    "techniques_raw",
    "tactics",
    "tactics_raw",
    "technique_names",
    "n_techniques",
    # C3-compatible fields
    "ioc",
    "ioc_type",
    "incident_stage",
    "asset_criticality",
    "local_occurrence",
    "cti_confidence",
    "freshness",
    "c3_threat_score",
    "investigation_priority",
]


def normalize_timestamps(series: pd.Series) -> pd.Series:
    """Parse to UTC; unparseable values become NaT (for backward compatibility)."""
    return pd.to_datetime(series, errors="coerce", utc=True)


def parse_step_timestamp(raw_ts: Any) -> tuple[str | None, str | None, bool]:
    """Parse timestamp string assuming UTC. Returns (iso_utc, original_str, is_missing)."""
    if raw_ts is None or (isinstance(raw_ts, str) and not raw_ts.strip()):
        return None, None, True
    raw_str = str(raw_ts).strip()
    try:
        # ISO format without tz is treated as UTC
        dt = datetime.fromisoformat(raw_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        else:
            dt = dt.astimezone(UTC)
        return dt.isoformat(), raw_str, False
    except ValueError:
        return None, raw_str, True


@dataclass
class QualityLog:
    whitespace_fixes: list[dict] = field(default_factory=list)
    invalid_techniques: list[dict] = field(default_factory=list)
    malformed_records: list[dict] = field(default_factory=list)
    missing_timestamps: list[dict] = field(default_factory=list)
    skipped_records: list[dict] = field(default_factory=list)


def clean_techniques(
    raw_val: Any,
    step_idx: int,
    episode_id: str,
    qlog: QualityLog,
) -> tuple[list[str], list[str]]:
    """Clean technique strings and validate with regex. Returns (valid_list, invalid_list)."""
    if not isinstance(raw_val, str) or not raw_val.strip():
        return [], []
    valid, invalid = [], []
    for part in raw_val.split(","):
        cleaned = part.strip()
        if part != cleaned:
            qlog.whitespace_fixes.append({
                "episode_id": episode_id,
                "step_index": step_idx,
                "field": "techniques",
                "raw_part": part,
                "cleaned_part": cleaned,
            })
        if not cleaned:
            continue
        if TECH_RX.match(cleaned):
            valid.append(cleaned)
        else:
            invalid.append(cleaned)
            qlog.invalid_techniques.append({
                "episode_id": episode_id,
                "step_index": step_idx,
                "raw_part": part,
                "invalid_value": cleaned,
            })
    return valid, invalid


def clean_tactics(
    raw_val: Any,
    step_idx: int,
    episode_id: str,
    qlog: QualityLog,
) -> list[str]:
    """Clean tactic strings stripping whitespace."""
    if not isinstance(raw_val, str) or not raw_val.strip():
        return []
    cleaned_tactics = []
    for part in raw_val.split(","):
        cleaned = " ".join(part.split())
        if part != cleaned:
            qlog.whitespace_fixes.append({
                "episode_id": episode_id,
                "step_index": step_idx,
                "field": "tactics",
                "raw_part": part,
                "cleaned_part": cleaned,
            })
        if cleaned:
            cleaned_tactics.append(cleaned)
    return cleaned_tactics


def extract_technique_names(
    metadata: dict[str, Any],
    step_idx: int,
    episode_id: str,
    qlog: QualityLog,
) -> list[str]:
    """Extract technique names, explicitly recovering malformed metadata keys."""
    names = []
    # Standard technique_name
    if "technique_name" in metadata:
        val = metadata["technique_name"]
        if isinstance(val, str):
            names.extend([x.strip() for x in val.split(",") if x.strip()])

    # Check for malformed keys (e.g. S1 step 23 typo)
    for k, v in metadata.items():
        if k.startswith("technique_name:") or ('"' in k and "technique_name" in k):
            recovered_name = k.replace("technique_name:", "").strip('": ')
            if isinstance(v, str):
                recovered_name = f"{recovered_name}: {v.strip('\" ')}"
            names.append(recovered_name)
            qlog.malformed_records.append({
                "episode_id": episode_id,
                "step_index": step_idx,
                "description": "Malformed technique_name JSON key with embedded quotes/colons recovered",
                "raw_key": k,
                "raw_val": v,
                "recovered_name": recovered_name,
            })
    return names


def normalize_step(
    raw_dict: dict[str, Any],
    step_idx: int,
    episode_id: str,
    scenario_id: str,
    source_archive: str,
    source_file: str,
    qlog: QualityLog,
) -> dict[str, Any]:
    """Normalize a single AttackMate raw JSON step dictionary."""
    event_id = f"{episode_id}-S{step_idx + 1:03d}"
    raw_ts = raw_dict.get("start-datetime")
    iso_ts, orig_ts, is_missing_ts = parse_step_timestamp(raw_ts)

    if is_missing_ts:
        qlog.missing_timestamps.append({
            "episode_id": episode_id,
            "step_index": step_idx,
            "raw_timestamp": raw_ts,
        })

    params = raw_dict.get("parameters") if isinstance(raw_dict.get("parameters"), dict) else {}
    metadata = params.get("metadata") if isinstance(params.get("metadata"), dict) else None

    techniques_raw = metadata.get("techniques") if metadata else None
    tactics_raw = metadata.get("tactics") if metadata else None

    valid_techs, _ = clean_techniques(techniques_raw, step_idx, episode_id, qlog)
    cleaned_tactics = clean_tactics(tactics_raw, step_idx, episode_id, qlog)
    technique_names = extract_technique_names(metadata, step_idx, episode_id, qlog) if metadata else []

    is_labeled = len(valid_techs) > 0

    return {
        "event_id": event_id,
        "episode_id": episode_id,
        "scenario_id": scenario_id,
        "source_archive": source_archive,
        "source_file": source_file,
        "source_line_or_step_index": step_idx,
        "timestamp": iso_ts,
        "original_timestamp": orig_ts,
        "timestamp_assumption": TIMESTAMP_ASSUMPTIONS.get(episode_id, "UTC"),
        "timestamp_missing": is_missing_ts,
        "step_type": raw_dict.get("type"),
        "cmd": str(raw_dict.get("cmd", "")),
        "hostname": params.get("hostname"),
        "username": params.get("username"),
        "is_labeled": is_labeled,
        "techniques": valid_techs,
        "techniques_raw": techniques_raw,
        "tactics": cleaned_tactics,
        "tactics_raw": tactics_raw,
        "technique_names": technique_names,
        "n_techniques": len(valid_techs),
        # C3-compatible fields (null in CAM-LDS)
        "ioc": None,
        "ioc_type": None,
        "incident_stage": None,
        "asset_criticality": None,
        "local_occurrence": None,  # Computed subsequently per episode
        "cti_confidence": None,
        "freshness": None,
        "c3_threat_score": None,
        "investigation_priority": None,
    }


def normalize_episode_steps(
    raw_steps: list[dict[str, Any]],
    episode_id: str,
    scenario_id: str,
    source_archive: str,
    source_file: str,
    qlog: QualityLog,
) -> list[dict[str, Any]]:
    """Normalize and sort all steps in an episode, computing local_occurrence."""
    events = []
    for idx, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            qlog.skipped_records.append({
                "episode_id": episode_id,
                "step_index": idx,
                "reason": "Step is not a JSON object",
                "raw_content": str(raw_step)[:100],
            })
            continue
        ev = normalize_step(
            raw_dict=raw_step,
            step_idx=idx,
            episode_id=episode_id,
            scenario_id=scenario_id,
            source_archive=source_archive,
            source_file=source_file,
            qlog=qlog,
        )
        events.append(ev)

    # Sort deterministically: missing timestamps last, then by timestamp UTC, tie-break by source step index
    def sort_key(e: dict[str, Any]):
        return (
            e["timestamp_missing"],
            e["timestamp"] or "",
            e["source_line_or_step_index"],
        )

    events.sort(key=sort_key)

    # Compute local_occurrence: per technique 1-indexed cumulative occurrence count
    # within this episode up to and including this step (stored as dict technique -> count)
    tech_counter: dict[str, int] = {}
    for ev in events:
        if ev["is_labeled"] and ev["techniques"]:
            occ_dict = {}
            for t in ev["techniques"]:
                tech_counter[t] = tech_counter.get(t, 0) + 1
                occ_dict[t] = tech_counter[t]
            ev["local_occurrence"] = occ_dict
        else:
            ev["local_occurrence"] = None

    return events


def events_to_dataframe(events: list[dict[str, Any]]) -> pd.DataFrame:
    """Convert list of event dicts to a pandas DataFrame."""
    df = pd.DataFrame(events)
    # Serialize list and dict columns to JSON strings for CSV compatibility
    for col in ["techniques", "tactics", "technique_names", "local_occurrence"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x)
    return df
