"""Generate reports/_baseline_hashes_7ep_inference.json for Prompt 12b inference outputs."""
import hashlib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

INFERENCE_FILES = [
    "data/processed_7ep/learning_curve_7ep.csv",
    "reports/7ep/learning_curve_7ep_results.json",
    "reports/7ep/learning_curve_7ep_report.md",
    "reports/7ep/learning_curve_7ep.png",
    "reports/7ep/learning_curve_7ep_plot_data.json",
    "data/processed_7ep/permutation_7ep_null_distribution.csv",
    "reports/7ep/permutation_7ep_report.json",
    "reports/7ep/permutation_7ep_report.md",
    "data/processed_7ep/planted_realscale_7ep_predictions.csv",
    "reports/7ep/planted_realscale_7ep_report.json",
    "reports/7ep/planted_realscale_7ep_report.md",
    "data/processed_7ep/e5_removed_predictions.csv",
    "reports/7ep/e5_removed_results.json",
    "reports/7ep/e5_removed_report.md",
    "reports/7ep/holm_claim_rule_results.json",
    "reports/7ep/holm_claim_rule_report.md",
    "reports/7ep/diagnostics_7ep.json",
    "reports/7ep/diagnostics_7ep.md",
]

hashes = {}
for rel_path in INFERENCE_FILES:
    file_path = BASE_DIR / rel_path
    if not file_path.is_file():
        raise FileNotFoundError(f"Missing expected file: {file_path}")
    h = hashlib.sha256(file_path.read_bytes()).hexdigest()
    hashes[rel_path] = h
    print(f"  {rel_path:<60} {h}")

out_path = BASE_DIR / "reports" / "_baseline_hashes_7ep_inference.json"
out_path.write_text(json.dumps(hashes, indent=2), encoding="utf-8")
print(f"\nWrote {len(hashes)} hashes to {out_path}")
