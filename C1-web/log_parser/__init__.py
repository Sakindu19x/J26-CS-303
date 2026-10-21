"""
Log parsers: convert raw web-server logs into the detection model's 14-column input format.

Kept separate from the model on purpose: each log format gets its own parser, and
every parser produces the same columns, so the trained model never changes.
"""

from log_parser.apache import parse_apache_file, parse_apache_log, parse_line

__all__ = ["parse_apache_file", "parse_apache_log", "parse_line"]
