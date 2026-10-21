"""Verify all dashboard color tokens meet WCAG 2.1 AA contrast ratio >= 4.5:1.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from c4.dashboard.theme import verify_all_tokens_contrast


def main() -> int:
    print("=" * 80)
    print("WCAG 2.1 AA COLOR CONTRAST VERIFICATION (min ratio >= 4.5:1)")
    print("=" * 80)
    
    results = verify_all_tokens_contrast(min_ratio=4.5)
    failures = []
    
    for pair, ratio, passed in results:
        status_str = "[PASS]" if passed else "[FAIL]"
        print(f"  {status_str} {pair.name:<25} ({pair.theme}): text={pair.text_color} bg={pair.bg_color} ratio={ratio:.2f}:1")
        if not passed:
            failures.append((pair.name, ratio))
            
    print("=" * 80)
    if failures:
        print(f"FAIL: {len(failures)} tokens failed WCAG 4.5:1 threshold: {failures}")
        return 1
    else:
        print(f"ALL {len(results)} THEME TOKEN PAIRS SATISFY WCAG 2.1 AA (>= 4.5:1).")
        return 0


if __name__ == "__main__":
    sys.exit(main())
