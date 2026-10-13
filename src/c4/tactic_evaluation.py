"""Secondary next-tactic Leave-One-Episode-Out (LOEO) evaluation.

Additive module for C4: evaluates next-tactic / stage prediction without touching
any existing technique-level models, samples, folds, or Stage 1 artifacts.

Framing:
"Primary result remains technique-level, collapsed/full (reports/evaluation_report.md).
This tactic-level evaluation is secondary and exploratory. All slices are reported;
none is selected after the fact."
"""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = BASE_DIR / "reports"

ATTACK_SEQUENCES_PATH = PROCESSED_DIR / "attack_sequences.json"
LOEO_FOLDS_PATH = PROCESSED_DIR / "loeo_folds.json"
TECH_REF_PATH = PROCESSED_DIR / "technique_tactic_reference.json"
TECH_PRED_PATH = PROCESSED_DIR / "evaluation_predictions.csv"

OUT_CSV_PATH = PROCESSED_DIR / "tactic_evaluation_predictions.csv"
OUT_JSON_PATH = REPORTS_DIR / "tactic_evaluation_results.json"
OUT_MD_PATH = REPORTS_DIR / "tactic_evaluation_report.md"

FRAMING_TEXT = (
    "Primary result remains technique-level, collapsed/full (reports/evaluation_report.md). "
    "This tactic-level evaluation is secondary and exploratory. "
    "All slices are reported; none is selected after the fact."
)

ENTERPRISE_TACTICS_14 = [
    "collection",
    "command-and-control",
    "credential-access",
    "defense-evasion",
    "discovery",
    "execution",
    "exfiltration",
    "impact",
    "initial-access",
    "lateral-movement",
    "persistence",
    "privilege-escalation",
    "reconnaissance",
    "resource-development",
]

CSV_FIELDS = [
    "configuration",
    "fold_id",
    "sample_id",
    "episode_id",
    "method",
    "current_tactic_set",
    "target_tactic_set",
    "predicted_candidates_top3",
    "status",
    "hit1",
    "hit3",
    "top1_tied",
    "top3_boundary_tied",
    "n_equal_top",
]


def to_shortname(tactic: str) -> str:
    """Normalize tactic name to ATT&CK v16.1 shortname (e.g. 'Initial Access' -> 'initial-access')."""
    return tactic.strip().lower().replace(" ", "-")


def to_shortnames(tactics: list[str] | set[str]) -> list[str]:
    """Map tactic collection to sorted unique shortnames."""
    return sorted(list(set(to_shortname(t) for t in tactics if t)))


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
    return f"{100 * _rate(h, n):.2f}%"


def random_guess_expected_hit(target_set: set[str], k: int) -> float:
    """Expected hit probability choosing k distinct tactics uniformly at random from 14.

    P(hit) = 1 - C(14 - |T|, k) / C(14, k).
    """
    m = len(target_set)
    total_comb = math.comb(14, k)
    miss_comb = math.comb(max(0, 14 - m), k)
    return 1.0 - (miss_comb / total_comb)


class TacticMarkovModel:
    """First-order Markov chain over multi-tactic sets."""

    def __init__(self) -> None:
        self.counts: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.n_step_transitions: dict[str, int] = defaultdict(int)
        self.supporting_evidence: dict[str, dict[str, list[list[str]]]] = defaultdict(lambda: defaultdict(list))
        self.probabilities: dict[str, dict[str, float]] = defaultdict(dict)
        self.training_episodes: list[str] = []

    def fit(
        self,
        ep_seqs: dict[str, list[dict[str, Any]]],
        training_episodes: list[str],
    ) -> TacticMarkovModel:
        self.training_episodes = sorted(list(training_episodes))
        self.counts = defaultdict(lambda: defaultdict(float))
        self.n_step_transitions = defaultdict(int)
        self.supporting_evidence = defaultdict(lambda: defaultdict(list))
        self.probabilities = defaultdict(dict)

        for ep_id in self.training_episodes:
            items = ep_seqs[ep_id]
            for i in range(len(items) - 1):
                cur_tacs = items[i]["tactics"]
                nxt_tacs = items[i + 1]["tactics"]
                m = len(cur_tacs)
                n = len(nxt_tacs)
                if m == 0 or n == 0:
                    continue
                w = 1.0 / (m * n)
                cur_eid = items[i].get("event_id") or ",".join(items[i].get("event_ids", []))
                nxt_eid = items[i + 1].get("event_id") or ",".join(items[i + 1].get("event_ids", []))
                for a in cur_tacs:
                    self.n_step_transitions[a] += 1
                    for b in nxt_tacs:
                        self.counts[a][b] += w
                        self.supporting_evidence[a][b].append([ep_id, cur_eid, nxt_eid])

        for a, tgts in sorted(self.counts.items()):
            tot = sum(tgts.values())
            if tot > 0:
                for b, c in sorted(tgts.items()):
                    self.probabilities[a][b] = c / tot
        return self

    def predict(self, current_set: list[str] | set[str], k: int | None = 3) -> dict[str, Any]:
        cur_list = sorted(list(set(current_set)))
        if not cur_list:
            return {"status": "empty_input", "candidates": [], "members_used": [], "all_candidates": []}

        members_used = [a for a in cur_list if a in self.probabilities and self.probabilities[a]]
        if not members_used:
            return {"status": "insufficient_evidence", "candidates": [], "members_used": [], "all_candidates": []}

        comb_p: dict[str, float] = defaultdict(float)
        w_mem = 1.0 / len(members_used)
        for a in members_used:
            for b, p in self.probabilities[a].items():
                comb_p[b] += w_mem * p

        tot_p = sum(comb_p.values())
        if abs(tot_p - 1.0) > 1e-9:
            for b in comb_p:
                comb_p[b] /= tot_p

        ranked = sorted(comb_p.items(), key=lambda x: (-x[1], x[0]))
        res_cands = ranked[:k] if (k is not None and k > 0) else ranked
        return {
            "status": "ok",
            "candidates": res_cands,
            "members_used": members_used,
            "all_candidates": ranked,
        }


class TacticFrequencyBaseline:
    """Unconditional target frequency baseline over tactics."""

    def __init__(self) -> None:
        self.counts: dict[str, float] = defaultdict(float)
        self.probabilities: dict[str, float] = {}
        self.supporting_evidence: dict[str, list[list[str]]] = defaultdict(list)
        self.training_episodes: list[str] = []

    def fit(
        self,
        ep_seqs: dict[str, list[dict[str, Any]]],
        training_episodes: list[str],
    ) -> TacticFrequencyBaseline:
        self.training_episodes = sorted(list(training_episodes))
        self.counts = defaultdict(float)
        self.probabilities = {}
        self.supporting_evidence = defaultdict(list)

        for ep_id in self.training_episodes:
            items = ep_seqs[ep_id]
            for i in range(len(items) - 1):
                cur_eid = items[i].get("event_id") or ",".join(items[i].get("event_ids", []))
                nxt_eid = items[i + 1].get("event_id") or ",".join(items[i + 1].get("event_ids", []))
                nxt_tacs = items[i + 1]["tactics"]
                n = len(nxt_tacs)
                if n == 0:
                    continue
                w = 1.0 / n
                for b in nxt_tacs:
                    self.counts[b] += w
                    self.supporting_evidence[b].append([ep_id, cur_eid, nxt_eid])

        tot = sum(self.counts.values())
        if tot > 0:
            for b, c in sorted(self.counts.items()):
                self.probabilities[b] = c / tot
        return self

    def predict(self, k: int | None = 3) -> dict[str, Any]:
        if not self.probabilities:
            return {"status": "empty_training", "candidates": []}
        ranked = sorted(self.probabilities.items(), key=lambda x: (-x[1], x[0]))
        res_cands = ranked[:k] if (k is not None and k > 0) else ranked
        return {"status": "ok", "candidates": res_cands}


def build_tactic_sequences(
    sequences_data: dict[str, Any],
    use_dataset_tactics: bool = False,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Extract raw and collapsed tactic sequences per episode."""
    tactic_seqs: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for ep_id, ep in sorted(sequences_data["episodes"].items()):
        raw_events = ep.get("raw", [])
        raw_items = []
        for idx, ev in enumerate(raw_events):
            tacs = ev.get("tactics", []) if use_dataset_tactics else ev.get("official_tactics", [])
            s_tacs = to_shortnames(tacs)
            eid = ev.get("event_id") or f"{ep_id}-S{idx + 1:03d}"
            raw_items.append({"event_id": eid, "tactics": s_tacs})

        # Merge consecutive events with identical tactic sets
        col_items = []
        for it in raw_items:
            if not col_items or col_items[-1]["tactics"] != it["tactics"]:
                col_items.append({"event_ids": [it["event_id"]], "tactics": it["tactics"]})
            else:
                col_items[-1]["event_ids"].append(it["event_id"])

        tactic_seqs[ep_id] = {
            "tactic_raw": raw_items,
            "tactic_collapsed": col_items,
        }
    return tactic_seqs


def evaluate_tactic_slice(
    variant: str = "tactic_collapsed",
    use_dataset_tactics: bool = False,
    sequences_data: dict[str, Any] | None = None,
    folds_data: list[dict[str, Any]] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Run secondary LOEO evaluation for one tactic slice."""
    if sequences_data is None:
        with open(ATTACK_SEQUENCES_PATH, "r", encoding="utf-8") as f:
            sequences_data = json.load(f)
    if folds_data is None:
        with open(LOEO_FOLDS_PATH, "r", encoding="utf-8") as f:
            folds_data = json.load(f)

    all_ep_seqs = build_tactic_sequences(sequences_data, use_dataset_tactics=use_dataset_tactics)
    ep_seqs = {ep_id: all_ep_seqs[ep_id][variant] for ep_id in all_ep_seqs}

    suffix = "_dataset_tactics" if use_dataset_tactics else ""
    config_name = f"{variant}{suffix}"

    # Build evaluation samples per episode
    samples = []
    for ep_id in sorted(ep_seqs.keys()):
        items = ep_seqs[ep_id]
        for k in range(len(items) - 1):
            cur = items[k]["tactics"]
            tgt = items[k + 1]["tactics"]
            tag = "tac-raw" if "raw" in variant else "tac-col"
            sid = f"{ep_id}-{tag}-K{k + 1:02d}"
            samples.append({
                "sample_id": sid,
                "episode_id": ep_id,
                "current_tactics": cur,
                "target_tactics": tgt,
            })

    rows: list[dict[str, Any]] = []
    per_fold: dict[str, Any] = {}

    for fold in folds_data:
        fid = fold["fold_id"]
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        fold_samples = [s for s in samples if s["episode_id"] == test_ep]

        m_model = TacticMarkovModel().fit(ep_seqs, train_eps)
        f_model = TacticFrequencyBaseline().fit(ep_seqs, train_eps)

        # Leakage assertions
        assert test_ep not in m_model.training_episodes, f"Leak: {test_ep} in Markov training"
        assert test_ep not in f_model.training_episodes, f"Leak: {test_ep} in Frequency training"
        for a, tgts in m_model.supporting_evidence.items():
            for b, evs in tgts.items():
                for ev in evs:
                    assert ev[0] != test_ep, f"Leak: Markov evidence {a}->{b} references {test_ep}"
        for b, evs in f_model.supporting_evidence.items():
            for ev in evs:
                assert ev[0] != test_ep, f"Leak: Frequency evidence {b} references {test_ep}"

        # Pool of training targets for ceiling
        train_tgt_pool: set[str] = set()
        for ep in train_eps:
            itms = ep_seqs[ep]
            for i in range(len(itms) - 1):
                train_tgt_pool.update(itms[i + 1]["tactics"])

        f_res = f_model.predict(k=3)
        f_cands = [c[0] for c in f_res["candidates"]]
        f_raw = [list(c) for c in f_res["candidates"]]

        m_h1_f = m_h3_f = f_h1_f = f_h3_f = fb_h1_f = fb_h3_f = 0
        ceil_hits_f = cov_hits_f = 0

        for s in fold_samples:
            sid = s["sample_id"]
            cur = s["current_tactics"]
            tgt = set(s["target_tactics"])

            if tgt & train_tgt_pool:
                ceil_hits_f += 1

            m_res = m_model.predict(cur, k=3)
            m_status = m_res["status"]

            if m_status == "ok":
                cov_hits_f += 1
                m_raw = [list(c) for c in m_res["candidates"]]
                m_cands = [c[0] for c in m_raw]
                m1 = 1 if (m_cands and m_cands[0] in tgt) else 0
                m3 = 1 if any(c in tgt for c in m_cands[:3]) else 0

                all_c = m_res.get("all_candidates", [])
                probs = [c[1] for c in all_c]
                t1_tied = len(probs) >= 2 and abs(probs[0] - probs[1]) < 1e-9
                t3_tied = len(probs) >= 4 and abs(probs[2] - probs[3]) < 1e-9
                n_eq = sum(1 for p in probs if abs(p - probs[0]) < 1e-9)
                t1_tied_str = "True" if t1_tied else "False"
                t3_tied_str = "True" if t3_tied else "False"
                n_eq_str = str(n_eq)
            else:
                m_raw = []
                m_cands = []
                m1 = m3 = 0
                t1_tied_str = t3_tied_str = n_eq_str = ""

            f1 = 1 if (f_cands and f_cands[0] in tgt) else 0
            f3 = 1 if any(c in tgt for c in f_cands[:3]) else 0

            if m_status == "ok":
                fb1, fb3, fb_status, fb_raw = m1, m3, "ok_markov", m_raw
            else:
                fb1, fb3, fb_status, fb_raw = f1, f3, "fallback_frequency", f_raw

            m_h1_f += m1
            m_h3_f += m3
            f_h1_f += f1
            f_h3_f += f3
            fb_h1_f += fb1
            fb_h3_f += fb3

            per_method = {
                "markov": (m_status, m_raw, m1, m3, t1_tied_str, t3_tied_str, n_eq_str),
                "frequency": (f_res["status"], f_raw, f1, f3, "", "", ""),
                "markov_fallback": (fb_status, fb_raw, fb1, fb3, "", "", ""),
            }

            for m, (st, raw, h1, h3, t1t, t3t, neq) in per_method.items():
                rows.append({
                    "configuration": config_name,
                    "fold_id": fid,
                    "sample_id": sid,
                    "episode_id": test_ep,
                    "method": m,
                    "current_tactic_set": json.dumps(cur),
                    "target_tactic_set": json.dumps(sorted(list(tgt))),
                    "predicted_candidates_top3": json.dumps(raw[:3]),
                    "status": st,
                    "hit1": h1,
                    "hit3": h3,
                    "top1_tied": t1t,
                    "top3_boundary_tied": t3t,
                    "n_equal_top": neq,
                })

        n_f = len(fold_samples)
        per_fold[fid] = {
            "test_episode": test_ep,
            "n_samples": n_f,
            "ceiling_hits": ceil_hits_f,
            "covered_samples": cov_hits_f,
            "markov": {"hit1": m_h1_f, "hit3": m_h3_f, "top1": _rate(m_h1_f, n_f), "top3": _rate(m_h3_f, n_f)},
            "frequency": {"hit1": f_h1_f, "hit3": f_h3_f, "top1": _rate(f_h1_f, n_f), "top3": _rate(f_h3_f, n_f)},
            "fallback": {"hit1": fb_h1_f, "hit3": fb_h3_f, "top1": _rate(fb_h1_f, n_f), "top3": _rate(fb_h3_f, n_f)},
        }

    # Summary aggregations
    N = len(samples)
    m_rows = [r for r in rows if r["method"] == "markov"]
    f_rows = [r for r in rows if r["method"] == "frequency"]
    fb_rows = [r for r in rows if r["method"] == "markov_fallback"]

    m1_tot = sum(r["hit1"] for r in m_rows)
    m3_tot = sum(r["hit3"] for r in m_rows)
    f1_tot = sum(r["hit1"] for r in f_rows)
    f3_tot = sum(r["hit3"] for r in f_rows)
    fb1_tot = sum(r["hit1"] for r in fb_rows)
    fb3_tot = sum(r["hit3"] for r in fb_rows)

    cov_tot = sum(1 for r in m_rows if r["status"] == "ok")
    ceil_tot = sum(f["ceiling_hits"] for f in per_fold.values())

    # Paired 2x2 & frequency-only split
    paired: dict[str, dict[str, int]] = {}
    freq_split: dict[str, dict[str, int]] = {}
    m_by_id = {r["sample_id"]: r for r in m_rows}
    f_by_id = {r["sample_id"]: r for r in f_rows}

    for k_val, h_col in ((1, "hit1"), (3, "hit3")):
        cell = {"both_hit": 0, "markov_only": 0, "freq_only": 0, "neither": 0}
        sp = {"freq_only_total": 0, "markov_returned_and_missed": 0, "markov_abstained": 0, "markov_other_status": 0}
        for sid in m_by_id:
            m_hit = m_by_id[sid][h_col]
            f_hit = f_by_id[sid][h_col]
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
        paired[f"top{k_val}"] = cell
        freq_split[f"top{k_val}"] = sp

    # Covered-only comparison
    ok_sids = set(r["sample_id"] for r in m_rows if r["status"] == "ok")
    cov_comp = {
        "n": len(ok_sids),
        "markov_hit1": sum(r["hit1"] for r in m_rows if r["sample_id"] in ok_sids),
        "markov_hit3": sum(r["hit3"] for r in m_rows if r["sample_id"] in ok_sids),
        "frequency_hit1": sum(r["hit1"] for r in f_rows if r["sample_id"] in ok_sids),
        "frequency_hit3": sum(r["hit3"] for r in f_rows if r["sample_id"] in ok_sids),
        "fallback_hit1": sum(r["hit1"] for r in fb_rows if r["sample_id"] in ok_sids),
        "fallback_hit3": sum(r["hit3"] for r in fb_rows if r["sample_id"] in ok_sids),
    }

    # Repeat current set reference and strict single-tactic subset
    rep1_tot = 0
    rep3_tot = 0
    rg1_vals = []
    rg3_vals = []
    self_equal = 0
    self_overlap = 0

    single_t_sids = set()
    rep_by_id: dict[str, tuple[int, int]] = {}

    for s in samples:
        sid = s["sample_id"]
        cur = set(s["current_tactics"])
        tgt = set(s["target_tactics"])
        if cur == tgt:
            self_equal += 1
        if cur & tgt:
            self_overlap += 1
        rep_cands = sorted(list(cur))[:3]
        h1_r = 1 if (rep_cands and rep_cands[0] in tgt) else 0
        h3_r = 1 if any(c in tgt for c in rep_cands[:3]) else 0
        rep_by_id[sid] = (h1_r, h3_r)
        rep1_tot += h1_r
        rep3_tot += h3_r
        rg1_vals.append(random_guess_expected_hit(tgt, 1))
        rg3_vals.append(random_guess_expected_hit(tgt, 3))

        if len(tgt) == 1:
            single_t_sids.add(sid)

    strict_single = {
        "n": len(single_t_sids),
        "markov_hit1": sum(r["hit1"] for r in m_rows if r["sample_id"] in single_t_sids),
        "markov_hit3": sum(r["hit3"] for r in m_rows if r["sample_id"] in single_t_sids),
        "frequency_hit1": sum(r["hit1"] for r in f_rows if r["sample_id"] in single_t_sids),
        "frequency_hit3": sum(r["hit3"] for r in f_rows if r["sample_id"] in single_t_sids),
        "fallback_hit1": sum(r["hit1"] for r in fb_rows if r["sample_id"] in single_t_sids),
        "fallback_hit3": sum(r["hit3"] for r in fb_rows if r["sample_id"] in single_t_sids),
        "repeat_hit1": sum(rep_by_id[sid][0] for sid in single_t_sids),
        "repeat_hit3": sum(rep_by_id[sid][1] for sid in single_t_sids),
    }

    # Tie diagnostic (Markov status ok)
    ok_m_rows = [r for r in m_rows if r["status"] == "ok"]
    t1_tied_cnt = sum(1 for r in ok_m_rows if r["top1_tied"] == "True")
    t3_tied_cnt = sum(1 for r in ok_m_rows if r["top3_boundary_tied"] == "True")
    neq_gte3_cnt = sum(1 for r in ok_m_rows if int(r["n_equal_top"] or 0) >= 3)
    tied_m_rows = [r for r in ok_m_rows if r["top1_tied"] == "True"]
    nottied_m_rows = [r for r in ok_m_rows if r["top1_tied"] == "False"]

    tie_diag = {
        "n_ok": len(ok_m_rows),
        "top1_tied": t1_tied_cnt,
        "top3_boundary_tied": t3_tied_cnt,
        "n_equal_top_gte_3": neq_gte3_cnt,
        "split_top1_tied": {
            "tied": {
                "n": len(tied_m_rows),
                "hit1": sum(r["hit1"] for r in tied_m_rows),
                "hit3": sum(r["hit3"] for r in tied_m_rows),
            },
            "not_tied": {
                "n": len(nottied_m_rows),
                "hit1": sum(r["hit1"] for r in nottied_m_rows),
                "hit3": sum(r["hit3"] for r in nottied_m_rows),
            },
        },
    }

    # Hit concentration by tactic
    hit_conc: dict[str, dict[str, dict[str, int]]] = {}
    for m, m_sub_rows in (("markov", m_rows), ("frequency", f_rows), ("markov_fallback", fb_rows)):
        t1_cnt: dict[str, int] = defaultdict(int)
        t3_cnt: dict[str, int] = defaultdict(int)
        for r in m_sub_rows:
            parsed_c = [c[0] for c in json.loads(r["predicted_candidates_top3"])]
            tgt_set = set(json.loads(r["target_tactic_set"]))
            if r["hit1"] and parsed_c and parsed_c[0] in tgt_set:
                t1_cnt[parsed_c[0]] += 1
            if r["hit3"]:
                for c in parsed_c[:3]:
                    if c in tgt_set:
                        t3_cnt[c] += 1
        hit_conc[m] = {
            "top1": dict(sorted(t1_cnt.items(), key=lambda x: (-x[1], x[0]))),
            "top3": dict(sorted(t3_cnt.items(), key=lambda x: (-x[1], x[0]))),
        }

    # Target frequencies (descriptive)
    target_freq = Counter()
    for s in samples:
        for t in s["target_tactics"]:
            target_freq[t] += 1
    top_targets = [{"tactic": t, "count": c} for t, c in target_freq.most_common(5)]

    fold_list = list(per_fold.values())
    summary: dict[str, Any] = {
        "configuration": config_name,
        "variant": variant,
        "use_dataset_tactics": use_dataset_tactics,
        "n_samples": N,
        "coverage": {"covered_samples": cov_tot, "coverage_rate": _rate(cov_tot, N)},
        "ceiling": {"hits": ceil_tot, "ceiling_rate": _rate(ceil_tot, N)},
        "headline": {
            "markov": {
                "hit1": m1_tot, "hit3": m3_tot, "top1": _rate(m1_tot, N), "top3": _rate(m3_tot, N),
                "wilson95_top1": list(wilson_interval(m1_tot, N)), "wilson95_top3": list(wilson_interval(m3_tot, N)),
                "fold_mean_top1": sum(f["markov"]["top1"] for f in fold_list) / len(fold_list),
                "fold_mean_top3": sum(f["markov"]["top3"] for f in fold_list) / len(fold_list),
            },
            "frequency": {
                "hit1": f1_tot, "hit3": f3_tot, "top1": _rate(f1_tot, N), "top3": _rate(f3_tot, N),
                "wilson95_top1": list(wilson_interval(f1_tot, N)), "wilson95_top3": list(wilson_interval(f3_tot, N)),
                "fold_mean_top1": sum(f["frequency"]["top1"] for f in fold_list) / len(fold_list),
                "fold_mean_top3": sum(f["frequency"]["top3"] for f in fold_list) / len(fold_list),
            },
            "markov_fallback": {
                "hit1": fb1_tot, "hit3": fb3_tot, "top1": _rate(fb1_tot, N), "top3": _rate(fb3_tot, N),
                "wilson95_top1": list(wilson_interval(fb1_tot, N)), "wilson95_top3": list(wilson_interval(fb3_tot, N)),
                "fold_mean_top1": sum(f["fallback"]["top1"] for f in fold_list) / len(fold_list),
                "fold_mean_top3": sum(f["fallback"]["top3"] for f in fold_list) / len(fold_list),
            },
        },
        "diagnostics": {
            "self_repeat": {
                "equal": self_equal, "equal_rate": _rate(self_equal, N),
                "overlap": self_overlap, "overlap_rate": _rate(self_overlap, N),
            },
            "strict_single_tactic": strict_single,
            "repeat_current_set": {
                "hit1": rep1_tot, "hit3": rep3_tot, "top1": _rate(rep1_tot, N), "top3": _rate(rep3_tot, N),
                "wilson95_top1": list(wilson_interval(rep1_tot, N)), "wilson95_top3": list(wilson_interval(rep3_tot, N)),
            },
            "random_guess": {
                "mean_p_hit1": sum(rg1_vals) / N if N else 0.0,
                "mean_p_hit3": sum(rg3_vals) / N if N else 0.0,
            },
            "tie_diagnostic": tie_diag,
            "hit_concentration": hit_conc,
            "top_targets_pooled": top_targets,
        },
        "per_fold": per_fold,
        "paired_2x2": paired,
        "frequency_only_split": freq_split,
        "covered_only": cov_comp,
    }

    return summary, rows


def evaluate_derived_tactics(
    tech_predictions_path: Path = TECH_PRED_PATH,
    ref_path: Path = TECH_REF_PATH,
) -> dict[str, Any]:
    """Score derived-tactic accuracy from technique predictions mapped to tactics."""
    with open(tech_predictions_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(ref_path, "r", encoding="utf-8") as f:
        tech_ref = json.load(f)

    def tech_to_tacs(tech: str) -> list[str]:
        clean = tech.strip().upper()
        if clean in tech_ref:
            return to_shortnames(tech_ref[clean].get("official_tactics", []))
        return []

    res: dict[str, Any] = {}
    mean_tacs_table: dict[str, dict[str, Any]] = {}

    for cfg in ("collapsed_full", "raw_full"):
        cfg_rows = [r for r in rows if r["configuration"] == cfg]
        by_m = defaultdict(list)
        for r in cfg_rows:
            by_m[r["method"]].append(r)

        methods_res = {}
        mean_tacs_table[cfg] = {}

        for m, mrows in by_m.items():
            n = len(mrows)
            h1 = h3 = 0
            n_cov = 0
            t1_tac_counts = []

            for r in mrows:
                cands = json.loads(r["predicted_candidates_top3"])
                if cands:
                    n_cov += 1
                    t1_tac_counts.append(len(tech_to_tacs(cands[0][0])))
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

            cov_rate = n_cov / n if n > 0 else 0.0
            mean_t = sum(t1_tac_counts) / len(t1_tac_counts) if t1_tac_counts else 0.0

            methods_res[m] = {
                "n": n,
                "covered": n_cov,
                "coverage_rate": cov_rate,
                "hit1": h1, "hit3": h3,
                "top1": _rate(h1, n), "top3": _rate(h3, n),
                "wilson95_top1": list(wilson_interval(h1, n)),
                "wilson95_top3": list(wilson_interval(h3, n)),
            }
            mean_tacs_table[cfg][m] = {
                "n_predicted": len(t1_tac_counts),
                "mean_tactics_per_top1": mean_t,
            }
        res[cfg] = methods_res

    return {
        "methods": res,
        "mean_tactics_per_top1_technique": mean_tacs_table,
    }


def run_full_tactic_evaluation() -> dict[str, Any]:
    """Execute all secondary tactic evaluation runs, produce CSV, JSON, and MD."""
    with open(ATTACK_SEQUENCES_PATH, "r", encoding="utf-8") as f:
        seq_data = json.load(f)
    with open(LOEO_FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)

    # 1. Main official-tactics slices
    col_summary, col_rows = evaluate_tactic_slice("tactic_collapsed", False, seq_data, folds_data)
    raw_summary, raw_rows = evaluate_tactic_slice("tactic_raw", False, seq_data, folds_data)

    # 2. Sensitivity: dataset ground-truth tactics slices
    col_ds_summary, col_ds_rows = evaluate_tactic_slice("tactic_collapsed", True, seq_data, folds_data)
    raw_ds_summary, raw_ds_rows = evaluate_tactic_slice("tactic_raw", True, seq_data, folds_data)

    # 3. Derived-tactic evaluation from technique predictions
    derived_summary = evaluate_derived_tactics()

    # 4. Write tactic prediction CSV
    all_rows = col_rows + raw_rows + col_ds_rows + raw_ds_rows
    OUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS, restval="")
        w.writeheader()
        w.writerows(all_rows)

    # Discrepant event discovery and (a)/(b) classification
    discrepant_events = []
    type_a_events = []
    type_b_events = []

    for ep_id, ep in sorted(seq_data["episodes"].items()):
        for it in ep["raw"]:
            dt = set(to_shortnames(it.get("tactics", [])))
            ot = set(to_shortnames(it.get("official_tactics", [])))
            if dt != ot:
                eid = it.get("event_id") or "unknown"
                extra = dt - ot
                is_subset = dt < ot
                if extra:
                    cls_code = "a"
                    cls_desc = "Dataset contains tactic NOT in official set"
                    type_a_events.append(eid)
                elif is_subset:
                    cls_code = "b"
                    cls_desc = "Dataset set is strict subset of official set"
                    type_b_events.append(eid)
                else:
                    cls_code = "other"
                    cls_desc = "Mixed difference"

                discrepant_events.append({
                    "event_id": eid,
                    "episode_id": ep_id,
                    "techniques": it.get("techniques", []),
                    "dataset_tactics": sorted(list(dt)),
                    "official_tactics": sorted(list(ot)),
                    "classification": cls_code,
                    "classification_description": cls_desc,
                    "extra_tactics": sorted(list(extra)),
                })

    payload = {
        "metadata": {
            "framing": FRAMING_TEXT,
            "evaluation_type": "Secondary Leave-One-Episode-Out (LOEO) Next-Tactic Prediction",
            "evaluator": "c4.tactic_evaluation",
            "tactics_count": len(ENTERPRISE_TACTICS_14),
            "tactics_universe": ENTERPRISE_TACTICS_14,
        },
        "slices": {
            "tactic_collapsed": col_summary,
            "tactic_raw": raw_summary,
            "tactic_collapsed_dataset_tactics": col_ds_summary,
            "tactic_raw_dataset_tactics": raw_ds_summary,
        },
        "derived_tactics": derived_summary,
        "discrepant_events_sensitivity": {
            "discrepant_events_count": len(discrepant_events),
            "type_a_count": len(type_a_events),
            "type_a_event_ids": sorted(type_a_events),
            "type_b_count": len(type_b_events),
            "type_b_event_ids": sorted(type_b_events),
            "discrepant_events": discrepant_events,
        },
    }

    OUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True, ensure_ascii=False)

    render_tactic_evaluation_markdown(payload, OUT_MD_PATH)
    return payload


def render_tactic_evaluation_markdown(data: dict[str, Any], output_path: Path | str) -> None:
    """Render markdown report for secondary tactic evaluation."""
    slices = data["slices"]
    derived = data["derived_tactics"]
    disc = data["discrepant_events_sensitivity"]

    L: list[str] = []
    A = L.append

    A(FRAMING_TEXT)
    A("")
    A("# C4 Secondary Next-Tactic Prediction: LOEO Evaluation Report")
    A("")
    A("This report evaluates next-tactic prediction across the 14 MITRE ATT&CK Enterprise tactics. "
      "All models are strictly fitted on training episodes under Leave-One-Episode-Out (LOEO) cross-validation.")
    A("")
    A("## 1. Setup and Sample Counts")
    A("")
    A("- **Tactic Universe**: 14 ATT&CK Enterprise v16.1 tactics (shortname tokens, e.g. `initial-access`, `defense-evasion`).")
    A("- **Folds**: 4 leave-one-episode-out folds reusing `data/processed/loeo_folds.json`.")
    A("")
    A("| Slice | Total N | E1 | E2 | E3 | E4 | Merge Rule |")
    A("|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        pf = s["per_fold"]
        e1 = pf["fold_1"]["n_samples"]
        e2 = pf["fold_2"]["n_samples"]
        e3 = pf["fold_3"]["n_samples"]
        e4 = pf["fold_4"]["n_samples"]
        rule = "Consecutive identical tactic sets collapsed" if "collapsed" in s_name else "Raw event transitions (no collapse)"
        A(f"| `{s_name}` | {s['n_samples']} | {e1} | {e2} | {e3} | {e4} | {rule} |")
    A("")

    A("## 2. Headline Results (Official ATT&CK Tactics)")
    A("")
    A("| Slice | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 | Coverage | Ceiling |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        cov_str = _pct(s["coverage"]["covered_samples"], s["n_samples"])
        ceil_str = _pct(s["ceiling"]["hits"], s["n_samples"])
        for m, key in (("markov", "markov"), ("frequency", "frequency"), ("markov_fallback", "markov_fallback")):
            hm = s["headline"][key]
            cov = cov_str if m == "markov" else "-"
            A(f"| `{s_name}` | {m} | {s['n_samples']} | {hm['hit1']} | {hm['hit3']} | "
              f"{100*hm['top1']:.2f}% | {100*hm['top3']:.2f}% | {100*hm['fold_mean_top1']:.2f}% | {100*hm['fold_mean_top3']:.2f}% | "
              f"{cov} | {ceil_str} |")
    A("")

    A("### Wilson 95% Score Intervals (Pooled)")
    A("")
    A("| Slice | Method | N | Top-1 interval | Top-3 interval |")
    A("|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        for m, key in (("markov", "markov"), ("frequency", "frequency"), ("markov_fallback", "markov_fallback")):
            hm = s["headline"][key]
            A(f"| `{s_name}` | {m} | {s['n_samples']} | "
              f"[{100*hm['wilson95_top1'][0]:.2f}%, {100*hm['wilson95_top1'][1]:.2f}%] | "
              f"[{100*hm['wilson95_top3'][0]:.2f}%, {100*hm['wilson95_top3'][1]:.2f}%] |")
    A("")

    A("### Per-Fold Performance Breakdown (All Configurations)")
    A("")
    A("| Configuration | Fold | Test Episode | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate |")
    A("|---|---|---|---|---|---|---|---|---|")
    for cfg_key in ("tactic_collapsed", "tactic_raw", "tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics"):
        s = slices[cfg_key]
        for fid in sorted(s["per_fold"].keys()):
            f_data = s["per_fold"][fid]
            tep = f_data["test_episode"]
            fn = f_data["n_samples"]
            for m_key, m_name in (("markov", "markov"), ("frequency", "frequency"), ("fallback", "markov_fallback")):
                mf = f_data[m_key]
                A(f"| `{cfg_key}` | {fid} | {tep} | {m_name} | {fn} | {mf['hit1']} | {mf['hit3']} | "
                  f"{100*mf['top1']:.2f}% | {100*mf['top3']:.2f}% |")
    A("")

    A("## 3. Diagnostic Baselines and Self-Repeat Analysis")
    A("")
    A("### Reference Baselines (Repeat-Current-Set and Random-Guess)")
    A("")
    A("| Slice | Reference Baseline | Top-1 | Top-3 | Wilson 95% Top-1 | Wilson 95% Top-3 |")
    A("|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        rep = s["diagnostics"]["repeat_current_set"]
        rg = s["diagnostics"]["random_guess"]
        A(f"| `{s_name}` | Repeat-current-set ({rep['hit1']}/{s['n_samples']} t1, {rep['hit3']}/{s['n_samples']} t3) | "
          f"{100*rep['top1']:.2f}% | {100*rep['top3']:.2f}% | "
          f"[{100*rep['wilson95_top1'][0]:.2f}%, {100*rep['wilson95_top1'][1]:.2f}%] | "
          f"[{100*rep['wilson95_top3'][0]:.2f}%, {100*rep['wilson95_top3'][1]:.2f}%] |")
        A(f"| `{s_name}` | Random-guess (uniform from 14) | {100*rg['mean_p_hit1']:.2f}% | {100*rg['mean_p_hit3']:.2f}% | - | - |")
    A("")

    A("### Self-Repeat Rates Across Slices")
    A("")
    A("| Slice | N | Target == Current Set (count) | Target == Current Set (rate) | Target Shares >=1 Tactic (count) | Target Shares >=1 Tactic (rate) |")
    A("|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        sr = s["diagnostics"]["self_repeat"]
        A(f"| `{s_name}` | {s['n_samples']} | {sr['equal']} | {100*sr['equal_rate']:.2f}% | "
          f"{sr['overlap']} | {100*sr['overlap_rate']:.2f}% |")
    A("")

    A("### Strict Single-Tactic Target Subset")
    A("")
    A("Evaluated exclusively on samples where the target consists of exactly one tactic:")
    A("")
    A("| Slice | Single-Tactic N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 | Repeat Top-1 | Repeat Top-3 |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        st = s["diagnostics"]["strict_single_tactic"]
        A(f"| `{s_name}` | {st['n']} | {st['markov_hit1']} | {st['markov_hit3']} | "
          f"{st['frequency_hit1']} | {st['frequency_hit3']} | {st['fallback_hit1']} | {st['fallback_hit3']} | "
          f"{st['repeat_hit1']} | {st['repeat_hit3']} |")
    A("")

    A("## 4. Paired Comparison and Frequency-Only Split")
    A("")
    A("### 2x2 Paired Tables (Markov vs Frequency)")
    A("")
    A("| Slice | k | Both hit | Markov-only | Frequency-only | Neither |")
    A("|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        for k_val in (1, 3):
            p = s["paired_2x2"][f"top{k_val}"]
            A(f"| `{s_name}` | {k_val} | {p['both_hit']} | {p['markov_only']} | {p['freq_only']} | {p['neither']} |")
    A("")

    A("### Frequency-Only Hits Split by Markov Status")
    A("")
    A("| Slice | k | Frequency-only hits | Markov returned a prediction and missed (status ok) | Markov abstained (insufficient_evidence) | Other status |")
    A("|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        for k_val in (1, 3):
            sp = s["frequency_only_split"][f"top{k_val}"]
            A(f"| `{s_name}` | {k_val} | {sp['freq_only_total']} | {sp['markov_returned_and_missed']} | {sp['markov_abstained']} | {sp['markov_other_status']} |")
    A("")

    A("## 5. Covered-Only Comparison (Markov Status ok)")
    A("")
    A("| Slice | Covered N | Markov Top-1 | Markov Top-3 | Frequency Top-1 | Frequency Top-3 | Fallback Top-1 | Fallback Top-3 |")
    A("|---|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        co = s["covered_only"]
        A(f"| `{s_name}` | {co['n']} | {co['markov_hit1']} | {co['markov_hit3']} | {co['frequency_hit1']} | {co['frequency_hit3']} | "
          f"{co['fallback_hit1']} | {co['fallback_hit3']} |")
    A("")

    A("## 6. Tie Diagnostic (Markov predictions with status ok)")
    A("")
    A("| Slice | Covered N | Top-1 tied | Top-3 boundary tied | n_equal_top >= 3 | Tied N | Tied Top-1 | Tied Top-3 | Not tied N | Not tied Top-1 | Not tied Top-3 |")
    A("|---|---|---|---|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = slices[s_name]
        td = s["diagnostics"]["tie_diagnostic"]
        sp_t = td["split_top1_tied"]["tied"]
        sp_nt = td["split_top1_tied"]["not_tied"]
        A(f"| `{s_name}` | {td['n_ok']} | {td['top1_tied']} | {td['top3_boundary_tied']} | {td['n_equal_top_gte_3']} | "
          f"{sp_t['n']} | {sp_t['hit1']} | {sp_t['hit3']} | {sp_nt['n']} | {sp_nt['hit1']} | {sp_nt['hit3']} |")
    A("")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        td = slices[s_name]["diagnostics"]["tie_diagnostic"]
        A(f"- `{s_name}`: {td['top1_tied']} of {td['n_ok']} Markov predictions have their Top-1 choice decided by the tactic-name tie-break.")
    A("")

    A("## 7. Hit Concentration by Tactic (`tactic_collapsed`)")
    A("")
    A("| Method | Tactic | Top-1 hit samples | Top-3 hit samples |")
    A("|---|---|---|---|")
    tcol_hc = slices["tactic_collapsed"]["diagnostics"]["hit_concentration"]
    for m in ("markov", "frequency", "markov_fallback"):
        t1_c = tcol_hc[m]["top1"]
        t3_c = tcol_hc[m]["top3"]
        all_tacs = sorted(set(t1_c) | set(t3_c), key=lambda x: (-t3_c.get(x, 0), -t1_c.get(x, 0), x))
        for tac in all_tacs:
            A(f"| {m} | {tac} | {t1_c.get(tac, 0)} | {t3_c.get(tac, 0)} |")
    A("")
    top_tacs = slices["tactic_collapsed"]["diagnostics"]["top_targets_pooled"]
    A("Most frequent target tactics pooled over all four episodes (descriptive only; computed on all episodes, not a leakage-free baseline):")
    A("")
    A("| Rank | Target Tactic | Test samples containing target (pooled) |")
    A("|---|---|---|")
    for idx, tt in enumerate(top_tacs, 1):
        A(f"| {idx} | {tt['tactic']} | {tt['count']} |")
    A("")

    A("## 8. Sensitivity: Ground-Truth Dataset Tactics (Attackmate)")
    A("")
    A(f"Total events differing between official tactics and ground-truth dataset tactics: **{disc['discrepant_events_count']}**.")
    A(f"- **Type (a)** (dataset contains a tactic NOT in official MITRE set): **{disc['type_a_count']} events** ({', '.join(disc['type_a_event_ids'])}).")
    A(f"- **Type (b)** (dataset tactic set is a strict subset of official MITRE set): **{disc['type_b_count']} events** ({', '.join(disc['type_b_event_ids'])}).")
    A("")
    A("### Discrepant Events Breakdown")
    A("")
    A("| Event ID | Episode | Class | Techniques | Dataset tactics | Official MITRE tactics |")
    A("|---|---|---|---|---|---|")
    for d in disc["discrepant_events"]:
        A(f"| {d['event_id']} | {d['episode_id']} | Type ({d['classification']}) | {', '.join(d['techniques'])} | {', '.join(d['dataset_tactics'])} | {', '.join(d['official_tactics'])} |")
    A("")
    A("### Sensitivity Results (Dataset Tactics)")
    A("")
    A("| Slice | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Fold-mean Top-1 | Fold-mean Top-3 |")
    A("|---|---|---|---|---|---|---|---|---|")
    for s_name in ("tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics"):
        s = slices[s_name]
        for m, key in (("markov", "markov"), ("frequency", "frequency"), ("markov_fallback", "markov_fallback")):
            hm = s["headline"][key]
            A(f"| `{s_name}` | {m} | {s['n_samples']} | {hm['hit1']} | {hm['hit3']} | "
              f"{100*hm['top1']:.2f}% | {100*hm['top3']:.2f}% | {100*hm['fold_mean_top1']:.2f}% | {100*hm['fold_mean_top3']:.2f}% |")
    A("")

    A("### Markov vs Frequency Ordering Comparison")
    A("")
    for variant in ("tactic_collapsed", "tactic_raw"):
        off_hl = slices[variant]["headline"]
        ds_hl = slices[f"{variant}_dataset_tactics"]["headline"]
        for k_val in (1, 3):
            col = f"hit{k_val}"
            m_off, f_off = off_hl["markov"][col], off_hl["frequency"][col]
            m_ds, f_ds = ds_hl["markov"][col], ds_hl["frequency"][col]
            ord_off = "above" if m_off > f_off else ("below" if m_off < f_off else "equal to")
            ord_ds = "above" if m_ds > f_ds else ("below" if m_ds < f_ds else "equal to")
            same_str = "the same" if ord_off == ord_ds else "different"
            A(f"- For `{variant}` at k={k_val}: under official tactics Markov ({m_off}) is {ord_off} Frequency ({f_off}), "
              f"and under dataset tactics Markov ({m_ds}) is {ord_ds} Frequency ({f_ds}); the Markov-vs-Frequency ordering is **{same_str}**.")
    A("")

    A("## 9. Derived-Tactic Evaluation from Technique-Level Predictions")
    A("")
    A("Scored by mapping each of the top-k predicted techniques from `evaluation_predictions.csv` to its official ATT&CK tactics, "
      "and testing for intersection with the target's official tactic set.")
    A("")
    A("| Technique Configuration | Method | N | Top-1 hits | Top-3 hits | Top-1 rate | Top-3 rate | Wilson 95% Top-1 | Wilson 95% Top-3 | Coverage |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    d_methods = derived["methods"]
    for cfg in ("collapsed_full", "raw_full"):
        m_dict = d_methods[cfg]
        for m in ("markov", "frequency", "markov_fallback"):
            d = m_dict[m]
            cov_str = f"{100*d['coverage_rate']:.2f}%"
            A(f"| `{cfg}` | {m} | {d['n']} | {d['hit1']} | {d['hit3']} | "
              f"{100*d['top1']:.2f}% | {100*d['top3']:.2f}% | "
              f"[{100*d['wilson95_top1'][0]:.2f}%, {100*d['wilson95_top1'][1]:.2f}%] | "
              f"[{100*d['wilson95_top3'][0]:.2f}%, {100*d['wilson95_top3'][1]:.2f}%] | "
              f"{cov_str} |")
    A("")
    A("> [!NOTE]")
    A("> Derived scoring uses any-overlap between the tactic set of the predicted technique(s) and the target tactic set; "
      "one technique can map to several tactics so derived Top-1 covers a tactic set, not a single tactic; "
      "the derived table uses technique slices (N=67 and N=95) while the direct table uses tactic slices (N=53 and N=95); "
      "therefore the two tables are not directly comparable.")
    A("")
    A("### Mean Official Tactics per Top-1 Predicted Technique")
    A("")
    A("| Technique Configuration | Method | Evaluated Predictions N | Mean Official Tactics per Top-1 Prediction |")
    A("|---|---|---|---|")
    mean_tacs = derived["mean_tactics_per_top1_technique"]
    for cfg in ("collapsed_full", "raw_full"):
        for m in ("markov", "frequency", "markov_fallback"):
            mt = mean_tacs[cfg][m]
            A(f"| `{cfg}` | {m} | {mt['n_predicted']} | {mt['mean_tactics_per_top1']:.2f} |")
    A("")

    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
