import random
import math
import sys
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

from src.c4.models.markov import MarkovModel
from src.c4.models.frequency import FrequencyBaseline
from src.c4.attack_sequence import collapse_sequence
from src.c4.evaluation import _hit_flags

V = ['T1003', 'T1003.008', 'T1005', 'T1007', 'T1016', 'T1018', 'T1021.004', 'T1021.005', 'T1033', 'T1036.005', 'T1039', 'T1041']
v_to_idx = {v: i for i, v in enumerate(V)}

def pi(t: str) -> str:
    return V[(v_to_idx[t] + 1) % 12]

def comp(t: str) -> str:
    return V[(v_to_idx[t] + 6) % 12]

# A1
def generate_a1(seed: int, s: float):
    rng = random.Random(seed)
    episodes = {}
    for ep_idx in range(8):
        ep_name = f"EP{ep_idx+1}"
        cur = rng.choice(V)
        raw_seq = [{"event_id": f"{ep_name}-0", "techniques": [cur], "timestamp": f"2026-01-01T00:00:00Z", "unlabeled_steps_skipped_before": 0}]
        for item_idx in range(1, 26):
            if rng.random() < s:
                nxt = pi(cur)
            else:
                others = [x for x in V if x != cur]
                nxt = rng.choice(others)
            raw_seq.append({"event_id": f"{ep_name}-{item_idx}", "techniques": [nxt], "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z", "unlabeled_steps_skipped_before": 0})
            cur = nxt
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes

# A2
def generate_a2(seed: int):
    rng = random.Random(seed)
    dom = V[0]
    others = V[1:]
    episodes = {}
    for ep_idx in range(8):
        ep_name = f"EP{ep_idx+1}"
        raw_seq = []
        for item_idx in range(26):
            it = dom if rng.random() < 0.30 else rng.choice(others)
            raw_seq.append({"event_id": f"{ep_name}-{item_idx}", "techniques": [it], "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z", "unlabeled_steps_skipped_before": 0})
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes

# A3
def generate_a3(seed: int, s: float):
    rng = random.Random(seed)
    episodes = {}
    for ep_idx in range(8):
        ep_name = f"EP{ep_idx+1}"
        cur = rng.choice(V)
        raw_seq = [{"event_id": f"{ep_name}-0", "techniques": sorted([cur, comp(cur)]), "timestamp": f"2026-01-01T00:00:00Z", "unlabeled_steps_skipped_before": 0}]
        for item_idx in range(1, 26):
            if rng.random() < s:
                nxt = pi(cur)
            else:
                others = [x for x in V if x != cur]
                nxt = rng.choice(others)
            raw_seq.append({"event_id": f"{ep_name}-{item_idx}", "techniques": sorted([nxt, comp(nxt)]), "timestamp": f"2026-01-01T00:{item_idx:02d}:00Z", "unlabeled_steps_skipped_before": 0})
            cur = nxt
        col_seq = collapse_sequence(raw_seq)
        episodes[ep_name] = {"collapsed": col_seq, "raw": raw_seq}
    return episodes

def evaluate_replicate(episodes_data, broken_markov=False):
    ep_names = sorted(list(episodes_data.keys()))
    m1_tot, f1_tot, n_tot = 0, 0, 0
    for test_ep in ep_names:
        train_eps = [e for e in ep_names if e != test_ep]
        seqs_dict = {"episodes": episodes_data}
        markov = MarkovModel(variant="collapsed", granularity="full").fit(seqs_dict, training_episodes=train_eps)
        freq = FrequencyBaseline(variant="collapsed", granularity="full").fit(seqs_dict, training_episodes=train_eps)
        test_items = episodes_data[test_ep]["collapsed"]
        f_pred = freq.predict(k=3)
        f_cands = [c[0] for c in f_pred["candidates"]]
        for k in range(len(test_items) - 1):
            cur = test_items[k]["techniques"]
            tgt = set(test_items[k+1]["techniques"])
            if broken_markov:
                m_cands = [V[0]]
            else:
                m_pred = markov.predict(cur, k=3)
                m_cands = [c[0] for c in m_pred["candidates"]]
            m1, _ = _hit_flags(m_cands, tgt)
            f1, _ = _hit_flags(f_cands, tgt)
            m1_tot += m1
            f1_tot += f1
            n_tot += 1
    return m1_tot / n_tot, f1_tot / n_tot

print("Testing all gates...")
# A1
a1_m_means = {}
a1_f_means = {}
a1_ses = {}
a1_oracles = {}
for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
    m_list, f_list = [], []
    for seed in range(20):
        eps = generate_a1(seed, s)
        m_rate, f_rate = evaluate_replicate(eps)
        m_list.append(m_rate)
        f_list.append(f_rate)
    m_mean = sum(m_list) / 20
    f_mean = sum(f_list) / 20
    var = sum((x - m_mean)**2 for x in m_list) / 19
    se = math.sqrt(var / 20)
    oracle = s + (1.0 - s) / 11.0
    a1_m_means[s] = m_mean
    a1_f_means[s] = f_mean
    a1_ses[s] = se
    a1_oracles[s] = oracle

# A2
a2_m_list, a2_f_list = [], []
for seed in range(20):
    eps = generate_a2(seed)
    m_rate, f_rate = evaluate_replicate(eps)
    a2_m_list.append(m_rate)
    a2_f_list.append(f_rate)
a2_m_mean = sum(a2_m_list) / 20
a2_f_mean = sum(a2_f_list) / 20

# A3
a3_m_means = {}
for s in [0.0, 0.25, 0.5, 0.75, 1.0]:
    m_list = []
    for seed in range(20):
        eps = generate_a3(seed, s)
        m_rate, _ = evaluate_replicate(eps)
        m_list.append(m_rate)
    a3_m_means[s] = sum(m_list) / 20

# Negative control
neg_list = []
for seed in range(20):
    eps = generate_a1(seed, 1.0)
    m_rate, _ = evaluate_replicate(eps, broken_markov=True)
    neg_list.append(m_rate)
neg_m_mean = sum(neg_list) / 20

# Check Gates:
chance = 1.0 / 11.0
g1_pass = a1_m_means[1.0] >= 0.98
g2_thresh = max(0.02, 3 * a1_ses[0.0])
g2_pass = abs(a1_m_means[0.0] - chance) <= g2_thresh
g3_pass = all(a1_m_means[s1] <= a1_m_means[s2] for s1, s2 in [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0)])
g4_pass = all(abs(a1_m_means[s] - a1_oracles[s]) <= 0.05 for s in [0.25, 0.5, 0.75, 1.0])
g5_pass = all((a1_m_means[s] - a1_f_means[s]) >= 0.20 for s in [0.5, 0.75, 1.0])
g6_pass = abs(a2_m_mean - a2_f_mean) <= 0.03
g7_pass = a3_m_means[1.0] >= 0.98 and all(a3_m_means[s1] <= a3_m_means[s2] for s1, s2 in [(0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0)])
neg_g1_fail = not (neg_m_mean >= 0.98)

print("\n--- GATE RESULTS ---")
print(f"G1 (A1 s=1.0 >= 0.98): {g1_pass} (val: {a1_m_means[1.0]:.4f})")
print(f"G2 (A1 s=0.0 diff <= {g2_thresh:.4f}): {g2_pass} (|M-chance|: {abs(a1_m_means[0.0] - chance):.4f})")
print(f"G3 (A1 non-decreasing): {g3_pass} ({[round(a1_m_means[s], 4) for s in [0.0, 0.25, 0.5, 0.75, 1.0]]})")
print(f"G4 (A1 s>=0.25 within 0.05 oracle): {g4_pass} (max diff: {max(abs(a1_m_means[s] - a1_oracles[s]) for s in [0.25, 0.5, 0.75, 1.0]):.4f})")
print(f"G5 (A1 s>=0.5 exceeds Freq by >=0.20): {g5_pass} (min diff: {min(a1_m_means[s] - a1_f_means[s] for s in [0.5, 0.75, 1.0]):.4f})")
print(f"G6 (A2 |M - F| <= 0.03): {g6_pass} (M={a2_m_mean:.4f}, F={a2_f_mean:.4f}, diff={abs(a2_m_mean - a2_f_mean):.4f})")
print(f"G7 (A3 s=1.0 >= 0.98 & non-decreasing): {g7_pass} ({[round(a3_m_means[s], 4) for s in [0.0, 0.25, 0.5, 0.75, 1.0]]})")
print(f"Negative Control (G1 fails on broken Markov): {neg_g1_fail} (broken M={neg_m_mean:.4f})")
