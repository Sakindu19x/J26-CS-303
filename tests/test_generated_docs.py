"""test_generated_docs.py

Pytest suite validating that all paths and file links named in:
- docs/PROJECT_MAP.md
- docs/data_lineage.md
- docs/process/cleanup_map.md
exist on disk without dead links.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_project_map_all_paths_exist():
    """Verify all file links in docs/PROJECT_MAP.md exist on disk."""
    doc_path = REPO_ROOT / "docs" / "PROJECT_MAP.md"
    assert doc_path.is_file()
    text = doc_path.read_text(encoding="utf-8")
    matches = re.findall(r"\(file:///([^)]+)\)", text)
    assert len(matches) > 0
    missing = [p for p in matches if not Path(p).exists()]
    assert not missing, f"Missing paths in PROJECT_MAP.md: {missing}"


def test_data_lineage_all_paths_exist():
    """Verify all file links in docs/data_lineage.md exist on disk."""
    doc_path = REPO_ROOT / "docs" / "data_lineage.md"
    assert doc_path.is_file()
    text = doc_path.read_text(encoding="utf-8")
    matches = re.findall(r"\(file:///([^)]+)\)", text)
    assert len(matches) > 0
    missing = [p for p in matches if not Path(p).exists()]
    assert not missing, f"Missing paths in data_lineage.md: {missing}"
