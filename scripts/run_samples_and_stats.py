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

import shutil

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def run_samples_and_stats(
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    sequences_json_path = processed_dir / "attack_sequences.json"
    timeline_json_path = processed_dir / "attack_timelines.json"

    if not sequences_json_path.is_file():
        raise FileNotFoundError(f"Missing {sequences_json_path}. Run run_timeline_pipeline.py first.")

    with open(sequences_json_path, encoding="utf-8") as f:
        sequences_data = json.load(f)

    with open(timeline_json_path, encoding="utf-8") as f:
        timelines_data = json.load(f)

    # 1. Ensure MITRE Reference is parsed and built
    ref_out_path = processed_dir / "technique_tactic_reference.json"
    if not ref_out_path.is_file():
        if DEFAULT_PROCESSED_REF_PATH.is_file():
            shutil.copyfile(DEFAULT_PROCESSED_REF_PATH, ref_out_path)
            ref_table = load_technique_reference(ref_out_path)
        elif DEFAULT_STIX_PATH.is_file():
            print(f"Building technique reference from {DEFAULT_STIX_PATH}...")
            ref_table = build_technique_tactic_reference(DEFAULT_STIX_PATH, ref_out_path)
        else:
            raise FileNotFoundError(f"Missing STIX file at {DEFAULT_STIX_PATH}")
    else:
        ref_table = load_technique_reference(ref_out_path)

    print(f"Technique Reference Loaded: {len(ref_table)} techniques.")

    # 2. Check technique/tactic discrepancies against CAM-LDS events
    all_events = [ev for ep_events in timelines_data.values() for ev in ep_events]
    discrepancy_report = detect_tactic_discrepancies(all_events, ref_table)

    disc_path = reports_dir / "tactic_discrepancy_report.json"
    with open(disc_path, "w", encoding="utf-8") as f:
        json.dump(discrepancy_report, f, indent=2, ensure_ascii=False)
    print(f"Tactic Discrepancy Report: {len(discrepancy_report['discrepancies'])} discrepancies -> {disc_path}")

    # 3. Generate Next-Step Samples (2x2 combinations)
    samples = generate_all_samples(sequences_data, min_prefix_length=1)
    samples_json_path = processed_dir / "next_technique_samples.json"
    samples_csv_path = processed_dir / "next_technique_samples.csv"
    export_samples(samples, samples_json_path, samples_csv_path)
    print(f"Next-Step Samples: {len(samples)} samples -> {samples_json_path} and {samples_csv_path}")

    # 4. Export LOEO folds definition with leakage assertions
    loeo_folds_path = processed_dir / "loeo_folds.json"
    episodes = sorted(list(sequences_data.get("episodes", {}).keys()))
    loeo_folds = [
        {
            "fold_id": f"fold_{idx + 1}",
            "test_episode": ep,
            "training_episodes": [e for e in episodes if e != ep],
        }
        for idx, ep in enumerate(episodes)
    ]

    # Leakage assertions
    for fold in loeo_folds:
        assert fold["test_episode"] not in fold["training_episodes"], (
            f"Data leakage detected in {fold['fold_id']}: {fold['test_episode']} present in training!"
        )
    for s in samples:
        assert s["episode_id"] in episodes, f"Unknown episode_id in sample {s['sample_id']}"
        # verify no sample crosses an episode boundary
        for eid in s.get("event_ids", []):
            assert eid.startswith(s["episode_id"] + "-"), (
                f"Sample {s['sample_id']} crosses episode boundary: event {eid}"
            )

    with open(loeo_folds_path, "w", encoding="utf-8") as f:
        json.dump(loeo_folds, f, indent=2, ensure_ascii=False)
    print(f"LOEO Folds: {len(loeo_folds)} folds -> {loeo_folds_path}")

    # 5. Compute Sequence Statistics & Coverage
    stats_data = compute_sequence_statistics(samples, sequences_data)
    stats_json_path = reports_dir / "sequence_statistics.json"
    stats_md_path = reports_dir / "sequence_statistics.md"
    export_sequence_statistics(stats_data, stats_json_path, stats_md_path)
    print(f"Sequence Statistics Report: {stats_json_path} and {stats_md_path}")

    return stats_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run samples and stats pipeline.")
    parser.add_argument("--processed-dir", "--out-dir", dest="processed_dir", type=Path, default=PROCESSED_DIR, help="Output directory for processed data")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR, help="Output directory for reports")
    args = parser.parse_args()

    run_samples_and_stats(processed_dir=args.processed_dir, reports_dir=args.reports_dir)
