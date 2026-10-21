"""
Preview what the parser produces for a log file (no model involved).

Run from the RA 1 folder:
    python -m log_parser log_parser/sample_access.log
    python -m log_parser log_parser/sample_access.log log_parser/parsed_output.csv   # also save every column to CSV
"""

import sys

import pandas as pd

from log_parser import parse_apache_file

if len(sys.argv) not in (2, 3):
    sys.exit("Usage: python -m log_parser <access.log> [output.csv]")

table = parse_apache_file(sys.argv[1])
pd.set_option("display.max_colwidth", 45)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)

print(f"Parsed lines : {len(table)}")
print(f"Skipped lines: {table.attrs['skipped_lines']} {table.attrs['skipped_line_numbers'] or ''}")
print()
print(table[["timestamp", "src_ip", "request_http_method", "request_http_request", "request_user_agent"]])

if len(sys.argv) == 3:
    table.to_csv(sys.argv[2], index=False)
    print(f"\nAll {table.shape[1]} columns saved to: {sys.argv[2]}")
