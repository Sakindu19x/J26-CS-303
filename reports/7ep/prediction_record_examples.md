# Explainable Prediction Record Worked Examples (7 Episodes, Schema 1.1.0)

> [!NOTE]
> This report presents seven full, worked, representative prediction records generated
> by Component 4 under Leave-One-Episode-Out (LOEO) evaluation across 7 episodes.
> Every record conforms to `schemas/c4_prediction_record.schema.json` (version 1.1.0) and satisfies
> requirements FR4 (candidate ranking), FR5 (evidence support), FR6 (explainability surface),
> FR7 (confidence scoring and reliability context), NFR2 (reproducibility), NFR3 (provenance),
> and NFR6 (schema compliance).

## Support Caution Summary

- **Total Prediction Records**: 171 (95 technique, 76 tactic)
- **Cautioned Records**: 92/171 (83/95 technique records, 9/76 tactic records)
- **Caution Threshold Policy**: A prediction record is flagged with `caution=True` when the current attack state has fewer than 2 supporting training episodes or fewer than 3 total historical transitions from that state. In the evaluation dataset, all 34 unobserved states (which trigger unconditional frequency fallback) are flagged with caution.
- **Fallback Mechanism**: The evaluation dataset contains exactly one fallback reason: unobserved historical state (zero outgoing training transitions). No secondary fallback modes exist in the data.

## Summary of Exemplars (7 Distinct Sample IDs)

| Exemplar Category | Sample ID | Episode | Level | Status | Caution | Top-1 Candidate | Top-1 Score | Score Type |
|:---|:---|:---:|:---:|:---:|:---:|:---|:---:|:---|
| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | YES | `T1057` | 0.4815 | `transition_probability` |
| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` | YES | `T1589.002` | 1.0000 | `transition_probability` |
| 3. Frequency Fallback (Unseen State) | `E1-col-ful-K03` | E1 | technique | `fallback` | YES | `T1105` | 0.0714 | `training_frequency_share` |
| 4. Tied Rank Boundary | `E1-col-ful-K02` | E1 | technique | `ok` | YES | `T1071.001` | 0.5000 | `transition_probability` |
| 5. Tactic-Level Prediction | `E1-tac-col-K01` | E1 | tactic | `ok` | YES | `command-and-control` | 0.5000 | `transition_probability` |
| 6. Single-Episode Support State | `E1-col-ful-K05` | E1 | technique | `ok` | YES | `T1033` | 1.0000 | `transition_probability` |
| 7. Set-Valued State | `E1-col-ful-K08` | E1 | technique | `ok` | No | `T1057` | 0.2083 | `transition_probability` |

## Exemplar: 1. First Hit (`E2-col-ful-K05`)

- **Description**: Technique prediction where top candidate matches ground-truth next step.
- **Record ID**: `27251c1aabbbcc25ac635333954a24ab164b2f4fd6b67de416af7b97639bb415`
- **Episode**: E2
- **Prediction Level**: technique
- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76f35d04d6981a03d8eb8e24b892`
- **Input Events SHA-256**: `c0d116b9f5e9f000b2aa4a660bebfe4394fafe44a737db67c8b2b0d14d888023`
- **Record SHA-256**: `5490301c6d6a8abdb6898c01f6afe15f9a6d7b2e649ac3727d763ad140eeb8cf`
- **Current State**: Techniques=`['T1083']`, Tactics=`['discovery']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=3, Transitions from State=2.08, Caution=True
- **Caution Text**: Caution: low historical support (observed in 3 training episode(s) with 2.1 state transitions; caution threshold: < 2 episodes or < 3 transitions).

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1057` | Process Discovery | 0.4815 | `transition_probability` | 1.00 | 2.08 | [E7] | Discovery |
| 2 | `T1059.004` | Unix Shell | 0.4815 | `transition_probability` | 1.00 | 2.08 | [E3] | Execution |
| 3 | `T1033` | System Owner/User Discovery | 0.0370 | `transition_probability` | 0.08 | 2.08 | [E1] | Discovery |

### Deterministic Explanation

> State [T1083] recognized in training episodes (E1, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 (Process Discovery) with estimated transition probability 0.4815 based on 1.00/2.08 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 3 training episode(s) with 2.1 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-1 boundary is tied among candidates: ['T1057', 'T1059.004']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "discovery"
    ],
    "current_technique_set": [
      "T1083"
    ],
    "episode_id": "E2",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-10-01T10:16:01.232391+00:00",
    "previous_supporting_techniques": [
      "T1021.004",
      "T1071.001",
      "T1573.001",
      "T1105",
      "T1547",
      "T1569",
      "T1083"
    ],
    "sample_id": "E2-col-ful-K05"
  },
  "input_events_sha256": "c0d116b9f5e9f000b2aa4a660bebfe4394fafe44a737db67c8b2b0d14d888023",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E2.json",
    "model_file_sha256": "3823a1d7a319bc0e2c00aeb9f657b283666a76f35d04d6981a03d8eb8e24b892",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E1",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 118.0
  },
  "prediction_type": "technique",
  "record_id": "27251c1aabbbcc25ac635333954a24ab164b2f4fd6b67de416af7b97639bb415",
  "record_sha256": "5490301c6d6a8abdb6898c01f6afe15f9a6d7b2e649ac3727d763ad140eeb8cf",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1083] recognized in training episodes (E1, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 (Process Discovery) with estimated transition probability 0.4815 based on 1.00/2.08 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 3 training episode(s) with 2.1 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-1 boundary is tied among candidates: ['T1057', 'T1059.004']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07456140350877193
      },
      {
        "candidate_id": "T1033",
        "candidate_name": "System Owner/User Discovery",
        "score": 0.053643724696356275
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03289473684210526
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "denominator": 2.0769230769230766,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.48148148148148145,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": "Unix Shell",
        "denominator": 2.0769230769230766,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.48148148148148145,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E3"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Execution"
        ],
        "tactics": [
          "execution"
        ]
      },
      {
        "candidate_id": "T1033",
        "candidate_name": "System Owner/User Discovery",
        "denominator": 2.0769230769230766,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.07692307692307693,
        "score": 0.037037037037037035,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E1"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": true,
      "caution_text": "Caution: low historical support (observed in 3 training episode(s) with 2.1 state transitions; caution threshold: < 2 episodes or < 3 transitions).",
      "n_supporting_training_episodes": 3,
      "n_transitions_from_state": 2.0769230769230766
    },
    "tie_flags": {
      "tie_at_top1": true,
      "tie_at_top3_boundary": false,
      "tied_candidates": [
        "T1057",
        "T1059.004"
      ]
    }
  }
}
```

---

## Exemplar: 2. First Miss (`E1-col-ful-K01`)

- **Description**: Technique prediction where top candidate missed ground-truth next step.
- **Record ID**: `29a9042a4b69807137fea14d8690d88a8e9b171d93f37bdfbb48dea0c7022d6f`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `9a770d3be96e6fcaa88bf3b11889b3df03104553f3227367ee4b8c3a967f67ea`
- **Record SHA-256**: `2010d4a016ca0bd5765478a6e20bba8af9fb503aca26b71792fe3330839f3b0b`
- **Current State**: Techniques=`['T1590.002', 'T1591']`, Tactics=`['reconnaissance']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=1, Transitions from State=1.00, Caution=True
- **Caution Text**: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1589.002` | Email Addresses | 1.0000 | `transition_probability` | 1.00 | 1.00 | [E7] | Reconnaissance |

### Deterministic Explanation

> State [T1590.002, T1591] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1589.002 (Email Addresses) with estimated transition probability 1.0000 based on 1.00/1.00 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "reconnaissance"
    ],
    "current_technique_set": [
      "T1590.002",
      "T1591"
    ],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-09-22T13:48:45.914565+00:00",
    "previous_supporting_techniques": [
      "T1590.002",
      "T1591"
    ],
    "sample_id": "E1-col-ful-K01"
  },
  "input_events_sha256": "9a770d3be96e6fcaa88bf3b11889b3df03104553f3227367ee4b8c3a967f67ea",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E1.json",
    "model_file_sha256": "76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 108.0
  },
  "prediction_type": "technique",
  "record_id": "29a9042a4b69807137fea14d8690d88a8e9b171d93f37bdfbb48dea0c7022d6f",
  "record_sha256": "2010d4a016ca0bd5765478a6e20bba8af9fb503aca26b71792fe3330839f3b0b",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1590.002, T1591] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1589.002 (Email Addresses) with estimated transition probability 1.0000 based on 1.00/1.00 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1589.002",
        "candidate_name": "Email Addresses",
        "denominator": 1.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 1.0,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Reconnaissance"
        ],
        "tactics": [
          "reconnaissance"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": true,
      "caution_text": "Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).",
      "n_supporting_training_episodes": 1,
      "n_transitions_from_state": 1.0
    },
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": false,
      "tied_candidates": []
    }
  }
}
```

---

## Exemplar: 3. Frequency Fallback (Unseen State) (`E1-col-ful-K03`)

- **Description**: Unobserved historical state; dataset exhibits exactly one fallback reason (unseen state with zero outgoing training transitions); falls back to unconditional training frequency baseline.
- **Record ID**: `b4bc22cb9dc27dfaa9f231770c1315b25872e66680c6980c7e4b87673c0914d2`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `ec5bfeda049ea7a6356dc0b4df036554ad41c221af955ced8abf5f400db4d5f5`
- **Record SHA-256**: `e4b71b0f0336dcbc8d05a1918a9881aea6f09454a5f2398165a0072e88a8d350`
- **Current State**: Techniques=`['T1595.002']`, Tactics=`['reconnaissance']`
- **Model Status**: `fallback`
- **Support Metrics**: Supporting Episodes=0, Transitions from State=0.00, Caution=True
- **Caution Text**: Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators.

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1105` | Ingress Tool Transfer | 0.0714 | `training_frequency_share` | 5.50 | 77.00 | [E2, E3, E4, E6] | Command and Control |
| 2 | `T1003.008` | /etc/passwd and /etc/shadow | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E3, E7] | Credential Access |
| 3 | `T1057` | Process Discovery | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E7] | Discovery |

### Alternative Candidates (Ranks 4..k)

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 4 | `T1083` | File and Directory Discovery | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E3, E7] |
| 5 | `T1059.004` | Unix Shell | 0.0303 | `training_frequency_share` | 2.33 | 77.00 | [E3, E6, E7] |
| 6 | `T1078.003` | Local Accounts | 0.0303 | `training_frequency_share` | 2.33 | 77.00 | [E4] |
| 7 | `T1016` | System Network Configuration Discovery | 0.0260 | `training_frequency_share` | 2.00 | 77.00 | [E2, E7] |
| 8 | `T1041` | Exfiltration Over C2 Channel | 0.0260 | `training_frequency_share` | 2.00 | 77.00 | [E2, E7] |

### Deterministic Explanation

> State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 (Ingress Tool Transfer) with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Support Context: Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "reconnaissance"
    ],
    "current_technique_set": [
      "T1595.002"
    ],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-09-22T13:49:32.635068+00:00",
    "previous_supporting_techniques": [
      "T1590.002",
      "T1591",
      "T1592.002",
      "T1595",
      "T1595.002"
    ],
    "sample_id": "E1-col-ful-K03"
  },
  "input_events_sha256": "ec5bfeda049ea7a6356dc0b4df036554ad41c221af955ced8abf5f400db4d5f5",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E1.json",
    "model_file_sha256": "76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 108.0
  },
  "prediction_type": "technique",
  "record_id": "b4bc22cb9dc27dfaa9f231770c1315b25872e66680c6980c7e4b87673c0914d2",
  "record_sha256": "e4b71b0f0336dcbc8d05a1918a9881aea6f09454a5f2398165a0072e88a8d350",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [
      {
        "candidate_id": "T1083",
        "candidate_name": "File and Directory Discovery",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E3",
          "E7"
        ],
        "supporting_episodes_count": 3,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": "Unix Shell",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.3333333333333335,
        "score": 0.030303030303030304,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E3",
          "E6",
          "E7"
        ],
        "supporting_episodes_count": 3,
        "tactic_display": [
          "Execution"
        ],
        "tactics": [
          "execution"
        ]
      },
      {
        "candidate_id": "T1078.003",
        "candidate_name": "Local Accounts",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.333333333333333,
        "score": 0.0303030303030303,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E4"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Defense Evasion",
          "Initial Access",
          "Persistence",
          "Privilege Escalation"
        ],
        "tactics": [
          "defense-evasion",
          "initial-access",
          "persistence",
          "privilege-escalation"
        ]
      },
      {
        "candidate_id": "T1016",
        "candidate_name": "System Network Configuration Discovery",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1041",
        "candidate_name": "Exfiltration Over C2 Channel",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Exfiltration"
        ],
        "tactics": [
          "exfiltration"
        ]
      }
    ],
    "explanation": "State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 (Ingress Tool Transfer) with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Support Context: Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 5.5,
        "score": 0.07142857142857142,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E3",
          "E4",
          "E6"
        ],
        "supporting_episodes_count": 4,
        "tactic_display": [
          "Command and Control"
        ],
        "tactics": [
          "command-and-control"
        ]
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E3",
          "E7"
        ],
        "supporting_episodes_count": 3,
        "tactic_display": [
          "Credential Access"
        ],
        "tactics": [
          "credential-access"
        ]
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "denominator": 77.0,
        "name_source": "technique_tactic_reference.json",
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      }
    ],
    "status": "fallback",
    "support": {
      "caution": true,
      "caution_text": "Caution: unobserved state in training episodes (0 transitions observed). Prediction derived from unconditional training frequency baseline; verify against secondary indicators.",
      "n_supporting_training_episodes": 0,
      "n_transitions_from_state": 0.0
    },
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": true,
      "tied_candidates": [
        "T1057",
        "T1083"
      ]
    }
  }
}
```

---

## Exemplar: 4. Tied Rank Boundary (`E1-col-ful-K02`)

- **Description**: Candidate scores tied at rank boundary; resolved deterministically by lexicographical order.
- **Record ID**: `199d080a07dd6020a4ca627b326c0aa2d74635f3fb0dfcc1d2b27450e56908f1`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `fccbaf4fc2989e6e9c644aba313bdf28a556a509bf945c3c8d146ee8540257d4`
- **Record SHA-256**: `53dc1fb3c213fa176623fd37f39228a58991ed1194336ad3e6ea5d066c90b2bb`
- **Current State**: Techniques=`['T1592.002', 'T1595']`, Tactics=`['reconnaissance']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=1, Transitions from State=1.00, Caution=True
- **Caution Text**: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1071.001` | Web Protocols | 0.5000 | `transition_probability` | 0.50 | 0.50 | [E7] | Command and Control |
| 2 | `T1573.001` | Symmetric Cryptography | 0.5000 | `transition_probability` | 0.50 | 0.50 | [E7] | Command and Control |

### Deterministic Explanation

> State [T1592.002, T1595] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1071.001 (Web Protocols) with estimated transition probability 0.5000 based on 0.50/0.50 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-1 boundary is tied among candidates: ['T1071.001', 'T1573.001']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "reconnaissance"
    ],
    "current_technique_set": [
      "T1592.002",
      "T1595"
    ],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-09-22T13:49:04.518780+00:00",
    "previous_supporting_techniques": [
      "T1590.002",
      "T1591",
      "T1592.002",
      "T1595"
    ],
    "sample_id": "E1-col-ful-K02"
  },
  "input_events_sha256": "fccbaf4fc2989e6e9c644aba313bdf28a556a509bf945c3c8d146ee8540257d4",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E1.json",
    "model_file_sha256": "76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 108.0
  },
  "prediction_type": "technique",
  "record_id": "199d080a07dd6020a4ca627b326c0aa2d74635f3fb0dfcc1d2b27450e56908f1",
  "record_sha256": "53dc1fb3c213fa176623fd37f39228a58991ed1194336ad3e6ea5d066c90b2bb",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1592.002, T1595] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1071.001 (Web Protocols) with estimated transition probability 0.5000 based on 0.50/0.50 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-1 boundary is tied among candidates: ['T1071.001', 'T1573.001']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1071.001",
        "candidate_name": "Web Protocols",
        "denominator": 0.5,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.5,
        "score": 0.5,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Command and Control"
        ],
        "tactics": [
          "command-and-control"
        ]
      },
      {
        "candidate_id": "T1573.001",
        "candidate_name": "Symmetric Cryptography",
        "denominator": 0.5,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.5,
        "score": 0.5,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Command and Control"
        ],
        "tactics": [
          "command-and-control"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": true,
      "caution_text": "Caution: low historical support (observed in 1 training episode(s) with 1.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).",
      "n_supporting_training_episodes": 1,
      "n_transitions_from_state": 1.0
    },
    "tie_flags": {
      "tie_at_top1": true,
      "tie_at_top3_boundary": false,
      "tied_candidates": [
        "T1071.001",
        "T1573.001"
      ]
    }
  }
}
```

---

## Exemplar: 5. Tactic-Level Prediction (`E1-tac-col-K01`)

- **Description**: Next-tactic prediction demonstrating secondary LOEO evaluation slice.
- **Record ID**: `a3a8bc98a9ce0c08c9fafff3c9b131e4b47595cf213efb900a3377b9e7b5d6be`
- **Episode**: E1
- **Prediction Level**: tactic
- **Model SHA-256**: `a9c83f06be95591cb05973b44275bdd2a3003fa6247874503d49466e02bda95c`
- **Input Events SHA-256**: `4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945`
- **Record SHA-256**: `b4812261b8b33924ee2bee2ac9e53961894ce16ff629d967b6fa8d99e2e28949`
- **Current State**: Techniques=`[]`, Tactics=`['reconnaissance']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=1, Transitions from State=2.00, Caution=True
- **Caution Text**: Caution: low historical support (observed in 1 training episode(s) with 2.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `command-and-control` | Command and Control | 0.5000 | `transition_probability` | 1.00 | 1.20 | [E7] | Command and Control |
| 2 | `credential-access` | Credential Access | 0.1000 | `transition_probability` | 0.20 | 1.20 | [E7] | Credential Access |
| 3 | `defense-evasion` | Defense Evasion | 0.1000 | `transition_probability` | 0.20 | 1.20 | [E7] | Defense Evasion |

### Alternative Candidates (Ranks 4..k)

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 4 | `initial-access` | Initial Access | 0.1000 | `transition_probability` | 0.20 | 1.20 | [E7] |
| 5 | `persistence` | Persistence | 0.1000 | `transition_probability` | 0.20 | 1.20 | [E7] |
| 6 | `privilege-escalation` | Privilege Escalation | 0.1000 | `transition_probability` | 0.20 | 1.20 | [E7] |

### Deterministic Explanation

> State [reconnaissance] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-tactic prediction is command-and-control (Command and Control) with estimated transition probability 0.5000 based on 1.00/1.20 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 2.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-3 rank boundary is tied with alternative candidates: ['defense-evasion', 'initial-access']. Empirical Reliability Context: Tactic Level (tactic_collapsed, N=76): Markov Hit@3 63.16% [51.93%, 73.12%] vs Frequency 63.16% [51.93%, 73.12%]; Coverage 97.37%. Order signal statistically significant under permutation S1. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "reconnaissance"
    ],
    "current_technique_set": [],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": null,
    "previous_supporting_techniques": [],
    "sample_id": "E1-tac-col-K01"
  },
  "input_events_sha256": "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/tactic_collapsed/E1.json",
    "model_file_sha256": "a9c83f06be95591cb05973b44275bdd2a3003fa6247874503d49466e02bda95c",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 112.0
  },
  "prediction_type": "tactic",
  "record_id": "a3a8bc98a9ce0c08c9fafff3c9b131e4b47595cf213efb900a3377b9e7b5d6be",
  "record_sha256": "b4812261b8b33924ee2bee2ac9e53961894ce16ff629d967b6fa8d99e2e28949",
  "schema_version": "1.1.0",
  "tactic_prediction": {
    "alternatives": [
      {
        "candidate_id": "initial-access",
        "candidate_name": "Initial Access",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.2,
        "score": 0.1,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Initial Access"
        ],
        "tactics": [
          "initial-access"
        ]
      },
      {
        "candidate_id": "persistence",
        "candidate_name": "Persistence",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.2,
        "score": 0.1,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Persistence"
        ],
        "tactics": [
          "persistence"
        ]
      },
      {
        "candidate_id": "privilege-escalation",
        "candidate_name": "Privilege Escalation",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.2,
        "score": 0.1,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Privilege Escalation"
        ],
        "tactics": [
          "privilege-escalation"
        ]
      }
    ],
    "explanation": "State [reconnaissance] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-tactic prediction is command-and-control (Command and Control) with estimated transition probability 0.5000 based on 1.00/1.20 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 2.0 state transitions; caution threshold: < 2 episodes or < 3 transitions). Notice: Top-3 rank boundary is tied with alternative candidates: ['defense-evasion', 'initial-access']. Empirical Reliability Context: Tactic Level (tactic_collapsed, N=76): Markov Hit@3 63.16% [51.93%, 73.12%] vs Frequency 63.16% [51.93%, 73.12%]; Coverage 97.37%. Order signal statistically significant under permutation S1. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "discovery",
        "candidate_name": "Discovery",
        "score": 0.20634920634920634
      },
      {
        "candidate_id": "defense-evasion",
        "candidate_name": "Defense Evasion",
        "score": 0.16957671957671955
      },
      {
        "candidate_id": "command-and-control",
        "candidate_name": "Command and Control",
        "score": 0.11825396825396825
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Tactic Level (tactic_collapsed, N=76): Markov Hit@3 63.16% [51.93%, 73.12%] vs Frequency 63.16% [51.93%, 73.12%]; Coverage 97.37%. Order signal statistically significant under permutation S1. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.9736842105263158,
      "frequency_hit3_pooled": 0.631578947368421,
      "frequency_hit3_wilson95": [
        0.5192506510138936,
        0.731245773968965
      ],
      "markov_hit3_pooled": 0.631578947368421,
      "markov_hit3_wilson95": [
        0.5192506510138936,
        0.731245773968965
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 76,
      "slice": "tactic_collapsed"
    },
    "ranked_candidates": [
      {
        "candidate_id": "command-and-control",
        "candidate_name": "Command and Control",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.5,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Command and Control"
        ],
        "tactics": [
          "command-and-control"
        ]
      },
      {
        "candidate_id": "credential-access",
        "candidate_name": "Credential Access",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.2,
        "score": 0.1,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Credential Access"
        ],
        "tactics": [
          "credential-access"
        ]
      },
      {
        "candidate_id": "defense-evasion",
        "candidate_name": "Defense Evasion",
        "denominator": 1.2,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.2,
        "score": 0.1,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Defense Evasion"
        ],
        "tactics": [
          "defense-evasion"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": true,
      "caution_text": "Caution: low historical support (observed in 1 training episode(s) with 2.0 state transitions; caution threshold: < 2 episodes or < 3 transitions).",
      "n_supporting_training_episodes": 1,
      "n_transitions_from_state": 2.0
    },
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": true,
      "tied_candidates": [
        "defense-evasion",
        "initial-access"
      ]
    }
  },
  "technique_prediction": null
}
```

---

## Exemplar: 6. Single-Episode Support State (`E1-col-ful-K05`)

- **Description**: State observed in exactly 1 training episode; demonstrates low-support caution handling.
- **Record ID**: `d7a92cd7407c66236a1778b007e59c08b75790fcbe34d85ffa186efbea30f90d`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `45be3de1fbc85e25f5e378620059ad4e858e4ac3092e9ed40a7c31d682ac9972`
- **Record SHA-256**: `40e2c2cb9cf6f31fdce3ee384541a55a2cd051fccf5a2d034c05a226a11d0527`
- **Current State**: Techniques=`['T1059.006', 'T1190']`, Tactics=`['initial-access']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=1, Transitions from State=0.33, Caution=True
- **Caution Text**: Caution: low historical support (observed in 1 training episode(s) with 0.3 state transitions; caution threshold: < 2 episodes or < 3 transitions).

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1033` | System Owner/User Discovery | 1.0000 | `transition_probability` | 0.33 | 0.33 | [E7] | Discovery |

### Deterministic Explanation

> State [T1059.006, T1190] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1033 (System Owner/User Discovery) with estimated transition probability 1.0000 based on 0.33/0.33 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 0.3 state transitions; caution threshold: < 2 episodes or < 3 transitions). Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "initial-access"
    ],
    "current_technique_set": [
      "T1059.006",
      "T1190"
    ],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-09-22T13:52:23.317936+00:00",
    "previous_supporting_techniques": [
      "T1590.002",
      "T1591",
      "T1592.002",
      "T1595",
      "T1595.002",
      "T1595.003",
      "T1059.006",
      "T1190"
    ],
    "sample_id": "E1-col-ful-K05"
  },
  "input_events_sha256": "45be3de1fbc85e25f5e378620059ad4e858e4ac3092e9ed40a7c31d682ac9972",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E1.json",
    "model_file_sha256": "76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 108.0
  },
  "prediction_type": "technique",
  "record_id": "d7a92cd7407c66236a1778b007e59c08b75790fcbe34d85ffa186efbea30f90d",
  "record_sha256": "40e2c2cb9cf6f31fdce3ee384541a55a2cd051fccf5a2d034c05a226a11d0527",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1059.006, T1190] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1033 (System Owner/User Discovery) with estimated transition probability 1.0000 based on 0.33/0.33 transition weight across episodes [E7]. Support Context: Caution: low historical support (observed in 1 training episode(s) with 0.3 state transitions; caution threshold: < 2 episodes or < 3 transitions). Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1033",
        "candidate_name": "System Owner/User Discovery",
        "denominator": 0.3333333333333333,
        "name_source": "technique_tactic_reference.json",
        "numerator": 0.3333333333333333,
        "score": 1.0,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": true,
      "caution_text": "Caution: low historical support (observed in 1 training episode(s) with 0.3 state transitions; caution threshold: < 2 episodes or < 3 transitions).",
      "n_supporting_training_episodes": 1,
      "n_transitions_from_state": 0.3333333333333333
    },
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": false,
      "tied_candidates": []
    }
  }
}
```

---

## Exemplar: 7. Set-Valued State (`E1-col-ful-K08`)

- **Description**: Current attack state comprises multiple simultaneous techniques with uniform 1/|S| weighting.
- **Record ID**: `e3b508ba4edeab61ea5711498a7879ac9432275b563164e679289433bff280f4`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `d93a25eaf32390f0ac499317dfc225b715b4b3b65a156c15ceaffa73c9dea509`
- **Record SHA-256**: `0fef9468a8a71e4c84d694d468ee3e5c21d3149f18abdc1073d429635f4441d0`
- **Current State**: Techniques=`['T1007', 'T1016', 'T1033', 'T1049', 'T1057', 'T1069', 'T1082', 'T1083', 'T1087', 'T1201', 'T1518', 'T1614', 'T1615']`, Tactics=`['discovery']`
- **Model Status**: `ok`
- **Support Metrics**: Supporting Episodes=4, Transitions from State=14.00, Caution=False

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes | Tactics (Display) |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|:---|
| 1 | `T1057` | Process Discovery | 0.2083 | `transition_probability` | 3.00 | 11.58 | [E2, E7] | Discovery |
| 2 | `T1016` | System Network Configuration Discovery | 0.1667 | `transition_probability` | 2.00 | 11.58 | [E2, E7] | Discovery |
| 3 | `T1105` | Ingress Tool Transfer | 0.1458 | `transition_probability` | 1.33 | 11.58 | [E2, E6] | Command and Control |

### Alternative Candidates (Ranks 4..k)

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 4 | `T1003` | OS Credential Dumping | 0.0769 | `transition_probability` | 1.00 | 11.58 | [E2] |
| 5 | `T1003.008` | /etc/passwd and /etc/shadow | 0.0705 | `transition_probability` | 2.00 | 11.58 | [E2, E7] |
| 6 | `T1041` | Exfiltration Over C2 Channel | 0.0321 | `transition_probability` | 1.00 | 11.58 | [E2, E7] |
| 7 | `T1007` | System Service Discovery | 0.0256 | `transition_probability` | 1.00 | 11.58 | [E2] |
| 8 | `T1059.004` | Unix Shell | 0.0256 | `transition_probability` | 1.00 | 11.58 | [E3] |

### Deterministic Explanation

> State [T1007, T1016, T1033, T1049, T1057, T1069, T1082, T1083, T1087, T1201, T1518, T1614, T1615] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 (Process Discovery) with estimated transition probability 0.2083 based on 3.00/11.58 transition weight across episodes [E2, E7]. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).

### Full Canonical JSON Record

```json
{
  "input": {
    "affected_asset": null,
    "c3_fields": {
      "asset_criticality": null,
      "cti_confidence": null,
      "freshness": null,
      "investigation_priority": null,
      "ioc": null,
      "ioc_type": null,
      "threat_score": null
    },
    "current_tactic_set": [
      "discovery"
    ],
    "current_technique_set": [
      "T1007",
      "T1016",
      "T1033",
      "T1049",
      "T1057",
      "T1069",
      "T1082",
      "T1083",
      "T1087",
      "T1201",
      "T1518",
      "T1614",
      "T1615"
    ],
    "episode_id": "E1",
    "event_index": null,
    "incident_stage": null,
    "last_timestamp": "2025-09-22T13:55:56.594335+00:00",
    "previous_supporting_techniques": [
      "T1590.002",
      "T1591",
      "T1592.002",
      "T1595",
      "T1595.002",
      "T1595.003",
      "T1059.006",
      "T1190",
      "T1105",
      "T1059",
      "T1007",
      "T1016",
      "T1033",
      "T1049",
      "T1057",
      "T1069",
      "T1082",
      "T1083",
      "T1087",
      "T1201",
      "T1518",
      "T1614",
      "T1615"
    ],
    "sample_id": "E1-col-ful-K08"
  },
  "input_events_sha256": "d93a25eaf32390f0ac499317dfc225b715b4b3b65a156c15ceaffa73c9dea509",
  "model": {
    "model_file_relpath": "artifacts/7ep/fold_models/collapsed_full/E1.json",
    "model_file_sha256": "76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1",
    "model_type": "first_order_markov_with_frequency_fallback",
    "set_weighting_rule": "uniform_1_over_cardinality",
    "tie_break_rule": "lexicographical_ascending",
    "training_episodes": [
      "E2",
      "E3",
      "E4",
      "E5",
      "E6",
      "E7"
    ],
    "transition_count": 108.0
  },
  "prediction_type": "technique",
  "record_id": "e3b508ba4edeab61ea5711498a7879ac9432275b563164e679289433bff280f4",
  "record_sha256": "0fef9468a8a71e4c84d694d468ee3e5c21d3149f18abdc1073d429635f4441d0",
  "schema_version": "1.1.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [
      {
        "candidate_id": "T1003",
        "candidate_name": "OS Credential Dumping",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.07692307692307693,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Credential Access"
        ],
        "tactics": [
          "credential-access"
        ]
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.0,
        "score": 0.07051282051282051,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Credential Access"
        ],
        "tactics": [
          "credential-access"
        ]
      },
      {
        "candidate_id": "T1041",
        "candidate_name": "Exfiltration Over C2 Channel",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.03205128205128205,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Exfiltration"
        ],
        "tactics": [
          "exfiltration"
        ]
      },
      {
        "candidate_id": "T1007",
        "candidate_name": "System Service Discovery",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.02564102564102564,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": "Unix Shell",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.0,
        "score": 0.02564102564102564,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E3"
        ],
        "supporting_episodes_count": 1,
        "tactic_display": [
          "Execution"
        ],
        "tactics": [
          "execution"
        ]
      }
    ],
    "explanation": "State [T1007, T1016, T1033, T1049, T1057, T1069, T1082, T1083, T1087, T1201, T1518, T1614, T1615] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 (Process Discovery) with estimated transition probability 0.2083 based on 3.00/11.58 transition weight across episodes [E2, E7]. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": "/etc/passwd and /etc/shadow",
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline. (Support caution threshold: < 2 episodes or < 3 state transitions).",
      "coverage_rate": 0.6421052631578947,
      "frequency_hit3_pooled": 0.16842105263157894,
      "frequency_hit3_wilson95": [
        0.10641255003021141,
        0.25620308968543903
      ],
      "markov_hit3_pooled": 0.031578947368421054,
      "markov_hit3_wilson95": [
        0.010797139474424379,
        0.08877098647308188
      ],
      "metric": "Markov vs Frequency Hit@3",
      "sample_count": 95,
      "slice": "collapsed_full"
    },
    "ranked_candidates": [
      {
        "candidate_id": "T1057",
        "candidate_name": "Process Discovery",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 3.0,
        "score": 0.20833333333333331,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1016",
        "candidate_name": "System Network Configuration Discovery",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 2.0,
        "score": 0.16666666666666666,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Discovery"
        ],
        "tactics": [
          "discovery"
        ]
      },
      {
        "candidate_id": "T1105",
        "candidate_name": "Ingress Tool Transfer",
        "denominator": 11.583333333333332,
        "name_source": "technique_tactic_reference.json",
        "numerator": 1.3333333333333333,
        "score": 0.14583333333333334,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E2",
          "E6"
        ],
        "supporting_episodes_count": 2,
        "tactic_display": [
          "Command and Control"
        ],
        "tactics": [
          "command-and-control"
        ]
      }
    ],
    "status": "ok",
    "support": {
      "caution": false,
      "caution_text": null,
      "n_supporting_training_episodes": 4,
      "n_transitions_from_state": 14.0
    },
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": false,
      "tied_candidates": []
    }
  }
}
```

---

