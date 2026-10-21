#!/usr/bin/env python3
"""
C2 escalation probability (proposal: derived from Stage 2 transition probabilities + ATT&CK tactic order).

  Escalation(Ti) = sum over Tj with tactic_rank(Tj) > tactic_rank(Ti) of P(Tj | Ti)
  P comes from the Stage 2 model (stage2_model.json, fitted on train+validation only).
  Tactic order = official ATT&CK Enterprise kill-chain order (NOT the dataset's own phase column).
  Technique with several tactics -> its LATEST tactic (assumption, see TACTICS below).

Usage: python stage3_escalation.py <task_B_next_technique.csv> <stage2_model.json> <out_dir>
Needs pandas + numpy + scikit-learn. Does not use task_C or any label column as input.
"""
import sys, json, numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score, brier_score_loss
B_CSV, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

ORDER = {"Reconnaissance":1,"Resource Development":2,"Initial Access":3,"Execution":4,"Persistence":5,"Privilege Escalation":6,
         "Defense Evasion":7,"Credential Access":8,"Discovery":9,"Lateral Movement":10,"Collection":11,"Command and Control":12,
         "Exfiltration":13,"Impact":14}
# technique -> ATT&CK tactic(s) (Enterprise matrix). Multi-tactic techniques use the latest tactic in ORDER.
TACTICS = {
 "T1021.006":["Lateral Movement"], "T1021.002":["Lateral Movement"], "T1047":["Execution"],
 "T1059.001":["Execution"], "T1059.003":["Execution"], "T1059.005":["Execution"],
 "T1574.001":["Persistence","Privilege Escalation","Defense Evasion"],
 "T1070.004":["Defense Evasion"], "T1562.004":["Defense Evasion"], "T1110":["Credential Access"],
 "T1087":["Discovery"], "T1087.001":["Discovery"], "T1069.001":["Discovery"], "T1201":["Discovery"],
 "T1016":["Discovery"], "T1049":["Discovery"], "T1033":["Discovery"],
 "T1095":["Command and Control"], "T1105":["Command and Control"]}
def rank(label):                      # label may be composite "T1059.003;T1574.001"
    return max(ORDER[t] for p in label.split(";") for t in TACTICS[p.strip()])

M = json.load(open(MODEL)); alpha, vocab, glob = M["alpha"], M["vocab"], M["global_frequency"]
V = len(vocab)
def dist(state):
    c = M["counts"].get(state) or glob
    tot = sum(c.values())
    return {v: (c.get(v, 0) + alpha) / (tot + alpha * V) for v in vocab}, bool(M["counts"].get(state))
def escalation(state):
    d, seen = dist(state); r0 = rank(state)
    return sum(p for v, p in d.items() if rank(v) > r0), seen

for t in set(vocab) | set(M["counts"]):                      # fail loudly on any unmapped technique
    rank(t)

B = pd.read_csv(B_CSV, low_memory=False)
B["src"] = B.source_dataset.str.split(":").str[0]
B = B.dropna(subset=["current_mitre_id","next_mitre_technique"])
te = B[B.split_assignment == "test"].copy()
tv = B[B.split_assignment.isin(["train","validation"])]
te["escalation_probability"], te["state_seen_in_training"] = zip(*[escalation(s) for s in te.current_mitre_id])
te["actual_escalation"] = [int(rank(n) > rank(c)) for c, n in zip(te.current_mitre_id, te.next_mitre_technique)]
base = float(np.mean([rank(n) > rank(c) for c, n in zip(tv.current_mitre_id, tv.next_mitre_technique)]))   # constant baseline from train+val

def report(d):
    y, p = d.actual_escalation.values, d.escalation_probability.values
    bins = np.clip((p * 10).astype(int), 0, 9)
    ece = float(sum((bins == b).mean() * abs(y[bins == b].mean() - p[bins == b].mean()) for b in range(10) if (bins == b).any()))
    r = {"n": int(len(d)), "actual_escalation_rate": float(y.mean()), "mean_predicted": float(p.mean()),
         "brier": float(brier_score_loss(y, p)), "brier_constant_baseline": float(brier_score_loss(y, np.full(len(y), base))), "ece": ece}
    r["auc"] = float(roc_auc_score(y, p)) if len(set(y)) == 2 else None
    return r
res = {"constant_baseline_rate_train_val": base,
       "tactic_map_used": {k: v for k, v in TACTICS.items()},
       "test_all": report(te), "test_by_source": {s: report(d) for s, d in te.groupby("src")}}

# per-scenario Windows-APT
w = te[te.src == "Windows-APT-2025"]
res["windows_apt_per_scenario"] = {s: report(d) for s, d in w.groupby("scenario_id")}

# handoff file to C3 (C2's own output): per event, top-3 next techniques with probabilities + escalation probability
rows = []
for r in te.itertuples():
    d, seen = dist(r.current_mitre_id)
    top = sorted(d.items(), key=lambda kv: (-kv[1], vocab.index(kv[0])))[:3]
    row = {"source_record_id": r.source_record_id, "scenario_id": r.scenario_id, "session_id": r.session_id, "timestamp": r.timestamp_normalized,
           "current_technique": r.current_mitre_id, "current_tactic_rank": rank(r.current_mitre_id),
           "escalation_probability": round(r.escalation_probability, 4), "state_seen_in_training": seen}
    for k, (n, p) in enumerate(top, 1):
        row[f"next_{k}"], row[f"next_{k}_prob"] = n, round(p, 4)
    rows.append(row)
pd.DataFrame(rows).to_csv(f"{OUT}/c2_output_for_c3.csv", index=False)
json.dump(rows[:50], open(f"{OUT}/c2_output_for_c3_sample.json", "w"), indent=1)
json.dump(res, open(f"{OUT}/stage3_escalation_metrics.json", "w"), indent=1)
print(json.dumps({k: res[k] for k in ("constant_baseline_rate_train_val","test_all","test_by_source")}, indent=1))
