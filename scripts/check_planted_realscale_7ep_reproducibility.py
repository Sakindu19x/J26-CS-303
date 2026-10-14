r"""Twice-run byte-identical hash check for 7-Episode Planted-Structure Power Analysis (A4 at 7ep)."""
import hashlib
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
CSV_PATH = BASE_DIR / "data" / "processed_7ep" / "planted_realscale_7ep_predictions.csv"
JSON_PATH = BASE_DIR / "reports" / "7ep" / "planted_realscale_7ep_report.json"
MD_PATH = BASE_DIR / "reports" / "7ep" / "planted_realscale_7ep_report.md"


def get_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("Running Run 1...")
    res1 = subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "run_planted_realscale_7ep.py")], check=True)
    h_csv_1 = get_hash(CSV_PATH)
    h_json_1 = get_hash(JSON_PATH)
    h_md_1 = get_hash(MD_PATH)

    print(f"Run 1 hashes:\n  CSV : {h_csv_1}\n  JSON: {h_json_1}\n  MD  : {h_md_1}")

    print("\nRunning Run 2...")
    res2 = subprocess.run([sys.executable, str(BASE_DIR / "scripts" / "run_planted_realscale_7ep.py")], check=True)
    h_csv_2 = get_hash(CSV_PATH)
    h_json_2 = get_hash(JSON_PATH)
    h_md_2 = get_hash(MD_PATH)

    print(f"Run 2 hashes:\n  CSV : {h_csv_2}\n  JSON: {h_json_2}\n  MD  : {h_md_2}")

    print("\nComparison:")
    print(f"  CSV  MATCH? {h_csv_1 == h_csv_2}")
    print(f"  JSON MATCH? {h_json_1 == h_json_2}")
    print(f"  MD   MATCH? {h_md_1 == h_md_2}")

    assert h_csv_1 == h_csv_2, "CSV hash mismatch between runs!"
    assert h_json_1 == h_json_2, "JSON hash mismatch between runs!"
    assert h_md_1 == h_md_2, "MD hash mismatch between runs!"
    print("ALL A4-7EP ARTIFACTS BYTE-IDENTICAL ACROSS BOTH RUNS!")


if __name__ == "__main__":
    main()
