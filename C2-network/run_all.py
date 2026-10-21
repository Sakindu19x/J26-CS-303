#!/usr/bin/env python3
"""
C2 run_all: reproduce the whole Component 2 chain from the dataset, audit it, and write the report tables and the C3 interface note.

Usage: python run_all.py <root_folder> <new_output_folder>
  root_folder must contain APT_C2_Detection_Dataset/ (task_A_event_classification.csv, task_B_next_technique.csv) and the C2 scripts
  (found by file name anywhere under root_folder; each is checked against the md5 of the audited version).
  new_output_folder must NOT exist yet.  Uses the current Python (run it with the project venv).  No input file is modified.
Outputs in <new_output_folder>: stage1/ stage2/ stage3/ pipeline/ sensitivity/ rerun/ logs/ report/AUDIT_REPORT.md report/audit.json
  report/report_tables.md report/C3_INTERFACE.md MANIFEST.sha256
"""
import sys, os, json, hashlib, subprocess, time, shutil, platform
import numpy as np, pandas as pd

ROOT, OUT = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
assert not os.path.exists(OUT), "output folder already exists - give a NEW folder name: " + OUT
DS = os.path.join(ROOT, "APT_C2_Detection_Dataset")
TASK_A, TASK_B = os.path.join(DS, "task_A_event_classification.csv"), os.path.join(DS, "task_B_next_technique.csv")
SCRIPT_MD5 = {"stage1_task_a.py": "7daddca138413aa27343a3a5d95e8cfa", "stage1_diagnostics.py": "9885be0a59db11f1ea0d64ad32899739",
              "stage1_shap.py": "9101cd15a3a26dcb5ca8a159bf59f0cf", "stage1_sensitivity.py": "6e3ec3a1e29d24c56e6d849f0cd7688f",
              "stage2_markov.py": "09581024f967c6ca2b672e7704055f58", "stage3_escalation.py": "d222e310025f59e19a0ca7bf0ff5183d",
              "c2_pipeline.py": "4507578b685ad16251e145857fcfee55"}
def md5(p): return hashlib.md5(open(p, "rb").read().replace(b"\r\n", b"\n").rstrip()).hexdigest()   # line-ending / trailing-newline tolerant
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()
checks, findings, timings = [], [], {}
def check(cid, name, ok, detail=""): checks.append({"id": cid, "check": name, "result": "PASS" if ok else "FAIL", "detail": str(detail)}); print(("PASS " if ok else "FAIL ") + cid + " " + name + " " + str(detail)[:160], flush=True)

# ---------------------------------------------------------------- locate scripts, verify md5
found = {}
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in (".venv", "venv", "__pycache__", "node_modules", ".git")]
    for f in fn:
        if f in SCRIPT_MD5:
            p = os.path.join(dp, f)
            if md5(p) == SCRIPT_MD5[f] and f not in found: found[f] = p
missing = sorted(set(SCRIPT_MD5) - set(found))
if missing:
    print("ABORT: audited version not found for:", missing); sys.exit(2)
check("A1", "all 7 scripts present with the audited md5", True, {k: os.path.relpath(v, ROOT) for k, v in found.items()})
in_hash = {p: sha(p) for p in (TASK_A, TASK_B)}
os.makedirs(OUT)
for d in ("stage1", "stage2", "stage3", "pipeline", "sensitivity", "rerun", "logs", "report"): os.makedirs(os.path.join(OUT, d))
P = lambda *a: os.path.join(OUT, *a)

def run(step, script, args):
    t = time.time(); r = subprocess.run([sys.executable, found[script]] + args, capture_output=True, text=True)
    timings[step] = round(time.time() - t, 1)
    open(P("logs", step + ".log"), "w", encoding="utf-8").write(r.stdout + "\n--- stderr ---\n" + r.stderr)
    print(f"[{step}] exit {r.returncode} in {timings[step]}s", flush=True)
    if r.returncode != 0:
        print(r.stderr[-1500:]); check("RUN", step + " exited 0", False, r.stderr[-300:]); finish(); sys.exit(1)

def finish():
    pass

# ---------------------------------------------------------------- run the chain
run("1_stage1", "stage1_task_a.py", [TASK_A, P("stage1")])
run("2_stage1_diagnostics", "stage1_diagnostics.py", [TASK_A, P("stage1")])
run("3_stage1_shap", "stage1_shap.py", [TASK_A, P("stage1")])
run("4_sensitivity", "stage1_sensitivity.py", [TASK_A, P("sensitivity")])
run("5_stage2", "stage2_markov.py", [TASK_B, P("stage1", "stage1_test_predictions.csv"), P("stage2")])
run("6_stage3", "stage3_escalation.py", [TASK_B, P("stage2", "stage2_model.json"), P("stage3")])
run("7_pipeline", "c2_pipeline.py", [TASK_B, P("stage1", "stage1_test_predictions_shap.csv"), P("stage2", "stage2_model.json"), P("stage3", "c2_output_for_c3.csv"), P("pipeline")])
check("A2", "every step exited 0", True, timings)

# ---------------------------------------------------------------- determinism: rerun stage 2, 3, pipeline
os.makedirs(P("rerun", "stage2")); os.makedirs(P("rerun", "stage3")); os.makedirs(P("rerun", "pipeline"))
run("8_rerun_stage2", "stage2_markov.py", [TASK_B, P("stage1", "stage1_test_predictions.csv"), P("rerun", "stage2")])
run("9_rerun_stage3", "stage3_escalation.py", [TASK_B, P("rerun", "stage2", "stage2_model.json"), P("rerun", "stage3")])
run("10_rerun_pipeline", "c2_pipeline.py", [TASK_B, P("stage1", "stage1_test_predictions_shap.csv"), P("rerun", "stage2", "stage2_model.json"), P("rerun", "stage3", "c2_output_for_c3.csv"), P("rerun", "pipeline")])
diff = [f for sub in ("stage2", "stage3", "pipeline") for f in os.listdir(P(sub)) if os.path.isfile(P("rerun", sub, f)) and sha(P(sub, f)) != sha(P("rerun", sub, f))]
check("A3", "re-running stage 2, stage 3 and the pipeline gives byte-identical outputs (NFR-03)", not diff, diff)

# ---------------------------------------------------------------- integrity of inputs (NFR-07)
check("A4", "input data files unchanged by the run (NFR-07)", all(sha(p) == h for p, h in in_hash.items()), "task_A, task_B sha256 compared before/after")

# ---------------------------------------------------------------- split / leakage checks
for name, path in (("task A", TASK_A), ("task B", TASK_B)):
    d = pd.read_csv(path, usecols=["scenario_id", "split_assignment"], low_memory=False)
    n = int((d.groupby("scenario_id").split_assignment.nunique() > 1).sum())
    check("A5", f"{name}: no scenario appears in more than one split", n == 0, f"{d.scenario_id.nunique()} scenarios, overlap={n}")
import joblib
art = joblib.load(P("stage1", "stage1_model.joblib")); pipe = art["pipeline"]
names = [n.split("__", 1)[1] for n in pipe.named_steps["pre"].get_feature_names_out()]
ALLOWED = ["image_basename", "parent_image_basename", "event_id", "dest_port_category", "network_protocol_clean", "image_dir_depth", "image_is_system32",
           "image_is_syswow64", "image_is_temp", "image_is_appdata", "image_is_windows", "cmd_length", "cmd_has_encoded", "cmd_has_noprofile",
           "cmd_has_bypass", "cmd_has_hidden", "cmd_has_iex", "cmd_has_download", "cmd_arg_count", "is_system_user", "has_network_info", "dest_port_num",
           "is_private_dest_ip", "has_dns", "dns_query_len", "dns_label_count", "src_port_is_ephemeral", "is_loopback_dest"]
bad = [n for n in names if not any(n == a or n.startswith(a + "_") for a in ALLOWED)]
check("A6", "Stage 1 model uses only allowed behavioural features (no scenario/session/source/label/raw-IP columns)", not bad, f"{len(names)} features; unexpected={bad[:10]}; feature_set={art.get('feature_set')}")

# ---------------------------------------------------------------- expected metrics (values from the audited runs)
def get(d, k):
    for p in k.split("."): d = d[p]
    return d
S1, S2, S3 = (json.load(open(P(*p))) for p in (("stage1", "stage1_metrics.json"), ("stage2", "stage2_metrics.json"), ("stage3", "stage3_escalation_metrics.json")))
PC = json.load(open(P("pipeline", "c2_pipeline_check.json")))
EXP = [("S1", S1, "test_overall.random_forest.accuracy", 0.93929, 0.005), ("S1", S1, "test_overall.random_forest.macro_f1", 0.71772, 0.005),
       ("S1", S1, "by_source.Windows-APT-2025.random_forest.accuracy", 1.0, 0.005), ("S1", S1, "by_source.OTRF.random_forest.accuracy", 0.88, 0.005),
       ("S1", S1, "by_source.OTRF.majority_baseline.accuracy", 0.89333, 0.005),
       ("S2", S2, "selected_alpha", 1.0, 1e-9), ("S2", S2, "test_by_source.Windows-APT-2025.markov.top1", 0.4648370497427101, 1e-9),
       ("S2", S2, "test_by_source.Windows-APT-2025.markov.top3", 0.8970840480274442, 1e-9),
       ("S2", S2, "test_by_source.Windows-APT-2025.frequency_baseline.top1", 0.29588336192109777, 1e-9),
       ("S2", S2, "test_by_source.Windows-APT-2025.frequency_baseline.top3", 0.7590051457975986, 1e-9),
       ("S3", S3, "test_all.auc", 0.9307431935246505, 1e-9), ("S3", S3, "test_by_source.Windows-APT-2025.auc", 0.9620792039357378, 1e-9),
       ("PIPE", PC, "events", 1278, 0), ("PIPE", PC, "detected", 1178, 0), ("PIPE", PC, "mismatches_with_stage3", 0, 0)]
for tag, d, k, e, tol in EXP:
    v = get(d, k); check("A7", f"{tag} {k} = {e}", abs(v - e) <= tol, f"got {v}")
sens = pd.read_csv(P("sensitivity", "stage1_sensitivity.csv"))
for exp, var, mod, e in (("A_train_WAPT_test_OTRF", "V_full", "rf", 0.678594), ("A_train_WAPT_test_OTRF", "V_full", "hgb", 0.770945),
                         ("A_train_WAPT_test_OTRF", "V_minimal", "hgb", 0.716207), ("B_leave_one_OTRF_capture_out", "V_full", "rf", 0.519881)):
    v = float(sens[(sens.experiment == exp) & (sens.variant == var) & (sens.model == mod)].auc.iloc[0]); check("A7", f"sensitivity {exp}/{var}/{mod} AUC = {e}", abs(v - e) <= 0.02, f"got {v:.6f}")

# ---------------------------------------------------------------- handoff file validity (FR-06, NFR-06)
c = pd.read_csv(P("pipeline", "c2_output.csv")); j = json.load(open(P("pipeline", "c2_output.json")))
det = c.detected_technique.notna()
ok = (len(c) == len(j) == 1278 and c.event_id.is_unique and (c.schema_version.astype(str) == "1.0").all())
check("A8", "handoff file: 1,278 unique events, CSV and JSON agree on count, schema_version 1.0", ok, f"csv={len(c)} json={len(j)}")
pcols = [x for x in c.columns if x.endswith("_prob") or x in ("classification_probability", "malicious_probability", "escalation_probability")]
check("A8", "all probabilities lie in [0,1]", all(c.loc[det, x].between(0, 1).all() for x in pcols), pcols)
check("A8", "next_1 >= next_2 >= next_3 and the three sum to <= 1", bool(((c.loc[det, "next_1_prob"] >= c.loc[det, "next_2_prob"]) & (c.loc[det, "next_2_prob"] >= c.loc[det, "next_3_prob"]) & (c.loc[det, ["next_1_prob", "next_2_prob", "next_3_prob"]].sum(axis=1) <= 1 + 1e-6)).all()))
check("A8", "undetected events have empty detection/prediction fields; detected events have all of them", bool(c.loc[~det, ["next_1", "escalation_probability", "classification_probability"]].isna().all().all() and c.loc[det, ["next_1", "next_2", "next_3", "escalation_probability", "classification_probability"]].notna().all().all()))
check("A8", "observed_sequence of a detected event ends with its detected technique", bool(all(s.split(" > ")[-1] == t for s, t in zip(c.loc[det, "observed_sequence"], c.loc[det, "detected_technique"]))))
mono = all(g.sequence_position.is_monotonic_increasing and pd.to_datetime(g.timestamp).is_monotonic_increasing for _, g in c.groupby("session_id"))
check("A8", "events are in time order within each session (FR-04)", mono)

# ---------------------------------------------------------------- findings (reported, not pass/fail)
pr = pd.read_csv(P("stage1", "stage1_test_predictions.csv"))
wb = int(((pr.source == "Windows-APT-2025") & (pr.true_label == "BENIGN")).sum()); ob = int(((pr.source == "OTRF") & (pr.true_label == "BENIGN")).sum())
findings += [f"Windows-APT test split contains {wb} benign rows (OTRF: {ob}); false-positive behaviour cannot be measured on Windows-APT.",
 f"Windows-APT Stage 1 accuracy {get(S1,'by_source.Windows-APT-2025.random_forest.accuracy'):.3f}: labels come from Wazuh rules, so this is rule re-learning, not detection capability.",
 f"OTRF Stage 1 accuracy {get(S1,'by_source.OTRF.random_forest.accuracy'):.3f} is BELOW the majority baseline {get(S1,'by_source.OTRF.majority_baseline.accuracy'):.3f}; end-to-end only {S2['end_to_end']['OTRF']['detected_by_stage1']} of {S2['end_to_end']['OTRF']['true_malicious_events']} OTRF malicious test events are flagged.",
 f"All-rows Stage 1 accuracy {get(S1,'test_overall.random_forest.accuracy'):.3f} mixes both sources and must not be the headline.",
 f"Test classes never seen in training: {S1['test_classes_never_seen_in_training']} ({S1['share_test_rows_with_unseen_class']:.3%} of test rows).",
 f"Stage 2 OTRF test: {S2['test_by_source']['OTRF']['state_unseen_in_training']:.1%} of states unseen in training; OTRF results there are not meaningful. All OTRF test transitions are self-transitions, so escalation has no positive cases there.",
 "Task A/B labels come from the dataset audit; tactic order (stage 3) is the official ATT&CK order with the 'latest tactic' rule for multi-tactic techniques (author's assumption).",
 "Stage 1 itself was not re-run twice here; its reproducibility rests on the two independent runs already compared (0 of 2,372 predictions differ).",
 "NFR-05 (scalability to additional records) was not tested."]

# ---------------------------------------------------------------- report tables
f3 = lambda x: f"{x:.3f}"
L = ["# C2 report tables (generated by run_all.py from this run's own metric files)\n"]
L += ["## Table 2 - Baseline / benchmark comparison (test split)\n", "| Task | Model | Baseline | Source | Model top-1 / accuracy | Baseline top-1 / accuracy | Model top-3 | Baseline top-3 |", "|---|---|---|---|---|---|---|---|"]
for s, k in (("Windows-APT-2025", "Windows-APT-2025"), ("OTRF", "OTRF")):
    r = S1["by_source"][k]; L.append(f"| ATT&CK classification | Random Forest | Majority class | {s} | {f3(r['random_forest']['accuracy'])} | {f3(r['majority_baseline']['accuracy'])} | {f3(r['rf_top3_accuracy'])} | n/a |")
for s in ("Windows-APT-2025", "OTRF"):
    r = S2["test_by_source"][s]; L.append(f"| Next-technique prediction | First-order Markov | Frequency | {s} | {f3(r['markov']['top1'])} | {f3(r['frequency_baseline']['top1'])} | {f3(r['markov']['top3'])} | {f3(r['frequency_baseline']['top3'])} |")
L.append("\nNote: the Windows-APT test split has no BENIGN rows, so the majority-class baseline (BENIGN) scores 0.000 there and is not a meaningful comparison. OTRF Stage 2 rows are not meaningful: 48% of states are unseen in training and every test transition is a self-transition.")
L += ["\n## Table 3 - ATT&CK classification metrics (Random Forest, test split; macro-averaged over the classes present)\n", "| Source | n | Accuracy | Precision | Recall | F1 | Majority accuracy | Majority macro-F1 |", "|---|---|---|---|---|---|---|---|"]
for s, r in (("Windows-APT-2025", S1["by_source"]["Windows-APT-2025"]), ("OTRF", S1["by_source"]["OTRF"]), ("All rows (do not use as headline)", S1["test_overall"])):
    n = r.get("n", S1["n_test"]); m = r["random_forest"]; b = r["majority_baseline"]
    L.append(f"| {s} | {n} | {f3(m['accuracy'])} | {f3(m['macro_precision'])} | {f3(m['macro_recall'])} | {f3(m['macro_f1'])} | {f3(b['accuracy'])} | {f3(b['macro_f1'])} |")
L.append("\nConfusion matrix and per-class report: stage1/stage1_confusion_matrix.csv, stage1/stage1_per_class_report.csv.\n")
w = S2["test_by_source"]["Windows-APT-2025"]; bt = S2["windows_apt_test_scenarios"]
L += ["## Table 4 - Escalation / next-technique prediction metrics (Windows-APT test, 6 scenarios)\n", "| Metric | Markov | Frequency baseline |", "|---|---|---|",
      f"| Top-1 accuracy | {f3(w['markov']['top1'])} | {f3(w['frequency_baseline']['top1'])} |", f"| Top-3 accuracy | {f3(w['markov']['top3'])} | {f3(w['frequency_baseline']['top3'])} |",
      f"| Log-loss | {f3(w['markov_log_loss'])} | {f3(w['frequency_log_loss'])} |", f"| Top-1 calibration error (ECE) | {f3(w['markov_top1_ece'])} | n/a |",
      f"\nBootstrap by scenario, Markov minus frequency: top-1 gain 95% CI {bt['bootstrap_top1']['difference_vs_frequency_95ci'][0]:.3f} to {bt['bootstrap_top1']['difference_vs_frequency_95ci'][1]:.3f}; top-3 gain 95% CI {bt['bootstrap_top3']['difference_vs_frequency_95ci'][0]:.3f} to {bt['bootstrap_top3']['difference_vs_frequency_95ci'][1]:.3f}.",
      f"Second-order Markov (comparison only): top-1 {f3(S2['second_order_comparison_windows_apt_test']['top1'])}, top-3 {f3(S2['second_order_comparison_windows_apt_test']['top3'])}.",
      f"\nDerived escalation probability (probability that the next technique belongs to a later ATT&CK tactic), Windows-APT test: AUC {f3(S3['test_by_source']['Windows-APT-2025']['auc'])}, Brier {f3(S3['test_by_source']['Windows-APT-2025']['brier'])} (constant baseline {f3(S3['test_by_source']['Windows-APT-2025']['brier_constant_baseline'])}), ECE {f3(S3['test_by_source']['Windows-APT-2025']['ece'])}."]
L += ["\n## Requirement traceability\n", "| ID | Requirement | Evidence | Status |", "|---|---|---|---|"]
tr = [("FR-01", "Ingest/preprocess Windows events", "Audited dataset, task_A/task_B", "Met (pre-processed dataset; raw ingest done upstream)"),
      ("FR-02", "Extract host and network features", "Feature set in stage1_task_a.py (A6)", "Met"),
      ("FR-03", "Map events to technique IDs with probabilities", "stage1_test_predictions.csv, c2_output.csv classification_probability", "Met; OTRF weak"),
      ("FR-04", "Order techniques chronologically into sequences", "observed_sequence, check A8", "Met"),
      ("FR-05", "Top-3 next techniques with probabilities", "next_1..3 and _prob, Table 4", "Met"),
      ("FR-06", "Structured JSON/CSV with IDs, sequence history, escalation", "pipeline/c2_output.json|csv, C3_INTERFACE.md", "Met; host = session_id"),
      ("NFR-01", "Explainability", "SHAP top-5 per event, transition counts", "Met"),
      ("NFR-02", "Practical run time", f"Step timings: {timings}", "Met on this machine"),
      ("NFR-03", "Consistent results", "check A3 (byte-identical reruns), fixed seed 42", "Met"),
      ("NFR-04", "Analyst-oriented format", "Flat CSV + nested JSON + C3_INTERFACE.md", "Partly (no GUI)"),
      ("NFR-05", "Scalability", "Not tested", "Not evidenced"),
      ("NFR-06", "Interoperability with C3", "check A8, schema_version 1.0", "Met on the C2 side; C3 acceptance not tested"),
      ("NFR-07", "Preserve integrity of source data", "check A4 (sha256 before/after)", "Met")]
L += [f"| {a} | {b} | {c_} | {d_} |" for a, b, c_, d_ in tr]
open(P("report", "report_tables.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ---------------------------------------------------------------- C3 interface note
ex = next(r for r in j if r["detection"]); ex = json.loads(json.dumps(ex)); ex["observed_sequence"] = ex["observed_sequence"][-3:]
I = f"""# C2 -> C3 interface (schema_version 1.0)

C2 delivers one record per event, ordered by session and time. Files: `c2_output.csv` (flat) and `c2_output.json` (nested). Keys are identical in both.

| Field | Type | Meaning |
|---|---|---|
| schema_version | string | Format version, currently "1.0" |
| event_id | string | Source record id of the event |
| scenario_id, session_id | string | Attack scenario and session. The dataset has no host column; `host_or_session` repeats `session_id` |
| source_dataset | string | Windows-APT-2025 or OTRF |
| timestamp, sequence_position | string, int | Event time and its position in the session |
| detected_technique | string or empty | MITRE ATT&CK technique ID predicted by Stage 1. Composite IDs such as `T1059.003;T1574.001` are one class. Empty = event not flagged |
| tactics | string | ATT&CK tactic(s) of the detected technique (`;`-separated in CSV) |
| classification_probability | 0-1 | Stage 1 probability of the predicted technique |
| malicious_probability | 0-1 | Stage 1 probability that the event is malicious |
| observed_sequence | string | Up to the last 10 detected techniques in the session, ` > `-separated, ending with this event's technique |
| next_1..next_3, next_k_prob | string, 0-1 | Top-3 next techniques from the first-order Markov model with transition probabilities |
| escalation_probability | 0-1 | Probability that the next technique belongs to a later ATT&CK tactic |
| state_seen_in_training | bool | False = no transition history for this technique; the prediction fell back to overall frequency |
| explanation_top5 / explanation_top_features | text / list | The five Stage 1 features with the largest SHAP value for the predicted technique |

Rules for C3: an event that is not flagged has empty detection and prediction fields - treat it as "no detection", not as zero. Probabilities are model scores; their calibration was only checked on Windows-APT. OTRF predictions are unreliable (see report) - filter on `source_dataset` if needed. Do not use `scenario_id` as a model input.

Example record (JSON, sequence shortened):

```json
{json.dumps(ex, indent=1)}
```
"""
open(P("report", "C3_INTERFACE.md"), "w", encoding="utf-8").write(I)

# ---------------------------------------------------------------- audit report, manifest
fails = [x for x in checks if x["result"] == "FAIL"]
A = ["# C2 audit report\n", f"Run: {time.strftime('%Y-%m-%d %H:%M:%S')} | Python {platform.python_version()} | pandas {pd.__version__} | numpy {np.__version__} | OS {platform.platform()}",
     f"\nResult: **{len(checks) - len(fails)} PASS, {len(fails)} FAIL**\n", "| ID | Check | Result | Detail |", "|---|---|---|---|"]
A += [f"| {x['id']} | {x['check']} | {x['result']} | {x['detail'][:140].replace('|', '/')} |" for x in checks]
A += ["\n## Findings to state honestly in the report and viva\n"] + [f"- {x}" for x in findings] + ["\n## Step timings (seconds)\n", json.dumps(timings)]
open(P("report", "AUDIT_REPORT.md"), "w", encoding="utf-8").write("\n".join(A) + "\n")
json.dump({"checks": checks, "findings": findings, "timings": timings}, open(P("report", "audit.json"), "w"), indent=1)
with open(P("MANIFEST.sha256"), "w") as m:
    for dp, dn, fn in os.walk(OUT):
        for f in sorted(fn):
            if f != "MANIFEST.sha256": m.write(f"{sha(os.path.join(dp, f))}  {os.path.relpath(os.path.join(dp, f), OUT)}\n")
print(f"\nDONE: {len(checks) - len(fails)} PASS, {len(fails)} FAIL. See {P('report', 'AUDIT_REPORT.md')}")
sys.exit(1 if fails else 0)
