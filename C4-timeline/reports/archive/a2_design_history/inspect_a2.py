import random
import sys
from pathlib import Path

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

from src.c4.models.markov import MarkovModel
from src.c4.models.frequency import FrequencyBaseline

V = ['T1003', 'T1003.008', 'T1005', 'T1007', 'T1016', 'T1018', 'T1021.004', 'T1021.005', 'T1033', 'T1036.005', 'T1039', 'T1041']

# Let's inspect a single fold of A2
rng = random.Random(0)
dom = V[0]
others = V[1:]
episodes = {}
for ep_idx in range(8):
    ep_name = f"EP{ep_idx+1}"
    seq = []
    for item_idx in range(26):
        item = dom if rng.random() < 0.30 else rng.choice(others)
        seq.append({"event_id": f"{ep_name}-{item_idx}", "techniques": [item]})
    episodes[ep_name] = {"collapsed": seq, "raw": seq}

seqs_dict = {"episodes": episodes}
train_eps = [f"EP{i}" for i in range(2, 9)]
markov = MarkovModel().fit(seqs_dict, training_episodes=train_eps)
freq = FrequencyBaseline().fit(seqs_dict, training_episodes=train_eps)

print("Frequency candidates:", freq.predict(k=3)["candidates"])
for t in V[:3]:
    print(f"Markov predict for {t}:", markov.predict([t], k=3)["candidates"])
