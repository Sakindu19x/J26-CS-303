from datetime import datetime, timezone, timedelta
from scoring_engine import calculate_score
from feature_calculators import (
    calculate_freshness,
    calculate_local_evidence,
    get_asset_criticality,
    get_benign_penalty
)
from priority_mapper import get_incident_stage_score, get_mitre_severity
from cti_confidence import calculate_cti_confidence, get_cti_summary


def process_ioc(
    ioc_value: str,
    ioc_type: str,
    local_count: int,
    max_local_count: int,
    asset_level: str,
    tactic: str,
    technique_id: str,
    last_seen: datetime,
    is_trusted: bool = False,
    vt_result: dict = None,
    otx_result: dict = None
):
    """
    Full pipeline for one IoC
    """

    # 1. Calculate each factor
    C = calculate_cti_confidence(vt_result, otx_result)
    F = calculate_freshness(last_seen)
    L = calculate_local_evidence(local_count, max_local_count)
    A = get_asset_criticality(asset_level)
    R = get_incident_stage_score(tactic)
    T = get_mitre_severity(technique_id)
    B = get_benign_penalty(is_trusted)

    # 2. Calculate final score
    result = calculate_score(
        cti_confidence=C,
        freshness=F,
        local_evidence=L,
        asset_criticality=A,
        incident_stage=R,
        mitre_severity=T,
        benign_penalty=B
    )

    # 3. Prepare readable output
    output = {
        "ioc": ioc_value,
        "ioc_type": ioc_type,
        "score": result["score"],
        "priority": result["priority"],
        "breakdown": result["breakdown"],
        "factors": {
            "C_CTI_Confidence": round(C, 3),
            "F_Freshness": round(F, 3),
            "L_Local_Evidence": round(L, 3),
            "A_Asset_Criticality": round(A, 3),
            "R_Incident_Stage": round(R, 3),
            "T_MITRE_Severity": round(T, 3),
            "B_Benign_Penalty": round(B, 3)
        },
        "cti_summary": get_cti_summary(vt_result, otx_result)
    }

    return output


# ==============================================
# Example test (you can change these values)
# ==============================================
if __name__ == "__main__":

    # Example 1: High risk IoC
    example_vt = {
        "malicious": 45,
        "suspicious": 8,
        "total": 70
    }

    example_otx = {
        "pulse_count": 12,
        "reputation": -5
    }

    result = process_ioc(
        ioc_value="185.220.101.45",
        ioc_type="ip",
        local_count=7,
        max_local_count=15,
        asset_level="Critical",
        tactic="command-and-control",
        technique_id="T1071",
        last_seen=datetime.now(timezone.utc) - timedelta(days=2),
        is_trusted=False,
        vt_result=example_vt,
        otx_result=example_otx
    )

    print("=" * 60)
    print("CTI PRIORITIZATION RESULT")
    print("=" * 60)
    print(f"IoC            : {result['ioc']}")
    print(f"Type           : {result['ioc_type']}")
    print(f"Final Score    : {result['score']}")
    print(f"Priority       : {result['priority']}")
    print("-" * 60)
    print("Factor Values:")
    for k, v in result["factors"].items():
        print(f"  {k:25}: {v}")
    print("-" * 60)
    print("Score Breakdown:")
    for k, v in result["breakdown"].items():
        print(f"  {k:25}: {v}")
    print("=" * 60)