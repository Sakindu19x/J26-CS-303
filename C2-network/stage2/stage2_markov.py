#!/usr/bin/env python3
"""
C2 Stage 2 - first-order Markov next-technique predictor (proposal Section 3.3, FR-04 / FR-05).

  P(Tj | Ti) = (N(Ti->Tj) + alpha) / (N(Ti) + alpha * V)      counts from TRAINING scenarios only
  unseen state Ti  ->  fall back to the global next-technique frequency distribution

Usage: python stage2_markov.py <task_B_next_technique.csv> <stage1_test_predictions.csv> <out_dir>
Needs only pandas + numpy. Seed 42. Does not modify any input.
"""
import sys, json
import numpy as np, pandas as pd
from collections import Counter, defaultdict

B_CSV, S1_CSV, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
SEED, EPS, ALPHAS = 42, 1e-6, [0.0, 0.01, 0.1, 1.0]
rng = np.random.default_rng(SEED)

# ------------------------------------------------------------------ data + sanity checks
B = pd.read_csv(B_CSV, low_memory=False)
B["src"] = B.source_dataset.str.split(":").str[0]
n0 = len(B)
B = B.dropna(subset=["current_mitre_id", "next_mitre_technique"]).sort_values(["session_id", "sequence_position"]).reset_index(drop=True)
B["ts"] = pd.to_datetime(B.timestamp_normalized, errors="coerce")
B["prev"] = B.groupby("session_id").current_mitre_id.shift(1).fillna("<START>")
chk = {"rows_in_file": n0, "rows_used": len(B), "scenarios": int(B.scenario_id.nunique()), "sessions": int(B.session_id.nunique()),
       "scenarios_in_more_than_one_split": int((B.groupby("scenario_id").split_assignment.nunique() > 1).sum()),
       "sessions_with_decreasing_timestamps": int((~B.groupby("session_id").ts.apply(lambda s: s.is_monotonic_increasing)).sum()),
       "states": int(B.current_mitre_id.nunique()), "next_classes": int(B.next_mitre_technique.nunique()),
       "self_transition_share": float((B.current_mitre_id == B.next_mitre_technique).mean()),
       "rows_by_split": B.split_assignment.value_counts().to_dict(), "scenarios_by_split": B.groupby("split_assignment").scenario_id.nunique().to_dict()}
assert chk["scenarios_in_more_than_one_split"] == 0
print(json.dumps(chk, indent=1))

tv = B[B.split_assignment.isin(["train", "validation"])]
te = B[B.split_assignment == "test"]

# ------------------------------------------------------------------ model
class Markov:
    def __init__(self, df, alpha):
        self.alpha = alpha
        self.cnt = defaultdict(Counter)
        for s, n in zip(df.current_mitre_id, df.next_mitre_technique):
            self.cnt[s][n] += 1
        self.freq = Counter(df.next_mitre_technique)
        self.vocab = sorted(self.freq, key=lambda c: (-self.freq[c], c))      # deterministic tie-break = global frequency
        self.V = len(self.vocab)
        self.o2 = defaultdict(Counter)
        for p, s, n in zip(df.prev, df.current_mitre_id, df.next_mitre_technique):
            self.o2[(p, s)][n] += 1

    def dist(self, state):
        c = self.cnt.get(state)
        base = c if c else self.freq
        tot = sum(base.values())
        pr = np.array([(base.get(v, 0) + self.alpha) / (tot + self.alpha * self.V) for v in self.vocab])
        return pr, bool(c), tot

    def top(self, state, k):
        pr, seen, tot = self.dist(state)
        order = sorted(range(self.V), key=lambda i: (-pr[i], i))[:k]
        return [(self.vocab[i], float(pr[i])) for i in order], seen, tot

    def top_o2(self, prev, state, k):
        c = self.o2.get((prev, state))
        if not c:
            return [t for t, _ in self.top(state, k)[0]]
        return [t for t, _ in sorted(c.items(), key=lambda kv: (-kv[1], self.vocab.index(kv[0]) if kv[0] in self.vocab else 10**6))[:k]]

def freq_top(model, k):
    return model.vocab[:k]

def evaluate(model, df, states=None):
    """Top-k accuracy, log-loss and top-1 calibration for the Markov model and the frequency baseline."""
    states = df.current_mitre_id.values if states is None else states
    y = df.next_mitre_technique.values
    out = {"markov_hit": {1: [], 3: [], 5: []}, "freq_hit": {1: [], 3: [], 5: []}}
    ll_m, ll_f, conf, correct, unseen = [], [], [], [], []
    idx = {v: i for i, v in enumerate(model.vocab)}
    ftot = sum(model.freq.values())
    for s, t in zip(states, y):
        top5, seen, _ = model.top(s, 5)
        names = [n for n, _ in top5]
        for k in (1, 3, 5):
            out["markov_hit"][k].append(t in names[:k]); out["freq_hit"][k].append(t in freq_top(model, k))
        pr, _, _ = model.dist(s)
        pm = pr[idx[t]] if t in idx else EPS
        pf = (model.freq.get(t, 0) + model.alpha) / (ftot + model.alpha * model.V) if t in idx else EPS
        ll_m.append(-np.log(max(pm, EPS))); ll_f.append(-np.log(max(pf, EPS)))
        conf.append(top5[0][1]); correct.append(names[0] == t); unseen.append(not seen)
    conf, correct = np.array(conf), np.array(correct)
    bins = np.clip((conf * 10).astype(int), 0, 9)
    ece = float(sum((bins == b).mean() * abs(correct[bins == b].mean() - conf[bins == b].mean()) for b in range(10) if (bins == b).any()))
    res = {"n": int(len(y)), "state_unseen_in_training": float(np.mean(unseen)), "target_unseen_in_training": float(np.mean([t not in idx for t in y])),
           "markov": {f"top{k}": float(np.mean(out["markov_hit"][k])) for k in (1, 3, 5)},
           "frequency_baseline": {f"top{k}": float(np.mean(out["freq_hit"][k])) for k in (1, 3, 5)},
           "repeat_current_top1": float(np.mean(np.array(states) == y)),
           "markov_log_loss": float(np.mean(ll_m)), "frequency_log_loss": float(np.mean(ll_f)), "markov_top1_ece": ece}
    return res

# ------------------------------------------------------------------ alpha selection: GroupKFold by scenario on train+val
scen = np.array(sorted(tv.scenario_id.unique().tolist()), dtype=object); rng.shuffle(scen)
folds = np.array_split(scen, 5)
assert sorted(np.concatenate(folds).tolist()) == sorted(scen.tolist()) and len(set(np.concatenate(folds).tolist())) == len(scen)  # every scenario in exactly one fold
cv = []
for a in ALPHAS:
    lls, t1s = [], []
    for f in folds:
        trn, val = tv[~tv.scenario_id.isin(f)], tv[tv.scenario_id.isin(f)]
        r = evaluate(Markov(trn, a), val); lls.append(r["markov_log_loss"]); t1s.append(r["markov"]["top1"])
    cv.append({"alpha": a, "cv_log_loss": float(np.mean(lls)), "cv_top1": float(np.mean(t1s))})
    print("CV", cv[-1])
ALPHA = min(cv, key=lambda r: r["cv_log_loss"])["alpha"]
print("selected alpha:", ALPHA)

# ------------------------------------------------------------------ final fit + single test evaluation
M = Markov(tv, ALPHA)
res = {"data_checks": chk, "alpha_cv": cv, "selected_alpha": ALPHA}
res["test_all_events"] = evaluate(M, te)
res["test_non_self_transitions"] = evaluate(M, te[te.current_mitre_id != te.next_mitre_technique])
res["test_by_source"] = {s: evaluate(M, d) for s, d in te.groupby("src")}
for s, d in te.groupby("src"):
    res["test_by_source"][s]["repeat_current_top1"] = float((d.current_mitre_id == d.next_mitre_technique).mean())

# second-order comparison (top-1 / top-3, back-off to first order)
w = te[te.src == "Windows-APT-2025"]
res["second_order_comparison_windows_apt_test"] = {f"top{k}": float(np.mean([t in M.top_o2(p, s, k) for p, s, t in zip(w.prev, w.current_mitre_id, w.next_mitre_technique)])) for k in (1, 3)}

# per-scenario + bootstrap-by-scenario (Windows-APT test scenarios)
per = []
for sc, d in w.groupby("scenario_id"):
    r = evaluate(M, d); per.append({"scenario_id": sc, "n": r["n"], "markov_top1": r["markov"]["top1"], "markov_top3": r["markov"]["top3"],
                                    "freq_top1": r["frequency_baseline"]["top1"], "freq_top3": r["frequency_baseline"]["top3"]})
per = pd.DataFrame(per); per.to_csv(f"{OUT}/stage2_per_scenario.csv", index=False)
def boot(col_m, col_f, B_=1000):
    d = []
    for _ in range(B_):
        s = per.sample(len(per), replace=True, random_state=int(rng.integers(1e9)))
        d.append((np.average(s[col_m], weights=s.n), np.average(s[col_f], weights=s.n)))
    d = np.array(d); diff = d[:, 0] - d[:, 1]
    return {"markov_95ci": [float(np.percentile(d[:, 0], 2.5)), float(np.percentile(d[:, 0], 97.5))],
            "difference_vs_frequency_95ci": [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]}
res["windows_apt_test_scenarios"] = {"n_scenarios": int(len(per)), "markov_top1_mean_std": [float(per.markov_top1.mean()), float(per.markov_top1.std())],
                                     "markov_top3_mean_std": [float(per.markov_top3.mean()), float(per.markov_top3.std())],
                                     "bootstrap_top1": boot("markov_top1", "freq_top1"), "bootstrap_top3": boot("markov_top3", "freq_top3")}

# supplementary: leave-one-scenario-out over ALL Windows-APT scenarios (uses test scenarios as training in other folds)
wa = B[B.src == "Windows-APT-2025"]; rows = []
for sc in wa.scenario_id.unique():
    r = evaluate(Markov(wa[wa.scenario_id != sc], ALPHA), wa[wa.scenario_id == sc])
    rows.append((r["n"], r["markov"]["top1"], r["markov"]["top3"], r["frequency_baseline"]["top1"], r["frequency_baseline"]["top3"]))
a_ = np.array(rows); wts = a_[:, 0]
res["supplementary_leave_one_scenario_out_windows_apt"] = {"n_scenarios": len(rows),
    "markov_top1_pooled": float(np.average(a_[:, 1], weights=wts)), "markov_top3_pooled": float(np.average(a_[:, 2], weights=wts)),
    "frequency_top1_pooled": float(np.average(a_[:, 3], weights=wts)), "frequency_top3_pooled": float(np.average(a_[:, 4], weights=wts)),
    "markov_top1_scenario_std": float(a_[:, 1].std()), "note": "supplementary only; not the headline test result"}

# ------------------------------------------------------------------ end-to-end: Stage 1 predicted state instead of the true state
S1 = pd.read_csv(S1_CSV, low_memory=False)[["source_record_id", "predicted", "p_malicious"]]
e = te.merge(S1, on="source_record_id", how="left")
res["end_to_end"] = {"test_rows": int(len(e)), "rows_without_stage1_prediction": int(e.predicted.isna().sum())}
e["state_e2e"] = np.where((e.p_malicious >= 0.5) & (e.predicted.notna()) & (e.predicted != "BENIGN"), e.predicted, "MISSED")
for name, d in [("all", e), ("Windows-APT-2025", e[e.src == "Windows-APT-2025"]), ("OTRF", e[e.src == "OTRF"])]:
    det = d[d.state_e2e != "MISSED"]
    r_det = evaluate(M, det, states=det.state_e2e.values) if len(det) else None
    r_orc = evaluate(M, d)
    hits = lambda k: sum(t in [n for n, _ in M.top(s, k)[0]] for s, t in zip(det.state_e2e, det.next_mitre_technique))
    res["end_to_end"][name] = {"true_malicious_events": int(len(d)), "detected_by_stage1": int(len(det)), "detection_coverage": float(len(det) / max(len(d), 1)),
        "top1_on_detected": r_det["markov"]["top1"] if r_det else None, "top3_on_detected": r_det["markov"]["top3"] if r_det else None,
        "top1_overall_missed_counted_wrong": float(hits(1) / max(len(d), 1)), "top3_overall_missed_counted_wrong": float(hits(3) / max(len(d), 1)),
        "oracle_top1": r_orc["markov"]["top1"], "oracle_top3": r_orc["markov"]["top3"]}

# ------------------------------------------------------------------ artefacts
states = sorted(set(B.current_mitre_id) | set(B.next_mitre_technique))
cnt = pd.DataFrame([{"from_state": s, "to_state": n, "count": c, "state_total": sum(M.cnt[s].values()), "probability_alpha0": c / sum(M.cnt[s].values())}
                    for s in sorted(M.cnt) for n, c in M.cnt[s].most_common()])
cnt.to_csv(f"{OUT}/stage2_transition_counts.csv", index=False)
pd.DataFrame([{"from_state": s, **{v: p for v, p in zip(M.vocab, M.dist(s)[0])}} for s in sorted(M.cnt)]).to_csv(f"{OUT}/stage2_transition_probs.csv", index=False)
rowsP = []
for r in e.itertuples():
    top, seen, tot = M.top(r.current_mitre_id, 5)
    d = {"source_record_id": r.source_record_id, "scenario_id": r.scenario_id, "source": r.src, "current_state": r.current_mitre_id, "true_next": r.next_mitre_technique,
         "state_seen_in_training": seen, "state_total": tot, "stage1_state": r.state_e2e}
    for k, (n, p) in enumerate(top, 1):
        d[f"top{k}"], d[f"top{k}_prob"], d[f"top{k}_count"] = n, round(p, 4), M.cnt.get(r.current_mitre_id, Counter()).get(n, 0)
    rowsP.append(d)
pd.DataFrame(rowsP).to_csv(f"{OUT}/stage2_predictions.csv", index=False)
json.dump({"alpha": ALPHA, "fallback": "global next-technique frequency", "vocab": M.vocab,
           "counts": {s: dict(c) for s, c in M.cnt.items()}, "global_frequency": dict(M.freq)}, open(f"{OUT}/stage2_model.json", "w"), indent=1)
json.dump(res, open(f"{OUT}/stage2_metrics.json", "w"), indent=1, default=float)

# calibration table (Windows-APT test, top-1 probability)
cal = []
for s, t in zip(w.current_mitre_id, w.next_mitre_technique):
    top, _, _ = M.top(s, 1); cal.append((top[0][1], top[0][0] == t))
cal = pd.DataFrame(cal, columns=["conf", "correct"]); cal["bin"] = pd.cut(cal.conf, np.linspace(0, 1, 11), include_lowest=True)
cal.groupby("bin", observed=True).agg(n=("correct", "size"), mean_confidence=("conf", "mean"), accuracy=("correct", "mean")).reset_index().to_csv(f"{OUT}/stage2_calibration.csv", index=False)

print("\n=== TEST ===")
print(json.dumps({k: res[k] for k in ("test_all_events", "test_non_self_transitions", "test_by_source", "second_order_comparison_windows_apt_test",
                                      "windows_apt_test_scenarios", "supplementary_leave_one_scenario_out_windows_apt", "end_to_end")}, indent=1, default=float))
