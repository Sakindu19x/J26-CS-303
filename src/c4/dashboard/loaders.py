"""Data loaders for C4 Streamlit Dashboard."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"
REPORTS_DIR = Path(__file__).resolve().parents[3] / "reports"

TIMELINES_PATH = PROCESSED_DIR / "attack_timelines.json"
SEQUENCES_PATH = PROCESSED_DIR / "attack_sequences.json"
DATA_QUALITY_PATH = REPORTS_DIR / "data_quality_report.json"
TACTIC_DISCREPANCY_PATH = REPORTS_DIR / "tactic_discrepancy_report.json"
WAZUH_CSV_PATH = PROCESSED_DIR / "wazuh_alerts_normalized.csv"


class MissingArtifactError(FileNotFoundError):
    """Raised when required preprocessed data files are missing."""
    pass


def check_required_artifacts() -> list[str]:
    """Check existence of essential preprocessed artifacts and return missing filenames."""
    missing = []
    if not TIMELINES_PATH.is_file():
        missing.append(str(TIMELINES_PATH.name))
    if not SEQUENCES_PATH.is_file():
        missing.append(str(SEQUENCES_PATH.name))
    if not DATA_QUALITY_PATH.is_file():
        missing.append(str(DATA_QUALITY_PATH.name))
    return missing


def load_dashboard_data() -> dict[str, Any]:
    """Load preprocessed artifacts for the dashboard without performing any preprocessing.

    Raises MissingArtifactError with actionable instructions if files are absent.
    """
    missing = check_required_artifacts()
    if missing:
        missing_str = ", ".join(missing)
        raise MissingArtifactError(
            f"Required processed files missing: [{missing_str}].\n"
            f"Please run the pipeline first by executing:\n"
            f"  python scripts/run_normalization.py\n"
            f"  python scripts/run_timeline_pipeline.py\n"
            f"  python scripts/run_samples_and_stats.py"
        )

    with open(TIMELINES_PATH, encoding="utf-8") as f:
        timelines = json.load(f)

    with open(SEQUENCES_PATH, encoding="utf-8") as f:
        sequences = json.load(f)

    with open(DATA_QUALITY_PATH, encoding="utf-8") as f:
        data_quality = json.load(f)

    tactic_discrepancies = {}
    if TACTIC_DISCREPANCY_PATH.is_file():
        with open(TACTIC_DISCREPANCY_PATH, encoding="utf-8") as f:
            tactic_discrepancies = json.load(f)

    wazuh_alerts_df = pd.DataFrame()
    if WAZUH_CSV_PATH.is_file():
        try:
            wazuh_alerts_df = pd.read_csv(WAZUH_CSV_PATH)
        except Exception:
            wazuh_alerts_df = pd.DataFrame()

    return {
        "timelines": timelines,
        "sequences": sequences,
        "data_quality": data_quality,
        "tactic_discrepancies": tactic_discrepancies,
        "wazuh_alerts_df": wazuh_alerts_df,
    }
