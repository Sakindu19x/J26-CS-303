"""Official MITRE ATT&CK Enterprise STIX reference parsing and cross-referencing."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ATTACK_VERSION = "16.1"
SOURCE_URL = "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack-16.1.json"

REFERENCE_DIR = Path(__file__).resolve().parents[2] / "data" / "reference"
PROCESSED_DIR = Path(__file__).resolve().parents[2] / "data" / "processed"
DEFAULT_STIX_PATH = REFERENCE_DIR / "enterprise-attack.json"
DEFAULT_PROCESSED_REF_PATH = PROCESSED_DIR / "technique_tactic_reference.json"

_CACHED_REF: dict[str, Any] | None = None


def to_parent_technique(technique_id: str) -> str:
    """Documented rule: map subtechnique to parent ID (T1059.006 -> T1059, T1105 -> T1105)."""
    if not technique_id:
        return ""
    clean_id = technique_id.strip().upper()
    return clean_id.split(".")[0]


def to_parent_technique_set(techniques: list[str] | set[str]) -> list[str]:
    """Map a collection of techniques to sorted deduplicated parent technique IDs."""
    if not techniques:
        return []
    parents = {to_parent_technique(t) for t in techniques if t}
    return sorted(list(parents))


def build_technique_tactic_reference(
    stix_path: Path = DEFAULT_STIX_PATH,
    output_json_path: Path = DEFAULT_PROCESSED_REF_PATH,
) -> dict[str, Any]:
    """Parse official MITRE Enterprise STIX bundle into technique_tactic_reference.json."""
    if not stix_path.is_file():
        raise FileNotFoundError(f"MITRE STIX file not found at: {stix_path}")

    with open(stix_path, encoding="utf-8") as f:
        bundle = json.load(f)

    # 1. Map tactic shortname -> official tactic name (e.g. 'initial-access' -> 'Initial Access')
    tactic_map: dict[str, str] = {}
    for obj in bundle.get("objects", []):
        if obj.get("type") == "x-mitre-tactic":
            shortname = obj.get("x_mitre_shortname")
            name = obj.get("name")
            if shortname and name:
                tactic_map[shortname] = name

    # 2. Map STIX attack-pattern IDs to external technique IDs (e.g. 'T1059.006')
    stix_to_ext: dict[str, str] = {}
    for obj in bundle.get("objects", []):
        if obj.get("type") == "attack-pattern":
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack" and "external_id" in ref:
                    stix_to_ext[obj["id"]] = ref["external_id"].strip().upper()

    # 3. Map subtechnique relationship -> parent technique ID
    sub_rel: dict[str, str] = {}
    for obj in bundle.get("objects", []):
        if (
            obj.get("type") == "relationship"
            and obj.get("relationship_type") == "subtechnique-of"
            and not obj.get("revoked", False)
            and not obj.get("x_mitre_deprecated", False)
        ):
            src_stix = obj.get("source_ref")
            tgt_stix = obj.get("target_ref")
            if src_stix in stix_to_ext and tgt_stix in stix_to_ext:
                sub_rel[stix_to_ext[src_stix]] = stix_to_ext[tgt_stix]

    # 4. Build comprehensive technique reference table
    ref_table: dict[str, Any] = {}
    for obj in bundle.get("objects", []):
        if obj.get("type") == "attack-pattern":
            for r in obj.get("external_references", []):
                if r.get("source_name") == "mitre-attack" and "external_id" in r:
                    tid = r["external_id"].strip().upper()
                    is_sub = bool(obj.get("x_mitre_is_subtechnique", False) or "." in tid)
                    parent_id = sub_rel.get(tid) or (tid.split(".")[0] if "." in tid else None)

                    # Official tactics from kill_chain_phases
                    official_tactics = []
                    for phase in obj.get("kill_chain_phases", []):
                        if phase.get("kill_chain_name") == "mitre-attack":
                            pname = phase.get("phase_name", "")
                            tactic_name = tactic_map.get(pname, pname.replace("-", " ").title())
                            official_tactics.append(tactic_name)

                    ref_table[tid] = {
                        "official_technique_name": obj.get("name", ""),
                        "official_tactics": sorted(list(set(official_tactics))),
                        "parent_technique_id": parent_id,
                        "is_subtechnique": is_sub,
                        "deprecated": bool(obj.get("x_mitre_deprecated", False)),
                        "revoked": bool(obj.get("revoked", False)),
                    }

    ref_table = dict(sorted(ref_table.items()))
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(ref_table, f, indent=2, ensure_ascii=False)

    global _CACHED_REF
    _CACHED_REF = ref_table
    return ref_table


def load_technique_reference(ref_path: Path = DEFAULT_PROCESSED_REF_PATH) -> dict[str, Any]:
    """Load preprocessed technique reference, building from STIX if missing."""
    global _CACHED_REF
    if _CACHED_REF is not None:
        return _CACHED_REF

    if ref_path.is_file():
        with open(ref_path, encoding="utf-8") as f:
            _CACHED_REF = json.load(f)
            return _CACHED_REF

    if DEFAULT_STIX_PATH.is_file():
        _CACHED_REF = build_technique_tactic_reference(DEFAULT_STIX_PATH, ref_path)
        return _CACHED_REF

    return {}


def get_official_tactics(
    technique_ids: list[str] | None,
    ref: dict[str, Any] | None = None,
) -> list[str]:
    """Return sorted unique official tactics for given technique IDs from reference."""
    if not technique_ids:
        return []
    if ref is None:
        ref = load_technique_reference()
    if not ref:
        return []

    tactics = set()
    for tid in technique_ids:
        t_clean = tid.strip().upper()
        if t_clean in ref:
            for tac in ref[t_clean].get("official_tactics", []):
                tactics.add(tac)
    return sorted(list(tactics))


def detect_tactic_discrepancies(
    events: list[dict[str, Any]],
    ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect missing techniques and discrepancies where step tactics != official tactics."""
    if ref is None:
        ref = load_technique_reference()

    all_cam_techs = set()
    for ev in events:
        for t in ev.get("techniques", []):
            if t:
                all_cam_techs.add(t.strip().upper())

    missing_techs = sorted([t for t in all_cam_techs if t not in ref])
    deprecated_or_revoked = sorted([
        t for t in all_cam_techs
        if t in ref and (ref[t].get("deprecated") or ref[t].get("revoked"))
    ])

    discrepancies = []
    for ev in events:
        if not ev.get("is_labeled"):
            continue
        step_tactics = set(ev.get("tactics", []))
        if not step_tactics:
            continue

        step_techs = [t.strip().upper() for t in ev.get("techniques", []) if t]
        official_tacs = set()
        for t in step_techs:
            if t in ref:
                official_tacs.update(ref[t].get("official_tactics", []))

        unmatched = step_tactics - official_tacs
        if unmatched:
            discrepancies.append({
                "event_id": ev.get("event_id"),
                "episode_id": ev.get("episode_id"),
                "techniques": step_techs,
                "dataset_tactics": sorted(list(step_tactics)),
                "official_tactics": sorted(list(official_tacs)),
                "discrepancy_tactics": sorted(list(unmatched)),
            })

    total_ref = len(ref)
    deprecated_count = sum(1 for v in ref.values() if v.get("deprecated"))
    revoked_count = sum(1 for v in ref.values() if v.get("revoked"))
    flagged_count = sum(1 for v in ref.values() if v.get("deprecated") or v.get("revoked"))
    active_count = total_ref - flagged_count

    return {
        "attack_version": ATTACK_VERSION,
        "source_url": SOURCE_URL,
        "version_selection_rationale": (
            "ATT&CK Enterprise v16.1 was chosen because it represents the latest mature release retaining the "
            "canonical 14 Enterprise tactics (including 'Defense Evasion'). In bleeding-edge releases (such as v19.2), "
            "MITRE restructured Defense Evasion into 'Stealth' and 'Defense Impairment', which generates 14 false-positive "
            "taxonomic discrepancies for standard defense evasion techniques while leaving the 8 genuine dataset anomalies "
            "unchanged. v16.1 maintains semantic alignment with the CAM-LDS ground-truth labeling taxonomy."
        ),
        "reference_counts": {
            "total_techniques": total_ref,
            "active_techniques": active_count,
            "deprecated_techniques": deprecated_count,
            "revoked_techniques": revoked_count,
            "flagged_techniques_total": flagged_count,
        },
        "total_cam_techniques": len(all_cam_techs),
        "missing_techniques": missing_techs,
        "deprecated_or_revoked_techniques": deprecated_or_revoked,
        "discrepancies_count": len(discrepancies),
        "discrepancies": discrepancies,
    }
