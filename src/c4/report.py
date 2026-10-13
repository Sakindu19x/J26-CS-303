"""Markdown rendering for reports/dataset_inventory.md (curated, verified facts only)."""
from __future__ import annotations

import json


def _j(obj, n=600) -> str:
    s = json.dumps(obj, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + " ...(truncated)"


def _short(name: str) -> str:
    return name.replace(".zip", "")


def verified_field_table(details: dict) -> list[dict]:
    """Rows: field, source, meaning, kind, evidence. Evidence counts come from the computed details."""
    ok = {k: d for k, d in details.items() if "labels" in d}
    if not ok:
        return []

    def per(fn):
        return "; ".join(f"{_short(k)}: {fn(d)}" for k, d in ok.items())

    wz = lambda d: next(iter(d["wazuh"]["json_files"].values()), None)
    rows = [
        ("start-datetime", "attackmate.json", "Step start time, ISO 8601 without timezone", "metadata",
         per(lambda d: f"{d['attackmate_window_naive'][0]} .. {d['attackmate_window_naive'][1]}" if d["attackmate_window_naive"] else "none")),
        ("type, cmd", "attackmate.json", "Attack tool/step kind and command executed by AttackMate", "metadata",
         per(lambda d: f"{d['labels']['n_entries']} steps, types {sorted(d['attackmate_step_types'])[:6]}")),
        ("parameters.metadata.techniques", "attackmate.json", "ATT&CK technique IDs of the step; comma-separated string, may hold several IDs",
         "GROUND TRUTH (label)", per(lambda d: f"{d['labels']['n_labeled']}/{d['labels']['n_entries']} steps labeled")),
        ("parameters.metadata.tactics", "attackmate.json", "ATT&CK tactic names of the step; comma-separated string",
         "GROUND TRUTH (label)", per(lambda d: f"{len(d['labels']['distinct_tactics'])} distinct tactics")),
        ("parameters.metadata.technique_name", "attackmate.json", "Technique name text", "GROUND TRUTH (label text)",
         per(lambda d: f"key present: {'technique_name' in d['labels']['metadata_keys']}")),
        ("parameters.metadata.action / delayed_manifestation", "attackmate.json", "Meaning not documented in the archive (UNVERIFIED)",
         "unverified", per(lambda d: str({k: v for k, v in d["labels"]["metadata_keys"].items() if k in ("action", "delayed_manifestation")} or "absent"))),
        ("parameters.hostname / username / creates_session", "attackmate.json", "Target host / account / session of SSH-type steps (where present)",
         "metadata", per(lambda d: f"hostname in {d['attackmate_parameter_keys'].get('hostname', 0)} steps")),
        ("rule.id, rule.level, rule.description", "wazuh/logs/alerts/alerts.json", "Wazuh rule that fired (detector output, not attack ground truth)",
         "metadata (detector output)", per(lambda d: f"{wz(d)['with_rule_id']}/{wz(d)['alerts']} alerts have rule.id" if wz(d) else "no alerts.json")),
        ("rule.mitre.id / tactic / technique", "wazuh/logs/alerts/alerts.json", "ATT&CK mapping attached by Wazuh rules; present on a subset; NOT the AttackMate truth",
         "metadata (detector-derived label)", per(lambda d: f"{wz(d)['with_mitre_id']}/{wz(d)['alerts']} alerts" if wz(d) else "no alerts.json")),
        ("timestamp, agent.name, location, full_log, data", "wazuh alerts.json", "Alert time (ISO 8601, +0000), source agent, log origin, raw log line",
         "metadata", per(lambda d: f"agents {list(wz(d)['agents'])}" if wz(d) else "n/a")),
        ("msg=audit(epoch:serial), type, syscall, AUID, UID ...", "<host>/logs/log/audit/audit.log", "Linux audit records (epoch UTC)", "metadata",
         per(lambda d: "records " + str({h: v['records'] for h, v in d['sources']['audit.log'].items()}))),
        ("[YYYY-MM-DD HH:MM:SS] + epoch metric lines", "<host>/logs/log/collectd/collectd.log", "collectd metric dump; no ground truth", "metadata",
         per(lambda d: "hosts " + str(sorted(d['sources']['collectd.log'])))),
        ("journal entries (realtime in header/entry)", "<host>/logs/log/journal/*.journal", "Binary systemd journal; entry fields not decoded (UNVERIFIED)", "metadata (unverified fields)",
         per(lambda d: "hosts " + str(sorted(d['sources']['journal'])))),
        ("ISO timestamp, host, process", "attacker/logs/log/auth.log, syslog", "Attacker host text logs (ISO 8601 +00:00)", "metadata",
         per(lambda d: str(sorted(d['sources']['attacker_text_logs'])))),
    ]
    c3 = {}
    for k, d in ok.items():
        for scope, found in d["c3_style_search"].items():
            for key, names in found.items():
                if names:
                    c3.setdefault((scope, key), set()).update(names)
    rows.append(("C3-style fields (threat score, priority, CTI confidence, freshness, asset criticality)", "searched: attackmate.json keys, Wazuh alert top-level + rule.* keys",
                 "Not found by key-name search" if not c3 else "Name matches: " + _j({f"{a}|{b}": sorted(v) for (a, b), v in c3.items()}),
                 "absent (within the searched scope)", "regex over parsed JSON key names; journal/audit/collectd text not searched for these names"))
    return [dict(zip(("field", "source", "meaning", "kind", "evidence"), r)) for r in rows]


def render_markdown(inv: dict) -> str:
    d = inv["details"]
    ok = {k: v for k, v in d.items() if "labels" in v}
    L = ["# Dataset Inventory (CAM-LDS)", "", f"Generated: {inv['generated_at']}", f"Raw dir: `{inv['raw_dir']}` (read-only)", ""]
    L += ["## 1. Archive status", "", "| Archive | Present | Readable | Files | Error |", "|---|---|---|---|---|"]
    for a in inv["archives"]:
        L.append(f"| {a['archive']} | {a['present']} | {a['readable']} | {a.get('n_files', '-')} | {a.get('error') or ''} |")
    L += ["", "Issues: " + (", ".join(f"{i['type']} `{i['file']}`" for i in inv["issues"]) or "none"), ""]
    if not ok:
        L += ["No readable archives with attackmate data; nothing further to report.", ""]
        return "\n".join(L) + "\n"

    # ---- comparison table
    names = list(ok)
    L += ["## 2. Scenario comparison", "", "| Metric | " + " | ".join(_short(n) for n in names) + " |", "|---|" + "---|" * len(names)]

    def row(label, fn):
        L.append(f"| {label} | " + " | ".join(str(fn(ok[n])) for n in names) + " |")

    wzf = lambda x: next((v for p, v in x["wazuh"]["json_files"].items() if p.endswith("alerts/alerts.json")), None) or {}
    row("attackmate steps", lambda x: x["labels"]["n_entries"])
    row("labeled / unlabeled", lambda x: f"{x['labels']['n_labeled']} / {x['labels']['n_unlabeled']}")
    row("steps with >1 technique", lambda x: x["labels"]["n_multi_technique_steps"])
    row("attackmate time range (no tz)", lambda x: " .. ".join(x["attackmate_window_naive"] or ["-"]))
    row("duration (s)", lambda x: (x["run_identification"].get("attackmate_timeline") or {}).get("duration_seconds", "-"))
    row("distinct techniques (cleaned)", lambda x: len(x["labels"]["distinct_techniques"]))
    row("distinct tactics (cleaned)", lambda x: len(x["labels"]["distinct_tactics"]))
    row("hosts", lambda x: ", ".join(x["hosts"]))
    row("Wazuh alerts.json (size B)", lambda x: next((e["size"] for e in x["wazuh"]["exact_paths"] if e["path"].endswith("alerts/alerts.json")), "-"))
    row("Wazuh alerts / with rule.id / with MITRE", lambda x: f"{wzf(x).get('alerts', '-')} / {wzf(x).get('with_rule_id', '-')} / {wzf(x).get('with_mitre_id', '-')}")
    row("Wazuh alerts inside attackmate window (UTC reading)", lambda x: wzf(x).get("alerts_inside_attackmate_window_assuming_utc", "-"))
    row("timestamp reading", lambda x: x["alignment"]["verdict"].split(":")[0])
    L.append("")

    # ---- per scenario
    for n, x in ok.items():
        lb = x["labels"]
        L += [f"## 3. {_short(n)}", ""]
        L += [f"- attackmate: `{x['attackmate_member']}`; unparseable lines: {x['attackmate_unparseable_lines']}",
              f"- step types: {x['attackmate_step_types']}",
              f"- distinct techniques ({len(lb['distinct_techniques'])}): {lb['distinct_techniques']}",
              f"- distinct tactics ({len(lb['distinct_tactics'])}): {lb['distinct_tactics']}",
              f"- unlabeled breakdown: {lb['unlabeled_breakdown']}", f"- metadata keys: {lb['metadata_keys']}",
              f"- metadata key anomalies (non-identifier characters): {lb['metadata_key_anomalies'] or 'none'}", ""]
        L += ["### Log sources per host (exact path patterns, non-empty files)", "", "| Host | Sources (files / bytes) |", "|---|---|"]
        for h, v in sorted(x["log_sources_by_host"].items()):
            L.append(f"| {h} | " + "; ".join(f"{k}: {s['files']} / {s['bytes']}" for k, s in v.items()) + " |")
        L += ["", "### Label analysis", "",
              f"- steps with more than one technique: **{lb['n_multi_technique_steps']}**", "- real examples:", "```json"]
        L += [_j(e, 500) for e in lb["multi_technique_examples"]] + ["```"]
        L += [f"- strictly adjacent steps (both labeled) with identical technique set: **{lb['adjacent_steps_identical_technique_set']}**",
              f"- consecutive labeled steps (unlabeled skipped) with identical technique set: **{lb['consecutive_labeled_identical_technique_set']}**",
              f"- consecutive labeled steps sharing at least one technique: {lb['consecutive_labeled_sharing_a_technique']}", "",
              "Real `parameters.metadata` of 3 labeled steps:", "```json"]
        L += [_j(e, 500) for e in lb["labeled_examples"]] + ["```", "Real `parameters.metadata` of 3 unlabeled steps:", "```json"]
        L += [_j(e, 500) for e in lb["unlabeled_examples"]] + ["```", ""]
        L += ["Values needing whitespace / case cleaning:", ""]
        if lb["cleaning_needed"]:
            for c in lb["cleaning_needed"]:
                L.append(f"- step {c['step']} `{c['field']}`: raw `{c['raw']!r}` -> problems "
                         + ", ".join(f"{p.get('part')!r}->{p.get('cleaned')!r} {p['issues']}" for p in c["problems"]))
        else:
            L.append("- none")
        L += [f"- tactic spellings differing only by case: {lb['tactic_case_variants'] or 'none'}", "",
              "Ordered cleaned technique sequence (labeled steps only; `+` joins several techniques in one step):", "",
              "`" + " -> ".join("+".join(s) for s in lb["cleaned_technique_sequence"]) + "`", ""]

        # wazuh
        w = x["wazuh"]
        L += ["### Wazuh files (wazuh host, exact archive paths)", "", "| Path | Size | CRC32 |", "|---|---|---|"]
        L += [f"| `{e['path']}` | {e['size']} | {e['crc32']} |" for e in w["exact_paths"]]
        L += ["", f"- byte-identical groups (same size and CRC32): {w['identical_file_groups'] or 'none'}",
              f"- archives.json / ossec.log / api.log / cluster.log present: {w['other_wazuh_log_candidates_present'] or 'none found'}", ""]
        for p, v in w["json_files"].items():
            L += [f"- `{p}`: {v['alerts']} alerts; rule.id {v['with_rule_id']}; MITRE ids on {v['with_mitre_id']}; "
                  f"{v['distinct_rule_ids']} rule ids; time {v['first_timestamp']} .. {v['last_timestamp']}; agents {v['agents']}",
                  f"  - in attackmate window (UTC reading): {v.get('alerts_inside_attackmate_window_assuming_utc', '-')} alerts, "
                  f"{v.get('mitre_alerts_inside_window', '-')} with MITRE; MITRE ids in window {v.get('mitre_ids_inside_window', '-')}; "
                  f"also in attackmate labels: {v.get('mitre_ids_inside_window_also_in_attackmate', '-')}"]
        first = next(iter(w["json_files"].values()), None)
        if first and first.get("example_alert_with_mitre"):
            L += ["", "Real Wazuh alert fields (example with MITRE):", "```json", _j(first["example_alert_with_mitre"], 700), "```"]
        L += [""]

        # timestamps
        s = x["sources"]
        L += ["### Timestamp formats (real samples)", "", f"- **journal**: {s['samples']['journal_format_note']}"]
        for k, v in s["samples"].get("journal", {}).items():
            L += [f"  - `{k}`: first entries {v['first_entry_realtime_utc']}; message strings {v['message_strings_found_uncompressed']}"]
        for h, v in s["journal"].items():
            L.append(f"  - {h}: {v['files']} files, header range {v['min']} .. {v['max']}")
        L += [f"- **audit.log**: {s['samples']['audit.log_format_note']}"]
        for h, v in s["samples"].get("audit.log", {}).items():
            L += [f"  - {h}: `{v[0]}`  ...  `{v[1]}`; range {s['audit.log'][h]['min']} .. {s['audit.log'][h]['max']}"]
        L += [f"- **collectd.log**: {s['samples']['collectd.log_format_note']}"]
        for h, v in s["samples"].get("collectd.log", {}).items():
            L += [f"  - {h}: `{v[0]}` / `{v[1] if len(v) > 1 else ''}`; range {s['collectd.log'][h]['min']} .. {s['collectd.log'][h]['max']}; "
                  f"bracket-epoch offsets {s['collectd.log'][h]['bracket_minus_epoch_seconds_observed']}"]
        L += [f"- **attacker auth.log / syslog**: {_j(s['attacker_text_logs'], 700)}",
              f"- **Wazuh alerts**: timestamp example `{first['timestamp_example'] if first else None}` (ISO 8601 with +0000 offset)",
              f"- **attackmate.json**: `start-datetime` e.g. `{x['attackmate_window_naive'][0] if x['attackmate_window_naive'] else None}`; no timezone",
              f"- host `/etc/timezone` files: {s['host_timezone_files']}", ""]
        a = x["alignment"]
        L += ["### Alignment of attackmate times with host logs", "", f"attackmate first/last step: {a.get('attackmate_first')} .. {a.get('attackmate_last')} (read as UTC)", "",
              "| Source | Host | Log min | Log max | First step inside | Last step inside |", "|---|---|---|---|---|---|"]
        L += [f"| {r['source']} | {r['host']} | {r['min']} | {r['max']} | {r['first_step_inside']} | {r['last_step_inside']} |" for r in a["ranges"]]
        L += ["", "sshd audit proximity (nearest sshd audit record to ssh-related steps):", "", "```json"] + [_j(p, 500) for p in a.get("ssh_proximity", [])] + ["```",
              f"**Verdict:** {a['verdict']}.", ""]

        # run id
        r = x["run_identification"]
        L += ["### Run identification", "", f"- root folder(s): {r['root_folders']} (equals archive name: {r['root_folder_equals_archive_stem']})",
              f"- zip comment: {r['zip_comment']!r}; attackmate.json files: {r['attackmate_json_count']}",
              f"- README files checked: {r['readme_files_checked']}; with scenario/run/simulation keywords: {r['readme_files_with_scenario_or_run_keywords'] or 'none'}",
              f"- .placeholder files: {r['placeholder_files']} (non-empty {r['placeholder_nonempty']}; example {r['placeholder_nonempty_example']})",
              f"- wazuh/facts.json: {r.get('wazuh_facts_json')}", f"- attackmate timeline: {r.get('attackmate_timeline')}", ""]

    # ---- cross-scenario notes
    L += ["## 4. Cross-scenario findings (computed)", ""]
    crcs = {}
    for n, x in ok.items():
        for e in x["wazuh"]["exact_paths"]:
            crcs.setdefault((e["path"].split("/")[-1], e["size"], e["crc32"]), []).append(_short(n))
    shared = {f"{k[0]} ({k[1]} B)": v for k, v in crcs.items() if len(v) > 1}
    L += [f"- Wazuh files byte-identical across several archives (same name, size, CRC32): {shared or 'none'}",
          "- Host logs (journal/audit/collectd) start before the attack window (see ranges above), so they are not limited to the simulated attack.", ""]

    L += ["## 5. Verified field table", "", "| Field | Source file | Meaning | Ground truth or metadata | Evidence |", "|---|---|---|---|---|"]
    for r in inv["verified_fields"]:
        L.append(f"| {r['field']} | {r['source']} | {r['meaning']} | {r['kind']} | {r['evidence']} |")
    L += ["", "## 6. Unverified / open items", "",
          "- Journal entry fields (`MESSAGE`, `_HOSTNAME`, ...) were not decoded; only header time ranges and uncompressed message strings were read.",
          "- Meaning of `metadata.action` / `delayed_manifestation` is not documented in the archives.",
          "- Whether each archive holds exactly one run: see per-scenario run identification; no explicit run ID was found in any README/placeholder.",
          "- Mapping of AttackMate steps to individual host log events has not been done.", ""]
    return "\n".join(L) + "\n"
