# PP2 Design: Adaptive Contextual Correlation
**Component 1: Adaptive Web Attack Detection & Correlation Model**
**Student:** Weerasinghe W.G.O.N (IT23378148) · **Group:** J26-CS-303 · **Supervisor:** Mr. Amila Senarathna
**Status:** Draft design for review before implementation (Prototypes 3–5)

---

## 1. Summary

The correlation design in the proposal (Section 3.4) is sound **in structure**: per-criterion similarity → data-derived weights (Conditional Rough Entropy + Knowledge Granularity, Sun, Gu & Chen [4]) → weighted score → threshold → groups, compared against an equal-weight baseline. This follows the same pattern as the attribute-similarity alert fusion of Liang et al. [6] and the alert aggregation of Sun et al. [4].

However, profiling the SR-BH 2020 context fields showed that **three of the five context fields carry no information**, so two of the four criteria must be redefined using other request fields. Four further method-level points need deciding before implementation (Section 4).

---

## 2. What the data actually contains (profiling results)

| Field | Unique values in the whole dataset | Usable for correlation? |
|---|---|---|
| `src_ip` | **1** (`172.26.0.1`, a Docker gateway) | ❌ Every request has the same source IP |
| `dst_ip` | **1** (`172.26.0.4`) | ❌ Single web server |
| `dst_port` | **1** (`80`) | ❌ |
| `src_port` | 16,389 | ❌ Ephemeral ports, randomly reused across days; only 21 of 16,190 reused ports repeat within 60 s, so a port does not identify a session |
| `timestamp` | 1-second resolution, 17 Jul – 1 Nov 2020 | ✅ All attacks occur 17–19 Jul 2020 |
| `request_http_request` (URI path) | 5,819 distinct paths among attack requests | ✅ Real target resource |
| `request_cookie` | 4,441 distinct values among attacks, incl. WordPress session cookies (e.g. `wordpress_logged_in_…=<user>%7C<expiry>…`) | ✅ Partial session identity |
| `request_user_agent` | 256 distinct values among attacks (Firefox 70/73, Nmap NSE, Googlebot, tampered variants) | ✅ Client/tool identity |
| Predicted labels + probabilities (from Stage 1) | 13 + 13 columns | ✅ Attack behaviour |

**Attack traffic arrives in campaigns.** Sorted by time, the test set breaks into 22,228 runs of a single attack type, some over 1,000 requests long (e.g. 1,007 SQL Injection requests in 34 minutes on 18 Jul). In 75% of hours only one attack type is present. This means **temporal + behavioural + target context genuinely separates attack activity**, which is what the correlation stage needs.

---

## 3. Stage 1 → Stage 2 hand-off

### 3.1 What a "detected event" is
One HTTP request for which the detector predicts **at least one attack label** (probability ≥ 0.5 on any label other than `000 - Normal`). Normal-only requests are not correlated.

### 3.2 Input record per event
| Group | Fields | Source |
|---|---|---|
| Event ID | original row index | dataset |
| Temporal | `timestamp` (parsed to UTC) | context fields |
| Source / identity | `request_cookie` session token, `request_user_agent` | request headers |
| Target | URI **path** (before `?` and before the first encoded payload character); `request_http_method` is carried through to the output but not scored | request |
| Attack / behaviour | 13 predicted labels, 13 probabilities | Stage 1 output |

`src_ip`, `dst_ip`, `src_port`, `dst_port` are still carried through to the output for completeness and for the integrated system (real deployments will have many IPs), but they are **not** used as criteria on this dataset.

### 3.3 Which requests to correlate (decision needed)
The current hand-off file `results/correlation_input.csv` holds predictions for the **20% test set only** (181,014 requests, ~76,000 detected attacks). Because the split is random, the timeline has every ~5th request, which thins out attack sequences.

| Option | How | Pros | Cons |
|---|---|---|---|
| **A. Out-of-fold predictions (recommended)** | 5-fold `cross_val_predict` over all 905,068 requests; each request is predicted by a model that never trained on it | Complete, honest timeline (~380,000 attack events); no leakage | ~15–20 min extra compute; new hand-off file |
| B. Test set only | Use the existing `correlation_input.csv` | Already exists | Gappy timeline; weaker sessions |

### 3.4 Scale
Comparing every pair is infeasible (76,000 events ≈ 2.9 billion pairs). Events are processed **in time order** and compared only with groups that were active within a time window *W*. This keeps the method identical in meaning to the proposal (pairwise score vs threshold) while staying linear in practice.

---

## 4. Review of the proposal's correlation logic

| # | Proposal says | Verdict | Change |
|---|---|---|---|
| 1 | Weighted sum of per-criterion similarities, threshold θ, group related events | ✅ Correct, keep | — |
| 2 | Equal-weight baseline with identical criteria, similarities and threshold procedure | ✅ Correct, keep | — |
| 3 | Threshold chosen experimentally | ✅ Keep | Report a sweep θ ∈ [0.3, 0.9] |
| 4 | **Source/identity** = shared source IP or session | ⚠️ IP unusable here | Use session cookie + user-agent (the proposal already allows "or session when we can find one") |
| 5 | **Target** = "web resources or URIs that were targeted" | ✅ Wording is right; ⚠️ previous code used `dst_ip`/`dst_port`, which are constant | Use URI path |
| 6 | **Weights from Conditional Rough Entropy + Knowledge Granularity** | ⚠️ Risk of circularity | See 4.1 |
| 7 | Probabilities used "only if shown helpful" | ✅ Keep | Run with and without probability cosine (ablation) |
| 8 | "Final criterion for assessing group quality to be set based on dataset evidence" | ⚠️ Still open | See 4.2 |

### 4.1 The weighting must not be circular
Rough-set significance measures how much a condition attribute reduces uncertainty about a **decision attribute D**. If D is the attack type **and** one criterion is attack-type similarity, that criterion explains D perfectly (conditional entropy = 0) and automatically gets almost all the weight. That is what happened in the earlier PP2 attempt (attack/behaviour = 59.8%), and an examiner can show that the weight is predetermined rather than learned.

Two defensible options (to be checked against the exact formulation in Sun, Gu & Chen [4] before coding):
- **Option 1 (unsupervised, preferred):** no decision attribute. The significance of criterion *a* is how much the knowledge granularity/rough entropy of the partition changes when *a* is removed from the full criterion set. This uses no labels, so it is also realistic for deployment.
- **Option 2 (supervised, independent D):** D = a reference session/campaign ID (Section 4.2) that is **not** one of the criteria.

Rough sets need discrete values, so the criteria are discretised before weighting: time → buckets (5-minute in the implementation), target → URI path, identity → session token / user-agent, behaviour → predicted label set.

### 4.2 How group quality will be evaluated
Alert reduction rate alone cannot show that groups are *right*. A grouping that puts everything in one group has a 99.99% reduction rate. The dataset has no scenario labels, so evaluation uses:

| Metric | Measures | Ground truth used |
|---|---|---|
| Alert reduction rate (ARR), number of groups | Workload reduction for an SME analyst | none |
| **Label purity / homogeneity** per group | Do grouped events share the same *true* CAPEC label? | true labels (correlation itself only uses *predicted* labels) |
| **Adjusted Rand Index / V-measure vs reference sessions** | Agreement with independent reference campaigns | reference sessions = maximal runs of the same true attack type with gaps < *g* in time order (tool runs) |
| Threshold sweep | Trade-off between over- and under-grouping | — |

Limitation to state openly: the reference sessions are a **proxy**, built from time and true labels. They are evidence of quality, not perfect ground truth.

### 4.3 Claims to avoid
The earlier PP2 attempt reported "threat-actor source continuity", "multi-stage attack chains" and "+76.6% detection fidelity". On this dataset every request has the same IP and there is no ground truth for chains, so these claims cannot be supported and should not be repeated.

---

## 5. Correlation criteria and similarity functions

For two events *A* and *B*:

| Criterion | Similarity S_i(A, B) ∈ [0, 1] |
|---|---|
| **Temporal** | `max(0, 1 − |t_A − t_B| / W)`, window *W* tuned (e.g. 60–600 s) |
| **Source / identity** | 1.0 if the same session cookie token; else 0.5 if the same user-agent; else 0 |
| **Target** | 1.0 if the same URI path; else the share of common leading path segments (e.g. `/blog/index.php/2020` vs `/blog/index.php/my-account` = 2/3) |
| **Attack / behaviour** | Jaccard overlap of predicted label sets; optional variant adds cosine of the probability vectors (ablation, Section 4 #7) |

Correlation score: `Corr(A, B) = Σ w_i · S_i(A, B)`, with `Σ w_i = 1`.
- Adaptive model: `w_i` from rough entropy + knowledge granularity (Section 4.1).
- Baseline: `w_i = 0.25` for all four.

The sub-weights inside a criterion (the 1.0 / 0.5 for identity) are fixed design choices. They should be stated as such and varied in a small sensitivity check, so that the "no manual weights" claim is not overstated.

---

## 6. Correlation flow

```
Stage 1 output (detected events + context)
   ↓
1. Filter: keep events with ≥1 predicted attack label
2. Extract criteria: timestamp (UTC), session token, user-agent, URI path, method, label set, probabilities
3. Discretise criteria → compute adaptive weights (rough entropy + KG)        [Prototype 4]
4. Sort events by time
5. For each event:                                                             [Prototype 3 + 5]
     compare with every group active within the last W seconds
     score = Σ w_i · S_i(event, group representative)
     if best score ≥ θ → add to that group, update its representative
     else            → start a new group
6. Repeat steps 4–5 with equal weights (baseline)
7. Evaluate: ARR, purity, ARI / V-measure vs reference sessions, θ sweep, weight ablation
```

---

## 7. Output (hand-off to the integrated system)

**`correlated_events.csv`** (one row per detected event)
`event_id, timestamp, src_ip, dst_ip, uri_path, method, session_token, user_agent, predicted_labels, max_probability, group_id, correlation_score`

**`correlation_groups.csv`** (one row per group / scenario)
`group_id, start_time, end_time, duration_s, event_count, attack_labels (counts), main_target_paths, identities, mean_correlation_score`

**`adaptive_weights.json`**: per-criterion weight, rough entropy and knowledge granularity values.

This matches the proposal's output list (Section 3.8.1): labels, confidence, retained context, correlation score, group/scenario ID, member events.

---

## 8. PP2 requirements

### 8.1 Functional requirements (refines FR3–FR7 of the proposal)
| ID | Requirement |
|---|---|
| FR3.1 | The component shall select as correlation input every request with at least one predicted attack label, together with its probabilities. |
| FR3.2 | The component shall extract temporal (timestamp), identity (session cookie, user-agent), target (URI path, method) and behaviour (predicted labels, probabilities) context for each detected event. |
| FR4.1 | The component shall compute a similarity in [0, 1] for each of the four criteria between an event and a candidate group. |
| FR5.1 | The component shall discretise the criteria and derive a weight for each from Conditional Rough Entropy and Knowledge Granularity, without using the criterion being weighted as the decision attribute. |
| FR5.2 | The component shall save the derived weights and the entropy/granularity values that produced them. |
| FR6.1 | The component shall compute a weighted correlation score and assign each event to the best-matching active group if the score ≥ θ, otherwise create a new group. |
| FR6.2 | The component shall only compare events with groups active within a configurable time window *W*. |
| FR6.3 | The component shall run the same procedure with equal weights (baseline). |
| FR7.1 | The component shall output an event-level file and a group-level file as defined in Section 7. |
| FR8.1 | The component shall report ARR, number of groups, label purity and agreement with reference sessions for both adaptive and baseline runs, across a θ sweep. |

### 8.2 Non-functional requirements
| Category | Requirement |
|---|---|
| Performance | Correlate ≥ 76,000 events on the development laptop in under 5 minutes. |
| Reproducibility | Fixed random seeds; all parameters (W, θ, discretisation) in one config file; results regenerated by one command. |
| Explainability | Every grouped event records its score and per-criterion similarities, so an analyst can see why it was grouped. |
| Portability | Criteria read from named columns, so real deployments can switch identity back to source IP when many IPs exist. |
| Integrity | Correlation never modifies Stage 1 outputs; it only reads them. |

---

## 9. Implementation plan

| Prototype | Work | Done when |
|---|---|---|
| 3a | (Option A) Out-of-fold predictions over the full dataset → new hand-off file | File with all requests, predictions, probabilities, context |
| 3b | Context extraction + four similarity functions + unit tests | Tests pass on hand-made event pairs |
| 4 | Discretisation + rough entropy / knowledge granularity weights (non-circular) | Weights + intermediate values saved; method checked against [4] |
| 5a | Time-windowed grouping, adaptive and baseline | Both runs produce event and group files |
| 5b | Evaluation: ARR, purity, ARI/V-measure, θ and W sweeps, probability ablation | Results tables + figures |

## 10. Decisions needed (with supervisor)
1. Option A (out-of-fold, full timeline) or Option B (test set only)?
2. Weighting formulation: unsupervised (Option 1) or with an independent decision attribute (Option 2)? Confirm against [4].
3. Accept the reference-session proxy for evaluation, and the gap *g* used to build it.
