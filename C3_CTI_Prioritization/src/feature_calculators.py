import math
from datetime import datetime, timezone
from typing import Optional


def calculate_freshness(last_seen: datetime, lambda_decay: float = 0.05) -> float:
    """
    F = e^(-λ * Δt)
    Δt is measured in days.
    Returns value between 0.0 and 1.0
    """
    now = datetime.now(timezone.utc)

    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=timezone.utc)

    delta_seconds = (now - last_seen).total_seconds()
    delta_days = delta_seconds / 86400.0

    freshness = math.exp(-lambda_decay * delta_days)
    return max(0.0, min(1.0, freshness))


def calculate_local_evidence(count: int, max_count: int) -> float:
    """
    L = log(1 + n) / log(1 + max_n)
    Returns value between 0.0 and 1.0
    """
    if max_count <= 0:
        return 0.0
    if count < 0:
        count = 0

    return math.log(1 + count) / math.log(1 + max_count)


def get_asset_criticality(level: str) -> float:
    """
    A = Asset Criticality
    Mapping:
        Low      → 0.25
        Medium   → 0.50
        High     → 0.75
        Critical → 1.00
    """
    mapping = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.75,
        "critical": 1.00
    }
    return mapping.get(level.lower().strip(), 0.50)  # default Medium


def get_benign_penalty(is_trusted: bool, trust_score: float = 1.0) -> float:
    """
    B = Benign / Trusted Infrastructure Penalty
    is_trusted = True  → full penalty
    is_trusted = False → 0.0
    """
    if is_trusted:
        return max(0.0, min(1.0, trust_score))
    return 0.0


def normalize_value(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Simple helper to keep values inside 0-1 range"""
    return max(min_val, min(max_val, value))