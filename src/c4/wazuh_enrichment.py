"""Wazuh alert extraction and normalization within episode attack windows."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

UTC = timezone.utc

WAZUH_ALERT_COLUMNS = [
    "alert_id",
    "episode_id",
    "timestamp",
    "agent_name",
    "rule_id",
    "rule_description",
    "rule_level",
    "wazuh_mitre_ids",
    "wazuh_mitre_tactics",
    "src_ip",
    "user",
    "file_path",
    "is_detector_derived",
]


def parse_wazuh_timestamp(raw_ts: str) -> datetime | None:
    """Parse Wazuh alert timestamp (e.g. '2025-09-22T13:34:43.361+0000') into UTC datetime."""
    if not raw_ts:
        return None
    try:
        # Standardize +0000 to +00:00 for ISO parsing
        s = raw_ts.strip()
        if s.endswith("+0000"):
            s = s[:-5] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)
    except Exception:
        return None


def extract_wazuh_alerts(
    zf: zipfile.ZipFile,
    wazuh_member: str,
    episode_id: str,
    window_start: datetime | None,
    window_end: datetime | None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Extract and filter Wazuh alerts strictly from wazuh/logs/alerts/alerts.json within attack window."""
    alerts = []
    stats = {
        "total_alerts": 0,
        "unparseable_lines": 0,
        "in_window": 0,
        "excluded_before_window": 0,
        "excluded_after_window": 0,
        "excluded_unparseable_ts": 0,
    }

    with zf.open(wazuh_member) as fh:
        for idx, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            stats["total_alerts"] += 1
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                stats["unparseable_lines"] += 1
                continue

            dt = parse_wazuh_timestamp(d.get("timestamp"))
            if dt is None:
                stats["excluded_unparseable_ts"] += 1
                continue

            # Check window containment if window is specified
            if window_start and dt < window_start:
                stats["excluded_before_window"] += 1
                continue
            if window_end and dt > window_end:
                stats["excluded_after_window"] += 1
                continue

            stats["in_window"] += 1

            # Extract fields
            rule = d.get("rule") if isinstance(d.get("rule"), dict) else {}
            rule_id = rule.get("id")
            rule_desc = rule.get("description")
            rule_level = rule.get("level")

            mitre = rule.get("mitre") if isinstance(rule.get("mitre"), dict) else {}
            wazuh_mitre_ids = mitre.get("id", [])
            wazuh_mitre_tactics = mitre.get("tactic", [])

            agent = d.get("agent") if isinstance(d.get("agent"), dict) else {}
            agent_name = agent.get("name")

            data_block = d.get("data") if isinstance(d.get("data"), dict) else {}
            src_ip = data_block.get("srcip") or data_block.get("src_ip") or d.get("srcip")
            user = (
                data_block.get("srcuser")
                or data_block.get("dstuser")
                or data_block.get("user")
                or data_block.get("username")
                or d.get("srcuser")
                or d.get("dstuser")
            )
            file_path = (
                data_block.get("file")
                or data_block.get("path")
                or (d.get("syscheck") or {}).get("path")
            )

            alert_record = {
                "alert_id": f"{episode_id}-WZ-{idx + 1:05d}",
                "episode_id": episode_id,
                "timestamp": dt.isoformat(),
                "agent_name": agent_name,
                "rule_id": rule_id,
                "rule_description": rule_desc,
                "rule_level": rule_level,
                "wazuh_mitre_ids": json.dumps(wazuh_mitre_ids) if isinstance(wazuh_mitre_ids, list) else str(wazuh_mitre_ids),
                "wazuh_mitre_tactics": json.dumps(wazuh_mitre_tactics) if isinstance(wazuh_mitre_tactics, list) else str(wazuh_mitre_tactics),
                "src_ip": str(src_ip) if src_ip else None,
                "user": str(user) if user else None,
                "file_path": str(file_path) if file_path else None,
                "is_detector_derived": True,
            }
            alerts.append(alert_record)

    from collections import Counter
    rule_counts = Counter((str(a["rule_id"]), str(a["rule_description"])) for a in alerts)
    total_in_win = len(alerts)
    top_10 = []
    for (rid, rdesc), cnt in rule_counts.most_common(10):
        share = round((cnt / total_in_win * 100), 2) if total_in_win > 0 else 0.0
        top_10.append({
            "rule_id": rid,
            "rule_description": rdesc,
            "count": cnt,
            "share_percent": share,
        })
    stats["top_10_rules"] = top_10

    return alerts, stats
