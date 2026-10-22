import math
from datetime import datetime, timezone
from typing import Dict, Optional
import json
import os


def load_weights(config_name: str = "balanced") -> Dict[str, float]:
    """
    Load weight configuration from config/weights.json
    """
    weights_path = os.path.join(os.path.dirname(__file__), "..", "config", "weights.json")

    with open(weights_path, "r", encoding="utf-8") as f:
        all_weights = json.load(f)

    if config_name not in all_weights:
        print(f"[!] Weight config '{config_name}' not found. Using 'balanced'.")
        config_name = "balanced"

    return all_weights[config_name]


def calculate_score(
    cti_confidence: float,
    freshness: float,
    local_evidence: float,
    asset_criticality: float,
    incident_stage: float,
    mitre_severity: float,
    benign_penalty: float,
    weights: Optional[Dict[str, float]] = None
) -> dict:
    """
    S = wC*C + wF*F + wL*L + wA*A + wR*R + wT*T - wB*B
    """

    if weights is None:
        weights = load_weights("balanced")

    w_c = weights.get("w_c", 0.25)
    w_f = weights.get("w_f", 0.15)
    w_l = weights.get("w_l", 0.20)
    w_a = weights.get("w_a", 0.15)
    w_r = weights.get("w_r", 0.10)
    w_t = weights.get("w_t", 0.10)
    w_b = weights.get("w_b", 0.05)

    raw_score = (
        w_c * cti_confidence +
        w_f * freshness +
        w_l * local_evidence +
        w_a * asset_criticality +
        w_r * incident_stage +
        w_t * mitre_severity -
        w_b * benign_penalty
    )

    # Normalize to 0-100
    score = max(0.0, min(100.0, raw_score * 100))

    # Priority mapping
    if score >= 75:
        priority = "Critical"
    elif score >= 50:
        priority = "High"
    elif score >= 25:
        priority = "Medium"
    else:
        priority = "Low"

    breakdown = {
        "CTI_Confidence": round(w_c * cti_confidence * 100, 2),
        "Freshness": round(w_f * freshness * 100, 2),
        "Local_Evidence": round(w_l * local_evidence * 100, 2),
        "Asset_Criticality": round(w_a * asset_criticality * 100, 2),
        "Incident_Stage": round(w_r * incident_stage * 100, 2),
        "MITRE_Severity": round(w_t * mitre_severity * 100, 2),
        "Benign_Penalty": round(-w_b * benign_penalty * 100, 2),
        "Final_Score": round(score, 2),
        "Priority": priority
    }

    return {
        "score": round(score, 2),
        "priority": priority,
        "breakdown": breakdown,
        "weights_used": weights
    }