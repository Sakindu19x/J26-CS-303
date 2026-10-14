r"""Read-Only Intake Audit of Three New CAM-LDS Archives.

Audits scenario_5, scenario_6_macro_binary, and scenario_7 as candidate episodes E5, E6, E7.
NO model imports. NO evaluation. NO modifications to existing data, models, or reports.
Reads zip files in memory using zipfile.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
REPORTS_DIR = BASE_DIR / "reports"
REFERENCE_DIR = BASE_DIR / "data" / "reference"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

TECH_REF_PATH = PROCESSED_DIR / "technique_tactic_reference.json"
STIX_PATH = REFERENCE_DIR / "enterprise-attack.json"

UTC = timezone.utc
TECH_RX = re.compile(r"^T\d{4}(\.\d{3})?$")

# Pre-declared Zenodo MD5 expectations
ZENODO_MD5 = {
    "scenario_1_sudo_pam": "e7e5bd19cda62a5bfb9a68525715cd78",
    "scenario_2_cron": "c33aca73d6962414bd6c2c3f82b934c4",
    "scenario_3_vnc_apt": "bfd7e44cdb2d038a9deab800350e4b98",
    "scenario_4": "f1bf6ecd793c6c51f922ee43e33d7cf4",
    "scenario_5": "c56fce722a7b714eba004d6fd6319879",
    "scenario_6_macro_binary": "aedd7c0b51700b16c04539f10784d5d4",
    "scenario_7": "88122133a82079e07e7ed1b782bc203f",
}

ALL_EPISODES = [
    ("E1", "scenario_1_sudo_pam", "scenario_1_sudo_pam.zip", True),
    ("E2", "scenario_2_cron", "scenario_2_cron.zip", True),
    ("E3", "scenario_3_vnc_apt", "scenario_3_vnc_apt.zip", True),
    ("E4", "scenario_4", "scenario_4.zip", True),
    ("E5", "scenario_5", "scenario_5.zip", False),
    ("E6", "scenario_6_macro_binary", "scenario_6_macro_binary.zip", False),
    ("E7", "scenario_7", "scenario_7.zip", False),
]


def compute_file_hashes(p: Path) -> tuple[str, str, int]:
    """Compute MD5, SHA-256, and byte size of a file."""
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    size = p.stat().st_size
    with open(p, "rb") as f:
        while chunk := f.read(1024 * 1024):
            md5.update(chunk)
            sha256.update(chunk)
    return md5.hexdigest(), sha256.hexdigest(), size


def load_mitre_reference() -> tuple[dict[str, Any], dict[str, Any]]:
    """Load ATT&CK v16.1 reference from processed JSON and STIX reference."""
    with open(TECH_REF_PATH, "r", encoding="utf-8") as f:
        tech_ref = json.load(f)

    stix_techs = {}
    if STIX_PATH.is_file():
        with open(STIX_PATH, "r", encoding="utf-8") as f:
            stix_bundle = json.load(f)
        for obj in stix_bundle.get("objects", []):
            if obj.get("type") == "attack-pattern":
                for ref in obj.get("external_references", []):
                    if ref.get("source_name") == "mitre-attack" and "external_id" in ref:
                        tid = ref["external_id"].strip().upper()
                        stix_techs[tid] = {
                            "name": obj.get("name"),
                            "revoked": bool(obj.get("revoked", False)),
                            "deprecated": bool(obj.get("x_mitre_deprecated", False)),
                        }
    return tech_ref, stix_techs


def parse_attackmate_from_zip(zf: zipfile.ZipFile, am_path: str, episode_id: str, scenario_id: str) -> dict[str, Any]:
    """Parse attackmate.json lines directly from memory in zip."""
    raw_bytes = zf.read(am_path)
    lines = raw_bytes.decode("utf-8", errors="replace").splitlines()

    entries = []
    bad_lines = 0
    for l in lines:
        l_str = l.strip()
        if not l_str:
            continue
        try:
            entries.append(json.loads(l_str))
        except json.JSONDecodeError:
            bad_lines += 1

    steps = []
    for idx, e in enumerate(entries):
        event_id = f"{episode_id}-S{idx + 1:03d}"
        param = e.get("parameters") if isinstance(e.get("parameters"), dict) else {}
        meta = param.get("metadata") if isinstance(param.get("metadata"), dict) else {}

        # Techniqes extraction & whitespace cleaning
        techs_raw = meta.get("techniques", "")
        tech_list = []
        if isinstance(techs_raw, str) and techs_raw.strip():
            for t in techs_raw.split(","):
                cleaned = t.strip().upper()
                if cleaned and TECH_RX.match(cleaned):
                    if cleaned not in tech_list:
                        tech_list.append(cleaned)

        tech_list = sorted(tech_list)

        # Tactics extraction
        tacs_raw = meta.get("tactics") or meta.get("tactic") or ""
        tac_list = []
        if isinstance(tacs_raw, str) and tacs_raw.strip():
            for tac in tacs_raw.split(","):
                cleaned = " ".join(tac.split())
                if cleaned and cleaned not in tac_list:
                    tac_list.append(cleaned)

        # Timestamp parsing
        raw_ts = e.get("start-datetime")
        iso_ts = None
        ts_unparseable = False
        if raw_ts:
            try:
                dt = datetime.fromisoformat(str(raw_ts).strip())
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                else:
                    dt = dt.astimezone(UTC)
                iso_ts = dt.isoformat()
            except Exception:
                ts_unparseable = True
        else:
            ts_unparseable = True

        steps.append({
            "step_index": idx + 1,
            "event_id": event_id,
            "raw_timestamp": raw_ts,
            "iso_timestamp": iso_ts,
            "ts_unparseable": ts_unparseable,
            "cmd": e.get("cmd"),
            "step_type": e.get("type"),
            "is_labeled": bool(tech_list),
            "techniques": tech_list,
            "tactics": tac_list,
            "raw_entry": e,
        })

    # Sort steps deterministically: (iso_timestamp or "", step_index)
    steps_sorted = sorted(steps, key=lambda s: (s["iso_timestamp"] or "", s["step_index"]))

    # Sequence extraction
    raw_seq = [s for s in steps_sorted if s["is_labeled"]]
    col_seq = []
    for s in raw_seq:
        if not col_seq or set(col_seq[-1]["techniques"]) != set(s["techniques"]):
            col_seq.append(s)

    all_ts = [s["iso_timestamp"] for s in steps_sorted if s["iso_timestamp"]]
    ts_counts = Counter(all_ts)
    duplicate_ts_count = sum(cnt for cnt in ts_counts.values() if cnt > 1)

    distinct_full = sorted(list({t for s in raw_seq for t in s["techniques"]}))
    distinct_parent = sorted(list({t.split(".")[0] for t in distinct_full}))
    distinct_tactics = sorted(list({tac for s in raw_seq for tac in s["tactics"]}))

    first_ts = steps_sorted[0]["iso_timestamp"] if steps_sorted else None
    last_ts = steps_sorted[-1]["iso_timestamp"] if steps_sorted else None
    duration_s = None
    if first_ts and last_ts:
        try:
            dt1 = datetime.fromisoformat(first_ts)
            dt2 = datetime.fromisoformat(last_ts)
            duration_s = (dt2 - dt1).total_seconds()
        except Exception:
            pass

    return {
        "episode_id": episode_id,
        "scenario_id": scenario_id,
        "total_steps": len(steps),
        "labeled_steps": len(raw_seq),
        "unlabeled_steps": len(steps) - len(raw_seq),
        "multi_technique_steps": sum(1 for s in raw_seq if len(s["techniques"]) > 1),
        "distinct_techniques_full": distinct_full,
        "distinct_techniques_parent": distinct_parent,
        "distinct_tactics": distinct_tactics,
        "timestamp_field_used": "start-datetime (ISO 8601 UTC assumption)",
        "first_timestamp": first_ts,
        "last_timestamp": last_ts,
        "duration_seconds": duration_s,
        "unparseable_or_missing_timestamps": sum(1 for s in steps if s["ts_unparseable"]),
        "duplicate_timestamp_ties": duplicate_ts_count,
        "raw_sequence_length": len(raw_seq),
        "collapsed_sequence_length": len(col_seq),
        "next_technique_samples_raw": max(0, len(raw_seq) - 1),
        "next_technique_samples_collapsed": max(0, len(col_seq) - 1),
        "tactic_level_samples_collapsed": max(0, len(col_seq) - 1),
        "steps_sorted": steps_sorted,
        "raw_sequence": raw_seq,
        "collapsed_sequence": col_seq,
        "top_level_keys": sorted(list(set().union(*(e.keys() for e in entries)))),
        "parameter_keys": sorted(list(set().union(*(e.get("parameters", {}).keys() for e in entries if isinstance(e.get("parameters"), dict))))),
        "metadata_keys": sorted(list(set().union(*(e.get("parameters", {}).get("metadata", {}).keys() for e in entries if isinstance(e.get("parameters"), dict) and isinstance(e.get("parameters", {}).get("metadata"), dict))))),
    }


def compute_counting_bounds_for_fold(
    episodes_collapsed: dict[str, list[dict[str, Any]]],
    test_ep: str,
    train_eps: list[str],
) -> dict[str, Any]:
    """Pure counting bounds independent of any c4 model classes.
    
    Reproduces exact definitions from src/c4/evaluation.py:
    - Coverage: sample has status ok iff current_technique_set intersects train_input_pool.
    - Ceiling: sample has target seen in training iff target_technique_set intersects train_target_pool.
    """
    train_input_pool = set()
    train_target_pool = set()
    for ep in train_eps:
        items = episodes_collapsed[ep]
        for i in range(len(items) - 1):
            train_input_pool.update(items[i]["techniques"])
            train_target_pool.update(items[i + 1]["techniques"])

    test_items = episodes_collapsed[test_ep]
    n_samples = max(0, len(test_items) - 1)
    covered = 0
    ceiling = 0
    for k in range(n_samples):
        cur_techs = set(test_items[k]["techniques"])
        tgt_techs = set(test_items[k + 1]["techniques"])
        if cur_techs & train_input_pool:
            covered += 1
        if tgt_techs & train_target_pool:
            ceiling += 1

    cov_rate = (covered / n_samples) if n_samples > 0 else 0.0
    ceil_rate = (ceiling / n_samples) if n_samples > 0 else 0.0

    return {
        "test_episode": test_ep,
        "training_episodes": train_eps,
        "n_samples": n_samples,
        "covered": covered,
        "coverage_rate": cov_rate,
        "ceiling_hits": ceiling,
        "ceiling_rate": ceil_rate,
    }


def evaluate_design_bounds(
    design_name: str,
    episodes: list[str],
    episodes_collapsed: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Evaluate LOEO counting bounds across a set of episodes."""
    per_fold = {}
    tot_n = 0
    tot_cov = 0
    tot_ceil = 0

    for idx, ep in enumerate(episodes, 1):
        fold_id = f"fold_{idx}"
        train_eps = [x for x in episodes if x != ep]
        fold_res = compute_counting_bounds_for_fold(episodes_collapsed, ep, train_eps)
        per_fold[fold_id] = fold_res
        tot_n += fold_res["n_samples"]
        tot_cov += fold_res["covered"]
        tot_ceil += fold_res["ceiling_hits"]

    return {
        "design_name": design_name,
        "episodes": episodes,
        "n_episodes": len(episodes),
        "per_fold": per_fold,
        "pooled": {
            "n_samples": tot_n,
            "covered": tot_cov,
            "coverage_rate": (tot_cov / tot_n) if tot_n > 0 else 0.0,
            "ceiling_hits": tot_ceil,
            "ceiling_rate": (tot_ceil / tot_n) if tot_n > 0 else 0.0,
        },
    }


def run_intake_audit() -> dict[str, Any]:
    """Execute the full intake audit pipeline and return audit data dictionary."""
    print("=" * 80)
    print("CAM-LDS NEW EPISODES INTAKE AUDIT (E5, E6, E7)")
    print("=" * 80)

    # 1. Step 1: Hashes & Structure of all 7 zips
    archive_hashes = {}
    archive_structures = {}
    episodes_profile = {}

    tech_ref, stix_techs = load_mitre_reference()

    for ep_id, scenario_id, zip_name, is_control in ALL_EPISODES:
        zip_path = RAW_DIR / zip_name
        if not zip_path.is_file():
            raise FileNotFoundError(f"Archive missing: {zip_path}")

        md5, sha256, byte_size = compute_file_hashes(zip_path)
        exp_md5 = ZENODO_MD5[scenario_id]
        md5_match = (md5 == exp_md5)

        archive_hashes[scenario_id] = {
            "episode_id": ep_id,
            "zip_file": zip_name,
            "full_path": str(zip_path.resolve()),
            "md5": md5,
            "expected_zenodo_md5": exp_md5,
            "md5_match": md5_match,
            "sha256": sha256,
            "size_bytes": byte_size,
        }

        # Inspect zip structure in memory
        with zipfile.ZipFile(zip_path, "r") as zf:
            infolist = zf.infolist()
            namelist = zf.namelist()
            uncompressed_size = sum(i.file_size for i in infolist)

            top_dirs = sorted({n.split("/")[0] for n in namelist if "/" in n})
            expected_am = f"{scenario_id}/attacker/logs/attackmate.json"
            direct_am = "attacker/logs/attackmate.json"
            has_am = (expected_am in namelist) or (direct_am in namelist)
            actual_am_path = expected_am if (expected_am in namelist) else (direct_am if direct_am in namelist else None)

            # Check other log sources present
            log_sources = sorted({n.split("/")[1] for n in namelist if n.count("/") >= 2 and n.startswith(f"{scenario_id}/")})

            archive_structures[scenario_id] = {
                "episode_id": ep_id,
                "n_files": len(infolist),
                "uncompressed_bytes": uncompressed_size,
                "top_level_folders": top_dirs,
                "has_attackmate_json": bool(has_am),
                "attackmate_member_path": actual_am_path,
                "subdirectories_under_root": log_sources,
            }

            if not actual_am_path:
                raise ValueError(f"attackmate.json not found in {zip_name}")

            profile = parse_attackmate_from_zip(zf, actual_am_path, ep_id, scenario_id)
            episodes_profile[ep_id] = profile

    # Step 3 Control check: 190 events, 99 labeled, 64 distinct techniques, raw 99, collapsed 71
    control_events = sum(episodes_profile[e]["total_steps"] for e in ["E1", "E2", "E3", "E4"])
    control_labeled = sum(episodes_profile[e]["labeled_steps"] for e in ["E1", "E2", "E3", "E4"])
    control_raw = sum(episodes_profile[e]["raw_sequence_length"] for e in ["E1", "E2", "E3", "E4"])
    control_collapsed_len = sum(episodes_profile[e]["collapsed_sequence_length"] for e in ["E1", "E2", "E3", "E4"])
    control_techs = sorted(list({t for e in ["E1", "E2", "E3", "E4"] for t in episodes_profile[e]["distinct_techniques_full"]}))

    print("\n--- STEP 3: CONTROL PROFILE REPRODUCTION (E1-E4) ---")
    print(f"  Total events     : {control_events} (expected 190) -> {'PASS' if control_events == 190 else 'FAIL'}")
    print(f"  Labeled steps    : {control_labeled} (expected 99)  -> {'PASS' if control_labeled == 99 else 'FAIL'}")
    print(f"  Distinct techs   : {len(control_techs)} (expected 64)  -> {'PASS' if len(control_techs) == 64 else 'FAIL'}")
    print(f"  Raw sequence len : {control_raw} (expected 99)  -> {'PASS' if control_raw == 99 else 'FAIL'}")
    print(f"  Collapsed len    : {control_collapsed_len} (expected 71)  -> {'PASS' if control_collapsed_len == 71 else 'FAIL'}")

    if not (control_events == 190 and control_labeled == 99 and len(control_techs) == 64 and control_raw == 99 and control_collapsed_len == 71):
        raise AssertionError("Control profile invariants failed to reproduce!")

    # Step 4: ATT&CK v16.1 validity & Tactic Discrepancies on new episodes
    tactic_discrepancies = {}
    technique_validity = {}

    for new_ep in ["E5", "E6", "E7"]:
        prof = episodes_profile[new_ep]
        techs = prof["distinct_techniques_full"]

        valid_count = 0
        unknown_techs = []
        revoked_techs = []
        deprecated_techs = []

        for t in techs:
            if t not in tech_ref:
                unknown_techs.append(t)
            else:
                is_rev = stix_techs.get(t, {}).get("revoked", False)
                is_dep = stix_techs.get(t, {}).get("deprecated", False)
                if is_rev:
                    revoked_techs.append(t)
                elif is_dep:
                    deprecated_techs.append(t)
                else:
                    valid_count += 1

        technique_validity[new_ep] = {
            "total_distinct_techniques": len(techs),
            "valid_v16_1_techniques": valid_count,
            "unknown_techniques": unknown_techs,
            "revoked_techniques": revoked_techs,
            "deprecated_techniques": deprecated_techs,
            "all_techniques_valid": len(unknown_techs) == 0 and len(revoked_techs) == 0 and len(deprecated_techs) == 0,
        }

        # Tactic Discrepancies
        type_a = []
        type_b = []
        exact_matches = []

        for step in prof["raw_sequence"]:
            ev_id = step["event_id"]
            step_techs = step["techniques"]
            step_tacs = set(step["tactics"])
            if not step_tacs:
                continue

            official_tacs = set()
            for t in step_techs:
                if t in tech_ref:
                    official_tacs.update(tech_ref[t].get("official_tactics", []))

            unmatched = step_tacs - official_tacs
            if unmatched:
                type_a.append({
                    "event_id": ev_id,
                    "techniques": step_techs,
                    "dataset_tactics": sorted(list(step_tacs)),
                    "official_tactics": sorted(list(official_tacs)),
                    "discrepancy_tactics": sorted(list(unmatched)),
                })
            elif step_tacs < official_tacs:
                type_b.append({
                    "event_id": ev_id,
                    "techniques": step_techs,
                    "dataset_tactics": sorted(list(step_tacs)),
                    "official_tactics": sorted(list(official_tacs)),
                    "missing_official_tactics": sorted(list(official_tacs - step_tacs)),
                })
            else:
                exact_matches.append(ev_id)

        tactic_discrepancies[new_ep] = {
            "type_a_count": len(type_a),
            "type_a_events": type_a,
            "type_b_count": len(type_b),
            "type_b_events": type_b,
            "exact_match_count": len(exact_matches),
        }

    # Step 5: Pure Counting Bounds
    episodes_collapsed = {e: episodes_profile[e]["collapsed_sequence"] for e in episodes_profile}

    # Test control reproduction
    control_bounds = evaluate_design_bounds("(a) 4-episode control", ["E1", "E2", "E3", "E4"], episodes_collapsed)
    cb_pooled = control_bounds["pooled"]
    print("\n--- STEP 5: COUNTING BOUNDS REPRODUCTION (E1-E4) ---")
    print(f"  N = {cb_pooled['n_samples']} (expected 67) -> {'PASS' if cb_pooled['n_samples'] == 67 else 'FAIL'}")
    print(f"  Coverage = {cb_pooled['covered']}/{cb_pooled['n_samples']} (expected 34/67) -> {'PASS' if cb_pooled['covered'] == 34 else 'FAIL'}")
    print(f"  Ceiling  = {cb_pooled['ceiling_hits']}/{cb_pooled['n_samples']} (expected 35/67) -> {'PASS' if cb_pooled['ceiling_hits'] == 35 else 'FAIL'}")

    if not (cb_pooled["n_samples"] == 67 and cb_pooled["covered"] == 34 and cb_pooled["ceiling_hits"] == 35):
        raise AssertionError("Control counting bounds failed to reproduce!")

    design_7ep = evaluate_design_bounds("(b) 7-episode design", ["E1", "E2", "E3", "E4", "E5", "E6", "E7"], episodes_collapsed)
    design_e5 = evaluate_design_bounds("(c1) E1-E4 + E5", ["E1", "E2", "E3", "E4", "E5"], episodes_collapsed)
    design_e6 = evaluate_design_bounds("(c2) E1-E4 + E6", ["E1", "E2", "E3", "E4", "E6"], episodes_collapsed)
    design_e7 = evaluate_design_bounds("(c3) E1-E4 + E7", ["E1", "E2", "E3", "E4", "E7"], episodes_collapsed)

    all_designs = {
        "design_a_control": control_bounds,
        "design_b_7episodes": design_7ep,
        "design_c1_plus_e5": design_e5,
        "design_c2_plus_e6": design_e6,
        "design_c3_plus_e7": design_e7,
    }

    # Step 6: Decision Rules Evaluation (D1 - D6)
    decision_rules = {}
    eligibility = {}

    schema_control_top = set(episodes_profile["E1"]["top_level_keys"])
    schema_control_param = set(episodes_profile["E1"]["parameter_keys"])

    for new_ep, sc_id in [("E5", "scenario_5"), ("E6", "scenario_6_macro_binary"), ("E7", "scenario_7")]:
        prof = episodes_profile[new_ep]
        h_info = archive_hashes[sc_id]
        tech_info = technique_validity[new_ep]

        # D1: MD5 equals Zenodo MD5
        d1_pass = h_info["md5_match"]
        d1_flag = "PASS" if d1_pass else "FAIL"

        # D2: Schema match attackmate.json
        top_match = set(prof["top_level_keys"]) == schema_control_top
        diffs = []
        if not top_match:
            diffs.append(f"Top-level keys differ: {set(prof['top_level_keys']) ^ schema_control_top}")
        if "tactic" in prof["metadata_keys"] and "tactics" not in prof["metadata_keys"]:
            diffs.append("metadata uses singular 'tactic' key instead of 'tactics'")
        if "description" in prof["metadata_keys"]:
            diffs.append("metadata includes extra 'description' field")
        d2_flag = "PASS" if top_match else "FAIL"

        # D3: Parseable timestamps under UTC rules
        unparseable_labeled = sum(1 for s in prof["raw_sequence"] if s["ts_unparseable"])
        d3_pass = (unparseable_labeled == 0)
        d3_flag = "PASS" if d3_pass else "FAIL"

        # D4: Techniques exist in ATT&CK v16.1
        d4_pass = tech_info["all_techniques_valid"]
        d4_flag = "PASS" if d4_pass else "FAIL"

        # D5: Yields at least 8 collapsed transitions (below 8 is flagged "small")
        col_transitions = prof["next_technique_samples_collapsed"]
        if col_transitions >= 8:
            d5_flag = "PASS"
        else:
            d5_flag = "FLAG (small)"

        # D6: Different runs from E1-E4
        identical_to = []
        for old_ep in ["E1", "E2", "E3", "E4"]:
            if [s["techniques"] for s in prof["collapsed_sequence"]] == [s["techniques"] for s in episodes_profile[old_ep]["collapsed_sequence"]]:
                identical_to.append(old_ep)
        d6_pass = (len(identical_to) == 0)
        d6_flag = "PASS" if d6_pass else "FAIL"

        # Overall eligibility: D1-D4 all PASS and D6 PASS
        is_eligible = (d1_flag == "PASS" and d2_flag == "PASS" and d3_flag == "PASS" and d4_flag == "PASS" and d6_flag == "PASS")
        eligibility_str = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"

        decision_rules[new_ep] = {
            "scenario_id": sc_id,
            "D1_zenodo_md5": {"result": d1_flag, "md5": h_info["md5"], "expected": h_info["expected_zenodo_md5"]},
            "D2_schema": {"result": d2_flag, "differences": diffs},
            "D3_timestamps": {"result": d3_flag, "unparseable_labeled": unparseable_labeled, "ties": prof["duplicate_timestamp_ties"]},
            "D4_attack_v16_1": {"result": d4_flag, "unknown": tech_info["unknown_techniques"], "revoked": tech_info["revoked_techniques"], "deprecated": tech_info["deprecated_techniques"]},
            "D5_transitions_threshold": {"result": d5_flag, "collapsed_transitions": col_transitions, "threshold": 8},
            "D6_sequence_uniqueness": {"result": d6_flag, "identical_to": identical_to},
            "eligibility": eligibility_str,
        }
        eligibility[new_ep] = eligibility_str

    # Clean serializable dictionary for episodes_profile
    serializable_profiles = {}
    for ep, p in episodes_profile.items():
        serializable_profiles[ep] = {k: v for k, v in p.items() if k not in ("steps_sorted", "raw_sequence", "collapsed_sequence")}

    audit_result = {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "pre_declared_rules": {
            "D1": "MD5 of each new zip equals the Zenodo MD5.",
            "D2": "Each new zip contains attacker/logs/attackmate.json, and the set of top-level keys matches the schema of E1-E4.",
            "D3": "Every labeled step has a parseable timestamp under Stage 1 UTC assumption.",
            "D4": "Every technique ID exists in ATT&CK Enterprise v16.1 reference.",
            "D5": "Each new episode yields at least 8 collapsed transitions (below 8 is flagged 'small', not failed).",
            "D6": "The new episodes have unique collapsed technique sequences compared to E1-E4.",
        },
        "archive_hashes": archive_hashes,
        "archive_structures": archive_structures,
        "episodes_profile": serializable_profiles,
        "control_invariants_check": {
            "total_events": control_events,
            "labeled_steps": control_labeled,
            "distinct_techniques": len(control_techs),
            "raw_sequence_length": control_raw,
            "collapsed_sequence_length": control_collapsed_len,
            "reproduced": True,
        },
        "technique_validity": technique_validity,
        "tactic_discrepancies": tactic_discrepancies,
        "counting_bounds_designs": all_designs,
        "decision_rules": decision_rules,
        "eligibility_summary": eligibility,
    }

    return audit_result


def generate_extended_hashes_file(audit_data: dict[str, Any]) -> None:
    """Write reports/raw_archive_hashes_extended.json."""
    out_path = REPORTS_DIR / "raw_archive_hashes_extended.json"
    hashes_list = []
    for sc_id, h in audit_data["archive_hashes"].items():
        hashes_list.append({
            "archive": h["zip_file"],
            "scenario": sc_id,
            "episode_id": h["episode_id"],
            "md5": h["md5"],
            "sha256": h["sha256"],
            "size_bytes": h["size_bytes"],
            "zenodo_md5_match": h["md5_match"],
        })
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"raw_archive_hashes_extended": hashes_list}, f, indent=2)
    print(f"Wrote {out_path}")


def generate_audit_json_file(audit_data: dict[str, Any]) -> None:
    """Write reports/new_episodes_intake_audit.json."""
    out_path = REPORTS_DIR / "new_episodes_intake_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Wrote {out_path}")


def generate_audit_markdown_file(audit_data: dict[str, Any]) -> None:
    """Generate reports/new_episodes_intake_audit.md strictly from JSON data."""
    out_path = REPORTS_DIR / "new_episodes_intake_audit.md"
    L = []

    def A(line: str = "") -> None:
        L.append(line)

    A("# CAM-LDS New Episodes Intake Audit: Scenario 5, 6, 7")
    A()
    A(f"**Audit Timestamp**: `{audit_data['audit_timestamp']}`  ")
    A("**Scope**: Read-only intake audit of three candidate archives (`scenario_5.zip`, `scenario_6_macro_binary.zip`, `scenario_7.zip`).  ")
    A("**Purpose**: Decide, from empirical facts, whether these three episodes are fit to be added as episodes E5, E6, E7 in a future extended experiment.  ")
    A()
    A("---")
    A()
    A("## Pre-Declared Decision Rules")
    A()
    for rule_id, rule_desc in audit_data["pre_declared_rules"].items():
        A(f"- **{rule_id}**: {rule_desc}")
    A()
    A("---")
    A()
    A("## Step 1: Archive Hashes (7 Archives)")
    A()
    A("| Episode | Scenario | Archive File | MD5 | Expected Zenodo MD5 | MD5 Match | SHA-256 |")
    A("|:---|:---|:---|:---|:---|:---:|:---|")
    for sc_id, h in audit_data["archive_hashes"].items():
        match_str = "**TRUE**" if h["md5_match"] else "**FALSE**"
        A(f"| {h['episode_id']} | `{sc_id}` | `{h['zip_file']}` | `{h['md5']}` | `{h['expected_zenodo_md5']}` | {match_str} | `{h['sha256']}` |")
    A()
    A("---")
    A()
    A("## Step 2: Archive Structure Comparison")
    A()
    A("| Episode | Scenario | Total Files | Uncompressed Size | Top-Level Folders | `attackmate.json` Path | Other Log Subdirectories |")
    A("|:---|:---|:---|:---|:---|:---|:---|")
    for sc_id, s in audit_data["archive_structures"].items():
        size_mb = f"{s['uncompressed_bytes'] / (1024 * 1024):.1f} MB"
        top_str = ", ".join(f"`{f}`" for f in s["top_level_folders"])
        sub_str = ", ".join(f"`{d}`" for d in s["subdirectories_under_root"])
        A(f"| {s['episode_id']} | `{sc_id}` | {s['n_files']} | {size_mb} ({s['uncompressed_bytes']:,} B) | {top_str} | `{s['attackmate_member_path']}` | {sub_str} |")
    A()
    A("---")
    A()
    A("## Step 3: AttackMate Profile & Control Invariants Reproduction")
    A()
    c_inv = audit_data["control_invariants_check"]
    A("### Stage 1 Control Reproduction (E1–E4)")
    A()
    A("| Metric | Control Expected | Actual Measured | Reproduction Status |")
    A("|:---|:---:|:---:|:---:|")
    A(f"| Total AttackMate Events | 190 | {c_inv['total_events']} | **MATCH** |")
    A(f"| Labeled Steps | 99 | {c_inv['labeled_steps']} | **MATCH** |")
    A(f"| Distinct ATT&CK Techniques | 64 | {c_inv['distinct_techniques']} | **MATCH** |")
    A(f"| Raw Sequence Length | 99 | {c_inv['raw_sequence_length']} | **MATCH** |")
    A(f"| Collapsed Sequence Length | 71 | {c_inv['collapsed_sequence_length']} | **MATCH** |")
    A()
    A("### Full 7-Episode Profile Summary")
    A()
    A("| Metric | E1 | E2 | E3 | E4 | E5 | E6 | E7 |")
    A("|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|")
    P = audit_data["episodes_profile"]
    A(f"| Scenario Name | `{P['E1']['scenario_id']}` | `{P['E2']['scenario_id']}` | `{P['E3']['scenario_id']}` | `{P['E4']['scenario_id']}` | `{P['E5']['scenario_id']}` | `{P['E6']['scenario_id']}` | `{P['E7']['scenario_id']}` |")
    A(f"| Total Steps | {P['E1']['total_steps']} | {P['E2']['total_steps']} | {P['E3']['total_steps']} | {P['E4']['total_steps']} | {P['E5']['total_steps']} | {P['E6']['total_steps']} | {P['E7']['total_steps']} |")
    A(f"| Labeled Steps | {P['E1']['labeled_steps']} | {P['E2']['labeled_steps']} | {P['E3']['labeled_steps']} | {P['E4']['labeled_steps']} | {P['E5']['labeled_steps']} | {P['E6']['labeled_steps']} | {P['E7']['labeled_steps']} |")
    A(f"| Unlabeled Steps | {P['E1']['unlabeled_steps']} | {P['E2']['unlabeled_steps']} | {P['E3']['unlabeled_steps']} | {P['E4']['unlabeled_steps']} | {P['E5']['unlabeled_steps']} | {P['E6']['unlabeled_steps']} | {P['E7']['unlabeled_steps']} |")
    A(f"| Multi-Technique Steps | {P['E1']['multi_technique_steps']} | {P['E2']['multi_technique_steps']} | {P['E3']['multi_technique_steps']} | {P['E4']['multi_technique_steps']} | {P['E5']['multi_technique_steps']} | {P['E6']['multi_technique_steps']} | {P['E7']['multi_technique_steps']} |")
    A(f"| Distinct Techniques (Full) | {len(P['E1']['distinct_techniques_full'])} | {len(P['E2']['distinct_techniques_full'])} | {len(P['E3']['distinct_techniques_full'])} | {len(P['E4']['distinct_techniques_full'])} | {len(P['E5']['distinct_techniques_full'])} | {len(P['E6']['distinct_techniques_full'])} | {len(P['E7']['distinct_techniques_full'])} |")
    A(f"| Distinct Techniques (Parent) | {len(P['E1']['distinct_techniques_parent'])} | {len(P['E2']['distinct_techniques_parent'])} | {len(P['E3']['distinct_techniques_parent'])} | {len(P['E4']['distinct_techniques_parent'])} | {len(P['E5']['distinct_techniques_parent'])} | {len(P['E6']['distinct_techniques_parent'])} | {len(P['E7']['distinct_techniques_parent'])} |")
    A(f"| Distinct Tactic Strings | {len(P['E1']['distinct_tactics'])} | {len(P['E2']['distinct_tactics'])} | {len(P['E3']['distinct_tactics'])} | {len(P['E4']['distinct_tactics'])} | {len(P['E5']['distinct_tactics'])} | {len(P['E6']['distinct_tactics'])} | {len(P['E7']['distinct_tactics'])} |")
    A(f"| Missing/Unparseable Timestamps | {P['E1']['unparseable_or_missing_timestamps']} | {P['E2']['unparseable_or_missing_timestamps']} | {P['E3']['unparseable_or_missing_timestamps']} | {P['E4']['unparseable_or_missing_timestamps']} | {P['E5']['unparseable_or_missing_timestamps']} | {P['E6']['unparseable_or_missing_timestamps']} | {P['E7']['unparseable_or_missing_timestamps']} |")
    A(f"| Duplicate Timestamp Ties | {P['E1']['duplicate_timestamp_ties']} | {P['E2']['duplicate_timestamp_ties']} | {P['E3']['duplicate_timestamp_ties']} | {P['E4']['duplicate_timestamp_ties']} | {P['E5']['duplicate_timestamp_ties']} | {P['E6']['duplicate_timestamp_ties']} | {P['E7']['duplicate_timestamp_ties']} |")
    A(f"| Raw Sequence Length | {P['E1']['raw_sequence_length']} | {P['E2']['raw_sequence_length']} | {P['E3']['raw_sequence_length']} | {P['E4']['raw_sequence_length']} | {P['E5']['raw_sequence_length']} | {P['E6']['raw_sequence_length']} | {P['E7']['raw_sequence_length']} |")
    A(f"| Collapsed Sequence Length | {P['E1']['collapsed_sequence_length']} | {P['E2']['collapsed_sequence_length']} | {P['E3']['collapsed_sequence_length']} | {P['E4']['collapsed_sequence_length']} | {P['E5']['collapsed_sequence_length']} | {P['E6']['collapsed_sequence_length']} | {P['E7']['collapsed_sequence_length']} |")
    A(f"| Next-Technique Samples (Raw) | {P['E1']['next_technique_samples_raw']} | {P['E2']['next_technique_samples_raw']} | {P['E3']['next_technique_samples_raw']} | {P['E4']['next_technique_samples_raw']} | {P['E5']['next_technique_samples_raw']} | {P['E6']['next_technique_samples_raw']} | {P['E7']['next_technique_samples_raw']} |")
    A(f"| Next-Technique Samples (Collapsed) | {P['E1']['next_technique_samples_collapsed']} | {P['E2']['next_technique_samples_collapsed']} | {P['E3']['next_technique_samples_collapsed']} | {P['E4']['next_technique_samples_collapsed']} | {P['E5']['next_technique_samples_collapsed']} | {P['E6']['next_technique_samples_collapsed']} | {P['E7']['next_technique_samples_collapsed']} |")
    A(f"| First Timestamp | `{P['E1']['first_timestamp']}` | `{P['E2']['first_timestamp']}` | `{P['E3']['first_timestamp']}` | `{P['E4']['first_timestamp']}` | `{P['E5']['first_timestamp']}` | `{P['E6']['first_timestamp']}` | `{P['E7']['first_timestamp']}` |")
    A(f"| Last Timestamp | `{P['E1']['last_timestamp']}` | `{P['E2']['last_timestamp']}` | `{P['E3']['last_timestamp']}` | `{P['E4']['last_timestamp']}` | `{P['E5']['last_timestamp']}` | `{P['E6']['last_timestamp']}` | `{P['E7']['last_timestamp']}` |")
    A()
    A("---")
    A()
    A("## Step 4: ATT&CK v16.1 Reference Validity & Tactic Discrepancies")
    A()
    A("### Technique Validity (Rule D4)")
    A()
    for new_ep in ["E5", "E6", "E7"]:
        tv = audit_data["technique_validity"][new_ep]
        A(f"- **{new_ep} (`{audit_data['episodes_profile'][new_ep]['scenario_id']}`)**:")
        A(f"  - Distinct Techniques: {tv['total_distinct_techniques']}")
        A(f"  - Valid Active v16.1: {tv['valid_v16_1_techniques']}")
        A(f"  - Unknown IDs: {tv['unknown_techniques'] if tv['unknown_techniques'] else 'None'}")
        A(f"  - Revoked IDs: {tv['revoked_techniques'] if tv['revoked_techniques'] else 'None'}")
        A(f"  - Deprecated IDs: {tv['deprecated_techniques'] if tv['deprecated_techniques'] else 'None'}")
    A()
    A("### Tactic Discrepancy Classification")
    A()
    A("Discrepancies are categorized under Stage 1 criteria:")
    A("- **Type (a)**: The dataset names a tactic that is **not in the official set** for that technique.")
    A("- **Type (b)**: The dataset gives a **strict subset** of the official tactics.")
    A()
    for new_ep in ["E5", "E6", "E7"]:
        td = audit_data["tactic_discrepancies"][new_ep]
        A(f"#### Episode {new_ep} (`{audit_data['episodes_profile'][new_ep]['scenario_id']}`)")
        A(f"- Exact matches: {td['exact_match_count']}")
        A(f"- Type (a) discrepancies: {td['type_a_count']}")
        if td["type_a_events"]:
            for item in td["type_a_events"]:
                A(f"  - `{item['event_id']}`: Techniques `{item['techniques']}` | Dataset tactics `{item['dataset_tactics']}` | Official tactics `{item['official_tactics']}` | Extra tactic(s): `{item['discrepancy_tactics']}`")
        A(f"- Type (b) discrepancies (strict subset): {td['type_b_count']}")
        if td["type_b_events"]:
            for item in td["type_b_events"]:
                A(f"  - `{item['event_id']}`: Techniques `{item['techniques']}` | Dataset tactics `{item['dataset_tactics']}` | Official tactics `{item['official_tactics']}`")
        A()
    A("---")
    A()
    A("## Step 5: Pure Counting Bounds (No Models)")
    A()
    A("> [!IMPORTANT]")
    A("> **Definitional Notice**: These counting bounds are empirical set intersections based strictly on closed vocabulary properties. They are **pure counting facts** and do not represent model inference, prediction results, or evidence of model accuracy.")
    A()
    A("### Quoted Definitions from `src/c4/evaluation.py`")
    A()
    A("```python")
    A("train_target_pool: set[str] = set()")
    A("for ep in train_eps:")
    A("    items = ep_sequences[ep][variant]")
    A("    for i in range(len(items) - 1):")
    A("        train_target_pool.update(markov._extract_tech_set(items[i + 1]))")
    A("...")
    A("if tgt & train_target_pool:")
    A("    ceiling_hits += 1")
    A("...")
    A("covered = sum(1 for s in fold_samples if preds['markov'][s['sample_id']]['status'] == 'ok')")
    A("```")
    A()
    A("### Counting Bounds by Experimental Design")
    A()
    for des_key, des in audit_data["counting_bounds_designs"].items():
        A(f"#### {des['design_name']}")
        A()
        A("| Fold | Test Episode | Training Episodes | N Samples | Covered | Coverage Rate | Ceiling Hits | Ceiling Rate |")
        A("|:---|:---:|:---|:---:|:---:|:---:|:---:|:---:|")
        for fid, f in des["per_fold"].items():
            train_str = ", ".join(f["training_episodes"])
            A(f"| {fid} | {f['test_episode']} | {train_str} | {f['n_samples']} | {f['covered']} | {f['coverage_rate'] * 100:.2f}% | {f['ceiling_hits']} | {f['ceiling_rate'] * 100:.2f}% |")
        p = des["pooled"]
        A(f"| **POOLED** | — | — | **{p['n_samples']}** | **{p['covered']}** | **{p['coverage_rate'] * 100:.2f}%** | **{p['ceiling_hits']}** | **{p['ceiling_rate'] * 100:.2f}%** |")
        A()
    A("---")
    A()
    A("## Step 6: Decision Rules & Intake Eligibility Summary")
    A()
    A("| Rule ID | Evaluated Criterion | E5 (`scenario_5`) | E6 (`scenario_6_macro_binary`) | E7 (`scenario_7`) |")
    A("|:---|:---|:---:|:---:|:---:|")
    dr = audit_data["decision_rules"]
    A(f"| **D1** | Zenodo MD5 Hash Match | **{dr['E5']['D1_zenodo_md5']['result']}** | **{dr['E6']['D1_zenodo_md5']['result']}** | **{dr['E7']['D1_zenodo_md5']['result']}** |")
    A(f"| **D2** | AttackMate Schema & Top Keys Match | **{dr['E5']['D2_schema']['result']}** | **{dr['E6']['D2_schema']['result']}** | **{dr['E7']['D2_schema']['result']}** |")
    A(f"| **D3** | Parseable Timestamps (UTC assumption) | **{dr['E5']['D3_timestamps']['result']}** | **{dr['E6']['D3_timestamps']['result']}** | **{dr['E7']['D3_timestamps']['result']}** |")
    A(f"| **D4** | Valid ATT&CK Enterprise v16.1 IDs | **{dr['E5']['D4_attack_v16_1']['result']}** | **{dr['E6']['D4_attack_v16_1']['result']}** | **{dr['E7']['D4_attack_v16_1']['result']}** |")
    A(f"| **D5** | >= 8 Collapsed Transitions (Threshold) | **{dr['E5']['D5_transitions_threshold']['result']}** ({dr['E5']['D5_transitions_threshold']['collapsed_transitions']}) | **{dr['E6']['D5_transitions_threshold']['result']}** ({dr['E6']['D5_transitions_threshold']['collapsed_transitions']}) | **{dr['E7']['D5_transitions_threshold']['result']}** ({dr['E7']['D5_transitions_threshold']['collapsed_transitions']}) |")
    A(f"| **D6** | Sequence Uniqueness vs E1–E4 | **{dr['E5']['D6_sequence_uniqueness']['result']}** | **{dr['E6']['D6_sequence_uniqueness']['result']}** | **{dr['E7']['D6_sequence_uniqueness']['result']}** |")
    A()
    A("### Eligibility Verdicts")
    A()
    for ep in ["E5", "E6", "E7"]:
        sc = audit_data["episodes_profile"][ep]["scenario_id"]
        el = audit_data["eligibility_summary"][ep]
        d5_note = f" (Note: D5 is {dr[ep]['D5_transitions_threshold']['result']} with {dr[ep]['D5_transitions_threshold']['collapsed_transitions']} transitions)" if "FLAG" in dr[ep]['D5_transitions_threshold']['result'] else ""
        A(f"- **{ep} (`{sc}`)**: **{el}**{d5_note}")
    A()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"Wrote {out_path}")


def main() -> None:
    audit_data = run_intake_audit()
    generate_extended_hashes_file(audit_data)
    generate_audit_json_file(audit_data)
    generate_audit_markdown_file(audit_data)
    print("\nIntake audit completed successfully.")


if __name__ == "__main__":
    main()
