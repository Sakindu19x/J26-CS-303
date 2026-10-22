import json
import os
from investigation_queue import create_investigation_queue, print_queue
from output_formatter import format_for_c4, save_c4_output, print_c4_preview


def load_events(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        events = json.load(f)
    return events


def main(weight_config: str = "balanced"):
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation_set_v2.json")

    print(f"[*] Loading events from file...")
    print(f"[*] Using weight configuration: {weight_config}\n")

    events = load_events(data_path)
    print(f"[*] Loaded {len(events)} events\n")

    # Create ranked queue
    ranked = create_investigation_queue(events, weight_config=weight_config)

    # Show ranking
    print_queue(ranked)

    # Format for C4
    c4_ready = format_for_c4(ranked, original_events=events)
    print_c4_preview(c4_ready)

    # Save internal ranked results
    output_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        f"ranked_results_{weight_config}.json"
    )
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ranked, f, indent=2)
    print(f"[*] Internal results saved to: {output_path}")

    # Save C4 output
    save_c4_output(c4_ready, filename=f"c3_to_c4_output_{weight_config}.json")


if __name__ == "__main__":
    main(weight_config="balanced")