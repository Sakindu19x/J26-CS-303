from typing import List, Dict, Any
from datetime import datetime, timezone
import json
import os


def get_recommendation(priority: str, tactic: str = None) -> str:
    if priority == "Critical":
        if tactic == "command-and-control":
            return "Immediate investigation. Isolate affected host and review C2 communications."
        if tactic == "exfiltration":
            return "Immediate investigation. Contain the asset and inspect outbound transfers."
        return "Immediate investigation required. Consider containment of the affected asset."
    if priority == "High":
        return "Prioritize investigation. Review related logs and network connections."
    if priority == "Medium":
        return "Schedule investigation. Monitor for further activity."
    return "Low priority. Keep under observation."


def format_for_c4(ranked_results: List[Dict[str, Any]], original_events: List[Dict] = None) -> Dict[str, Any]:
    """
    Final structured output for C4.
    """
    event_lookup = {}
    if original_events:
        for ev in original_events:
            event_lookup[ev.get("ioc", "")] = ev

    items = []
    for item in ranked_results:
        ioc = item.get("ioc")
        original = event_lookup.get(ioc, {})
        priority = item.get("priority", "Low")
        tactic = original.get("tactic")

        items.append({
            "rank": item.get("rank"),
            "event_id": original.get("event_id"),
            "ioc": ioc,
            "ioc_type": item.get("ioc_type"),
            "threat_score": item.get("score"),
            "priority": priority,
            "score_breakdown": item.get("breakdown", {}),
            "tactic": tactic,
            "technique_id": original.get("technique_id"),
            "asset_level": original.get("asset_level"),
            "local_count": original.get("local_count"),
            "days_old": original.get("days_old"),
            "is_trusted": original.get("is_trusted", False),
            "recommended_action": get_recommendation(priority, tactic),
            "source_component": "C3"
        })

    return {
        "component": "C3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_iocs": len(items),
        "priority_counts": {
            "Critical": sum(1 for x in items if x["priority"] == "Critical"),
            "High": sum(1 for x in items if x["priority"] == "High"),
            "Medium": sum(1 for x in items if x["priority"] == "Medium"),
            "Low": sum(1 for x in items if x["priority"] == "Low")
        },
        "investigation_queue": items
    }


def save_c4_output(formatted_results: Dict[str, Any], filename: str = "c3_to_c4_output.json"):
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(formatted_results, f, indent=2)

    print(f"[*] C4-ready output saved to: {output_path}")
    return output_path


def print_c4_preview(formatted_results: Dict[str, Any]):
    print("\n" + "=" * 75)
    print("C3 → C4 OUTPUT PREVIEW")
    print("=" * 75)
    print(f"Total IoCs : {formatted_results.get('total_iocs')}")
    print(f"Counts     : {formatted_results.get('priority_counts')}")
    print("-" * 75)

    for item in formatted_results.get("investigation_queue", []):
        print(f"Rank {item['rank']}: {item['ioc']} ({item['ioc_type']})")
        print(f"  Score       : {item['threat_score']}")
        print(f"  Priority    : {item['priority']}")
        print(f"  Action      : {item['recommended_action']}")
        print("-" * 55)

    print("=" * 75 + "\n")