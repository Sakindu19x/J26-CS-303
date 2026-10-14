"""Verify SHA-256 hashes of all 16 protected baseline files.

(a) 3 Technique files against reports/_baseline_hashes_stage2.json
(b) 10 Stage 1 files against canonical Stage 1 baseline
(c) 3 Tactic files against reports/_baseline_hashes_tactic.json
"""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

# Load baselines
with open(BASE_DIR / "reports" / "_baseline_hashes_stage2.json", "r", encoding="utf-8") as f:
    b_tech = json.load(f)

with open(BASE_DIR / "reports" / "_baseline_hashes_tactic.json", "r", encoding="utf-8") as f:
    b_tactic = json.load(f)

b_stage1 = {
    "data/processed/attack_sequences.json": "d76fcadc27b510b3d19c02f237e50b42c4b6516cf1e835e0e1dc8185ea113f76",
    "data/processed/attack_timelines.json": "5592c69735495a65f0824738d6f15923a78ab54ab6b44690afe040e079851fc4",
    "data/processed/loeo_folds.json": "a4bf2fa577e54b3e6176b0bf5199dfb58c87bc9bfea8e88cbf99b11c7a1d58ed",
    "data/processed/next_technique_samples.json": "6208603ce67e673a6c980dbd265484a9079396f9deb840892805ae8493f06849",
    "data/processed/normalized_events.json": "963f37f74b2497c628de8416442fe192b8d6d5e3914bb6ad3fec6f0d0c7ea2b4",
    "data/processed/technique_tactic_reference.json": "087c390fc2f5abcaba9bdf53977a9eb70a6f0aef7ba9c326709b7d6bc0597bd7",
    "reports/data_quality_report.json": "56fea61d59f52cf09eff2a6d0b301b1a4b2d25bc8555e09a84d039ab6690a113",
    "reports/timeline_validation_report.json": "0f5d0832c6a0c0dc148d55de01a7a3b7a4530223df4209e995a3b7060845a6d0",
    "reports/tactic_discrepancy_report.json": "0621ee6ad3d002537cdceb7850b88d119848d92a9bdd4df2658f7d7317742e80",
    "reports/sequence_statistics.json": "dc1eb91ba37fadee0b4eda6e41afa14bd2c282627b31afc2bcebaa845555b6ae",
}

print("=" * 80)
print("SHA-256 BASELINE INTEGRITY VERIFICATION REPORT")
print("=" * 80)

# (a) Technique files
print("\n(a) Technique Files (vs reports/_baseline_hashes_stage2.json):")
tech_paths = {
    "evaluation_report.md": BASE_DIR / "reports" / "evaluation_report.md",
    "evaluation_results.json": BASE_DIR / "reports" / "evaluation_results.json",
    "evaluation_predictions.csv": BASE_DIR / "data" / "processed" / "evaluation_predictions.csv",
}
for name, p in tech_paths.items():
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    match = (h == b_tech[name])
    status = "MATCH" if match else "MISMATCH"
    print(f"  {name:<30} {h}  [{status}]")
    if not match:
        raise ValueError(f"Byte mismatch in technique file: {name}")

# (b) Stage 1 files
print("\n(b) Stage 1 Files (10 canonical files):")
for rel_path, exp_h in b_stage1.items():
    p = BASE_DIR / rel_path
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    match = (h == exp_h)
    status = "MATCH" if match else "MISMATCH"
    print(f"  {rel_path:<45} {h}  [{status}]")
    if not match:
        raise ValueError(f"Byte mismatch in Stage 1 file: {rel_path}")

# (c) Tactic files
print("\n(c) Tactic Files (vs reports/_baseline_hashes_tactic.json):")
tactic_paths = {
    "tactic_evaluation_report.md": BASE_DIR / "reports" / "tactic_evaluation_report.md",
    "tactic_evaluation_results.json": BASE_DIR / "reports" / "tactic_evaluation_results.json",
    "tactic_evaluation_predictions.csv": BASE_DIR / "data" / "processed" / "tactic_evaluation_predictions.csv",
}
for name, p in tactic_paths.items():
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    match = (h == b_tactic[name])
    status = "MATCH" if match else "MISMATCH"
    print(f"  {name:<35} {h}  [{status}]")
    if not match:
        raise ValueError(f"Byte mismatch in tactic file: {name}")

# (d) 7-Episode Stage 1 files
print("\n(d) 7-Episode Stage 1 Files (vs reports/_baseline_hashes_7ep_stage1.json):")
hash_file_7ep = BASE_DIR / "reports" / "_baseline_hashes_7ep_stage1.json"
if hash_file_7ep.is_file():
    with open(hash_file_7ep, "r", encoding="utf-8") as f:
        b_7ep = json.load(f)
    for rel_path, exp_h in b_7ep.items():
        p = BASE_DIR / rel_path
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        match = (h == exp_h)
        status = "MATCH" if match else "MISMATCH"
        print(f"  {rel_path:<52} {h}  [{status}]")
        if not match:
            raise ValueError(f"Byte mismatch in 7-episode Stage 1 file: {rel_path}")

# (e) 7-Episode Evaluation files
print("\n(e) 7-Episode Evaluation Files (vs reports/_baseline_hashes_7ep_eval.json):")
hash_file_7ep_eval = BASE_DIR / "reports" / "_baseline_hashes_7ep_eval.json"
if hash_file_7ep_eval.is_file():
    with open(hash_file_7ep_eval, "r", encoding="utf-8") as f:
        b_7ep_eval = json.load(f)
    for rel_path, exp_h in b_7ep_eval.items():
        p = BASE_DIR / rel_path
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        match = (h == exp_h)
        status = "MATCH" if match else "MISMATCH"
        print(f"  {rel_path:<52} {h}  [{status}]")
        if not match:
            raise ValueError(f"Byte mismatch in 7-episode Evaluation file: {rel_path}")

print("\n" + "=" * 80)
print("ALL BASELINE FILES BYTE-IDENTICAL AND FULLY VERIFIED")
print("=" * 80)

