# Phase 2: Data Cleaning and Dataset Split Summary

## 1. Cleaning Results

- **Initial Records:** 907,815
- **Exact Duplicates Removed:** 2,746
- **Incomplete Core Records Removed:** 1
- **Clean Record Count:** 905,068

## 2. Partition Dimensions

- **Training Set (80%):** 724,054 requests (`X_train`: (724054, 14), `y_train`: (724054, 13))
- **Testing Set (20%):** 181,014 requests (`X_test`: (181014, 14), `y_test`: (181014, 13))
- **Preserved Test Context:** 181,014 records with attributes: `timestamp, src_ip, src_port, dst_ip, dst_port`

## 3. Label Distribution in Splits

| Attack Label | Clean Total | Train Positives | Test Positives | Test Ratio (%) |
| :--- | :--- | :--- | :--- | :--- |
| 000 - Normal | 522,734 | 418,382 | 104,352 | 19.96% |
| 66 - SQL Injection | 250,230 | 200,121 | 50,109 | 20.03% |
| 194 - Fake the Source of Data | 56,120 | 44,947 | 11,173 | 19.91% |
| 126 - Path Traversal | 20,950 | 16,685 | 4,265 | 20.36% |
| 34 - HTTP Response Splitting | 19,738 | 15,823 | 3,915 | 19.83% |
| 242 - Code Injection | 15,827 | 12,617 | 3,210 | 20.28% |
| 272 - Protocol Manipulation | 9,011 | 7,207 | 1,804 | 20.02% |
| 88 - OS Command Injection | 7,482 | 5,928 | 1,554 | 20.77% |
| 274 - HTTP Verb Tampering | 5,437 | 4,305 | 1,132 | 20.82% |
| 310 - Scanning for Vulnerable Software | 2,718 | 2,184 | 534 | 19.65% |
| 153 - Input Data Manipulation | 2,272 | 1,819 | 453 | 19.94% |
| 16 - Dictionary-based Password Attack | 1,847 | 1,465 | 382 | 20.68% |
| 33 - HTTP Request Smuggling | 1,059 | 849 | 210 | 19.83% |

