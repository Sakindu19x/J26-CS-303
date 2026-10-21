#!/usr/bin/env python3
"""
C2 Stage 1 - ATT&CK technique classification of single events (Task A).

Data   : APT_C2_Detection_Dataset/task_A_event_classification.csv
Target : technique ID for malicious events, "BENIGN" for benign events
         (60 malicious rows with no technique in the source are excluded from the multiclass task)
Split  : the dataset's own scenario-level split. Model selection = GroupKFold by scenario on
         train+validation; the test split is touched once, after the choice is made.
Models : majority-class baseline, Random Forest (main), HistGradientBoosting (comparison)
"""
import sys, json, warnings
import numpy as np, pandas as pd, joblib
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, precision_recall_fscore_support, f1_score,
                             confusion_matrix, roc_auc_score, brier_score_loss)
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
warnings.filterwarnings("ignore")

SRC, OUT = sys.argv[1], sys.argv[2]
SEED = 42

# ----------------------------------------------------------------------------- data
D = pd.read_csv(SRC, low_memory=False)
D["technique"] = np.where(D.malicious_benign_label == 1, D.current_mitre_id_label, "BENIGN")
D["source"] = D.source_dataset.str.split(":").str[0]
n_no_tech = int(D.technique.isna().sum())
D_bin = D.copy()                                   # keeps every row, used only for the binary view
D = D[D.technique.notna()].reset_index(drop=True)  # multiclass task
print(f"rows {len(D_bin)} | multiclass rows {len(D)} | malicious without technique (excluded): {n_no_tech}")

CAT = ["image_basename", "parent_image_basename", "event_id", "dest_port_category", "network_protocol_clean"]
CORE_NUM = ["image_dir_depth", "image_is_system32", "image_is_syswow64", "image_is_temp", "image_is_appdata",
            "image_is_windows", "cmd_length", "cmd_has_encoded", "cmd_has_noprofile", "cmd_has_bypass",
            "cmd_has_hidden", "cmd_has_iex", "cmd_has_download", "cmd_arg_count", "is_system_user",
            "has_network_info", "dest_port_num", "is_private_dest_ip", "has_dns", "dns_query_len",
            "dns_label_count", "src_port_is_ephemeral", "is_loopback_dest"]
TIME_NUM = ["hour_of_day", "day_of_week", "time_since_previous_event", "sequence_position"]
TEXT = "command_line"
# deliberately NOT used: scenario/session/source ids, raw IPs, raw source port, raw user, full paths,
# network_category, label_justification, verified_source_mitre_id, proposed_relabel, relabel_reason, any label column

FEATURE_SETS = {
    "core":            dict(num=CORE_NUM,            text=False),
    "core+time":       dict(num=CORE_NUM + TIME_NUM, text=False),
    "core+cmdtokens":  dict(num=CORE_NUM,            text=True),
    "all":             dict(num=CORE_NUM + TIME_NUM, text=True),
}

def make_X(df):
    X = df[CAT + CORE_NUM + TIME_NUM].copy()
    for c in CAT:
        X[c] = X[c].astype("string").fillna("none").astype(str)
    X[TEXT] = df[TEXT].fillna("").astype(str)
    return X

def make_pipe(fs, model):
    spec = FEATURE_SETS[fs]
    parts = [("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=10, sparse_output=False), CAT),
             ("num", SimpleImputer(strategy="constant", fill_value=-1), spec["num"])]
    if spec["text"]:
        parts.append(("txt", TfidfVectorizer(lowercase=True, token_pattern=r"[A-Za-z][A-Za-z0-9_\-\.]{1,}",
                                             min_df=10, max_features=150, binary=True), TEXT))
    return Pipeline([("pre", ColumnTransformer(parts)), ("clf", model)])

def rf():  return RandomForestClassifier(n_estimators=300, min_samples_leaf=2, class_weight="balanced_subsample",
                                         n_jobs=-1, random_state=SEED)
def hgb(): return HistGradientBoostingClassifier(max_iter=150, learning_rate=0.1, class_weight="balanced", random_state=SEED)
def maj(): return DummyClassifier(strategy="most_frequent")

def scores(y_true, y_pred):
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return dict(accuracy=accuracy_score(y_true, y_pred), macro_precision=p, macro_recall=r, macro_f1=f,
                weighted_f1=f1_score(y_true, y_pred, average="weighted", zero_division=0))

def top_k(pipe, X, y_true, k):
    pr = pipe.predict_proba(X); cls = pipe.classes_
    top = cls[np.argsort(-pr, axis=1)[:, :k]]
    return float(np.mean([t in row for t, row in zip(y_true, top)]))

# ----------------------------------------------------------------------------- split
tv = D[D.split_assignment.isin(["train", "validation"])].reset_index(drop=True)
te = D[D.split_assignment == "test"].reset_index(drop=True)
Xtv, ytv, gtv = make_X(tv), tv.technique.values, tv.scenario_id.values
Xte, yte = make_X(te), te.technique.values
print(f"train+val {len(tv)} rows / {tv.scenario_id.nunique()} scenarios | test {len(te)} rows / {te.scenario_id.nunique()} scenarios")

# ----------------------------------------------------------------------------- model selection (grouped CV)
cv_rows = []
gkf = GroupKFold(n_splits=5)
for fs in FEATURE_SETS:
    for name, mk in (("majority", maj), ("random_forest", rf), ("hist_gradient_boosting", hgb)):
        if name == "majority" and fs != "core":
            continue
        fold = []
        for tr, va in gkf.split(Xtv, ytv, gtv):
            assert not set(gtv[tr]) & set(gtv[va])
            m = make_pipe(fs, mk()).fit(Xtv.iloc[tr], ytv[tr])
            fold.append(scores(ytv[va], m.predict(Xtv.iloc[va])))
        agg = {k: float(np.mean([f[k] for f in fold])) for k in fold[0]}
        agg["macro_f1_std"] = float(np.std([f["macro_f1"] for f in fold]))
        cv_rows.append(dict(feature_set=fs if name != "majority" else "-", model=name, **agg))
        print(f"CV  {fs:15s} {name:24s} acc {agg['accuracy']:.3f}  macroF1 {agg['macro_f1']:.3f} (+/-{agg['macro_f1_std']:.3f})  wF1 {agg['weighted_f1']:.3f}")
cv = pd.DataFrame(cv_rows)
best = cv[cv.model == "random_forest"].sort_values("macro_f1", ascending=False).iloc[0]
BEST_FS = best.feature_set
print("selected feature set (RF, by grouped-CV macro-F1):", BEST_FS)

# ----------------------------------------------------------------------------- final fit + single test evaluation
final = make_pipe(BEST_FS, rf()).fit(Xtv, ytv)
base = make_pipe("core", maj()).fit(Xtv, ytv)
hg = make_pipe(BEST_FS, hgb()).fit(Xtv, ytv)
pred, bpred, hpred = final.predict(Xte), base.predict(Xte), hg.predict(Xte)
proba = final.predict_proba(Xte); cls = final.classes_

seen = np.isin(yte, cls)
res = {"n_train_val": len(tv), "n_test": len(te), "selected_feature_set": BEST_FS,
       "malicious_rows_without_technique_excluded": n_no_tech,
       "classes_in_training": list(cls),
       "test_classes_never_seen_in_training": sorted(set(yte) - set(cls)),
       "share_test_rows_with_unseen_class": float(1 - seen.mean())}
res["test_overall"] = {"random_forest": scores(yte, pred), "hist_gradient_boosting": scores(yte, hpred),
                       "majority_baseline": scores(yte, bpred)}
res["test_overall"]["random_forest"].update(top3_accuracy=top_k(final, Xte, yte, 3), top1_accuracy=float((pred == yte).mean()))
res["test_overall"]["hist_gradient_boosting"]["top3_accuracy"] = top_k(hg, Xte, yte, 3)
res["test_seen_classes_only"] = {"n": int(seen.sum()), "random_forest": scores(yte[seen], pred[seen]),
                                 "majority_baseline": scores(yte[seen], bpred[seen]),
                                 "rf_top3_accuracy": top_k(final, Xte[seen], yte[seen], 3)}
res["by_source"] = {}
for s in te.source.unique():
    m_ = (te.source == s).values
    res["by_source"][s] = {"n": int(m_.sum()), "random_forest": scores(yte[m_], pred[m_]),
                           "majority_baseline": scores(yte[m_], bpred[m_]),
                           "rf_top3_accuracy": top_k(final, Xte[m_], yte[m_], 3)}
net = (te.has_network_info == 1).values
res["network_events_only"] = {"n": int(net.sum()), "random_forest": scores(yte[net], pred[net]),
                              "majority_baseline": scores(yte[net], bpred[net]),
                              "classes_present": sorted(set(yte[net]))}

# binary detection view (malicious vs benign) from the same multiclass model: P(malicious) = 1 - P(BENIGN)
ib = list(cls).index("BENIGN")
p_mal = 1 - proba[:, ib]; y_mal = (yte != "BENIGN").astype(int)
bins = np.linspace(0, 1, 11); idx = np.clip(np.digitize(p_mal, bins) - 1, 0, 9)
ece = float(sum((idx == b).mean() * abs(y_mal[idx == b].mean() - p_mal[idx == b].mean()) for b in range(10) if (idx == b).any()))
pb, rb, fb, _ = precision_recall_fscore_support(y_mal, (p_mal >= 0.5).astype(int), average="binary", zero_division=0)
res["binary_detection_test"] = {"precision": pb, "recall": rb, "f1": fb, "roc_auc": float(roc_auc_score(y_mal, p_mal)),
                                "brier": float(brier_score_loss(y_mal, p_mal)), "ece_10bins": ece,
                                "accuracy": float(accuracy_score(y_mal, (p_mal >= 0.5).astype(int)))}
res["binary_detection_by_source"] = {}
for s in te.source.unique():
    m_ = (te.source == s).values
    p1, r1, f1_, _ = precision_recall_fscore_support(y_mal[m_], (p_mal[m_] >= 0.5).astype(int), average="binary", zero_division=0)
    res["binary_detection_by_source"][s] = {"n": int(m_.sum()), "precision": p1, "recall": r1, "f1": f1_}

# ----------------------------------------------------------------------------- artefacts
labels = sorted(set(yte) | set(pred))
pd.DataFrame(confusion_matrix(yte, pred, labels=labels), index=[f"true:{l}" for l in labels],
             columns=[f"pred:{l}" for l in labels]).to_csv(f"{OUT}/stage1_confusion_matrix.csv")
p, r, f, s = precision_recall_fscore_support(yte, pred, labels=labels, zero_division=0)
pd.DataFrame(dict(class_=labels, precision=p, recall=r, f1=f, support=s,
                  seen_in_training=[l in set(cls) for l in labels])).to_csv(f"{OUT}/stage1_per_class_report.csv", index=False)

order = np.argsort(-proba, axis=1)[:, :3]
pred_df = pd.DataFrame({"source_record_id": te.source_record_id, "scenario_id": te.scenario_id, "source": te.source,
                        "true_label": yte, "predicted": pred, "p_malicious": np.round(p_mal, 4)})
for k in range(3):
    pred_df[f"top{k+1}"] = cls[order[:, k]]
    pred_df[f"top{k+1}_prob"] = np.round(proba[np.arange(len(te)), order[:, k]], 4)
pred_df.to_csv(f"{OUT}/stage1_test_predictions.csv", index=False)

pi = permutation_importance(final, Xte, yte, scoring="f1_macro", n_repeats=5, random_state=SEED, n_jobs=1)
imp = pd.DataFrame({"feature": Xte.columns, "perm_importance_macro_f1": pi.importances_mean,
                    "std": pi.importances_std}).sort_values("perm_importance_macro_f1", ascending=False)
imp.to_csv(f"{OUT}/stage1_feature_importance.csv", index=False)
cv.to_csv(f"{OUT}/stage1_cv_model_selection.csv", index=False)
res["top_features_permutation"] = {r_.feature: round(float(r_.perm_importance_macro_f1), 4) for r_ in imp.head(10).itertuples()}
json.dump(res, open(f"{OUT}/stage1_metrics.json", "w"), indent=1, default=float)
joblib.dump({"pipeline": final, "feature_set": BEST_FS, "classes": list(cls)}, f"{OUT}/stage1_model.joblib")

print("\n=== TEST (RF vs majority) ===")
print(json.dumps({k: res[k] for k in ("test_overall", "test_seen_classes_only", "by_source", "network_events_only",
                                       "binary_detection_test", "binary_detection_by_source",
                                       "test_classes_never_seen_in_training", "share_test_rows_with_unseen_class",
                                       "top_features_permutation")}, indent=1, default=float))
