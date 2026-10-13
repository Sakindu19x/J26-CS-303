"""Verified deep inspection of CAM-LDS scenario archives (read-only; archives are never modified).

Everything reported here is computed from real archive members. Anything that cannot be computed
is returned as None / "UNVERIFIED" rather than guessed.
"""
from __future__ import annotations

import calendar
import json
import posixpath
import re
import struct
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone

UTC = timezone.utc
TECH_RX = re.compile(r"^T\d{4}(\.\d{3})?$")
SSHD_AUDIT_TYPES = ("USER_LOGIN", "USER_AUTH", "USER_START", "USER_ACCT", "CRED_ACQ", "LOGIN")
C3_RX = {
    "threat_score": re.compile(r"threat[_ ]?score", re.I),
    "investigation_priority": re.compile(r"investigation[_ ]?priority", re.I),
    "cti_confidence": re.compile(r"(cti[_ ]?)?confidence", re.I),
    "freshness": re.compile(r"fresh", re.I),
    "asset_criticality": re.compile(r"(asset[_ ]?)?critical", re.I),
}
_WAZUH_CACHE: dict = {}


def _iso(us: int | None) -> str | None:
    return datetime.fromtimestamp(us / 1e6, UTC).isoformat() if us else None


def _members(zf: zipfile.ZipFile) -> dict:
    return {i.filename: i for i in zf.infolist() if not i.is_dir()}


def _strip_root(name: str) -> str:
    return name.split("/", 1)[1] if "/" in name else name


def _host(name: str):
    p = name.split("/")
    return p[1] if len(p) >= 3 else None


def _naive_utc(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


# ---------------------------------------------------------------- attackmate labels
def _split(v):
    return v.split(",") if isinstance(v, str) else []


def load_attackmate(zf: zipfile.ZipFile, member: str) -> tuple[list[dict], int]:
    entries, bad = [], 0
    with zf.open(member) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                bad += 1
                continue
            if isinstance(obj, dict):
                entries.append(obj)
    return entries, bad


def analyze_labels(entries: list[dict]) -> dict:
    steps, cleaning = [], []
    tactic_variants = defaultdict(Counter)
    meta_keys = Counter()
    kinds = Counter()
    for idx, e in enumerate(entries):
        p = e.get("parameters") if isinstance(e.get("parameters"), dict) else {}
        m = p.get("metadata")
        if isinstance(m, dict):
            meta_keys.update(m.keys())
        tech_raw = m.get("techniques") if isinstance(m, dict) else None
        tac_raw = m.get("tactics") if isinstance(m, dict) else None
        ids, issues_t = [], []
        for part in _split(tech_raw):
            c = part.strip().upper()
            iss = []
            if part != part.strip():
                iss.append("whitespace")
            if part.strip() != part.strip().upper():
                iss.append("case")
            if c and not TECH_RX.match(c):
                iss.append("invalid_format")
            if c:
                ids.append(c)
            if iss:
                issues_t.append({"part": part, "cleaned": c, "issues": iss})
        if issues_t:
            cleaning.append({"step": idx, "field": "techniques", "raw": tech_raw, "problems": issues_t})
        tacs, issues_c = [], []
        for part in _split(tac_raw):
            c = " ".join(part.split())
            iss = []
            if part != part.strip() or "  " in part:
                iss.append("whitespace")
            if c:
                tacs.append(c)
                tactic_variants[c.lower()][c] += 1
            if iss:
                issues_c.append({"part": part, "cleaned": c, "issues": iss})
        if issues_c:
            cleaning.append({"step": idx, "field": "tactics", "raw": tac_raw, "problems": issues_c})
        tn = m.get("technique_name") if isinstance(m, dict) else None
        if isinstance(tn, str) and tn != tn.strip():
            cleaning.append({"step": idx, "field": "technique_name", "raw": tn, "problems": [{"issues": ["whitespace"]}]})
        labeled = bool(ids)
        if m is None:
            kinds["metadata_null"] += 1 if not labeled else 0
        elif isinstance(m, dict) and not labeled:
            kinds["metadata_dict_without_technique"] += 1
        steps.append({"index": idx, "type": e.get("type"), "cmd": str(e.get("cmd"))[:70], "ids": ids,
                      "tactics": tacs, "labeled": labeled, "metadata": m})
    case_variants = {k: dict(v) for k, v in tactic_variants.items() if len(v) > 1}
    labeled_steps = [s for s in steps if s["labeled"]]
    unlabeled_steps = [s for s in steps if not s["labeled"]]
    multi = [s for s in labeled_steps if len(set(s["ids"])) > 1]
    adj_same = sum(1 for a, b in zip(steps, steps[1:])
                   if a["labeled"] and b["labeled"] and set(a["ids"]) == set(b["ids"]))
    seq_same = sum(1 for a, b in zip(labeled_steps, labeled_steps[1:]) if set(a["ids"]) == set(b["ids"]))
    seq_overlap = sum(1 for a, b in zip(labeled_steps, labeled_steps[1:]) if set(a["ids"]) & set(b["ids"]))

    def brief(s):
        return {"step_index": s["index"], "type": s["type"], "cmd": s["cmd"], "metadata": s["metadata"]}

    none_first = [s for s in unlabeled_steps if s["metadata"] is None]
    dict_first = [s for s in unlabeled_steps if isinstance(s["metadata"], dict)]
    picks = (dict_first[:1] + none_first[:2])
    for s in unlabeled_steps:
        if len(picks) >= 3:
            break
        if s not in picks:
            picks.append(s)
    return {
        "n_entries": len(steps),
        "n_labeled": len(labeled_steps),
        "n_unlabeled": len(unlabeled_steps),
        "unlabeled_breakdown": dict(kinds),
        "metadata_keys": dict(meta_keys),
        "metadata_key_anomalies": [k for k in meta_keys if not re.fullmatch(r"[A-Za-z_]+", k)],
        "distinct_techniques": sorted({i for s in labeled_steps for i in s["ids"]}),
        "distinct_tactics": sorted({t for s in steps for t in s["tactics"]}),
        "n_multi_technique_steps": len(multi),
        "multi_technique_examples": [dict(brief(s), ids=s["ids"]) for s in multi[:3]],
        "adjacent_steps_identical_technique_set": adj_same,
        "consecutive_labeled_identical_technique_set": seq_same,
        "consecutive_labeled_sharing_a_technique": seq_overlap,
        "labeled_examples": [brief(s) for s in labeled_steps[:3]],
        "unlabeled_examples": [brief(s) for s in picks[:3]],
        "cleaning_needed": cleaning,
        "tactic_case_variants": case_variants,
        "cleaned_technique_sequence": [s["ids"] for s in labeled_steps],
    }


# ---------------------------------------------------------------- wazuh
def _wazuh_json_stats(zf: zipfile.ZipFile, member: str) -> dict:
    stats = {"n": 0, "n_rule_id": 0, "n_mitre": 0, "rule_ids": set(), "mitre_ids": Counter(),
             "agents": Counter(), "top_keys": Counter(), "rule_keys": Counter(), "mitre_keys": Counter(),
             "ts": [], "sample_ts": None, "sample_mitre_alert": None, "bad_lines": 0}
    with zf.open(member) as fh:
        for raw in fh:
            raw = raw.strip()
            if not raw:
                continue
            try:
                d = json.loads(raw)
            except json.JSONDecodeError:
                stats["bad_lines"] += 1
                continue
            stats["n"] += 1
            stats["top_keys"].update(d.keys())
            r = d.get("rule") if isinstance(d.get("rule"), dict) else {}
            stats["rule_keys"].update(r.keys())
            if r.get("id"):
                stats["n_rule_id"] += 1
                stats["rule_ids"].add(r["id"])
            mit = r.get("mitre") if isinstance(r.get("mitre"), dict) else None
            ids = (mit or {}).get("id") or []
            if mit:
                stats["mitre_keys"].update(mit.keys())
            if ids:
                stats["n_mitre"] += 1
                stats["mitre_ids"].update(ids)
                if stats["sample_mitre_alert"] is None:
                    stats["sample_mitre_alert"] = {"timestamp": d.get("timestamp"),
                                                   "agent": (d.get("agent") or {}).get("name"),
                                                   "rule": {k: r.get(k) for k in ("id", "level", "description", "mitre")}}
            stats["agents"][(d.get("agent") or {}).get("name")] += 1
            ts = d.get("timestamp")
            stats["sample_ts"] = stats["sample_ts"] or ts
            try:
                stats["ts"].append((datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S.%f%z"), bool(ids), tuple(ids)))
            except (TypeError, ValueError):
                pass
    return stats


def analyze_wazuh(zf, members, window, am_ids) -> dict:
    files = sorted([n for n in members if _host(n) == "wazuh" and "/logs/alerts/" in n])
    out = {"exact_paths": [], "identical_file_groups": [], "json_files": {}}
    by_crc = defaultdict(list)
    for n in files:
        i = members[n]
        out["exact_paths"].append({"path": _strip_root(n), "size": i.file_size, "crc32": f"{i.CRC:08x}"})
        by_crc[(i.CRC, i.file_size)].append(_strip_root(n))
    out["identical_file_groups"] = [v for v in by_crc.values() if len(v) > 1]
    out["other_wazuh_log_candidates_present"] = sorted(
        _strip_root(n) for n in members if _host(n) == "wazuh" and members[n].file_size > 0
        and re.search(r"/(archives\.(json|log)|ossec\.log|api\.log|cluster\.log)$", n))
    for n in files:
        if not n.endswith(".json") or members[n].file_size == 0:
            continue
        key = (members[n].CRC, members[n].file_size)
        if key not in _WAZUH_CACHE:
            _WAZUH_CACHE[key] = _wazuh_json_stats(zf, n)
        st = _WAZUH_CACHE[key]
        tss = [t for t, _, _ in st["ts"]]
        rec = {
            "alerts": st["n"], "with_rule_id": st["n_rule_id"], "with_mitre_id": st["n_mitre"],
            "distinct_rule_ids": len(st["rule_ids"]), "distinct_mitre_ids": sorted(st["mitre_ids"]),
            "agents": dict(st["agents"]), "top_level_keys": dict(st["top_keys"]),
            "rule_keys": dict(st["rule_keys"]), "mitre_keys": dict(st["mitre_keys"]),
            "first_timestamp": min(tss).isoformat() if tss else None,
            "last_timestamp": max(tss).isoformat() if tss else None,
            "timestamp_example": st["sample_ts"], "unparseable_lines": st["bad_lines"],
            "example_alert_with_mitre": st["sample_mitre_alert"],
        }
        if window and st["ts"]:
            inw = [(t, m, ids) for t, m, ids in st["ts"] if window[0] <= t <= window[1]]
            wm = Counter(i for _, m, ids in inw if m for i in ids)
            rec["alerts_inside_attackmate_window_assuming_utc"] = len(inw)
            rec["mitre_alerts_inside_window"] = sum(1 for _, m, _ in inw if m)
            rec["mitre_ids_inside_window"] = sorted(wm)
            rec["mitre_ids_inside_window_also_in_attackmate"] = sorted(set(wm) & set(am_ids))
        out["json_files"][_strip_root(n)] = rec
    return out


# ---------------------------------------------------------------- timestamps / sources
def _journal_header(h: bytes):
    if len(h) < 208 or h[:8] != b"LPKSHHRH":
        return None
    incompat = struct.unpack_from("<I", h, 12)[0]
    n_entries = struct.unpack_from("<Q", h, 152)[0]
    head_rt, tail_rt = struct.unpack_from("<QQ", h, 184)
    return {"head": head_rt, "tail": tail_rt, "n_entries": n_entries, "incompat_flags": incompat}


def _journal_sample(buf: bytes) -> dict:
    out = {"first_entry_realtime_utc": [], "message_strings_found_uncompressed": []}
    try:
        off = struct.unpack_from("<Q", buf, 88)[0]
        n = 0
        while off + 40 <= len(buf) and n < 50000 and len(out["first_entry_realtime_utc"]) < 3:
            otype = buf[off]
            size = struct.unpack_from("<Q", buf, off + 8)[0]
            if size < 16:
                break
            if otype == 3:
                seq, rt, _ = struct.unpack_from("<QQQ", buf, off + 16)
                out["first_entry_realtime_utc"].append({"seqnum": seq, "realtime_utc": _iso(rt)})
            off = (off + size + 7) & ~7
            n += 1
    except struct.error:
        pass
    for m in re.finditer(rb"MESSAGE=([\x20-\x7e]{8,140})", buf):
        out["message_strings_found_uncompressed"].append(m.group(1).decode())
        if len(out["message_strings_found_uncompressed"]) >= 3:
            break
    return out


def _epoch_dt(sec: float) -> datetime:
    return datetime.fromtimestamp(sec, UTC)


def analyze_sources(zf, members, entries) -> dict:
    out = {"journal": {}, "audit.log": {}, "collectd.log": {}, "attacker_text_logs": {}, "samples": {}}
    # journals
    per_host = defaultdict(list)
    largest = {}
    for n, i in members.items():
        if re.search(r"\.journal~?$", n) and i.file_size >= 208:
            with zf.open(n) as fh:
                h = _journal_header(fh.read(208))
            host = _host(n)
            per_host[host].append(h)
            if posixpath.basename(n) == "system.journal" and (host not in largest or i.file_size > members[largest[host]].file_size):
                largest[host] = n
    for host, hs in per_host.items():
        good = [h for h in hs if h]
        out["journal"][host] = {
            "files": len(hs), "unreadable_headers": len(hs) - len(good),
            "min": _iso(min(h["head"] for h in good)) if good else None,
            "max": _iso(max(h["tail"] for h in good)) if good else None,
            "entries_in_headers": sum(h["n_entries"] for h in good),
        }
    for host, n in list(largest.items())[:2]:
        with zf.open(n) as fh:
            buf = fh.read(4 * 1024 * 1024)
        out["samples"].setdefault("journal", {})[f"{host}:{_strip_root(n)}"] = _journal_sample(buf)
    out["samples"]["journal_format_note"] = (
        "Binary systemd journal (signature LPKSHHRH). Header realtime fields are microseconds since the Unix "
        "epoch (UTC by systemd definition). Per-entry text fields were not decoded (UNVERIFIED).")
    # audit + sshd records
    sshd_records = []
    for n, i in members.items():
        if n.endswith("/logs/log/audit/audit.log") and i.file_size:
            data = zf.read(n)
            ts = [float(x) for x in re.findall(rb"audit\((\d+\.\d+):", data)]
            lines = data.decode("utf-8", "replace").splitlines()
            host = _host(n)
            if ts:
                out["audit.log"][host] = {"min": _epoch_dt(min(ts)).isoformat(), "max": _epoch_dt(max(ts)).isoformat(),
                                          "records": len(ts)}
            out["samples"].setdefault("audit.log", {})[host] = [lines[0][:170], lines[-1][:170]]
            for ln in lines:
                if ln.startswith("type=") and "sshd" in ln and any(ln.startswith("type=" + t) for t in SSHD_AUDIT_TYPES):
                    m = re.search(r"audit\((\d+\.\d+):", ln)
                    if m:
                        sshd_records.append((float(m.group(1)), host, ln.split()[0]))
    out["samples"]["audit.log_format_note"] = "msg=audit(<unix epoch seconds.millis>:<serial>): epoch time => no timezone ambiguity (UTC)."
    # collectd
    for n, i in members.items():
        if n.endswith("/logs/log/collectd/collectd.log") and i.file_size:
            text = zf.read(n).decode("utf-8", "replace")
            lines = text.splitlines()
            br = re.findall(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]", text, re.M)
            offsets = set()
            for a, b in zip(lines, lines[1:300]):
                m = re.match(r"^\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\]", a)
                m2 = re.match(r"^\S+ \S+ (\d{9,10})$", b)
                if m and m2:
                    bracket = calendar.timegm(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").timetuple())
                    offsets.add(bracket - int(m2.group(1)))
            host = _host(n)
            out["collectd.log"][host] = {"min": br[0] if br else None, "max": br[-1] if br else None,
                                         "bracket_minus_epoch_seconds_observed": sorted(offsets)[:5]}
            out["samples"].setdefault("collectd.log", {})[host] = lines[:2]
    out["samples"]["collectd.log_format_note"] = (
        "'[YYYY-MM-DD HH:MM:SS]' without timezone; value lines carry a unix epoch. bracket_minus_epoch_seconds_observed == [0] "
        "means the bracket time equals UTC epoch time.")
    # attacker text logs
    for n, i in members.items():
        if _host(n) == "attacker" and re.search(r"/logs/log/(auth\.log|syslog)$", n) and i.file_size:
            lines = zf.read(n).decode("utf-8", "replace").splitlines()
            iso = [re.match(r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+[+-]\d\d:\d\d)", ln) for ln in lines]
            iso = [m.group(1) for m in iso if m]
            out["attacker_text_logs"][posixpath.basename(n)] = {
                "lines": len(lines), "first": lines[0][:130] if lines else None, "last": lines[-1][:130] if lines else None,
                "min": min(iso) if iso else None, "max": max(iso) if iso else None}
    # timezone config of hosts
    tz = {}
    for n in members:
        if n.endswith("/configs/etc/timezone"):
            tz[_host(n)] = zf.read(n).decode("utf-8", "replace").strip()
    out["host_timezone_files"] = tz
    out["_sshd_records"] = sshd_records
    return out


def alignment(entries, sources, wazuh_json) -> dict:
    starts = sorted(_naive_utc(e["start-datetime"]) for e in entries if isinstance(e.get("start-datetime"), str))
    if not starts:
        return {"verdict": "unclear (no start-datetime values)", "ranges": [], "ssh_proximity": []}
    first, last = starts[0], starts[-1]
    rows = []

    def add(source, host, mn, mx):
        if not (mn and mx):
            return
        mn_d = datetime.fromisoformat(mn.replace(" ", "T")).replace(tzinfo=UTC) if "+" not in mn[10:] else datetime.fromisoformat(mn)
        mx_d = datetime.fromisoformat(mx.replace(" ", "T")).replace(tzinfo=UTC) if "+" not in mx[10:] else datetime.fromisoformat(mx)
        rows.append({"source": source, "host": host, "min": mn, "max": mx,
                     "first_step_inside": mn_d <= first <= mx_d, "last_step_inside": mn_d <= last <= mx_d})

    for h, v in sources["journal"].items():
        add("journal", h, v["min"], v["max"])
    for h, v in sources["audit.log"].items():
        add("audit.log", h, v["min"], v["max"])
    for h, v in sources["collectd.log"].items():
        add("collectd.log", h, v["min"], v["max"])
    for name, v in sources["attacker_text_logs"].items():
        add(name, "attacker", v["min"], v["max"])
    for path, v in wazuh_json.items():
        if path.endswith("/alerts.json") or path == "logs/alerts/alerts.json":
            add("wazuh alerts.json", "wazuh", v["first_timestamp"], v["last_timestamp"])
    # sshd audit proximity
    recs = sources.get("_sshd_records", [])
    ssh_steps = [(i, e) for i, e in enumerate(entries)
                 if isinstance(e.get("start-datetime"), str) and (e.get("type") == "ssh" or re.search(r"\b(ssh|scp|sshpass)\b", str(e.get("cmd"))[:60]))][:3]
    prox = []
    for i, e in ssh_steps:
        t = _naive_utc(e["start-datetime"]).timestamp()
        if recs:
            r = min(recs, key=lambda x: abs(x[0] - t))
            prox.append({"step_index": i, "start_datetime": e["start-datetime"], "nearest_sshd_audit_record": {
                "host": r[1], "type": r[2], "utc": _epoch_dt(r[0]).isoformat(), "delta_seconds_audit_minus_step": round(r[0] - t, 3)}})
    close = sum(1 for p in prox if abs(p["nearest_sshd_audit_record"]["delta_seconds_audit_minus_step"]) <= 30)
    if prox and close >= 2 and close * 2 >= len(prox):
        verdict = (f"consistent with UTC: {close}/{len(prox)} ssh-related steps have an sshd audit record within 30 s "
                   "when the attackmate time is read as UTC")
    else:
        verdict = "unclear: sshd audit proximity did not give a clear match" if prox else "unclear: no ssh-related steps or sshd audit records"
    return {"attackmate_first": first.isoformat(), "attackmate_last": last.isoformat(), "ranges": rows,
            "ssh_proximity": prox, "verdict": verdict}


# ---------------------------------------------------------------- run identification
def run_identification(zf, members, entries, stem) -> dict:
    kw = re.compile(rb"(scenario|run[_ -]?id|simulation|attackmate|experiment)", re.I)
    readmes = [n for n, i in members.items() if posixpath.basename(n).upper().startswith("README") and i.file_size < 200000]
    hits = [_strip_root(n) for n in readmes if kw.search(zf.read(n))]
    ph = [n for n in members if n.endswith(".placeholder")]
    ph_ne = [n for n in ph if members[n].file_size]
    roots = {n.split("/")[0] for n in members}
    out = {"zip_comment": zf.comment.decode("utf-8", "replace"), "root_folders": sorted(roots),
           "root_folder_equals_archive_stem": roots == {stem},
           "readme_files_checked": len(readmes), "readme_files_with_scenario_or_run_keywords": hits[:5],
           "placeholder_files": len(ph), "placeholder_nonempty": len(ph_ne),
           "placeholder_nonempty_example": (_strip_root(ph_ne[0]), zf.read(ph_ne[0])[:80].decode("utf-8", "replace")) if ph_ne else None,
           "attackmate_json_count": sum(1 for n in members if posixpath.basename(n) == "attackmate.json")}
    facts = [n for n in members if n.endswith("/wazuh/facts.json")]
    if facts:
        try:
            d = json.loads(zf.read(facts[0]))
            dt_ = (d.get("ansible_facts") or {}).get("ansible_date_time") or (d.get("ansible_facts") or {}).get("date_time") or {}
            out["wazuh_facts_json"] = {"inventory_hostname": d.get("inventory_hostname"), "group_names": d.get("group_names"),
                                       "gathered_iso8601": dt_.get("iso8601"), "has_run_or_scenario_key": any(
                                           re.search(r"scenario|run_id", k, re.I) for k in d)}
        except Exception as exc:
            out["wazuh_facts_json"] = {"error": f"{type(exc).__name__}"}
    starts = [_naive_utc(e["start-datetime"]) for e in entries if isinstance(e.get("start-datetime"), str)]
    if len(starts) > 1:
        gaps = [(b - a).total_seconds() for a, b in zip(starts, starts[1:])]
        out["attackmate_timeline"] = {"steps": len(starts), "monotonic_non_decreasing": all(g >= 0 for g in gaps),
                                      "max_gap_seconds": round(max(gaps), 1), "duration_seconds": round((starts[-1] - starts[0]).total_seconds(), 1)}
    return out


# ---------------------------------------------------------------- orchestration
def inspect_scenario(path) -> dict:
    stem = posixpath.splitext(posixpath.basename(str(path)))[0]
    try:
        with zipfile.ZipFile(path) as zf:
            members = _members(zf)
            res = {"archive": posixpath.basename(str(path))}
            hosts = sorted({_host(n) for n in members if _host(n)})
            res["hosts"] = hosts
            am = sorted(n for n in members if posixpath.basename(n) == "attackmate.json")
            res["attackmate_member"] = [_strip_root(n) for n in am]
            entries, bad = ([], 0)
            if am:
                entries, bad = load_attackmate(zf, am[0])
            res["attackmate_unparseable_lines"] = bad
            res["labels"] = analyze_labels(entries)
            starts = sorted(_naive_utc(e["start-datetime"]) for e in entries if isinstance(e.get("start-datetime"), str))
            res["attackmate_window_naive"] = [starts[0].replace(tzinfo=None).isoformat(), starts[-1].replace(tzinfo=None).isoformat()] if starts else None
            window = (starts[0], starts[-1]) if starts else None
            res["attackmate_step_types"] = dict(Counter(e.get("type") for e in entries))
            res["attackmate_top_level_keys"] = dict(Counter(k for e in entries for k in e))
            res["attackmate_parameter_keys"] = dict(Counter(k for e in entries if isinstance(e.get("parameters"), dict) for k in e["parameters"]))
            res["wazuh"] = analyze_wazuh(zf, members, window, res["labels"]["distinct_techniques"])
            src = analyze_sources(zf, members, entries)
            res["sources"] = {k: v for k, v in src.items() if k != "_sshd_records"}
            res["alignment"] = alignment(entries, src, res["wazuh"]["json_files"])
            res["run_identification"] = run_identification(zf, members, entries, stem)
            # log source inventory by exact path patterns
            ls = defaultdict(lambda: defaultdict(lambda: [0, 0]))
            pats = [("journal", r"/logs/log/journal/.+\.journal~?$"), ("audit.log", r"/logs/log/audit/audit\.log$"),
                    ("collectd.log", r"/logs/log/collectd/collectd\.log$"), ("auth.log", r"/logs/log/auth\.log$"),
                    ("syslog", r"/logs/log/syslog$"), ("wazuh alerts", r"/wazuh/logs/alerts/"),
                    ("attackmate.json", r"/logs/attackmate\.json$")]
            for n, i in members.items():
                if i.file_size == 0:
                    continue
                for label, rx in pats:
                    if re.search(rx, n):
                        c = ls[_host(n)][label]
                        c[0] += 1
                        c[1] += i.file_size
            res["log_sources_by_host"] = {h: {k: {"files": v[0], "bytes": v[1]} for k, v in d.items()} for h, d in ls.items()}
            # C3-style search in the JSON key sets that were actually parsed
            keysets = {"attackmate.json keys": set(res["attackmate_top_level_keys"]) | set(res["attackmate_parameter_keys"]) | set(res["labels"]["metadata_keys"])}
            wk = set()
            for v in res["wazuh"]["json_files"].values():
                wk |= set(v["top_level_keys"]) | set(v["rule_keys"])
            keysets["wazuh alert keys (top-level + rule.*)"] = wk
            res["c3_style_search"] = {scope: {k: sorted(x for x in names if rx.search(x)) for k, rx in C3_RX.items()} for scope, names in keysets.items()}
            return res
    except (zipfile.BadZipFile, OSError) as exc:
        return {"archive": posixpath.basename(str(path)), "error": f"{type(exc).__name__}: {exc}"}
