"""tests/test_lineage_doc.py (Prompt 17 Part T1).

Automated verification of docs/data_lineage.md:
1. Every file path referenced in the markdown exists on disk.
2. Every raw archive name in Section 1 matches an actual file on disk under data/raw/.
3. No row repeats an identical verification-method string unless the same script actually covers both outputs.
"""
from __future__ import annotations

import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LINEAGE_MD_PATH = REPO_ROOT / "docs" / "data_lineage.md"


def test_lineage_file_exists():
    assert LINEAGE_MD_PATH.is_file(), f"Lineage document missing: {LINEAGE_MD_PATH}"


def test_every_path_in_lineage_doc_exists():
    content = LINEAGE_MD_PATH.read_text(encoding="utf-8")
    
    # Extract markdown links: [text](../path) or [`path`](../path)
    links = re.findall(r"\[.*?\]\(\.\./([^\)]+)\)", content)
    assert len(links) > 0, "No relative links found in data_lineage.md"
    
    missing_paths = []
    for rel_link in links:
        # Strip anchors if any
        target_path = rel_link.split("#")[0]
        full_p = REPO_ROOT / target_path
        if not full_p.exists():
            missing_paths.append(target_path)
            
    assert not missing_paths, f"Referenced file paths missing on disk: {missing_paths}"


def test_every_archive_name_matches_file_on_disk():
    content = LINEAGE_MD_PATH.read_text(encoding="utf-8")
    
    # Find all zip files mentioned
    zip_matches = re.findall(r"`([a-zA-Z0-9_\-]+\.zip)`", content)
    assert len(zip_matches) > 0, "No zip archive names found in doc"
    
    raw_dir = REPO_ROOT / "data" / "raw"
    actual_zips = {p.name for p in raw_dir.glob("*.zip")}
    
    for zip_name in zip_matches:
        assert zip_name in actual_zips, f"Archive {zip_name} cited in doc does not exist under data/raw/"


def test_verification_method_distinctness_and_coverage():
    content = LINEAGE_MD_PATH.read_text(encoding="utf-8")
    
    # Parse rows in the Pipeline Stage Lineage Matrix table
    matrix_lines = []
    in_matrix = False
    for line in content.splitlines():
        if "Pipeline Stage Lineage Matrix" in line:
            in_matrix = True
            continue
        if in_matrix and line.startswith("|"):
            if "Stage Description" not in line and ":---" not in line:
                matrix_lines.append(line)
        elif in_matrix and line.startswith("##"):
            break

    assert len(matrix_lines) >= 20, f"Expected at least 20 stages, found {len(matrix_lines)}"

    verifier_to_outputs: dict[str, list[str]] = {}
    for line in matrix_lines:
        parts = [p.strip() for p in line.split("|")[1:-1]]
        if len(parts) >= 6:
            out_file = parts[3]
            verifier = parts[5]
            # Extract plain text from markdown links
            out_m = re.search(r"\[`([^`]+)`\]", out_file)
            ver_m = re.search(r"\[`([^`]+)`\]", verifier)
            out_clean = out_m.group(1) if out_m else out_file
            ver_clean = ver_m.group(1) if ver_m else verifier
            
            verifier_to_outputs.setdefault(ver_clean, []).append(out_clean)

    # Verify: if a verifier is shared, it must actually cover all associated output files
    for verifier, outputs in verifier_to_outputs.items():
        if verifier == "`none`" or verifier == "none":
            continue
        v_path = REPO_ROOT / verifier
        assert v_path.is_file(), f"Verifier script {verifier} missing on disk"
        v_content = v_path.read_text(encoding="utf-8")
        
        # Check that verifier covers each associated output
        for out in outputs:
            fname = Path(out).name
            assert (fname in v_content or Path(out).stem in v_content), (
                f"Verifier {verifier} is assigned to output {out}, but does not reference it"
            )
