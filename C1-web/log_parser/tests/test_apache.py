"""Parser tests (no model involved). Run from the RA 1 folder: python -m pytest log_parser -q"""

from pathlib import Path

from log_parser import parse_apache_file, parse_apache_log, parse_line
from src.config import CONTEXT_COLUMNS, DETECTION_FEATURES

SAMPLE = Path(__file__).resolve().parent.parent / "sample_access.log"

COMBINED = (
    '198.51.100.23 - - [21/Jul/2020:22:54:02 +0100] '
    '"GET /blog/index.php?id=1%27+UNION+SELECT HTTP/1.1" 200 512 "-" "sqlmap/1.4.7"'
)


def test_combined_line_maps_to_model_columns():
    row = parse_line(COMBINED)
    assert row["request_http_method"] == "GET"
    assert row["request_http_request"] == "/blog/index.php?id=1%27+UNION+SELECT"
    assert row["request_http_protocol"] == "HTTP/1.1"
    assert row["request_user_agent"] == "sqlmap/1.4.7"
    assert row["timestamp"] == "21/Jul/2020:22:54:02 +0100"
    assert row["src_ip"] == "198.51.100.23"


def test_missing_fields_become_empty_strings():
    row = parse_line(COMBINED)
    assert row["request_referer"] == ""          # "-" in the log
    assert row["request_cookie"] == ""           # not in this log format
    assert row["request_body"] == ""
    assert row["dst_ip"] is None                 # context the log does not carry


def test_common_format_without_referer_and_agent():
    row = parse_line('192.0.2.55 - - [21/Jul/2020:22:55:41 +0100] "GET /blog/feed/ HTTP/1.1" 200 2048')
    assert row["request_http_request"] == "/blog/feed/"
    assert row["request_user_agent"] == ""


def test_escaped_quote_in_user_agent():
    row = parse_line('192.0.2.1 - - [21/Jul/2020:10:00:00 +0100] "GET / HTTP/1.1" 200 1 "-" "bad\\"agent"')
    assert row["request_user_agent"] == 'bad"agent'


def test_invalid_lines_are_skipped_and_counted():
    table = parse_apache_log([COMBINED, "", "garbage line"])
    assert len(table) == 1
    assert table.attrs["skipped_lines"] == 1
    assert table.attrs["skipped_line_numbers"] == [3]


def test_output_has_exact_model_and_context_columns():
    table = parse_apache_file(SAMPLE)
    assert list(table.columns) == DETECTION_FEATURES + CONTEXT_COLUMNS
    assert len(table) == 6
    assert table.attrs["skipped_lines"] == 1
    assert table[DETECTION_FEATURES].isnull().sum().sum() == 0   # model input has no NaN
