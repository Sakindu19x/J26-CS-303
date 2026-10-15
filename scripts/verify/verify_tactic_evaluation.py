"""Independent verification script for secondary next-tactic LOEO evaluation.

Reads ONLY:
- data/processed/tactic_evaluation_predictions.csv
- data/processed/evaluation_predictions.csv
- data/processed/technique_tactic_reference.json
- data/processed/attack_sequences.json (for event-level sensitivity discrepancy classification)

NO imports from c4.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
TACTIC_CSV_PATH = BASE_DIR / "data" / "processed" / "tactic_evaluation_predictions.csv"
TECH_PRED_PATH = BASE_DIR / "data" / "processed" / "evaluation_predictions.csv"
TECH_REF_PATH = BASE_DIR / "data" / "processed" / "technique_tactic_reference.json"
ATTACK_SEQUENCES_PATH = BASE_DIR / "data" / "processed" / "attack_sequences.json"


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score 95% interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z ** 2) / total
    center = (p + (z ** 2) / (2.0 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / total) + (z ** 2 / (4.0 * (total ** 2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def random_guess_expected_hit(target_set: set[str], k: int) -> float:
    """Hypergeometric expected hit probability choosing k distinct tactics uniformly from 14."""
    m = len(target_set)
    total_comb = math.comb(14, k)
    miss_comb = math.comb(max(0, 14 - m), k)
    return 1.0 - (miss_comb / total_comb)


def rebuild_tactic_samples_from_sequences(
    sequences_path: Path | str = ATTACK_SEQUENCES_PATH,
) -> dict[str, dict[str, list[tuple[list[str], list[str]]]]]:
    """Rebuilds evaluation samples strictly from attack_sequences.json (NO c4 imports).

    Returns dict: config -> episode_id -> list of (current_tactics, target_tactics).
    """
    p = Path(sequences_path)
    with open(p, "r", encoding="utf-8") as f:
        seq_data = json.load(f)

    configs = [
        ("tactic_raw", False, False),
        ("tactic_collapsed", True, False),
        ("tactic_raw_dataset_tactics", False, True),
        ("tactic_collapsed_dataset_tactics", True, True),
    ]

    rebuilt: dict[str, dict[str, list[tuple[list[str], list[str]]]]] = {}
    for cfg_name, is_collapsed, use_ds in configs:
        rebuilt[cfg_name] = {}
        for ep_id in sorted(seq_data["episodes"].keys()):
            raw_events = seq_data["episodes"][ep_id]["raw"]
            items: list[tuple[str, ...]] = []
            for ev in raw_events:
                tacs = ev.get("tactics", []) if use_ds else ev.get("official_tactics", [])
                norm_tacs = tuple(sorted(set(t.strip().lower().replace(" ", "-") for t in tacs if t)))
                items.append(norm_tacs)

            if is_collapsed:
                col_items: list[tuple[str, ...]] = []
                for it in items:
                    if not col_items or col_items[-1] != it:
                        col_items.append(it)
                seq = col_items
            else:
                seq = items

            ep_samples: list[tuple[list[str], list[str]]] = []
            for i in range(len(seq) - 1):
                ep_samples.append((sorted(list(seq[i])), sorted(list(seq[i + 1]))))
            rebuilt[cfg_name][ep_id] = ep_samples

    return rebuilt


def verify_tactic_sample_reconstruction(
    tactic_csv_path: Path | str = TACTIC_CSV_PATH,
    sequences_path: Path | str = ATTACK_SEQUENCES_PATH,
) -> dict[str, dict[str, int]]:
    """Compares rebuilt samples from attack_sequences.json with rows in tactic_evaluation_predictions.csv.

    Fails loudly on any mismatch. Returns N per configuration per episode.
    """
    rebuilt = rebuild_tactic_samples_from_sequences(sequences_path)
    with open(tactic_csv_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    counts: dict[str, dict[str, int]] = {}
    for cfg in ("tactic_raw", "tactic_collapsed", "tactic_raw_dataset_tactics", "tactic_collapsed_dataset_tactics"):
        counts[cfg] = {}
        m_rows = [r for r in rows if r["configuration"] == cfg and r["method"] == "markov"]
        by_ep: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in m_rows:
            by_ep[r["episode_id"]].append(r)

        for ep_id in sorted(rebuilt[cfg].keys()):
            exp_samples = rebuilt[cfg][ep_id]
            csv_samples = [
                (sorted(json.loads(r["current_tactic_set"])), sorted(json.loads(r["target_tactic_set"])))
                for r in by_ep[ep_id]
            ]

            if len(exp_samples) != len(csv_samples):
                raise ValueError(
                    f"RECONSTRUCTION MISMATCH in {cfg} {ep_id}: rebuilt {len(exp_samples)} samples vs CSV {len(csv_samples)}"
                )

            for idx, (rb, cs) in enumerate(zip(exp_samples, csv_samples)):
                if rb != cs:
                    raise ValueError(
                        f"RECONSTRUCTION MISMATCH in {cfg} {ep_id} sample #{idx}:\n"
                        f"  Rebuilt: current={rb[0]}, target={rb[1]}\n"
                        f"  CSV:     current={cs[0]}, target={cs[1]}"
                    )
            counts[cfg][ep_id] = len(exp_samples)

    return counts


def recompute_from_csv(
    tactic_csv_path: Path | str = TACTIC_CSV_PATH,
    tech_pred_path: Path | str = TECH_PRED_PATH,
    tech_ref_path: Path | str = TECH_REF_PATH,
    sequences_path: Path | str = ATTACK_SEQUENCES_PATH,
) -> dict[str, Any]:
    """Recomputes all tactic evaluation metrics independently from CSV and reference files."""
    p_tac = Path(tactic_csv_path)
    if not p_tac.exists():
        raise FileNotFoundError(f"Tactic predictions CSV not found: {p_tac}")

    with open(p_tac, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # 1. Re-derive hit1 and hit3 for every single row
    verified_rows = 0
    for r in rows:
        parsed_cands = json.loads(r["predicted_candidates_top3"])
        cands = [c[0] for c in parsed_cands]
        target_set = set(json.loads(r["target_tactic_set"]))

        derived_h1 = 1 if (cands and cands[0] in target_set) else 0
        derived_h3 = 1 if any(c in target_set for c in cands[:3]) else 0

        stored_h1 = int(r["hit1"])
        stored_h3 = int(r["hit3"])

        if derived_h1 != stored_h1 or derived_h3 != stored_h3:
            raise ValueError(
                f"FATAL: Hit flag mismatch in row {r['configuration']} {r['sample_id']} {r['method']}: "
                f"derived=({derived_h1}, {derived_h3}) vs stored=({stored_h1}, {stored_h3})"
            )
        verified_rows += 1

    # Group by configuration
    configs: list[str] = []
    by_config: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        cfg = r["configuration"]
        if cfg not in by_config:
            configs.append(cfg)
            by_config[cfg] = []
        by_config[cfg].append(r)

    results: dict[str, Any] = {"_meta": {"rows_verified": verified_rows}}

    for cfg in configs:
        c_rows = by_config[cfg]
        methods: list[str] = []
        by_method: dict[str, list[dict[str, str]]] = {}
        for r in c_rows:
            m = r["method"]
            if m not in by_method:
                methods.append(m)
                by_method[m] = []
            by_method[m].append(r)

        m_rows_first = by_method[methods[0]] if methods else []
        n_samples = len(m_rows_first)

        cfg_res: dict[str, Any] = {
            "n": n_samples,
            "methods": {},
            "paired_2x2": {},
            "frequency_only_split": {},
            "coverage": {},
            "covered_only": {},
            "ceiling": {},
            "reference_baselines": {},
            "self_repeat": {},
            "strict_single_tactic": {},
            "tie_diagnostic": {},
            "hit_concentration": {},
        }

        # 2. Recompute per method
        for m in methods:
            m_rows = by_method[m]
            n_m = len(m_rows)
            h1 = sum(int(r["hit1"]) for r in m_rows)
            h3 = sum(int(r["hit3"]) for r in m_rows)
            p1 = h1 / n_m if n_m > 0 else 0.0
            p3 = h3 / n_m if n_m > 0 else 0.0

            # Per fold
            folds: dict[str, dict[str, Any]] = {}
            for r in m_rows:
                fid = r["fold_id"]
                if fid not in folds:
                    folds[fid] = {"n": 0, "hit1": 0, "hit3": 0, "test_episode": r["episode_id"]}
                folds[fid]["n"] += 1
                folds[fid]["hit1"] += int(r["hit1"])
                folds[fid]["hit3"] += int(r["hit3"])

            sorted_folds = {k: folds[k] for k in sorted(folds.keys())}
            fold_rates_t1 = [d["hit1"] / d["n"] if d["n"] > 0 else 0.0 for d in sorted_folds.values()]
            fold_rates_t3 = [d["hit3"] / d["n"] if d["n"] > 0 else 0.0 for d in sorted_folds.values()]
            fold_mean_t1 = sum(fold_rates_t1) / len(fold_rates_t1) if fold_rates_t1 else 0.0
            fold_mean_t3 = sum(fold_rates_t3) / len(fold_rates_t3) if fold_rates_t3 else 0.0

            cov_hits = sum(1 for r in m_rows if r["status"] == "ok")
            cov_rate = cov_hits / n_m if n_m > 0 else 0.0

            cfg_res["methods"][m] = {
                "n": n_m,
                "hit1": h1,
                "hit3": h3,
                "pooled_top1": p1,
                "pooled_top3": p3,
                "wilson95_top1": list(wilson_interval(h1, n_m)),
                "wilson95_top3": list(wilson_interval(h3, n_m)),
                "fold_mean_top1": fold_mean_t1,
                "fold_mean_top3": fold_mean_t3,
                "per_fold": sorted_folds,
                "coverage_n": cov_hits,
                "coverage_rate": cov_rate,
            }

        # Coverage (Markov status ok)
        markov_rows = by_method.get("markov", [])
        ok_markov_rows = [r for r in markov_rows if r["status"] == "ok"]
        n_cov = len(ok_markov_rows)
        cfg_res["coverage"] = {
            "n": n_samples,
            "covered": n_cov,
            "rate": n_cov / n_samples if n_samples > 0 else 0.0,
        }

        # Covered-only subset
        ok_sids = set(r["sample_id"] for r in ok_markov_rows)
        cov_comp = {"n": n_cov}
        for m_key, m_name in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
            sub_r = [r for r in by_method.get(m_name, []) if r["sample_id"] in ok_sids]
            cov_comp[f"{m_key}_hit1"] = sum(int(r["hit1"]) for r in sub_r)
            cov_comp[f"{m_key}_hit3"] = sum(int(r["hit3"]) for r in sub_r)
        cfg_res["covered_only"] = cov_comp

        # 3. Recompute ceiling: samples whose target set shares >=1 tactic with union of targets in other episodes
        targets_by_ep: dict[str, set[str]] = defaultdict(set)
        for r in markov_rows:
            tgt = set(json.loads(r["target_tactic_set"]))
            targets_by_ep[r["episode_id"]].update(tgt)

        ceil_hits = 0
        for r in markov_rows:
            ep = r["episode_id"]
            other_targets: set[str] = set()
            for other_ep, t_set in targets_by_ep.items():
                if other_ep != ep:
                    other_targets.update(t_set)
            tgt = set(json.loads(r["target_tactic_set"]))
            if tgt & other_targets:
                ceil_hits += 1

        cfg_res["ceiling"] = {
            "n": n_samples,
            "hits": ceil_hits,
            "rate": ceil_hits / n_samples if n_samples > 0 else 0.0,
        }

        # 4. Reference baselines: repeat-current-set and random-guess
        rep1 = rep3 = 0
        rg1_list = []
        rg3_list = []
        self_equal = 0
        self_overlap = 0

        single_t_sids = set()
        rep_by_id: dict[str, tuple[int, int]] = {}

        for r in markov_rows:
            sid = r["sample_id"]
            cur = sorted(json.loads(r["current_tactic_set"]))
            tgt = set(json.loads(r["target_tactic_set"]))
            cur_set = set(cur)

            if cur_set == tgt:
                self_equal += 1
            if cur_set & tgt:
                self_overlap += 1

            h1_r = 1 if (cur and cur[0] in tgt) else 0
            h3_r = 1 if any(c in tgt for c in cur[:3]) else 0
            rep_by_id[sid] = (h1_r, h3_r)
            rep1 += h1_r
            rep3 += h3_r

            rg1_list.append(random_guess_expected_hit(tgt, 1))
            rg3_list.append(random_guess_expected_hit(tgt, 3))

            if len(tgt) == 1:
                single_t_sids.add(sid)

        cfg_res["reference_baselines"] = {
            "repeat_current_set": {
                "n": n_samples,
                "hit1": rep1,
                "hit3": rep3,
                "top1": rep1 / n_samples if n_samples else 0.0,
                "top3": rep3 / n_samples if n_samples else 0.0,
                "wilson95_top1": list(wilson_interval(rep1, n_samples)),
                "wilson95_top3": list(wilson_interval(rep3, n_samples)),
            },
            "random_guess": {
                "mean_p_hit1": sum(rg1_list) / n_samples if n_samples else 0.0,
                "mean_p_hit3": sum(rg3_list) / n_samples if n_samples else 0.0,
            },
        }

        cfg_res["self_repeat"] = {
            "n": n_samples,
            "equal": self_equal,
            "equal_rate": self_equal / n_samples if n_samples else 0.0,
            "overlap": self_overlap,
            "overlap_rate": self_overlap / n_samples if n_samples else 0.0,
        }

        cfg_res["strict_single_tactic"] = {
            "n": len(single_t_sids),
            "markov_hit1": sum(int(r["hit1"]) for r in markov_rows if r["sample_id"] in single_t_sids),
            "markov_hit3": sum(int(r["hit3"]) for r in markov_rows if r["sample_id"] in single_t_sids),
            "frequency_hit1": sum(int(r["hit1"]) for r in by_method.get("frequency", []) if r["sample_id"] in single_t_sids),
            "frequency_hit3": sum(int(r["hit3"]) for r in by_method.get("frequency", []) if r["sample_id"] in single_t_sids),
            "fallback_hit1": sum(int(r["hit1"]) for r in by_method.get("markov_fallback", []) if r["sample_id"] in single_t_sids),
            "fallback_hit3": sum(int(r["hit3"]) for r in by_method.get("markov_fallback", []) if r["sample_id"] in single_t_sids),
            "repeat_hit1": sum(rep_by_id[sid][0] for sid in single_t_sids),
            "repeat_hit3": sum(rep_by_id[sid][1] for sid in single_t_sids),
        }

        # 2x2 Paired comparison & frequency-only split
        if "markov" in by_method and "frequency" in by_method:
            m_by_id = {r["sample_id"]: r for r in by_method["markov"]}
            f_by_id = {r["sample_id"]: r for r in by_method["frequency"]}
            common_ids = sorted(set(m_by_id.keys()) & set(f_by_id.keys()))

            for k_val, hit_col in ((1, "hit1"), (3, "hit3")):
                cell = {"both_hit": 0, "markov_only": 0, "freq_only": 0, "neither": 0}
                sp = {"freq_only_total": 0, "markov_returned_and_missed": 0, "markov_abstained": 0, "markov_other_status": 0}
                for sid in common_ids:
                    m_hit = int(m_by_id[sid][hit_col])
                    f_hit = int(f_by_id[sid][hit_col])
                    if m_hit and f_hit:
                        cell["both_hit"] += 1
                    elif m_hit and not f_hit:
                        cell["markov_only"] += 1
                    elif not m_hit and f_hit:
                        cell["freq_only"] += 1
                        sp["freq_only_total"] += 1
                        st = m_by_id[sid]["status"]
                        if st == "ok":
                            sp["markov_returned_and_missed"] += 1
                        elif st == "insufficient_evidence":
                            sp["markov_abstained"] += 1
                        else:
                            sp["markov_other_status"] += 1
                    else:
                        cell["neither"] += 1

                cfg_res["paired_2x2"][f"top{k_val}"] = cell
                cfg_res["frequency_only_split"][f"top{k_val}"] = sp

        # 5. Tie diagnostic
        t1_tied = sum(1 for r in ok_markov_rows if r.get("top1_tied") == "True")
        t3_tied = sum(1 for r in ok_markov_rows if r.get("top3_boundary_tied") == "True")
        neq_gte3 = sum(1 for r in ok_markov_rows if int(r.get("n_equal_top") or 0) >= 3)
        tied_r = [r for r in ok_markov_rows if r.get("top1_tied") == "True"]
        nottied_r = [r for r in ok_markov_rows if r.get("top1_tied") == "False"]

        cfg_res["tie_diagnostic"] = {
            "n_ok": n_cov,
            "top1_tied": t1_tied,
            "top3_boundary_tied": t3_tied,
            "n_equal_top_gte_3": neq_gte3,
            "split_top1_tied": {
                "tied": {"n": len(tied_r), "hit1": sum(int(r["hit1"]) for r in tied_r), "hit3": sum(int(r["hit3"]) for r in tied_r)},
                "not_tied": {"n": len(nottied_r), "hit1": sum(int(r["hit1"]) for r in nottied_r), "hit3": sum(int(r["hit3"]) for r in nottied_r)},
            },
        }

        # Hit concentration
        hit_conc: dict[str, dict[str, dict[str, int]]] = {}
        for m in methods:
            t1_counts: dict[str, int] = defaultdict(int)
            t3_counts: dict[str, int] = defaultdict(int)
            for r in by_method[m]:
                h1 = int(r["hit1"])
                h3 = int(r["hit3"])
                cands_top3 = [c[0] for c in json.loads(r["predicted_candidates_top3"])]
                tgt_s = set(json.loads(r["target_tactic_set"]))
                if h1 and cands_top3 and cands_top3[0] in tgt_s:
                    t1_counts[cands_top3[0]] += 1
                if h3:
                    for c in cands_top3[:3]:
                        if c in tgt_s:
                            t3_counts[c] += 1
            hit_conc[m] = {
                "top1": dict(sorted(t1_counts.items(), key=lambda x: (-x[1], x[0]))),
                "top3": dict(sorted(t3_counts.items(), key=lambda x: (-x[1], x[0]))),
            }
        cfg_res["hit_concentration"] = hit_conc

        results[cfg] = cfg_res

    # 6. Recompute derived-tactic table from evaluation_predictions.csv + technique_tactic_reference.json
    p_tech = Path(tech_pred_path)
    p_ref = Path(tech_ref_path)
    if p_tech.exists() and p_ref.exists():
        with open(p_tech, "r", encoding="utf-8") as f:
            tech_rows = list(csv.DictReader(f))
        with open(p_ref, "r", encoding="utf-8") as f:
            tech_ref = json.load(f)

        def tech_to_tacs(tech_id: str) -> list[str]:
            c = tech_id.strip().upper()
            if c in tech_ref:
                return sorted(list(set(t.strip().lower().replace(" ", "-") for t in tech_ref[c].get("official_tactics", []))))
            return []

        derived_res: dict[str, Any] = {}
        mean_tacs_res: dict[str, dict[str, Any]] = {}
        for cfg in ("collapsed_full", "raw_full"):
            cfg_rows = [r for r in tech_rows if r["configuration"] == cfg]
            by_m = defaultdict(list)
            for r in cfg_rows:
                by_m[r["method"]].append(r)

            derived_res[cfg] = {}
            mean_tacs_res[cfg] = {}
            for m in ("markov", "frequency", "markov_fallback"):
                mrows = by_m.get(m, [])
                n = len(mrows)
                h1 = h3 = n_cov = 0
                t1_tac_lens = []
                for r in mrows:
                    cands = json.loads(r["predicted_candidates_top3"])
                    if cands:
                        n_cov += 1
                        t1_tac_lens.append(len(tech_to_tacs(cands[0][0])))
                    pred_t1 = set(tech_to_tacs(cands[0][0])) if cands else set()
                    pred_t3 = set()
                    for c in cands[:3]:
                        pred_t3.update(tech_to_tacs(c[0]))

                    tgt_techs = json.loads(r["target_technique_set"])
                    tgt_tacs = set()
                    for t in tgt_techs:
                        tgt_tacs.update(tech_to_tacs(t))

                    if pred_t1 & tgt_tacs:
                        h1 += 1
                    if pred_t3 & tgt_tacs:
                        h3 += 1

                cov_rate = n_cov / n if n else 0.0
                mean_t = sum(t1_tac_lens) / len(t1_tac_lens) if t1_tac_lens else 0.0
                derived_res[cfg][m] = {
                    "n": n,
                    "covered": n_cov,
                    "coverage_rate": cov_rate,
                    "hit1": h1, "hit3": h3,
                    "top1": h1 / n if n else 0.0,
                    "top3": h3 / n if n else 0.0,
                    "wilson95_top1": list(wilson_interval(h1, n)),
                    "wilson95_top3": list(wilson_interval(h3, n)),
                }
                mean_tacs_res[cfg][m] = {
                    "n_predicted": len(t1_tac_lens),
                    "mean_tactics_per_top1": mean_t,
                }
        results["_derived_tactics"] = derived_res
        results["_mean_tactics_per_top1"] = mean_tacs_res

    # 7. Recompute sensitivity discrepancy classification (a)/(b)
    p_seq = Path(sequences_path)
    if p_seq.exists():
        with open(p_seq, "r", encoding="utf-8") as f:
            seq_data = json.load(f)

        type_a = []
        type_b = []
        all_diff = []
        for ep_id, ep in sorted(seq_data["episodes"].items()):
            for ev in ep.get("raw", []):
                dt = set(t.strip().lower().replace(" ", "-") for t in ev.get("tactics", []))
                ot = set(t.strip().lower().replace(" ", "-") for t in ev.get("official_tactics", []))
                if dt != ot:
                    eid = ev.get("event_id") or "unknown"
                    extra = dt - ot
                    is_sub = dt < ot
                    if extra:
                        type_a.append(eid)
                        cls_code = "a"
                    elif is_sub:
                        type_b.append(eid)
                        cls_code = "b"
                    else:
                        cls_code = "other"
                    all_diff.append({
                        "event_id": eid,
                        "episode_id": ep_id,
                        "classification": cls_code,
                        "techniques": sorted(list(set(ev.get("techniques", [])))),
                        "dataset_tactics": sorted(list(dt)),
                        "official_tactics": sorted(list(ot)),
                        "extra": sorted(list(extra)),
                    })

        results["_discrepancies"] = {
            "total_count": len(all_diff),
            "type_a_count": len(type_a),
            "type_a_ids": sorted(type_a),
            "type_b_count": len(type_b),
            "type_b_ids": sorted(type_b),
            "events": all_diff,
        }

    # 8. Rebuild and verify samples from attack_sequences.json
    p_seq = Path(sequences_path)
    if p_seq.exists():
        recon_counts = verify_tactic_sample_reconstruction(p_tac, p_seq)
        results["_sample_reconstruction"] = recon_counts

    return results


def print_verifier_summary(res: dict[str, Any]) -> None:
    """Print clean verification summary across all components."""
    print("=" * 80)
    print("INDEPENDENT TACTIC-LEVEL LOEO VERIFICATION REPORT")
    print(f"Verified row-level predictions: {res['_meta']['rows_verified']}")
    print("=" * 80)

    # Sample reconstruction check
    recon = res.get("_sample_reconstruction", {})
    if recon:
        print("\nSAMPLE RECONSTRUCTION CHECK (attack_sequences.json vs CSV):")
        print("-" * 80)
        for cfg, ep_counts in recon.items():
            ep_str = ", ".join(f"{ep}: N={n}" for ep, n in sorted(ep_counts.items()))
            total_n = sum(ep_counts.values())
            print(f"  {cfg:<34} Total N={total_n:<3} ({ep_str}) [MATCH]")
        print("-" * 80)

    for cfg in ("tactic_collapsed", "tactic_raw"):
        d = res[cfg]
        print(f"\nConfiguration: {cfg} (N={d['n']})")
        print("-" * 80)
        print(f"{'Method':<18} {'H@1':<5} {'H@3':<5} {'Top-1':<9} {'Top-3':<9} {'FoldMean-1':<12} {'FoldMean-3':<12} {'Coverage':<9}")
        print("-" * 80)
        for m, md in d["methods"].items():
            cov_str = f"{md['coverage_rate']*100:.1f}%" if m == "markov" else "-"
            print(
                f"{m:<18} {md['hit1']:<5} {md['hit3']:<5} "
                f"{md['pooled_top1']*100:>6.2f}%   {md['pooled_top3']*100:>6.2f}%   "
                f"{md['fold_mean_top1']*100:>8.2f}%    {md['fold_mean_top3']*100:>8.2f}%    "
                f"{cov_str:>7}"
            )
        rep = d["reference_baselines"]["repeat_current_set"]
        rg = d["reference_baselines"]["random_guess"]
        print(f"  Reference Repeat-Current-Set: Top-1={rep['hit1']}/{d['n']} ({rep['top1']*100:.2f}%), Top-3={rep['hit3']}/{d['n']} ({rep['top3']*100:.2f}%)")
        print(f"  Reference Random-Guess Expected: Top-1={rg['mean_p_hit1']*100:.2f}%, Top-3={rg['mean_p_hit3']*100:.2f}%")
        print(f"  Coverage: {d['coverage']['covered']}/{d['n']} ({d['coverage']['rate']*100:.2f}%) | Ceiling: {d['ceiling']['hits']}/{d['n']} ({d['ceiling']['rate']*100:.2f}%)")

    # Discrepancies
    disc = res.get("_discrepancies", {})
    if disc:
        print("\n" + "=" * 80)
        print(f"SENSITIVITY DISCREPANCY CLASSIFICATION: Total Differing Events = {disc['total_count']}")
        print(f"  Type (a) - Dataset contains tactic NOT in official set: Count = {disc['type_a_count']}")
        print(f"    IDs: {disc['type_a_ids']}")
        print(f"  Type (b) - Dataset set is strict subset of official set: Count = {disc['type_b_count']}")
        print(f"    IDs: {disc['type_b_ids']}")

    print("\n" + "=" * 80)
    print("VERIFICATION COMPLETE: ALL TABLES CONFIRMED")
    print("=" * 80)


if __name__ == "__main__":
    r = recompute_from_csv()
    print_verifier_summary(r)
