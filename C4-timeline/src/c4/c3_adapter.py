"""Component 3 Telemetry Ingestion Adapter (FR8, NFR5).

Ingests C3-formatted investigation telemetry events and adapts them to
Component 4 timelines and attack sequences.
"""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
from collections import defaultdict
from typing import Any

VALID_PRIORITIES = {"Low", "Medium", "High", "Critical", None}

# Configurable Field Alias Table (NFR5 loose coupling)
FIELD_ALIASES: dict[str, list[str]] = {
    "event_id": ["event_id", "id", "uuid"],
    "episode_id": ["episode_id", "scenario_id", "incident_id"],
    "timestamp": ["timestamp", "time", "datetime", "observed_at"],
    "technique": ["technique", "techniques", "technique_id"],
    "tactic": ["tactic", "tactics", "tactic_name"],
    "incident_stage": ["incident_stage", "stage", "kill_chain_phase"],
    "affected_asset": ["affected_asset", "host", "hostname", "asset"],
    "asset_criticality": ["asset_criticality", "criticality", "host_criticality"],
    "ioc": ["ioc", "indicator", "observable"],
    "ioc_type": ["ioc_type", "indicator_type", "observable_type"],
    "local_occurrence": ["local_occurrence", "count", "frequency"],
    "cti_confidence": ["cti_confidence", "confidence", "threat_intel_confidence"],
    "freshness": ["freshness", "age_seconds", "recency"],
    "threat_score": ["threat_score", "c3_threat_score", "score"],
    "investigation_priority": ["investigation_priority", "priority", "triage_priority"],
}

KNOWN_INPUT_KEYS = {alias for aliases in FIELD_ALIASES.values() for alias in aliases}


class C3AdapterError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_canonical(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def parse_to_utc_iso(ts_str: str) -> str:
    """Parse timestamp string into canonical ISO-8601 UTC string."""
    cleaned = ts_str.strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"

    try:
        dt = datetime.datetime.fromisoformat(cleaned)
    except Exception as exc:
        raise C3AdapterError("ERR_INVALID_TIMESTAMP", f"Unable to parse ISO timestamp: {ts_str} ({exc})")

    if dt.tzinfo is None:
        # Default to UTC if naive
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        dt = dt.astimezone(datetime.timezone.utc)

    return dt.isoformat()


def resolve_field(raw: dict[str, Any], canonical_name: str) -> Any:
    for alias in FIELD_ALIASES.get(canonical_name, [canonical_name]):
        if alias in raw:
            return raw[alias]
    return None


def adapt_c3_event(raw_event: dict[str, Any], input_index: int = 0) -> dict[str, Any]:
    """Adapt a single C3 event envelope into C4 canonical telemetry structure.

    Parameters
    ----------
    raw_event : dict
        Raw incoming C3 event.
    input_index : int
        Index in input stream for deterministic tie-breaking on identical timestamps.

    Returns
    -------
    dict
        Canonical C4 adapted event.
    """
    if not isinstance(raw_event, dict):
        raise C3AdapterError("ERR_SCHEMA_VALIDATION_FAILURE", f"Expected dictionary event, got {type(raw_event).__name__}")

    # Deep copy and cryptographic hash (NFR3)
    raw_deep_copy = copy.deepcopy(raw_event)
    raw_sha256 = sha256_canonical(raw_deep_copy)

    # Required fields
    episode_id = resolve_field(raw_event, "episode_id")
    if not episode_id or not str(episode_id).strip():
        raise C3AdapterError("ERR_MISSING_REQUIRED_FIELD", "Missing required field 'episode_id'")
    episode_id = str(episode_id).strip()

    raw_ts = resolve_field(raw_event, "timestamp")
    if raw_ts is None or not str(raw_ts).strip():
        raise C3AdapterError("ERR_MISSING_REQUIRED_FIELD", "Missing required field 'timestamp'")
    raw_ts_str = str(raw_ts).strip()
    utc_ts = parse_to_utc_iso(raw_ts_str)

    # Priority enum check
    prio = resolve_field(raw_event, "investigation_priority")
    if prio is not None and prio not in VALID_PRIORITIES:
        raise C3AdapterError(
            "ERR_INVALID_PRIORITY_ENUM",
            f"Invalid investigation priority '{prio}'. Must be one of {sorted([p for p in VALID_PRIORITIES if p])}"
        )

    # Technique handling (string -> list or list -> list)
    tech_raw = resolve_field(raw_event, "technique")
    techniques: list[str] = []
    if tech_raw is not None:
        if isinstance(tech_raw, list):
            techniques = [str(t).strip() for t in tech_raw if str(t).strip()]
        elif isinstance(tech_raw, str):
            parts = [t.strip() for t in tech_raw.replace(";", ",").split(",")]
            techniques = [p for p in parts if p]

    # Tactic handling
    tactic_raw = resolve_field(raw_event, "tactic")
    tactics: list[str] = []
    if tactic_raw is not None:
        if isinstance(tactic_raw, list):
            tactics = [str(t).strip() for t in tactic_raw if str(t).strip()]
        elif isinstance(tactic_raw, str):
            parts = [t.strip() for t in tactic_raw.replace(";", ",").split(",")]
            tactics = [p for p in parts if p]

    # Unknown extra fields
    extra_fields: dict[str, Any] = {}
    for k, v in raw_event.items():
        if k not in KNOWN_INPUT_KEYS:
            extra_fields[k] = v

    event_id = resolve_field(raw_event, "event_id")
    if not event_id:
        event_id = f"{episode_id}-IDX{input_index:04d}"

    is_labeled = len(techniques) > 0
    inclusion_status = "INCLUDED_IN_SEQUENCE" if is_labeled else "EXCLUDED_FROM_SEQUENCE"
    exclusion_reason = None if is_labeled else "UNLABELED_STEP"

    adapted: dict[str, Any] = {
        "event_id": str(event_id),
        "episode_id": episode_id,
        "input_index": input_index,
        "timestamp": utc_ts,
        "original_timestamp": raw_ts_str,
        "techniques": sorted(techniques),
        "tactics": sorted(tactics),
        "is_labeled": is_labeled,
        "inclusion_status": inclusion_status,
        "exclusion_reason": exclusion_reason,
        "incident_stage": resolve_field(raw_event, "incident_stage"),
        "affected_asset": resolve_field(raw_event, "affected_asset"),
        "asset_criticality": resolve_field(raw_event, "asset_criticality"),
        "ioc": resolve_field(raw_event, "ioc"),
        "ioc_type": resolve_field(raw_event, "ioc_type"),
        "local_occurrence": resolve_field(raw_event, "local_occurrence"),
        "cti_confidence": resolve_field(raw_event, "cti_confidence"),
        "freshness": resolve_field(raw_event, "freshness"),
        "threat_score": resolve_field(raw_event, "threat_score"),
        "investigation_priority": prio,
        "extra": extra_fields,
        "c3_event_sha256": raw_sha256,
        "original_event_copy": raw_deep_copy,
    }
    return adapted


def adapt_c3_stream(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Ingest, validate, sort, and segment a stream of C3 telemetry events.

    Returns structured dict containing:
    - episodes: dict of episode_id -> {timeline, sequences: {raw, collapsed}}
    - duplicates: list of detected duplicates
    - rejected: list of rejected malformed events with error codes
    """
    ep_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    duplicates: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seen_fingerprints: set[tuple[str, str, str]] = set()

    for idx, raw_ev in enumerate(events):
        try:
            adapted = adapt_c3_event(raw_ev, input_index=idx)
        except C3AdapterError as err:
            rejected.append({"input_index": idx, "error_code": err.code, "message": err.message, "raw_event": raw_ev})
            continue

        # Duplicate check: (episode_id, timestamp, tuple(sorted(techniques)))
        fp = (adapted["episode_id"], adapted["timestamp"], ",".join(adapted["techniques"]))
        if fp in seen_fingerprints and adapted["is_labeled"]:
            duplicates.append({
                "input_index": idx,
                "event_id": adapted["event_id"],
                "episode_id": adapted["episode_id"],
                "timestamp": adapted["timestamp"],
                "reason_code": "DUPLICATE_EVENT",
            })
            # Flag on adapted object
            adapted["duplicate_flag"] = True
        else:
            if adapted["is_labeled"]:
                seen_fingerprints.add(fp)
            adapted["duplicate_flag"] = False

        ep_events[adapted["episode_id"]].append(adapted)

    # Build timelines and sequences per episode (FR2 chronological segmentation)
    episodes_result: dict[str, Any] = {}
    for ep_id in sorted(ep_events.keys()):
        # Sort timeline by (timestamp ASC, input_index ASC)
        timeline = sorted(ep_events[ep_id], key=lambda e: (e["timestamp"], e["input_index"]))

        # Build raw sequence (labeled events only)
        raw_seq: list[dict[str, Any]] = []
        for ev in timeline:
            if ev["is_labeled"]:
                raw_seq.append({
                    "event_id": ev["event_id"],
                    "timestamp": ev["timestamp"],
                    "techniques": list(ev["techniques"]),
                    "tactics": list(ev["tactics"]),
                })

        # Build collapsed sequence (merge consecutive items with identical technique sets)
        collapsed_seq: list[dict[str, Any]] = []
        for itm in raw_seq:
            if not collapsed_seq or collapsed_seq[-1]["techniques"] != itm["techniques"]:
                collapsed_seq.append({
                    "event_ids": [itm["event_id"]],
                    "timestamp": itm["timestamp"],
                    "techniques": list(itm["techniques"]),
                    "tactics": list(itm["tactics"]),
                })
            else:
                collapsed_seq[-1]["event_ids"].append(itm["event_id"])

        episodes_result[ep_id] = {
            "timeline": timeline,
            "raw": raw_seq,
            "collapsed": collapsed_seq,
        }

    return {
        "episodes": episodes_result,
        "duplicates": duplicates,
        "rejected": rejected,
    }


def export_normalized_events_to_c3(normalized_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Serialise Stage 1 normalized_events as C3-style telemetry events."""
    c3_events: list[dict[str, Any]] = []
    for ev in normalized_events:
        c3_ev = {
            "event_id": ev.get("event_id"),
            "episode_id": ev.get("episode_id"),
            "timestamp": ev.get("original_timestamp") or ev.get("timestamp"),
            "technique": ev.get("techniques", []),
            "tactic": ev.get("tactics", []),
            "incident_stage": ev.get("incident_stage"),
            "affected_asset": ev.get("hostname"),
            "asset_criticality": ev.get("asset_criticality"),
            "ioc": ev.get("ioc"),
            "ioc_type": ev.get("ioc_type"),
            "local_occurrence": ev.get("local_occurrence"),
            "cti_confidence": ev.get("cti_confidence"),
            "freshness": ev.get("freshness"),
            "threat_score": ev.get("c3_threat_score"),
            "investigation_priority": ev.get("investigation_priority"),
        }
        c3_events.append(c3_ev)
    return c3_events
