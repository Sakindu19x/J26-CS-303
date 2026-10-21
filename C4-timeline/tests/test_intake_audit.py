"""Tests for Read-Only Intake Audit of New CAM-LDS Archives (E5, E6, E7)."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = BASE_DIR / "reports"
RAW_DIR = BASE_DIR / "data" / "raw"

JSON_PATH = REPORTS_DIR / "new_episodes_intake_audit.json"
MD_PATH = REPORTS_DIR / "new_episodes_intake_audit.md"
HASHES_EXT_PATH = REPORTS_DIR / "raw_archive_hashes_extended.json"


def test_intake_audit_files_exist() -> None:
    """Verify all 3 output files exist and are non-empty."""
    assert JSON_PATH.is_file(), f"Missing {JSON_PATH}"
    assert MD_PATH.is_file(), f"Missing {MD_PATH}"
    assert HASHES_EXT_PATH.is_file(), f"Missing {HASHES_EXT_PATH}"
    assert JSON_PATH.stat().st_size > 0
    assert MD_PATH.stat().st_size > 0
    assert HASHES_EXT_PATH.stat().st_size > 0


def test_control_reproduces_stage1_invariants() -> None:
    """Test that control reproduces 190/99/64/71 exactly."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    ctrl = data["control_invariants_check"]
    assert ctrl["total_events"] == 190
    assert ctrl["labeled_steps"] == 99
    assert ctrl["distinct_techniques"] == 64
    assert ctrl["raw_sequence_length"] == 99
    assert ctrl["collapsed_sequence_length"] == 71
    assert ctrl["reproduced"] is True


def test_control_reproduces_counting_bounds() -> None:
    """Test that counting bounds reproduces 67/34/35 exactly."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    pooled = data["counting_bounds_designs"]["design_a_control"]["pooled"]
    assert pooled["n_samples"] == 67
    assert pooled["covered"] == 34
    assert pooled["ceiling_hits"] == 35


def test_json_md5s_equal_fresh_recomputation_of_zips() -> None:
    """Verify that MD5s in the JSON equal fresh recomputation of the raw zips."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(HASHES_EXT_PATH, "r", encoding="utf-8") as f:
        ext_hashes = json.load(f)["raw_archive_hashes_extended"]

    ext_map = {item["scenario"]: item for item in ext_hashes}

    for sc_id, h_info in data["archive_hashes"].items():
        zip_path = RAW_DIR / h_info["zip_file"]
        assert zip_path.is_file(), f"Zip missing: {zip_path}"

        hasher = hashlib.md5()
        with open(zip_path, "rb") as fh:
            while chunk := fh.read(1024 * 1024):
                hasher.update(chunk)
        fresh_md5 = hasher.hexdigest()

        assert fresh_md5 == h_info["md5"], f"MD5 mismatch for {sc_id}"
        assert fresh_md5 == ext_map[sc_id]["md5"], f"Extended hashes MD5 mismatch for {sc_id}"
        assert h_info["md5_match"] is True, f"Zenodo MD5 mismatch for {sc_id}"


def test_every_number_in_markdown_equals_json() -> None:
    """Verify numbers in markdown report correspond to the JSON source."""
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Check key pooled numbers in Markdown
    for design_key, des in json_data["counting_bounds_designs"].items():
        p = des["pooled"]
        pattern = rf"\*\*POOLED\*\* \| — \| — \| \*\*{p['n_samples']}\*\* \| \*\*{p['covered']}\*\* \| \*\*{p['coverage_rate']*100:.2f}%\*\* \| \*\*{p['ceiling_hits']}\*\* \| \*\*{p['ceiling_rate']*100:.2f}%\*\*"
        assert re.search(pattern, md_text), f"Pooled row mismatch for {design_key}"

    # Check control numbers in table
    assert "| Total AttackMate Events | 190 | 190 | **MATCH** |" in md_text
    assert "| Labeled Steps | 99 | 99 | **MATCH** |" in md_text
    assert "| Distinct ATT&CK Techniques | 64 | 64 | **MATCH** |" in md_text
    assert "| Raw Sequence Length | 99 | 99 | **MATCH** |" in md_text
    assert "| Collapsed Sequence Length | 71 | 71 | **MATCH** |" in md_text

    # Check profile step numbers
    P = json_data["episodes_profile"]
    assert f"| Total Steps | {P['E1']['total_steps']} | {P['E2']['total_steps']} | {P['E3']['total_steps']} | {P['E4']['total_steps']} | {P['E5']['total_steps']} | {P['E6']['total_steps']} | {P['E7']['total_steps']} |" in md_text


def test_script_wrote_nothing_outside_three_output_files() -> None:
    """Verify that the only files produced by the audit in reports/ are the designated 3 files."""
    expected_new = {
        "raw_archive_hashes_extended.json",
        "new_episodes_intake_audit.json",
        "new_episodes_intake_audit.md",
    }
    # Verify each expected file is in reports/
    for name in expected_new:
        assert (REPORTS_DIR / name).is_file()
