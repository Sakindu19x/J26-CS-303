#!/usr/bin/env python3
"""Audit permutation test v2.1 reports (BEFORE=88c26ba, AFTER=42e941a, and working tree)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def get_git_file(commit: str, rel_path: str) -> str:
    res = subprocess.run(["git", "show", f"{commit}:{rel_path}"], cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Failed to get {rel_path} at {commit}: {res.stderr}")
    return res.stdout


def compare_json_leaves(p1: dict | list, p2: dict | list, path: str = "") -> list[dict]:
    diffs = []
    if type(p1) != type(p2):
        diffs.append({"path": path, "val1": p1, "val2": p2, "type1": type(p1).__name__, "type2": type(p2).__name__})
        return diffs

    if isinstance(p1, dict):
        all_keys = sorted(set(p1.keys()) | set(p2.keys()))
        for k in all_keys:
            subpath = f"{path}.{k}" if path else k
            if k not in p1 or k not in p2:
                diffs.append({"path": subpath, "val1": p1.get(k), "val2": p2.get(k)})
            else:
                diffs.extend(compare_json_leaves(p1[k], p2[k], subpath))
    elif isinstance(p1, list):
        if len(p1) != len(p2):
            diffs.append({"path": f"{path}.<len>", "val1": len(p1), "val2": len(p2)})
        for idx in range(min(len(p1), len(p2))):
            diffs.extend(compare_json_leaves(p1[idx], p2[idx], f"{path}[{idx}]"))
    else:
        if p1 != p2:
            diffs.append({"path": path, "val1": p1, "val2": p2})
    return diffs


def main() -> None:
    print("=" * 80)
    print("AUDIT S1/S3 UNCHANGED (88c26ba vs 42e941a vs Working Tree)")
    print("=" * 80)

    rel_md = "reports/permutation_test_v2_report.md"
    rel_json = "reports/permutation_test_v2_report.json"

    md_before = get_git_file("88c26ba", rel_md)
    md_after = get_git_file("42e941a", rel_md)
    md_work = (REPO_ROOT / rel_md).read_text(encoding="utf-8")

    json_before_str = get_git_file("88c26ba", rel_json)
    json_after_str = get_git_file("42e941a", rel_json)
    json_work_str = (REPO_ROOT / rel_json).read_text(encoding="utf-8")

    # Assert AFTER commit == working tree
    assert md_after == md_work, "AFTER md commit 42e941a != working tree md"
    assert json_after_str == json_work_str, "AFTER json commit 42e941a != working tree json"
    print("Assertion passed: commit 42e941a == working tree for both .md and .json.")

    # Section split
    headings = [
        ("Intro / Design", "## Pre-Declared Test Design & Purpose"),
        ("Validity Section", "## Scheme Validity Check (Order-Free Frequency Statistics)"),
        ("Sample Counts", "## Sample Count Distribution (Confound Resolution)"),
        ("S1 Table", "## Primary Scheme S1 Results (Headline)"),
        ("S3 Table", "## Constrained Scheme S3 Results (Adjacency-Constrained Null)"),
        ("S2 Table", "## Sensitivity Scheme S2 Results (Rate-Based Comparison)"),
        ("Remainder / Limits", "## What this test cannot show"),
    ]

    # Find split positions in md_before and md_after
    def split_pieces(text: str) -> dict[str, tuple[int, str]]:
        pieces = {}
        indices = []
        for name, h in headings:
            idx = text.find(h)
            if idx == -1:
                raise ValueError(f"Heading not found: {h}")
            indices.append((idx, name))
        indices.sort()
        for i in range(len(indices)):
            start_idx, name = indices[i]
            end_idx = indices[i + 1][0] if i + 1 < len(indices) else len(text)
            pieces[name] = (start_idx, text[start_idx:end_idx].strip())
        return pieces

    pieces_b = split_pieces(md_before)
    pieces_a = split_pieces(md_after)

    print("\n--- Markdown Pieces Comparison ---")
    print(f"| Piece Name | Heading Found (Idx) | Len Before | Len After | SHA256 Before | SHA256 After | Identical? |")
    print(f"|:---|:---:|:---:|:---:|:---:|:---:|:---:|")

    for name, _ in headings:
        idx_b, text_b = pieces_b[name]
        idx_a, text_a = pieces_a[name]
        h_b = sha256_str(text_b)
        h_a = sha256_str(text_a)
        ident = (text_b == text_a)
        print(f"| {name} | {idx_b} (B) / {idx_a} (A) | {len(text_b)} | {len(text_a)} | `{h_b[:16]}...` | `{h_a[:16]}...` | **{ident}** |")

    # Raw git diff
    print("\n--- Raw git diff 88c26ba 42e941a -- reports/permutation_test_v2_report.md ---")
    diff_res = subprocess.run(
        ["git", "diff", "88c26ba", "42e941a", "--", rel_md],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    print(diff_res.stdout)

    # JSON comparison
    print("--- JSON Differing Key Paths ---")
    j_before = json.loads(json_before_str)
    j_after = json.loads(json_after_str)
    diffs = compare_json_leaves(j_before, j_after)
    print(f"Total differing leaves: {len(diffs)}")
    all_numeric_equal = True
    all_differing_are_strings = True
    for d in diffs:
        v1, v2 = d["val1"], d["val2"]
        is_num = isinstance(v1, (int, float)) or isinstance(v2, (int, float))
        is_str = isinstance(v1, str) and isinstance(v2, str)
        if is_num:
            all_numeric_equal = False
        if not is_str:
            all_differing_are_strings = False
        print(f"  Path: {d['path']}")
        print(f"    BEFORE: {repr(v1)}")
        print(f"    AFTER : {repr(v2)}")

    print(f"\nAssertion: all numeric leaves equal -> {all_numeric_equal}")
    print(f"Assertion: all differing leaves are strings -> {all_differing_are_strings}")
    assert all_numeric_equal, "Failed: some numeric leaves differed in JSON!"
    assert all_differing_are_strings, "Failed: non-string leaf differed in JSON!"
    print("ALL JSON ASSERTIONS PASSED.")


if __name__ == "__main__":
    main()
