"""Runner for next-technique sample generation and sequence statistics."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c4.mitre_reference import (
    DEFAULT_PROCESSED_REF_PATH,
    DEFAULT_STIX_PATH,
    build_technique_tactic_reference,
    detect_tactic_discrepancies,
    load_technique_reference,
)
from c4.samples import export_samples, generate_all_samples
from c4.sequence_statistics import compute_sequence_statistics, export_sequence_statistics

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def run_samples_and_stats() -> dict:
    sequences_json_path = PROCESSED_DIR / "attack_sequences.json"
    timeline_json_path = PROCESSED_DIR / "attack_timelines.json"

    if not sequences_json_path.is_file():
        raise FileNotFoundError(f"Missing {sequences_json_path}. Run run_timeline_pipeline.py first.")

    with open(sequences_json_path, encoding="utf-8") as f:
        sequences_data = json.load(f)

    with open(timeline_json_path, encoding="utf-8") as f:
        timelines_data = json.load(f)

    # 1. Ensure MITRE Reference is parsed and built
    if not DEFAULT_PROCESSED_REF_PATH.is_file() and DEFAULT_STIX_PATH.is_file():
        print(f"Building technique reference from {DEFAULT_STIX_PATH}...")
        ref_table = build_technique_tactic_reference(DEFAULT_STIX_PATH, DEFAULT_PROCESSED_REF_PATH)
    else:
        ref_table = load_technique_reference(DEFAULT_PROCESSED_REF_PATH)

    print(f"Technique Reference Loaded: {len(ref_table)} techniques.")

    # 2. Check technique/tactic discrepancies against CAM-LDS events
    all_events = [ev for ep_events in timelines_data.values() for ev in ep_events]
    discrepancy_report = detect_tactic_discrepancies(all_events, ref_table)

    disc_path = REPORTS_DIR / "tactic_discrepancy_report.json"
    with open(disc_path, "w", encoding="utf-8") as f:
        json.dump(discrepancy_report, f, indent=2, ensure_ascii=False)
    print(f"Tactic Discrepancy Report: {len(discrepancy_report['discrepancies'])} discrepancies -> {disc_path}")

    # 3. Generate Next-Step Samples (2x2 combinations)
    samples = generate_all_samples(sequences_data, min_prefix_length=1)
    samples_json_path = PROCESSED_DIR / "next_technique_samples.json"
    samples_csv_path = PROCESSED_DIR / "next_technique_samples.csv"
    export_samples(samples, samples_json_path, samples_csv_path)
    print(f"Next-Step Samples: {len(samples)} samples -> {samples_json_path} and {samples_csv_path}")

    # 4. Export LOEO folds definition
    loeo_folds_path = PROCESSED_DIR / "loeo_folds.json"
    episodes = sorted(list(sequences_data.get("episodes", {}).keys()))
    loeo_folds = [
        {
            "fold_id": f"fold_{idx + 1}",
            "test_episode": ep,
            "training_episodes": [e for e in episodes if e != ep],
        }
        for idx, ep in enumerate(episodes)
    ]
    with open(loeo_folds_path, "w", encoding="utf-8") as f:
        json.dump(loeo_folds, f, indent=2, ensure_ascii=False)
    print(f"LOEO Folds: {len(loeo_folds)} folds -> {loeo_folds_path}")

    # 5. Compute Sequence Statistics & Coverage
    stats_data = compute_sequence_statistics(samples, sequences_data)
    stats_json_path = REPORTS_DIR / "sequence_statistics.json"
    stats_md_path = REPORTS_DIR / "sequence_statistics.md"
    export_sequence_statistics(stats_data, stats_json_path, stats_md_path)
    print(f"Sequence Statistics Report: {stats_json_path} and {stats_md_path}")

    return stats_data


if __name__ == "__main__":
    run_samples_and_stats()
