"""Run complete CAM-LDS normalization pipeline for C4."""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import pandas as pd

from c4.data_loading import RAW_DIR
from c4.data_quality import build_data_quality_report, render_quality_markdown
from c4.normalization import (
    EPISODE_MAPPING,
    EPISODE_MAPPING_7EP,
    QualityLog,
    events_to_dataframe,
    normalize_episode_steps,
)
from c4.wazuh_enrichment import extract_wazuh_alerts

PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"


def run_pipeline(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    reports_dir: Path = REPORTS_DIR,
    episode_mapping: dict[str, str] | None = None,
) -> dict:
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    if episode_mapping is None:
        episode_mapping = EPISODE_MAPPING

    qlog = QualityLog()
    all_events = []
    all_wazuh_alerts = []
    episode_summaries = {}
    wazuh_summaries = {}

    for scenario_id, episode_id in episode_mapping.items():
        archive_name = f"{scenario_id}.zip"
        archive_path = raw_dir / archive_name
        if not archive_path.is_file():
            print(f"Warning: Archive {archive_path} not found. Skipping.")
            continue

        with zipfile.ZipFile(archive_path, "r") as zf:
            # 1. AttackMate Steps
            am_members = [n for n in zf.namelist() if n.endswith("attacker/logs/attackmate.json")]
            if not am_members:
                print(f"Warning: attackmate.json not found in {archive_name}")
                continue

            am_member = am_members[0]
            raw_steps = []
            with zf.open(am_member) as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        try:
                            raw_steps.append(json.loads(line))
                        except json.JSONDecodeError as exc:
                            qlog.skipped_records.append({
                                "episode_id": episode_id,
                                "step_index": len(raw_steps),
                                "reason": f"JSONDecodeError: {exc}",
                                "raw_content": str(line)[:100],
                            })

            norm_events = normalize_episode_steps(
                raw_steps=raw_steps,
                episode_id=episode_id,
                scenario_id=scenario_id,
                source_archive=archive_name,
                source_file=am_member,
                qlog=qlog,
            )
            all_events.extend(norm_events)

            # Attack Window
            valid_ts_events = [e for e in norm_events if e["timestamp"]]
            win_start_dt = datetime.fromisoformat(valid_ts_events[0]["timestamp"]) if valid_ts_events else None
            win_end_dt = datetime.fromisoformat(valid_ts_events[-1]["timestamp"]) if valid_ts_events else None

            labeled_count = sum(1 for e in norm_events if e["is_labeled"])
            unlabeled_count = len(norm_events) - labeled_count
            multi_count = sum(1 for e in norm_events if e["n_techniques"] > 1)

            episode_summaries[episode_id] = {
                "scenario_id": scenario_id,
                "source_archive": archive_name,
                "total_events": len(norm_events),
                "labeled_events": labeled_count,
                "unlabeled_events": unlabeled_count,
                "multi_technique_steps": multi_count,
                "window_start": win_start_dt.isoformat() if win_start_dt else None,
                "window_end": win_end_dt.isoformat() if win_end_dt else None,
            }

            # 2. Wazuh Alerts
            wazuh_members = [n for n in zf.namelist() if n.endswith("wazuh/logs/alerts/alerts.json")]
            if wazuh_members:
                wazuh_member = wazuh_members[0]
                alerts, w_stats = extract_wazuh_alerts(
                    zf=zf,
                    wazuh_member=wazuh_member,
                    episode_id=episode_id,
                    window_start=win_start_dt,
                    window_end=win_end_dt,
                )
                all_wazuh_alerts.extend(alerts)
                w_stats["in_window_with_rule_id"] = sum(1 for a in alerts if a["rule_id"])
                w_stats["in_window_with_mitre"] = sum(1 for a in alerts if a["wazuh_mitre_ids"] != "[]")
                wazuh_summaries[episode_id] = w_stats

    # Write normalized events
    events_df = events_to_dataframe(all_events)
    events_csv_path = processed_dir / "normalized_events.csv"
    events_json_path = processed_dir / "normalized_events.json"

    events_df.to_csv(events_csv_path, index=False, encoding="utf-8", lineterminator="\n")
    with open(events_json_path, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)

    # Write normalized Wazuh alerts
    wazuh_df = pd.DataFrame(all_wazuh_alerts)
    wazuh_csv_path = processed_dir / "wazuh_alerts_normalized.csv"
    wazuh_df.to_csv(wazuh_csv_path, index=False, encoding="utf-8", lineterminator="\n")

    # Build and write Data Quality Report
    dq_report = build_data_quality_report(
        episode_summaries=episode_summaries,
        qlog=qlog,
        wazuh_summaries=wazuh_summaries,
    )

    dq_json_path = reports_dir / "data_quality_report.json"
    dq_md_path = reports_dir / "data_quality_report.md"

    with open(dq_json_path, "w", encoding="utf-8") as f:
        json.dump(dq_report, f, indent=2, ensure_ascii=False)

    dq_md = render_quality_markdown(dq_report)
    with open(dq_md_path, "w", encoding="utf-8") as f:
        f.write(dq_md)

    print("Pipeline Execution Complete:")
    print(f"  Normalized Events: {len(all_events)} -> {events_csv_path}")
    print(f"  Wazuh In-Window Alerts: {len(all_wazuh_alerts)} -> {wazuh_csv_path}")
    print(f"  Quality Report: {dq_json_path} and {dq_md_path}")
    for ep, s in episode_summaries.items():
        print(f"  {ep} ({s['scenario_id']}): total={s['total_events']}, labeled={s['labeled_events']}, unlabeled={s['unlabeled_events']}")

    return dq_report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run normalization pipeline.")
    parser.add_argument("--episodes", choices=["4", "7", "all"], default="4", help="Episodes to process: 4 (E1-E4) or 7 (E1-E7)")
    parser.add_argument("--processed-dir", "--out-dir", dest="processed_dir", type=Path, default=PROCESSED_DIR, help="Output directory for processed data")
    parser.add_argument("--reports-dir", type=Path, default=REPORTS_DIR, help="Output directory for reports")
    args = parser.parse_args()

    ep_map = EPISODE_MAPPING_7EP if args.episodes in ("7", "all") else EPISODE_MAPPING
    run_pipeline(processed_dir=args.processed_dir, reports_dir=args.reports_dir, episode_mapping=ep_map)
