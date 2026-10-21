"""First-order Markov chain next-step prediction model for forensic ATT&CK sequences."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from c4.mitre_reference import to_parent_technique_set


class MarkovModel:
    """First-order Markov model capturing conditional ATT&CK technique transition probabilities."""

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

        # Transition statistics
        # counts[a][b] = float
        self.counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        # n_step_transitions[a] = int (number of step transitions where a was present in current set)
        self.n_step_transitions: dict[str, int] = defaultdict(int)
        # supporting_evidence[a][b] = list of [episode_id, current_event_id, target_event_id]
        self.supporting_evidence: dict[str, dict[str, list[list[str]]]] = defaultdict(lambda: defaultdict(list))
        # probabilities[a][b] = float (P(b|a))
        self.probabilities: dict[str, dict[str, float]] = defaultdict(dict)

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
    ) -> MarkovModel:
        """Fit transition counts and probabilities on training episodes only.
        
        Transitions are strictly within-episode between consecutive items.
        Zero cross-episode transitions are ever recorded.
        """
        # Reset fitted state
        self.counts = defaultdict(lambda: defaultdict(float))
        self.n_step_transitions = defaultdict(int)
        self.supporting_evidence = defaultdict(lambda: defaultdict(list))
        self.probabilities = defaultdict(dict)

        # Standardize episodes mapping: episode_id -> items
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

        # Filter training episodes if specified
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

                cur_set = self._extract_tech_set(cur_item)
                nxt_set = self._extract_tech_set(nxt_item)

                m = len(cur_set)
                n = len(nxt_set)
                if m == 0 or n == 0:
                    continue

                cur_eid = self._extract_event_id(cur_item)
                nxt_eid = self._extract_event_id(nxt_item)

                weight = 1.0 / (m * n)

                for a in cur_set:
                    self.n_step_transitions[a] += 1
                    for b in nxt_set:
                        self.counts[a][b] += weight
                        self.supporting_evidence[a][b].append([ep_id, cur_eid, nxt_eid])

        # Compute conditional probabilities P(b|a) = count[a][b] / sum_k count[a][k]
        for a in sorted(self.counts.keys()):
            row_sum = sum(self.counts[a].values())
            if row_sum > 0:
                self.probabilities[a] = {}
                for b, c in sorted(self.counts[a].items()):
                    self.probabilities[a][b] = c / row_sum

        return self

    def predict(
        self,
        current_technique_set: Iterable[str] | str,
        k: int | None = 3,
    ) -> dict[str, Any]:
        """Predict top-k next ATT&CK techniques from current technique set.
        
        Averages conditional distributions of observed members in current_technique_set.
        Returns ranked list of (technique, probability) tuples and full metadata.
        """
        if isinstance(current_technique_set, str):
            current_techs = [current_technique_set]
        else:
            current_techs = list(current_technique_set)

        if self.granularity == "parent":
            current_set = sorted(list(set(to_parent_technique_set(current_techs))))
        else:
            current_set = sorted(list(set(current_techs)))

        if not current_set:
            return {
                "status": "empty_input",
                "current_set": [],
                "members_used": [],
                "members_unseen": [],
                "candidates": [],
                "number_of_supporting_step_transitions": 0,
                "supporting_evidence": [],
            }

        members_used = [a for a in current_set if a in self.probabilities and len(self.probabilities[a]) > 0]
        members_unseen = [a for a in current_set if a not in members_used]

        if not members_used:
            return {
                "status": "insufficient_evidence",
                "current_set": current_set,
                "members_used": [],
                "members_unseen": members_unseen,
                "candidates": [],
                "number_of_supporting_step_transitions": 0,
                "supporting_evidence": [],
            }

        # Average probability distributions of members with outgoing transitions
        # Equal weight per member (1 / len(members_used))
        combined_probs: dict[str, float] = defaultdict(float)
        w_member = 1.0 / len(members_used)

        for a in members_used:
            for b, p in self.probabilities[a].items():
                combined_probs[b] += w_member * p

        # Verify sum of probabilities equals 1.0 within 1e-9
        total_p = sum(combined_probs.values())
        if abs(total_p - 1.0) > 1e-9:
            # Re-normalize if any floating-point drift occurred
            for b in combined_probs:
                combined_probs[b] /= total_p

        # Sort by probability descending, deterministic tie-breaking by technique ID ascending
        sorted_candidates = sorted(
            combined_probs.items(),
            key=lambda item: (-item[1], item[0]),
        )

        ranked_candidates = sorted_candidates[:k] if (k is not None and k > 0) else sorted_candidates

        # Supporting transitions and evidence
        n_supporting_transitions = sum(self.n_step_transitions[a] for a in members_used)
        evidence_collected = []
        for b, _ in ranked_candidates:
            for a in members_used:
                for ev in self.supporting_evidence.get(a, {}).get(b, []):
                    evidence_collected.append({
                        "source_technique": a,
                        "target_technique": b,
                        "episode_id": ev[0],
                        "current_event_id": ev[1],
                        "target_event_id": ev[2],
                    })

        return {
            "status": "ok",
            "current_set": current_set,
            "members_used": members_used,
            "members_unseen": members_unseen,
            "candidates": ranked_candidates,  # list of (technique, probability)
            "number_of_supporting_step_transitions": n_supporting_transitions,
            "supporting_evidence": evidence_collected,
        }

    def save(self, output_path: Path | str) -> Path:
        """Save fitted model to deterministic JSON file (sorted keys, no timestamps)."""
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        # Convert defaultdicts to regular sorted dicts for serialization
        data = {
            "schema_version": self.schema_version,
            "att_and_ck_reference_version": self.att_and_ck_reference_version,
            "config": self.config,
            "training_episodes": self.training_episodes,
            "n_step_transitions": dict(sorted(self.n_step_transitions.items())),
            "counts": {
                a: dict(sorted(self.counts[a].items()))
                for a in sorted(self.counts.keys())
            },
            "probabilities": {
                a: dict(sorted(self.probabilities[a].items()))
                for a in sorted(self.probabilities.keys())
            },
            "evidence": {
                a: {b: self.supporting_evidence[a][b] for b in sorted(self.supporting_evidence[a].keys())}
                for a in sorted(self.supporting_evidence.keys())
            },
        }

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)

        return p

    @classmethod
    def load(cls, path: Path | str) -> MarkovModel:
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
        model.n_step_transitions = defaultdict(int, data.get("n_step_transitions", {}))

        counts_raw = data.get("counts", {})
        for a, row in counts_raw.items():
            for b, c in row.items():
                model.counts[a][b] = float(c)

        probs_raw = data.get("probabilities", {})
        for a, row in probs_raw.items():
            model.probabilities[a] = {b: float(p_val) for b, p_val in row.items()}

        evidence_raw = data.get("evidence", {})
        for a, row in evidence_raw.items():
            for b, ev_list in row.items():
                model.supporting_evidence[a][b] = ev_list

        return model
