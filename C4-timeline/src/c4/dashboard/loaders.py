"""Data loaders for C4 Streamlit Dashboard."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]


class MissingArtifactError(FileNotFoundError):
    """Raised when required preprocessed data files are missing."""
    pass


def check_required_artifacts(episodes: int = 4) -> list[str]:
    """Check existence of essential preprocessed artifacts and return missing filenames."""
    if episodes == 7:
        processed_dir = REPO_ROOT / "data" / "processed_7ep"
        reports_dir = REPO_ROOT / "reports" / "7ep"
    else:
        processed_dir = REPO_ROOT / "data" / "processed"
        reports_dir = REPO_ROOT / "reports"

    timelines_path = processed_dir / "attack_timelines.json"
    sequences_path = processed_dir / "attack_sequences.json"
    data_quality_path = reports_dir / "data_quality_report.json"

    missing = []
    if not timelines_path.is_file():
        missing.append(str(timelines_path.name))
    if not sequences_path.is_file():
        missing.append(str(sequences_path.name))
    if not data_quality_path.is_file():
        missing.append(str(data_quality_path.name))
    return missing


def load_dashboard_data(episodes: int = 4) -> dict[str, Any]:
    """Load preprocessed artifacts for the dashboard without performing any preprocessing.

    Raises MissingArtifactError with actionable instructions if files are absent.
    """
    if episodes == 7:
        processed_dir = REPO_ROOT / "data" / "processed_7ep"
        reports_dir = REPO_ROOT / "reports" / "7ep"
    else:
        processed_dir = REPO_ROOT / "data" / "processed"
        reports_dir = REPO_ROOT / "reports"

    timelines_path = processed_dir / "attack_timelines.json"
    sequences_path = processed_dir / "attack_sequences.json"
    data_quality_path = reports_dir / "data_quality_report.json"
    tactic_discrepancy_path = reports_dir / "tactic_discrepancy_report.json"
    wazuh_csv_path = processed_dir / "wazuh_alerts_normalized.csv"

    missing = check_required_artifacts(episodes=episodes)
    if missing:
        missing_str = ", ".join(missing)
        raise MissingArtifactError(
            f"Required processed files missing: [{missing_str}].\n"
            f"Please run the pipeline first by executing:\n"
            f"  python scripts/pipeline/s01_normalize_events.py\n"
            f"  python scripts/pipeline/s02_timeline_pipeline.py\n"
            f"  python scripts/pipeline/s03_samples_and_stats.py"
        )

    with open(timelines_path, encoding="utf-8") as f:
        timelines = json.load(f)

    with open(sequences_path, encoding="utf-8") as f:
        sequences = json.load(f)

    with open(data_quality_path, encoding="utf-8") as f:
        data_quality = json.load(f)

    tactic_discrepancies = {}
    if tactic_discrepancy_path.is_file():
        with open(tactic_discrepancy_path, encoding="utf-8") as f:
            tactic_discrepancies = json.load(f)

    wazuh_alerts_df = pd.DataFrame()
    if wazuh_csv_path.is_file():
        try:
            wazuh_alerts_df = pd.read_csv(wazuh_csv_path)
        except Exception:
            wazuh_alerts_df = pd.DataFrame()

    return {
        "timelines": timelines,
        "sequences": sequences,
        "data_quality": data_quality,
        "tactic_discrepancies": tactic_discrepancies,
        "wazuh_alerts_df": wazuh_alerts_df,
    }
