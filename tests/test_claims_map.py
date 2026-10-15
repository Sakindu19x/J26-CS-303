"""test_claims_map.py

Pytest suite for reports/viva/claims.json and claims_to_evidence_map.md (Prompt 14 Q5).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_claims_map import verify_claims_map


def test_verify_claims_map_independent_verifier():
    """Verify that independent verifier passes completely without errors."""
    verify_claims_map()


def test_claims_required_set_and_placeholders():
    """Verify required claims, anchors, and reproducibility wording."""
    import json
    with open(REPO_ROOT / "reports" / "viva" / "claims.json", "r", encoding="utf-8") as f:
        claims = json.load(f)
    assert len(claims) == 13
    names = {c["name"] for c in claims}
    assert "pipeline_reproducibility" in names
    c1 = next(c for c in claims if c["name"] == "pipeline_reproducibility")
    assert "verified" in c1["template"] or "not proven" in c1["template"]


def test_forbidden_permutation_p_values_guard():
    """Verify that no Markov-Frequency difference permutation p-value appears in claims."""
    import json
    import re
    claims_text = (REPO_ROOT / "reports" / "viva" / "claims.json").read_text(encoding="utf-8")
    md_text = (REPO_ROOT / "reports" / "viva" / "claims_to_evidence_map.md").read_text(encoding="utf-8")

    perm_path = REPO_ROOT / "reports" / "7ep" / "permutation_7ep_report.json"
    with open(perm_path, "r", encoding="utf-8") as f:
        pj = json.load(f)

    for scheme in pj.get("schemes", {}).values():
        for slice_data in scheme.values():
            for k, val in slice_data.items():
                if "markov_minus_frequency" in k:
                    pval = val.get("p_value")
                    if pval is not None:
                        token = f"{pval:.4f}"
                        assert not re.search(rf"\b{re.escape(token)}\b", claims_text), f"Forbidden {token} found in claims.json"
                        assert not re.search(rf"\b{re.escape(token)}\b", md_text), f"Forbidden {token} found in claims_to_evidence_map.md"
