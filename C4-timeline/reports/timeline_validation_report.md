# Forensic Attack Timeline & Sequence Validation Report

> [!IMPORTANT]
> **Forensic Causality Notice:** Note on Forensic Causality: Chronological ordering of attack steps reflects the temporal manifestation sequence recorded in telemetry; temporal precedence does not by itself prove causal dependency.

## 1. Episode Timeline & Sequence Metrics

| Episode | Total Events | Labeled (GT) | Unlabeled | Missing TS | Duplicate IDs | Raw Seq Length | Collapsed Seq Length | Distinct Techniques |
|---|---|---|---|---|---|---|---|---|
| **E1** | 38 | 27 | 11 | 0 | None | **27** | **19** | 31 |
| **E2** | 29 | 21 | 8 | 0 | None | **21** | **20** | 21 |
| **E3** | 77 | 29 | 48 | 0 | None | **29** | **21** | 23 |
| **E4** | 46 | 22 | 24 | 0 | None | **22** | **11** | 10 |

## 2. Integrity & Quality Findings

- **Global Duplicate Event IDs:** None
- **Chronological Monotonicity:** Verified. All valid timestamps in all episodes are strictly sorted in non-decreasing order.
- **Timestamp Completeness:** 100% of AttackMate steps have valid UTC timestamps (0 missing timestamps).
- **Unlabeled Steps Integrity:** All unlabeled steps (total 91 across 4 episodes) are fully preserved in the timeline with `label_status = 'unlabeled'` and are cleanly excluded from the ATT&CK sequence items while tracking `unlabeled_steps_skipped_before`.

## 3. Sequence Compression Summary

| Episode | Raw Steps | Collapsed Steps | Reduction (%) | Consecutive Repetition Notes |
|---|---|---|---|---|
| **E1** | 27 | 19 | 29.6% | Merged consecutive identical technique sets |
| **E2** | 21 | 20 | 4.8% | Merged consecutive identical technique sets |
| **E3** | 29 | 21 | 27.6% | Merged consecutive identical technique sets |
| **E4** | 22 | 11 | 50.0% | Merged consecutive identical technique sets |
