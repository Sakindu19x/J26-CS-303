# PP1 Changes & Refinements from Proposal
**Component 1: Adaptive Web Attack Detection & Correlation Model**  
**Student:** Weerasinghe W.G.O.N (IT23378148)  
**Research Group:** J26-CS-303  
**Supervisor:** Mr. Amila Senarathna  
**Milestone:** Progress Presentation 1 (PP1) — 22 October 2026  

---

## 1. Executive Summary

During the transition from the conceptual **Research Proposal** to the empirical **PP1 Implementation**, six critical refinements were made to the dataset handling, feature taxonomy, target definitions, and model evaluation pipeline. 

These changes do not represent deviations from the core research scope; rather, they represent **rigorous scientific adjustments** necessary to prevent data leakage, adhere to sound statistical machine learning principles, and establish a formal mathematical bridge between **Stage 1 (Detection)** and **Stage 2 (Adaptive Correlation)**.

---

## 2. Comprehensive Comparison: Proposal vs. PP1 Actual

| Area | Planned in Proposal | Implemented in PP1 | Academic Rationale & Justification |
| :--- | :--- | :--- | :--- |
| **Target Labels** | All 14 CAPEC attack categories present in SR-BH 2020. | **13 Supervised Labels** (`248 - Command Injection` excluded). | `CAPEC 248` contains only $N=1$ instance in 907,815 rows. In supervised learning, a single sample cannot be divided across train and test sets, and no classifier can learn a generalizable decision boundary from one example. Preserved in documentation, excluded from supervised training. |
| **Dataset Size & Hygiene** | 907,815 raw records ingested directly. | **905,068 clean records** (2,746 duplicate rows + 1 malformed record removed). | Duplicate HTTP requests appearing in both training and test sets introduce synthetic data leakage, artificially inflating accuracy. Removing duplicates ensures true out-of-sample evaluation on unseen requests. |
| **Contextual Attributes** | Contextual fields noted for correlation. | **Strict Stage Decoupling & Exclusion from Detector ($X$).** | 5 Context fields (`timestamp`, `src_ip`, `dst_ip`, `src_port`, `dst_port`) were isolated and strictly excluded from the detection model to prevent the classifier from memorizing network IP topologies or timestamps. They were saved in `context_test.csv` for PP2. |
| **Response-Side Features** | Undefined inclusion of server response headers. | **Strictly Excluded from Detection Pipeline.** | Server response attributes (`response_http_status_code`, `response_content_length`, etc.) occur *after* request processing. Feeding response codes (e.g. 404, 500) into an attack detector causes post-incident data leakage. |
| **Feature Transformation** | General TF-IDF and One-Hot Encoding. | **Leakage-Free `ColumnTransformer` fitted strictly on $X_{train}$.** | The TF-IDF vocabulary (10,000 max features each for URI and Body) and One-Hot categories (12 headers) were fitted *exclusively* on the 80% training split (724,054 records) and then transformed onto the 20% test split (181,014 records). |
| **Class Imbalance & Model Baseline** | Standard One-vs-Rest Logistic Regression. | **Unweighted OvR baseline kept; minority-class under-detection measured and documented.** | Real data only (no synthetic oversampling, same as the dataset authors). Macro and per-label metrics reported so rare classes stay visible. Per-label threshold tuning on a validation split (and possibly class weighting) is the planned improvement. |
| **Inter-Stage Handover** | Conceptual hand-off between detection and correlation. | **Formal Handover Artifact: `results/correlation_input.csv`.** | Produced an explicit 181,014 row $\times$ 31 column dataset combining 5 context attributes, 13 binary predictions, and 13 continuous probability scores, defining a clean architectural contract for PP2. |

---

## 3. Deep-Dive: Justification for Key Changes

### Change 1: Exclusion of CAPEC 248 (Command Injection)
- **The Finding:** During dataset profiling, `248 - Command Injection` was found to have a total support of only **1 positive record** out of 907,815 entries ($0.00011\%$).
- **The Problem:** If placed in `X_train`, the test set has 0 positive samples, making recall and precision mathematically undefined ($0/0$). If placed in `X_test`, the classifier has 0 training examples, guaranteeing a false negative.
- **The Academic Solution:** The label was documented and removed from the active multi-label target matrix $Y$, reducing the target space from 14 to 13 classes. This demonstrates sound data engineering rather than blind execution.

### Change 2: Removal of 2,746 Exact Duplicates
- **The Finding:** 2,746 rows had identical HTTP request payloads, headers, timestamps, and network tuples.
- **The Problem:** In an 80/20 random split, identical rows would appear in both training and test partitions. The model would achieve high accuracy merely by memorizing requests it had already seen.
- **The Academic Solution:** Deduplication was executed *before* splitting, leaving 905,068 unique records. This adheres strictly to the **Standards & Best Practices** rubric criterion (20% of LO3).

### Change 3: Strict Feature Separation to Prevent Data Leakage
- **Request Detection Features ($X$, 14 columns):**
  - Text fields: `request_http_request` (URI), `request_body`.
  - Categorical headers: `request_http_method`, `request_http_protocol`, `request_host`, `request_user_agent`, `request_referer`, `request_origin`, `request_cookie`, `request_content_type`, `request_accept`, `request_accept_language`, `request_accept_encoding`, `request_connection`.
- **Contextual Correlation Attributes (5 columns):**
  - `timestamp`, `src_ip`, `dst_ip`, `src_port`, `dst_port`.
  - *Why separated?* A web attack detector must recognize malicious payloads based on attack patterns (e.g., SQL syntax or path traversal strings), not because an IP address was frequently flagged during training. IP-based correlation is strictly the domain of **Stage 2 (PP2)**.
- **Response Features (Excluded):**
  - `response_http_status_code`, `response_content_length`, `response_http_status_message`, `response_http_protocol`.
  - *Why separated?* In real-time intrusion detection, incoming requests must be evaluated upon arrival, before server execution. Using server responses introduces post-execution leakage.
- **Sparse Feature (Excluded):**
  - `request_do_not_track`: dropped due to near 100% missing values.

### Change 4: Class Imbalance Handled Transparently
- **Baseline:** unweighted One-vs-Rest Logistic Regression at the default 0.5 threshold. Micro F1 = **0.9854**, Macro F1 = **0.9227**, Hamming Loss = **0.0023**.
- **No synthetic data:** like the dataset authors, only real requests were used (no SMOTE), and imbalance-aware metrics (macro, per-label, Hamming loss) are reported.
- **Finding:** the three rarest classes have high precision but low recall (`Protocol Manipulation`: 55.49%, `OS Command Injection`: 64.16%, `HTTP Request Smuggling`: 48.10%).
- **Planned next step (not yet run):** per-label threshold tuning on a validation split taken from the training data. Class weighting is a second option to test and compare.

---

## 4. Ready-to-Use Slide Blueprint: "Modifications from Proposal"

```markdown
Slide Title: Refinements & Modifications from Proposal Stage

1. Target Space Refinement (14 → 13 Supervised Labels):
   - Excluded CAPEC 248 (Command Injection) due to single-sample support (N=1).
   - Prevents undefined division-by-zero metrics and ungeneralizable model fitting.

2. Rigorous Data Leakage Controls:
   - Deduplication: Removed 2,746 duplicate records prior to train/test partitioning.
   - Preprocessing Isolation: TF-IDF & One-Hot transformers fitted strictly on X_train.
   - Feature Taxonomy: Server-side responses excluded; IP/temporal attributes reserved strictly for PP2.

3. Transparent Baseline Evaluation:
   - Unweighted One-vs-Rest Logistic Regression (Micro F1: 98.54%, Macro F1: 92.27%, Hamming Loss: 0.23%).
   - Macro and per-label metrics reported so rare classes stay visible.
   - Rare-class recall (48-64%) identified; per-label threshold tuning planned.

4. Concrete Handover Contract for PP2:
   - Formulated correlation_input.csv (181,014 records × 31 attributes).
   - Fully bridges Stage 1 (Detection) and Stage 2 (Adaptive Correlation).
```

---

## 5. Examiner Q&A Script for Defending PP1 Changes

**Examiner: "Why did your number of attack classes change from 14 in the proposal to 13 in PP1?"**  
> *"In the proposal, we identified 14 CAPEC labels in the SR-BH 2020 dataset. However, during data exploration in Phase 1, we discovered that CAPEC 248 (Command Injection) had exactly 1 positive instance across all 907,815 rows. In machine learning, a single sample cannot be split into both training and testing sets. Training on $N=1$ would lead to severe overfitting, and testing on it would produce statistically invalid metrics. We therefore preserved CAPEC 248 in the raw data records for documentation integrity, but restricted supervised modeling to the 13 statistically viable attack classes."*

**Examiner: "Why did you exclude IP addresses and timestamps from your machine learning features?"**  
> *"Including IP addresses and timestamps in the detection model feature set $X$ would cause severe data leakage and overfitting. The model would learn that specific attacker IPs or specific dates are malicious, rather than learning the generic syntax of the attack payload. Furthermore, our proposed two-stage architecture explicitly dedicates temporal and network identity analysis to Stage 2 (Adaptive Correlation in PP2). Separating detection features from contextual features ensures both stages operate with scientific validity."*

**Examiner: "Did you consider class balancing for the rare attack categories?"**  
> *"For PP1 I kept an unweighted baseline and measured the effect of imbalance openly: the rare classes have high precision but 48-64% recall. Like the dataset authors, I didn't add synthetic data. The next step is per-label threshold tuning on a validation split from the training data. Class weighting is a second option I'll compare, checking that it doesn't increase false alarms on normal traffic, which matters for SMEs."*
