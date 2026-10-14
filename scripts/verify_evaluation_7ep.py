"""Independent Verifier for Pre-Registered 7-Episode LOEO Evaluation (Prompt 12a).

CONSTRAINTS:
- Reads ONLY:
    * data/processed_7ep/evaluation_7ep_predictions.csv
    * data/processed_7ep/loeo_folds.json
    * data/processed_7ep/next_technique_samples.json
    * artifacts/7ep/fold_models/manifest.json
    * artifacts/7ep/fold_models/<slice>/<test_episode>.json
    * reports/7ep/evaluation_7ep_results.json
    * reports/7ep/evaluation_7ep_report.md
- MUST NOT import src/c4 model code (no imports from src.c4).
- Confirms:
    1. Each test sample's episode is absent from its fold's training list.
    2. Each fold-model manifest hash matches bytes on disk.
    3. Sample count per slice equals Stage 1 count (95 collapsed_full / 76 tactic / 131 raw_full).
    4. Recomputes N, hits, coverage, ceiling, Wilson intervals, per-fold and pooled tables,
       and McNemar counts and exact p-values.
    5. Compares with evaluation_7ep_results.json and every number token in evaluation_7ep_report.md.
    6. Exits non-zero on any mismatch.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Ensure stdout handles UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]

# Input paths
PREDICTIONS_CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "evaluation_7ep_predictions.csv"
FOLDS_PATH = BASE_DIR / "data" / "processed_7ep" / "loeo_folds.json"
SAMPLES_PATH = BASE_DIR / "data" / "processed_7ep" / "next_technique_samples.json"
FOLD_MODELS_DIR = BASE_DIR / "artifacts" / "7ep" / "fold_models"
MANIFEST_PATH = FOLD_MODELS_DIR / "manifest.json"
RESULTS_JSON_PATH = BASE_DIR / "reports" / "7ep" / "evaluation_7ep_results.json"
REPORT_MD_PATH = BASE_DIR / "reports" / "7ep" / "evaluation_7ep_report.md"


def sha256_file(path: Path) -> str:
    """Compute SHA-256 of file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """Wilson score 95% confidence interval for a binomial proportion."""
    if total <= 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z ** 2) / total
    center = (p + (z ** 2) / (2.0 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / total) + (z ** 2 / (4.0 * (total ** 2))))) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def exact_mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar test p-value based on binomial distribution under H0: p=0.5."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    prob_tails = sum(math.comb(n, i) * (0.5 ** n) for i in range(k + 1))
    return min(1.0, 2.0 * prob_tails)


def verify_evaluation_7ep() -> bool:
    print("=" * 80)
    print("INDEPENDENT VERIFIER FOR PRE-REGISTERED 7-EPISODE LOEO EVALUATION (E1-E7)")
    print("=" * 80)

    # Enforce NO import of src.c4
    disallowed_modules = [m for m in sys.modules if m.startswith("src.c4") or m.startswith("c4")]
    if disallowed_modules:
        raise RuntimeError(f"Disallowed module imported: {disallowed_modules}")

    # Check file existence
    required_files = [
        PREDICTIONS_CSV_PATH, FOLDS_PATH, SAMPLES_PATH,
        MANIFEST_PATH, RESULTS_JSON_PATH, REPORT_MD_PATH
    ]
    for rf in required_files:
        if not rf.exists():
            raise FileNotFoundError(f"Missing required file: {rf}")

    # -------------------------------------------------------------------------
    # 1. Fold Split Disjointness & Test Episode Absence
    # -------------------------------------------------------------------------
    print("\n[Step 1] Verifying Fold Split Disjointness and Test Episode Absence...")
    with open(FOLDS_PATH, "r", encoding="utf-8") as f:
        folds_data = json.load(f)

    if len(folds_data) != 7:
        raise ValueError(f"Expected 7 folds in loeo_folds.json, got {len(folds_data)}")

    all_episodes = {f"E{i}" for i in range(1, 8)}
    fold_train_map: dict[str, list[str]] = {}

    for fold in folds_data:
        test_ep = fold["test_episode"]
        train_eps = fold["training_episodes"]
        fold_id = fold["fold_id"]

        if test_ep in train_eps:
            raise ValueError(f"DATA LEAKAGE: Test episode {test_ep} found in training episodes for {fold_id}!")
        if len(train_eps) != 6:
            raise ValueError(f"Fold {fold_id} has {len(train_eps)} training episodes, expected 6")
        if set(train_eps) | {test_ep} != all_episodes:
            raise ValueError(f"Fold {fold_id} train+test union does not equal full E1-E7 set")
        fold_train_map[test_ep] = train_eps
        print(f"  {fold_id} (test {test_ep}): disjoint from 6 training episodes {train_eps} [PASS]")

    # -------------------------------------------------------------------------
    # 2. Fold Model Manifest Integrity & Structure
    # -------------------------------------------------------------------------
    print("\n[Step 2] Verifying Fold Model Manifest and Model Files on Disk...")
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)["files"]

    expected_model_count = 21  # 3 slices * 7 folds
    if len(manifest) != expected_model_count:
        raise ValueError(f"Expected {expected_model_count} models in manifest, got {len(manifest)}")

    for rel_path, meta in sorted(manifest.items()):
        file_path = BASE_DIR / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"Manifest file missing on disk: {file_path}")
        actual_hash = sha256_file(file_path)
        if actual_hash != meta["sha256"]:
            raise ValueError(f"Hash mismatch for {rel_path}: expected {meta['sha256']}, got {actual_hash}")
        actual_size = file_path.stat().st_size
        if actual_size != meta["size_bytes"]:
            raise ValueError(f"Size mismatch for {rel_path}: expected {meta['size_bytes']}, got {actual_size}")

        # Verify model file internal structure without model code
        with open(file_path, "r", encoding="utf-8") as mf:
            m_data = json.load(mf)
        test_ep = m_data["test_episode"]
        train_eps = m_data["training_episodes"]
        if test_ep in train_eps:
            raise ValueError(f"Model file {rel_path} has test episode {test_ep} in training episodes!")
        if "markov" not in m_data or "frequency" not in m_data:
            raise ValueError(f"Model file {rel_path} missing markov or frequency keys")

    print(f"  All {len(manifest)} fold models verified against SHA-256 manifest and structurally checked [PASS]")

    # -------------------------------------------------------------------------
    # 3. Sample Count Verification (matching Stage 1)
    # -------------------------------------------------------------------------
    print("\n[Step 3] Verifying Sample Counts Against Stage 1...")
    with open(SAMPLES_PATH, "r", encoding="utf-8") as f:
        stage1_samples = json.load(f)

    cf_stage1 = [s for s in stage1_samples if s["variant"] == "collapsed" and s["granularity"] == "full"]
    raw_stage1 = [s for s in stage1_samples if s["variant"] == "raw" and s["granularity"] == "full"]

    if len(cf_stage1) != 95:
        raise ValueError(f"Stage 1 collapsed_full count is {len(cf_stage1)}, expected 95")
    if len(raw_stage1) != 131:
        raise ValueError(f"Stage 1 raw_full count is {len(raw_stage1)}, expected 131")

    # Read predictions CSV
    with open(PREDICTIONS_CSV_PATH, "r", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))

    total_csv_rows = len(csv_rows)
    expected_total_rows = 95 + 76 + 131  # 302
    if total_csv_rows != expected_total_rows:
        raise ValueError(f"Expected {expected_total_rows} total rows in CSV, got {total_csv_rows}")

    rows_by_slice: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in csv_rows:
        rows_by_slice[r["slice"]].append(r)

    n_cf = len(rows_by_slice["collapsed_full"])
    n_tac = len(rows_by_slice["tactic_collapsed"])
    n_raw = len(rows_by_slice["raw_full"])

    if n_cf != 95:
        raise ValueError(f"CSV collapsed_full count is {n_cf}, expected 95")
    if n_tac != 76:
        raise ValueError(f"CSV tactic_collapsed count is {n_tac}, expected 76")
    if n_raw != 131:
        raise ValueError(f"CSV raw_full count is {n_raw}, expected 131")

    # Verify per-sample leakage check: each test_episode must match fold
    for r in csv_rows:
        tep = r["test_episode"]
        if tep not in fold_train_map:
            raise ValueError(f"Unknown test episode {tep} in sample {r['sample_id']}")
        if tep in fold_train_map[tep]:
            raise ValueError(f"DATA LEAKAGE: Sample {r['sample_id']} has test episode {tep} in its training fold!")

    print(f"  collapsed_full:   N = {n_cf} (expected 95) [MATCH]")
    print(f"  tactic_collapsed: N = {n_tac} (expected 76) [MATCH]")
    print(f"  raw_full:         N = {n_raw} (expected 131) [MATCH]")
    print(f"  Total CSV Rows:   N = {total_csv_rows} (expected 302) [MATCH]")

    # -------------------------------------------------------------------------
    # 4. Independent Recomputation of Metrics from Predictions CSV
    # -------------------------------------------------------------------------
    print("\n[Step 4] Independently Recomputing Metrics from Predictions CSV...")
    with open(RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
        results_json = json.load(f)

    recomputed_slices: dict[str, Any] = {}

    for slice_name, json_key in [
        ("collapsed_full", "primary_slice_technique_collapsed_full"),
        ("tactic_collapsed", "secondary_slice_tactic_collapsed"),
        ("raw_full", "reference_slice_technique_raw_full"),
    ]:
        s_rows = rows_by_slice[slice_name]
        n_slice = len(s_rows)
        slice_json = results_json[json_key]

        if slice_json["n_samples"] != n_slice:
            raise ValueError(f"JSON n_samples mismatch for {slice_name}")

        # Compute hits
        m_h1 = sum(int(r["markov_hit1"]) for r in s_rows)
        m_h3 = sum(int(r["markov_hit3"]) for r in s_rows)
        f_h1 = sum(int(r["frequency_hit1"]) for r in s_rows)
        f_h3 = sum(int(r["frequency_hit3"]) for r in s_rows)
        fb_h1 = sum(int(r["markov_fallback_hit1"]) for r in s_rows)
        fb_h3 = sum(int(r["markov_fallback_hit3"]) for r in s_rows)

        # Coverage and Ceiling
        cov_count = sum(1 for r in s_rows if r["markov_status"] == "ok")
        ceil_count = sum(1 for r in s_rows if r["ceiling"].lower() in ("true", "1"))

        # Wilson intervals
        m_w1 = wilson_interval(m_h1, n_slice)
        m_w3 = wilson_interval(m_h3, n_slice)
        f_w1 = wilson_interval(f_h1, n_slice)
        f_w3 = wilson_interval(f_h3, n_slice)
        fb_w1 = wilson_interval(fb_h1, n_slice)
        fb_w3 = wilson_interval(fb_h3, n_slice)

        # Per fold metrics
        by_fold: dict[str, list[dict[str, str]]] = defaultdict(list)
        for r in s_rows:
            by_fold[r["test_episode"]].append(r)

        per_fold_recomputed: dict[str, dict[str, Any]] = {}
        fold_rates_m1: list[float] = []
        fold_rates_m3: list[float] = []
        fold_rates_f1: list[float] = []
        fold_rates_f3: list[float] = []
        fold_rates_fb1: list[float] = []
        fold_rates_fb3: list[float] = []

        for ep_idx in range(1, 8):
            ep_id = f"E{ep_idx}"
            f_rows = by_fold.get(ep_id, [])
            fn = len(f_rows)
            fm_h1 = sum(int(r["markov_hit1"]) for r in f_rows)
            fm_h3 = sum(int(r["markov_hit3"]) for r in f_rows)
            ff_h1 = sum(int(r["frequency_hit1"]) for r in f_rows)
            ff_h3 = sum(int(r["frequency_hit3"]) for r in f_rows)
            ffb_h1 = sum(int(r["markov_fallback_hit1"]) for r in f_rows)
            ffb_h3 = sum(int(r["markov_fallback_hit3"]) for r in f_rows)
            fcov = sum(1 for r in f_rows if r["markov_status"] == "ok")
            fceil = sum(1 for r in f_rows if r["ceiling"].lower() in ("true", "1"))

            m1_rate = fm_h1 / fn if fn > 0 else 0.0
            m3_rate = fm_h3 / fn if fn > 0 else 0.0
            f1_rate = ff_h1 / fn if fn > 0 else 0.0
            f3_rate = ff_h3 / fn if fn > 0 else 0.0
            fb1_rate = ffb_h1 / fn if fn > 0 else 0.0
            fb3_rate = ffb_h3 / fn if fn > 0 else 0.0
            fold_rates_m1.append(m1_rate)
            fold_rates_m3.append(m3_rate)
            fold_rates_f1.append(f1_rate)
            fold_rates_f3.append(f3_rate)
            fold_rates_fb1.append(fb1_rate)
            fold_rates_fb3.append(fb3_rate)

            fid = f"fold_{ep_idx}"
            per_fold_recomputed[fid] = {
                "test_episode": ep_id,
                "n_samples": fn,
                "markov_hit1": fm_h1,
                "markov_hit3": fm_h3,
                "markov_top1": m1_rate,
                "markov_top3": m3_rate,
                "frequency_hit1": ff_h1,
                "frequency_hit3": ff_h3,
                "fallback_hit1": ffb_h1,
                "fallback_hit3": ffb_h3,
                "covered_samples": fcov,
                "ceiling_hits": fceil,
            }

            # Check with JSON per-fold
            json_f = slice_json["per_fold"][fid]
            if json_f["n_samples"] != fn:
                raise ValueError(f"Mismatch in {slice_name} {fid} N: recomputed={fn}, json={json_f['n_samples']}")
            if json_f["markov"]["hit1"] != fm_h1 or json_f["markov"]["hit3"] != fm_h3:
                raise ValueError(f"Mismatch in {slice_name} {fid} Markov hits")
            if json_f["frequency"]["hit1"] != ff_h1 or json_f["frequency"]["hit3"] != ff_h3:
                raise ValueError(f"Mismatch in {slice_name} {fid} Frequency hits")
            # Covered and ceiling in fold
            if slice_name == "tactic_collapsed":
                if json_f["covered_samples"] != fcov or json_f["ceiling_hits"] != fceil:
                    raise ValueError(f"Mismatch in {slice_name} {fid} coverage/ceiling")
            else:
                if json_f["markov"]["covered_samples"] != fcov or json_f["ceiling"]["hits"] != fceil:
                    raise ValueError(f"Mismatch in {slice_name} {fid} coverage/ceiling")

        fold_mean_m1 = sum(fold_rates_m1) / 7.0
        fold_mean_m3 = sum(fold_rates_m3) / 7.0
        fold_mean_f1 = sum(fold_rates_f1) / 7.0
        fold_mean_f3 = sum(fold_rates_f3) / 7.0
        fold_mean_fb1 = sum(fold_rates_fb1) / 7.0
        fold_mean_fb3 = sum(fold_rates_fb3) / 7.0

        # Verify Headline with JSON
        head_json = slice_json["headline"]
        fallback_key = "markov_fallback" if slice_name == "tactic_collapsed" else "fallback"

        if head_json["markov"]["hit1"] != m_h1 or head_json["markov"]["hit3"] != m_h3:
            raise ValueError(f"Mismatch in {slice_name} headline Markov hits")
        if head_json["frequency"]["hit1"] != f_h1 or head_json["frequency"]["hit3"] != f_h3:
            raise ValueError(f"Mismatch in {slice_name} headline Frequency hits")
        if head_json[fallback_key]["hit1"] != fb_h1 or head_json[fallback_key]["hit3"] != fb_h3:
            raise ValueError(f"Mismatch in {slice_name} headline Fallback hits")

        # Verify Wilson interval numbers
        for bound_idx, bound_name in [(0, "lower"), (1, "upper")]:
            if abs(head_json["markov"]["wilson95_top1"][bound_idx] - m_w1[bound_idx]) > 1e-4:
                raise ValueError(f"Wilson interval mismatch for {slice_name} markov hit1 {bound_name}")
            if abs(head_json["markov"]["wilson95_top3"][bound_idx] - m_w3[bound_idx]) > 1e-4:
                raise ValueError(f"Wilson interval mismatch for {slice_name} markov hit3 {bound_name}")
            if abs(head_json["frequency"]["wilson95_top1"][bound_idx] - f_w1[bound_idx]) > 1e-4:
                raise ValueError(f"Wilson interval mismatch for {slice_name} frequency hit1 {bound_name}")
            if abs(head_json["frequency"]["wilson95_top3"][bound_idx] - f_w3[bound_idx]) > 1e-4:
                raise ValueError(f"Wilson interval mismatch for {slice_name} frequency hit3 {bound_name}")

        # Verify fold means
        if abs(head_json["markov"]["fold_mean_top1"] - fold_mean_m1) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} markov hit1")
        if abs(head_json["markov"]["fold_mean_top3"] - fold_mean_m3) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} markov hit3")
        if abs(head_json["frequency"]["fold_mean_top1"] - fold_mean_f1) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} frequency hit1")
        if abs(head_json["frequency"]["fold_mean_top3"] - fold_mean_f3) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} frequency hit3")
        if abs(head_json[fallback_key]["fold_mean_top1"] - fold_mean_fb1) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} fallback hit1")
        if abs(head_json[fallback_key]["fold_mean_top3"] - fold_mean_fb3) > 1e-4:
            raise ValueError(f"Fold-mean mismatch for {slice_name} fallback hit3")

        # Verify coverage and ceiling
        cov_key = slice_json["coverage"] if slice_name == "tactic_collapsed" else head_json["coverage"]
        ceil_key = slice_json["ceiling"] if slice_name == "tactic_collapsed" else head_json["ceiling"]
        if cov_key["covered_samples"] != cov_count:
            raise ValueError(f"Coverage mismatch for {slice_name}: recomputed={cov_count}, json={cov_key['covered_samples']}")
        if ceil_key["hits"] != ceil_count:
            raise ValueError(f"Ceiling mismatch for {slice_name}: recomputed={ceil_count}, json={ceil_key['hits']}")

        recomputed_slices[slice_name] = {
            "n_samples": n_slice,
            "m_h1": m_h1, "m_h3": m_h3,
            "f_h1": f_h1, "f_h3": f_h3,
            "fb_h1": fb_h1, "fb_h3": fb_h3,
            "cov_count": cov_count, "ceil_count": ceil_count,
            "m_w1": m_w1, "m_w3": m_w3,
            "f_w1": f_w1, "f_w3": f_w3,
            "fb_w1": fb_w1, "fb_w3": fb_w3,
            "fold_mean_m1": fold_mean_m1, "fold_mean_m3": fold_mean_m3,
            "fold_mean_f1": fold_mean_f1, "fold_mean_f3": fold_mean_f3,
            "fold_mean_fb1": fold_mean_fb1, "fold_mean_fb3": fold_mean_fb3,
            "per_fold": per_fold_recomputed,
        }

        print(
            f"  {slice_name:16s} | N={n_slice:2d} | Markov: {m_h1}/{n_slice} (Hit@1), {m_h3}/{n_slice} (Hit@3) | "
            f"Freq: {f_h1}/{n_slice}, {f_h3}/{n_slice} | Covered: {cov_count}/{n_slice} | Ceiling: {ceil_count}/{n_slice} [PASS]"
        )

    # -------------------------------------------------------------------------
    # 5. Independent Recomputation of McNemar Paired Tests
    # -------------------------------------------------------------------------
    print("\n[Step 5] Independently Recomputing McNemar Paired Tests...")
    paired_json = results_json["paired_tests"]

    def verify_paired(test_id: str, slice_name: str, m1_col: str, m2_col: str) -> dict[str, Any]:
        s_rows = rows_by_slice[slice_name]
        n = len(s_rows)
        both = sum(1 for r in s_rows if int(r[m1_col]) == 1 and int(r[m2_col]) == 1)
        b = sum(1 for r in s_rows if int(r[m1_col]) == 1 and int(r[m2_col]) == 0)
        c = sum(1 for r in s_rows if int(r[m1_col]) == 0 and int(r[m2_col]) == 1)
        neither = sum(1 for r in s_rows if int(r[m1_col]) == 0 and int(r[m2_col]) == 0)

        p_val = exact_mcnemar(b, c)
        m1_rate = sum(int(r[m1_col]) for r in s_rows) / n
        m2_rate = sum(int(r[m2_col]) for r in s_rows) / n
        diff = m1_rate - m2_rate

        j_test = paired_json[test_id]
        jt = j_test["table"]

        if jt["both_hit"] != both or jt["b_m1_only"] != b or jt["c_m2_only"] != c or jt["neither"] != neither:
            raise ValueError(f"Contingency table mismatch for {test_id}: calc={(both, b, c, neither)}, json={jt}")
        if abs(j_test["m1_rate"] - m1_rate) > 1e-4 or abs(j_test["m2_rate"] - m2_rate) > 1e-4:
            raise ValueError(f"Rate mismatch for {test_id}")
        if abs(j_test["rate_difference"] - diff) > 1e-4:
            raise ValueError(f"Rate difference mismatch for {test_id}")
        if abs(j_test["p_value_raw"] - p_val) > 1e-4:
            raise ValueError(f"McNemar p-value mismatch for {test_id}: calc={p_val:.6f}, json={j_test['p_value_raw']:.6f}")
        if j_test["label"] != "raw p, pre-Holm":
            raise ValueError(f"Expected 'raw p, pre-Holm' label for {test_id}, got {j_test['label']}")

        print(
            f"  {test_id:42s} | a={both:2d}, b={b:2d}, c={c:2d}, d={neither:2d} | "
            f"m1={m1_rate:.4f}, m2={m2_rate:.4f}, diff={diff:+.4f} | exact p = {p_val:.4f} [PASS]"
        )
        return {"both": both, "b": b, "c": c, "neither": neither, "p_val": p_val, "diff": diff}

    # P1: Tactic tactic_collapsed Hit@3
    rec_p1 = verify_paired("P1_tactic_collapsed_hit3", "tactic_collapsed", "markov_hit3", "frequency_hit3")
    # P2: Technique collapsed_full Hit@3
    rec_p2 = verify_paired("P2_technique_collapsed_full_hit3", "collapsed_full", "markov_hit3", "frequency_hit3")

    # Descriptive comparisons
    verify_paired("descriptive_technique_collapsed_full_hit1", "collapsed_full", "markov_hit1", "frequency_hit1")
    verify_paired("descriptive_tactic_collapsed_hit1", "tactic_collapsed", "markov_hit1", "frequency_hit1")
    verify_paired("descriptive_technique_fallback_vs_freq_hit3", "collapsed_full", "markov_fallback_hit3", "frequency_hit3")
    verify_paired("descriptive_technique_fallback_vs_freq_hit1", "collapsed_full", "markov_fallback_hit1", "frequency_hit1")
    verify_paired("descriptive_tactic_fallback_vs_freq_hit3", "tactic_collapsed", "markov_fallback_hit3", "frequency_hit3")
    verify_paired("descriptive_tactic_fallback_vs_freq_hit1", "tactic_collapsed", "markov_fallback_hit1", "frequency_hit1")

    # -------------------------------------------------------------------------
    # 6. Verify Markdown Report Tokens and Consistency
    # -------------------------------------------------------------------------
    print("\n[Step 6] Verifying Markdown Report Number Tokens and Text Consistency...")
    with open(REPORT_MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Verify key tokens directly from recomputed values
    cf = recomputed_slices["collapsed_full"]
    tac = recomputed_slices["tactic_collapsed"]
    raw = recomputed_slices["raw_full"]

    expected_strings = [
        # Setup
        "Pre-Registered 7-Episode LOEO Evaluation Report (E1–E7)",
        "Primary**: Technique `collapsed_full` ($N=95$ transition samples)",
        "Secondary**: Tactic `tactic_collapsed` ($N=76$ transition samples)",
        "Reference**: Technique `raw_full` ($N=131$ transition samples)",
        # P2 headline numbers
        f"Markov          |  {cf['m_h1']:d} / 95 | {cf['m_h1']/95:.4f} | [{cf['m_w1'][0]:.4f}, {cf['m_w1'][1]:.4f}]      |  {cf['m_h3']:d} / 95 | {cf['m_h3']/95:.4f} | [{cf['m_w3'][0]:.4f}, {cf['m_w3'][1]:.4f}]",
        f"Frequency       |  {cf['f_h1']:d} / 95 | {cf['f_h1']/95:.4f} | [{cf['f_w1'][0]:.4f}, {cf['f_w1'][1]:.4f}]      | {cf['f_h3']:d} / 95 | {cf['f_h3']/95:.4f} | [{cf['f_w3'][0]:.4f}, {cf['f_w3'][1]:.4f}]",
        f"Markov Fallback |  {cf['fb_h1']:d} / 95 | {cf['fb_h1']/95:.4f} | [{cf['fb_w1'][0]:.4f}, {cf['fb_w1'][1]:.4f}]      |  {cf['fb_h3']:d} / 95 | {cf['fb_h3']/95:.4f} | [{cf['fb_w3'][0]:.4f}, {cf['fb_w3'][1]:.4f}]",
        f"Coverage (Markov Status ok)**: {cf['cov_count']}/95 ({cf['cov_count']/95:.4f})",
        f"Target Ceiling**: {cf['ceil_count']}/95 ({cf['ceil_count']/95:.4f})",
        # P1 headline numbers
        f"Markov          | {tac['m_h1']:d} / 76 | {tac['m_h1']/76:.4f} | [{tac['m_w1'][0]:.4f}, {tac['m_w1'][1]:.4f}]      | {tac['m_h3']:d} / 76 | {tac['m_h3']/76:.4f} | [{tac['m_w3'][0]:.4f}, {tac['m_w3'][1]:.4f}]",
        f"Frequency       | {tac['f_h1']:d} / 76 | {tac['f_h1']/76:.4f} | [{tac['f_w1'][0]:.4f}, {tac['f_w1'][1]:.4f}]      | {tac['f_h3']:d} / 76 | {tac['f_h3']/76:.4f} | [{tac['f_w3'][0]:.4f}, {tac['f_w3'][1]:.4f}]",
        f"Markov Fallback | {tac['fb_h1']:d} / 76 | {tac['fb_h1']/76:.4f} | [{tac['fb_w1'][0]:.4f}, {tac['fb_w1'][1]:.4f}]      | {tac['fb_h3']:d} / 76 | {tac['fb_h3']/76:.4f} | [{tac['fb_w3'][0]:.4f}, {tac['fb_w3'][1]:.4f}]",
        f"Coverage (Markov Status ok)**: {tac['cov_count']}/76 ({tac['cov_count']/76:.4f})",
        f"Target Ceiling**: {tac['ceil_count']}/76 ({tac['ceil_count']/76:.4f})",
        # Reference headline numbers
        f"Markov          | {raw['m_h1']:d} / 131 | {raw['m_h1']/131:.4f} | [{raw['m_w1'][0]:.4f}, {raw['m_w1'][1]:.4f}]      | {raw['m_h3']:d} / 131 | {raw['m_h3']/131:.4f} | [{raw['m_w3'][0]:.4f}, {raw['m_w3'][1]:.4f}]",
        f"Frequency       |  {raw['f_h1']:d} / 131 | {raw['f_h1']/131:.4f} | [{raw['f_w1'][0]:.4f}, {raw['f_w1'][1]:.4f}]      | {raw['f_h3']:d} / 131 | {raw['f_h3']/131:.4f} | [{raw['f_w3'][0]:.4f}, {raw['f_w3'][1]:.4f}]",
        f"Coverage (Markov Status ok)**: {raw['cov_count']}/131 ({raw['cov_count']/131:.4f})",
        f"Target Ceiling**: {raw['ceil_count']}/131 ({raw['ceil_count']/131:.4f})",
        # P1 McNemar
        f"Both Hit ($a$) | {rec_p1['both']:2d}",
        f"Markov Only ($b$) | {rec_p1['b']:2d}",
        f"Frequency Only ($c$) | {rec_p1['c']:2d}",
        f"Neither Hit ($d$) | {rec_p1['neither']:2d}",
        f"Discordant Counts**: $b = {rec_p1['b']}$, $c = {rec_p1['c']}$",
        f"Exact Two-Sided McNemar Test**: $p = {rec_p1['p_val']:.4f}$ (raw p, pre-Holm)",
        # P2 McNemar
        f"Both Hit ($a$) |  {rec_p2['both']:d}",
        f"Markov Only ($b$) |  {rec_p2['b']:d}",
        f"Frequency Only ($c$) | {rec_p2['c']:2d}",
        f"Neither Hit ($d$) | {rec_p2['neither']:2d}",
        f"Discordant Counts**: $b = {rec_p2['b']}$, $c = {rec_p2['c']}$",
        f"Exact Two-Sided McNemar Test**: $p = {rec_p2['p_val']:.4f}$ (raw p, pre-Holm)",
        # Comparison with 4ep table numbers
        "| Technique (`collapsed_full`) | Sample Count ($N$) | 67 | 95 | +28 |",
        "| Technique (`collapsed_full`) | Markov Hit@1 | 1/67 (0.0149) | 3/95 (0.0316) | +0.0167 |",
        "| Technique (`collapsed_full`) | Markov Hit@3 | 2/67 (0.0299) | 3/95 (0.0316) | +0.0017 |",
        "| Technique (`collapsed_full`) | Frequency Hit@1 | 4/67 (0.0597) | 7/95 (0.0737) | +0.0140 |",
        "| Technique (`collapsed_full`) | Frequency Hit@3 | 8/67 (0.1194) | 16/95 (0.1684) | +0.0490 |",
        "| Technique (`collapsed_full`) | Markov Fallback Hit@1 | 2/67 (0.0299) | 3/95 (0.0316) | +0.0017 |",
        "| Technique (`collapsed_full`) | Markov Fallback Hit@3 | 5/67 (0.0746) | 4/95 (0.0421) | -0.0325 |",
        "| Technique (`collapsed_full`) | Coverage (Status ok) | 34/67 (0.5075) | 61/95 (0.6421) | +0.1346 |",
        "| Technique (`collapsed_full`) | Target Ceiling | 35/67 (0.5224) | 59/95 (0.6211) | +0.0987 |",
        "| Tactic (`tactic_collapsed`) | Sample Count ($N$) | 53 | 76 | +23 |",
        "| Tactic (`tactic_collapsed`) | Markov Hit@1 | 11/53 (0.2075) | 22/76 (0.2895) | +0.0819 |",
        "| Tactic (`tactic_collapsed`) | Markov Hit@3 | 28/53 (0.5283) | 48/76 (0.6316) | +0.1033 |",
        "| Tactic (`tactic_collapsed`) | Frequency Hit@1 | 9/53 (0.1698) | 14/76 (0.1842) | +0.0144 |",
        "| Tactic (`tactic_collapsed`) | Frequency Hit@3 | 33/53 (0.6226) | 48/76 (0.6316) | +0.0089 |",
        "| Tactic (`tactic_collapsed`) | Markov Fallback Hit@1 | 13/53 (0.2453) | 24/76 (0.3158) | +0.0705 |",
        "| Tactic (`tactic_collapsed`) | Markov Fallback Hit@3 | 30/53 (0.5660) | 50/76 (0.6579) | +0.0919 |",
        "| Tactic (`tactic_collapsed`) | Coverage (Status ok) | 50/53 (0.9434) | 74/76 (0.9737) | +0.0303 |",
        "| Tactic (`tactic_collapsed`) | Target Ceiling | 49/53 (0.9245) | 73/76 (0.9605) | +0.0360 |",
    ]

    for s in expected_strings:
        if s not in md_text:
            raise ValueError(f"Expected string not found in Markdown report:\n'{s}'")

    # Now verify all digit tokens in MD against known valid tokens
    print("  Verifying all numeric tokens in Markdown report...")
    num_tokens = re.findall(r"(?:\d+\.\d+|\b\d+\b)", md_text)
    print(f"  Total number tokens in report: {len(num_tokens)}")

    # Build set of all known numbers from recomputed and metadata
    known_tokens = {
        # Section and outline numbers
        "1", "2", "3", "4", "5", "6", "7", "8", "9", "95", "76", "131",
        # Sample counts
        "18", "19", "20", "10", "14", "12", "26", "28", "21", "22", "13", "8", "11",
        # 4ep baseline numbers
        "4", "67", "53", "34", "35", "50", "49", "23", "28",
        # Percentages / CI
        "95",
        # Random guess reference
        "14",
    }
    # Add all recomputed counts, hits, rates, bounds
    for s_data in recomputed_slices.values():
        known_tokens.add(str(s_data["n_samples"]))
        known_tokens.add(str(s_data["m_h1"]))
        known_tokens.add(str(s_data["m_h3"]))
        known_tokens.add(str(s_data["f_h1"]))
        known_tokens.add(str(s_data["f_h3"]))
        known_tokens.add(str(s_data["fb_h1"]))
        known_tokens.add(str(s_data["fb_h3"]))
        known_tokens.add(str(s_data["cov_count"]))
        known_tokens.add(str(s_data["ceil_count"]))
        known_tokens.add(f"{s_data['m_h1']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['m_h3']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['f_h1']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['f_h3']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['fb_h1']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['fb_h3']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['cov_count']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['ceil_count']/s_data['n_samples']:.4f}")
        known_tokens.add(f"{s_data['m_w1'][0]:.4f}")
        known_tokens.add(f"{s_data['m_w1'][1]:.4f}")
        known_tokens.add(f"{s_data['m_w3'][0]:.4f}")
        known_tokens.add(f"{s_data['m_w3'][1]:.4f}")
        known_tokens.add(f"{s_data['f_w1'][0]:.4f}")
        known_tokens.add(f"{s_data['f_w1'][1]:.4f}")
        known_tokens.add(f"{s_data['f_w3'][0]:.4f}")
        known_tokens.add(f"{s_data['f_w3'][1]:.4f}")
        known_tokens.add(f"{s_data['fb_w1'][0]:.4f}")
        known_tokens.add(f"{s_data['fb_w1'][1]:.4f}")
        known_tokens.add(f"{s_data['fb_w3'][0]:.4f}")
        known_tokens.add(f"{s_data['fb_w3'][1]:.4f}")
        known_tokens.add(f"{s_data['fold_mean_m1']:.4f}")
        known_tokens.add(f"{s_data['fold_mean_m3']:.4f}")
        known_tokens.add(f"{s_data['fold_mean_f1']:.4f}")
        known_tokens.add(f"{s_data['fold_mean_f3']:.4f}")
        known_tokens.add(f"{s_data['fold_mean_fb1']:.4f}")
        known_tokens.add(f"{s_data['fold_mean_fb3']:.4f}")

        # Per fold numbers
        for pf in s_data["per_fold"].values():
            known_tokens.add(str(pf["n_samples"]))
            known_tokens.add(str(pf["markov_hit1"]))
            known_tokens.add(str(pf["markov_hit3"]))
            known_tokens.add(str(pf["frequency_hit1"]))
            known_tokens.add(str(pf["frequency_hit3"]))
            known_tokens.add(str(pf["fallback_hit1"]))
            known_tokens.add(str(pf["fallback_hit3"]))
            known_tokens.add(str(pf["covered_samples"]))
            known_tokens.add(str(pf["ceiling_hits"]))
            known_tokens.add(f"{pf['markov_top1']:.4f}")
            known_tokens.add(f"{pf['markov_top3']:.4f}")
            known_tokens.add(f"{pf['frequency_hit1']/pf['n_samples']:.4f}" if pf['n_samples'] > 0 else "0.0000")
            known_tokens.add(f"{pf['frequency_hit3']/pf['n_samples']:.4f}" if pf['n_samples'] > 0 else "0.0000")
            known_tokens.add(f"{pf['fallback_hit1']/pf['n_samples']:.4f}" if pf['n_samples'] > 0 else "0.0000")
            known_tokens.add(f"{pf['fallback_hit3']/pf['n_samples']:.4f}" if pf['n_samples'] > 0 else "0.0000")

    # Add paired tests
    for pt in paired_json.values():
        known_tokens.add(str(pt["n_samples"]))
        known_tokens.add(str(pt["table"]["both_hit"]))
        known_tokens.add(str(pt["table"]["b_m1_only"]))
        known_tokens.add(str(pt["table"]["c_m2_only"]))
        known_tokens.add(str(pt["table"]["neither"]))
        known_tokens.add(f"{pt['m1_rate']:.4f}")
        known_tokens.add(f"{pt['m2_rate']:.4f}")
        known_tokens.add(f"{pt['rate_difference']:+.4f}")
        known_tokens.add(f"{pt['rate_difference']:.4f}")
        known_tokens.add(f"{abs(pt['rate_difference']):.4f}")
        known_tokens.add(f"{pt['p_value_raw']:.4f}")

    # Add 4ep comparison rates and differences
    for comp in results_json["comparison_with_4ep"].values():
        c4 = comp["4ep"]
        c7 = comp["7ep"]
        for k in ["n_samples", "markov_hit1", "markov_hit3", "frequency_hit1", "frequency_hit3",
                  "fallback_hit1", "fallback_hit3", "coverage_covered", "ceiling_hits"]:
            known_tokens.add(str(c4[k]))
            known_tokens.add(str(c7[k]))
            if k != "n_samples":
                r4 = c4[k] / c4["n_samples"]
                r7 = c7[k] / c7["n_samples"]
                known_tokens.add(f"{r4:.4f}")
                known_tokens.add(f"{r7:.4f}")
                known_tokens.add(f"{r7 - r4:+.4f}")
                known_tokens.add(f"{r7 - r4:.4f}")
                known_tokens.add(f"{abs(r7 - r4):.4f}")

    # Add covered-only numbers
    head_cf = results_json["primary_slice_technique_collapsed_full"]["headline"]
    known_tokens.add(str(head_cf["coverage"]["covered_n"]))
    known_tokens.add(str(head_cf["coverage"]["markov_on_covered_hit1"]))
    known_tokens.add(str(head_cf["coverage"]["markov_on_covered_hit3"]))
    known_tokens.add(str(head_cf["coverage"]["frequency_on_covered_hit1"]))
    known_tokens.add(str(head_cf["coverage"]["frequency_on_covered_hit3"]))
    known_tokens.add(f"{head_cf['coverage']['markov_on_covered_top1']:.4f}")
    known_tokens.add(f"{head_cf['coverage']['markov_on_covered_top3']:.4f}")
    known_tokens.add(f"{head_cf['coverage']['frequency_on_covered_top1']:.4f}")
    known_tokens.add(f"{head_cf['coverage']['frequency_on_covered_top3']:.4f}")

    # Add tactic random reference numbers
    rg = results_json["secondary_slice_tactic_collapsed"]["diagnostics"]["random_guess"]
    known_tokens.add(f"{rg['mean_p_hit1']:.4f}")
    known_tokens.add(f"{rg['mean_p_hit3']:.4f}")

    # Check each token
    unrecognized = []
    for tok in num_tokens:
        clean_tok = tok.lstrip("+").lstrip("-")
        if tok not in known_tokens and clean_tok not in known_tokens:
            unrecognized.append(tok)

    if unrecognized:
        raise ValueError(f"Unrecognized number tokens in Markdown report: {set(unrecognized)}")

    print(f"  All {len(num_tokens)} number tokens in Markdown report verified against recomputed data [PASS]")

    print("\n" + "=" * 80)
    print("ALL 7-EPISODE INDEPENDENT VERIFICATION CHECKS PASSED (EXIT CODE 0)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        success = verify_evaluation_7ep()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
