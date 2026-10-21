# 03. Empirical Evaluation Scores & Performance Verification

> [!NOTE]
> All figures below are extracted directly from `reports/7ep/evaluation_7ep_results.json` without recomputation.

---

## 1. Primary Slice: Technique Level (collapsed_full, N=95)

| Metric | Markov Model | Frequency Baseline | Relative Difference / Comparison |
|:---|:---:|:---:|:---:|
| **Top-1 Accuracy** | **3.16%** [1.08%, 8.88%] | **7.37%** [3.61%, 14.44%] | Baseline ahead by +4.21% |
| **Top-3 Accuracy (Hit@3)** | **3.16%** [1.08%, 8.88%] | **16.84%** [10.64%, 25.62%] | Baseline ahead by +13.68% (p = 0.0034) |
| **Precision (Macro / Weighted)** | Macro: 0.0242 / Weighted: 0.0316 | Macro: 0.0485 / Weighted: 0.0737 | Documented in `precision_recall_f1` table |
| **Recall (Macro / Weighted)** | Macro: 0.0242 / Weighted: 0.0316 | Macro: 0.0485 / Weighted: 0.0737 | Documented in `precision_recall_f1` table |
| **F1-Score (Macro / Weighted)** | Macro: 0.0242 / Weighted: 0.0316 | Macro: 0.0485 / Weighted: 0.0737 | Documented in `precision_recall_f1` table |
| **Confusion Matrix** | **Status: MISSING** | **Status: MISSING** | *Not produced by 7-episode LOEO evaluation pipeline (stopped item per specification)* |
| **Error Analysis** | **Status: MISSING** | **Status: MISSING** | *Not produced by 7-episode LOEO evaluation pipeline (stopped item per specification)* |

---

## 2. Secondary Slice: Tactic Level (tactic_collapsed, N=76)

| Metric | Markov Model | Frequency Baseline | Relative Difference / Comparison |
|:---|:---:|:---:|:---:|
| **Top-1 Accuracy** | **28.95%** [19.96%, 39.96%] | **18.42%** [11.30%, 28.58%] | Markov ahead by +10.53% |
| **Top-3 Accuracy (Hit@3)** | **63.16%** [51.93%, 73.12%] | **63.16%** [51.93%, 73.12%] | Baseline ahead by +0.00% |
| **Confusion Matrix** | **Status: MISSING** | **Status: MISSING** | *Not produced by 7-episode LOEO evaluation pipeline (stopped item per specification)* |
| **Error Analysis** | **Status: MISSING** | **Status: MISSING** | *Not produced by 7-episode LOEO evaluation pipeline (stopped item per specification)* |

---

## 3. Reachability Ceilings & Empirical Constraints

- **Empirical Reachability Ceiling**: **62.11%** (59/95 samples). 36 test targets never appeared in their respective training folds.
- **State Coverage Rate**: **64.21%** (61/95 samples). 34 samples evaluate unseen current states requiring fallback.
- **Perfect-Order Theoretical Cap**: **64.98%** (calibrated via real-scale A4 planted-structure simulation).
- **Core Scientific Conclusion**: The proposal's hypothetical 75% accuracy threshold is theoretically unreachable under LOEO on CAM-LDS.
