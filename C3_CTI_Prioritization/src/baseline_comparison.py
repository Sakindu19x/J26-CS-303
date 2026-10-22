import json
import os
from investigation_queue import create_investigation_queue
from cti_confidence import calculate_cti_confidence
from cti_apis import enrich_ioc


def _get(event, *keys, default=None):
    for k in keys:
        if k in event and event[k] is not None:
            return event[k]
    return default


def unweighted_cti_score(vt_result, otx_result):
    """
    Baseline: Conventional unweighted CTI enrichment.
    Only uses CTI confidence; local context is ignored.
    """
    C = calculate_cti_confidence(vt_result, otx_result)
    score = C * 100

    if score >= 75:
        priority = "Critical"
    elif score >= 50:
        priority = "High"
    elif score >= 25:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "score": round(score, 2),
        "priority": priority,
        "method": "unweighted_cti",
        "cti_confidence": round(C, 3),
    }


def run_baseline_comparison():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation_set_v2.json")
    with open(data_path, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Contextual path: exact same pipeline as process_from_file.py
    contextual_ranked = create_investigation_queue(events, weight_config="balanced")
    contextual_by_ioc = {}
    # Handle duplicate IoCs by order index
    for idx, item in enumerate(contextual_ranked):
        # store by (ioc, original order later); first build map by rank list aligned to events
        pass

    # Better: process events in original order for baseline, and map contextual by running queue then matching sequence
    # create_investigation_queue sorts by score, so rebuild contextual in input order using full queue results keyed by composite

    # Re-run mapping in input order by calling queue internal logic once and indexing
    # We'll compute contextual from ranked list by matching all fields
    from full_pipeline_test import full_process

    results = []

    print("\n" + "=" * 80)
    print("BASELINE COMPARISON: Unweighted CTI  vs  Contextual Scoring")
    print("=" * 80)

    for event in events:
        ioc = _get(event, "ioc", "ioc_value")
        ioc_type = _get(event, "ioc_type", "type", default="ip")
        local_count = int(_get(event, "local_count", default=3))
        max_local_count = int(_get(event, "max_local_count", default=50))
        asset_level = _get(event, "asset_level", "asset_criticality", default="Medium")
        tactic = _get(event, "tactic", "mitre_tactic", default="discovery")
        technique_id = _get(event, "technique_id", "mitre_technique", default="T1595")
        days_old = int(_get(event, "days_old", "age_days", default=5))
        is_trusted = _get(event, "is_trusted", "trusted", default=False)
        if isinstance(is_trusted, str):
            is_trusted = is_trusted.lower().strip() in ("1", "true", "yes")

        # Enrich once
        enrichment = enrich_ioc(ioc, ioc_type)
        vt = enrichment.get("virustotal")
        otx = enrichment.get("otx")

        # Baseline
        baseline = unweighted_cti_score(vt, otx)

        # Contextual: exact same function used by investigation queue
        contextual = full_process(
            ioc=ioc,
            ioc_type=ioc_type,
            local_count=local_count,
            max_local_count=max_local_count,
            asset_level=asset_level,
            tactic=tactic,
            technique_id=technique_id,
            days_old=days_old,
            is_trusted=bool(is_trusted),
            weight_config="balanced",
        )

        results.append({
            "ioc": ioc,
            "ioc_type": ioc_type,
            "baseline_score": baseline["score"],
            "baseline_priority": baseline["priority"],
            "contextual_score": contextual["score"],
            "contextual_priority": contextual["priority"],
            "asset_level": asset_level,
            "tactic": tactic,
            "days_old": days_old,
            "is_trusted": bool(is_trusted),
            "local_count": local_count,
        })

        print(f"\nIoC: {ioc}")
        print(f"  Baseline (Unweighted CTI) : {baseline['score']:6.2f}  → {baseline['priority']}")
        print(f"  Contextual (Our Model)    : {contextual['score']:6.2f}  → {contextual['priority']}")

    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "baseline_vs_contextual.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[*] Comparison saved to: {output_path}")


if __name__ == "__main__":
    run_baseline_comparison()
