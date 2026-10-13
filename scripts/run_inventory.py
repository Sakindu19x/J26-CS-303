"""Generate reports/dataset_inventory.{json,md}. Usage: python scripts/run_inventory.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from c4.inventory import build_inventory, write_reports

if __name__ == "__main__":
    inv = build_inventory()
    j, m = write_reports(inv)
    print("Present:", inv["archives_present"] or "NONE")
    for i in inv["issues"]:
        print("ISSUE:", i)
    print("Wrote", j, "and", m)
