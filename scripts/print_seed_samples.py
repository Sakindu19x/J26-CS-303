"""Print five test samples chosen with fixed seed with predictions and supporting evidence."""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

from c4.models.markov import MarkovModel

BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLES_PATH = BASE_DIR / "data" / "processed" / "next_technique_samples.json"
PRED_PATH = BASE_DIR / "data" / "processed" / "evaluation_predictions.csv"
SEQS_PATH = BASE_DIR / "data" / "processed" / "attack_sequences.json"
FOLDS_PATH = BASE_DIR / "data" / "processed" / "loeo_folds.json"

with open(SAMPLES_PATH, encoding="utf-8") as f:
    samples = json.load(f)
cf_samples = [s for s in samples if s["variant"] == "collapsed" and s["granularity"] == "full"]

with open(PRED_PATH, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

m_by_s = {r["sample_id"]: r for r in rows if r["configuration"] == "collapsed_full" and r["method"] == "markov"}
f_by_s = {r["sample_id"]: r for r in rows if r["configuration"] == "collapsed_full" and r["method"] == "frequency"}

with open(SEQS_PATH, encoding="utf-8") as f:
    sequences = json.load(f)

with open(FOLDS_PATH, encoding="utf-8") as f:
    folds = json.load(f)
folds_by_ep = {f["test_episode"]: f for f in folds}

random.seed(42)
sampled = sorted(random.sample(cf_samples, 5), key=lambda s: s["sample_id"])

print("=== 5 TEST SAMPLES CHOSEN WITH FIXED SEED (seed=42) ===\n")
for idx, s in enumerate(sampled, 1):
    sid = s["sample_id"]
    ep = s["episode_id"]
    cur = s["current_technique_set"]
    tgt = s["target_technique_set"]
    m_r = m_by_s[sid]
    f_r = f_by_s[sid]
    fold_info = folds_by_ep[ep]

    m_status = m_r["status"]
    m_cands = json.loads(m_r["predicted_candidates_top3"])
    f_cands = json.loads(f_r["predicted_candidates_top3"])

    # Load fold Markov model to show supporting evidence
    train_eps = fold_info["training_episodes"]
    mm = MarkovModel("collapsed", "full").fit(sequences, train_eps)
    m_pred_obj = mm.predict(cur, k=3)
    ev_list = m_pred_obj.get("supporting_evidence", [])

    tgt_set = set(tgt)
    m_preds = [c[0] for c in m_cands] if m_status == "ok" else []
    hand_m_hit1 = 1 if (m_preds and m_preds[0] in tgt_set) else 0
    hand_m_hit3 = 1 if any(c in tgt_set for c in m_preds[:3]) else 0

    f_preds = [c[0] for c in f_cands]
    hand_f_hit1 = 1 if (f_preds and f_preds[0] in tgt_set) else 0
    hand_f_hit3 = 1 if any(c in tgt_set for c in f_preds[:3]) else 0

    print(f"Sample {idx}: {sid} (Episode={ep}, Fold={m_r['fold_id']}, Training Episodes={train_eps})")
    print(f"  Current Technique Set: {cur}")
    print(f"  Target Technique Set:  {tgt}")
    print(f"  Markov Prediction:")
    print(f"    Status: {m_status}")
    print(f"    Candidates: {m_cands}")
    if ev_list:
        print(f"    Supporting Evidence ({len(ev_list)} transitions): {ev_list[:2]}")
    else:
        print(f"    Supporting Evidence: None (Abstained: 0 outgoing transitions in {train_eps})")
    print(f"  Frequency Prediction:")
    print(f"    Candidates: {f_cands}")
    print(f"  Hand-Computed Hit Values:")
    print(f"    Markov:    Hit@1={hand_m_hit1} (CSV={m_r['hit1']}), Hit@3={hand_m_hit3} (CSV={m_r['hit3']})")
    print(f"    Frequency: Hit@1={hand_f_hit1} (CSV={f_r['hit1']}), Hit@3={hand_f_hit3} (CSV={f_r['hit3']})")
    print()
