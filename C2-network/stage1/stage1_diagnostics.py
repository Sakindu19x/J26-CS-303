#!/usr/bin/env python3
"""Diagnostics for Stage 1: why is Windows-APT scored 100%, and what happens on the OTRF holdout?"""
import sys, json, warnings
import numpy as np, pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
warnings.filterwarnings("ignore")

SRC, OUT = sys.argv[1], sys.argv[2]
D = pd.read_csv(SRC, low_memory=False)
D["technique"] = np.where(D.malicious_benign_label == 1, D.current_mitre_id_label, "BENIGN")
D["source"] = D.source_dataset.str.split(":").str[0]
D = D[D.technique.notna()].reset_index(drop=True)
for c in ["image_basename", "parent_image_basename", "event_id", "dest_port_category", "network_protocol_clean"]:
    D[c] = D[c].astype("string").fillna("none").astype(str)
tv = D[D.split_assignment.isin(["train", "validation"])].reset_index(drop=True)
te = D[D.split_assignment == "test"].reset_index(drop=True)
res = {}

# 1) how deterministic is the label given process identity alone? (Windows-APT rows only)
w = tv[tv.source == "Windows-APT-2025"]
sig = ["event_id", "image_basename", "parent_image_basename"]
g = w.groupby(sig).technique.agg(["nunique", "size"])
res["signature_event_process_parent"] = {
    "distinct_signatures": int(len(g)),
    "share_of_rows_whose_signature_has_one_label": float(g[g["nunique"] == 1]["size"].sum() / g["size"].sum())}

# 2) lookup table: majority label per signature, learned on train+val, applied to Windows-APT test rows
table = w.groupby(sig).technique.agg(lambda s: s.value_counts().index[0])
wt = te[te.source == "Windows-APT-2025"].copy()
key = list(zip(wt.event_id, wt.image_basename, wt.parent_image_basename))
lk = pd.Series([table.get(k, "BENIGN") for k in key], index=wt.index)
res["lookup_table_on_windows_apt_test"] = {"n": int(len(wt)), "accuracy": float(accuracy_score(wt.technique, lk)),
                                           "signatures_unseen_in_training": float(np.mean([k not in table.index for k in key]))}

# 3) ablation: remove process identity (image/parent names) and event id, keep behaviour + network flags
CAT_ALL = ["image_basename", "parent_image_basename", "event_id", "dest_port_category", "network_protocol_clean"]
NUM = ["image_dir_depth", "image_is_system32", "image_is_syswow64", "image_is_temp", "image_is_appdata", "image_is_windows",
       "cmd_length", "cmd_has_encoded", "cmd_has_noprofile", "cmd_has_bypass", "cmd_has_hidden", "cmd_has_iex",
       "cmd_has_download", "cmd_arg_count", "is_system_user", "has_network_info", "dest_port_num", "is_private_dest_ip",
       "has_dns", "dns_query_len", "dns_label_count", "src_port_is_ephemeral", "is_loopback_dest"]

def pipe(cat):
    pre = ColumnTransformer([("c", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10, sparse_output=False), cat),
                             ("n", SimpleImputer(strategy="constant", fill_value=-1), NUM)])
    return Pipeline([("pre", pre), ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=2,
                                                                  class_weight="balanced_subsample", n_jobs=-1, random_state=42))])

variants = {"full_core": CAT_ALL,
            "no_process_names": ["event_id", "dest_port_category", "network_protocol_clean"],
            "no_process_names_no_event_id": ["dest_port_category", "network_protocol_clean"]}
res["ablation"] = {}
for name, cat in variants.items():
    X_tv, X_te = tv[cat + NUM], te[cat + NUM]
    f1s, accs = [], []
    for tr, va in GroupKFold(5).split(X_tv, tv.technique, tv.scenario_id):
        m = pipe(cat).fit(X_tv.iloc[tr], tv.technique.iloc[tr]); p = m.predict(X_tv.iloc[va])
        f1s.append(f1_score(tv.technique.iloc[va], p, average="macro", zero_division=0)); accs.append(accuracy_score(tv.technique.iloc[va], p))
    m = pipe(cat).fit(X_tv, tv.technique); p = m.predict(X_te)
    out = {"cv_macro_f1": float(np.mean(f1s)), "cv_accuracy": float(np.mean(accs))}
    for s in ("Windows-APT-2025", "OTRF"):
        k = (te.source == s).values
        out[f"test_{s}_accuracy"] = float(accuracy_score(te.technique[k], p[k]))
        out[f"test_{s}_macro_f1"] = float(f1_score(te.technique[k], p[k], average="macro", zero_division=0))
    res["ablation"][name] = out
    print(name, json.dumps(out))

# 4) OTRF holdout: what does the full model predict for the malicious events?
m = pipe(CAT_ALL).fit(tv[CAT_ALL + NUM], tv.technique)
o = te[te.source == "OTRF"].copy(); o["pred"] = m.predict(o[CAT_ALL + NUM])
res["otrf_malicious_true_vs_pred"] = pd.crosstab(o[o.technique != "BENIGN"].technique, o[o.technique != "BENIGN"].pred).to_dict()
res["otrf_benign_flagged_as_attack"] = int(((o.technique == "BENIGN") & (o.pred != "BENIGN")).sum())
res["otrf_benign_total"] = int((o.technique == "BENIGN").sum())
# network-only slice by source
nt = te[te.has_network_info == 1].copy(); nt["pred"] = m.predict(nt[CAT_ALL + NUM])
res["network_only_by_source"] = {s: {"n": int(len(d)), "accuracy": float(accuracy_score(d.technique, d.pred)),
                                     "majority_accuracy": float((d.technique == d.technique.value_counts().index[0]).mean()),
                                     "classes": d.technique.value_counts().to_dict()}
                                 for s, d in nt.groupby("source")}
json.dump(res, open(f"{OUT}/stage1_diagnostics.json", "w"), indent=1)
print(json.dumps({k: res[k] for k in res if k != "ablation"}, indent=1))
