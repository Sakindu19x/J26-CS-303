# Dataset Exploration and Schema Verification Summary

- **Dataset File:** `data_capec_multilabel.csv`
- **Total Records:** 907,815
- **Total Attributes:** 38
- **Exact Duplicates:** 2,746
- **Incomplete Core Records:** 2
- **Clean Record Count (after cleaning):** 905,068 (the 2 incomplete rows are identical blank rows, so one is already removed as a duplicate: 907,815 − 2,746 − 1)

## Label Distribution (14 CAPEC Classes)

| CAPEC Label | Positive Samples | Percentage (%) |
| :--- | :--- | :--- |
| 000 - Normal | 525,195 | 57.8526% |
| 66 - SQL Injection | 250,311 | 27.5729% |
| 194 - Fake the Source of Data | 56,145 | 6.1846% |
| 126 - Path Traversal | 20,992 | 2.3124% |
| 34 - HTTP Response Splitting | 19,738 | 2.1742% |
| 242 - Code Injection | 15,827 | 1.7434% |
| 272 - Protocol Manipulation | 9,153 | 1.0082% |
| 88 - OS Command Injection | 7,482 | 0.8242% |
| 274 - HTTP Verb Tampering | 5,437 | 0.5989% |
| 310 - Scanning for Vulnerable Software | 2,718 | 0.2994% |
| 153 - Input Data Manipulation | 2,272 | 0.2503% |
| 16 - Dictionary-based Password Attack | 1,847 | 0.2035% |
| 33 - HTTP Request Smuggling | 1,059 | 0.1167% |
| 248 - Command Injection | 1 | 0.0001% |


## Missing Values in Top Attributes

| Attribute | Missing Count | Missing (%) | Data Type |
| :--- | :--- | :--- | :--- |
| request_do_not_track | 907,110 | 99.92% | float64 |
| request_origin | 906,206 | 99.82% | str |
| request_accept_language | 891,955 | 98.25% | str |
| request_body | 881,072 | 97.05% | str |
| request_content_type | 879,271 | 96.86% | str |
| request_referer | 616,421 | 67.90% | str |
| request_accept_encoding | 541,515 | 59.65% | str |
| request_accept | 526,032 | 57.94% | str |
| request_cookie | 462,553 | 50.95% | str |
| request_connection | 424,955 | 46.81% | str |
| request_user_agent | 3,834 | 0.42% | str |
| response_content_length | 3,292 | 0.36% | float64 |
| request_host | 34 | 0.00% | str |
| timestamp | 2 | 0.00% | str |
| request_http_method | 2 | 0.00% | str |
| dst_port | 2 | 0.00% | float64 |
| dst_ip | 2 | 0.00% | str |
| src_port | 2 | 0.00% | float64 |
| src_ip | 2 | 0.00% | str |
| request_http_protocol | 2 | 0.00% | str |
| response_http_protocol | 2 | 0.00% | str |
| request_http_request | 2 | 0.00% | str |
| response_http_status_code | 2 | 0.00% | float64 |
| response_http_status_message | 2 | 0.00% | str |

