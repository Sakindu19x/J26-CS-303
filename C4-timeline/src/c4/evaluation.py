"""Leave-one-episode-out (LOEO) evaluation of the C4 next-technique models.

Every number and explanatory sentence in the generated report is computed from the
run's data. Statements that are hypotheses are explicitly labelled
"Hypothesis (not tested)". No model logic lives here except the evaluation-only
extension "markov_fallback" and the diagnostic reference "repeat current set".
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from c4.mitre_reference import to_parent_technique
from c4.models.frequency import FrequencyBaseline
from c4.models.markov import MarkovModel


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

PRIMARY_CONFIG = "collapsed_full"
METHODS = ("markov", "frequency", "markov_fallback")
CSV_FIELDS = [
    "configuration", "fold_id", "sample_id", "episode_id", "method",
    "current_technique_set", "target_technique_set", "predicted_candidates_top3",
    "status", "hit1", "hit3", "support_mass", "support_episodes",
    "top1_tied", "top3_boundary_tied", "n_equal_top",
]


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------
def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score 95% interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z ** 2) / total
    center = (p + (z ** 2) / (2.0 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / total) + (z ** 2 / (4.0 * (total ** 2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def _rate(h: int, n: int) -> float:
    return h / n if n > 0 else 0.0


def _pct(h: int, n: int) -> str:
    return f"{100.0 * h / n:.2f}%" if n > 0 else "n/a"


def _cmp_word(a: int, b: int) -> str:
    return "above" if a > b else ("equal to" if a == b else "below")


def _hit_flags(cands: list[str], target: set[str]) -> tuple[int, int]:
    h1 = 1 if (cands and cands[0] in target) else 0
    h3 = 1 if any(c in target for c in cands[:3]) else 0
    return h1, h3


def compute_set_metrics(pred_target_pairs: list[tuple[set[str], set[str]]]) -> dict[str, Any]:
    """Set-based micro and macro precision/recall/F1.

    Micro: TP = sum |pred & target|, FP = sum |pred - target|, FN = sum |target - pred|
    (an abstention is an empty pred set, so it only adds FN).
    Macro: per-technique TP/FP/FN over every technique appearing in any target or
    prediction set, averaged over those techniques, zero_division = 0.
    """
    total_tp = sum(len(p & t) for p, t in pred_target_pairs)
    total_fp = sum(len(p - t) for p, t in pred_target_pairs)
    total_fn = sum(len(t - p) for p, t in pred_target_pairs)

    micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
    micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
    micro_f1 = (2.0 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) > 0 else 0.0

    classes_set: set[str] = set()
    for p, t in pred_target_pairs:
        classes_set.update(p)
        classes_set.update(t)
    classes = sorted(classes_set)

    ps: list[float] = []
    rs: list[float] = []
    fs: list[float] = []
    for c in classes:
        tp_c = sum(1 for p, t in pred_target_pairs if c in p and c in t)
        fp_c = sum(1 for p, t in pred_target_pairs if c in p and c not in t)
        fn_c = sum(1 for p, t in pred_target_pairs if c not in p and c in t)
        p_c = tp_c / (tp_c + fp_c) if (tp_c + fp_c) > 0 else 0.0
        r_c = tp_c / (tp_c + fn_c) if (tp_c + fn_c) > 0 else 0.0
        f_c = (2.0 * p_c * r_c / (p_c + r_c)) if (p_c + r_c) > 0 else 0.0
        ps.append(p_c)
        rs.append(r_c)
        fs.append(f_c)

    n_cls = len(classes)
    return {
        "micro": {"tp": total_tp, "fp": total_fp, "fn": total_fn,
                  "precision": micro_p, "recall": micro_r, "f1": micro_f1},
        "macro": {"num_classes": n_cls,
                  "precision": sum(ps) / n_cls if n_cls else 0.0,
                  "recall": sum(rs) / n_cls if n_cls else 0.0,
                  "f1": sum(fs) / n_cls if n_cls else 0.0},
    }


def _load_inputs() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    with open(PROCESSED_DIR / "attack_sequences.json", encoding="utf-8") as f:
        seqs = json.load(f)
    with open(PROCESSED_DIR / "loeo_folds.json", encoding="utf-8") as f:
        folds = json.load(f)
    with open(PROCESSED_DIR / "next_technique_samples.json", encoding="utf-8") as f:
        samples = json.load(f)
    return seqs, folds, samples


# ---------------------------------------------------------------------------
# LOEO evaluation of one configuration
# ---------------------------------------------------------------------------
def _support_for(markov: MarkovModel, members: list[str]) -> tuple[float, int]:
    """Total outgoing transition mass of the source technique(s) and distinct
    training episodes contributing evidence for them."""
    mass = 0.0
    eps: set[str] = set()
    for a in members:
        mass += sum(markov.counts[a].values())
        for ev_list in markov.supporting_evidence.get(a, {}).values():
            for ev in ev_list:
                eps.add(ev[0])
    return mass, len(eps)


def evaluate_loeo_slice(
    variant: str = "collapsed",
    granularity: str = "full",
    exclude_e3_s006: bool = False,
    save_fold_models: bool = True,
    sequences_data: dict[str, Any] | None = None,
    folds_data: list[dict[str, Any]] | None = None,
    samples_data: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run LOEO evaluation for one (variant, granularity) slice."""
    if sequences_data is None or folds_data is None or samples_data is None:
        s, f, sm = _load_inputs()
        sequences_data = sequences_data if sequences_data is not None else s
        folds_data = folds_data if folds_data is not None else f
        samples_data = samples_data if samples_data is not None else sm

    ep_sequences = sequences_data["episodes"]
    slice_samples = [s for s in samples_data if s["variant"] == variant and s["granularity"] == granularity]

    if exclude_e3_s006:
        kept = []
        for s in slice_samples:
            cur_eids = s.get("input_item_event_ids", [])[-1] if s.get("input_item_event_ids") else []
            tgt_eids = s.get("target_event_id", [])
            if isinstance(tgt_eids, str):
                tgt_eids = [tgt_eids]
            if "E3-S006" in cur_eids or "E3-S006" in tgt_eids:
                continue
            kept.append(s)
        slice_samples = kept

    config_name = f"{variant}_{granularity}" + ("_no_s006" if exclude_e3_s006 else "")

    rows: list[dict[str, Any]] = []
    fold_metrics: dict[str, dict[str, Any]] = {}
    preds: dict[str, dict[str, dict[str, Any]]] = {m: {} for m in METHODS}

    loeo_dir = MODELS_DIR / "loeo"
    if save_fold_models:
        loeo_dir.mkdir(parents=True, exist_ok=True)

    for fold in folds_data:
        fold_id = fold["fold_id"]
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]

        markov = MarkovModel(variant=variant, granularity=granularity).fit(sequences_data, training_episodes=train_eps)
        freq = FrequencyBaseline(variant=variant, granularity=granularity).fit(sequences_data, training_episodes=train_eps)

        assert test_ep not in markov.training_episodes, f"Leak in {fold_id}: {test_ep} in Markov training episodes"
        assert test_ep not in freq.training_episodes, f"Leak in {fold_id}: {test_ep} in Frequency training episodes"
        for a, targets in markov.supporting_evidence.items():
            for b, ev_list in targets.items():
                for ev in ev_list:
                    assert ev[0] != test_ep, f"Leak in {fold_id}: Markov evidence {a}->{b} references {test_ep}"
        for b, ev_list in freq.supporting_evidence.items():
            for ev in ev_list:
                assert ev[0] != test_ep, f"Leak in {fold_id}: Frequency evidence {b} references {test_ep}"

        if save_fold_models:
            markov.save(loeo_dir / f"{variant}_{granularity}_{fold_id}.json")
            markov.save(loeo_dir / f"markov_{variant}_{granularity}_{fold_id}.json")
            freq.save(loeo_dir / f"frequency_{variant}_{granularity}_{fold_id}.json")

        train_target_pool: set[str] = set()
        for ep in train_eps:
            items = ep_sequences[ep][variant]
            for i in range(len(items) - 1):
                train_target_pool.update(markov._extract_tech_set(items[i + 1]))

        fold_samples = [s for s in slice_samples if s["episode_id"] == test_ep]
        ceiling_hits = 0
        f_res = freq.predict(k=3)
        f_cands_raw = f_res["candidates"]
        f_cands = [c[0] for c in f_cands_raw]

        for s in fold_samples:
            sid = s["sample_id"]
            cur = s["current_technique_set"]
            tgt = set(s["target_technique_set"])
            if tgt & train_target_pool:
                ceiling_hits += 1

            m_full = markov.predict(cur, k=None)
            m_status = m_full["status"]
            if m_status == "ok":
                m_raw_all = [list(c) for c in m_full["candidates"]]
                m_raw = m_raw_all[:3]
                m_cands = [c[0] for c in m_raw]
                m1, m3 = _hit_flags(m_cands, tgt)
                mass, n_eps = _support_for(markov, m_full["members_used"])
                support_mass: Any = f"{mass:.10f}"
                support_eps: Any = n_eps

                probs = [c[1] for c in m_raw_all]
                is_t1_tied = len(probs) >= 2 and abs(probs[0] - probs[1]) < 1e-9
                is_t3_boundary_tied = len(probs) >= 4 and abs(probs[2] - probs[3]) < 1e-9
                eq_top = sum(1 for p in probs if abs(p - probs[0]) < 1e-9)
                top1_tied_val = "True" if is_t1_tied else "False"
                top3_boundary_tied_val = "True" if is_t3_boundary_tied else "False"
                n_equal_top_val = str(eq_top)
            else:
                m_raw = []
                m_cands = []
                m1, m3 = 0, 0
                support_mass, support_eps = "", ""
                top1_tied_val = ""
                top3_boundary_tied_val = ""
                n_equal_top_val = ""

            f1, f3 = _hit_flags(f_cands, tgt)
            if m_status == "ok":
                fb_status, fb_raw, fb1, fb3 = "ok_markov", m_raw, m1, m3
            else:
                fb_status, fb_raw = "fallback_frequency", [list(c) for c in f_cands_raw]
                fb1, fb3 = f1, f3

            per_method = {
                "markov": (m_status, m_raw, m1, m3),
                "frequency": (f_res["status"], [list(c) for c in f_cands_raw], f1, f3),
                "markov_fallback": (fb_status, fb_raw, fb1, fb3),
            }
            for method, (status, raw, h1, h3) in per_method.items():
                preds[method][sid] = {"status": status, "cands": [c[0] for c in raw], "hit1": h1, "hit3": h3}
                rows.append({
                    "configuration": config_name, "fold_id": fold_id, "sample_id": sid,
                    "episode_id": test_ep, "method": method,
                    "current_technique_set": json.dumps(cur),
                    "target_technique_set": json.dumps(sorted(tgt)),
                    "predicted_candidates_top3": json.dumps(raw[:3]),
                    "status": status, "hit1": h1, "hit3": h3,
                    "support_mass": support_mass if method == "markov" else "",
                    "support_episodes": support_eps if method == "markov" else "",
                    "top1_tied": top1_tied_val if method == "markov" else "",
                    "top3_boundary_tied": top3_boundary_tied_val if method == "markov" else "",
                    "n_equal_top": n_equal_top_val if method == "markov" else "",
                })

        n_fold = len(fold_samples)
        fm: dict[str, Any] = {
            "test_episode": test_ep, "training_episodes": train_eps, "n_samples": n_fold,
            "ceiling": {"hits": ceiling_hits, "rate": _rate(ceiling_hits, n_fold)},
        }
        for key, method in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
            ids = [s["sample_id"] for s in fold_samples]
            h1 = sum(preds[method][i]["hit1"] for i in ids)
            h3 = sum(preds[method][i]["hit3"] for i in ids)
            fm[key] = {"hit1": h1, "hit3": h3, "top1": _rate(h1, n_fold), "top3": _rate(h3, n_fold)}
        covered = sum(1 for s in fold_samples if preds["markov"][s["sample_id"]]["status"] == "ok")
        fm["markov"]["covered_samples"] = covered
        fm["markov"]["coverage"] = _rate(covered, n_fold)
        fold_metrics[fold_id] = fm

    n_total = len(slice_samples)
    sids = [s["sample_id"] for s in slice_samples]

    def pooled(method: str, ids: list[str]) -> tuple[int, int]:
        return (sum(preds[method][i]["hit1"] for i in ids), sum(preds[method][i]["hit3"] for i in ids))

    fold_list = list(fold_metrics.values())

    def fold_mean(key: str, which: str) -> float:
        return sum(f[key][which] for f in fold_list) / len(fold_list) if fold_list else 0.0

    headline: dict[str, Any] = {}
    for key, method in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
        h1, h3 = pooled(method, sids)
        headline[key] = {
            "hit1": h1, "hit3": h3, "top1": _rate(h1, n_total), "top3": _rate(h3, n_total),
            "wilson95_top1": list(wilson_interval(h1, n_total)),
            "wilson95_top3": list(wilson_interval(h3, n_total)),
            "fold_mean_top1": fold_mean(key, "top1"), "fold_mean_top3": fold_mean(key, "top3"),
        }

    cov_ids = [i for i in sids if preds["markov"][i]["status"] == "ok"]
    n_cov = len(cov_ids)
    cm1, cm3 = pooled("markov", cov_ids)
    cf1, cf3 = pooled("frequency", cov_ids)
    pooled_ceiling = sum(f["ceiling"]["hits"] for f in fold_list)
    headline["coverage"] = {
        "covered_samples": n_cov, "coverage_rate": _rate(n_cov, n_total), "covered_n": n_cov,
        "markov_on_covered_hit1": cm1, "markov_on_covered_hit3": cm3,
        "frequency_on_covered_hit1": cf1, "frequency_on_covered_hit3": cf3,
        "markov_on_covered_top1": _rate(cm1, n_cov), "markov_on_covered_top3": _rate(cm3, n_cov),
        "frequency_on_covered_top1": _rate(cf1, n_cov), "frequency_on_covered_top3": _rate(cf3, n_cov),
    }
    headline["ceiling"] = {"hits": pooled_ceiling, "ceiling_rate": _rate(pooled_ceiling, n_total)}

    single_ids = [s["sample_id"] for s in slice_samples if len(s["target_technique_set"]) == 1]
    strict: dict[str, Any] = {"n_samples": len(single_ids)}
    for key, method in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
        h1, h3 = pooled(method, single_ids)
        strict[f"{key}_hit1"], strict[f"{key}_hit3"] = h1, h3
        strict[f"{key}_top1"], strict[f"{key}_top3"] = _rate(h1, len(single_ids)), _rate(h3, len(single_ids))

    def pairs(method: str, k: int) -> list[tuple[set[str], set[str]]]:
        return [(set(preds[method][s["sample_id"]]["cands"][:k]), set(s["target_technique_set"])) for s in slice_samples]

    pr = {}
    for key, method in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
        for k in (1, 3):
            pr[f"{key}_top{k}"] = compute_set_metrics(pairs(method, k))

    paired: dict[str, dict[str, int]] = {}
    for k, hk in ((1, "hit1"), (3, "hit3")):
        cell = {"both_hit": 0, "markov_only": 0, "freq_only": 0, "neither": 0}
        for i in sids:
            m, f = preds["markov"][i][hk], preds["frequency"][i][hk]
            cell["both_hit" if m and f else "markov_only" if m else "freq_only" if f else "neither"] += 1
        paired[f"top{k}"] = cell

    results = {
        "config": config_name, "variant": variant, "granularity": granularity,
        "exclude_e3_s006": exclude_e3_s006, "n_samples": n_total,
        "headline": headline, "per_fold": fold_metrics,
        "strict_subset_single_target": strict, "precision_recall_f1": pr, "paired_2x2": paired,
    }
    return results, rows


# ---------------------------------------------------------------------------
# Row-level analysis (works purely on the prediction rows)
# ---------------------------------------------------------------------------
def analyze_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute per-configuration tables from prediction rows only."""
    out: dict[str, Any] = {}
    configs: list[str] = []
    for r in rows:
        if r["configuration"] not in configs:
            configs.append(r["configuration"])
    for cfg in configs:
        cr = [r for r in rows if r["configuration"] == cfg]
        by_m: dict[str, dict[str, dict[str, Any]]] = {m: {} for m in METHODS}
        for r in cr:
            by_m[r["method"]][r["sample_id"]] = r
        sids = sorted(by_m["markov"])
        n = len(sids)
        methods: dict[str, Any] = {}
        for m in METHODS:
            folds: dict[str, dict[str, int]] = {}
            for r in by_m[m].values():
                d = folds.setdefault(r["fold_id"], {"n": 0, "hit1": 0, "hit3": 0})
                d["n"] += 1
                d["hit1"] += int(r["hit1"])
                d["hit3"] += int(r["hit3"])
            folds = {k: folds[k] for k in sorted(folds)}
            h1 = sum(int(r["hit1"]) for r in by_m[m].values())
            h3 = sum(int(r["hit3"]) for r in by_m[m].values())
            methods[m] = {
                "n": len(by_m[m]), "hit1": h1, "hit3": h3,
                "pooled_top1": _rate(h1, len(by_m[m])), "pooled_top3": _rate(h3, len(by_m[m])),
                "fold_mean_top1": sum(_rate(d["hit1"], d["n"]) for d in folds.values()) / len(folds) if folds else 0.0,
                "fold_mean_top3": sum(_rate(d["hit3"], d["n"]) for d in folds.values()) / len(folds) if folds else 0.0,
                "per_fold": folds,
            }
        ok = [i for i in sids if by_m["markov"][i]["status"] == "ok"]
        methods["markov"]["coverage_n"] = len(ok)
        methods["markov"]["coverage"] = _rate(len(ok), n)

        paired: dict[str, dict[str, int]] = {}
        split: dict[str, dict[str, int]] = {}
        for k, hk in ((1, "hit1"), (3, "hit3")):
            cell = {"both_hit": 0, "markov_only": 0, "freq_only": 0, "neither": 0}
            sp = {"freq_only_total": 0, "markov_returned_and_missed": 0,
                  "markov_abstained": 0, "markov_other_status": 0}
            for i in sids:
                m = int(by_m["markov"][i][hk])
                f = int(by_m["frequency"][i][hk])
                cell["both_hit" if m and f else "markov_only" if m else "freq_only" if f else "neither"] += 1
                if f and not m:
                    sp["freq_only_total"] += 1
                    st = by_m["markov"][i]["status"]
                    if st == "ok":
                        sp["markov_returned_and_missed"] += 1
                    elif st == "insufficient_evidence":
                        sp["markov_abstained"] += 1
                    else:
                        sp["markov_other_status"] += 1
            paired[f"top{k}"] = cell
            split[f"top{k}"] = sp

        cov = {"n": len(ok)}
        for key, m in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
            cov[f"{key}_hit1"] = sum(int(by_m[m][i]["hit1"]) for i in ok)
            cov[f"{key}_hit3"] = sum(int(by_m[m][i]["hit3"]) for i in ok)

        buckets: dict[str, dict[str, int]] = {}
        for i in ok:
            e = by_m["markov"][i]["support_episodes"]
            d = buckets.setdefault(str(e), {"n": 0, "hit1": 0, "hit3": 0})
            d["n"] += 1
            d["hit1"] += int(by_m["markov"][i]["hit1"])
            d["hit3"] += int(by_m["markov"][i]["hit3"])
        buckets = {k: buckets[k] for k in sorted(buckets, key=lambda x: int(x))}

        # Tie diagnostics (Markov status == ok)
        tie_diag = {
            "n_ok": len(ok),
            "top1_tied": 0,
            "top3_boundary_tied": 0,
            "n_equal_top_gte_3": 0,
            "split_top1_tied": {
                "tied": {"n": 0, "hit1": 0, "hit3": 0},
                "not_tied": {"n": 0, "hit1": 0, "hit3": 0},
            },
        }
        for i in ok:
            r = by_m["markov"][i]
            is_t1 = r.get("top1_tied") == "True"
            is_t3 = r.get("top3_boundary_tied") == "True"
            n_eq = int(r.get("n_equal_top") or 0)
            if is_t1:
                tie_diag["top1_tied"] += 1
            if is_t3:
                tie_diag["top3_boundary_tied"] += 1
            if n_eq >= 3:
                tie_diag["n_equal_top_gte_3"] += 1

            h1 = int(r["hit1"])
            h3 = int(r["hit3"])
            bkey = "tied" if is_t1 else "not_tied"
            tie_diag["split_top1_tied"][bkey]["n"] += 1
            tie_diag["split_top1_tied"][bkey]["hit1"] += h1
            tie_diag["split_top1_tied"][bkey]["hit3"] += h3

        # Hit concentration by technique
        hit_conc: dict[str, dict[str, dict[str, int]]] = {}
        for m in METHODS:
            t1_counts: dict[str, int] = defaultdict(int)
            t3_counts: dict[str, int] = defaultdict(int)
            for i in sids:
                r = by_m[m][i]
                h1 = int(r["hit1"])
                h3 = int(r["hit3"])
                cands_top3 = [c[0] for c in json.loads(r["predicted_candidates_top3"])]
                tgt = set(json.loads(r["target_technique_set"]))
                if h1 and cands_top3 and cands_top3[0] in tgt:
                    t1_counts[cands_top3[0]] += 1
                if h3:
                    for c in cands_top3[:3]:
                        if c in tgt:
                            t3_counts[c] += 1
            hit_conc[m] = {
                "top1": dict(sorted(t1_counts.items(), key=lambda x: (-x[1], x[0]))),
                "top3": dict(sorted(t3_counts.items(), key=lambda x: (-x[1], x[0]))),
            }

        out[cfg] = {
            "n": n, "methods": methods, "paired": paired, "frequency_only_split": split,
            "covered_only": cov, "support_buckets": buckets,
            "tie_diagnostic": tie_diag, "hit_concentration": hit_conc,
        }
    return out


# ---------------------------------------------------------------------------
# Confusion analysis
# ---------------------------------------------------------------------------
def compute_confusion_analysis(
    slice_samples: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int], pd.DataFrame]:
    """Top-1 error pairs (full ID), abstentions per target, and a parent-level
    confusion matrix restricted to single-target samples (with ABSTAIN column)."""
    by_sid = {r["sample_id"]: r for r in rows if r["method"] == "markov"}
    err: dict[tuple[str, str], int] = defaultdict(int)
    abst: dict[str, int] = defaultdict(int)
    pm: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    tpar: set[str] = set()
    ppar: set[str] = set()

    for s in slice_samples:
        r = by_sid[s["sample_id"]]
        tgt = s["target_technique_set"]
        cands = json.loads(r["predicted_candidates_top3"]) if isinstance(r["predicted_candidates_top3"], str) else r["predicted_candidates_top3"]
        top1 = cands[0][0] if (cands and r["status"] == "ok") else None
        if r["status"] == "insufficient_evidence":
            for t in tgt:
                abst[t] += 1
        elif top1 is not None and top1 not in tgt:
            for t in tgt:
                err[(t, top1)] += 1
        if len(tgt) == 1:
            tp = to_parent_technique(tgt[0])
            tpar.add(tp)
            if top1 is None:
                pm[tp]["ABSTAIN"] += 1
            else:
                pp = to_parent_technique(top1)
                ppar.add(pp)
                pm[tp][pp] += 1

    pairs = [{"target_technique": k[0], "predicted_top1": k[1], "count": v}
             for k, v in sorted(err.items(), key=lambda x: (-x[1], x[0]))]
    cols = sorted(ppar) + ["ABSTAIN"]
    data = [dict({"target_parent": r}, **{c: pm[r][c] for c in cols}) for r in sorted(tpar)]
    df = pd.DataFrame(data, columns=["target_parent"] + cols).set_index("target_parent")
    return pairs, dict(sorted(abst.items(), key=lambda x: (-x[1], x[0]))), df


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------
def self_repeat_rates(samples: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per slice: share of samples whose target shares >=1 technique with the
    current set, and share where target set == current set."""
    out: dict[str, dict[str, Any]] = {}
    for variant in ("raw", "collapsed"):
        for gran in ("full", "parent"):
            ss = [s for s in samples if s["variant"] == variant and s["granularity"] == gran]
            n = len(ss)
            overlap = sum(1 for s in ss if set(s["current_technique_set"]) & set(s["target_technique_set"]))
            equal = sum(1 for s in ss if set(s["current_technique_set"]) == set(s["target_technique_set"]))
            out[f"{variant}_{gran}"] = {
                "n": n, "overlap": overlap, "equal": equal,
                "overlap_rate": _rate(overlap, n), "equal_rate": _rate(equal, n),
            }
    return out


def repeat_current_set_reference(current_set: list[str], k: int = 3) -> list[str]:
    """DIAGNOSTIC REFERENCE ONLY (not a proposed model): predict the members of
    the current technique set, ties by technique ID ascending, truncated to k."""
    return sorted(set(current_set))[:k]


def repeat_current_set_results(samples: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Evaluate the repeat-current-set reference on all four slices."""
    out: dict[str, dict[str, Any]] = {}
    for variant in ("raw", "collapsed"):
        for gran in ("full", "parent"):
            ss = [s for s in samples if s["variant"] == variant and s["granularity"] == gran]
            n = len(ss)
            h1 = h3 = 0
            for s in ss:
                tgt = set(s["target_technique_set"])
                a, b = _hit_flags(repeat_current_set_reference(s["current_technique_set"], 3), tgt)
                c, _ = _hit_flags(repeat_current_set_reference(s["current_technique_set"], 1), tgt)
                h1 += c
                h3 += b
            out[f"{variant}_{gran}"] = {
                "n": n, "hit1": h1, "hit3": h3,
                "top1": _rate(h1, n), "top3": _rate(h3, n),
                "wilson95_top1": list(wilson_interval(h1, n)),
                "wilson95_top3": list(wilson_interval(h3, n)),
            }
    return out


def frequency_top_targets_per_fold(
    sequences: dict[str, Any], folds: list[dict[str, Any]], samples: list[dict[str, Any]],
) -> dict[str, Any]:
    """collapsed/full: per fold, the baseline's top-3 targets, how often each is a
    target in the training episodes, and how many test samples contain it."""
    out: dict[str, Any] = {}
    cf = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]
    for fold in folds:
        freq = FrequencyBaseline("collapsed", "full").fit(sequences, training_episodes=fold["training_episodes"])
        test_samples = [s for s in cf if s["episode_id"] == fold["test_episode"]]
        top = freq.predict(k=3)["candidates"]
        n_train_transitions = int(freq.n_step_transitions) if not isinstance(freq.n_step_transitions, dict) else sum(freq.n_step_transitions.values())
        entries = []
        for tech, prob in top:
            entries.append({
                "technique": tech, "probability": prob,
                "training_transitions_with_target": len(freq.supporting_evidence.get(tech, [])),
                "test_samples_containing_target": sum(1 for s in test_samples if tech in s["target_technique_set"]),
            })
        top_set = [t for t, _ in top]
        out[fold["fold_id"]] = {
            "test_episode": fold["test_episode"], "n_test_samples": len(test_samples),
            "training_transitions": n_train_transitions, "top3": entries,
            "test_samples_hit_by_any_top3": sum(1 for s in test_samples if set(top_set) & set(s["target_technique_set"])),
        }
    return out


def compute_frequent_targets(
    samples: list[dict[str, Any]], config: str = PRIMARY_CONFIG,
) -> list[dict[str, Any]]:
    """Primary slice (collapsed/full): 5 most frequent targets pooled over all 4 episodes."""
    cf = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]
    c: Counter[str] = Counter()
    for s in cf:
        for t in s["target_technique_set"]:
            c[t] += 1
    return [{"technique": t, "count": count} for t, count in c.most_common(5)]


# ---------------------------------------------------------------------------
# Examples chosen by rule
# ---------------------------------------------------------------------------
def select_examples(rows: list[dict[str, Any]], config: str = PRIMARY_CONFIG) -> dict[str, Any]:
    """Rule-based example selection from the prediction rows."""
    by: dict[str, dict[str, dict[str, Any]]] = {m: {} for m in METHODS}
    for r in rows:
        if r["configuration"] == config:
            by[r["method"]][r["sample_id"]] = r
    sids = sorted(by["markov"])

    def item(sid: str) -> dict[str, Any]:
        m, f = by["markov"][sid], by["frequency"][sid]
        return {
            "sample_id": sid, "fold_id": m["fold_id"],
            "current_technique_set": json.loads(m["current_technique_set"]),
            "target_technique_set": json.loads(m["target_technique_set"]),
            "markov_candidates": json.loads(m["predicted_candidates_top3"]),
            "frequency_candidates": json.loads(f["predicted_candidates_top3"]),
            "markov_status": m["status"],
            "markov_hit1": int(m["hit1"]), "frequency_hit1": int(f["hit1"]),
        }

    rule_i = [i for i in sids if int(by["markov"][i]["hit1"]) == 1]
    rule_ii = [i for i in sids if int(by["frequency"][i]["hit1"]) == 1
               and int(by["markov"][i]["hit1"]) == 0 and by["markov"][i]["status"] == "ok"][:3]
    rule_iii = [i for i in sids if by["markov"][i]["status"] == "insufficient_evidence"][:3]
    return {
        "configuration": config,
        "rule_i": "every sample where Markov hit at Top-1",
        "rule_ii": "up to 3 samples where Frequency hit at Top-1, Markov status ok and Markov missed at Top-1, ordered by sample_id",
        "rule_iii": "up to 3 samples where Markov abstained (insufficient_evidence), ordered by sample_id",
        "markov_top1_hits": [item(i) for i in rule_i],
        "frequency_only_top1_markov_ok": [item(i) for i in rule_ii],
        "abstentions": [item(i) for i in rule_iii],
    }


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def generate_evaluation_figures(primary: dict[str, Any], df_parent: pd.DataFrame, output_dir: Path | str) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    n = primary["n_samples"]
    head = primary["headline"]

    fig, ax = plt.subplots(figsize=(9, 5), dpi=200)
    methods = ["Markov", "Frequency", "Markov+freq fallback (extension)"]
    keys = ["markov", "frequency", "fallback"]
    t1 = [head[k]["top1"] * 100 for k in keys]
    t3 = [head[k]["top3"] * 100 for k in keys]
    x = np.arange(len(methods))
    r1 = ax.bar(x - 0.175, t1, 0.35, label="Top-1 (%)", color="#2b5c8f")
    r2 = ax.bar(x + 0.175, t3, 0.35, label="Top-3 (%)", color="#e27c38")
    cov = head["coverage"]["coverage_rate"] * 100
    ceil = head["ceiling"]["ceiling_rate"] * 100
    ax.axhline(cov, color="#6c757d", linestyle="--", label=f"Markov coverage ({cov:.1f}%)")
    ax.axhline(ceil, color="#28a745", linestyle=":", label=f"Target ceiling ({ceil:.1f}%)")
    ax.set_ylabel("Percent of test samples")
    ax.set_title(f"{primary['config']} pooled over LOEO folds (N={n})")
    ax.set_xticks(x)
    ax.set_xticklabels(methods, fontsize=9)
    ax.set_ylim(0, max(cov, ceil, max(t3)) + 10)
    ax.legend(fontsize=8, loc="upper left")
    for rect in list(r1) + list(r2):
        ax.annotate(f"{rect.get_height():.1f}%", (rect.get_x() + rect.get_width() / 2, rect.get_height()),
                    xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8)
    plt.tight_layout()
    fig.savefig(out / "headline_metrics.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=200)
    fids = sorted(primary["per_fold"])
    labels = [f"{f} (test {primary['per_fold'][f]['test_episode']}, N={primary['per_fold'][f]['n_samples']})" for f in fids]
    x = np.arange(len(fids))
    series = [("markov", "top1", "Markov Top-1", "#1f77b4"), ("markov", "top3", "Markov Top-3", "#aec7e8"),
              ("frequency", "top1", "Frequency Top-1", "#ff7f0e"), ("frequency", "top3", "Frequency Top-3", "#ffbb78")]
    vals_all = []
    for j, (mk, tk, lab, col) in enumerate(series):
        vals = [primary["per_fold"][f][mk][tk] * 100 for f in fids]
        vals_all += vals
        ax.bar(x + (j - 1.5) * 0.2, vals, 0.2, label=lab, color=col)
    ax.set_ylabel("Percent of fold test samples")
    ax.set_title("Per-fold results")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0, max(vals_all + [1]) + 5)
    ax.legend(fontsize=8)
    plt.tight_layout()
    fig.savefig(out / "per_fold_performance.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 10), dpi=200)
    data = df_parent.values if df_parent.size else np.zeros((1, 1))
    im = ax.imshow(data, cmap="Blues", aspect="auto")
    ax.set_xticks(np.arange(len(df_parent.columns)))
    ax.set_yticks(np.arange(len(df_parent.index)))
    ax.set_xticklabels(list(df_parent.columns), rotation=90, fontsize=8)
    ax.set_yticklabels(list(df_parent.index), fontsize=8)
    ax.set_xlabel("Predicted parent technique (Markov Top-1) or ABSTAIN")
    ax.set_ylabel("Target parent technique")
    ax.set_title(f"Parent-level confusion (single-target samples, N={int(data.sum())})")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            if data[i, j] > 0:
                ax.text(j, i, str(int(data[i, j])), ha="center", va="center", fontsize=7,
                        color="white" if data[i, j] > data.max() / 2 else "black")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    plt.tight_layout()
    fig.savefig(out / "confusion_matrix_parent.png")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
SLICE_SPECS = [
    ("collapsed", "full", False, True),
    ("collapsed", "parent", False, True),
    ("raw", "full", False, True),
    ("raw", "parent", False, True),
    ("collapsed", "full", True, False),
]


def run_full_evaluation() -> dict[str, Any]:
    """Run every configuration and write all evaluation outputs."""
    seqs, folds, samples = _load_inputs()

    slices: dict[str, Any] = {}
    all_rows: list[dict[str, Any]] = []
    for variant, gran, excl, save in SLICE_SPECS:
        res, rows = evaluate_loeo_slice(variant, gran, excl, save, seqs, folds, samples)
        slices[res["config"]] = res
        all_rows.extend(rows)

    csv_out_path = PROCESSED_DIR / "evaluation_predictions.csv"
    if csv_out_path.exists():
        with open(csv_out_path, "r", encoding="utf-8") as f:
            old_rows = list(csv.DictReader(f))
        assert len(old_rows) == len(all_rows), (
            f"Row count mismatch: old={len(old_rows)}, new={len(all_rows)}"
        )
        mismatches = 0
        for i, (old_r, new_r) in enumerate(zip(old_rows, all_rows)):
            for k in ("configuration", "fold_id", "sample_id", "method", "status", "hit1", "hit3"):
                if str(old_r[k]) != str(new_r[k]):
                    mismatches += 1
                    raise AssertionError(
                        f"Row {i} ({new_r['sample_id']} {new_r['method']}) mismatch on key {k}: "
                        f"old='{old_r[k]}', new='{new_r[k]}'"
                    )
        print(f"Comparison against existing predictions CSV: rows compared = {len(all_rows)}, mismatches = {mismatches}")

    with open(csv_out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, restval="")
        w.writeheader()
        w.writerows(all_rows)

    primary = slices[PRIMARY_CONFIG]
    primary_samples = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]
    primary_rows = [r for r in all_rows if r["configuration"] == PRIMARY_CONFIG]
    err_pairs, abst, df_parent = compute_confusion_analysis(primary_samples, primary_rows)
    df_parent.to_csv(REPORTS_DIR / "confusion_matrix_parent.csv", lineterminator="\n")
    generate_evaluation_figures(primary, df_parent, FIGURES_DIR)

    nz = int((df_parent.values > 0).sum()) if df_parent.size else 0
    payload: dict[str, Any] = {
        "metadata": {
            "evaluation_type": "Leave-One-Episode-Out (LOEO)",
            "evaluator": "c4.evaluation",
            "primary_configuration": PRIMARY_CONFIG,
        },
        "slices": slices,
        "primary_slice": primary,
        "sensitivity_slices": {k: v for k, v in slices.items() if k != PRIMARY_CONFIG},
        "row_analysis": analyze_rows(all_rows),
        "confusion_analysis": {
            "top_error_pairs": err_pairs[:10],
            "abstentions_by_target": abst,
            "parent_matrix_rows": int(df_parent.shape[0]),
            "parent_matrix_columns": int(df_parent.shape[1]),
            "parent_matrix_nonzero_cells": nz,
            "parent_matrix_total_cells": int(df_parent.size),
            "parent_matrix_samples": int(df_parent.values.sum()) if df_parent.size else 0,
        },
        "diagnostics": {
            "self_repeat": self_repeat_rates(samples),
            "repeat_current_set_reference": repeat_current_set_results(samples),
            "frequency_top_targets_per_fold": frequency_top_targets_per_fold(seqs, folds, samples),
            "frequent_targets_pooled": compute_frequent_targets(samples, PRIMARY_CONFIG),
        },
        "examples": select_examples(all_rows, PRIMARY_CONFIG),
    }
    with open(REPORTS_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)
    render_evaluation_markdown(payload, REPORTS_DIR / "evaluation_report.md")
    return payload


# ---------------------------------------------------------------------------
# Report rendering (every number / sentence computed from `data`)
# ---------------------------------------------------------------------------
def _cands(c: list[list[Any]]) -> str:
    return ", ".join(f"{t} ({p:.3f})" for t, p in c) if c else "(none)"


def render_evaluation_markdown(data: dict[str, Any], output_path: Path | str) -> None:
    ra = data["row_analysis"]
    slices = data["slices"]
    prim = data["primary_slice"]
    pcfg = prim["config"]
    diag = data["diagnostics"]
    conf = data["confusion_analysis"]
    ex = data["examples"]
    configs = list(slices)
    L: list[str] = []
    A = L.append

    A("# C4 Next-Technique Prediction: LOEO Evaluation Report")
    A("")
    A("All numbers and explanatory sentences below are generated from this run's prediction rows. "
      "Sentences labelled *Hypothesis (not tested)* are not backed by a computation in this report. "
      "Probabilities are estimates from observed training sequences, not guarantees. "
      "No significance test is performed and nothing here supports a generalization claim.")
    A("")
    A("## 1. Setup")
    A("")
    A(f"- Evaluation unit: samples in `data/processed/next_technique_samples.json`; primary configuration `{pcfg}` (N={prim['n_samples']}).")
    A(f"- Folds: {len(prim['per_fold'])} leave-one-episode-out folds (test = one complete episode, training = the others). "
      "A fresh `MarkovModel` and `FrequencyBaseline` is fitted per fold on training episodes only; "
      "runtime assertions check that no fold model lists the test episode as training and no evidence entry references it.")
    A("- Prediction: from `current_technique_set` only, k=3, no smoothing, no tuning, no randomness. "
      "Markov abstains when status is `insufficient_evidence` (counted as a miss). Frequency never abstains.")
    A("- `markov_fallback` is an **extension, NOT part of the proposal**, implemented in the evaluation module only: Markov when status is ok, else the frequency prediction.")
    A(f"- Configurations run: {', '.join(f'`{c}`' for c in configs)}.")
    A("")
    A("## 2. Definitions")
    A("")
    A("- **Hit@k**: 1 if at least one of the top-k returned candidates is in the target set, else 0. Abstention is a miss. No padding of Top-3.")
    A("- **Pooled rate**: hits / N over all test samples of the configuration. **Fold mean**: unweighted mean of the per-fold rates.")
    A("- **Coverage**: fraction of samples with Markov status ok.")
    A("- **Ceiling**: fraction of test samples whose target set contains at least one technique that appears as a target in that fold's training episodes.")
    A("- **Micro P/R/F1**: TP = sum |pred ∩ target|, FP = sum |pred − target|, FN = sum |target − pred| (abstention = empty pred set, so only FN).")
    A("- **Macro P/R/F1**: per-technique TP/FP/FN over every technique appearing in any target or prediction, averaged over those techniques, zero_division = 0.")
    A("- **Wilson 95% interval**: score interval for a pooled hit rate. Samples within an episode are not independent, so the intervals understate uncertainty.")
    A("")

    A("## 3. Results by configuration and method")
    A("")
    A("| Configuration | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 | Markov coverage |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for c in configs:
        for m in METHODS:
            d = ra[c]["methods"][m]
            cov = _pct(ra[c]["methods"]["markov"]["coverage_n"], ra[c]["n"]) if m == "markov" else "-"
            A(f"| {c} | {m} | {d['n']} | {d['hit1']} | {d['hit3']} | {100*d['pooled_top1']:.2f}% | {100*d['pooled_top3']:.2f}% | "
              f"{100*d['fold_mean_top1']:.2f}% | {100*d['fold_mean_top3']:.2f}% | {cov} |")
    A("")
    A("### Wilson 95% intervals (pooled)")
    A("")
    A("| Configuration | Method | N | Top-1 interval | Top-3 interval |")
    A("|---|---|---|---|---|")
    for c in configs:
        for key, m in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
            h = slices[c]["headline"][key]
            A(f"| {c} | {m} | {slices[c]['n_samples']} | [{100*h['wilson95_top1'][0]:.2f}%, {100*h['wilson95_top1'][1]:.2f}%] | "
              f"[{100*h['wilson95_top3'][0]:.2f}%, {100*h['wilson95_top3'][1]:.2f}%] |")
    A("")
    A("### Markov versus frequency baseline (computed comparison of hit counts)")
    A("")
    for c in configs:
        mm, ff = ra[c]["methods"]["markov"], ra[c]["methods"]["frequency"]
        n = ra[c]["n"]
        A(f"- `{c}`: Top-1 Markov {mm['hit1']}/{n} is **{_cmp_word(mm['hit1'], ff['hit1'])}** Frequency {ff['hit1']}/{n}; "
          f"Top-3 Markov {mm['hit3']}/{n} is **{_cmp_word(mm['hit3'], ff['hit3'])}** Frequency {ff['hit3']}/{n}.")
    A("")

    A("## 4. Per-fold results")
    A("")
    A("| Configuration | Fold | Test episode | Method | N | Top-1 hits | Top-3 hits |")
    A("|---|---|---|---|---|---|---|")
    for c in configs:
        for m in METHODS:
            for fid, d in ra[c]["methods"][m]["per_fold"].items():
                A(f"| {c} | {fid} | {slices[c]['per_fold'][fid]['test_episode']} | {m} | {d['n']} | {d['hit1']} | {d['hit3']} |")
    A("")

    A("## 5. Coverage and ceiling")
    A("")
    A("| Configuration | N | Markov covered | Coverage | Samples with target seen in training (ceiling) | Ceiling rate |")
    A("|---|---|---|---|---|---|")
    for c in configs:
        h = slices[c]["headline"]
        A(f"| {c} | {slices[c]['n_samples']} | {h['coverage']['covered_samples']} | {_pct(h['coverage']['covered_samples'], slices[c]['n_samples'])} | "
          f"{h['ceiling']['hits']} | {_pct(h['ceiling']['hits'], slices[c]['n_samples'])} |")
    A("")
    A(f"Per-fold ceiling and coverage for `{pcfg}`:")
    A("")
    A("| Fold | Test episode | N | Covered | Ceiling hits |")
    A("|---|---|---|---|---|")
    for fid, f in sorted(prim["per_fold"].items()):
        A(f"| {fid} | {f['test_episode']} | {f['n_samples']} | {f['markov']['covered_samples']} | {f['ceiling']['hits']} |")
    A("")

    A("## 6. Covered-only comparison (samples where Markov status is ok)")
    A("")
    A("| Configuration | Covered N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |")
    A("|---|---|---|---|---|---|---|---|")
    for c in configs:
        v = ra[c]["covered_only"]
        A(f"| {c} | {v['n']} | {v['markov_hit1']} | {v['markov_hit3']} | {v['frequency_hit1']} | {v['frequency_hit3']} | "
          f"{v['fallback_hit1']} | {v['fallback_hit3']} |")
    A("")
    A("Values are hit counts on that subset.")
    A("")

    A("## 7. Strict subset (target set has exactly one technique)")
    A("")
    A("| Configuration | N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |")
    A("|---|---|---|---|---|---|---|---|")
    for c in configs:
        s = slices[c]["strict_subset_single_target"]
        A(f"| {c} | {s['n_samples']} | {s['markov_hit1']} | {s['markov_hit3']} | {s['frequency_hit1']} | {s['frequency_hit3']} | "
          f"{s['fallback_hit1']} | {s['fallback_hit3']} |")
    A("")
    A("Values are hit counts.")
    A("")

    A(f"## 8. Precision / recall / F1 (`{pcfg}`)")
    A("")
    A("| Method | Cutoff | TP | FP | FN | Micro P | Micro R | Micro F1 | Macro P | Macro R | Macro F1 | Classes |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for key in ("markov", "frequency", "fallback"):
        for k in (1, 3):
            p = prim["precision_recall_f1"][f"{key}_top{k}"]
            mi, ma = p["micro"], p["macro"]
            A(f"| {key} | Top-{k} | {mi['tp']} | {mi['fp']} | {mi['fn']} | {mi['precision']:.4f} | {mi['recall']:.4f} | {mi['f1']:.4f} | "
              f"{ma['precision']:.4f} | {ma['recall']:.4f} | {ma['f1']:.4f} | {ma['num_classes']} |")
    A("")

    A("## 9. Paired comparison (Markov vs Frequency, counts only)")
    A("")
    A("| Configuration | k | Both hit | Markov-only | Frequency-only | Neither |")
    A("|---|---|---|---|---|---|")
    for c in configs:
        for k in (1, 3):
            p = ra[c]["paired"][f"top{k}"]
            A(f"| {c} | {k} | {p['both_hit']} | {p['markov_only']} | {p['freq_only']} | {p['neither']} |")
    A("")
    A("### Frequency-only hits split by Markov status")
    A("")
    A("| Configuration | k | Frequency-only hits | Markov returned a prediction and missed (status ok) | Markov abstained (insufficient_evidence) | Other status |")
    A("|---|---|---|---|---|---|")
    for c in configs:
        for k in (1, 3):
            s = ra[c]["frequency_only_split"][f"top{k}"]
            A(f"| {c} | {k} | {s['freq_only_total']} | {s['markov_returned_and_missed']} | {s['markov_abstained']} | {s['markov_other_status']} |")
    A("")
    for c in configs:
        for k in (1, 3):
            s = ra[c]["frequency_only_split"][f"top{k}"]
            A(f"- `{c}`: Of {s['freq_only_total']} frequency-only Top-{k} hits, {s['markov_returned_and_missed']} occurred where Markov "
              f"returned a prediction and missed, and {s['markov_abstained']} where Markov abstained.")
    A("")

    A("## 10. Sensitivity configurations")
    A("")
    A("Sensitivity runs use the same code path. Their hit counts appear in sections 3-9 (one row per configuration); "
      "the comparison sentences in section 3 are computed. The `collapsed_full_no_s006` configuration "
      f"has N={slices['collapsed_full_no_s006']['n_samples']} versus N={prim['n_samples']} for `{pcfg}`.")
    A("")
    A("Hypothesis (not tested): differences between raw/collapsed or full/parent configurations may reflect changes in vocabulary size "
      "or in the number of repeated consecutive techniques; this report does not test either explanation (see Diagnostics for repeat rates).")
    A("")

    A("## 11. Confusion analysis")
    A("")
    A(f"### Most frequent Top-1 errors at full ID (`{pcfg}`; Markov status ok and Top-1 not in target)")
    A("")
    A("| Target technique | Predicted Top-1 | Count |")
    A("|---|---|---|")
    for e in conf["top_error_pairs"]:
        A(f"| {e['target_technique']} | {e['predicted_top1']} | {e['count']} |")
    A("")
    A("### Abstentions by target technique (a sample with several targets counts once per target)")
    A("")
    A("| Target technique | Abstentions |")
    A("|---|---|")
    for t, c in list(conf["abstentions_by_target"].items())[:15]:
        A(f"| {t} | {c} |")
    A("")
    A(f"Parent-level confusion matrix (single-target samples only, N={conf['parent_matrix_samples']}): "
      f"{conf['parent_matrix_rows']} target rows x {conf['parent_matrix_columns']} prediction columns (including ABSTAIN), "
      f"{conf['parent_matrix_nonzero_cells']} of {conf['parent_matrix_total_cells']} cells non-zero "
      f"({_pct(conf['parent_matrix_nonzero_cells'], conf['parent_matrix_total_cells'])}); the matrix is sparse. "
      "Saved as `reports/confusion_matrix_parent.csv` and `reports/figures/confusion_matrix_parent.png`.")
    A("")

    A(f"## 12. Examples chosen by rule (`{ex['configuration']}`)")
    A("")
    A(f"Rules: (i) {ex['rule_i']}; (ii) {ex['rule_ii']}; (iii) {ex['rule_iii']}.")
    A("")
    for title, key in (("(i) Markov Top-1 hits", "markov_top1_hits"),
                       ("(ii) Frequency-only Top-1 hits with Markov status ok", "frequency_only_top1_markov_ok"),
                       ("(iii) Abstention cases", "abstentions")):
        A(f"### {title} ({len(ex[key])} shown)")
        A("")
        if not ex[key]:
            A("None matched the rule.")
            A("")
            continue
        A("| Sample | Fold | Current set | Target set | Markov status | Markov candidates | Frequency candidates |")
        A("|---|---|---|---|---|---|---|")
        for it in ex[key]:
            A(f"| {it['sample_id']} | {it['fold_id']} | {', '.join(it['current_technique_set'])} | {', '.join(it['target_technique_set'])} | "
              f"{it['markov_status']} | {_cands(it['markov_candidates'])} | {_cands(it['frequency_candidates'])} |")
        A("")

    A("## 13. Diagnostics")
    A("")
    A("### 13.1 Self-repeat rate per slice (all samples of the slice)")
    A("")
    A("| Slice | N | Target shares >=1 technique with current set | Rate | Target == current set | Rate |")
    A("|---|---|---|---|---|---|")
    for s, d in diag["self_repeat"].items():
        A(f"| {s} | {d['n']} | {d['overlap']} | {_pct(d['overlap'], d['n'])} | {d['equal']} | {_pct(d['equal'], d['n'])} |")
    A("")
    A("### 13.2 Repeat-current-set reference (DIAGNOSTIC REFERENCE, not a proposed model)")
    A("")
    A("Top-k candidates are the members of the current set (ties by technique ID ascending, truncated to k). "
      "It uses no training data, so it is evaluated on every sample of each slice.")
    A("")
    A("| Slice | N | Top-1 hits | Top-1 | Top-1 Wilson 95% | Top-3 hits | Top-3 | Top-3 Wilson 95% |")
    A("|---|---|---|---|---|---|---|---|")
    for s, d in diag["repeat_current_set_reference"].items():
        A(f"| {s} | {d['n']} | {d['hit1']} | {100*d['top1']:.2f}% | [{100*d['wilson95_top1'][0]:.2f}%, {100*d['wilson95_top1'][1]:.2f}%] | "
          f"{d['hit3']} | {100*d['top3']:.2f}% | [{100*d['wilson95_top3'][0]:.2f}%, {100*d['wilson95_top3'][1]:.2f}%] |")
    A("")
    A("Comparison with the proposal methods on the same slice (hit counts, computed):")
    A("")
    for s, d in diag["repeat_current_set_reference"].items():
        if s in ra:
            mm, ff = ra[s]["methods"]["markov"], ra[s]["methods"]["frequency"]
            A(f"- `{s}`: repeat-current-set Top-1 {d['hit1']}/{d['n']} is {_cmp_word(d['hit1'], mm['hit1'])} Markov ({mm['hit1']}) "
              f"and {_cmp_word(d['hit1'], ff['hit1'])} Frequency ({ff['hit1']}); Top-3 {d['hit3']}/{d['n']} is "
              f"{_cmp_word(d['hit3'], mm['hit3'])} Markov ({mm['hit3']}) and {_cmp_word(d['hit3'], ff['hit3'])} Frequency ({ff['hit3']}).")
    A("")
    A("### 13.3 Markov hit rate by support strength (status ok only)")
    A("")
    A("`support_episodes` is the number of distinct training episodes contributing evidence for the source technique(s); "
      "`support_mass` (per row in `evaluation_predictions.csv`) is their total outgoing transition mass.")
    A("")
    A("| Configuration | support_episodes | N | Top-1 hits | Top-3 hits |")
    A("|---|---|---|---|---|")
    small = False
    for c in configs:
        for b, d in ra[c]["support_buckets"].items():
            A(f"| {c} | {b} | {d['n']} | {d['hit1']} | {d['hit3']} |")
            if d["n"] < 30:
                small = True
    A("")
    if small:
        A("Some buckets have fewer than 30 samples, so these buckets are too small for inference.")
        A("")
    A(f"### 13.4 What the frequency baseline predicts per fold (`{pcfg}`)")
    A("")
    A("| Fold | Test episode | Test N | Rank | Technique | Probability | Training transitions with this target | Test samples containing it as target |")
    A("|---|---|---|---|---|---|---|---|")
    for fid, d in diag["frequency_top_targets_per_fold"].items():
        for r, e in enumerate(d["top3"], 1):
            A(f"| {fid} | {d['test_episode']} | {d['n_test_samples']} | {r} | {e['technique']} | {e['probability']:.4f} | "
              f"{e['training_transitions_with_target']} | {e['test_samples_containing_target']} |")
    A("")
    for fid, d in diag["frequency_top_targets_per_fold"].items():
        A(f"- {fid}: {d['test_samples_hit_by_any_top3']} of {d['n_test_samples']} test samples have at least one of the three top targets in their target set.")
    A("")

    A("### 13.5 Tie diagnostic (status ok Markov predictions only)")
    A("")
    A("| Configuration | Covered N | Top-1 tied | Top-3 boundary tied | n_equal_top >= 3 | Tied N | Tied Top-1 hits | Tied Top-3 hits | Not tied N | Not tied Top-1 hits | Not tied Top-3 hits |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in configs:
        td = ra[c]["tie_diagnostic"]
        sp_tied = td["split_top1_tied"]["tied"]
        sp_not = td["split_top1_tied"]["not_tied"]
        A(f"| {c} | {td['n_ok']} | {td['top1_tied']} | {td['top3_boundary_tied']} | {td['n_equal_top_gte_3']} | "
          f"{sp_tied['n']} | {sp_tied['hit1']} | {sp_tied['hit3']} | "
          f"{sp_not['n']} | {sp_not['hit1']} | {sp_not['hit3']} |")
    A("")
    for c in configs:
        td = ra[c]["tie_diagnostic"]
        A(f"- `{c}`: {td['top1_tied']} of {td['n_ok']} Markov predictions have their Top-1 choice decided by the technique-ID tie-break.")
    A("")

    A(f"### 13.6 Hit concentration by technique (`{pcfg}`, descriptive)")
    A("")
    A("| Method | Technique | Top-1 hit samples | Top-3 hit samples |")
    A("|---|---|---|---|")
    prim_hc = ra[pcfg]["hit_concentration"]
    for m in METHODS:
        m_t1 = prim_hc[m]["top1"]
        m_t3 = prim_hc[m]["top3"]
        all_techs = sorted(set(m_t1) | set(m_t3), key=lambda t: (-m_t3.get(t, 0), -m_t1.get(t, 0), t))
        for t in all_techs:
            A(f"| {m} | {t} | {m_t1.get(t, 0)} | {m_t3.get(t, 0)} |")
    A("")
    A("Most frequent targets in the primary slice pooled over all four episodes (descriptive only; computed on all episodes, not a leakage-free baseline):")
    A("")
    A("| Rank | Target technique | Test samples containing target (pooled) |")
    A("|---|---|---|")
    for r_idx, ft in enumerate(diag.get("frequent_targets_pooled", []), 1):
        A(f"| {r_idx} | {ft['technique']} | {ft['count']} |")
    A("")
    freq_t3 = prim_hc["frequency"]["top3"]
    if freq_t3:
        top_tech, top_count = next(iter(freq_t3.items()))
        total_freq_t3 = ra[pcfg]["methods"]["frequency"]["hit3"]
        A(f"- In `{pcfg}`, {top_count} of {total_freq_t3} Frequency Top-3 hits involve technique {top_tech}.")
    A("")

    A("## 14. Limitations (only statements backed by numbers in this report)")
    A("")
    h = prim["headline"]
    n = prim["n_samples"]
    A(f"- Sample size: {n} test samples in `{pcfg}` from {len(prim['per_fold'])} episodes; Wilson intervals in section 3 are wide and understate uncertainty because samples within an episode are not independent.")
    A(f"- Closed vocabulary: in `{pcfg}`, {h['ceiling']['hits']} of {n} samples ({_pct(h['ceiling']['hits'], n)}) have at least one target technique seen as a training target; "
      f"{n - h['ceiling']['hits']} do not, so neither method can hit them.")
    A(f"- Markov coverage in `{pcfg}` is {h['coverage']['covered_samples']} of {n} ({_pct(h['coverage']['covered_samples'], n)}); "
      f"the other {n - h['coverage']['covered_samples']} samples are abstentions counted as misses.")
    A("- The frequency baseline and the Markov model are compared on hit counts only; no significance test was run.")
    A("")
    A("Hypothesis (not tested): low Markov hit counts may be related to few repeated transitions across episodes; "
      "the support-bucket table (13.3) and the repeat-current-set reference (13.2) are the only related computations here and do not establish a cause.")
    A("")
    A("Hypothesis (not tested): the techniques the frequency baseline predicts may be common across episodes for reasons specific to this dataset; "
      "table 13.4 shows only how often they occur as targets.")
    A("")
    A("## 15. Figures")
    A("")
    A("- `reports/figures/headline_metrics.png`")
    A("- `reports/figures/per_fold_performance.png`")
    A("- `reports/figures/confusion_matrix_parent.png`")

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
