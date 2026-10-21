#!/usr/bin/env python3
"""
C2 pipeline: merge Stage 1 (technique + probability + SHAP), sequence, Stage 2 (next techniques) and escalation
into ONE record per event for Component 3 (proposal sections 3.8 and 4.3).

Usage: python c2_pipeline.py <task_B_next_technique.csv> <stage1_test_predictions_shap.csv> <stage2_model.json> <stage3_c2_output_for_c3.csv> <out_dir>
Writes: c2_output.json, c2_output.csv, c2_pipeline_check.json.   Needs pandas + numpy. Seed-free (deterministic).

State used for the Markov step = the technique PREDICTED by Stage 1 (what a deployed system would have).
Events Stage 1 does not flag (p_malicious < 0.5 or BENIGN) get detected_technique = null and no next-technique prediction.
Test-split events of task B only (1,278 rows, 8 scenarios). The dataset has no host field: session_id is the host/session identifier.
"""
import sys, json, numpy as np, pandas as pd
B_CSV, S1_CSV, MODEL, S3_CSV, OUT = sys.argv[1:6]
SCHEMA = "1.0"

# --- same ATT&CK order / map as stage3_escalation.py (verified against it below)
ORDER = {"Reconnaissance":1,"Resource Development":2,"Initial Access":3,"Execution":4,"Persistence":5,"Privilege Escalation":6,
         "Defense Evasion":7,"Credential Access":8,"Discovery":9,"Lateral Movement":10,"Collection":11,"Command and Control":12,
         "Exfiltration":13,"Impact":14}
TACTICS = {"T1021.006":["Lateral Movement"],"T1021.002":["Lateral Movement"],"T1047":["Execution"],"T1059.001":["Execution"],
 "T1059.003":["Execution"],"T1059.005":["Execution"],"T1574.001":["Persistence","Privilege Escalation","Defense Evasion"],
 "T1070.004":["Defense Evasion"],"T1562.004":["Defense Evasion"],"T1110":["Credential Access"],"T1087":["Discovery"],
 "T1087.001":["Discovery"],"T1069.001":["Discovery"],"T1201":["Discovery"],"T1016":["Discovery"],"T1049":["Discovery"],
 "T1033":["Discovery"],"T1095":["Command and Control"],"T1105":["Command and Control"]}
def rank(label): return max(ORDER[t] for p in label.split(";") for t in TACTICS[p.strip()])
def tactics(label): return sorted({t for p in label.split(";") for t in TACTICS[p.strip()]}, key=lambda t: ORDER[t])

M = json.load(open(MODEL)); alpha, vocab, glob = M["alpha"], M["vocab"], M["global_frequency"]; V = len(vocab)
def dist(state):
    c = M["counts"].get(state); seen = bool(c); c = c or glob; tot = sum(c.values())
    return {v: (c.get(v, 0) + alpha) / (tot + alpha * V) for v in vocab}, seen, tot

B = pd.read_csv(B_CSV, low_memory=False).dropna(subset=["current_mitre_id", "next_mitre_technique"])
te = B[B.split_assignment == "test"][["source_record_id","scenario_id","session_id","source_dataset","timestamp_normalized","sequence_position","current_mitre_id"]]
S1 = pd.read_csv(S1_CSV, low_memory=False)
assert S1.source_record_id.is_unique and te.source_record_id.is_unique
e = te.merge(S1, on="source_record_id", how="left", suffixes=("", "_s1"))
assert e.predicted.notna().all(), "every task-B test event must have a Stage 1 prediction"
e = e.sort_values(["session_id", "sequence_position"]).reset_index(drop=True)
e["detected"] = (e.p_malicious >= 0.5) & (e.predicted != "BENIGN")

recs, seq_by_session = [], {}
for r in e.itertuples():
    seq = seq_by_session.setdefault(r.session_id, [])
    rec = {"schema_version": SCHEMA, "event_id": r.source_record_id, "scenario_id": r.scenario_id, "session_id": r.session_id,
           "host_or_session": r.session_id, "source_dataset": r.source_dataset.split(":")[0], "timestamp": r.timestamp_normalized,
           "sequence_position": int(r.sequence_position)}
    if r.detected:
        t = r.predicted; seq.append(t)
        rec["detection"] = {"technique_id": t, "tactics": tactics(t), "classification_probability": round(float(r.top1_prob), 4),
                            "malicious_probability": round(float(r.p_malicious), 4),
                            "alternatives": [{"technique_id": getattr(r, f"top{k}"), "probability": round(float(getattr(r, f"top{k}_prob")), 4)} for k in (2, 3)],
                            "explanation_top_features": [{"feature": getattr(r, f"shap_feat{k}"), "shap_value": float(getattr(r, f"shap_feat{k}_value"))} for k in range(1, 6)]}
        d, seen, tot = dist(t)
        top = sorted(d.items(), key=lambda kv: (-kv[1], vocab.index(kv[0])))[:3]
        esc = sum(p for v, p in d.items() if rank(v) > rank(t))
        rec["observed_sequence"] = list(seq[-10:])
        rec["prediction"] = {"next_techniques": [{"technique_id": n, "probability": round(p, 4), "training_transition_count": M["counts"].get(t, {}).get(n, 0)} for n, p in top],
                             "escalation_probability": round(esc, 4), "state_seen_in_training": seen, "state_training_total": tot,
                             "model": "first-order Markov", "alpha": alpha}
    else:
        rec["detection"] = None; rec["observed_sequence"] = list(seq[-10:]); rec["prediction"] = None
    recs.append(rec)

json.dump(recs, open(f"{OUT}/c2_output.json", "w"), indent=1)
flat = []
for x in recs:
    d, p = x["detection"], x["prediction"]
    row = {k: x[k] for k in ("schema_version","event_id","scenario_id","session_id","host_or_session","source_dataset","timestamp","sequence_position")}
    row.update({"detected_technique": d and d["technique_id"], "classification_probability": d and d["classification_probability"],
                "malicious_probability": d and d["malicious_probability"], "tactics": d and ";".join(d["tactics"]),
                "observed_sequence": " > ".join(x["observed_sequence"]),
                "explanation_top5": d and " | ".join(f"{f['feature']}={f['shap_value']}" for f in d["explanation_top_features"])})
    for k in (1, 2, 3):
        n = p["next_techniques"][k-1] if p else None
        row[f"next_{k}"], row[f"next_{k}_prob"] = n and n["technique_id"], n and n["probability"]
    row["escalation_probability"] = p and p["escalation_probability"]
    row["state_seen_in_training"] = p and p["state_seen_in_training"]
    flat.append(row)
pd.DataFrame(flat).to_csv(f"{OUT}/c2_output.csv", index=False)

# --- consistency check against stage3 output: where Stage 1 state == true state, escalation + next-3 must be identical
S3 = pd.read_csv(S3_CSV).set_index("source_record_id"); bad = 0; cmp_n = 0
for x, r in zip(recs, e.itertuples()):
    if x["prediction"] and r.predicted == r.current_mitre_id:
        s = S3.loc[r.source_record_id]; cmp_n += 1
        ok = abs(s.escalation_probability - x["prediction"]["escalation_probability"]) < 1e-9 and \
             [s.next_1, s.next_2, s.next_3] == [n["technique_id"] for n in x["prediction"]["next_techniques"]]
        bad += (not ok)
chk = {"events": len(recs), "detected": int(e.detected.sum()), "not_detected": int((~e.detected).sum()),
       "by_source_detected": e.groupby(e.source_dataset.str.split(":").str[0]).detected.sum().astype(int).to_dict(),
       "rows_compared_with_stage3": cmp_n, "mismatches_with_stage3": bad,
       "events_where_stage1_state_differs_from_true_state": int((e.detected & (e.predicted != e.current_mitre_id)).sum())}
assert bad == 0, chk
json.dump(chk, open(f"{OUT}/c2_pipeline_check.json", "w"), indent=1); print(json.dumps(chk, indent=1))
