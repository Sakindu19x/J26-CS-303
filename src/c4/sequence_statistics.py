"""Statistical analysis and LOEO coverage evaluation for next-step attack sequences."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from c4.mitre_reference import to_parent_technique_set

UTC = timezone.utc
REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
DEFAULT_STATS_JSON = REPORTS_DIR / "sequence_statistics.json"
DEFAULT_STATS_MD = REPORTS_DIR / "sequence_statistics.md"


def compute_sequence_statistics(
    all_samples: list[dict[str, Any]],
    sequences_data: dict[str, Any],
) -> dict[str, Any]:
    """Compute comprehensive statistics across variants and granularities."""
    episodes = sorted(list(sequences_data.get("episodes", {}).keys()))

    # 1. Distinct techniques per episode and pairwise overlap matrices
    overlap_matrices: dict[str, Any] = {}
    for gran in ["full", "parent"]:
        ep_techs: dict[str, list[str]] = {}
        for ep in episodes:
            raw_items = sequences_data["episodes"][ep].get("raw", [])
            t_set = set()
            for it in raw_items:
                for t in it.get("techniques", []):
                    t_set.add(t)
            if gran == "parent":
                ep_techs[ep] = to_parent_technique_set(list(t_set))
            else:
                ep_techs[ep] = sorted(list(t_set))

        matrix: dict[str, dict[str, int]] = {e1: {} for e1 in episodes}
        shared_details: list[dict[str, Any]] = []

        for e1 in episodes:
            for e2 in episodes:
                shared = sorted(list(set(ep_techs[e1]) & set(ep_techs[e2])))
                matrix[e1][e2] = len(shared)
                if e1 < e2:
                    shared_details.append({
                        "episode_a": e1,
                        "episode_b": e2,
                        "shared_count": len(shared),
                        "shared_techniques": shared,
                    })

        overlap_matrices[gran] = {
            "distinct_techniques_per_episode": {e: len(ep_techs[e]) for e in episodes},
            "technique_sets_per_episode": ep_techs,
            "matrix": matrix,
            "pairwise_shared": shared_details,
        }

    # 2. Slice analysis for each combination of (variant, granularity)
    combos = [
        ("collapsed", "full"),
        ("collapsed", "parent"),
        ("raw", "full"),
        ("raw", "parent"),
    ]

    slices: dict[str, Any] = {}

    for variant, gran in combos:
        key = f"{variant}_{gran}"
        combo_samples = [s for s in all_samples if s["variant"] == variant and s["granularity"] == gran]

        # Counts per episode
        ep_counts: dict[str, int] = Counter(s["episode_id"] for s in combo_samples)
        total_samples = len(combo_samples)

        # Expected counts validation
        expected = 67 if variant == "collapsed" else 95
        count_mismatch = (total_samples != expected)

        # Frequency counts as current and target
        current_freq: Counter[str] = Counter()
        target_freq: Counter[str] = Counter()
        multi_inputs = 0
        multi_targets = 0
        self_repeats = 0

        for s in combo_samples:
            for t in s["current_technique_set"]:
                current_freq[t] += 1
            for t in s["target_technique_set"]:
                target_freq[t] += 1

            if len(s["current_technique_set"]) > 1:
                multi_inputs += 1
            if len(s["target_technique_set"]) > 1:
                multi_targets += 1
            if s["flags"]["is_self_repeat"]:
                self_repeats += 1

        self_repeat_rate = round((self_repeats / total_samples * 100), 2) if total_samples > 0 else 0.0

        # Leave-One-Episode-Out (LOEO) Folds
        folds = []
        for test_ep in episodes:
            train_eps = [e for e in episodes if e != test_ep]
            test_samples = [s for s in combo_samples if s["episode_id"] == test_ep]
            train_samples = [s for s in combo_samples if s["episode_id"] in train_eps]

            train_sources = set(t for s in train_samples for t in s["current_technique_set"])
            train_targets = set(t for s in train_samples for t in s["target_technique_set"])

            usable_count = sum(1 for s in test_samples if bool(set(s["current_technique_set"]) & train_sources))
            reachable_count = sum(1 for s in test_samples if bool(set(s["target_technique_set"]) & train_targets))

            n_test = len(test_samples)
            usable_pct = round((usable_count / n_test * 100), 1) if n_test > 0 else 0.0
            reachable_pct = round((reachable_count / n_test * 100), 1) if n_test > 0 else 0.0

            test_all_targets = set(t for s in test_samples for t in s["target_technique_set"])
            unseen_targets = sorted(list(test_all_targets - train_targets))

            folds.append({
                "test_episode": test_ep,
                "train_episodes": train_eps,
                "test_samples_count": n_test,
                "usable_samples_count": usable_count,
                "usable_percent": usable_pct,
                "reachable_samples_count": reachable_count,
                "reachable_percent": reachable_pct,
                "distinct_unseen_targets_count": len(unseen_targets),
                "distinct_unseen_targets": unseen_targets,
            })

        slices[key] = {
            "variant": variant,
            "granularity": gran,
            "total_samples": total_samples,
            "expected_samples": expected,
            "count_mismatch": count_mismatch,
            "samples_per_episode": dict(ep_counts),
            "self_repeat_count": self_repeats,
            "self_repeat_rate_percent": self_repeat_rate,
            "multi_technique_inputs_count": multi_inputs,
            "multi_technique_targets_count": multi_targets,
            "top_current_techniques": current_freq.most_common(10),
            "top_target_techniques": target_freq.most_common(10),
            "loeo_folds": folds,
        }

    return {
        "episodes": episodes,
        "overlap_matrices": overlap_matrices,
        "slices": slices,
        "evaluation_limitations_summary": (
            "Empirical Limitations of CAM-LDS Next-Stage Modeling:\n"
            "1. Dataset Sample Size: Across all four distinct attack campaigns, only 67 collapsed transition samples "
            "(95 raw transition samples) are available at full technique granularity.\n"
            "2. Closed-Vocabulary Bounds (Full ID Granularity): Pooled over the 4 collapsed full-ID folds, 34 of 67 test samples "
            "(50.7%) have a current technique seen in training and 35 of 67 (52.2%) have a target technique seen in training. "
            "These values establish the empirical upper bounds on what any closed-vocabulary model can achieve on this dataset.\n"
            "3. Closed-Vocabulary Bounds (Parent Granularity): For parent granularity, 41 of 67 test samples (61.2%) have a current "
            "technique seen in training and 39 of 67 (58.2%) have a target technique seen in training targets."
        ),
    }


def render_statistics_markdown(stats: dict[str, Any]) -> str:
    """Render comprehensive sequence statistics into Markdown."""
    lines = [
        "# CAM-LDS Sequence Statistics & Next-Step Coverage Report",
        "",
        "> [!IMPORTANT]",
        "> **Forensic Scope Notice:** This report presents telemetry sequence distribution and coverage analysis only; "
        "no machine learning model was trained and no predictive accuracy is reported.",
        "",
        "## 1. Next-Step Sample Volume & Self-Repeat Rates",
        "",
        "| Slice (Variant + Granularity) | Total Samples | Expected | Mismatch? | E1 | E2 | E3 | E4 | Multi Inputs | Multi Targets | Self-Repeats | Self-Repeat Rate (%) |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for key, sl in stats["slices"].items():
        ep_c = sl["samples_per_episode"]
        mismatch_str = "FLAG" if sl["count_mismatch"] else "None"
        lines.append(
            f"| **{sl['variant']} ({sl['granularity']})** | **{sl['total_samples']}** | {sl['expected_samples']} | {mismatch_str} | "
            f"{ep_c.get('E1', 0)} | {ep_c.get('E2', 0)} | {ep_c.get('E3', 0)} | {ep_c.get('E4', 0)} | "
            f"{sl['multi_technique_inputs_count']} | {sl['multi_technique_targets_count']} | "
            f"{sl['self_repeat_count']} | **{sl['self_repeat_rate_percent']:.2f}%** |"
        )

    lines.extend([
        "",
        "## 2. Technique Overlap Across Episodes (Full Technique ID)",
        "",
        "### Distinct Technique Counts per Episode",
        "",
    ])

    distinct_full = stats["overlap_matrices"]["full"]["distinct_techniques_per_episode"]
    lines.append("| " + " | ".join(f"**{ep}**" for ep in stats["episodes"]) + " |")
    lines.append("| " + " | ".join("---" for _ in stats["episodes"]) + " |")
    lines.append("| " + " | ".join(str(distinct_full[ep]) for ep in stats["episodes"]) + " |")

    lines.extend([
        "",
        "### Pairwise Technique Overlap Matrix",
        "",
        "| Episode | E1 | E2 | E3 | E4 |",
        "|---|---|---|---|---|",
    ])

    mat_full = stats["overlap_matrices"]["full"]["matrix"]
    for ep1 in stats["episodes"]:
        row = [f"**{ep1}**"] + [str(mat_full[ep1][ep2]) for ep2 in stats["episodes"]]
        lines.append("| " + " | ".join(row) + " |")

    lines.extend([
        "",
        "### Pairwise Shared Techniques",
        "",
    ])
    for pair in stats["overlap_matrices"]["full"]["pairwise_shared"]:
        shared_list_str = ", ".join(f"`{t}`" for t in pair["shared_techniques"])
        lines.append(f"- **{pair['episode_a']} & {pair['episode_b']}** ({pair['shared_count']} shared): {shared_list_str}")

    lines.extend([
        "",
        "## 3. Leave-One-Episode-Out (LOEO) Fold Coverage Analysis",
        "",
        "Each fold tests on one isolated episode while training strictly on the remaining three episodes.",
        "",
    ])

    for key, sl in stats["slices"].items():
        lines.extend([
            f"### Slice: `{sl['variant']}` variant at `{sl['granularity']}` granularity",
            "",
            "| Test Episode | Training Episodes | Test Samples (N) | Usable Sources (%) | Reachable Targets (%) | Unseen Targets (Count) | Unseen Targets (Sample) |",
            "|---|---|---|---|---|---|---|",
        ])
        for f in sl["loeo_folds"]:
            unseen_samp = ", ".join(f"`{t}`" for t in f["distinct_unseen_targets"][:4])
            if len(f["distinct_unseen_targets"]) > 4:
                unseen_samp += f" (+{len(f['distinct_unseen_targets']) - 4} more)"
            lines.append(
                f"| **{f['test_episode']}** | {', '.join(f['train_episodes'])} | {f['test_samples_count']} | "
                f"**{f['usable_percent']:.1f}%** ({f['usable_samples_count']}/{f['test_samples_count']}) | "
                f"**{f['reachable_percent']:.1f}%** ({f['reachable_samples_count']}/{f['test_samples_count']}) | "
                f"**{f['distinct_unseen_targets_count']}** | {unseen_samp} |"
            )
        lines.append("")

    lines.extend([
        "## 4. Evaluation Feasibility & Dataset Limitations",
        "",
        stats["evaluation_limitations_summary"],
        "",
    ])

    return "\n".join(lines)


def export_sequence_statistics(
    stats_data: dict[str, Any],
    json_path: Path = DEFAULT_STATS_JSON,
    md_path: Path = DEFAULT_STATS_MD,
) -> None:
    """Write sequence statistics to JSON and Markdown reports."""
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, indent=2, ensure_ascii=False)

    md_content = render_statistics_markdown(stats_data)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
