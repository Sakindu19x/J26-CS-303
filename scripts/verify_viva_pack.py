"""Token and Content Verifier for Viva Pack Documents (P9).

Verifies that:
1. All viva pack documents and figures exist with non-zero size.
2. Numbers, hashes, and metrics in 01_dataset.md, 02_split_and_training.md, and 03_scores.md
   match source JSON artifacts exactly.
3. Missing metrics (confusion matrix, error analysis) are explicitly marked as MISSING.
4. Image figures are valid PNG files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VIVA_DIR = REPO_ROOT / "viva_pack"
FIG_DIR = VIVA_DIR / "05_figures"

REQUIRED_DOCS = [
    "README.md",
    "01_dataset.md",
    "02_split_and_training.md",
    "03_scores.md",
    "04_worked_examples.md",
    "06_claims_and_limits.md",
    "07_reproduce.md",
]

REQUIRED_FIGS = [
    "learning_curve_7ep.png",
    "a4_power_curve.png",
    "loeo_performance_bar_chart.png",
]


def verify_viva_pack() -> int:
    print("--- Verifying Viva Pack Documents and Figures ---")
    errors = []

    # 1. Existence and non-empty check
    for doc in REQUIRED_DOCS:
        p = VIVA_DIR / doc
        if not p.is_file() or p.stat().st_size == 0:
            errors.append(f"Missing or empty document: {p}")
        else:
            print(f"  [OK] Document exists: {doc} ({p.stat().st_size} bytes)")

    for fig in REQUIRED_FIGS:
        p = FIG_DIR / fig
        if not p.is_file() or p.stat().st_size == 0:
            errors.append(f"Missing or empty figure: {p}")
        else:
            # Check PNG header
            header = p.read_bytes()[:8]
            if header != b"\x89PNG\r\n\x1a\n":
                errors.append(f"Invalid PNG header in figure: {p}")
            else:
                print(f"  [OK] Valid PNG figure: {fig} ({p.stat().st_size} bytes)")

    # 2. Token & metric parity checks
    # Load source JSONs
    with open(REPO_ROOT / "reports" / "7ep" / "evaluation_7ep_results.json", "r", encoding="utf-8") as f:
        eval_data = json.load(f)
    with open(REPO_ROOT / "artifacts" / "7ep" / "fold_models" / "manifest.json", "r", encoding="utf-8") as f:
        fold_manifest = json.load(f)

    # Check 01_dataset.md
    d01_text = (VIVA_DIR / "01_dataset.md").read_text(encoding="utf-8")
    for expected_hash in [
        "0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc",
        "b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791",
        "346919e2d23dd2937043de5f906e9e973a5b0860a85c99916a96cdc57ea6a9cd",
        "81f1e68e4c896cc31d5b16eba00c2c89be317887165d50e653635330d8a76e53",
    ]:
        if expected_hash not in d01_text:
            errors.append(f"Expected hash {expected_hash} not found in 01_dataset.md")

    # Check 02_split_and_training.md
    d02_text = (VIVA_DIR / "02_split_and_training.md").read_text(encoding="utf-8")
    for ep in ["E1", "E2", "E3", "E4", "E5", "E6", "E7"]:
        m_rel = f"artifacts/7ep/fold_models/collapsed_full/{ep}.json"
        m_sha_prefix = fold_manifest["files"][m_rel]["sha256"][:16]
        if m_sha_prefix not in d02_text:
            errors.append(f"Expected model hash prefix {m_sha_prefix} for {ep} not found in 02_split_and_training.md")

    if "counting" not in d02_text.lower():
        errors.append("Principle of counting not documented in 02_split_and_training.md")

    # Check 03_scores.md
    d03_text = (VIVA_DIR / "03_scores.md").read_text(encoding="utf-8")
    tech_h = eval_data["primary_slice_technique_collapsed_full"]["headline"]
    tac_h = eval_data["secondary_slice_tactic_collapsed"]["headline"]

    expected_tokens = [
        f"{tech_h['markov']['top1']*100:.2f}%",
        f"{tech_h['frequency']['top1']*100:.2f}%",
        f"{tech_h['markov']['top3']*100:.2f}%",
        f"{tech_h['frequency']['top3']*100:.2f}%",
        f"{tac_h['markov']['top1']*100:.2f}%",
        f"{tac_h['frequency']['top1']*100:.2f}%",
        f"{tac_h['markov']['top3']*100:.2f}%",
        f"{tac_h['frequency']['top3']*100:.2f}%",
        "62.11%",
        "64.21%",
        "64.98%",
        "Status: MISSING",
    ]
    for tok in expected_tokens:
        if tok not in d03_text:
            errors.append(f"Expected score token '{tok}' not found in 03_scores.md")

    if errors:
        print("\n[FAIL] Viva pack verification encountered errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("\n[PASS] All viva pack documents, figures, and tokens verified successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(verify_viva_pack())
