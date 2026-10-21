"""Dataset discovery: builds reports/dataset_inventory.{json,md} from real archive contents only."""
from __future__ import annotations

import json
import posixpath
import re
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .data_loading import EXPECTED_ARCHIVES, RAW_DIR, REPORTS_DIR, ArchiveStatus, discover

C3_KEYWORDS = {
    "threat_score": r"threat[_ ]?score",
    "investigation_priority": r"(investigation[_ ]?)?priority",
    "cti_confidence": r"(cti[_ ]?)?confidence",
    "freshness": r"fresh",
    "asset_criticality": r"(asset[_ ]?)?critical",
}
LABEL_HINTS = re.compile(r"(attack|mitre|tactic|technique|ttp|label|ground[_ ]?truth|step)", re.I)
TS_HINTS = re.compile(r"(time|date|ts$|^ts|epoch)", re.I)
ID_HINTS = re.compile(r"(host|user|run|scenario|session|id$)", re.I)
TEXT_EXT = {".json", ".jsonl", ".log", ".txt", ".csv", ".yml", ".yaml", ".md", ".xml", ""}
SAMPLE_BYTES = 64 * 1024

TS_PATTERNS = [
    ("ISO8601", r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?"),
    ("syslog (Mon DD HH:MM:SS)", r"[A-Z][a-z]{2}\s+\d{1,2}\s\d{2}:\d{2}:\d{2}"),
    ("epoch seconds/ms", r"\b1[5-9]\d{8}(\d{3})?(\.\d+)?\b"),
]


def _walk_json(obj, path="$", out=None, depth=0):
    """Collect (path, type) for every key; lists collapsed to [] ."""
    out = {} if out is None else out
    if depth > 8:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            out.setdefault(p, set()).add(type(v).__name__)
            _walk_json(v, p, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj[:50]:
            _walk_json(v, path + "[]", out, depth + 1)
    return out


def _read_sample(zf: zipfile.ZipFile, name: str, limit=SAMPLE_BYTES) -> str:
    with zf.open(name) as fh:
        return fh.read(limit).decode("utf-8", errors="replace")


def _sniff_timestamps(text: str) -> list[dict]:
    lines = [ln for ln in text.splitlines() if ln.strip()][:200]
    res = []
    for label, pat in TS_PATTERNS:
        rx = re.compile(pat)
        hits = [m.group(0) for ln in lines if (m := rx.search(ln))]
        if hits:
            res.append({"format": label, "matched_lines_of_sample": len(hits), "example": hits[0]})
    return res


def _inspect_file(zf: zipfile.ZipFile, info: zipfile.ZipInfo) -> dict:
    name = info.filename
    ext = posixpath.splitext(name)[1].lower()
    rec = {"name": name, "size": info.file_size, "ext": ext}
    if info.file_size == 0 or ext not in TEXT_EXT:
        return rec
    try:
        text = _read_sample(zf, name)
    except Exception as exc:  # unreadable member
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec
    head = [ln[:300] for ln in text.splitlines()[:3]]
    rec["head_lines"] = head
    rec["timestamp_formats"] = _sniff_timestamps(text)
    if ext in (".json", ".jsonl") or (head and head[0].lstrip().startswith(("{", "["))):
        fields = {}
        try:
            if ext == ".jsonl" or "\n{" in text[:2000] and info.file_size > SAMPLE_BYTES:
                docs = [json.loads(ln) for ln in text.splitlines()[:-1] if ln.strip()][:50]
                for d in docs:
                    _walk_json(d, "$", fields)
            else:
                _walk_json(json.loads(text if info.file_size <= SAMPLE_BYTES else _read_sample(zf, name, info.file_size)), "$", fields)
            rec["json_fields"] = {k: sorted(v) for k, v in fields.items()}
        except Exception as exc:
            rec["json_parse_note"] = f"not fully parseable as one JSON doc/JSONL sample: {type(exc).__name__}"
    elif ext == ".csv" and head:
        rec["csv_columns"] = [c.strip() for c in head[0].split(",")]
    return rec


def _run_ids(entries: list[dict]) -> dict:
    """Group files by first-level folder(s); never assumes what a 'run' is."""
    groups = defaultdict(int)
    for e in entries:
        if e["is_dir"]:
            continue
        parts = e["name"].split("/")
        groups["/".join(parts[:-1][:2]) or "<root>"] += 1
    return dict(sorted(groups.items()))


def inspect_archive(st: ArchiveStatus) -> dict:
    out = {"archive": st.name, "present": st.present, "readable": st.readable, "error": st.error}
    if not (st.present and st.readable):
        return out
    files = [e for e in st.entries if not e["is_dir"]]
    out["n_files"] = len(files)
    out["total_uncompressed_bytes"] = sum(e["size"] for e in files)
    out["contents"] = st.entries
    out["extension_counts"] = dict(Counter(posixpath.splitext(e["name"])[1].lower() or "<none>" for e in files))
    out["folder_groups_candidate_runs"] = _run_ids(st.entries)
    out["run_identification_note"] = (
        "Candidate groups are folders at depth<=2; whether they are independent runs must be confirmed "
        "from the content (UNVERIFIED)."
    )
    with zipfile.ZipFile(st.path) as zf:
        infos = {i.filename: i for i in zf.infolist()}
        am = [e["name"] for e in files if posixpath.basename(e["name"]).lower() == "attackmate.json"]
        out["attackmate_json_files"] = am
        out["attackmate_json_raw_head"] = {n: _read_sample(zf, n, 4096) for n in am}
        out["attackmate_analysis"] = {n: analyze_attackmate(zf, n) for n in am}
        logs = log_sources(files)
        out["log_sources_by_host"] = logs
        out["hosts_candidates"] = sorted({e["name"].split("/")[1] for e in files if e["name"].count("/") >= 2})
        # Only sniff log-like members (archives are full filesystem snapshots, ~12k files each).
        to_inspect = [f["path"] for v in logs.values() for f in v][:150]
        out["files"] = [_inspect_file(zf, infos[n]) for n in to_inspect]
    return out


def analyze_attackmate(zf: zipfile.ZipFile, name: str) -> dict:
    """Parse the whole attackmate.json line by line; nothing is assumed beyond what parses."""
    entries, bad = [], 0
    with zf.open(name) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entries.append(json.loads(raw))
            except json.JSONDecodeError:
                bad += 1
    entries = [e for e in entries if isinstance(e, dict)]

    def meta(e):
        m = (e.get("parameters") or {}).get("metadata") if isinstance(e.get("parameters"), dict) else None
        return m if isinstance(m, dict) else None

    labeled = [e for e in entries if meta(e) and meta(e).get("techniques")]
    unlabeled = [e for e in entries if not (meta(e) and meta(e).get("techniques"))]
    starts = sorted(e["start-datetime"] for e in entries if "start-datetime" in e)
    return {
        "format": "JSON Lines (one object per line)",
        "n_entries": len(entries),
        "unparseable_lines": bad,
        "top_level_keys": dict(Counter(k for e in entries for k in e)),
        "parameter_keys": dict(Counter(k for e in entries if isinstance(e.get("parameters"), dict) for k in e["parameters"])),
        "metadata_keys": dict(Counter(k for e in entries if meta(e) for k in meta(e))),
        "entries_with_attack_label": len(labeled),
        "entries_without_attack_label": len(unlabeled),
        "distinct_techniques": sorted({meta(e)["techniques"] for e in labeled}),
        "distinct_tactics": sorted({meta(e).get("tactics") for e in labeled if meta(e).get("tactics")}),
        "start_datetime_first": starts[0] if starts else None,
        "start_datetime_last": starts[-1] if starts else None,
        "types": dict(Counter(e.get("type") for e in entries)),
        "example_labeled_entries": labeled[:3],
        "example_unlabeled_entries": unlabeled[:2],
    }


LOG_PATH_RX = re.compile(r"(/logs/|/var/log/|/audit/|wazuh|tcpdump|\.journal$)", re.I)


def log_sources(files: list[dict]) -> dict:
    """Per host (2nd path component): largest non-empty log-like files. Path-name based only."""
    per_host = defaultdict(list)
    for f in files:
        p = f["name"]
        if LOG_PATH_RX.search(p) and f["size"] > 0:
            parts = p.split("/")
            per_host[parts[1] if len(parts) > 1 else "<root>"].append({"path": p, "size": f["size"]})
    return {h: sorted(v, key=lambda x: -x["size"])[:40] for h, v in per_host.items()}


def classify_fields(archives: list[dict]) -> dict:
    """Name-based candidates restricted to attackmate.json fields. Flagged unconfirmed."""
    label_c, ts_c, id_c, c3 = set(), set(), set(), defaultdict(set)
    for a in archives:
        for am in a.get("attackmate_analysis", {}).values():
            names = set(am["top_level_keys"]) | set(am["parameter_keys"]) | set(am["metadata_keys"])
            for n in names:
                if LABEL_HINTS.search(n):
                    label_c.add(n)
                if TS_HINTS.search(n):
                    ts_c.add(n)
                if ID_HINTS.search(n):
                    id_c.add(n)
                for k, pat in C3_KEYWORDS.items():
                    if re.search(pat, n, re.I):
                        c3[k].add(n)
    return {
        "status": "name-based heuristic over attackmate.json keys only; NOT confirmed ground truth",
        "ground_truth_label_candidates": sorted(label_c),
        "timestamp_field_candidates": sorted(ts_c),
        "identifier_field_candidates": sorted(id_c),
        "c3_style_field_matches": {k: sorted(c3.get(k, [])) for k in C3_KEYWORDS},
    }



from .deep_inspect import inspect_scenario
from .report import render_markdown, verified_field_table


def build_inventory(raw_dir: Path | str = RAW_DIR) -> dict:
    raw_dir = Path(raw_dir)
    statuses = discover(raw_dir)
    archives = [inspect_archive(s) for s in statuses]
    present = [a["archive"] for a in archives if a["present"]]
    issues = []
    for n in EXPECTED_ARCHIVES:
        if n not in present:
            issues.append({"type": "missing_archive", "file": f"data/raw/{n}"})
    for a in archives:
        if a["present"] and not a["readable"]:
            issues.append({"type": "unreadable_archive", "file": a["archive"], "error": a["error"]})
        if a["present"] and a["readable"] and not a.get("attackmate_json_files"):
            issues.append({"type": "missing_label_file", "file": f"attackmate.json not found in {a['archive']}"})

    details = {}
    for s in statuses:
        if s.present and s.readable:
            try:
                details[s.name] = inspect_scenario(Path(s.path))
            except Exception as exc:
                details[s.name] = {"archive": s.name, "error": f"{type(exc).__name__}: {exc}"}

    inv = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "raw_dir": str(raw_dir),
        "expected_archives": EXPECTED_ARCHIVES,
        "archives_present": present,
        "issues": issues,
        "archives": archives,
        "details": details,
        "verified_fields": verified_field_table(details),
        "field_classification": classify_fields(archives),
        "ground_truth_vs_metadata_note": (
            "Separation of ground-truth labels vs event metadata is only reported when real files exist; "
            "see verified_fields."
        ),
    }
    if not present:
        inv["conclusion"] = "No archives found: nothing inspected. No fields, labels or runs are reported."
    return inv


def to_markdown(inv: dict) -> str:
    if inv.get("details"):
        return render_markdown(inv)
    L = ["# Dataset Inventory (CAM-LDS)", "", f"Generated: {inv['generated_at']}", f"Raw dir: `{inv['raw_dir']}`", ""]
    L += ["## Archive status", "", "| Archive | Present | Readable | Files | Note |", "|---|---|---|---|---|"]
    for a in inv["archives"]:
        L.append(f"| {a['archive']} | {a['present']} | {a['readable']} | {a.get('n_files', '-')} | {a.get('error') or ''} |")
    L += ["", "## Issues (missing / unreadable / unlabeled)", ""]
    L += [f"- **{i['type']}**: `{i['file']}`" + (f" ({i['error']})" if i.get("error") else "") for i in inv["issues"]] or ["- none"]
    if inv.get("conclusion"):
        L += ["", "## Conclusion", "", inv["conclusion"]]
    for a in inv["archives"]:
        if not a.get("readable"):
            continue
        L += ["", f"## {a['archive']}", "", f"- Files: {a['n_files']}, uncompressed bytes: {a['total_uncompressed_bytes']}",
              f"- Extensions: {a['extension_counts']}", f"- {a['run_identification_note']}", "", "### Candidate run groups", ""]
        L += [f"- `{k}`: {v} files" for k, v in a["folder_groups_candidate_runs"].items()]
        L += ["", "### Files", "", "| Path | Size | Timestamp formats |", "|---|---|---|"]
        for f in a["files"]:
            tf = "; ".join(t["format"] + f" (e.g. `{t['example']}`)" for t in f.get("timestamp_formats", []))
            L.append(f"| {f['name']} | {f['size']} | {tf} |")
        for n, raw in a["attackmate_json_raw_head"].items():
            L += ["", f"### {n} (first 4 KB, verbatim)", "", "```json", raw, "```"]
        for n, am in a.get("attackmate_analysis", {}).items():
            L += ["", f"### Analysis of {n}", "",
                  f"- format: {am['format']}; entries: {am['n_entries']}; unparseable lines: {am['unparseable_lines']}",
                  f"- with ATT&CK label (parameters.metadata.techniques): {am['entries_with_attack_label']}; "
                  f"without: {am['entries_without_attack_label']}",
                  f"- start-datetime range: {am['start_datetime_first']} .. {am['start_datetime_last']}",
                  f"- top-level keys: {am['top_level_keys']}", f"- metadata keys: {am['metadata_keys']}",
                  f"- techniques: {am['distinct_techniques']}", f"- tactics: {am['distinct_tactics']}",
                  f"- step types: {am['types']}"]
        L += ["", f"Host candidates (2nd path component): {a.get('hosts_candidates')}", "", "### Log-like sources per host (largest first, path-name based)", ""]
        for h, v in a.get("log_sources_by_host", {}).items():
            L.append(f"- **{h}**: " + ", ".join(f"`{x['path'].split('/', 2)[-1]}` ({x['size']})" for x in v[:8]))

    fc = inv["field_classification"]
    L += ["", "## Field classification (heuristic, unconfirmed)", ""]
    for k in ("ground_truth_label_candidates", "timestamp_field_candidates", "identifier_field_candidates"):
        L.append(f"- {k}: {fc[k] or 'none found'}")
    L += ["", "### C3-style fields", ""] + [f"- {k}: {v or 'not found'}" for k, v in fc["c3_style_field_matches"].items()]
    return "\n".join(L) + "\n"


def write_reports(inv: dict, reports_dir: Path = REPORTS_DIR) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    j, m = reports_dir / "dataset_inventory.json", reports_dir / "dataset_inventory.md"
    j.write_text(json.dumps(inv, indent=2, default=str), encoding="utf-8")
    m.write_text(to_markdown(inv), encoding="utf-8")
    return j, m
