#!/usr/bin/env python3
"""C2 Stage 1 sensitivity analysis (exploratory; NOT used for model selection).
Usage: python stage1_sensitivity.py <task_A csv> <out_dir>
A: feature-set x model, train Windows-APT train, test OTRF (AUC + @0.5). B: leave-one-OTRF-capture-out."""
import sys, os, warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import roc_auc_score
CSV, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
D = pd.read_csv(CSV, low_memory=False); D['src'] = D.source_dataset.str.split(':').str[0]
L = 'malicious_benign_label'
CAT = ['image_basename','parent_image_basename','event_id','dest_port_category','network_protocol_clean']
NUM = ['image_dir_depth','image_is_system32','image_is_syswow64','image_is_temp','image_is_appdata','image_is_windows','cmd_length',
 'cmd_has_encoded','cmd_has_noprofile','cmd_has_bypass','cmd_has_hidden','cmd_has_iex','cmd_has_download','cmd_arg_count',
 'is_system_user','has_network_info','dest_port_num','is_private_dest_ip','has_dns','dns_query_len','dns_label_count',
 'src_port_is_ephemeral','is_loopback_dest']
PAR = ['parent_image_basename','cmd_length','cmd_has_encoded','cmd_has_noprofile','cmd_has_bypass','cmd_has_hidden','cmd_has_iex','cmd_has_download','cmd_arg_count']
VARS = {'V_full':(CAT,NUM),
 'V_noparent_nocmd':([c for c in CAT if c!='parent_image_basename'],[c for c in NUM if c not in PAR]),
 'V_minimal':(['dest_port_category','network_protocol_clean'],[c for c in NUM if c not in PAR])}
def X_(df,cat,num):
    X = df[cat+num].copy()
    for c in cat: X[c] = X[c].astype('string').fillna('none').astype(str)
    return X
def pipe(kind,cat,num):
    n = Pipeline([('i',SimpleImputer(strategy='constant',fill_value=-1)),('s',StandardScaler())]) if kind=='logreg' else SimpleImputer(strategy='constant',fill_value=-1)
    pre = ColumnTransformer([('c',OneHotEncoder(handle_unknown='infrequent_if_exist',min_frequency=10,sparse_output=False),cat),('n',n,num)])
    m = {'rf':RandomForestClassifier(n_estimators=300,min_samples_leaf=2,class_weight='balanced_subsample',n_jobs=-1,random_state=42),
         'hgb':HistGradientBoostingClassifier(max_iter=150,class_weight='balanced',random_state=42),
         'logreg':LogisticRegression(max_iter=2000,class_weight='balanced')}[kind]
    return Pipeline([('p',pre),('m',m)])
def met(y,p,t=0.5):
    q=(p>=t); tp=(q&(y==1)).sum(); fp=(q&(y==0)).sum()
    return dict(auc=roc_auc_score(y,p),recall=tp/max((y==1).sum(),1),precision=tp/max(tp+fp,1),fpr=fp/max((y==0).sum(),1))
W=D[D.src=='Windows-APT-2025']; trn=W[W.split_assignment=='train']; val=W[W.split_assignment=='validation']; ot=D[D.src=='OTRF']
rows=[]
for vn,(cat,num) in VARS.items():
    for k in ('rf','hgb','logreg'):
        m=pipe(k,cat,num).fit(X_(trn,cat,num),trn[L].values)
        r=met(ot[L].values,m.predict_proba(X_(ot,cat,num))[:,1])
        r.update(experiment='A_train_WAPT_test_OTRF',variant=vn,model=k,
                 wapt_val_auc=roc_auc_score(val[L].values,m.predict_proba(X_(val,cat,num))[:,1])); rows.append(r)
caps=sorted(ot.scenario_id.unique())
for vn in ('V_full','V_noparent_nocmd'):
    cat,num=VARS[vn]
    for k in ('rf','hgb'):
        ys,ps=[],[]
        for c in caps:
            tr=pd.concat([trn,ot[ot.scenario_id!=c]]); te=ot[ot.scenario_id==c]
            m=pipe(k,cat,num).fit(X_(tr,cat,num),tr[L].values)
            ys.append(te[L].values); ps.append(m.predict_proba(X_(te,cat,num))[:,1])
        r=met(np.concatenate(ys),np.concatenate(ps)); r.update(experiment='B_leave_one_OTRF_capture_out',variant=vn,model=k); rows.append(r)
R=pd.DataFrame(rows); R.to_csv(os.path.join(OUT,'stage1_sensitivity.csv'),index=False); print(R.round(3).to_string())
