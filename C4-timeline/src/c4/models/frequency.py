"""Global target frequency baseline model for forensic ATT&CK sequence prediction."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from c4.mitre_reference import to_parent_technique_set


class FrequencyBaseline:
    """Frequency baseline model estimating marginal next-technique probability P(T_{t+1} = b)."""

    def __init__(
        self,
        variant: str = "collapsed",
        granularity: str = "full",
        schema_version: str = "1.0.0",
        att_and_ck_reference_version: str = "16.1",
    ) -> None:
        if variant not in {"collapsed", "raw"}:
            raise ValueError(f"Unknown sequence variant: {variant}. Expected 'collapsed' or 'raw'.")
        if granularity not in {"full", "parent"}:
            raise ValueError(f"Unknown technique granularity: {granularity}. Expected 'full' or 'parent'.")

        self.variant = variant
        self.granularity = granularity
        self.schema_version = schema_version
        self.att_and_ck_reference_version = att_and_ck_reference_version

        self.config = {
            "variant": self.variant,
            "granularity": self.granularity,
        }

        # Target occurrence counts: target_technique -> weighted occurrences
        self.counts: dict[str, float] = defaultdict(float)
        # probabilities: target_technique -> P(b)
        self.probabilities: dict[str, float] = {}
        self.n_step_transitions: int = 0
        # supporting_evidence: target_technique -> list of [episode_id, current_event_id, target_event_id]
        self.supporting_evidence: dict[str, list[list[str]]] = defaultdict(list)
        self.training_episodes: list[str] = []

    def _extract_items(self, ep_val: Any) -> list[dict[str, Any]]:
        """Extract sequence items list from raw episode data structure."""
        if isinstance(ep_val, list):
            return ep_val
        if isinstance(ep_val, dict):
            if self.variant in ep_val:
                return ep_val[self.variant]
            if "items" in ep_val:
                return ep_val["items"]
        return []

    def _extract_tech_set(self, item: dict[str, Any]) -> list[str]:
        """Extract unique techniques from item matching model granularity."""
        raw_techs = item.get("techniques", [])
        if self.granularity == "parent":
            return sorted(list(set(to_parent_technique_set(raw_techs))))
        return sorted(list(set(raw_techs)))

    def _extract_event_id(self, item: dict[str, Any]) -> str:
        """Extract representative event ID string for evidence tracking."""
        if "event_ids" in item and item["event_ids"]:
            eids = item["event_ids"]
            return ",".join(eids) if isinstance(eids, list) else str(eids)
        if "event_id" in item:
            return str(item["event_id"])
        return "unknown_event"

    def fit(
        self,
        episodes: dict[str, Any] | list[dict[str, Any]],
        training_episodes: list[str] | None = None,
    ) -> FrequencyBaseline:
        """Fit global target frequency baseline on training episodes only."""
        self.counts = defaultdict(float)
        self.probabilities = {}
        self.n_step_transitions = 0
        self.supporting_evidence = defaultdict(list)

        ep_dict: dict[str, Any] = {}
        if isinstance(episodes, dict):
            if "episodes" in episodes and isinstance(episodes["episodes"], dict):
                ep_dict = episodes["episodes"]
            else:
                ep_dict = episodes
        elif isinstance(episodes, list):
            for idx, ep_obj in enumerate(episodes):
                ep_id = ep_obj.get("episode_id", f"EP_{idx+1}")
                ep_dict[ep_id] = ep_obj

        if training_episodes is not None:
            active_eps = [ep for ep in training_episodes if ep in ep_dict]
        else:
            active_eps = sorted(list(ep_dict.keys()))

        self.training_episodes = sorted(list(active_eps))

        for ep_id in self.training_episodes:
            items = self._extract_items(ep_dict[ep_id])
            if len(items) < 2:
                continue

            for i in range(len(items) - 1):
                cur_item = items[i]
                nxt_item = items[i + 1]

                nxt_set = self._extract_tech_set(nxt_item)
                n = len(nxt_set)
                if n == 0:
                    continue

                cur_eid = self._extract_event_id(cur_item)
                nxt_eid = self._extract_event_id(nxt_item)

                self.n_step_transitions += 1
                weight = 1.0 / n

                for b in nxt_set:
                    self.counts[b] += weight
                    self.supporting_evidence[b].append([ep_id, cur_eid, nxt_eid])

        total_weight = sum(self.counts.values())
        if total_weight > 0:
            for b, c in sorted(self.counts.items()):
                self.probabilities[b] = c / total_weight

        return self

    def predict(self, k: int | None = 3) -> dict[str, Any]:
        """Return top-k candidates based on unconditional target frequency distribution.
        
        Does not depend on the current technique.
        """
        if not self.probabilities:
            return {
                "status": "empty_training",
                "candidates": [],
                "number_of_supporting_step_transitions": 0,
                "supporting_evidence": [],
            }

        sorted_candidates = sorted(
            self.probabilities.items(),
            key=lambda item: (-item[1], item[0]),
        )

        ranked_candidates = sorted_candidates[:k] if (k is not None and k > 0) else sorted_candidates

        evidence_collected = []
        for b, _ in ranked_candidates:
            for ev in self.supporting_evidence.get(b, []):
                evidence_collected.append({
                    "target_technique": b,
                    "episode_id": ev[0],
                    "current_event_id": ev[1],
                    "target_event_id": ev[2],
                })

        return {
            "status": "ok",
            "candidates": ranked_candidates,  # list of (technique, probability)
            "number_of_supporting_step_transitions": self.n_step_transitions,
            "supporting_evidence": evidence_collected,
        }

    def save(self, output_path: Path | str) -> Path:
        """Save fitted baseline model to deterministic JSON file."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "schema_version": self.schema_version,
            "att_and_ck_reference_version": self.att_and_ck_reference_version,
            "config": self.config,
            "training_episodes": self.training_episodes,
            "n_step_transitions": self.n_step_transitions,
            "counts": dict(sorted(self.counts.items())),
            "probabilities": dict(sorted(self.probabilities.items())),
            "evidence": {b: self.supporting_evidence[b] for b in sorted(self.supporting_evidence.keys())},
        }

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)

        return p

    @classmethod
    def load(cls, path: Path | str) -> FrequencyBaseline:
        """Load fitted model from JSON file."""
        p = Path(path)
        with open(p, encoding="utf-8") as f:
            data = json.load(f)

        config = data.get("config", {})
        model = cls(
            variant=config.get("variant", "collapsed"),
            granularity=config.get("granularity", "full"),
            schema_version=data.get("schema_version", "1.0.0"),
            att_and_ck_reference_version=data.get("att_and_ck_reference_version", "16.1"),
        )
        model.training_episodes = data.get("training_episodes", [])
        model.n_step_transitions = data.get("n_step_transitions", 0)

        for b, c in data.get("counts", {}).items():
            model.counts[b] = float(c)

        for b, p_val in data.get("probabilities", {}).items():
            model.probabilities[b] = float(p_val)

        for b, ev_list in data.get("evidence", {}).items():
            model.supporting_evidence[b] = ev_list

        return model
