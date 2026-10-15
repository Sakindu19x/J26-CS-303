"""Batch script to run full LOEO cross-validation evaluation and generate reports and figures."""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to pythonpath
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from c4.evaluation import run_full_evaluation


def main() -> None:
    print("Running full LOEO cross-validation evaluation across all configurations...")
    results = run_full_evaluation()
    print("Evaluation completed successfully.")
    print("Primary slice headline metrics:")
    head = results["primary_slice"]["headline"]
    print(f"  Markov Top-1: {head['markov']['top1']*100:.2f}% ({head['markov']['hit1']}/{results['primary_slice']['n_samples']})")
    print(f"  Markov Top-3: {head['markov']['top3']*100:.2f}% ({head['markov']['hit3']}/{results['primary_slice']['n_samples']})")
    print(f"  Frequency Top-1: {head['frequency']['top1']*100:.2f}% ({head['frequency']['hit1']}/{results['primary_slice']['n_samples']})")
    print(f"  Frequency Top-3: {head['frequency']['top3']*100:.2f}% ({head['frequency']['hit3']}/{results['primary_slice']['n_samples']})")
    print(f"  Markov Coverage: {head['coverage']['coverage_rate']*100:.2f}% ({head['coverage']['covered_samples']}/{results['primary_slice']['n_samples']})")
    print(f"  Target Ceiling: {head['ceiling']['ceiling_rate']*100:.2f}% ({head['ceiling']['hits']}/{results['primary_slice']['n_samples']})")


if __name__ == "__main__":
    main()
