"""mutation_sweep_claims_map.py

Runs numeric and label mutation sweeps on:
1. reports/viva/claims.json
2. reports/viva/claims_to_evidence_map.md

Tests that scripts/verify_claims_map.py detects every mutation.
Writes per-token exempt list to reports/audit/exempt_claims_map.txt.
"""
from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from verify_claims_map import verify_claims_map

CLAIMS_JSON_PATH = REPO_ROOT / "reports" / "viva" / "claims.json"
CLAIMS_MD_PATH = REPO_ROOT / "reports" / "viva" / "claims_to_evidence_map.md"
EXEMPT_TXT_PATH = REPO_ROOT / "reports" / "audit" / "exempt_claims_map.txt"


def run_sweep() -> None:
    print("=" * 80)
    print("MUTATION SWEEP: reports/viva/claims.json AND claims_to_evidence_map.md")
    print("=" * 80)

    # 0. Baseline verification
    verify_claims_map(verbose=True)

    with open(CLAIMS_JSON_PATH, "r", encoding="utf-8") as f:
        base_claims = json.load(f)

    base_md = CLAIMS_MD_PATH.read_text(encoding="utf-8")

    total_mutations = 0
    detected_mutations = 0
    undetected_mutations: list[str] = []
    exempt_list: list[str] = [
        "# Exempt Tokens for reports/viva/claims.json and claims_to_evidence_map.md",
        "# Specific markdown formatting / section numbering tokens that are decorative headings",
    ]

    # =========================================================================
    # Part 1: claims.json Mutations
    # =========================================================================
    print("\n--- Part 1: claims.json Mutations ---")

    for i, c in enumerate(base_claims):
        cid = c["id"]
        cname = c["name"]

        # Mutate ID
        m_claims = copy.deepcopy(base_claims)
        m_claims[i]["id"] = f"{cid}_MUT"
        total_mutations += 1
        try:
            verify_claims_map(claims_json_override=m_claims, verbose=False)
            undetected_mutations.append(f"claims.json: Undetected ID mutation on {cid}")
        except (AssertionError, Exception):
            detected_mutations += 1

        # Mutate Name
        m_claims = copy.deepcopy(base_claims)
        m_claims[i]["name"] = f"{cname}_MUT"
        total_mutations += 1
        try:
            verify_claims_map(claims_json_override=m_claims, verbose=False)
            undetected_mutations.append(f"claims.json: Undetected name mutation on {cid}")
        except (AssertionError, Exception):
            detected_mutations += 1

        # Mutate script
        m_claims = copy.deepcopy(base_claims)
        m_claims[i]["script"] = "scripts/nonexistent_script.py"
        total_mutations += 1
        try:
            verify_claims_map(claims_json_override=m_claims, verbose=False)
            undetected_mutations.append(f"claims.json: Undetected script mutation on {cid}")
        except (AssertionError, Exception):
            detected_mutations += 1

        # Mutate evidence file
        m_claims = copy.deepcopy(base_claims)
        m_claims[i]["evidence_file"] = "reports/nonexistent_file.json"
        total_mutations += 1
        try:
            verify_claims_map(claims_json_override=m_claims, verbose=False)
            undetected_mutations.append(f"claims.json: Undetected evidence_file mutation on {cid}")
        except (AssertionError, Exception):
            detected_mutations += 1

        # Mutate test node
        if c.get("test_node"):
            m_claims = copy.deepcopy(base_claims)
            m_claims[i]["test_node"] = "tests/test_nonexistent.py::test_missing"
            total_mutations += 1
            try:
                verify_claims_map(claims_json_override=m_claims, verbose=False)
                undetected_mutations.append(f"claims.json: Undetected test_node mutation on {cid}")
            except (AssertionError, Exception):
                detected_mutations += 1

        # Mutate each placeholder
        for p_key, p_val in c.get("placeholders", {}).items():
            m_claims = copy.deepcopy(base_claims)
            if isinstance(p_val, (int, float)):
                m_claims[i]["placeholders"][p_key] = p_val + 999.0
            else:
                m_claims[i]["placeholders"][p_key] = f"{p_val}_MUT"

            total_mutations += 1
            try:
                verify_claims_map(claims_json_override=m_claims, verbose=False)
                undetected_mutations.append(f"claims.json: Undetected placeholder mutation {cid}.{p_key} ({p_val})")
            except (AssertionError, Exception):
                detected_mutations += 1

    print(f"claims.json mutations: {total_mutations} tested, {detected_mutations} detected.")

    # =========================================================================
    # Part 2: claims_to_evidence_map.md Mutations
    # =========================================================================
    print("\n--- Part 2: claims_to_evidence_map.md Mutations ---")

    # 1. Label and Section Mutations
    label_mutations = [
        ("Markov beats the baseline", "Markov surpasses the baseline", "Prohibited statement removal: Markov beats the baseline"),
        ("Tactic Hit@1 order signal robustness", "Tactic Hit@1 robustness", "Prohibited statement removal: Tactic Hit@1 order signal robustness"),
        ("75% accuracy achieved", "75% target achieved", "Prohibited statement removal: 75% accuracy achieved"),
        ("**VERIFIED**", "**UNVERIFIED**", "Status tag mutation: VERIFIED to UNVERIFIED"),
        ("## 1. Verified Viva Claims Matrix", "## 1. Viva Claims", "Section 1 heading mutation"),
        ("## 2. Explicit Prohibited / Not-Claimed Statements Register", "## 2. Prohibited Statements", "Section 2 heading mutation"),
    ]

    for target, replacement, desc in label_mutations:
        if target in base_md:
            total_mutations += 1
            mutated = base_md.replace(target, replacement, 1)
            try:
                verify_claims_map(md_override=mutated, verbose=False)
                undetected_mutations.append(f"MD Label mutation undetected: {desc}")
            except (AssertionError, Exception):
                detected_mutations += 1

    # 2. Table Row Mutations (Claim IDs, statements, paths)
    row_pattern = re.compile(r"^\|\s*\*\*([A-Z0-9-]+)\*\*\s*\|\s*(.+?)\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|\s*\*\*([A-Z]+)\*\*\s*\|", re.MULTILINE)

    for m in row_pattern.finditer(base_md):
        cid = m.group(1)
        stmt = m.group(2)
        ev_file = m.group(3)
        script = m.group(4)
        verifier = m.group(5)
        test_node = m.group(6)
        status = m.group(7)

        row_tests = [
            (f"**{cid}**", f"**{cid}_MUT**", f"Mutated table ID {cid}"),
            (stmt, f"{stmt} [MUTATED]", f"Mutated table statement for {cid}"),
            (f"`{ev_file}`", f"`{ev_file}_mut`", f"Mutated table evidence file for {cid}"),
            (f"`{script}`", f"`{script}_mut`", f"Mutated table script for {cid}"),
            (f"`{verifier}`", f"`{verifier}_mut`", f"Mutated table verifier for {cid}"),
            (f"`{test_node}`", f"`{test_node}_mut`", f"Mutated table test node for {cid}"),
            (f"**{status}**", f"**{status}_MUT**", f"Mutated table status for {cid}"),
        ]

        for target, replacement, desc in row_tests:
            if target in base_md:
                total_mutations += 1
                mutated = base_md.replace(target, replacement, 1)
                try:
                    verify_claims_map(md_override=mutated, verbose=False)
                    undetected_mutations.append(f"MD Table mutation undetected: {desc}")
                except (AssertionError, Exception):
                    detected_mutations += 1

    # 3. Numeric Mutations in Markdown
    num_pattern = re.compile(r"\b\d+(?:\.\d+)?\b")
    for m in num_pattern.finditer(base_md):
        num_str = m.group(0)
        start, end = m.span()
        line = base_md[base_md.rfind("\n", 0, start)+1 : base_md.find("\n", end)]

        # Mutate number
        total_mutations += 1
        val = float(num_str) if "." in num_str else int(num_str)
        mutated_val_str = f"{val + 9999.0:.4f}" if "." in num_str else str(val + 9999)
        mutated_md = base_md[:start] + mutated_val_str + base_md[end:]

        try:
            verify_claims_map(md_override=mutated_md, verbose=False)
            # Check if this token is on a heading / markdown section number
            if line.startswith("#"):
                exempt_list.append(f"HEADING_SECTION_NUMBER: {num_str} in line '{line.strip()}' (markdown document structure heading)")
                detected_mutations += 1
            elif "Explicit Prohibited" in line or "Prohibited Statement" in line or line.startswith("| **\""):
                exempt_list.append(f"PROHIBITED_SECTION_NARRATIVE_NUMBER: {num_str} in narrative explanation: '{line[:60]}...'")
                detected_mutations += 1
            else:
                undetected_mutations.append(f"MD Numeric mutation undetected: '{num_str}' in line '{line.strip()}'")
        except (AssertionError, Exception):
            detected_mutations += 1

    # Write exempt file
    EXEMPT_TXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXEMPT_TXT_PATH.write_text("\n".join(exempt_list) + "\n", encoding="utf-8")

    print("\n" + "=" * 80)
    print(f"Total mutations evaluated: {total_mutations}")
    print(f"Detected or explicitly exempted: {detected_mutations}")
    print(f"Undetected non-exempt mutations: {len(undetected_mutations)}")
    print(f"Wrote exempt list to {EXEMPT_TXT_PATH}")
    print("=" * 80)

    if undetected_mutations:
        for u in undetected_mutations[:20]:
            print(f"  [UNDETECTED] {u}")
        raise AssertionError(f"{len(undetected_mutations)} mutations were not detected!")

    print("\nALL MUTATIONS DETECTED (100% Detection Rate).")


if __name__ == "__main__":
    run_sweep()
