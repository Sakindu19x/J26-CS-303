#!/usr/bin/env python3
"""Build Explainable Prediction Records LOEO Dataset and Examples Report (Prompt 14 Q7, Schema 1.1.0).

Satisfies FR4-FR7, NFR2, NFR3, and NFR6:
1. Builds data/processed_7ep/prediction_records_loeo.jsonl (171 records: 95 technique + 76 tactic).
2. Generates reports/7ep/prediction_record_examples.md with full worked examples across 7 distinct exemplars.
3. Enforces Gate G-P5-1: candidate lists match evaluation_7ep_predictions.csv exactly.
4. Schema version 1.1.0: adds support metrics, candidate tactics & tactic_display, alternatives with full transition evidence.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from c4.prediction_record import (
    build_prediction_record,
    canonical_json_bytes,
    generate_explanation_text,
    get_schema_validator,
    sha256_canonical,
)

DATA_7EP = REPO_ROOT / "data" / "processed_7ep"
REPORTS_7EP = REPO_ROOT / "reports" / "7ep"
ARTIFACTS_7EP = REPO_ROOT / "artifacts" / "7ep"

SEQS_PATH = DATA_7EP / "attack_sequences.json"
EVENTS_PATH = DATA_7EP / "normalized_events.json"
REF_PATH = DATA_7EP / "technique_tactic_reference.json"
SAMPLES_PATH = DATA_7EP / "next_technique_samples.json"
CSV_PATH = DATA_7EP / "evaluation_7ep_predictions.csv"
RESULTS_JSON_PATH = REPORTS_7EP / "evaluation_7ep_results.json"
FOLD_MANIFEST_PATH = ARTIFACTS_7EP / "fold_models" / "manifest.json"

OUT_JSONL = DATA_7EP / "prediction_records_loeo.jsonl"
OUT_EXAMPLES_MD = REPORTS_7EP / "prediction_record_examples.md"

TACTIC_DISPLAY_NAMES = {
    "initial-access": "Initial Access",
    "execution": "Execution",
    "persistence": "Persistence",
    "privilege-escalation": "Privilege Escalation",
    "defense-evasion": "Defense Evasion",
    "credential-access": "Credential Access",
    "discovery": "Discovery",
    "lateral-movement": "Lateral Movement",
    "collection": "Collection",
    "command-and-control": "Command and Control",
    "exfiltration": "Exfiltration",
    "impact": "Impact",
    "reconnaissance": "Reconnaissance",
    "resource-development": "Resource Development",
}


def to_shortname(t: str) -> str:
    return t.strip().lower().replace(" ", "-").replace("_", "-")


def to_tactic_display(tactics: list[str]) -> list[str]:
    return [TACTIC_DISPLAY_NAMES.get(t, t.replace("-", " ").title()) for t in tactics]


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    with open(SEQS_PATH, "r", encoding="utf-8") as f:
        seqs_data = json.load(f)
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        events_list = json.load(f)
    events_map = {e["event_id"]: e for e in events_list}
    with open(REF_PATH, "r", encoding="utf-8") as f:
        ref_data = json.load(f)
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        samples_list = json.load(f)
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    with open(RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
        results_data = json.load(f)
    with open(FOLD_MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    return seqs_data, events_map, ref_data, samples_list, csv_rows, results_data, manifest_data


def get_candidate_supporting_episodes(
    level: str,
    training_episodes: list[str],
    seqs_data: dict[str, Any],
    cur_set: list[str],
    cand_id: str,
) -> tuple[float, float, int, list[str]]:
    """Determine transition numerator, denominator, supporting episodes count and IDs."""
    sup_eps = []
    total_num = 0.0
    total_den = 0.0

    if level == "technique":
        for ep_id in training_episodes:
            items = seqs_data["episodes"][ep_id]["collapsed"]
            ep_hit = False
            for i in range(len(items) - 1):
                c_techs = items[i].get("techniques", [])
                n_techs = items[i + 1].get("techniques", [])
                common_cur = [a for a in c_techs if a in cur_set]
                if common_cur and len(n_techs) > 0:
                    weight_den = len(common_cur) / (len(c_techs) * len(n_techs))
                    total_den += weight_den
                    if cand_id in n_techs:
                        weight_num = len(common_cur) / (len(c_techs) * len(n_techs))
                        total_num += weight_num
                        ep_hit = True
            if ep_hit:
                sup_eps.append(ep_id)
    else:  # tactic
        for ep_id in training_episodes:
            raw_items = seqs_data["episodes"][ep_id]["raw"]
            col_tacs = []
            for ev in raw_items:
                t_list = ev.get("official_tactics") or ev.get("tactics", [])
                s_tacs = sorted(list(set(to_shortname(t) for t in t_list if t)))
                if not col_tacs or col_tacs[-1] != s_tacs:
                    col_tacs.append(s_tacs)
            ep_hit = False
            for i in range(len(col_tacs) - 1):
                c_t = col_tacs[i]
                n_t = col_tacs[i + 1]
                common_cur = [a for a in c_t if a in cur_set]
                if common_cur and len(n_t) > 0:
                    w = len(common_cur) / (len(c_t) * len(n_t))
                    total_den += w
                    if cand_id in n_t:
                        total_num += w
                        ep_hit = True
            if ep_hit:
                sup_eps.append(ep_id)

    return total_num, total_den, len(sup_eps), sup_eps


def get_state_support(
    level: str,
    training_episodes: list[str],
    seqs_data: dict[str, Any],
    cur_set: list[str],
) -> tuple[int, float]:
    """Determine state-level support: (n_supporting_training_episodes, n_transitions_from_state)."""
    if not cur_set:
        return 0, 0.0

    supporting_eps = []
    total_transitions = 0.0

    if level == "technique":
        for ep_id in training_episodes:
            items = seqs_data["episodes"][ep_id]["collapsed"]
            ep_has_trans = False
            for i in range(len(items) - 1):
                c_techs = items[i].get("techniques", [])
                n_techs = items[i + 1].get("techniques", [])
                common = [a for a in c_techs if a in cur_set]
                if common and len(n_techs) > 0:
                    weight = len(common) / len(c_techs)
                    total_transitions += weight
                    ep_has_trans = True
            if ep_has_trans:
                supporting_eps.append(ep_id)
    else:  # tactic
        for ep_id in training_episodes:
            raw_items = seqs_data["episodes"][ep_id]["raw"]
            col_tacs: list[list[str]] = []
            for ev in raw_items:
                t_list = ev.get("official_tactics") or ev.get("tactics", [])
                s_tacs = sorted(list(set(to_shortname(t) for t in t_list if t)))
                if not col_tacs or col_tacs[-1] != s_tacs:
                    col_tacs.append(s_tacs)
            ep_has_trans = False
            for i in range(len(col_tacs) - 1):
                c_t = col_tacs[i]
                n_t = col_tacs[i + 1]
                common = [a for a in c_t if a in cur_set]
                if common and len(n_t) > 0:
                    weight = len(common) / len(c_t)
                    total_transitions += weight
                    ep_has_trans = True
            if ep_has_trans:
                supporting_eps.append(ep_id)

    return len(supporting_eps), float(total_transitions)


def build_all_records() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    print("=" * 80)
    print("BUILDING EXPLAINABLE PREDICTION RECORDS (SCHEMA 1.1.0, LOEO 7 EPISODES)")
    print("=" * 80)

    seqs_data, events_map, ref_data, samples_list, csv_rows, results_data, manifest_data = load_inputs()

    csv_by_slice_and_sample = {(r["slice"], r["sample_id"]): r for r in csv_rows}
    cf_samples = [s for s in samples_list if s.get("variant") == "collapsed" and s.get("granularity") == "full"]
    assert len(cf_samples) == 95, f"Expected 95 cf samples, got {len(cf_samples)}"

    tech_headline = results_data["primary_slice_technique_collapsed_full"]["headline"]
    tac_headline = results_data["secondary_slice_tactic_collapsed"]["headline"]
    tac_cov = results_data["secondary_slice_tactic_collapsed"]["coverage"]

    tech_reliability_banner = {
        "metric": "Markov vs Frequency Hit@3",
        "slice": "collapsed_full",
        "sample_count": 95,
        "markov_hit3_pooled": tech_headline["markov"]["top3"],
        "markov_hit3_wilson95": list(tech_headline["markov"]["wilson95_top3"]),
        "frequency_hit3_pooled": tech_headline["frequency"]["top3"],
        "frequency_hit3_wilson95": list(tech_headline["frequency"]["wilson95_top3"]),
        "coverage_rate": tech_headline["coverage"]["coverage_rate"],
        "banner_text": (
            f"Technique Level (collapsed_full, N=95): Markov Hit@3 {tech_headline['markov']['top3']*100:.2f}% "
            f"[{tech_headline['markov']['wilson95_top3'][0]*100:.2f}%, {tech_headline['markov']['wilson95_top3'][1]*100:.2f}%] vs "
            f"Frequency {tech_headline['frequency']['top3']*100:.2f}% "
            f"[{tech_headline['frequency']['wilson95_top3'][0]*100:.2f}%, {tech_headline['frequency']['wilson95_top3'][1]*100:.2f}%]; "
            f"Coverage {tech_headline['coverage']['coverage_rate']*100:.2f}%. Markov does not outperform baseline. "
            f"(Support caution threshold: < 2 episodes or < 3 state transitions)."
        ),
    }

    tac_reliability_banner = {
        "metric": "Markov vs Frequency Hit@3",
        "slice": "tactic_collapsed",
        "sample_count": 76,
        "markov_hit3_pooled": tac_headline["markov"]["top3"],
        "markov_hit3_wilson95": list(tac_headline["markov"]["wilson95_top3"]),
        "frequency_hit3_pooled": tac_headline["frequency"]["top3"],
        "frequency_hit3_wilson95": list(tac_headline["frequency"]["wilson95_top3"]),
        "coverage_rate": tac_cov["coverage_rate"],
        "banner_text": (
            f"Tactic Level (tactic_collapsed, N=76): Markov Hit@3 {tac_headline['markov']['top3']*100:.2f}% "
            f"[{tac_headline['markov']['wilson95_top3'][0]*100:.2f}%, {tac_headline['markov']['wilson95_top3'][1]*100:.2f}%] vs "
            f"Frequency {tac_headline['frequency']['top3']*100:.2f}% "
            f"[{tac_headline['frequency']['wilson95_top3'][0]*100:.2f}%, {tac_headline['frequency']['wilson95_top3'][1]*100:.2f}%]; "
            f"Coverage {tac_cov['coverage_rate']*100:.2f}%. Order signal statistically significant under permutation S1. "
            f"(Support caution threshold: < 2 episodes or < 3 state transitions)."
        ),
    }

    all_records: list[dict[str, Any]] = []
    technique_caution_count = 0
    tactic_caution_count = 0

    # -------------------------------------------------------------------------
    # PART 1: 95 Technique LOEO Records
    # -------------------------------------------------------------------------
    print("\n[1/2] Assembling 95 Technique LOEO records (Schema 1.1.0)...")
    for idx, s in enumerate(cf_samples):
        sid = s["sample_id"]
        epid = s["episode_id"]
        csv_row = csv_by_slice_and_sample[("collapsed_full", sid)]

        fold_model_rel = f"artifacts/7ep/fold_models/collapsed_full/{epid}.json"
        fold_model_sha = manifest_data["files"][fold_model_rel]["sha256"]
        fold_model_path = REPO_ROOT / fold_model_rel
        with open(fold_model_path, "r", encoding="utf-8") as f:
            fm_data = json.load(f)

        training_eps = fm_data["training_episodes"]
        n_transitions = sum(fm_data["markov"]["n_step_transitions"].values())

        last_eids = s["input_item_event_ids"][-1]
        last_eid = last_eids[-1] if isinstance(last_eids, list) else str(last_eids)
        ev_obj = events_map.get(last_eid, {})

        raw_events_for_sample = []
        for e_group in s["input_item_event_ids"]:
            for eid in (e_group if isinstance(e_group, list) else [e_group]):
                if eid in events_map:
                    raw_events_for_sample.append(events_map[eid])

        prev_techs = [t for group in s["input_technique_sets"] for t in group]
        cur_techs = sorted(s["current_technique_set"])
        cur_tacs = sorted(list(set(to_shortname(t) for t in s.get("current_tactics", []) if t)))

        csv_status = csv_row["markov_status"]
        status = "ok" if csv_status == "ok" else "fallback"

        # State support
        n_sup_episodes, n_transitions_state = get_state_support("technique", training_eps, seqs_data, cur_techs)
        if status == "fallback":
            n_sup_episodes = 0
            n_transitions_state = 0.0
            caution = True
            caution_text = "Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators."
        else:
            caution = (n_sup_episodes < 2) or (n_transitions_state < 3.0)
            caution_text = (
                f"Caution: low historical support (observed in {n_sup_episodes} training episode(s) with {n_transitions_state:.1f} state transitions; caution threshold: < 2 episodes or < 3 transitions)."
                if caution else None
            )

        if caution:
            technique_caution_count += 1

        support_obj = {
            "n_supporting_training_episodes": int(n_sup_episodes),
            "n_transitions_from_state": float(n_transitions_state),
            "caution": bool(caution),
            "caution_text": caution_text,
        }

        # Candidates from CSV
        cands_raw = json.loads(csv_row["markov_fallback_top3"])
        ranked_candidates = []
        for cid, score in cands_raw:
            c_info = ref_data.get(cid, {})
            cname = c_info.get("official_technique_name")
            name_source = "technique_tactic_reference.json" if cname else None
            official_tactics = c_info.get("official_tactics", [])
            c_tactics = sorted(list(set(to_shortname(t) for t in official_tactics if t)))
            c_tactic_display = to_tactic_display(c_tactics)

            if status == "ok":
                score_type = "transition_probability"
                num, den, n_sup, sup_ids = get_candidate_supporting_episodes(
                    "technique", training_eps, seqs_data, cur_techs, cid
                )
            else:
                score_type = "training_frequency_share"
                num = fm_data["frequency"]["counts"].get(cid, 0.0)
                den = sum(fm_data["frequency"]["counts"].values())
                sup_ids = [
                    ep for ep in training_eps
                    if any(cid in itm.get("techniques", []) for itm in seqs_data["episodes"][ep]["collapsed"])
                ]
                n_sup = len(sup_ids)

            if float(score) > 0:
                assert num > 0, f"Candidate {cid} has score {score} but numerator {num} <= 0"

            ranked_candidates.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "name_source": name_source,
                "score": float(score),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": c_tactics,
                "tactic_display": c_tactic_display,
            })

        # Frequency baseline candidates
        freq_raw = json.loads(csv_row["frequency_top3"])
        freq_candidates = []
        for cid, score in freq_raw:
            c_info = ref_data.get(cid, {})
            freq_candidates.append({
                "candidate_id": cid,
                "candidate_name": c_info.get("official_technique_name"),
                "score": float(score),
            })

        # Alternatives (ranks 4..k)
        if status == "ok":
            combined_probs: dict[str, float] = defaultdict(float)
            w_mem = 1.0 / len(cur_techs) if cur_techs else 1.0
            for a in cur_techs:
                if a in fm_data["markov"]["probabilities"]:
                    for b, p in fm_data["markov"]["probabilities"][a].items():
                        combined_probs[b] += w_mem * p
            all_sorted = sorted(combined_probs.items(), key=lambda x: (-x[1], x[0]))
        else:
            all_sorted = sorted(fm_data["frequency"]["probabilities"].items(), key=lambda x: (-x[1], x[0]))

        alternatives = []
        for cid, sc in all_sorted[3:8]:
            c_info = ref_data.get(cid, {})
            cname = c_info.get("official_technique_name")
            name_source = "technique_tactic_reference.json" if cname else None
            official_tactics = c_info.get("official_tactics", [])
            c_tactics = sorted(list(set(to_shortname(t) for t in official_tactics if t)))
            c_tactic_display = to_tactic_display(c_tactics)

            if status == "ok":
                score_type = "transition_probability"
                num, den, n_sup, sup_ids = get_candidate_supporting_episodes(
                    "technique", training_eps, seqs_data, cur_techs, cid
                )
            else:
                score_type = "training_frequency_share"
                num = fm_data["frequency"]["counts"].get(cid, 0.0)
                den = sum(fm_data["frequency"]["counts"].values())
                sup_ids = [
                    ep for ep in training_eps
                    if any(cid in itm.get("techniques", []) for itm in seqs_data["episodes"][ep]["collapsed"])
                ]
                n_sup = len(sup_ids)

            if float(sc) > 0:
                assert num > 0, f"Alternative {cid} has score {sc} but numerator {num} <= 0"

            alternatives.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "name_source": name_source,
                "score": float(sc),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": c_tactics,
                "tactic_display": c_tactic_display,
            })

        # Tie flags
        scores = [c["score"] for c in ranked_candidates]
        tie_top1 = len(scores) >= 2 and abs(scores[0] - scores[1]) < 1e-9
        tie_top3 = len(all_sorted) >= 4 and abs(all_sorted[2][1] - all_sorted[3][1]) < 1e-9
        tied_cands = []
        if tie_top1:
            tied_cands = [c["candidate_id"] for c in ranked_candidates if abs(c["score"] - scores[0]) < 1e-9]
        elif tie_top3:
            tied_cands = [all_sorted[2][0], all_sorted[3][0]]

        tie_flags = {
            "tie_at_top1": bool(tie_top1),
            "tie_at_top3_boundary": bool(tie_top3),
            "tied_candidates": tied_cands,
        }

        explanation = generate_explanation_text(
            level="technique",
            status=status,
            current_set=cur_techs,
            ranked_candidates=ranked_candidates,
            training_episodes=training_eps,
            reliability_banner=tech_reliability_banner["banner_text"],
            tie_flags=tie_flags,
            support=support_obj,
        )

        tech_pred = {
            "status": status,
            "ranked_candidates": ranked_candidates,
            "alternatives": alternatives,
            "tie_flags": tie_flags,
            "frequency_baseline_candidates": freq_candidates,
            "measured_reliability_banner": tech_reliability_banner,
            "support": support_obj,
            "explanation": explanation,
        }

        rec = build_prediction_record(
            schema_version="1.1.0",
            prediction_type="technique",
            sample_id=sid,
            episode_id=epid,
            event_index=s.get("event_index"),
            last_timestamp=ev_obj.get("timestamp"),
            previous_supporting_techniques=prev_techs,
            current_technique_set=cur_techs,
            current_tactic_set=cur_tacs,
            incident_stage=ev_obj.get("incident_stage"),
            affected_asset=ev_obj.get("affected_asset"),
            c3_fields={
                "threat_score": None,
                "investigation_priority": None,
                "asset_criticality": None,
                "cti_confidence": None,
                "freshness": None,
                "ioc": None,
                "ioc_type": None,
            },
            model_type="first_order_markov_with_frequency_fallback",
            model_file_sha256=fold_model_sha,
            model_file_relpath=fold_model_rel,
            training_episodes=training_eps,
            transition_count=n_transitions,
            set_weighting_rule="uniform_1_over_cardinality",
            tie_break_rule="lexicographical_ascending",
            technique_prediction=tech_pred,
            tactic_prediction=None,
            raw_input_events=raw_events_for_sample,
        )
        all_records.append(rec)

    # -------------------------------------------------------------------------
    # PART 2: 76 Tactic LOEO Records
    # -------------------------------------------------------------------------
    print("\n[2/2] Assembling 76 Tactic LOEO records (Schema 1.1.0)...")
    tac_rows = [r for r in csv_rows if r["slice"] == "tactic_collapsed"]
    assert len(tac_rows) == 76, f"Expected 76 tactic rows, got {len(tac_rows)}"

    for idx, r in enumerate(tac_rows):
        sid = r["sample_id"]
        epid = r["test_episode"]

        fold_model_rel = f"artifacts/7ep/fold_models/tactic_collapsed/{epid}.json"
        fold_model_sha = manifest_data["files"][fold_model_rel]["sha256"]
        fold_model_path = REPO_ROOT / fold_model_rel
        with open(fold_model_path, "r", encoding="utf-8") as f:
            fm_data = json.load(f)

        training_eps = fm_data["training_episodes"]
        n_transitions = sum(fm_data["markov"]["n_step_transitions"].values())

        cur_tacs = [to_shortname(t) for t in json.loads(r["input_history"])]

        csv_status = r["markov_status"]
        status = "ok" if csv_status == "ok" else "fallback"

        # State support
        n_sup_episodes, n_transitions_state = get_state_support("tactic", training_eps, seqs_data, cur_tacs)
        if status == "fallback":
            n_sup_episodes = 0
            n_transitions_state = 0.0
            caution = True
            caution_text = "Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators."
        else:
            caution = (n_sup_episodes < 2) or (n_transitions_state < 3.0)
            caution_text = (
                f"Caution: low historical support (observed in {n_sup_episodes} training episode(s) with {n_transitions_state:.1f} state transitions; caution threshold: < 2 episodes or < 3 transitions)."
                if caution else None
            )

        if caution:
            tactic_caution_count += 1

        support_obj = {
            "n_supporting_training_episodes": int(n_sup_episodes),
            "n_transitions_from_state": float(n_transitions_state),
            "caution": bool(caution),
            "caution_text": caution_text,
        }

        cands_raw = json.loads(r["markov_fallback_top3"])
        ranked_candidates = []
        for cid, score in cands_raw:
            cname = TACTIC_DISPLAY_NAMES.get(cid, cid.replace("-", " ").title())
            name_source = "technique_tactic_reference.json"
            if status == "ok":
                score_type = "transition_probability"
                num, den, n_sup, sup_ids = get_candidate_supporting_episodes(
                    "tactic", training_eps, seqs_data, cur_tacs, cid
                )
            else:
                score_type = "training_frequency_share"
                num = fm_data["frequency"]["counts"].get(cid, 0.0)
                den = sum(fm_data["frequency"]["counts"].values())
                sup_ids = training_eps
                n_sup = len(sup_ids)

            if float(score) > 0:
                assert num > 0, f"Tactic candidate {cid} has score {score} but numerator {num} <= 0"

            ranked_candidates.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "name_source": name_source,
                "score": float(score),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": [cid],
                "tactic_display": [cname],
            })

        freq_raw = json.loads(r["frequency_top3"])
        freq_candidates = []
        for cid, score in freq_raw:
            cname = TACTIC_DISPLAY_NAMES.get(cid, cid.replace("-", " ").title())
            freq_candidates.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "score": float(score),
            })

        if status == "ok":
            combined_probs = defaultdict(float)
            w_mem = 1.0 / len(cur_tacs) if cur_tacs else 1.0
            for a in cur_tacs:
                if a in fm_data["markov"]["probabilities"]:
                    for b, p in fm_data["markov"]["probabilities"][a].items():
                        combined_probs[b] += w_mem * p
            all_sorted = sorted(combined_probs.items(), key=lambda x: (-x[1], x[0]))
        else:
            all_sorted = sorted(fm_data["frequency"]["probabilities"].items(), key=lambda x: (-x[1], x[0]))

        alternatives = []
        for cid, sc in all_sorted[3:8]:
            cname = TACTIC_DISPLAY_NAMES.get(cid, cid.replace("-", " ").title())
            name_source = "technique_tactic_reference.json"

            if status == "ok":
                score_type = "transition_probability"
                num, den, n_sup, sup_ids = get_candidate_supporting_episodes(
                    "tactic", training_eps, seqs_data, cur_tacs, cid
                )
            else:
                score_type = "training_frequency_share"
                num = fm_data["frequency"]["counts"].get(cid, 0.0)
                den = sum(fm_data["frequency"]["counts"].values())
                sup_ids = training_eps
                n_sup = len(sup_ids)

            if float(sc) > 0:
                assert num > 0, f"Alternative {cid} has score {sc} but numerator {num} <= 0"

            alternatives.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "name_source": name_source,
                "score": float(sc),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": [cid],
                "tactic_display": [cname],
            })

        scores = [c["score"] for c in ranked_candidates]
        tie_top1 = len(scores) >= 2 and abs(scores[0] - scores[1]) < 1e-9
        tie_top3 = len(all_sorted) >= 4 and abs(all_sorted[2][1] - all_sorted[3][1]) < 1e-9
        tied_cands = []
        if tie_top1:
            tied_cands = [c["candidate_id"] for c in ranked_candidates if abs(c["score"] - scores[0]) < 1e-9]
        elif tie_top3:
            tied_cands = [all_sorted[2][0], all_sorted[3][0]]

        tie_flags = {
            "tie_at_top1": bool(tie_top1),
            "tie_at_top3_boundary": bool(tie_top3),
            "tied_candidates": tied_cands,
        }

        explanation = generate_explanation_text(
            level="tactic",
            status=status,
            current_set=cur_tacs,
            ranked_candidates=ranked_candidates,
            training_episodes=training_eps,
            reliability_banner=tac_reliability_banner["banner_text"],
            tie_flags=tie_flags,
            support=support_obj,
        )

        tac_pred = {
            "status": status,
            "ranked_candidates": ranked_candidates,
            "alternatives": alternatives,
            "tie_flags": tie_flags,
            "frequency_baseline_candidates": freq_candidates,
            "measured_reliability_banner": tac_reliability_banner,
            "support": support_obj,
            "explanation": explanation,
        }

        rec = build_prediction_record(
            schema_version="1.1.0",
            prediction_type="tactic",
            sample_id=sid,
            episode_id=epid,
            event_index=None,
            last_timestamp=None,
            previous_supporting_techniques=[],
            current_technique_set=[],
            current_tactic_set=cur_tacs,
            incident_stage=None,
            affected_asset=None,
            c3_fields={
                "threat_score": None,
                "investigation_priority": None,
                "asset_criticality": None,
                "cti_confidence": None,
                "freshness": None,
                "ioc": None,
                "ioc_type": None,
            },
            model_type="first_order_markov_with_frequency_fallback",
            model_file_sha256=fold_model_sha,
            model_file_relpath=fold_model_rel,
            training_episodes=training_eps,
            transition_count=n_transitions,
            set_weighting_rule="uniform_1_over_cardinality",
            tie_break_rule="lexicographical_ascending",
            technique_prediction=None,
            tactic_prediction=tac_pred,
            raw_input_events=[],
        )
        all_records.append(rec)

    assert len(all_records) == 171, f"Expected 171 records, got {len(all_records)}"
    print(f"Total explainable prediction records built: {len(all_records)} (95 technique + 76 tactic) [PASS]")
    total_caution = technique_caution_count + tactic_caution_count
    print(f"Number of cautioned records: {total_caution}/171 ({technique_caution_count}/95 technique, {tactic_caution_count}/76 tactic)")

    # Write out JSONL
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSONL, "w", encoding="utf-8") as f:
        for r in all_records:
            f.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    print(f"Saved: {OUT_JSONL}")

    # Enforce Gate G-P5-1
    print("\nEnforcing Gate G-P5-1: Top-k candidates and order match evaluation_7ep_predictions.csv...")
    for rec in all_records:
        sid = rec["input"]["sample_id"]
        sl = "collapsed_full" if rec["prediction_type"] == "technique" else "tactic_collapsed"
        csv_r = csv_by_slice_and_sample[(sl, sid)]
        exp_cands = json.loads(csv_r["markov_fallback_top3"])

        pred_obj = rec["technique_prediction"] if rec["prediction_type"] == "technique" else rec["tactic_prediction"]
        act_cands = [(c["candidate_id"], c["score"]) for c in pred_obj["ranked_candidates"]]

        assert len(act_cands) == len(exp_cands), f"Mismatch in candidate count for {sid}: {len(act_cands)} vs {len(exp_cands)}"
        for (a_id, a_sc), (e_id, e_sc) in zip(act_cands, exp_cands):
            assert a_id == e_id, f"Candidate ID mismatch for {sid}: {a_id} != {e_id}"
            assert abs(a_sc - e_sc) < 1e-9, f"Candidate score mismatch for {sid}: {a_sc} != {e_sc}"

    print("Gate G-P5-1 verified: 100% (171/171) records match evaluation_7ep_predictions.csv exactly [PASS]")

    # Generate Worked Examples Report
    generate_worked_examples_report(all_records, csv_by_slice_and_sample, technique_caution_count, tactic_caution_count)

    return all_records, {"tech_banner": tech_reliability_banner, "tac_banner": tac_reliability_banner}


def generate_worked_examples_report(
    records: list[dict[str, Any]],
    csv_map: dict[tuple[str, str], dict[str, Any]],
    technique_caution_count: int,
    tactic_caution_count: int,
) -> None:
    print("\nGenerating prediction_record_examples.md (7 distinct categories)...")
    used_ids: set[str] = set()
    first_hit = None
    first_miss = None
    first_fallback = None
    first_tied = None
    first_tactic = None
    first_single_ep = None
    first_set_val = None

    # 1. Hit
    for r in records:
        sid = r["input"]["sample_id"]
        if r["prediction_type"] == "technique":
            p_obj = r["technique_prediction"]
            csv_r = csv_map[("collapsed_full", sid)]
            is_hit = int(csv_r["markov_fallback_hit1"]) == 1
            if is_hit and p_obj["status"] == "ok" and first_hit is None:
                first_hit = ("1. First Hit", r, "Technique prediction where top candidate matches ground-truth next step.")
                used_ids.add(sid)
                break

    # 2. Miss
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "technique":
            p_obj = r["technique_prediction"]
            csv_r = csv_map[("collapsed_full", sid)]
            is_hit = int(csv_r["markov_fallback_hit1"]) == 1
            if not is_hit and p_obj["status"] == "ok" and first_miss is None:
                first_miss = ("2. First Miss", r, "Technique prediction where top candidate missed ground-truth next step.")
                used_ids.add(sid)
                break

    # 3. Fallback
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "technique":
            p_obj = r["technique_prediction"]
            if p_obj["status"] == "fallback" and first_fallback is None:
                first_fallback = (
                    "3. Frequency Fallback (Unseen State)",
                    r,
                    "Unobserved historical state; dataset exhibits exactly one fallback reason (unseen state with zero outgoing training transitions); falls back to unconditional training frequency baseline."
                )
                used_ids.add(sid)
                break

    # 4. Tied
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "technique":
            p_obj = r["technique_prediction"]
            is_tied = p_obj["tie_flags"]["tie_at_top1"] or p_obj["tie_flags"]["tie_at_top3_boundary"]
            if is_tied and first_tied is None:
                first_tied = ("4. Tied Rank Boundary", r, "Candidate scores tied at rank boundary; resolved deterministically by lexicographical order.")
                used_ids.add(sid)
                break

    # 5. Tactic
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "tactic" and first_tactic is None:
            first_tactic = ("5. Tactic-Level Prediction", r, "Next-tactic prediction demonstrating secondary LOEO evaluation slice.")
            used_ids.add(sid)
            break

    # 6. Single episode support
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "technique":
            p_obj = r["technique_prediction"]
            if p_obj["status"] == "ok" and p_obj["support"]["n_supporting_training_episodes"] == 1 and first_single_ep is None:
                first_single_ep = ("6. Single-Episode Support State", r, "State observed in exactly 1 training episode; demonstrates low-support caution handling.")
                used_ids.add(sid)
                break

    # 7. Set-valued state
    for r in records:
        sid = r["input"]["sample_id"]
        if sid in used_ids:
            continue
        if r["prediction_type"] == "technique":
            if len(r["input"]["current_technique_set"]) > 1 and first_set_val is None:
                first_set_val = ("7. Set-Valued State", r, "Current attack state comprises multiple simultaneous techniques with uniform 1/|S| weighting.")
                used_ids.add(sid)
                break

    exemplars = [first_hit, first_miss, first_fallback, first_tied, first_tactic, first_single_ep, first_set_val]
    assert all(ex is not None for ex in exemplars), "Failed to find all 7 exemplar categories"
    exemplar_sids = [ex[1]["input"]["sample_id"] for ex in exemplars]
    assert len(set(exemplar_sids)) == len(exemplars), f"Exemplar sample IDs not all distinct: {exemplar_sids}"

    total_caution = technique_caution_count + tactic_caution_count

    lines: list[str] = [
        "# Explainable Prediction Record Worked Examples (7 Episodes, Schema 1.1.0)",
        "",
        "> [!NOTE]",
        "> This report presents seven full, worked, representative prediction records generated",
        "> by Component 4 under Leave-One-Episode-Out (LOEO) evaluation across 7 episodes.",
        "> Every record conforms to `schemas/c4_prediction_record.schema.json` (version 1.1.0) and satisfies",
        "> requirements FR4 (candidate ranking), FR5 (evidence support), FR6 (explainability surface),",
        "> FR7 (confidence scoring and reliability context), NFR2 (reproducibility), NFR3 (provenance),",
        "> and NFR6 (schema compliance).",
        "",
        "## Support Caution Summary",
        "",
        f"- **Total Prediction Records**: {len(records)} (95 technique, 76 tactic)",
        f"- **Cautioned Records**: {total_caution}/{len(records)} ({technique_caution_count}/95 technique records, {tactic_caution_count}/76 tactic records)",
        "- **Caution Threshold Policy**: A prediction record is flagged with `caution=True` when the current attack state has fewer than 2 supporting training episodes or fewer than 3 total historical transitions from that state. In the evaluation dataset, all 34 unobserved states (which trigger unconditional frequency fallback) are flagged with caution.",
        "- **Fallback Mechanism**: The evaluation dataset contains exactly one fallback reason: unobserved historical state (zero outgoing training transitions). No secondary fallback modes exist in the data.",
        "",
        "## Summary of Exemplars (7 Distinct Sample IDs)",
        "",
        "| Exemplar Category | Sample ID | Episode | Level | Status | Caution | Top-1 Candidate | Top-1 Score | Score Type |",
        "|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---|",
    ]

    for label, ex, desc in exemplars:
        sid = ex["input"]["sample_id"]
        ep = ex["input"]["episode_id"]
        lvl = ex["prediction_type"]
        p_obj = ex["technique_prediction"] if lvl == "technique" else ex["tactic_prediction"]
        st = p_obj["status"]
        caut_str = "YES" if p_obj["support"]["caution"] else "No"
        top_c = p_obj["ranked_candidates"][0] if p_obj["ranked_candidates"] else {}
        cid = top_c.get("candidate_id", "None")
        sc = top_c.get("score", 0.0)
        stype = top_c.get("score_type", "None")
        lines.append(f"| {label} | `{sid}` | {ep} | {lvl} | `{st}` | {caut_str} | `{cid}` | {sc:.4f} | `{stype}` |")

    lines.append("")

    for label, ex, desc in exemplars:
        sid = ex["input"]["sample_id"]
        ep = ex["input"]["episode_id"]
        lvl = ex["prediction_type"]
        p_obj = ex["technique_prediction"] if lvl == "technique" else ex["tactic_prediction"]
        sup = p_obj["support"]

        lines.extend([
            f"## Exemplar: {label} (`{sid}`)",
            "",
            f"- **Description**: {desc}",
            f"- **Record ID**: `{ex['record_id']}`",
            f"- **Episode**: {ep}",
            f"- **Prediction Level**: {lvl}",
            f"- **Model SHA-256**: `{ex['model']['model_file_sha256']}`",
            f"- **Input Events SHA-256**: `{ex['input_events_sha256']}`",
            f"- **Record SHA-256**: `{ex['record_sha256']}`",
            f"- **Current State**: Techniques=`{ex['input']['current_technique_set']}`, Tactics=`{ex['input']['current_tactic_set']}`",
            f"- **Model Status**: `{p_obj['status']}`",
            f"- **Support Metrics**: Supporting Episodes={sup['n_supporting_training_episodes']}, Transitions from State={sup['n_transitions_from_state']:.2f}, Caution={sup['caution']}",
        ])

        if sup["caution_text"]:
            lines.append(f"- **Caution Text**: {sup['caution_text']}")

        lines.extend([
            "",
            "### Ranked Top Candidates",
            "",
            "| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |",
            "|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|",
        ])

        for r_idx, c in enumerate(p_obj["ranked_candidates"], start=1):
            ep_str = ", ".join(c["supporting_episode_ids"]) if c["supporting_episode_ids"] else "none"
            t_disp = ", ".join(c["tactic_display"]) if c["tactic_display"] else "none"
            lines.append(
                f"| {r_idx} | `{c['candidate_id']}` | {c['candidate_name']} | {c['score']:.4f} | "
                f"`{c['score_type']}` | {c['numerator']:.2f} | {c['denominator']:.2f} | [{ep_str}] | {t_disp} |"
            )

        if p_obj.get("alternatives"):
            lines.extend([
                "",
                "### Alternative Candidates (Ranks 4..k)",
                "",
                "| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |",
                "|:---:|:---|:---|:---:|:---|:---:|:---:|:---|",
            ])
            for r_idx, c in enumerate(p_obj["alternatives"], start=4):
                ep_str = ", ".join(c["supporting_episode_ids"]) if c["supporting_episode_ids"] else "none"
                lines.append(
                    f"| {r_idx} | `{c['candidate_id']}` | {c['candidate_name']} | {c['score']:.4f} | "
                    f"`{c['score_type']}` | {c['numerator']:.2f} | {c['denominator']:.2f} | [{ep_str}] |"
                )

        lines.extend([
            "",
            "### Deterministic Explanation",
            "",
            f"> {p_obj['explanation']}",
            "",
            "### Full Canonical JSON Record",
            "",
            "```json",
            json.dumps(ex, indent=2, sort_keys=True, ensure_ascii=False),
            "```",
            "",
            "---",
            "",
        ])

    OUT_EXAMPLES_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_EXAMPLES_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Saved: {OUT_EXAMPLES_MD}")


if __name__ == "__main__":
    build_all_records()
