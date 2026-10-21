# PP1 Progress Presentation Guide & Defense Notes
**Component 1: Adaptive Web Attack Detection & Correlation Model**  
**Student:** Weerasinghe W.G.O.N (IT23378148)  
**Research Group:** J26-CS-303  
**Supervisor:** Mr. Amila Senarathna  
**Presentation Date:** 22 October 2026  

---

## 1. Project Identity & Problem Statement
- **Title:** Adaptive Web Attack Detection & Correlation Model (Component 1 of *CTI-Assisted Digital Forensic Investigation Tool for SMEs*).
- **Core Problem:** Small and Medium-sized Enterprises (SMEs) lack dedicated Security Operations Centers (SOCs). When cyberattacks occur, monitoring systems generate hundreds of fragmented, independent alerts. Analysts suffer from alert fatigue and cannot discern whether separate alerts are part of an organized multi-stage attack.
- **Two-Stage Solution:**
  1. **Stage 1 (PP1 Milestone):** Multi-label detection model capable of classifying multiple simultaneous attack types per HTTP request.
  2. **Stage 2 (PP2 Milestone):** Adaptive contextual correlation using Conditional Rough Entropy and Knowledge Granularity to link related detections across time, source, target, and behavior.

---

## 2. Approved Methodology for PP1 (Detection Stage)

```
Raw HTTP Request Data (data_capec_multilabel.csv: 907,815 rows, 38 columns)
   ↓
Data Cleaning & Deduplication (2,746 duplicates + 1 invalid row removed → 905,068 clean records)
   ↓
Feature Taxonomy & Separation:
   - 14 Request-side Detection Features (X)
   - 13 Supervised CAPEC Target Labels (y) [CAPEC 248 excluded due to N=1]
   - 5 Contextual Correlation Fields preserved for PP2 (timestamp, src_ip, src_port, dst_ip, dst_port)
   ↓
Reproducible Partitioning (80:20 Split, random_state=42):
   - Training Set: 724,054 records
   - Testing Set: 181,014 records
   ↓
Feature Transformation (ColumnTransformer):
   - TF-IDF Vectorization (max_features=10,000) for URI and Body text
   - One-Hot Encoding for 12 categorical HTTP headers/method
   - *Strictly fit only on X_train to prevent data leakage*
   ↓
Multi-Label Classification:
   - One-vs-Rest (OvR) Logistic Regression (solver='liblinear', max_iter=1000)
   ↓
Predictions & Probabilities Generated on Held-Out Test Set (181,014 samples)
   ↓
PP1 Deliverable: correlation_input.csv (31 columns combining context + predictions + probabilities)
```

---

## 3. Experimental Results Summary

### Overall Detection Performance

| Metric | Measured Value | Academic Interpretation |
| :--- | :--- | :--- |
| **Micro Precision** | **0.9877** | Global accuracy of positive predictions across all classes. |
| **Micro Recall** | **0.9831** | Global proportion of actual attack instances successfully flagged. |
| **Micro F1-Score** | **0.9854** | Harmonic mean of global precision and recall. |
| **Macro Precision** | **0.9800** | Unweighted average precision across all 13 attack classes. |
| **Macro Recall** | **0.8893** | Unweighted average recall; reflects difficulty in minority attack classes. |
| **Macro F1-Score** | **0.9227** | Balanced metric accounting equally for frequent and rare classes. |
| **Hamming Loss** | **0.0023** | Only **0.23%** of individual binary label decisions were incorrect. |

---

## 4. Per-Class Performance Breakdown

| Attack Category | Precision | Recall | F1-Score | Test Support |
| :--- | :--- | :--- | :--- | :--- |
| **000 - Normal** | 0.9878 | 0.9938 | 0.9908 | 104,352 |
| **16 - Dictionary-based Password Attack** | **1.0000** | **1.0000** | **1.0000** | 382 |
| **274 - HTTP Verb Tampering** | **1.0000** | **1.0000** | **1.0000** | 1,132 |
| **153 - Input Data Manipulation** | 0.9934 | **1.0000** | 0.9967 | 453 |
| **34 - HTTP Response Splitting** | 0.9919 | 0.9985 | 0.9952 | 3,915 |
| **310 - Scanning for Vulnerable Software** | 0.9907 | 0.9981 | 0.9944 | 534 |
| **66 - SQL Injection** | 0.9901 | 0.9901 | 0.9901 | 50,109 |
| **194 - Fake the Source of Data** | 0.9868 | 0.9885 | 0.9876 | 11,173 |
| **242 - Code Injection** | 0.9956 | 0.9760 | 0.9857 | 3,210 |
| **126 - Path Traversal** | 0.9852 | 0.9383 | 0.9612 | 4,265 |
| **88 - OS Command Injection** | 0.9755 | **0.6416** | 0.7741 | 1,554 |
| **272 - Protocol Manipulation** | 0.8534 | **0.5549** | 0.6725 | 1,804 |
| **33 - HTTP Request Smuggling** | 0.9902 | **0.4810** | 0.6474 | 210 |

---

## 5. Critical Research Discussion: Minority Class Under-Detection
- **Observation:** Notice that for `Protocol Manipulation`, `OS Command Injection`, and `HTTP Request Smuggling`, the precision is high (85%–99%), but the recall drops to 48%–64%.
- **Academic Cause:** Severe class imbalance. The dataset is heavily dominated by Normal traffic (58%) and SQL Injection (28%). When using a standard fixed decision threshold of $0.50$, the classifier requires very strong evidence to trigger a positive label on rare categories.
- **Academic Defense / Future Work:** This finding directly justifies future experiments in threshold tuning on a validation partition, or class-weighted loss functions, providing a clear narrative for ongoing research.

---

## 6. The PP1 Handover Artifact: `correlation_input.csv`
- Demonstrates that PP1 has fulfilled its obligation to the broader research architecture.
- Dimensions: **181,014 records x 31 columns**:
  - **5 Contextual Attributes:** `timestamp`, `src_ip`, `src_port`, `dst_ip`, `dst_port`
  - **13 Predicted Attack Labels:** Binary decisions
  - **13 Detection Probabilities:** Continuous confidence scores ($0.0$ to $1.0$)
- In PP2, these 31 columns will be fed into the contextual similarity equations (temporal, source, target, behavioural, confidence) and weighted by **Conditional Rough Entropy** and **Knowledge Granularity**.

---

## 7. Anticipated Examiner Q&A

**Q1: Why did you use One-vs-Rest (OvR) Logistic Regression instead of Random Forest, XGBoost, or Neural Networks?**  
*Answer:*  
1. Web attack detection on HTTP requests produces extremely high-dimensional, sparse feature matrices after TF-IDF vectorization (over 34,800 features). Logistic Regression scales efficiently on sparse matrices.
2. OvR is mathematically required because web requests frequently carry multiple simultaneous attack labels (e.g., Code Injection + Path Traversal). Multi-class softmax assumes mutually exclusive classes, which violates the dataset reality.
3. Logistic Regression outputs calibrated probability estimates ($0.0$ to $1.0$) via the sigmoid function, which are directly required as confidence features for the PP2 adaptive correlation model.

**Q2: Why did you exclude CAPEC 248 (Command Injection) from supervised training?**  
*Answer:* In the entire 907,815-row dataset, `248 - Command Injection` has only $N=1$ positive sample. If placed in the training set, it cannot be tested; if placed in the test set, the model cannot learn it. Statistically, it is impossible to evaluate a supervised classifier on single-sample support. It was preserved in the raw dataset for documentation integrity, but excluded from supervised learning.

**Q3: How did you ensure there was no data leakage?**  
*Answer:*  
1. We removed duplicate rows before splitting to prevent identical requests from appearing in both training and test sets.
2. We strictly separated the 80:20 split *before* fitting the `ColumnTransformer`. The vocabulary and one-hot categories were learned exclusively from `X_train`.
3. Server-side response attributes (status codes, response lengths) and contextual attributes (IPs, timestamps) were strictly excluded from model input features ($X$).

**Q4: Why is Hamming Loss reported in addition to F1-Score?**  
*Answer:* In multi-label classification, standard accuracy is overly punitive because it considers a prediction wrong if even 1 of 13 labels is mispredicted. Hamming Loss measures the fraction of wrong individual label assignments across all labels and samples. A Hamming Loss of **0.0023** demonstrates that 99.77% of individual label decisions made by the model were correct.
