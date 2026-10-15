"""Driver script to execute secondary next-tactic LOEO evaluation."""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR / "src"))

from c4.tactic_evaluation import run_full_tactic_evaluation


def main() -> None:
    print("Running secondary next-tactic LOEO cross-validation evaluation...")
    payload = run_full_tactic_evaluation()
    print("Secondary tactic evaluation completed successfully.")
    for s_name in ("tactic_collapsed", "tactic_raw"):
        s = payload["slices"][s_name]
        print(f"\nHeadline metrics for {s_name} (N={s['n_samples']}):")
        print(f"  Markov Top-1: {s['headline']['markov']['top1']*100:.2f}% ({s['headline']['markov']['hit1']}/{s['n_samples']})")
        print(f"  Markov Top-3: {s['headline']['markov']['top3']*100:.2f}% ({s['headline']['markov']['hit3']}/{s['n_samples']})")
        print(f"  Frequency Top-1: {s['headline']['frequency']['top1']*100:.2f}% ({s['headline']['frequency']['hit1']}/{s['n_samples']})")
        print(f"  Frequency Top-3: {s['headline']['frequency']['top3']*100:.2f}% ({s['headline']['frequency']['hit3']}/{s['n_samples']})")
        print(f"  Repeat-current-set Top-1: {s['diagnostics']['repeat_current_set']['top1']*100:.2f}% ({s['diagnostics']['repeat_current_set']['hit1']}/{s['n_samples']})")
        print(f"  Random-guess expected Top-1: {s['diagnostics']['random_guess']['mean_p_hit1']*100:.2f}%")


if __name__ == "__main__":
    main()
