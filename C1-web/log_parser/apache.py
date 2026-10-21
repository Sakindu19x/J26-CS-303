"""
Apache / Nginx access-log parser
Component 1: Adaptive Web Attack Detection & Correlation Model
Final Year Research - Group J26-CS-303

Turns raw access-log lines into the 14-column request table the detection model
was trained on (DETECTION_FEATURES), plus the 5 context columns kept for
correlation (CONTEXT_COLUMNS). Fields a log line does not carry are filled with
"" for request fields (as in src/data_preparation.py) and None for context.

Supported line formats (Apache and Nginx share them):
- combined: IP - user [time] "METHOD URI PROTOCOL" status size "referer" "user-agent"
- common:   IP - user [time] "METHOD URI PROTOCOL" status size
"""

import re

import pandas as pd

from src.config import CONTEXT_COLUMNS, DETECTION_FEATURES

# Quoted fields may contain escaped quotes (\"), which Apache writes for odd user-agents.
_QUOTED = r'"((?:[^"\\]|\\.)*)"'

LOG_LINE = re.compile(
    r"^(?P<ip>\S+) \S+ \S+ "
    r"\[(?P<time>[^\]]+)\] "
    + _QUOTED.replace("(", "(?P<request>", 1)
    + r" (?P<status>\d{3}|-) (?P<size>\d+|-)"
    + r"(?: " + _QUOTED.replace("(", "(?P<referer>", 1)
    + r" " + _QUOTED.replace("(", "(?P<agent>", 1) + r")?"
)


def _clean(value):
    """Logs write '-' for 'not present'; the model was trained with '' for absent fields."""
    if value is None or value == "-":
        return ""
    return value.replace('\\"', '"')


def _split_request(request_line):
    """'GET /a?b=1 HTTP/1.1' -> ('GET', '/a?b=1', 'HTTP/1.1'); tolerant of malformed lines."""
    parts = request_line.split(" ")
    if len(parts) >= 3:
        return parts[0], " ".join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return parts[0], parts[1], ""
    return "", request_line, ""


def parse_line(line):
    """Parse one log line into a dict of model + context columns, or None if it does not match."""
    match = LOG_LINE.match(line.strip())
    if not match:
        return None

    method, uri, protocol = _split_request(_clean(match["request"]))

    row = {column: "" for column in DETECTION_FEATURES}
    row.update({
        "request_http_method": method,
        "request_http_request": uri,          # kept percent-encoded, exactly as logged
        "request_http_protocol": protocol,
        "request_referer": _clean(match["referer"]),
        "request_user_agent": _clean(match["agent"]),
    })

    context = {column: None for column in CONTEXT_COLUMNS}
    context.update({
        "timestamp": match["time"],           # same format as SR-BH: 21/Jul/2020:22:53:19 +0100
        "src_ip": match["ip"],
    })
    return {**row, **context}


def parse_apache_log(lines):
    """
    Parse an iterable of access-log lines.

    Returns a DataFrame with DETECTION_FEATURES followed by CONTEXT_COLUMNS, one row
    per valid line. Lines that do not match are skipped; their count is stored in
    df.attrs["skipped_lines"] and their line numbers in df.attrs["skipped_line_numbers"].
    """
    rows, skipped = [], []
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        parsed = parse_line(line)
        if parsed is None:
            skipped.append(number)
        else:
            rows.append(parsed)

    table = pd.DataFrame(rows, columns=DETECTION_FEATURES + CONTEXT_COLUMNS)
    table.attrs["skipped_lines"] = len(skipped)
    table.attrs["skipped_line_numbers"] = skipped
    return table


def parse_apache_file(path, encoding="utf-8"):
    """Read and parse an access-log file."""
    with open(path, encoding=encoding, errors="replace") as handle:
        return parse_apache_log(handle)
