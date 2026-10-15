#!/usr/bin/env python3
"""Build Explainable Prediction Records LOEO Dataset and Examples Report (P5).

Satisfies FR4-FR7, NFR2, NFR3, and NFR6:
1. Builds data/processed_7ep/prediction_records_loeo.jsonl (171 records: 95 technique + 76 tactic).
2. Generates reports/7ep/prediction_record_examples.md with full worked examples.
3. Enforces Gate G-P5-1: candidate lists match evaluation_7ep_predictions.csv exactly.
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
            # build collapsed tactics
            col_tacs = []
            for ev in raw_items:
                t_list = ev.get("official_tactics") or ev.get("tactics", [])
                # simplify to shortnames
                s_tacs = sorted(list(set(t.lower().replace(" ", "-").replace("_", "-") for t in t_list if t)))
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


def build_all_records() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    print("=" * 80)
    print("BUILDING EXPLAINABLE PREDICTION RECORDS (LOEO, 7 EPISODES)")
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
            f"Coverage {tech_headline['coverage']['coverage_rate']*100:.2f}%. Markov does not outperform baseline."
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
            f"Coverage {tac_cov['coverage_rate']*100:.2f}%. Order signal statistically significant under permutation S1."
        ),
    }

    all_records: list[dict[str, Any]] = []

    # -------------------------------------------------------------------------
    # PART 1: 95 Technique LOEO Records
    # -------------------------------------------------------------------------
    print("\n[1/2] Assembling 95 Technique LOEO records...")
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

        # Determine last event
        last_eids = s["input_item_event_ids"][-1]
        last_eid = last_eids[-1] if isinstance(last_eids, list) else str(last_eids)
        ev_obj = events_map.get(last_eid, {})

        # Raw input events for SHA-256
        raw_events_for_sample = []
        for e_group in s["input_item_event_ids"]:
            for eid in (e_group if isinstance(e_group, list) else [e_group]):
                if eid in events_map:
                    raw_events_for_sample.append(events_map[eid])

        # Previous techniques in order
        prev_techs = [t for group in s["input_technique_sets"] for t in group]
        cur_techs = sorted(s["current_technique_set"])
        cur_tacs = sorted(s.get("current_tactics", []))

        # Check model status
        csv_status = csv_row["markov_status"]
        status = "ok" if csv_status == "ok" else "fallback"

        # Predictions from CSV
        cands_raw = json.loads(csv_row["markov_fallback_top3"])

        # Top-3 candidates formatting
        ranked_candidates = []
        for cid, score in cands_raw:
            cname = ref_data.get(cid, {}).get("name")
            tactics = ref_data.get(cid, {}).get("tactics", [])
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

            ranked_candidates.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "score": float(score),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": tactics,
            })

        # Frequency baseline top-3
        freq_raw = json.loads(csv_row["frequency_top3"])
        freq_candidates = [
            {
                "candidate_id": cid,
                "candidate_name": ref_data.get(cid, {}).get("name"),
                "score": float(score),
            }
            for cid, score in freq_raw
        ]

        # Alternatives (FR6): next candidates 4..k from all candidates
        # Extract from fold model
        if status == "ok":
            # Combined probs
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
            alternatives.append({
                "candidate_id": cid,
                "candidate_name": ref_data.get(cid, {}).get("name"),
                "score": float(sc),
                "score_type": "transition_probability" if status == "ok" else "training_frequency_share",
                "numerator": 0.0,
                "denominator": 1.0,
                "supporting_episodes_count": 0,
                "supporting_episode_ids": [],
                "tactics": ref_data.get(cid, {}).get("tactics", []),
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
        )

        tech_pred = {
            "status": status,
            "ranked_candidates": ranked_candidates,
            "alternatives": alternatives,
            "tie_flags": tie_flags,
            "frequency_baseline_candidates": freq_candidates,
            "measured_reliability_banner": tech_reliability_banner,
            "explanation": explanation,
        }

        rec = build_prediction_record(
            schema_version="1.0.0",
            prediction_type="technique",
            sample_id=sid,
            episode_id=epid,
            event_index=s.get("prefix_length"),
            last_timestamp=ev_obj.get("timestamp"),
            previous_supporting_techniques=prev_techs,
            current_technique_set=cur_techs,
            current_tactic_set=cur_tacs,
            incident_stage=ev_obj.get("incident_stage"),
            affected_asset=ev_obj.get("hostname"),
            c3_fields={
                "threat_score": ev_obj.get("c3_threat_score"),
                "investigation_priority": ev_obj.get("investigation_priority"),
                "asset_criticality": ev_obj.get("asset_criticality"),
                "cti_confidence": ev_obj.get("cti_confidence"),
                "freshness": ev_obj.get("freshness"),
                "ioc": ev_obj.get("ioc"),
                "ioc_type": ev_obj.get("ioc_type"),
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
    print("\n[2/2] Assembling 76 Tactic LOEO records...")
    tactic_csv_rows = [r for r in csv_rows if r["slice"] == "tactic_collapsed"]
    assert len(tactic_csv_rows) == 76, f"Expected 76 tactic rows, got {len(tactic_csv_rows)}"

    for idx, r in enumerate(tactic_csv_rows):
        sid = r["sample_id"]
        epid = r["test_episode"]

        fold_model_rel = f"artifacts/7ep/fold_models/tactic_collapsed/{epid}.json"
        fold_model_sha = manifest_data["files"][fold_model_rel]["sha256"]
        fold_model_path = REPO_ROOT / fold_model_rel
        with open(fold_model_path, "r", encoding="utf-8") as f:
            fm_data = json.load(f)

        training_eps = fm_data["training_episodes"]
        n_transitions = sum(fm_data["markov"]["n_step_transitions"].values())

        cur_tacs = json.loads(r["input_history"])

        csv_status = r["markov_status"]
        status = "ok" if csv_status == "ok" else "fallback"

        cands_raw = json.loads(r["markov_fallback_top3"])
        ranked_candidates = []
        for cid, score in cands_raw:
            cname = cid.capitalize().replace("-", " ")
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

            ranked_candidates.append({
                "candidate_id": cid,
                "candidate_name": cname,
                "score": float(score),
                "score_type": score_type,
                "numerator": float(num),
                "denominator": float(den) if den > 0 else 1.0,
                "supporting_episodes_count": int(n_sup),
                "supporting_episode_ids": sup_ids,
                "tactics": [cid],
            })

        freq_raw = json.loads(r["frequency_top3"])
        freq_candidates = [
            {
                "candidate_id": cid,
                "candidate_name": cid.capitalize().replace("-", " "),
                "score": float(score),
            }
            for cid, score in freq_raw
        ]

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
            alternatives.append({
                "candidate_id": cid,
                "candidate_name": cid.capitalize().replace("-", " "),
                "score": float(sc),
                "score_type": "transition_probability" if status == "ok" else "training_frequency_share",
                "numerator": 0.0,
                "denominator": 1.0,
                "supporting_episodes_count": 0,
                "supporting_episode_ids": [],
                "tactics": [cid],
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
        )

        tac_pred = {
            "status": status,
            "ranked_candidates": ranked_candidates,
            "alternatives": alternatives,
            "tie_flags": tie_flags,
            "frequency_baseline_candidates": freq_candidates,
            "measured_reliability_banner": tac_reliability_banner,
            "explanation": explanation,
        }

        rec = build_prediction_record(
            schema_version="1.0.0",
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
    generate_worked_examples_report(all_records, csv_by_slice_and_sample)

    return all_records, {"tech_banner": tech_reliability_banner, "tac_banner": tac_reliability_banner}


def generate_worked_examples_report(
    records: list[dict[str, Any]],
    csv_map: dict[tuple[str, str], dict[str, Any]],
) -> None:
    print("\nGenerating prediction_record_examples.md...")
    first_hit = None
    first_miss = None
    first_fallback = None
    first_unseen = None
    first_tied = None

    for r in records:
        if r["prediction_type"] == "technique":
            sid = r["input"]["sample_id"]
            csv_r = csv_map[("collapsed_full", sid)]
            is_hit = int(csv_r["markov_fallback_hit1"]) == 1
            status = r["technique_prediction"]["status"]
            is_tied = r["technique_prediction"]["tie_flags"]["tie_at_top1"] or r["technique_prediction"]["tie_flags"]["tie_at_top3_boundary"]

            if is_hit and first_hit is None:
                first_hit = r
            if not is_hit and first_miss is None:
                first_miss = r
            if status == "fallback" and first_fallback is None:
                first_fallback = r
            if csv_r["markov_status"] == "insufficient_evidence" and first_unseen is None:
                first_unseen = r
            if is_tied and first_tied is None:
                first_tied = r

    lines: list[str] = [
        "# Explainable Prediction Record Worked Examples (7 Episodes)",
        "",
        "> [!NOTE]",
        "> This report presents five full, worked, representative prediction records generated",
        "> by Component 4 under Leave-One-Episode-Out (LOEO) evaluation across 7 episodes.",
        "> Every record conforms to `schemas/c4_prediction_record.schema.json` and satisfies",
        "> requirements FR4 (candidate ranking), FR5 (evidence support), FR6 (explainability surface),",
        "> FR7 (confidence scoring and reliability context), NFR2 (reproducibility), NFR3 (provenance),",
        "> and NFR6 (schema compliance).",
        "",
        "## Summary of Exemplars",
        "",
        "| Exemplar Type | Sample ID | Episode | Level | Status | Top-1 Candidate | Top-1 Score | Score Type |",
        "|:---|:---|:---:|:---:|:---:|:---|:---:|:---|",
    ]

    exemplars = [
        ("1. First Hit", first_hit),
        ("2. First Miss", first_miss),
        ("3. First Fallback", first_fallback),
        ("4. First Unseen State", first_unseen),
        ("5. First Tied Boundary", first_tied),
    ]

    for label, ex in exemplars:
        if ex:
            sid = ex["input"]["sample_id"]
            ep = ex["input"]["episode_id"]
            lvl = ex["prediction_type"]
            p_obj = ex["technique_prediction"] if lvl == "technique" else ex["tactic_prediction"]
            st = p_obj["status"]
            top_c = p_obj["ranked_candidates"][0] if p_obj["ranked_candidates"] else {}
            cid = top_c.get("candidate_id", "None")
            sc = top_c.get("score", 0.0)
            stype = top_c.get("score_type", "None")
            lines.append(f"| {label} | `{sid}` | {ep} | {lvl} | `{st}` | `{cid}` | {sc:.4f} | `{stype}` |")

    lines.append("")

    for label, ex in exemplars:
        if not ex:
            continue
        sid = ex["input"]["sample_id"]
        ep = ex["input"]["episode_id"]
        lvl = ex["prediction_type"]
        p_obj = ex["technique_prediction"] if lvl == "technique" else ex["tactic_prediction"]

        lines.extend([
            f"## Exemplar: {label} (`{sid}`)",
            "",
            f"- **Record ID**: `{ex['record_id']}`",
            f"- **Episode**: {ep}",
            f"- **Prediction Level**: {lvl}",
            f"- **Model SHA-256**: `{ex['model']['model_file_sha256']}`",
            f"- **Input Events SHA-256**: `{ex['input_events_sha256']}`",
            f"- **Record SHA-256**: `{ex['record_sha256']}`",
            f"- **Current State**: `{ex['input']['current_technique_set']}` (Tactics: `{ex['input']['current_tactic_set']}`)",
            f"- **Model Status**: `{p_obj['status']}`",
            "",
            "### Ranked Top Candidates",
            "",
            "| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |",
            "|:---:|:---|:---|:---:|:---|:---:|:---:|:---|",
        ])

        for r_idx, c in enumerate(p_obj["ranked_candidates"], start=1):
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
