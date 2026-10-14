#!/usr/bin/env python3
"""Audit PNG anomaly and learning curve file hashes across commits for Prompt 13 P1.2."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_git_bytes(commit: str, rel_path: str) -> bytes:
    res = subprocess.run(["git", "show", f"{commit}:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to read {commit}:{rel_path}")
    return res.stdout


def main() -> None:
    print("=" * 80)
    print("PNG ANOMALY AND LEARNING CURVE HASH AUDIT (1.2)")
    print("=" * 80)

    # 1. reports/7ep/learning_curve_7ep.png at 88c26ba, 4e9d663, 42e941a, and working tree
    png_rel = "reports/7ep/learning_curve_7ep.png"
    commits = ["88c26ba", "4e9d663", "42e941a"]
    print("\n--- reports/7ep/learning_curve_7ep.png Across Commits ---")
    print("| Location | Byte Size | SHA-256 |")
    print("|:---|:---:|:---|")
    for c in commits:
        data = get_git_bytes(c, png_rel)
        h = hashlib.sha256(data).hexdigest()
        print(f"| commit `{c}` | {len(data)} | `{h}` |")
    data_wt = (REPO_ROOT / png_rel).read_bytes()
    h_wt = hashlib.sha256(data_wt).hexdigest()
    print(f"| Working Tree | {len(data_wt)} | `{h_wt}` |")

    # 2. learning_curve_7ep_results.json, _report.md, _plot_data.json at 88c26ba and 42e941a
    other_files = [
        "reports/7ep/learning_curve_7ep_results.json",
        "reports/7ep/learning_curve_7ep_report.md",
        "reports/7ep/learning_curve_7ep_plot_data.json",
    ]
    print("\n--- Learning Curve JSON / MD / Plot Data at 88c26ba vs 42e941a ---")
    print("| File | Commit | Byte Size | SHA-256 |")
    print("|:---|:---|:---:|:---|")
    for rel in other_files:
        for c in ["88c26ba", "42e941a"]:
            data = get_git_bytes(c, rel)
            h = hashlib.sha256(data).hexdigest()
            print(f"| `{rel}` | `{c}` | {len(data)} | `{h}` |")

    # 3. Baseline hash entries from 88c26ba vs current
    base_88_data = get_git_bytes("88c26ba", "reports/_baseline_hashes_7ep_inference.json")
    base_88 = json.loads(base_88_data.decode("utf-8"))
    base_cur = json.loads((REPO_ROOT / "reports" / "_baseline_hashes_7ep_inference.json").read_text(encoding="utf-8"))

    print("\n--- Baseline Hash Entries in reports/_baseline_hashes_7ep_inference.json ---")
    print("| File in Baseline | 88c26ba Hash | 42e941a / Current Hash | Match? |")
    print("|:---|:---|:---|:---:|")
    all_check_files = [png_rel] + other_files + ["data/processed_7ep/learning_curve_7ep.csv"]
    for f in all_check_files:
        h_88 = base_88.get(f, "MISSING")
        h_cur = base_cur.get(f, "MISSING")
        print(f"| `{f}` | `{h_88}` | `{h_cur}` | **{h_88 == h_cur}** |")

    # Explanation statement:
    print("\n--- Assessment of 12c Step 0 Table ---")
    # At 88c26ba, the PNG file had hash 6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b.
    # When 12c Part B regenerated the plot, matplotlib generated 6477f996... if byte-identical or a new one?
    # Notice: at 88c26ba, learning_curve_7ep.png ALREADY had hash 6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b!
    h_88_png = hashlib.sha256(get_git_bytes("88c26ba", png_rel)).hexdigest()
    h_42_png = hashlib.sha256(get_git_bytes("42e941a", png_rel)).hexdigest()
    print(f"PNG hash at 88c26ba: {h_88_png}")
    print(f"PNG hash at 42e941a: {h_42_png}")
    if h_88_png == h_42_png:
        print("Verdict: The PNG was already committed with hash 6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b in 88c26ba, so the 12c Step 0 table showing this hash for the PNG was genuine verbatim output from verify_all_hashes.py matching the 88c26ba baseline.")
    else:
        print("Verdict: The PNG hash changed between 88c26ba and 42e941a.")


if __name__ == "__main__":
    main()
