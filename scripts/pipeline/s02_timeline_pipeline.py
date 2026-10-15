"""Timeline reconstruction and ATT&CK sequence generation runner for C4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from c4.attack_sequence import build_all_sequences, export_sequences
from c4.episodes import EpisodeManager
from c4.timeline import export_timelines, reconstruct_all_timelines
from c4.timeline_validation import (
    render_timeline_validation_markdown,
    validate_timelines_and_sequences,
)

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def run_timeline_pipeline(
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
) -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    norm_events_path = processed_dir / "normalized_events.json"
    if not norm_events_path.is_file():
        raise FileNotFoundError(f"Normalized events not found at {norm_events_path}. Run run_normalization.py first.")

    with open(norm_events_path, encoding="utf-8") as f:
        events = json.load(f)

    # 1. Episode Management
    ep_mgr = EpisodeManager(events)
    episodes = ep_mgr.list_episodes()
    events_by_episode = {ep.episode_id: ep.events for ep in episodes}

    # 2. Timeline Reconstruction
    timelines = reconstruct_all_timelines(events_by_episode)
    timeline_json_path = processed_dir / "attack_timelines.json"
    timeline_csv_path = processed_dir / "attack_timelines.csv"
    export_timelines(timelines, timeline_json_path, timeline_csv_path)

    # 3. ATT&CK Sequences (raw and collapsed)
    sequences_data = build_all_sequences(timelines)
    sequences_json_path = processed_dir / "attack_sequences.json"
    export_sequences(sequences_data, sequences_json_path)

    # 4. Validation Report
    val_report = validate_timelines_and_sequences(timelines, sequences_data)
    val_json_path = reports_dir / "timeline_validation_report.json"
    val_md_path = reports_dir / "timeline_validation_report.md"

    with open(val_json_path, "w", encoding="utf-8") as f:
        json.dump(val_report, f, indent=2, ensure_ascii=False)

    val_md = render_timeline_validation_markdown(val_report)
    with open(val_md_path, "w", encoding="utf-8") as f:
        f.write(val_md)

    print("Timeline Pipeline Execution Complete:")
    print(f"  Attack Timelines: {timeline_json_path} and {timeline_csv_path}")
    print(f"  Attack Sequences: {sequences_json_path}")
    print(f"  Validation Report: {val_json_path} and {val_md_path}")
    for ep_id, ep_info in val_report["episodes"].items():
        print(f"  {ep_id}: events={ep_info['total_events']}, raw_seq={ep_info['raw_sequence_length']}, collapsed_seq={ep_info['collapsed_sequence_length']}, distinct_techs={ep_info['distinct_techniques']}")

    return val_report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run timeline pipeline.")
    parser.add_argument("--processed-dir", "--out-dir", dest="processed_dir", type=Path, default=PROCESSED_DIR, help="Output directory for processed data")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR, help="Output directory for reports")
    args = parser.parse_args()

    run_timeline_pipeline(processed_dir=args.processed_dir, reports_dir=args.reports_dir)
