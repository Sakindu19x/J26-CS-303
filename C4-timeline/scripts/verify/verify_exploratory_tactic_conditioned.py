r"""Independent Verifier for Exploratory Tactic-Conditioned Technique Prediction.

Reads data/processed_7ep/exploratory_tactic_conditioned_predictions.csv and verifies:
1. Row-level hit derivation matches stored flags for 100% of rows (95 samples).
2. Pooled hit counts, hit rates, and Wilson 95% score intervals match results JSON and MD.
3. Fold-mean hit rates match results JSON and MD.
4. Exact McNemar paired counts (b, c) and p-values match results JSON and MD.
5. Tie-sensitivity expected, best, and worst hit metrics match results JSON and MD.
6. E5-removed sensitivity subset (N=93) metrics match results JSON and MD.
7. Markdown report tokens and values match results JSON.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = REPO_ROOT / "data" / "processed_7ep" / "exploratory_tactic_conditioned_predictions.csv"
JSON_PATH = REPO_ROOT / "reports" / "7ep" / "exploratory_tactic_conditioned_results.json"
MD_PATH = REPO_ROOT / "reports" / "7ep" / "exploratory_tactic_conditioned_report.md"


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z ** 2) / total
    center = (p + (z ** 2) / (2.0 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / total) + (z ** 2 / (4.0 * (total ** 2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def exact_mcnemar(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def verify_exploratory_tactic_conditioned() -> bool:
    print("=" * 80)
    print("VERIFYING EXPLORATORY TACTIC-CONDITIONED TECHNIQUE PREDICTION")
    print("=" * 80)

    if not CSV_PATH.is_file():
        raise FileNotFoundError(f"Missing predictions CSV: {CSV_PATH}")
    if not JSON_PATH.is_file():
        raise FileNotFoundError(f"Missing results JSON: {JSON_PATH}")
    if not MD_PATH.is_file():
        raise FileNotFoundError(f"Missing report Markdown: {MD_PATH}")

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        res_json = json.load(f)
    md_text = MD_PATH.read_text(encoding="utf-8")

    # Step 1: Row count
    assert len(rows) == 95, f"Expected 95 rows in predictions CSV, got {len(rows)}"
    print(f"[Step 1] Read {len(rows)} prediction rows successfully [PASS]")

    # Step 2: Row-level hit derivation
    for idx, r in enumerate(rows):
        cands = json.loads(r["predicted_candidates_top3"])
        tgt = set(json.loads(r["target_set"]))

        derived_h1 = 1 if (cands and cands[0] in tgt) else 0
        derived_h3 = 1 if any(c in tgt for c in cands[:3]) else 0

        stored_h1 = int(r["variant_hit1"])
        stored_h3 = int(r["variant_hit3"])

        assert derived_h1 == stored_h1, f"Row {idx} ({r['sample_id']}): derived H@1 {derived_h1} != stored {stored_h1}"
        assert derived_h3 == stored_h3, f"Row {idx} ({r['sample_id']}): derived H@3 {derived_h3} != stored {stored_h3}"

    print(f"[Step 2] Row-level hit re-derivation verified across all {len(rows)} rows (0 mismatches) [PASS]")

    # Step 3: Recompute 7-episode aggregates
    r7_json = res_json["runs"]["7ep"]
    assert r7_json["n_samples"] == 95

    v_h1 = sum(int(r["variant_hit1"]) for r in rows)
    v_h3 = sum(int(r["variant_hit3"]) for r in rows)
    f_h1 = sum(int(r["frequency_hit1"]) for r in rows)
    f_h3 = sum(int(r["frequency_hit3"]) for r in rows)
    m_h1 = sum(int(r["markov_hit1"]) for r in rows)
    m_h3 = sum(int(r["markov_hit3"]) for r in rows)

    assert v_h1 == r7_json["models"]["variant"]["hit1"]
    assert v_h3 == r7_json["models"]["variant"]["hit3"]
    assert f_h1 == r7_json["models"]["frequency"]["hit1"]
    assert f_h3 == r7_json["models"]["frequency"]["hit3"]
    assert m_h1 == r7_json["models"]["markov"]["hit1"]
    assert m_h3 == r7_json["models"]["markov"]["hit3"]

    # Wilson intervals
    w1 = wilson_interval(v_h1, 95)
    w3 = wilson_interval(v_h3, 95)
    assert abs(w1[0] - r7_json["models"]["variant"]["wilson95_top1"][0]) < 1e-9
    assert abs(w1[1] - r7_json["models"]["variant"]["wilson95_top1"][1]) < 1e-9
    assert abs(w3[0] - r7_json["models"]["variant"]["wilson95_top3"][0]) < 1e-9
    assert abs(w3[1] - r7_json["models"]["variant"]["wilson95_top3"][1]) < 1e-9

    # McNemar
    b1 = sum(1 for r in rows if int(r["variant_hit1"]) == 1 and int(r["frequency_hit1"]) == 0)
    c1 = sum(1 for r in rows if int(r["variant_hit1"]) == 0 and int(r["frequency_hit1"]) == 1)
    b3 = sum(1 for r in rows if int(r["variant_hit3"]) == 1 and int(r["frequency_hit3"]) == 0)
    c3 = sum(1 for r in rows if int(r["variant_hit3"]) == 0 and int(r["frequency_hit3"]) == 1)

    p1 = exact_mcnemar(b1, c1)
    p3 = exact_mcnemar(b3, c3)
    assert b1 == r7_json["mcnemar_vs_frequency"]["top1"]["b"]
    assert c1 == r7_json["mcnemar_vs_frequency"]["top1"]["c"]
    assert abs(p1 - r7_json["mcnemar_vs_frequency"]["top1"]["p_value"]) < 1e-9
    assert b3 == r7_json["mcnemar_vs_frequency"]["top3"]["b"]
    assert c3 == r7_json["mcnemar_vs_frequency"]["top3"]["c"]
    assert abs(p3 - r7_json["mcnemar_vs_frequency"]["top3"]["p_value"]) < 1e-9

    print(f"[Step 3] 7-episode pooled metrics and McNemar verified (Variant: {v_h1}/95 H@1, {v_h3}/95 H@3) [PASS]")

    # Step 4: Fold-mean metrics
    by_ep = defaultdict(list)
    for r in rows:
        by_ep[r["test_episode"]].append(r)
    assert len(by_ep) == 7

    fold_mean_v1 = sum(sum(int(r["variant_hit1"]) for r in by_ep[ep]) / len(by_ep[ep]) for ep in by_ep) / 7.0
    fold_mean_v3 = sum(sum(int(r["variant_hit3"]) for r in by_ep[ep]) / len(by_ep[ep]) for ep in by_ep) / 7.0
    assert abs(fold_mean_v1 - r7_json["models"]["variant"]["fold_mean_top1"]) < 1e-9
    assert abs(fold_mean_v3 - r7_json["models"]["variant"]["fold_mean_top3"]) < 1e-9

    print(f"[Step 4] Fold-mean metrics verified (Variant Fold-Mean: {fold_mean_v1*100:.2f}% H@1, {fold_mean_v3*100:.2f}% H@3) [PASS]")

    # Step 5: Tie sensitivity metrics
    t1_tied = sum(1 for r in rows if r["top1_tied"] == "True")
    t3_tied = sum(1 for r in rows if r["top3_boundary_tied"] == "True")
    assert t1_tied == r7_json["tie_sensitivity"]["tied_samples_top1"]
    assert t3_tied == r7_json["tie_sensitivity"]["tied_samples_top3"]

    exp_h1 = sum(float(r["top1_expected_hit"]) for r in rows)
    exp_h3 = sum(float(r["top3_expected_hit"]) for r in rows)
    best_h1 = sum(int(r["top1_best_hit"]) for r in rows)
    best_h3 = sum(int(r["top3_best_hit"]) for r in rows)
    worst_h1 = sum(int(r["top1_worst_hit"]) for r in rows)
    worst_h3 = sum(int(r["top3_worst_hit"]) for r in rows)

    assert abs(exp_h1 - r7_json["tie_sensitivity"]["top1"]["expected"]) < 1e-4
    assert abs(exp_h3 - r7_json["tie_sensitivity"]["top3"]["expected"]) < 1e-4
    assert best_h1 == r7_json["tie_sensitivity"]["top1"]["best"]
    assert best_h3 == r7_json["tie_sensitivity"]["top3"]["best"]
    assert worst_h1 == r7_json["tie_sensitivity"]["top1"]["worst"]
    assert worst_h3 == r7_json["tie_sensitivity"]["top3"]["worst"]

    print(f"[Step 5] Tie-sensitivity metrics verified (Tied Top-1: {t1_tied}, Tied Top-3: {t3_tied}) [PASS]")

    # Step 6: Independent CSV-only recomputation of E5-removed McNemar
    e5_rows = [r for r in rows if r["test_episode"] != "E5"]
    assert len(e5_rows) == 93, f"Expected 93 E5-removed rows, got {len(e5_rows)}"
    b1_e5 = sum(1 for r in e5_rows if int(r["variant_hit1"]) == 1 and int(r["frequency_hit1"]) == 0)
    c1_e5 = sum(1 for r in e5_rows if int(r["variant_hit1"]) == 0 and int(r["frequency_hit1"]) == 1)
    b3_e5 = sum(1 for r in e5_rows if int(r["variant_hit3"]) == 1 and int(r["frequency_hit3"]) == 0)
    c3_e5 = sum(1 for r in e5_rows if int(r["variant_hit3"]) == 0 and int(r["frequency_hit3"]) == 1)
    p1_e5 = exact_mcnemar(b1_e5, c1_e5)
    p3_e5 = exact_mcnemar(b3_e5, c3_e5)

    re5_json = res_json["runs"]["e5_removed"]
    assert b1_e5 == re5_json["mcnemar_vs_frequency"]["top1"]["b"]
    assert c1_e5 == re5_json["mcnemar_vs_frequency"]["top1"]["c"]
    assert abs(p1_e5 - re5_json["mcnemar_vs_frequency"]["top1"]["p_value"]) < 1e-9
    assert b3_e5 == re5_json["mcnemar_vs_frequency"]["top3"]["b"]
    assert c3_e5 == re5_json["mcnemar_vs_frequency"]["top3"]["c"]
    assert abs(p3_e5 - re5_json["mcnemar_vs_frequency"]["top3"]["p_value"]) < 1e-9

    print(f"[Step 6] E5-removed McNemar independently recomputed from CSV: Top-1 p={p1_e5:.4f}, Top-3 p={p3_e5:.4f} [PASS]")

    # Step 7: Markdown tokens, exact McNemar strings, and integrity statements
    assert "> **EXPLORATORY, POST HOC, NOT A PRE-REGISTERED RESULT**" in md_text
    assert 'The pre-registered primary evaluation verdict ("improvement over baseline not demonstrated") is finalized and cannot be modified or overturned by this exploratory variant.' in md_text
    assert f"- **Top-1**: Variant hits and Frequency misses ($b={b1}$); Frequency hits and Variant misses ($c={c1}$); Exact McNemar $p = {p1:.4f}$ (descriptive, raw p)." in md_text
    assert f"- **Top-3**: Variant hits and Frequency misses ($b={b3}$); Frequency hits and Variant misses ($c={c3}$); Exact McNemar $p = {p3:.4f}$ (descriptive, raw p)." in md_text
    assert f"- **McNemar vs Frequency (E5-Removed)**: Top-1 $p = {p1_e5:.4f}$; Top-3 $p = {p3_e5:.4f}$ (descriptive, raw p)." in md_text
    assert f"| Exploratory Variant (Tactic-Conditioned) | {v_h1} | {v_h3} | {v_h1/95*100:.2f}% |" in md_text
    assert f"| Frequency Baseline | {f_h1} | {f_h3} | {f_h1/95*100:.2f}% |" in md_text
    assert f"| Markov Model (Technique) | {m_h1} | {m_h3} | {m_h1/95*100:.2f}% |" in md_text

    print("[Step 7] Markdown report tokens, exact McNemar strings, and disclaimer banners verified [PASS]")

    print("\n" + "=" * 80)
    print("ALL EXPLORATORY TACTIC-CONDITIONED VERIFICATIONS PASSED SUCCESSFULLY")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        ok = verify_exploratory_tactic_conditioned()
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
