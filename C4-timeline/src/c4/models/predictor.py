"""Common prediction interface for C4 next-step ATT&CK technique prediction."""
from __future__ import annotations

from typing import Any

from c4.mitre_reference import get_official_tactics, load_technique_reference
from c4.models.frequency import FrequencyBaseline
from c4.models.markov import MarkovModel

PROBABILITY_ESTIMATE_DISCLAIMER = (
    "Probabilities are empirical estimates derived from observed training sequences and not guarantees."
)


def predict_next(
    sequence_items: list[dict[str, Any]],
    model: MarkovModel | FrequencyBaseline,
    method: str = "markov",
    k: int = 3,
    ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Predict the next ATT&CK techniques using strictly the last sequence item as current state.

    Parameters
    ----------
    sequence_items : list[dict]
        Chronological list of sequence items. Only the last item sequence_items[-1]
        is used as the current state.
    model : MarkovModel | FrequencyBaseline
        Fitted prediction model.
    method : str
        Prediction method identifier: 'markov' or 'frequency'.
    k : int
        Number of top candidates to return.
    ref : dict | None
        Optional preloaded MITRE technique-to-tactic reference dictionary.

    Returns
    -------
    dict
        Structured prediction output containing method, config, status, candidates,
        supporting counts, official tactics, and disclaimers.
    """
    if method not in {"markov", "frequency"}:
        raise ValueError(f"Unknown prediction method '{method}'. Expected 'markov' or 'frequency'.")

    if ref is None:
        ref = load_technique_reference()

    warnings: list[str] = []

    if not sequence_items:
        last_item: dict[str, Any] | None = None
        current_techniques: list[str] = []
        last_event_id: str | None = None
        last_timestamp: str | None = None
        warnings.append("Empty sequence input: no sequence items provided.")
    else:
        last_item = sequence_items[-1]
        current_techniques = list(last_item.get("techniques", []))

        # Extract last event ID
        if "event_ids" in last_item and last_item["event_ids"]:
            eids = last_item["event_ids"]
            last_event_id = eids[-1] if isinstance(eids, list) else str(eids)
        elif "event_id" in last_item:
            last_event_id = str(last_item["event_id"])
        else:
            last_event_id = None

        # Extract last timestamp
        last_timestamp = last_item.get("timestamp") or last_item.get("end_timestamp")

    # Execute model prediction
    if method == "markov":
        if not isinstance(model, MarkovModel):
            raise TypeError(f"Method 'markov' requires a MarkovModel instance, got {type(model).__name__}.")
        raw_pred = model.predict(current_techniques, k=k)
    else:
        if not isinstance(model, FrequencyBaseline):
            raise TypeError(f"Method 'frequency' requires a FrequencyBaseline instance, got {type(model).__name__}.")
        raw_pred = model.predict(k=k)

    status = raw_pred["status"]
    candidates_raw = raw_pred["candidates"]  # list of (technique, probability) tuples

    if status == "insufficient_evidence":
        warnings.append(
            f"No outgoing transitions observed in training for techniques: {raw_pred.get('members_unseen', current_techniques)}."
        )
    elif status == "empty_input":
        warnings.append("No input techniques provided.")
    elif status == "empty_training":
        warnings.append("Model was not trained on any transitions.")

    # Format predicted candidates with probabilities
    formatted_candidates = []
    official_tactics: dict[str, dict[str, Any]] = {}

    for tid, prob in candidates_raw:
        formatted_candidates.append({
            "technique": tid,
            "probability": round(prob, 6),
        })
        # Look up official tactics from reference
        tacs = get_official_tactics([tid], ref=ref)
        official_tactics[tid] = {
            "official_tactics": tacs,
            "source": "mitre_attack_reference_v16_1",
            "is_derived": True,
        }

    return {
        "method": method,
        "config": model.config,
        "status": status,
        "current_techniques": current_techniques,
        "predicted_candidates": formatted_candidates,
        "official_tactics": official_tactics,
        "supporting_transition_count": raw_pred["number_of_supporting_step_transitions"],
        "supporting_evidence": raw_pred["supporting_evidence"],
        "warnings": warnings,
        "last_observed_event_id": last_event_id,
        "last_observed_timestamp": last_timestamp,
        "disclaimer": PROBABILITY_ESTIMATE_DISCLAIMER,
    }
