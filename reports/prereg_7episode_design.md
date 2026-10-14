# Pre-Registration: 7-Episode Evaluation Design

**Registration Date**: 2026-10-14  
**Scope**: Experimental protocol, evaluation slices, model variants, evaluation metrics, statistical comparisons, learning curves, and permutation null hypotheses for the extended 7-episode CAM-LDS benchmark.  
**Integrity Rule**: Committed prior to running any models or evaluations on episodes E5, E6, or E7.

---

## 1. Episodes and Archive Identification

The 7-episode evaluation dataset consists of episodes E1 through E7. Scenario folder names and archive MD5 hashes are drawn directly from `reports/raw_archive_hashes.json` and `reports/raw_archive_hashes_extended.json`:

| Episode ID | Scenario Folder Name | Archive File Name | Archive MD5 Checksum | Archive SHA-256 Checksum | Zenodo Published MD5 Match |
|:---|:---|:---|:---|:---|:---:|
| **E1** | `scenario_1_sudo_pam` | `scenario_1_sudo_pam.zip` | `e7e5bd19cda62a5bfb9a68525715cd78` | `0851d2cec590d3b56575fc385416190e12e258442023257d66879e19cb9e74fc` | TRUE |
| **E2** | `scenario_2_cron` | `scenario_2_cron.zip` | `c33aca73d6962414bd6c2c3f82b934c4` | `b2026121bdb035628b7536a042f01c3e92e36852b65cac9d69fd05c31ba98791` | TRUE |
| **E3** | `scenario_3_vnc_apt` | `scenario_3_vnc_apt.zip` | `bfd7e44cdb2d038a9deab800350e4b98` | `5c23b9d614689194f43cc844e4a25ed43568879ae83edc43df93336e0a33f911` | TRUE |
| **E4** | `scenario_4` | `scenario_4.zip` | `f1bf6ecd793c6c51f922ee43e33d7cf4` | `a79fefbfeebd25b163e57f9ec7b9581f8e6f0abed2f2775fba45cf55a004b637` | TRUE |
| **E5** | `scenario_5` | `scenario_5.zip` | `c56fce722a7b714eba004d6fd6319879` | `e54df7f4c2f8e12e374272544809cee42b2c7e68ac37d950934e4123364f7911` | TRUE |
| **E6** | `scenario_6_macro_binary` | `scenario_6_macro_binary.zip` | `aedd7c0b51700b16c04539f10784d5d4` | `73a31bf763c5a65ed1a14bb5919151dbbf324563d4f8eaabb0c58d9c0f67f3b1` | TRUE |
| **E7** | `scenario_7` | `scenario_7.zip` | `88122133a82079e07e7ed1b782bc203f` | `7f0ff0b5d939437b5ebad7f52eea69dc024775e5c73663c5b4ac7ba58f1b3a56` | TRUE |

### Selection of `scenario_6_macro_binary` as E6 Representative
Inspection of `reports/new_episodes_intake_audit.md` indicates that while `scenario_6_macro_binary.zip` was audited against decision rules D1–D6, the specific selection rule distinguishing `scenario_6_macro_binary` from any alternative (e.g., `scenario_6_macro_library`) is:
**rule not recorded**.

---

## 2. Folds and Partitioning

- **Cross-Validation Scheme**: 7-fold Leave-One-Episode-Out (LOEO).
- **Independence Guarantee**: A completely fresh model instance is trained for each fold from the remaining 6 training episodes. No model weights, state, or frequency statistics are shared across folds.
- **Scenario Alignment**: Each episode constitutes its own distinct scenario; evaluating LOEO directly measures cross-scenario generalization.

---

## 3. Evaluation Slices

The evaluation evaluates three slices:
1. **Primary Slice**: Technique level, `collapsed_full` (consecutive duplicate multi-label steps collapsed into single transitions, preserving complete technique identifier strings).
2. **Secondary Slice**: Tactic level, `tactic_collapsed` (consecutive duplicate tactic sets collapsed).
3. **Reference Slice**: Technique level, `raw_full` (uncollapsed consecutive steps, reported for completeness and benchmark transparency).

---

## 4. Models and Tuning Constraints

The models evaluated in this design are:
1. `MarkovModel`: First-order Markov chain predicting conditional transition probabilities $P(S_{t+1} \mid S_t)$.
2. `FrequencyBaseline`: Global unigram frequency baseline predicting unconditional marginal probabilities $P(S_{t+1})$.
3. `markov_fallback`: Markov model that falls back to marginal unigram frequency whenever the conditioning state $S_t$ was unseen in training (`unseen_history`).

### Model Constraints:
- All models are evaluated **exactly as implemented in `src/c4/models.py`** without hyperparameter tuning.
- **No Random Forest**: Tree-based ensembles or other feature-engineered discriminative models are explicitly excluded.
- **No ad-hoc model variants**: Any further variant (e.g., Laplace-smoothed Markov, second-order Markov, weighted interpolation/blends) requires a separate, pre-declared prompt with nested cross-validation to prevent data leakage and multiple-testing inflation.

---

## 5. Evaluation Metrics

For every model and fold, as well as pooled across all evaluated samples, the following metrics are computed:
- **Hit@1**: Proportion of test transitions where at least one ground-truth technique/tactic is in the top-1 prediction.
- **Hit@3**: Proportion of test transitions where at least one ground-truth technique/tactic is in the top-3 predictions.
- **Coverage**: Proportion of test samples where the model produces a valid prediction (status `'ok'`).
- **Ceiling**: Upper bound on achievable recall given the training vocabulary (proportion of test targets containing at least one item present in the training set).
- **Wilson 95% Confidence Intervals**: Exact binomial confidence intervals computed for Hit@1, Hit@3, Coverage, and Ceiling.
- **Micro and Macro Precision / Recall / F1**: Multi-label classification metrics across all classes, computed at both pooled and per-fold levels.

---

## 6. Primary Hypotheses and Statistical Comparisons

### Pre-Registered Primary Comparisons:
- **P1**: Tactic level (`tactic_collapsed`) — `MarkovModel` Hit@3 vs. `FrequencyBaseline` Hit@3.
- **P2**: Technique level (`collapsed_full`) — `MarkovModel` Hit@3 vs. `FrequencyBaseline` Hit@3.
- **P3**: Tactic level (`tactic_collapsed`) — `MarkovModel` Hit@3 vs. shuffled-order null distributions (S1 collapsed-order shuffle and S3 constrained shuffle).
- **P4**: Technique level (`collapsed_full`) — `MarkovModel` Hit@3 vs. shuffled-order null distributions (S1 collapsed-order shuffle and S3 constrained shuffle).

### Statistical Testing Protocol:
- **Paired Hypothesis Test**: Exact two-sided McNemar test computed on per-sample paired binary outcomes (hit vs. miss) between `MarkovModel` and `FrequencyBaseline`.
- **Descriptive Fold Consistency**: Exact count of folds (out of 7) where $\text{Hit@3}(\text{Markov}) \ge \text{Hit@3}(\text{Frequency})$.
- **Multiple Comparisons Correction**: Holm-Bonferroni step-down adjustment applied across the primary tests P1–P4.
- **Pre-Declared Substantive Claim Rule**:
  > An **"improvement over the baseline demonstrated"** conclusion will be claimed **if and only if**:
  > 1. Pooled Markov Hit@3 > Pooled Frequency Hit@3, **AND**
  > 2. The Holm-adjusted $p$-value is $< 0.05$ for at least one slice level (technique or tactic).
  > 
  > Otherwise, the formal conclusion must report: **"not demonstrated"**.

---

## 7. Learning Curve Protocol

To quantify model performance as a function of available training scenarios:
- For each held-out test episode $e \in \{E1, \dots, E7\}$:
  - From the remaining 6 episodes, for each subset size $k \in \{1, 2, 3, 4, 5, 6\}$:
    - Enumerate **ALL** $\binom{6}{k}$ possible training subsets:
      - $k=1: \binom{6}{1} = 6$ subsets
      - $k=2: \binom{6}{2} = 15$ subsets
      - $k=3: \binom{6}{3} = 20$ subsets
      - $k=4: \binom{6}{4} = 15$ subsets
      - $k=5: \binom{6}{5} = 6$ subsets
      - $k=6: \binom{6}{6} = 1$ subset
      - **Total subsets per fold**: $6 + 15 + 20 + 15 + 6 + 1 = 63$ training subsets (441 subset evaluations per model across all 7 folds).
    - **No sampling or subsampling**: Complete combinatorial enumeration is mandatory.
- **Aggregation**: Compute metric averages across subsets for each held-out episode, then average over all 7 held-out episodes.
- **Reported Models & Levels**: Report Hit@1, Hit@3, and Coverage for `MarkovModel`, `FrequencyBaseline`, and `markov_fallback` at both technique and tactic levels.

---

## 8. Handling of Episode E5 (Sensitivity Analysis)

Intake audit confirmed Episode E5 contains only 3 labeled steps (2 collapsed transitions), resulting in zero test coverage and zero ceiling under 7-fold LOEO.
- **Headline Analysis**: All 7 episodes (E1 through E7) included, retaining standard LOEO fidelity.
- **Sensitivity Analysis**: Complete secondary evaluation conducted with Episode E5 entirely removed (neither used for training nor evaluation), yielding a 6-fold LOEO design over {E1, E2, E3, E4, E6, E7}. Both sets of metrics must be reported side-by-side to assess sensitivity to the small sample size of E5.

---

## 9. Real-Scale Planted Structure Power Analysis (A4 Re-Run)

The synthetic planted-structure power analysis (A4) must be re-run calibrated directly to the empirical 7-episode collapsed sequence lengths and transition counts:
- Evaluate synthetic sequences generated under ground-truth $k$-th order Markov dynamics with controlled transition entropy.
- Verify statistical power and estimator recovery under Gates G8–G11:
  - **G8**: Estimator consistency (true model recovers planted order parameter).
  - **G9**: Null rejection power ($\ge 80\%$ rejection of null when order structure is planted at observed sequence lengths).
  - **G10**: False positive control ($\le 5\%$ false rejection rate under unigram null).
  - **G11**: Sample size scaling consistency across varying sequence lengths.

---

## 10. Permutation Null Hypotheses at 7 Episodes

Permutation testing at 7 episodes evaluates order dependence against unigram baselines with $B = 1000$ permutations (seeds $0, \dots, 999$):
- **Scheme S1 (Collapsed-Order Shuffle)**:
  - Pre-declared headline null hypothesis.
  - Shuffles the temporal order of items in each episode's collapsed sequence while preserving exact sample count $N$ and marginal item frequencies.
- **Scheme S3 (Constrained Shuffle)**:
  - Rejection-sampled shuffle subject to the constraint that no two adjacent items in the shuffled sequence have identical technique sets (technique level) or identical tactic sets (tactic level).
  - Introduced after the 4-episode S1/S2 analysis revealed that unconstrained shuffles create artificial consecutive identical transitions not present in collapsed real sequences.
- **Reporting Rule**:
  - S1 is the pre-declared headline.
  - S3 is reported alongside S1.
  - If S1 and S3 disagree regarding significance, both results and their divergence must be explicitly reported without selecting the more favorable result.

---

## 11. Immutability and Pre-Registration Protocol ("No-Change Rule")

- **Pre-Registration Lock**: This document is finalized and committed prior to running any model training, prediction, or evaluation on episodes E5, E6, or E7.
- **Post-Run Amendments**: Following any 7-episode model run, this file may not be modified except by appending dated, explicitly labeled amendment sections detailing post-hoc explorations.
- **Preservation of Prior Art**: The 4-episode experimental artifacts and reports (`evaluation_results.json`, `tactic_evaluation_results.json`, `permutation_test_v2_report.json`, etc.) remain archived with their verified, frozen SHA-256 hashes.


---

## Amendment 1 (2026-10-14, before any 7-episode model run)

This amendment formally records corrections and clarifications to the pre-registration protocol prior to running any model training, prediction, or evaluation on episodes E5, E6, or E7.

### 1. Model Implementation Location, Docstrings, and Fallback Rule (Correction to Section 4)
The baseline models reside in the package `src/c4/models/` (specifically `src/c4/models/markov.py` and `src/c4/models/frequency.py`), not in a single `src/c4/models.py` file.

- **`MarkovModel` class docstring** (quoted verbatim from `src/c4/models/markov.py`):
  > "First-order Markov model capturing conditional ATT&CK technique transition probabilities."

- **`FrequencyBaseline` class docstring** (quoted verbatim from `src/c4/models/frequency.py`):
  > "Frequency baseline model estimating marginal next-technique probability P(T_{t+1} = b)."

- **`markov_fallback` evaluation-level rule** (quoted verbatim from `src/c4/evaluation.py`, lines 262–266):
```python
            if m_status == "ok":
                fb_status, fb_raw, fb1, fb3 = "ok_markov", m_raw, m1, m3
            else:
                fb_status, fb_raw = "fallback_frequency", [list(c) for c in f_cands_raw]
                fb1, fb3 = f1, f3
```
- **Accuracy of `unseen_history` description in Section 4**:
  The description in Section 4 using the label `unseen_history` is inaccurate: the codebase implements fallback whenever `m_status != 'ok'` (specifically when `m_status == 'insufficient_evidence'` due to no outgoing transitions observed in training for the conditioning techniques, assigning fallback status `'fallback_frequency'`). The token `unseen_history` does not exist in `src/c4/models/` or `src/c4/evaluation.py`.

### 2. Ceiling and Coverage Exact Definitions (Correction to Section 5)
- **Ceiling Definition** (quoted verbatim from `reports/evaluation_report.md`):
  > "Ceiling: fraction of test samples whose target set contains at least one technique that appears as a target in that fold's training episodes."
  
  And from `src/c4/evaluation.py` (lines 208–232):
```python
        train_target_pool: set[str] = set()
        for ep in train_eps:
            items = ep_sequences[ep][variant]
            for i in range(len(items) - 1):
                train_target_pool.update(markov._extract_tech_set(items[i + 1]))
...
            if tgt & train_target_pool:
                ceiling_hits += 1
```
- **Coverage Definition** (quoted verbatim from `reports/evaluation_report.md`):
  > "Coverage: fraction of samples with Markov status ok."
  
  Where `status == 'ok'` indicates that the conditioning technique set had observed transitions in training.

### 3. Episode E5 Counting Bounds (Correction to Section 8)
The initial phrasing that E5 has 'zero test coverage' was an informal description; the exact per-fold counting metrics for E5 under the 7-episode design (fold 5) read directly from `reports/new_episodes_intake_audit.json` are:
- Evaluated samples ($N$): 2
- Covered samples: 0 (coverage rate: 0.0%)
- Ceiling hits: 0 (ceiling rate: 0.0%)

### 4. Real-Scale Planted Structure Power Analysis Design (Correction to Section 9)
The text previously drafted in Section 9 referenced generic Markov benchmarks rather than the actual pre-declared A4 design. The wrong text in Section 9 was drafted using generic synthetic Markov benchmark language rather than quoting the pre-declared A4 real-scale power analysis protocol established in Prompt 10b.

The actual A4 design parameters and gates, quoted directly from `reports/planted_realscale_report.md` and `reports/planted_realscale_report.json`, are:
- **Vocabulary ($V$)**: All distinct MITRE ATT&CK technique IDs present in the collapsed sequence vocabulary across the evaluated episodes.
- **Planted Successor Permutation ($\pi$)**: Deterministic cyclic permutation $\pi(t_i) = t_{(i+1) % V}$ over the sorted vocabulary without fixed points.
- **Episode Lengths**: Exact empirical collapsed sequence lengths of the evaluated episodes (yielding 95 evaluated transition samples at 7 episodes).
- **Evaluation Protocol**: Leave-One-Episode-Out cross-validation evaluating production `MarkovModel` and `FrequencyBaseline`.
- **Signal Levels ($s$)**: `0.00, 0.25, 0.50, 0.75, 1.00`.
- **Replicates**: 200 synthetic dataset replicates per signal level using random seeds `0..199`.
- **Reachable Fraction ($R$)**: Share of test fold samples whose exact $(current \to target)$ transition appears at least once in that fold's training episodes (computed independently of model predictions).
- **Pre-Declared Gates (quoted verbatim from `reports/planted_realscale_report.json`)**:
  - **G8**: "at s=0, |Markov Top-1 - 1/(V-1)| <= max(0.02, 3*SE)"
  - **G9**: "Markov Top-1 mean is non-decreasing across s levels"
  - **G10**: "at s=1.0, Markov Top-1 <= R + 1e-9 in every replicate AND mean Markov Top-1 >= 0.99 * mean R"
  - **G11**: "Negative control: with Markov deliberately broken (fixed candidate), G10 fails"


### 5. Primary Comparisons, Holm Adjustment, and Claim Boundary (Clarification to Section 6)
- The $p$-value entering the Holm-Bonferroni correction for primary tests P3 and P4 is strictly the **S1** permutation $p$-value. Scheme S3 is reported alongside S1 as a sensitivity null and does not enter the Holm step-down correction.
- The substantive claim **"improvement over the baseline demonstrated"** is governed **strictly by P1 and P2** (Markov vs. Frequency). Hypotheses P3 and P4 (Markov vs. Shuffled Null) support the separate, independent claim: **"order carries detectable signal"**.
- The paired McNemar test is two-sided; however, to claim that Markov improves over Frequency, it is an explicit requirement that **pooled Markov Hit@3 > pooled Frequency Hit@3** in addition to the Holm-adjusted $p < 0.05$.

### 6. Withdrawal of Unverified Scenario Reference (Correction to Section 1)
In Section 1, the mention of `scenario_6_macro_library` as a hypothetical counterpart to `scenario_6_macro_binary` was unverified. An automated filesystem and metadata audit across all repository files and Zenodo archives confirmed that no archive or scenario named `scenario_6_macro_library` exists. The example is confirmed **not verified** and is formally withdrawn.

### 7. Constrained Shuffle Scheme S3 Execution Protocol (Specification for Section 10)
For each episode and permutation replicate, scheme S3 shuffles the collapsed sequence uniformly at random subject to the strict constraint that no two adjacent items share identical technique sets (technique slice) or identical tactic sets (tactic slice):
- **Rejection Sampling Bound**: Rejection sampling will perform at most **10,000 tries** per episode per permutation replicate.
- **Abort Criterion**: If more than **5%** (> 50 of the 1,000 permutations) fail to find a valid constrained shuffle, the procedure must abort.
- **Reporting of Excluded Replicates**: If valid shuffles are found in $\ge 95\%$ of permutations, any failing permutations are excluded, their exact count is reported, and the mean and maximum number of rejection tries are documented.
- **Sample Invariant**: In every valid S3 permutation, the number of evaluated samples $N$ is asserted to equal the empirical observed sample count $N$ ($N=67$ at 4 episodes, $N=95$ at 7 episodes).
