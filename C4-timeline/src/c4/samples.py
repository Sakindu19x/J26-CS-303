"""Next-step sequence sample generation for C4 forensic investigation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from c4.mitre_reference import to_parent_technique_set
from c4.normalization import EPISODE_MAPPING

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
DEFAULT_SEQUENCES_PATH = PROCESSED_DIR / "attack_sequences.json"
DEFAULT_SAMPLES_JSON_PATH = PROCESSED_DIR / "next_technique_samples.json"
DEFAULT_SAMPLES_CSV_PATH = PROCESSED_DIR / "next_technique_samples.csv"


def build_samples_for_sequence(
    items: list[dict[str, Any]],
    episode_id: str,
    scenario_id: str,
    variant: str,
    granularity: str,
    min_prefix_length: int = 1,
) -> list[dict[str, Any]]:
    """Build next-step prediction samples from a single sequence within an episode.

    Sample k:
      input = first k items of the sequence
      target = item k+1
    """
    if len(items) <= min_prefix_length:
        return []

    samples = []
    gran_short = "ful" if granularity == "full" else "par"
    var_short = "col" if variant == "collapsed" else "raw"

    for k in range(min_prefix_length, len(items)):
        input_items = items[:k]
        target_item = items[k]
        last_input_item = input_items[-1]

        # Extract event IDs
        if variant == "collapsed":
            input_event_ids = [it.get("event_ids", []) for it in input_items]
            target_event_id = target_item.get("event_ids", [])
        else:
            input_event_ids = [it.get("event_id") for it in input_items]
            target_event_id = target_item.get("event_id")

        # Map techniques according to granularity
        if granularity == "parent":
            input_technique_sets = [to_parent_technique_set(it.get("techniques", [])) for it in input_items]
            current_technique_set = to_parent_technique_set(last_input_item.get("techniques", []))
            target_technique_set = to_parent_technique_set(target_item.get("techniques", []))
        else:
            input_technique_sets = [sorted(list(it.get("techniques", []))) for it in input_items]
            current_technique_set = sorted(list(last_input_item.get("techniques", [])))
            target_technique_set = sorted(list(target_item.get("techniques", [])))

        current_tactics = list(last_input_item.get("tactics", []))
        unlabeled_skipped_target = target_item.get("unlabeled_steps_skipped_before", 0)

        is_self_repeat = bool(current_technique_set == target_technique_set)
        is_multi_input = len(current_technique_set) > 1
        is_multi_target = len(target_technique_set) > 1
        has_unlabeled_gap = unlabeled_skipped_target > 0

        flags = {
            "is_self_repeat": is_self_repeat,
            "is_multi_technique_input": is_multi_input,
            "is_multi_technique_target": is_multi_target,
            "has_unlabeled_gap_before_target": has_unlabeled_gap,
        }

        sample_id = f"{episode_id}-{var_short}-{gran_short}-K{k:02d}"

        sample = {
            "sample_id": sample_id,
            "episode_id": episode_id,
            "scenario_id": scenario_id,
            "variant": variant,
            "granularity": granularity,
            "prefix_length": k,
            "input_item_event_ids": input_event_ids,
            "input_technique_sets": input_technique_sets,
            "current_technique_set": current_technique_set,
            "current_tactics": current_tactics,
            "target_event_id": target_event_id,
            "target_technique_set": target_technique_set,
            "unlabeled_steps_skipped_before_target": unlabeled_skipped_target,
            "flags": flags,
        }
        samples.append(sample)

    return samples


def generate_all_samples(
    sequences_data: dict[str, Any],
    min_prefix_length: int = 1,
) -> list[dict[str, Any]]:
    """Generate samples for all 2x2 combinations (collapsed/raw x full/parent)."""
    all_samples = []
    episodes_dict = sequences_data.get("episodes", {})

    # Invert mapping to get scenario_id from episode_id
    ep_to_scenario = {v: k for k, v in EPISODE_MAPPING.items()}

    for ep_id, ep_content in episodes_dict.items():
        scenario_id = ep_to_scenario.get(ep_id, f"scenario_{ep_id}")

        for variant in ["collapsed", "raw"]:
            items = ep_content.get(variant, [])
            for granularity in ["full", "parent"]:
                samples = build_samples_for_sequence(
                    items=items,
                    episode_id=ep_id,
                    scenario_id=scenario_id,
                    variant=variant,
                    granularity=granularity,
                    min_prefix_length=min_prefix_length,
                )
                all_samples.extend(samples)

    return all_samples


def export_samples(
    samples: list[dict[str, Any]],
    json_path: Path = DEFAULT_SAMPLES_JSON_PATH,
    csv_path: Path = DEFAULT_SAMPLES_CSV_PATH,
) -> None:
    """Export samples list to both JSON and flattened CSV."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)

    flat_rows = []
    for s in samples:
        row = {
            "sample_id": s["sample_id"],
            "episode_id": s["episode_id"],
            "scenario_id": s["scenario_id"],
            "variant": s["variant"],
            "granularity": s["granularity"],
            "prefix_length": s["prefix_length"],
            "input_item_event_ids": json.dumps(s["input_item_event_ids"]),
            "input_technique_sets": json.dumps(s["input_technique_sets"]),
            "current_technique_set": json.dumps(s["current_technique_set"]),
            "current_tactics": json.dumps(s["current_tactics"]),
            "target_event_id": json.dumps(s["target_event_id"]) if isinstance(s["target_event_id"], list) else s["target_event_id"],
            "target_technique_set": json.dumps(s["target_technique_set"]),
            "unlabeled_steps_skipped_before_target": s["unlabeled_steps_skipped_before_target"],
            "is_self_repeat": s["flags"]["is_self_repeat"],
            "is_multi_technique_input": s["flags"]["is_multi_technique_input"],
            "is_multi_technique_target": s["flags"]["is_multi_technique_target"],
            "has_unlabeled_gap_before_target": s["flags"]["has_unlabeled_gap_before_target"],
        }
        flat_rows.append(row)

    df = pd.DataFrame(flat_rows)
    df.to_csv(csv_path, index=False, encoding="utf-8")
