import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from c4.attack_sequence import attack_sequence
from c4.data_loading import EXPECTED_ARCHIVES, check_archive
from c4.episodes import segment_by_gap, split_by_run
from c4.inventory import build_inventory, write_reports
from c4.normalization import normalize_timestamps
from c4.timeline import build_timeline


def test_missing_archives_reported(tmp_path):
    inv = build_inventory(tmp_path)
    missing = [i["file"] for i in inv["issues"] if i["type"] == "missing_archive"]
    assert len(missing) == len(EXPECTED_ARCHIVES)
    assert inv["archives_present"] == []


def test_reads_synthetic_zip_without_modifying(tmp_path):
    z = tmp_path / "scenario_4.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("run_a/attackmate.json", json.dumps({"k": 1}))
        zf.writestr("run_a/auth.log", "2024-01-01T00:00:00Z host sshd ok\n")
    before = z.read_bytes()
    inv = build_inventory(tmp_path)
    j, m = write_reports(inv, tmp_path / "rep")
    assert j.exists() and m.exists()
    assert check_archive(z).readable
    assert z.read_bytes() == before


def test_unreadable_archive(tmp_path):
    (tmp_path / "scenario_4.zip").write_bytes(b"not a zip")
    inv = build_inventory(tmp_path)
    assert any(i["type"] == "unreadable_archive" for i in inv["issues"])


def test_runs_not_merged_and_unlabeled_skipped():
    df = pd.DataFrame({
        "run_id": ["a", "a", "b"],
        "timestamp_utc": normalize_timestamps(pd.Series(["2024-01-01T00:00:00Z", "2024-01-01T00:00:10Z", "2024-01-02T00:00:00Z"])),
        "attack_label": ["T1", None, "T2"],
    })
    runs = split_by_run(df)
    assert set(runs) == {"a", "b"}
    assert attack_sequence(build_timeline(runs["a"])) == ["T1"]
    assert segment_by_gap(runs["a"]).tolist() == [0, 0]
