import random
import sys
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

from src.c4.models.markov import MarkovModel
from src.c4.models.frequency import FrequencyBaseline
from src.c4.attack_sequence import collapse_sequence
from src.c4.evaluation import _hit_flags

V = ['T1003', 'T1003.008', 'T1005', 'T1007', 'T1016', 'T1018', 'T1021.004', 'T1021.005', 'T1033', 'T1036.005', 'T1039', 'T1041']
dom = V[0]
others = V[1:]

m_list, f_list = [], []
for seed in range(20):
    rng = random.Random(seed)
    episodes = {}
    for ep_idx in range(8):
        ep_name = f"EP{ep_idx+1}"
        raw_seq = []
        for item_idx in range(26):
            it = dom if rng.random() < 0.30 else rng.choice(others)
            raw_seq.append({"event_id": f"{ep_name}-{item_idx}", "techniques": [it], "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z", "unlabeled_steps_skipped_before": 0})
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
        
    ep_names = sorted(list(episodes.keys()))
    m1_tot, f1_tot, n_tot = 0, 0, 0
    for test_ep in ep_names:
        train_eps = [e for e in ep_names if e != test_ep]
        seqs_dict = {"episodes": episodes}
        markov = MarkovModel(variant="collapsed").fit(seqs_dict, training_episodes=train_eps)
        freq = FrequencyBaseline(variant="collapsed").fit(seqs_dict, training_episodes=train_eps)
        test_items = episodes[test_ep]["collapsed"]
        f_pred = freq.predict(k=3)
        f_cands = [c[0] for c in f_pred["candidates"]]
        for k in range(len(test_items) - 1):
            cur = test_items[k]["techniques"]
            tgt = set(test_items[k+1]["techniques"])
            m_pred = markov.predict(cur, k=3)
            m_cands = [c[0] for c in m_pred["candidates"]]
            m1, _ = _hit_flags(m_cands, tgt)
            f1, _ = _hit_flags(f_cands, tgt)
            m1_tot += m1
            f1_tot += f1
            n_tot += 1
    m_list.append(m1_tot / n_tot)
    f_list.append(f1_tot / n_tot)

mean_m = sum(m_list) / 20
mean_f = sum(f_list) / 20
print(f"With collapse_sequence: M={mean_m:.4f}, F={mean_f:.4f}, diff={abs(mean_m - mean_f):.4f}")
