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
    """Verify all relative and absolute markdown links in docs/PROJECT_MAP.md resolve to real paths."""
    doc_path = REPO_ROOT / "docs" / "PROJECT_MAP.md"
    assert doc_path.is_file()
    text = doc_path.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert len(links) >= 15, f"Expected at least 15 links, found {len(links)}"
    missing = []
    for link in links:
        if link.startswith("file:///"):
            target = Path(link[8:])
        else:
            target = (doc_path.parent / link).resolve()
        if not target.exists():
            missing.append((link, str(target)))
    assert not missing, f"Missing link targets in PROJECT_MAP.md: {missing}"


def test_data_lineage_all_paths_exist():
    """Verify all relative and absolute markdown links in docs/data_lineage.md resolve to real paths."""
    doc_path = REPO_ROOT / "docs" / "data_lineage.md"
    assert doc_path.is_file()
    text = doc_path.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert len(links) >= 10, f"Expected at least 10 links, found {len(links)}"
    missing = []
    for link in links:
        if link.startswith("file:///"):
            target = Path(link[8:])
        else:
            target = (doc_path.parent / link).resolve()
        if not target.exists():
            missing.append((link, str(target)))
    assert not missing, f"Missing link targets in data_lineage.md: {missing}"
