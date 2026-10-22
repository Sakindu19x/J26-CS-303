import json
import os
from investigation_queue import create_investigation_queue


def load_events():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation_set.json")
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_all_weights():
    events = load_events()
    configs = ["balanced", "cti_focused", "context_focused"]

    all_results = {}

    for config in configs:
        print(f"\n{'='*70}")
        print(f"Running configuration: {config.upper()}")
        print(f"{'='*70}")

        ranked = create_investigation_queue(events, weight_config=config)
        all_results[config] = ranked

        print(f"\nTop 3 for {config}:")
        for item in ranked[:3]:
            print(f"  Rank {item['rank']}: {item['ioc']} → {item['score']} ({item['priority']})")

    # Save full comparison
    output_path = os.path.join(os.path.dirname(__file__), "..", "data", "weight_comparison.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n[*] Full comparison saved to: {output_path}")

    # Simple summary table
    print("\n" + "="*80)
    print("COMPARISON SUMMARY (Score of each IoC under different weights)")
    print("="*80)

    # Get all unique IoCs
    iocs = [item["ioc"] + " (" + item.get("description", "")[:30] + ")" for item in all_results["balanced"]]
    
    # Better clean summary
    print(f"{'IoC':<45} {'Balanced':<12} {'CTI Focus':<12} {'Context Focus':<12}")
    print("-"*80)

    for i in range(len(all_results["balanced"])):
        ioc = all_results["balanced"][i]["ioc"]
        bal = all_results["balanced"][i]["score"]
        cti = all_results["cti_focused"][i]["score"]
        ctx = all_results["context_focused"][i]["score"]
        print(f"{ioc:<45} {bal:<12} {cti:<12} {ctx:<12}")


if __name__ == "__main__":
    compare_all_weights()