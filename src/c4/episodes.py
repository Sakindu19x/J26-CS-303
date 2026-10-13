"""Episode management: strictly isolates individual attack simulation runs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_PROCESSED_JSON = Path(__file__).resolve().parents[2] / "data" / "processed" / "normalized_events.json"


@dataclass
class Episode:
    """Represents an isolated, self-contained attack simulation run."""
    episode_id: str
    scenario_id: str
    source_archive: str
    window_start: str | None
    window_end: str | None
    event_count: int
    labeled_count: int
    unlabeled_count: int
    events: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "scenario_id": self.scenario_id,
            "source_archive": self.source_archive,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "event_count": self.event_count,
            "labeled_count": self.labeled_count,
            "unlabeled_count": self.unlabeled_count,
        }


class EpisodeManager:
    """Manages collection of discrete episodes, guaranteeing episodes are never merged."""

    def __init__(self, events: list[dict[str, Any]] | None = None):
        self._episodes: dict[str, Episode] = {}
        if events is not None:
            self.load_events(events)

    def load_events(self, events: list[dict[str, Any]]) -> None:
        """Partition events strictly by episode_id into discrete Episode containers."""
        grouped: dict[str, list[dict[str, Any]]] = {}
        for ev in events:
            ep_id = ev.get("episode_id", "UNKNOWN")
            grouped.setdefault(ep_id, []).append(ev)

        self._episodes.clear()
        for ep_id, ep_events in grouped.items():
            first_ev = ep_events[0]
            scenario_id = first_ev.get("scenario_id", "")
            source_archive = first_ev.get("source_archive", "")

            valid_ts = [e["timestamp"] for e in ep_events if e.get("timestamp")]
            win_start = min(valid_ts) if valid_ts else None
            win_end = max(valid_ts) if valid_ts else None

            labeled_count = sum(1 for e in ep_events if e.get("is_labeled"))
            unlabeled_count = len(ep_events) - labeled_count

            self._episodes[ep_id] = Episode(
                episode_id=ep_id,
                scenario_id=scenario_id,
                source_archive=source_archive,
                window_start=win_start,
                window_end=win_end,
                event_count=len(ep_events),
                labeled_count=labeled_count,
                unlabeled_count=unlabeled_count,
                events=ep_events,
            )

    def list_episodes(self) -> list[Episode]:
        """Return list of all registered episodes."""
        return list(self._episodes.values())

    def get_episode(self, episode_id: str) -> Episode | None:
        """Retrieve an episode by its ID without merging or mutating."""
        return self._episodes.get(episode_id)


_DEFAULT_MANAGER: EpisodeManager | None = None


def get_default_manager() -> EpisodeManager:
    """Lazy-load episode manager from default processed normalized_events.json if available."""
    global _DEFAULT_MANAGER
    if _DEFAULT_MANAGER is None:
        if DEFAULT_PROCESSED_JSON.is_file():
            with open(DEFAULT_PROCESSED_JSON, encoding="utf-8") as f:
                data = json.load(f)
            _DEFAULT_MANAGER = EpisodeManager(data)
        else:
            _DEFAULT_MANAGER = EpisodeManager([])
    return _DEFAULT_MANAGER


def list_episodes() -> list[Episode]:
    """Public API: List all episodes from default manager."""
    return get_default_manager().list_episodes()


def get_episode(episode_id: str) -> Episode | None:
    """Public API: Get episode by ID from default manager."""
    return get_default_manager().get_episode(episode_id)


# Backward-compatibility helpers for existing test fixtures
def split_by_run(events: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Group events dataframe by run_id or episode_id without merging."""
    if events.empty:
        return {}
    group_col = "run_id" if "run_id" in events.columns else "episode_id"
    sort_col = "timestamp_utc" if "timestamp_utc" in events.columns else "timestamp"
    if sort_col in events.columns:
        return {rid: g.sort_values(sort_col).reset_index(drop=True) for rid, g in events.groupby(group_col)}
    return {rid: g.reset_index(drop=True) for rid, g in events.groupby(group_col)}


def segment_by_gap(run_events: pd.DataFrame, gap_seconds: float = 300.0) -> pd.Series:
    """Episode index by time gap within a single run."""
    if run_events.empty:
        return pd.Series(dtype="int64")
    ts_col = "timestamp_utc" if "timestamp_utc" in run_events.columns else "timestamp"
    if ts_col not in run_events.columns or run_events[ts_col].isna().all():
        return pd.Series(0, index=run_events.index, dtype="int64")
    ts_series = pd.to_datetime(run_events[ts_col], errors="coerce", utc=True)
    gaps = ts_series.diff().dt.total_seconds().fillna(0)
    return (gaps > gap_seconds).cumsum()
