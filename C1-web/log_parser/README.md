# log_parser

Converts raw web-server logs into the detection model's input format: the 14 request columns (`DETECTION_FEATURES`) plus the 5 context columns (`CONTEXT_COLUMNS`) from `src/config.py`.

It is **separate from the model on purpose**. Each log format gets its own parser, and all of them produce the same columns, so the trained model and preprocessor never change.

| File | What it is |
| --- | --- |
| `apache.py` | Parser for Apache/Nginx access logs (combined and common formats) |
| `__main__.py` | Preview: `python -m log_parser log_parser/sample_access.log`; add `log_parser/parsed_output.csv` at the end to save all 19 columns |
| `parsed_output.csv` | The parsed sample log (all 19 columns), for opening in Excel |
| `sample_access.log` | 7 example lines: normal, SQL injection, path traversal, login POST, common format, one invalid line |
| `tests/test_apache.py` | Parser tests: `python -m pytest log_parser -q` |

Run everything from the `RA 1` folder.

## What it fills

| Model column | From the log |
| --- | --- |
| `request_http_method`, `request_http_request`, `request_http_protocol` | the quoted request line (URI kept percent-encoded, as logged) |
| `request_referer`, `request_user_agent` | combined format only; `-` → `""` |
| all other request columns (body, cookie, accept…) | `""`: access logs don't record them (same as missing headers in training) |
| `timestamp`, `src_ip` | the log line |
| `src_port`, `dst_ip`, `dst_port` | `None`: not in access logs |

## Not done yet

- **Not connected to the model.** The future UI will call `parse_apache_file(...)`, then the saved preprocessor and model.
- Other formats (ModSecurity audit log, IIS W3C) will be added as separate parser files with the same output columns.
- Access logs carry fewer fields than SR-BH 2020 (no body, cookie or most headers), so accuracy on real logs must be checked separately.

## Finding from a sanity check (21 Oct 2026)

Running the 6 sample lines through the current saved model (not integrated, just a check):

- Attacks were detected: SQL injection (91%) and path traversal (99%).
- There were also **false alarms on normal lines**: Protocol Manipulation on `/blog/index.php?p=1` and `/blog/feed/`, and SQL Injection on a normal `POST /blog/wp-login.php`.
- Predictions changed a lot when only `request_host`, `request_user_agent` or `request_referer` changed. With the host filled in, a normal Firefox 73 page view became "SQL Injection 88%", because Firefox 70/73 were the attacker's browsers in SR-BH 2020.

Conclusion: the model leans on **dataset-specific header values**, not only on the URI and body. Before running it on real logs, train a log-robust variant: use only the fields access logs have (URI, method, protocol), or randomly blank headers during training. Then evaluate it.
