#!/usr/bin/env python3
"""
C2 Stage 1 - step C: SHAP top-5 features per test prediction.
Usage: python c2/stage1/stage1_shap.py <task_A_csv> <stage1_dir>
Loads the saved model (stage1_model.joblib) produced by reference/files/stage1_task_a.py and
explains the predicted class of every test row with shap.TreeExplainer.
Test rows/feature construction replicate stage1_task_a.py (make_X, multiclass filter, split == test).
Writes ONLY stage1_test_predictions_shap.csv (refuses to overwrite). Reads, never changes, other files.
"""
import sys, os
import numpy as np, pandas as pd, joblib, shap

SRC, OUT = sys.argv[1], sys.argv[2]
dst = os.path.join(OUT, "stage1_test_predictions_shap.csv")
assert not os.path.exists(dst), "refusing to overwrite " + dst

D = pd.read_csv(SRC, low_memory=False)
D["technique"] = np.where(D.malicious_benign_label == 1, D.current_mitre_id_label, "BENIGN")
D = D[D.technique.notna()].reset_index(drop=True)
te = D[D.split_assignment == "test"].reset_index(drop=True)

CAT = ["image_basename", "parent_image_basename", "event_id", "dest_port_category", "network_protocol_clean"]
CORE_NUM = ["image_dir_depth", "image_is_system32", "image_is_syswow64", "image_is_temp", "image_is_appdata",
            "image_is_windows", "cmd_length", "cmd_has_encoded", "cmd_has_noprofile", "cmd_has_bypass",
            "cmd_has_hidden", "cmd_has_iex", "cmd_has_download", "cmd_arg_count", "is_system_user",
            "has_network_info", "dest_port_num", "is_private_dest_ip", "has_dns", "dns_query_len",
            "dns_label_count", "src_port_is_ephemeral", "is_loopback_dest"]
TIME_NUM = ["hour_of_day", "day_of_week", "time_since_previous_event", "sequence_position"]
def make_X(df):
    X = df[CAT + CORE_NUM + TIME_NUM].copy()
    for c in CAT:
        X[c] = X[c].astype("string").fillna("none").astype(str)
    X["command_line"] = df["command_line"].fillna("").astype(str)
    return X

art = joblib.load(os.path.join(OUT, "stage1_model.joblib"))
pipe, cls = art["pipeline"], np.array(art["classes"])
Xte = make_X(te)

# consistency check against the saved predictions file (same rows, same predictions)
ref = pd.read_csv(os.path.join(OUT, "stage1_test_predictions.csv"))
assert len(ref) == len(te) and (ref.source_record_id.values == te.source_record_id.values).all(), "row mismatch"
pred = pipe.predict(Xte)
assert (pred == ref.predicted.values).all(), "saved model does not reproduce saved predictions"

Z = pipe.named_steps["pre"].transform(Xte)
names = pipe.named_steps["pre"].get_feature_names_out()
names = [n.split("__", 1)[1] for n in names]
rf = pipe.named_steps["clf"]
sv = shap.TreeExplainer(rf).shap_values(Z)
sv = np.stack(sv, axis=-1) if isinstance(sv, list) else np.asarray(sv)   # (n, features, classes)
assert sv.shape == (len(te), len(names), len(cls)), sv.shape

ci = np.array([list(cls).index(p) for p in pred])
rows = {}
for k in range(5):
    rows[f"shap_feat{k+1}"] = []; rows[f"shap_feat{k+1}_value"] = []
for i in range(len(te)):
    v = sv[i, :, ci[i]]
    top = np.argsort(-np.abs(v))[:5]
    for k, j in enumerate(top):
        rows[f"shap_feat{k+1}"].append(names[j]); rows[f"shap_feat{k+1}_value"].append(round(float(v[j]), 5))

out = ref.copy()
for c, v in rows.items():
    out[c] = v
out.to_csv(dst, index=False)
print("wrote", dst, out.shape, "| shap", shap.__version__, "| feature columns", len(names))
