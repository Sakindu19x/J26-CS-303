import json
import os
from typing import List, Dict, Any
from full_pipeline_test import full_process


def _get(item: Dict[str, Any], *keys, default=None):
    for k in keys:
        if k in item and item[k] is not None:
            return item[k]
    return default


def load_trusted_sources() -> Dict[str, Any]:
    path = os.path.join(os.path.dirname(__file__), "..", "config", "trusted_sources.json")
    if not os.path.exists(path):
        return {"ips": [], "domains": [], "ip_prefixes": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_known_trusted(ioc: str, ioc_type: str) -> bool:
    """
    Check static trusted infrastructure list.
    Used to strengthen benign penalty for known-safe sources.
    """
    trusted = load_trusted_sources()
    ioc = (ioc or "").strip().lower()
    ioc_type = (ioc_type or "").strip().lower()

    if ioc_type == "ip":
        if ioc in [x.lower() for x in trusted.get("ips", [])]:
            return True
        for prefix in trusted.get("ip_prefixes", []):
            if ioc.startswith(prefix.lower()):
                return True

    if ioc_type in ("domain", "url"):
        # extract host-like token for urls
        host = ioc
        if "://" in host:
            host = host.split("://", 1)[1]
        host = host.split("/", 1)[0]
        host = host.split(":", 1)[0]

        for d in trusted.get("domains", []):
            d = d.lower()
            if host == d or host.endswith("." + d):
                return True

    return False


def create_investigation_queue(
    ioc_list: List[Dict[str, Any]],
    weight_config: str = "balanced"
) -> List[Dict]:
    """
    Process multiple IoCs and return a ranked investigation queue.
    Accepts evaluation_set field names and internal field names.
    Auto-applies trusted source list.
    """

    results = []

    for item in ioc_list:
        ioc = _get(item, "ioc", "ioc_value")
        ioc_type = _get(item, "ioc_type", "type", default="ip")

        local_count = int(_get(item, "local_count", default=3))
        max_local_count = int(_get(item, "max_local_count", default=50))
        asset_level = _get(item, "asset_level", "asset_criticality", default="Medium")
        tactic = _get(item, "tactic", "mitre_tactic", default="discovery")
        technique_id = _get(item, "technique_id", "mitre_technique", default="T1595")
        days_old = int(_get(item, "days_old", "age_days", default=5))

        is_trusted = _get(item, "is_trusted", "trusted", default=False)
        if isinstance(is_trusted, str):
            is_trusted = is_trusted.lower().strip() in ("1", "true", "yes")
        is_trusted = bool(is_trusted) or is_known_trusted(str(ioc), str(ioc_type))

        result = full_process(
            ioc=ioc,
            ioc_type=ioc_type,
            local_count=local_count,
            max_local_count=max_local_count,
            asset_level=asset_level,
            tactic=tactic,
            technique_id=technique_id,
            days_old=days_old,
            is_trusted=is_trusted,
            weight_config=weight_config
        )

        results.append({
            "ioc": ioc,
            "ioc_type": ioc_type,
            "score": result["score"],
            "priority": result["priority"],
            "breakdown": result["breakdown"],
            "weight_config": weight_config,
            "asset_level": asset_level,
            "tactic": tactic,
            "technique_id": technique_id,
            "days_old": days_old,
            "is_trusted": is_trusted,
            "local_count": local_count,
        })

    ranked = sorted(results, key=lambda x: x["score"], reverse=True)
    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx
    return ranked


def print_queue(ranked_list: List[Dict]):
    print("\n" + "=" * 75)
    print("RANKED INVESTIGATION QUEUE")
    print("=" * 75)
    print(f"{'Rank':<6} {'Score':<8} {'Priority':<10} {'Type':<8} {'IoC'}")
    print("-" * 75)
    for item in ranked_list:
        print(f"{item['rank']:<6} {item['score']:<8} {item['priority']:<10} {item['ioc_type']:<8} {item['ioc']}")
    print("=" * 75 + "\n")
