from typing import Optional, Dict, Any


def calculate_cti_confidence(
    vt_result: Optional[Dict[str, Any]] = None,
    otx_result: Optional[Dict[str, Any]] = None
) -> float:
    """
    Improved CTI Confidence (C) calculation
    Range: 0.0 – 1.0
    """

    vt_score = 0.0
    otx_score = 0.0
    vt_available = False
    otx_available = False
    vt_malicious = False
    otx_malicious = False

    # ========== VirusTotal ==========
    if vt_result and not vt_result.get("not_found"):
        vt_available = True
        malicious = vt_result.get("malicious", 0)
        suspicious = vt_result.get("suspicious", 0)
        total = vt_result.get("total", 1)

        if total > 0:
            # Weighted: malicious counts fully, suspicious counts half
            vt_score = (malicious + (suspicious * 0.5)) / total
            vt_malicious = malicious >= 3  # at least 3 engines

    # ========== OTX ==========
    if otx_result and not otx_result.get("not_found"):
        otx_available = True
        pulse_count = otx_result.get("pulse_count", 0)
        reputation = otx_result.get("reputation", 0)

        # Pulse count scoring (capped)
        pulse_score = min(pulse_count / 15.0, 1.0)

        # Reputation scoring (negative reputation is bad)
        rep_score = 0.0
        if reputation < 0:
            rep_score = min(abs(reputation) / 10.0, 1.0)

        otx_score = max(pulse_score, rep_score)
        otx_malicious = pulse_count >= 3 or reputation < -1

    # ========== Combine ==========
    if not vt_available and not otx_available:
        return 0.05  # Almost no intelligence

    scores = []
    if vt_available:
        scores.append(vt_score)
    if otx_available:
        scores.append(otx_score)

    base_score = sum(scores) / len(scores)

    # Agreement bonus
    if vt_available and otx_available:
        if vt_malicious and otx_malicious:
            agreement_bonus = 0.20
        elif vt_malicious or otx_malicious:
            agreement_bonus = 0.08
        else:
            agreement_bonus = 0.0
    else:
        agreement_bonus = 0.05  # only one source

    # Conflict penalty
    conflict_penalty = 0.0
    if vt_available and otx_available:
        if (vt_malicious and not otx_malicious) or (otx_malicious and not vt_malicious):
            conflict_penalty = 0.12

    final = base_score + agreement_bonus - conflict_penalty
    final = max(0.0, min(1.0, final))

    return round(final, 3)


def get_cti_summary(vt_result: Optional[Dict] = None, otx_result: Optional[Dict] = None) -> Dict:
    """Readable summary for explainability"""
    confidence = calculate_cti_confidence(vt_result, otx_result)

    summary = {
        "confidence_score": confidence,
        "virus_total": "No data",
        "otx": "No data",
        "agreement": "No data"
    }

    if vt_result and not vt_result.get("not_found"):
        malicious = vt_result.get("malicious", 0)
        total = vt_result.get("total", 0)
        summary["virus_total"] = f"{malicious}/{total} engines flagged malicious"

    if otx_result and not otx_result.get("not_found"):
        pulses = otx_result.get("pulse_count", 0)
        summary["otx"] = f"{pulses} pulses found"

    # Agreement
    vt_mal = False
    otx_mal = False

    if vt_result and not vt_result.get("not_found"):
        vt_mal = vt_result.get("malicious", 0) >= 3
    if otx_result and not otx_result.get("not_found"):
        otx_mal = otx_result.get("pulse_count", 0) >= 3

    if vt_result and otx_result:
        if vt_mal and otx_mal:
            summary["agreement"] = "Both sources agree → Malicious"
        elif not vt_mal and not otx_mal:
            summary["agreement"] = "Both sources agree → Not clearly malicious"
        else:
            summary["agreement"] = "Sources conflict"

    return summary