# Phase 3: Web Attack Detection Model & Evaluation Summary

- **Algorithm:** One-vs-Rest Logistic Regression (`solver='liblinear'`, `max_iter=1000`)
- **Preprocessing:** TF-IDF (10,000 max features for URI and Body) + One-Hot Encoding for 12 categorical headers
- **Total Sparse Input Features:** 34,822
- **Training Samples:** 724,054
- **Testing Samples:** 181,014
- **Training Time:** 196.95 seconds

## 1. Overall Performance Metrics

| Metric | Value |
| :--- | :--- |
| Micro Precision | 0.9877 |
| Micro Recall | 0.9831 |
| Micro F1-Score | 0.9854 |
| Macro Precision | 0.98 |
| Macro Recall | 0.8893 |
| Macro F1-Score | 0.9227 |
| Hamming Loss | 0.0023 |

## 2. Per-Label Performance

| Attack Category | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| 000 - Normal | 0.9878 | 0.9938 | 0.9908 | 104,352 |
| 272 - Protocol Manipulation | 0.8534 | 0.5549 | 0.6725 | 1,804 |
| 242 - Code Injection | 0.9956 | 0.9760 | 0.9857 | 3,210 |
| 88 - OS Command Injection | 0.9755 | 0.6416 | 0.7741 | 1,554 |
| 126 - Path Traversal | 0.9852 | 0.9383 | 0.9612 | 4,265 |
| 66 - SQL Injection | 0.9901 | 0.9901 | 0.9901 | 50,109 |
| 16 - Dictionary-based Password Attack | 1.0000 | 1.0000 | 1.0000 | 382 |
| 310 - Scanning for Vulnerable Software | 0.9907 | 0.9981 | 0.9944 | 534 |
| 153 - Input Data Manipulation | 0.9934 | 1.0000 | 0.9967 | 453 |
| 274 - HTTP Verb Tampering | 1.0000 | 1.0000 | 1.0000 | 1,132 |
| 194 - Fake the Source of Data | 0.9868 | 0.9885 | 0.9876 | 11,173 |
| 34 - HTTP Response Splitting | 0.9919 | 0.9985 | 0.9952 | 3,915 |
| 33 - HTTP Request Smuggling | 0.9902 | 0.4810 | 0.6474 | 210 |

## 3. Minority Class Under-Detection Analysis

| Attack Category | Actual Positives | Predicted Positives | Difference |
| :--- | :--- | :--- | :--- |
| 000 - Normal | 104,352 | 104,988 | 636 |
| 66 - SQL Injection | 50,109 | 50,109 | 0 |
| 194 - Fake the Source of Data | 11,173 | 11,192 | 19 |
| 126 - Path Traversal | 4,265 | 4,062 | -203 |
| 34 - HTTP Response Splitting | 3,915 | 3,941 | 26 |
| 242 - Code Injection | 3,210 | 3,147 | -63 |
| 272 - Protocol Manipulation | 1,804 | 1,173 | -631 |
| 88 - OS Command Injection | 1,554 | 1,022 | -532 |
| 274 - HTTP Verb Tampering | 1,132 | 1,132 | 0 |
| 310 - Scanning for Vulnerable Software | 534 | 538 | 4 |
| 153 - Input Data Manipulation | 453 | 456 | 3 |
| 16 - Dictionary-based Password Attack | 382 | 382 | 0 |
| 33 - HTTP Request Smuggling | 210 | 102 | -108 |

