from datetime import datetime, timezone, timedelta
from cti_apis import enrich_ioc
from cti_confidence import calculate_cti_confidence
from feature_calculators import (
    calculate_freshness,
    calculate_local_evidence,
    get_asset_criticality,
    get_benign_penalty
)
from priority_mapper import get_incident_stage_score, get_mitre_severity
from scoring_engine import calculate_score, load_weights


def full_process(
    ioc: str,
    ioc_type: str,
    local_count: int = 5,
    max_local_count: int = 20,
    asset_level: str = "High",
    tactic: str = "command-and-control",
    technique_id: str = "T1071",
    days_old: int = 3,
    is_trusted: bool = False,
    weight_config: str = "balanced"
):
    print(f"\n[*] Processing IoC: {ioc} ({ioc_type}) | Weights: {weight_config}")
    print("-" * 60)

    # 1. Enrich with real CTI
    enrichment = enrich_ioc(ioc, ioc_type)
    vt_result = enrichment.get("virustotal")
    otx_result = enrichment.get("otx")

    # 2. Calculate all factors
    C = calculate_cti_confidence(vt_result, otx_result)
    F = calculate_freshness(datetime.now(timezone.utc) - timedelta(days=days_old))
    L = calculate_local_evidence(local_count, max_local_count)
    A = get_asset_criticality(asset_level)
    R = get_incident_stage_score(tactic)
    T = get_mitre_severity(technique_id)
    B = get_benign_penalty(is_trusted)

    # 3. Load weights and calculate score
    weights = load_weights(weight_config)
    result = calculate_score(C, F, L, A, R, T, B, weights=weights)

    # 4. Print output
    print("\n========== FINAL RESULT ==========")
    print(f"IoC              : {ioc}")
    print(f"Type             : {ioc_type}")
    print(f"Weight Config    : {weight_config}")
    print(f"Final Score      : {result['score']}")
    print(f"Priority         : {result['priority']}")
    print("\n--- Factor Values ---")
    print(f"C (CTI Confidence)   : {C:.3f}")
    print(f"F (Freshness)        : {F:.3f}")
    print(f"L (Local Evidence)   : {L:.3f}")
    print(f"A (Asset Criticality): {A:.3f}")
    print(f"R (Incident Stage)   : {R:.3f}")
    print(f"T (MITRE Severity)   : {T:.3f}")
    print(f"B (Benign Penalty)   : {B:.3f}")
    print("\n--- Score Breakdown ---")
    for k, v in result["breakdown"].items():
        print(f"{k:22}: {v}")
    print("==================================\n")

    return result


if __name__ == "__main__":
    full_process(
        ioc="185.220.101.1",
        ioc_type="ip",
        local_count=8,
        max_local_count=15,
        asset_level="Critical",
        tactic="command-and-control",
        technique_id="T1071",
        days_old=2,
        is_trusted=False,
        weight_config="balanced"
    )