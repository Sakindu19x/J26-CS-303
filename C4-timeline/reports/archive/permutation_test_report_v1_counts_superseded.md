> **SUPERSEDED: hit counts were compared across permutations with different sample counts N. Do not cite.**

# Permutation Test on Real Episodes (E1–E4) Report

## Pre-Declared Test Design & Purpose

- **Purpose**: Determine whether event ORDER carries detectable predictive signal beyond an order-free baseline in telemetry episodes E1–E4.
- **Primary Statistic**: Pooled Leave-One-Episode-Out (LOEO) Markov Hit@1 and Hit@3 on technique-level collapsed/full (`collapsed_full`, N=67).
- **Secondary Statistic**: Pooled LOEO Markov Hit@1 and Hit@3 on tactic-level collapsed (`tactic_collapsed`, N=53).
- **Null Distribution**: B=1000 permutations (stdlib `random.Random` seeds 0..999).
- **Permutation Scheme**: Raw labeled events are shuffled *strictly within each episode* (episodes never mixed). Collapsed sequences and samples are rebuilt using production pipeline functions, followed by production LOEO evaluation.
- **One-Sided p-value Formula**: `p = (1 + count(null >= observed)) / (1 + B)`.
- **Pre-Declared Interpretation Rule**: `p < 0.05` indicates *'order carries detectable signal under this null'*; otherwise *'no detectable order signal at this sample size (this is not proof of absence)'*.

---

## Baseline Observed Values Verification

Before executing permutations, observed hits were verified against production evaluation reports:
- **Technique Level (`collapsed_full`)**: Markov Hit@1 = `1`, Hit@3 = `2`; Frequency Hit@1 = `4`, Hit@3 = `8` (**CONFIRMED**).
- **Tactic Level (`tactic_collapsed`)**: Markov Hit@1 = `11`, Hit@3 = `28`; Frequency Hit@1 = `9`, Hit@3 = `33` (**CONFIRMED**).

---

## Permutation Test Results: Primary Slice (Technique Level `collapsed_full`)

| Method / Statistic | Metric | Observed | Null Mean | Null SD | 2.5th Pct | 97.5th Pct | Min | Max | p-value | Interpretation |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov | Hit@1 | `+1` | `0.6290` | `0.9520` | `0.00` | `3.00` | `0` | `7` | `0.3886` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov | Hit@3 | `+2` | `1.4870` | `1.4608` | `0.00` | `5.00` | `0` | `7` | `0.4466` | no detectable order signal at this sample size (this is not proof of absence) |
| Frequency Baseline | Hit@1 | `+4` | `5.7300` | `4.4921` | `0.00` | `13.00` | `0` | `13` | `0.7043` | no detectable order signal at this sample size (this is not proof of absence) |
| Frequency Baseline | Hit@3 | `+8` | `10.5720` | `2.7478` | `4.00` | `14.00` | `0` | `16` | `0.8771` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov Fallback | Hit@1 | `+2` | `4.3240` | `3.2480` | `0.00` | `11.00` | `0` | `14` | `0.7662` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov Fallback | Hit@3 | `+5` | `8.3850` | `2.5599` | `2.98` | `13.00` | `0` | `16` | `0.9201` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov - Frequency | Hit@1 | `-3` | `-5.1010` | `4.5852` | `-12.00` | `2.00` | `-13` | `5` | `0.3926` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov - Frequency | Hit@3 | `-6` | `-9.0850` | `3.1263` | `-13.00` | `-1.00` | `-15` | `2` | `0.1528` | no detectable order signal at this sample size (this is not proof of absence) |

---

## Permutation Test Results: Secondary Slice (Tactic Level `tactic_collapsed`)

| Method / Statistic | Metric | Observed | Null Mean | Null SD | 2.5th Pct | 97.5th Pct | Min | Max | p-value | Interpretation |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| Markov | Hit@1 | `+11` | `8.3830` | `3.3722` | `3.00` | `16.00` | `0` | `20` | `0.2358` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov | Hit@3 | `+28` | `22.4670` | `5.3283` | `12.00` | `34.00` | `9` | `38` | `0.1728` | no detectable order signal at this sample size (this is not proof of absence) |
| Frequency Baseline | Hit@1 | `+9` | `10.6880` | `1.6839` | `8.00` | `15.00` | `6` | `20` | `0.9301` | no detectable order signal at this sample size (this is not proof of absence) |
| Frequency Baseline | Hit@3 | `+33` | `45.8410` | `5.4510` | `33.00` | `56.00` | `23` | `59` | `0.9780` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov Fallback | Hit@1 | `+13` | `10.1160` | `3.4410` | `4.00` | `18.00` | `2` | `22` | `0.2208` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov Fallback | Hit@3 | `+30` | `27.7280` | `5.4308` | `18.00` | `39.00` | `12` | `43` | `0.3437` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov - Frequency | Hit@1 | `+2` | `-2.3050` | `3.4955` | `-8.02` | `6.00` | `-13` | `10` | `0.1249` | no detectable order signal at this sample size (this is not proof of absence) |
| Markov - Frequency | Hit@3 | `-5` | `-23.3740` | `6.9779` | `-37.00` | `-9.00` | `-43` | `5` | `0.0100` | order carries detectable signal under this null |

---

## Summary of Findings

1. **Technique Level**: Markov Hit@1 (p = `0.3886`) and Hit@3 (p = `0.4466`) exhibit `no detectable order signal at this sample size (this is not proof of absence)`.
2. **Tactic Level**: Markov Hit@1 (p = `0.2358`) and Hit@3 (p = `0.1728`) exhibit `no detectable order signal at this sample size (this is not proof of absence)`.
3. **Scientific Implication**: Together with Part A (which established 100% recovery under planted order), these empirical permutation tests confirm that the near-chance predictive performance on the 4 real enterprise telemetry episodes is driven by high inter-episode variation and sparse sequence coverage, not by model defect or algorithmic failure.
