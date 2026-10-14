# P1 Audit Findings

## 1.1 S1/S3 Permutation Test v2.1 Audit
- `commit 42e941a == working tree (.md)`: **True**
- `commit 42e941a == working tree (.json)`: **True**

| Section Piece | Index (88c26ba) | Index (42e941a) | Len Before | Len After | SHA-256 Before | SHA-256 After | Identical? |
|:---|:---:|:---:|:---:|:---:|:---|:---|:---:|
| Intro / Design | 57 | 57 | 2008 | 2008 | `a218c9a84fa9ca5c08c4feb91b290909fd7260f7b5e140bb3b4cb3408f4370de` | `a218c9a84fa9ca5c08c4feb91b290909fd7260f7b5e140bb3b4cb3408f4370de` | **True** |
| Validity Section | 2067 | 2067 | 2300 | 2300 | `510f0a2d09345cb823502cbf86224a7453a3b2765da79e1ce740e1987f2184b9` | `510f0a2d09345cb823502cbf86224a7453a3b2765da79e1ce740e1987f2184b9` | **True** |
| Sample Counts | 4369 | 4369 | 1079 | 1079 | `9210bf8eef5564c362f42423d1fdb6e70fd15079e6daafb560f540f5b2c32b92` | `9210bf8eef5564c362f42423d1fdb6e70fd15079e6daafb560f540f5b2c32b92` | **True** |
| S1 Table | 5450 | 5450 | 3949 | 3949 | `1da9c6bc1c7aab4670acb3514b1f3d716894c10479778881321ffa0710f62074` | `1da9c6bc1c7aab4670acb3514b1f3d716894c10479778881321ffa0710f62074` | **True** |
| S3 Table | 9401 | 9401 | 8204 | 8204 | `0dece1897d964087688f68faf004d8376ec171f7d3b6f6fd1ade51a6a6730668` | `0dece1897d964087688f68faf004d8376ec171f7d3b6f6fd1ade51a6a6730668` | **True** |
| S2 Table | 17607 | 17607 | 3608 | 3947 | `ef51ab841b6e91de277d592f8bd6984117e037bc730f75b7418ba550019cf8d3` | `5d653eeb14b1e443f76b64faca42c6612bc6672e8a03be9df37aa6d912a4a61d` | **False** |
| Remainder / Limits | 21217 | 21556 | 947 | 947 | `10479b1a4122106645edcb7499bb1fd29a5d9257f0b447913a9816ad42edff34` | `10479b1a4122106645edcb7499bb1fd29a5d9257f0b447913a9816ad42edff34` | **True** |

- `total_json_differing_leaves`: 8
- `numeric_leaves_equal`: **True**
- `all_differing_leaves_are_strings`: **True**

## 1.2 PNG and Learning Curve File Hashes

| Artifact | Commit / State | Byte Size | SHA-256 |
|:---|:---|:---:|:---|
| `reports/7ep/learning_curve_7ep.png` | `88c26ba` | 245761 | `aa2f8d3aa7a48ccdc6d7e0dd6b8eb29c71818ffd98ef5e216a60a9a9b523ea81` |
| `reports/7ep/learning_curve_7ep.png` | `4e9d663` | 245761 | `aa2f8d3aa7a48ccdc6d7e0dd6b8eb29c71818ffd98ef5e216a60a9a9b523ea81` |
| `reports/7ep/learning_curve_7ep.png` | `42e941a` | 374522 | `6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b` |
| `reports/7ep/learning_curve_7ep.png` | Working Tree | 374522 | `6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b` |
| `reports/7ep/learning_curve_7ep_results.json` | `88c26ba` | 56970 | `513cc5f9eb15571c0990e8d4f5f8b62b808afb360511b7727eb53d4908ae3d31` |
| `reports/7ep/learning_curve_7ep_results.json` | `42e941a` | 68541 | `88cac63f0083f2f603050bc32612b0fffb83d5368b930da7e81c5f85566f1da0` |
| `reports/7ep/learning_curve_7ep_report.md` | `88c26ba` | 12475 | `b0a65aee12187162c1f7061855e659b7afecba663cc6572156cc817d888b5d30` |
| `reports/7ep/learning_curve_7ep_report.md` | `42e941a` | 18526 | `565387a7831a36b14f9abde7df512aaaa3abecbdc4f8efff9d9cc7959e9cdc36` |
| `reports/7ep/learning_curve_7ep_plot_data.json` | `88c26ba` | 2335 | `9cec95aea4350a834e93cad5a4120c1423a6d0c6105cd33cb1d75986eac5d922` |
| `reports/7ep/learning_curve_7ep_plot_data.json` | `42e941a` | 6799 | `c208230b095248fc73d9110fe9b5d83d6f8e9313df01684cd357fe1e13609b80` |

| Baseline Entry | 88c26ba Baseline Hash | 42e941a Baseline Hash |
|:---|:---|:---|
| `reports/7ep/learning_curve_7ep.png` | `aa2f8d3aa7a48ccdc6d7e0dd6b8eb29c71818ffd98ef5e216a60a9a9b523ea81` | `6477f996ef65d8dbad4305e126720a443762841e40c4c2d7cdf316be2335062b` |
| `reports/7ep/learning_curve_7ep_results.json` | `9297d86262c70ee3b733556d68ff2d061b0eb584c1173beaac0e4ed6d873a00c` | `826b964dfe0c9661372e5ec72dac8b32b8d16b61854552eee7774f53964e6324` |
| `reports/7ep/learning_curve_7ep_report.md` | `50ec55b3def0b87f2bb5c80dcf2eaaee64a7f054c83d4dfda013f25c37aae1ca` | `00a5947ec909691c4d5b3ff4f4911e578db89ae6cbfe061bcad48a09a6b2ec99` |
| `reports/7ep/learning_curve_7ep_plot_data.json` | `9fc95e0fad1402d5ffc38051855171cbcf8008f484391e8a0639543ad9057364` | `b4aa2bbb6b296e02a3e6f4a184a86eac932a8d46244205a04daca43a30e3edf7` |
| `data/processed_7ep/learning_curve_7ep.csv` | `6b43483d0800a1c5890d467afd012724a772af98129aa510ecc673ba37091867` | `6b43483d0800a1c5890d467afd012724a772af98129aa510ecc673ba37091867` |

- `png_hash_changed_between_88c26ba_and_42e941a`: **True**
- `step0_table_png_hash_matched_working_tree_prior_to_commit`: **True**

## 1.3 Exempt Tokens and Intro Numbers Audit

| Report | Total Lines | Total Tokens | Exempt Tokens | Tested Tokens | Detected | Undetected |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| `learning_curve_7ep_report.md` | 233 | 1673 | 107 | 1566 | 1566 | 0 |
| `permutation_7ep_report.md` | 143 | 697 | 32 | 665 | 665 | 0 |
| `planted_realscale_7ep_report.md` | 48 | 168 | 18 | 150 | 150 | 0 |
| `e5_removed_report.md` | 106 | 455 | 33 | 422 | 422 | 0 |
| `holm_claim_rule_report.md` | 43 | 95 | 16 | 79 | 79 | 0 |
| `diagnostics_7ep.md` | 89 | 398 | 20 | 378 | 378 | 0 |
| `e5_hit1_change_diagnostic.md` | 42 | 177 | 36 | 141 | 141 | 0 |

- `learning_curve_lines_1_to_30_not_covered_count`: **0**
- `intro_numbers_covered_by_sweep`: **True**

## 1.4 Prereg Strings and Append-Only History

| Search String | Commits Found in `git log -S` |
|:---|:---|
| `Stage 1 Data Build Directory and Processed Files` | 4e9d663 Prereg amendment 5: record that amendment 2 as committed differs from earlier chat report |
| `Primary Evaluation Protocol` | 4e9d663 Prereg amendment 5: record that amendment 2 as committed differs from earlier chat report |
| `Model Execution Rules` | 4e9d663 Prereg amendment 5: record that amendment 2 as committed differs from earlier chat report |
| `Reporting Rules` | 4e9d663 Prereg amendment 5: record that amendment 2 as committed differs from earlier chat report |
| `Episodes and Scenario Mapping` | 4e9d663 Prereg amendment 5: record that amendment 2 as committed differs from earlier chat report |
| `returning 0 matches` | None (0 commits) |

| Amendment Block | Line Range | SHA-256 |
|:---|:---:|:---|
| ## Amendment 1 (2026-10-14, before any 7-episode model run) | Lines 157-239 | `bbb10f658778e4dda3c97df0f631e57d7b20632a5f410735b9cfbb3a97a94af6` |
| ## Amendment 2 (2026-10-14, before any 7-episode model run) | Lines 240-257 | `e4263f5fc12d5478d8a9efdef7d2f852da5815646af0f1c3ab7e2b844a263ebd` |
| ## Amendment 3 (2026-10-14, before any 7-episode model run) | Lines 258-271 | `470d22472345d50ea4c7948307751ab5d816231c0e3381e38edeb4c91831f552` |
| ## Amendment 4 (2026-10-14, before any inference run) | Lines 272-294 | `5b5571720ac0ca10fa2d60fe9bf4fe5a01b43279e837b34ecf17fcedee4a4c01` |
| ## Amendment 5 (2026-10-15, before any inference result was interpreted) | Lines 295-302 | `408b852c5ce3cac1b08456070d5ce04acedfc998940bd80c721376fe28084f9c` |

| Commit Transition | Added Lines | Removed/Changed Lines | Append-Only? |
|:---|:---:|:---:|:---:|
| `2cf7786` -> `340c788` | 86 | 0 | **True** |
| `340c788` -> `3a6b306` | 18 | 0 | **True** |
| `3a6b306` -> `b9ab249` | 15 | 0 | **True** |
| `b9ab249` -> `fdc9b17` | 24 | 0 | **True** |
| `fdc9b17` -> `88c26ba` | 0 | 0 | **True** |
| `88c26ba` -> `4e9d663` | 7 | 0 | **True** |
| `4e9d663` -> `42e941a` | 0 | 0 | **True** |

- `append_only_holds_across_all_pairs`: **True**

## 1.5 Learning Curve k=6 Aggregation Audit

### Slice: `technique_collapsed_full`

| Metric | LC k=6 Ep-Mean | Eval Fold-Mean | Diff (Ep-Mean) | LC k=6 Pooled | Eval Pooled | Diff (Pooled) | Pass (<1e-9)? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `markov_hit1` | 0.03370927 | 0.03370927 | 0.00e+00 | 0.03157895 | 0.03157895 | 0.00e+00 | **True** |
| `markov_hit3` | 0.03370927 | 0.03370927 | 0.00e+00 | 0.03157895 | 0.03157895 | 0.00e+00 | **True** |
| `frequency_hit1` | 0.05948204 | 0.05948204 | 0.00e+00 | 0.07368421 | 0.07368421 | 0.00e+00 | **True** |
| `frequency_hit3` | 0.14481442 | 0.14481442 | 0.00e+00 | 0.16842105 | 0.16842105 | 0.00e+00 | **True** |
| `markov_fallback_hit1` | 0.03370927 | 0.03370927 | 0.00e+00 | 0.03157895 | 0.03157895 | 0.00e+00 | **True** |
| `markov_fallback_hit3` | 0.04391335 | 0.04391335 | 0.00e+00 | 0.04210526 | 0.04210526 | 0.00e+00 | **True** |
| `coverage` | 0.57064686 | 0.57064686 | 0.00e+00 | 0.64210526 | 0.64210526 | 0.00e+00 | **True** |
| `ceiling` | 0.54849624 | 0.54849624 | 0.00e+00 | 0.62105263 | 0.62105263 | 0.00e+00 | **True** |

### Slice: `tactic_collapsed`

| Metric | LC k=6 Ep-Mean | Eval Fold-Mean | Diff (Ep-Mean) | LC k=6 Pooled | Eval Pooled | Diff (Pooled) | Pass (<1e-9)? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `markov_hit1` | 0.30934066 | 0.30934066 | 0.00e+00 | 0.28947368 | 0.28947368 | 0.00e+00 | **True** |
| `markov_hit3` | 0.62518315 | 0.62518315 | 0.00e+00 | 0.63157895 | 0.63157895 | 0.00e+00 | **True** |
| `frequency_hit1` | 0.22692308 | 0.22692308 | 0.00e+00 | 0.18421053 | 0.18421053 | 0.00e+00 | **True** |
| `frequency_hit3` | 0.69725275 | 0.69725275 | 0.00e+00 | 0.63157895 | 0.63157895 | 0.00e+00 | **True** |
| `markov_fallback_hit1` | 0.32838828 | 0.32838828 | 0.00e+00 | 0.31578947 | 0.31578947 | 0.00e+00 | **True** |
| `markov_fallback_hit3` | 0.64423077 | 0.64423077 | 0.00e+00 | 0.65789474 | 0.65789474 | 0.00e+00 | **True** |
| `coverage` | 0.98095238 | 0.98095238 | 0.00e+00 | 0.97368421 | 0.97368421 | 0.00e+00 | **True** |
| `ceiling` | 0.96309524 | 0.96309524 | 0.00e+00 | 0.96052632 | 0.96052632 | 0.00e+00 | **True** |

- `all_k6_metrics_pass_lt_1e9`: **True**

## Gate Summary
- `Gate 1.1 (numeric leaves equal, string-only diffs)`: **True**
- `Gate 1.4 (append-only holds for all commits)`: **True**
- `Gate 1.5 (all k=6 differences < 1e-9)`: **True**
- `Overall P1 Gate`: **PASS**
