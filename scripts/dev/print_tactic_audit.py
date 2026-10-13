"""Developer audit script for tactic-level LOEO evaluation.

Prints comprehensive summary tables including verifier headline metrics,
per-fold breakdowns, self-repeat rates, strict single-tactic subsets,
sensitivity ordering sentences, discrepancy classifications (a)/(b),
and SHA-256 baseline hash verifications.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from scripts.verify_tactic_evaluation import recompute_from_csv, print_verifier_summary

if __name__ == "__main__":
    res = recompute_from_csv()

    print("=== 1. VERIFIER SUMMARY ===")
    print_verifier_summary(res)

    print("\n=== 2. PER-FOLD TABLE ===")
    print(f"{'Configuration':<34} {'Fold':<8} {'Ep':<4} {'Method':<18} {'N':<4} {'H@1':<5} {'H@3':<5} {'Top-1':<8} {'Top-3':<8}")
    print("-" * 97)
    for cfg in ("tactic_collapsed", "tactic_raw", "tactic_collapsed_dataset_tactics", "tactic_raw_dataset_tactics"):
        d = res[cfg]
        for fid in sorted(d["methods"]["markov"]["per_fold"].keys()):
            for m in ("markov", "frequency", "markov_fallback"):
                fd = d["methods"][m]["per_fold"][fid]
                ep = fd["test_episode"]
                n = fd["n"]
                h1 = fd["hit1"]
                h3 = fd["hit3"]
                r1 = f"{h1/n*100:.2f}%" if n else "0.00%"
                r3 = f"{h3/n*100:.2f}%" if n else "0.00%"
                print(f"{cfg:<34} {fid:<8} {ep:<4} {m:<18} {n:<4} {h1:<5} {h3:<5} {r1:<8} {r3:<8}")

    print("\n=== 3. SELF-REPEAT TABLE ===")
    print(f"{'Slice':<20} {'N':<5} {'Target==Current (cnt)':<24} {'Target==Current (rate)':<24} {'Target Shares >=1 (cnt)':<25} {'Target Shares >=1 (rate)':<25}")
    print("-" * 125)
    for cfg in ("tactic_collapsed", "tactic_raw"):
        sr = res[cfg]["self_repeat"]
        print(f"{cfg:<20} {sr['n']:<5} {sr['equal']:<24} {sr['equal_rate']*100:>6.2f}%{' ': <17} {sr['overlap']:<25} {sr['overlap_rate']*100:>6.2f}%")

    print("\n=== 4. STRICT SINGLE-TACTIC TARGET SUBSET TABLE ===")
    print(f"{'Slice':<20} {'N_single':<10} {'Markov H@1/3':<15} {'Freq H@1/3':<15} {'Fallback H@1/3':<16} {'Repeat H@1/3':<15}")
    print("-" * 95)
    for cfg in ("tactic_collapsed", "tactic_raw"):
        st = res[cfg]["strict_single_tactic"]
        m_str = f"{st['markov_hit1']}/{st['markov_hit3']}"
        f_str = f"{st['frequency_hit1']}/{st['frequency_hit3']}"
        fb_str = f"{st['fallback_hit1']}/{st['fallback_hit3']}"
        rep_str = f"{st['repeat_hit1']}/{st['repeat_hit3']}"
        print(f"{cfg:<20} {st['n']:<10} {m_str:<15} {f_str:<15} {fb_str:<16} {rep_str:<15}")

    print("\n=== 5. SENSITIVITY ORDERING SENTENCES ===")
    with open(BASE_DIR / "reports" / "tactic_evaluation_report.md", "r", encoding="utf-8") as f:
        for line in f:
            if "Markov-vs-Frequency ordering is" in line:
                print(line.strip())

    print("\n=== 6. (A)/(B) DISCREPANCY COUNTS ===")
    disc = res["_discrepancies"]
    print(f"Total differing events: {disc['total_count']}")
    print(f"Type (a) - Dataset contains tactic NOT in official set: count = {disc['type_a_count']}")
    print(f"  IDs: {disc['type_a_ids']}")
    print(f"Type (b) - Dataset tactic set is strict subset of official set: count = {disc['type_b_count']}")
    print(f"  IDs: {disc['type_b_ids']}")

    print("\n=== 7. STAGE 2 BASELINE HASH CHECK ===")
    with open(BASE_DIR / "reports" / "_baseline_hashes_stage2.json", "r", encoding="utf-8") as f:
        b2 = json.load(f)
    fmap2 = {
        "evaluation_report.md": BASE_DIR / "reports" / "evaluation_report.md",
        "evaluation_results.json": BASE_DIR / "reports" / "evaluation_results.json",
        "evaluation_predictions.csv": BASE_DIR / "data" / "processed" / "evaluation_predictions.csv",
    }
    for name, path in fmap2.items():
        h = hashlib.sha256(open(path, "rb").read()).hexdigest()
        match = (h == b2[name])
        print(f"{name}: {h[:16]}... MATCH: {match}")

    print("\n=== 8. STAGE 1 HASH CHECK ===")
    stage1_files = {
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
    for fpath, exp_h in stage1_files.items():
        cur_h = hashlib.sha256(open(BASE_DIR / fpath, "rb").read()).hexdigest()
        match = (cur_h == exp_h)
        print(f"{fpath}: {cur_h[:16]}... MATCH: {match}")
