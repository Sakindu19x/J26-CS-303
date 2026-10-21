"""
Run ONE held-out test request through the saved model and show input -> output.
No app needed. Component 1: Adaptive Web Attack Detection & Correlation Model.

Run from the RA 1 folder:
    python demo/run_test_row.py                      # first test request
    python demo/run_test_row.py 443732               # a specific row_id (see Dataset/processed/readable/test_sample.csv)
    python demo/run_test_row.py --attack 66          # a random test request with that CAPEC label (66 = SQL Injection)
    python demo/run_test_row.py --random-attack      # any random attack request
"""

import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # RA 1 folder, so `src` can be imported

from src.config import MODEL_PATH, PREPROCESSOR_PATH, X_TEST_PATH, Y_TEST_PATH

THRESHOLD = 0.5
LINE = "=" * 78

print("Loading test data and saved model (about 10-20 seconds)...")
X_test = joblib.load(X_TEST_PATH)
y_test = joblib.load(Y_TEST_PATH)
model = joblib.load(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)
labels = list(y_test.columns)

# ---------------------------------------------------------------- choose the request
args = sys.argv[1:]
rng = np.random.default_rng()
if not args:
    row_id = X_test.index[0]
elif args[0] == "--attack" and len(args) == 2:
    column = next((c for c in labels if c.split(" - ")[0] == args[1]), None)
    if column is None:
        sys.exit(f"Unknown CAPEC code {args[1]}. Choose from: {', '.join(c.split(' - ')[0] for c in labels)}")
    row_id = rng.choice(y_test.index[y_test[column] == 1])
elif args[0] == "--random-attack":
    row_id = rng.choice(y_test.index[y_test["000 - Normal"] == 0])
else:
    row_id = int(args[0])
    if row_id not in X_test.index:
        sys.exit(f"Row {row_id} is not in the test set (it may be a training row). "
                 "Pick one from Dataset/processed/readable/test_sample.csv.")

sample = X_test.loc[[row_id]]
actual = y_test.loc[row_id]

# ---------------------------------------------------------------- 1. input
print(f"\n{LINE}\n1. INPUT  - test request row_id {row_id}  (from {X_TEST_PATH.name}, never seen in training)\n{LINE}")
for column, value in sample.iloc[0].items():
    if str(value).strip():
        print(f"  {column:26s}: {str(value)[:110]}")
print("  (empty fields not shown)")

# ---------------------------------------------------------------- 2. model
print(f"\n{LINE}\n2. MODEL  - saved preprocessor (TF-IDF + One-Hot) -> One-vs-Rest Logistic Regression\n{LINE}")
features = preprocessor.transform(sample)
print(f"  Request turned into {features.shape[1]:,} numbers ({features.nnz} non-zero)")
probabilities = model.predict_proba(features)[0]
predicted = (probabilities >= THRESHOLD).astype(int)

# ---------------------------------------------------------------- 3. output
print(f"\n{LINE}\n3. OUTPUT - probability for each of the 13 CAPEC labels (detected if >= 50%)\n{LINE}")
for label, p, pred, act in zip(labels, probabilities, predicted, actual.values):
    bar = "#" * int(round(p * 30))
    flag = "DETECTED" if pred else ""
    truth = "<- true label" if act else ""
    print(f"  {label:40s} {p * 100:6.2f}%  {bar:30s} {flag:8s} {truth}")

# ---------------------------------------------------------------- 4. result
predicted_names = [l for l, v in zip(labels, predicted) if v]
actual_names = [l for l, v in zip(labels, actual.values) if v]
print(f"\n{LINE}\n4. RESULT\n{LINE}")
print(f"  Model says : {', '.join(predicted_names) or 'nothing above 50%'}")
print(f"  True answer: {', '.join(actual_names)}")
print(f"  All 13 labels correct: {'YES' if list(predicted) == list(actual.values) else 'NO'}\n")
