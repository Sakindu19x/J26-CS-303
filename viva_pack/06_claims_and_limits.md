# 06. Scientific Claims, Statistical Decisions, and Methodological Boundaries

---

## 1. Demonstrated Scientific Claims

1. **Pipeline Reproducibility (NFR2, NFR3)**:
   - Full pipeline determinism verified across `PYTHONHASHSEED=0, 1, 4242`.
   - Raw event immutability verified with deep-copy input hashing (SHA-256 identical before and after inference).
2. **Pre-Registered Primary Hypothesis Verdict (Negative Result)**:
   - The pre-registered primary hypothesis ($H_1$: First-order Markov chain outperforms Frequency baseline at technique level) is **rejected**.
   - Frequency baseline significantly outperforms Markov at technique Hit@3 (16.84% vs 3.16%, $p = 0.0034$, paired permutation test).
3. **Sequential Order Signal at Tactic Level**:
   - Order permutation test demonstrates a statistically significant sequential dependency at the tactic level ($p = 0.0210$).
   - At the technique level, no statistically significant order signal is observed ($p = 0.5210$).
4. **Information-Theoretic Reachability Ceiling**:
   - Out-of-vocabulary and state sparsity impose an empirical ceiling of 62.11% and an A4 simulation cap of 64.98%, proving that 75% accuracy is mathematically unachievable under LOEO on this dataset.

---

## 2. Forbidden Claims (Audit Enforced)

The following claims are **strictly forbidden** and contradicted by empirical evidence:
- ❌ *"Markov chain outperforms the baseline at technique level"* (False; Frequency wins).
- ❌ *"The model achieves 75% accuracy"* (False; empirical ceiling is 62.11%).
- ❌ *"Sequential order improves technique prediction"* (False; permutation test yields $p = 0.5210$).
- ❌ *"Evaluation was conducted on live C3 incident data"* (False; historical CAM-LDS simulation telemetry only).

---

## 3. Known Limitations

- **Small Episode Count**: 7 attack episodes limit the diversity of observable transitions.
- **Zero Live C3 Telemetry**: Upstream C3 attributes (threat score, priority) are recorded as `"not provided by dataset"` pending live integration.
- **State Sparsity**: 35.79% of test samples represent unseen technique combinations, triggering frequency fallback.
