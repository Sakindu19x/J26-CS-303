#!/usr/bin/env python3
"""Train Production Model on all 7 episodes (Prompt 13 Section 5.1).

Trains Markov and Frequency models on all 7 episodes (E1-E7) for:
1. Technique primary slice: collapsed_full
2. Tactic secondary slice: tactic_collapsed

Saves artifacts under artifacts/7ep/production_model/ with manifest.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from c4.models.frequency import FrequencyBaseline
from c4.models.markov import MarkovModel
from c4.tactic_evaluation import (
    TacticFrequencyBaseline,
    TacticMarkovModel,
    build_tactic_sequences,
)

SEQS_PATH = REPO_ROOT / "data" / "processed_7ep" / "attack_sequences.json"
OUT_DIR = REPO_ROOT / "artifacts" / "7ep" / "production_model"
MANIFEST_PATH = OUT_DIR / "manifest.json"

TRAINING_EPISODES = ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def train_and_save_production_models() -> dict[str, Any]:
    print("=" * 80)
    print("TRAINING PRODUCTION MODELS ON ALL 7 EPISODES (E1-E7)")
    print("=" * 80)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SEQS_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)

    ep_seqs = {
        ep_id: seqs_data["episodes"][ep_id]["collapsed"]
        for ep_id in TRAINING_EPISODES
    }

    # 1. Technique Model: collapsed_full
    print("\n[1/2] Training Technique Model (collapsed_full)...")
    m_tech = MarkovModel(variant="collapsed", granularity="full").fit(
        ep_seqs, training_episodes=TRAINING_EPISODES
    )
    f_tech = FrequencyBaseline(variant="collapsed", granularity="full").fit(
        ep_seqs, training_episodes=TRAINING_EPISODES
    )

    n_tech_transitions = sum(m_tech.n_step_transitions.values())
    n_tech_states = len(m_tech.counts)
    print(f"  Technique states: {n_tech_states}, total transition count: {n_tech_transitions}")

    tech_file = OUT_DIR / "collapsed_full.json"
    tech_data = {
        "slice": "collapsed_full",
        "model_level": "technique",
        "training_episodes": TRAINING_EPISODES,
        "n_sequences": len(TRAINING_EPISODES),
        "n_states": n_tech_states,
        "n_step_transitions_total": n_tech_transitions,
        "markov": {
            "n_step_transitions": dict(sorted(m_tech.n_step_transitions.items())),
            "counts": {
                a: dict(sorted(m_tech.counts[a].items()))
                for a in sorted(m_tech.counts.keys())
            },
            "probabilities": {
                a: dict(sorted(m_tech.probabilities[a].items()))
                for a in sorted(m_tech.probabilities.keys())
            },
        },
        "frequency": {
            "n_step_transitions": f_tech.n_step_transitions,
            "counts": dict(sorted(f_tech.counts.items())),
            "probabilities": dict(sorted(f_tech.probabilities.items())),
        },
    }
    with open(tech_file, "w", encoding="utf-8") as f:
        json.dump(tech_data, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"  Saved: {tech_file}")

    # 2. Tactic Model: tactic_collapsed
    print("\n[2/2] Training Tactic Model (tactic_collapsed)...")
    t_seqs = build_tactic_sequences(seqs_data)
    ep_t_seqs = {
        ep_id: t_seqs["episodes"][ep_id]["tactic_collapsed"] if "episodes" in t_seqs else t_seqs[ep_id]["tactic_collapsed"]
        for ep_id in TRAINING_EPISODES
    }

    m_tac = TacticMarkovModel().fit(ep_t_seqs, TRAINING_EPISODES)
    f_tac = TacticFrequencyBaseline().fit(ep_t_seqs, TRAINING_EPISODES)

    n_tac_transitions = sum(m_tac.n_step_transitions.values())
    n_tac_states = len(m_tac.counts)
    print(f"  Tactic states: {n_tac_states}, total transition count: {n_tac_transitions}")

    tac_file = OUT_DIR / "tactic_collapsed.json"
    tac_data = {
        "slice": "tactic_collapsed",
        "model_level": "tactic",
        "training_episodes": TRAINING_EPISODES,
        "n_sequences": len(TRAINING_EPISODES),
        "n_states": n_tac_states,
        "n_step_transitions_total": n_tac_transitions,
        "markov": {
            "n_step_transitions": dict(sorted(m_tac.n_step_transitions.items())),
            "counts": {
                a: dict(sorted(m_tac.counts[a].items()))
                for a in sorted(m_tac.counts.keys())
            },
            "probabilities": {
                a: dict(sorted(m_tac.probabilities[a].items()))
                for a in sorted(m_tac.probabilities.keys())
            },
        },
        "frequency": {
            "counts": dict(sorted(f_tac.counts.items())),
            "probabilities": dict(sorted(f_tac.probabilities.items())),
        },
    }
    with open(tac_file, "w", encoding="utf-8") as f:
        json.dump(tac_data, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"  Saved: {tac_file}")

    # 3. Build Manifest
    print("\nWriting production model manifest...")
    manifest = {
        "production_model_training_policy": "all_seven_episodes",
        "training_episodes": TRAINING_EPISODES,
        "files": {
            "artifacts/7ep/production_model/collapsed_full.json": {
                "sha256": sha256_file(tech_file),
                "size_bytes": tech_file.stat().st_size,
                "model_level": "technique",
                "slice": "collapsed_full",
                "training_episodes": TRAINING_EPISODES,
                "n_sequences": len(TRAINING_EPISODES),
                "n_states": n_tech_states,
                "n_transitions": n_tech_transitions,
            },
            "artifacts/7ep/production_model/tactic_collapsed.json": {
                "sha256": sha256_file(tac_file),
                "size_bytes": tac_file.stat().st_size,
                "model_level": "tactic",
                "slice": "tactic_collapsed",
                "training_episodes": TRAINING_EPISODES,
                "n_sequences": len(TRAINING_EPISODES),
                "n_states": n_tac_states,
                "n_transitions": n_tac_transitions,
            },
        },
    }
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True, ensure_ascii=False)
    print(f"  Manifest written: {MANIFEST_PATH}")
    print(f"  collapsed_full SHA-256: {manifest['files']['artifacts/7ep/production_model/collapsed_full.json']['sha256']}")
    print(f"  tactic_collapsed SHA-256: {manifest['files']['artifacts/7ep/production_model/tactic_collapsed.json']['sha256']}")

    print("\n" + "=" * 80)
    print("PRODUCTION MODEL TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return manifest


if __name__ == "__main__":
    train_and_save_production_models()
