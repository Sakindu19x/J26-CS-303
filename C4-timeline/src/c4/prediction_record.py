"""Explainable Prediction Record Generator (FR4-FR7, NFR2, NFR3, NFR6).

Provides deterministic generation and validation of structured next-step
attack prediction records for Component 4.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "schemas" / "c4_prediction_record.schema.json"

_COMPILED_SCHEMA: jsonschema.Draft7Validator | None = None


def get_schema_validator() -> jsonschema.Draft7Validator:
    global _COMPILED_SCHEMA
    if _COMPILED_SCHEMA is None:
        if not SCHEMA_PATH.is_file():
            raise FileNotFoundError(f"Missing schema: {SCHEMA_PATH}")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
        _COMPILED_SCHEMA = jsonschema.Draft7Validator(schema_data)
    return _COMPILED_SCHEMA


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object to deterministic canonical JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_canonical(obj: Any) -> str:
    """Compute SHA-256 of canonical JSON serialization."""
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def generate_explanation_text(
    level: str,
    status: str,
    current_set: list[str],
    ranked_candidates: list[dict[str, Any]],
    training_episodes: list[str],
    reliability_banner: str,
    tie_flags: dict[str, Any],
    support: dict[str, Any] | None = None,
) -> str:
    """Build deterministic template explanation strictly from record fields."""
    cur_str = ", ".join(sorted(current_set)) if current_set else "EMPTY"
    parts: list[str] = []

    if status == "ok":
        top = ranked_candidates[0] if ranked_candidates else None
        top_id = top["candidate_id"] if top else "None"
        top_name = f" ({top['candidate_name']})" if top and top.get("candidate_name") else ""
        prob = top["score"] if top else 0.0
        num = top["numerator"] if top else 0
        den = top["denominator"] if top else 0
        ep_ids = ", ".join(top["supporting_episode_ids"]) if top and top["supporting_episode_ids"] else "none"

        parts.append(
            f"State [{cur_str}] recognized in training episodes ({', '.join(training_episodes)}). "
            f"Top next-{level} prediction is {top_id}{top_name} with estimated transition probability "
            f"{prob:.4f} based on {num:.2f}/{den:.2f} transition weight across episodes [{ep_ids}]."
        )
    elif status in ("unseen_state", "fallback"):
        top = ranked_candidates[0] if ranked_candidates else None
        top_id = top["candidate_id"] if top else "None"
        top_name = f" ({top['candidate_name']})" if top and top.get("candidate_name") else ""
        prob = top["score"] if top else 0.0
        parts.append(
            f"State [{cur_str}] was not observed in training episodes ({', '.join(training_episodes)}) "
            f"(zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. "
            f"Top candidate is {top_id}{top_name} with training frequency share {prob:.4f}. "
            f"Note: this score is an unconditional empirical frequency share, not a conditional transition probability."
        )
    else:
        parts.append(f"State [{cur_str}] resulted in status '{status}'.")

    if support and support.get("caution"):
        parts.append(f"Support Context: {support.get('caution_text')}")

    if tie_flags.get("tie_at_top1"):
        parts.append(f"Notice: Top-1 boundary is tied among candidates: {tie_flags.get('tied_candidates', [])}.")
    elif tie_flags.get("tie_at_top3_boundary"):
        parts.append(f"Notice: Top-3 rank boundary is tied with alternative candidates: {tie_flags.get('tied_candidates', [])}.")

    parts.append(f"Empirical Reliability Context: {reliability_banner}")
    return " ".join(parts)


def build_prediction_record(
    schema_version: str,
    prediction_type: str,
    sample_id: str,
    episode_id: str,
    event_index: int | None,
    last_timestamp: str | None,
    previous_supporting_techniques: list[str],
    current_technique_set: list[str],
    current_tactic_set: list[str],
    incident_stage: str | None,
    affected_asset: str | None,
    c3_fields: dict[str, Any],
    model_type: str,
    model_file_sha256: str,
    model_file_relpath: str,
    training_episodes: list[str],
    transition_count: float,
    set_weighting_rule: str,
    tie_break_rule: str,
    technique_prediction: dict[str, Any] | None,
    tactic_prediction: dict[str, Any] | None,
    raw_input_events: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble complete explainable prediction record matching schema specification."""
    input_obj = {
        "sample_id": sample_id,
        "episode_id": episode_id,
        "event_index": event_index,
        "last_timestamp": last_timestamp,
        "previous_supporting_techniques": list(previous_supporting_techniques),
        "current_technique_set": list(current_technique_set),
        "current_tactic_set": list(current_tactic_set),
        "incident_stage": incident_stage,
        "affected_asset": affected_asset,
        "c3_fields": {
            "threat_score": c3_fields.get("threat_score"),
            "investigation_priority": c3_fields.get("investigation_priority"),
            "asset_criticality": c3_fields.get("asset_criticality"),
            "cti_confidence": c3_fields.get("cti_confidence"),
            "freshness": c3_fields.get("freshness"),
            "ioc": c3_fields.get("ioc"),
            "ioc_type": c3_fields.get("ioc_type"),
        },
    }

    model_obj = {
        "model_type": model_type,
        "model_file_sha256": model_file_sha256,
        "model_file_relpath": model_file_relpath,
        "training_episodes": sorted(list(training_episodes)),
        "transition_count": float(transition_count),
        "set_weighting_rule": set_weighting_rule,
        "tie_break_rule": tie_break_rule,
    }

    record_id_payload = {
        "schema_version": schema_version,
        "prediction_type": prediction_type,
        "input": input_obj,
        "model": model_obj,
    }
    record_id = sha256_canonical(record_id_payload)
    input_events_sha256 = sha256_canonical(raw_input_events)

    record: dict[str, Any] = {
        "schema_version": schema_version,
        "record_id": record_id,
        "prediction_type": prediction_type,
        "input": input_obj,
        "model": model_obj,
        "technique_prediction": technique_prediction,
        "tactic_prediction": tactic_prediction,
        "input_events_sha256": input_events_sha256,
    }

    # Compute record_sha256 over all fields except record_sha256 itself
    record_sha256 = sha256_canonical(record)
    record["record_sha256"] = record_sha256

    # Validate against JSON schema
    validator = get_schema_validator()
    validator.validate(record)

    return record
