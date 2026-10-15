# C4 Architecture and Mathematical Specifications

Component 4 (C4) of the research project: **"CTI-Assisted Digital Forensic Investigation Tool for SMEs: Explainable Attack Timeline Reconstruction and Next-Stage Prediction Model"**.

---

## 1. System Architecture Overview

C4 provides a fully reproducible, deterministic forensic analysis pipeline and next-step attack prediction engine across 7 CAM-LDS attack simulation episodes:

```
[Raw CAM-LDS Archives (data/raw/*.zip)]
                 │
                 ▼
[Stage 1: Normalization & Telemetry] ──> data/processed_7ep/normalized_events.{csv,json}
                 │
                 ▼
[Stage 2: Timeline Reconstruction]   ──> data/processed_7ep/attack_timelines.{csv,json}
                 │                   ──> data/processed_7ep/attack_sequences.json
                 ▼
[Stage 3: Samples & Statistics]      ──> data/processed_7ep/next_technique_samples.json
                 │                   ──> data/processed_7ep/loeo_folds.json
                 ▼
[Stage 4: LOEO Evaluation & Models]  ──> artifacts/7ep/production_model/
                 │                   ──> reports/7ep/evaluation_7ep_results.json
                 ▼
[Stage 5: Hypothesis & Power Tests]  ──> reports/7ep/permutation_7ep_report.json
                 │                   ──> reports/7ep/holm_claim_rule_results.json
                 ▼
[Stage 6: Prediction Records]        ──> data/processed_7ep/prediction_records_loeo.jsonl
                 │
                 ▼
[Analyst Console / Dashboard]        ──> Streamlit + Altair Forensic Dashboard
```

---

## 2. Next-Stage Attack Technique Prediction Models

### Architectural Distinction: Markov vs. Frequency Baseline

| Dimension | First-Order Markov Model (`c4.models.markov.MarkovModel`) | Global Frequency Baseline (`c4.models.frequency.FrequencyBaseline`) |
|---|---|---|
| **Mathematical Concept** | **Conditional Transition Probability:** $P(T_{t+1} = b \mid T_t = a)$ | **Unconditioned Marginal Distribution:** $P(T_{t+1} = b)$ |
| **State Dependency** | **State-Dependent:** Conditioned on the attacker's currently observed technique set at time $t$. | **State-Agnostic:** Predicts the overall most common next techniques regardless of current state. |
| **Forensic Interpretation** | "Given that the attacker just executed Technique $A$, what technique do they historically transition to next?" | "Across all observed transitions in training, what techniques are historically targeted most frequently?" |
| **Failure Mode on Unseen State** | Returns status `"insufficient_evidence"` when current technique has 0 outgoing training transitions. | Always returns predictions (unless training set itself is completely empty). |

---

## 3. First-Order Markov Model Formulation

### Transition Counting with Multi-Technique Steps
In CAM-LDS, attack steps may carry multiple MITRE ATT&CK techniques simultaneously. To preserve the total statistical weight of exactly **1.0 per step transition**, weight is evenly distributed:

- Let $S = \{a_1, \dots, a_m\}$ be the source technique set (size $m$).
- Let $T = \{b_1, \dots, b_n\}$ be the target technique set (size $n$).
- For every pair $(a \in S, b \in T)$, the transition count is updated by:
  $$w = \frac{1}{m \times n}$$
- The sum of weights for the step transition satisfies:
  $$\sum_{a \in S} \sum_{b \in T} \frac{1}{m \times n} = m \cdot n \cdot \frac{1}{m \cdot n} = 1.0$$

### Conditional Transition Probabilities
For each source technique $a$ with outgoing transitions:
$$P(b \mid a) = \frac{\text{count}[a][b]}{\sum_k \text{count}[a][k]}$$

By construction:
$$\sum_b P(b \mid a) = 1.0 \quad (\pm 10^{-9})$$

### Multi-Technique Current Set Inference
When predicting from an observed current technique set $S$:
1. Identify observed members $M \subseteq S$ that have outgoing transitions in the training set:
   $$M = \{a \in S \mid \sum_k \text{count}[a][k] > 0\}$$
2. If $|M| = 0$, return status `"insufficient_evidence"` and **no probabilities**.
3. If $|M| > 0$, average the conditional distributions of all valid members with equal weight:
   $$P(b \mid S) = \frac{1}{|M|} \sum_{a \in M} P(b \mid a)$$
4. Rank candidate techniques by probability descending, using deterministic tie-breaking by technique ID ascending:
   $$\text{sort\_key} = (-\text{probability}, \text{technique\_id})$$

---

## 4. Global Frequency Baseline Formulation

The frequency baseline estimates the empirical marginal target distribution across all step transitions in training:

- For each step transition ending at target set $T = \{b_1, \dots, b_n\}$:
  $$\text{weight}(b) = \frac{1}{n} \quad \forall b \in T$$
- The normalized probability of each target technique is:
  $$P(b) = \frac{\sum \text{weight}(b)}{\sum_{k} \sum \text{weight}(k)}$$
- Predictions are ranked by $P(b)$ descending, with ties broken by technique ID ascending.
- The frequency baseline serves as a non-sequential benchmark to determine whether sequence transitions provide predictive signal over base-rate technique popularity.

---

## 5. Common Prediction Interface (`c4.models.predictor.predict_next`)

The common function `predict_next(sequence_items, model, method="markov"|"frequency", k=3)` enforces uniform invocation across models:

- **State Extraction:** Strictly consumes the last sequence item `sequence_items[-1]` as the current state.
- **Enrichment:** Maps predicted technique candidates to official ATT&CK tactics via the MITRE v16.1 reference table (labeled derived).
- **Status Codes:**
  - `"ok"`: Valid prediction generated.
  - `"insufficient_evidence"`: Current technique was never observed with outgoing transitions in training.
  - `"empty_input"`: Sequence items list is empty.
  - `"empty_training"`: Model training set contained 0 transitions.
- **Forensic Disclaimer:**
  > *"Probabilities are empirical estimates derived from observed training sequences and not guarantees."*
- **Explainability Policy:** As specified by forensic protocol, no synthetic feature importance (e.g., SHAP) is computed; all explanations are grounded in empirical supporting transition counts and specific episode/event evidence identifiers.
