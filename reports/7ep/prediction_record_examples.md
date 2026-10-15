# Explainable Prediction Record Worked Examples (7 Episodes)

> [!NOTE]
> This report presents five full, worked, representative prediction records generated
> by Component 4 under Leave-One-Episode-Out (LOEO) evaluation across 7 episodes.
> Every record conforms to `schemas/c4_prediction_record.schema.json` and satisfies
> requirements FR4 (candidate ranking), FR5 (evidence support), FR6 (explainability surface),
> FR7 (confidence scoring and reliability context), NFR2 (reproducibility), NFR3 (provenance),
> and NFR6 (schema compliance).

## Summary of Exemplars

| Exemplar Type | Sample ID | Episode | Level | Status | Top-1 Candidate | Top-1 Score | Score Type |
|:---|:---|:---:|:---:|:---:|:---|:---:|:---|
| 1. First Hit | `E2-col-ful-K05` | E2 | technique | `ok` | `T1057` | 0.4815 | `transition_probability` |
| 2. First Miss | `E1-col-ful-K01` | E1 | technique | `ok` | `T1589.002` | 1.0000 | `transition_probability` |
| 3. First Fallback | `E1-col-ful-K03` | E1 | technique | `fallback` | `T1105` | 0.0714 | `training_frequency_share` |
| 4. First Unseen State | `E1-col-ful-K03` | E1 | technique | `fallback` | `T1105` | 0.0714 | `training_frequency_share` |
| 5. First Tied Boundary | `E1-col-ful-K02` | E1 | technique | `ok` | `T1071.001` | 0.5000 | `transition_probability` |

## Exemplar: 1. First Hit (`E2-col-ful-K05`)

- **Record ID**: `e819e9c1f3ea725441586bd27b0b17b0a2843577be416f660acc6618bcb21a05`
- **Episode**: E2
- **Prediction Level**: technique
- **Model SHA-256**: `3823a1d7a319bc0e2c00aeb9f657b283666a76f35d04d6981a03d8eb8e24b892`
- **Input Events SHA-256**: `c0d116b9f5e9f000b2aa4a660bebfe4394fafe44a737db67c8b2b0d14d888023`
- **Record SHA-256**: `0384175ad1ff253d80ae1fd8b639c85235855e910b43d327877744ecca04302d`
- **Current State**: `['T1083']` (Tactics: `['Discovery']`)
- **Model Status**: `ok`

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 1 | `T1057` | None | 0.4815 | `transition_probability` | 1.00 | 2.08 | [E7] |
| 2 | `T1059.004` | None | 0.4815 | `transition_probability` | 1.00 | 2.08 | [E3] |
| 3 | `T1033` | None | 0.0370 | `transition_probability` | 0.08 | 2.08 | [E1] |

### Deterministic Explanation

> State [T1083] recognized in training episodes (E1, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 with estimated transition probability 0.4815 based on 1.00/2.08 transition weight across episodes [E7]. Notice: Top-1 boundary is tied among candidates: ['T1057', 'T1059.004']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.

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
      "Discovery"
    ],
    "current_technique_set": [
      "T1083"
    ],
    "episode_id": "E2",
    "event_index": 5,
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
  "record_id": "e819e9c1f3ea725441586bd27b0b17b0a2843577be416f660acc6618bcb21a05",
  "record_sha256": "0384175ad1ff253d80ae1fd8b639c85235855e910b43d327877744ecca04302d",
  "schema_version": "1.0.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1083] recognized in training episodes (E1, E3, E4, E5, E6, E7). Top next-technique prediction is T1057 with estimated transition probability 0.4815 based on 1.00/2.08 transition weight across episodes [E7]. Notice: Top-1 boundary is tied among candidates: ['T1057', 'T1059.004']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": null,
        "score": 0.07456140350877193
      },
      {
        "candidate_id": "T1033",
        "candidate_name": null,
        "score": 0.053643724696356275
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "score": 0.03289473684210526
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
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
        "candidate_name": null,
        "denominator": 2.0769230769230766,
        "numerator": 1.0,
        "score": 0.48148148148148145,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": null,
        "denominator": 2.0769230769230766,
        "numerator": 1.0,
        "score": 0.48148148148148145,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E3"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      },
      {
        "candidate_id": "T1033",
        "candidate_name": null,
        "denominator": 2.0769230769230766,
        "numerator": 0.07692307692307693,
        "score": 0.037037037037037035,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E1"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      }
    ],
    "status": "ok",
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

- **Record ID**: `95d5f7d31cc45469cf8eecef4ca7608c116d1af301a274a27fa54f68d7adc0ca`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `9a770d3be96e6fcaa88bf3b11889b3df03104553f3227367ee4b8c3a967f67ea`
- **Record SHA-256**: `730b7d3099277233a03c30b9338170d60fa466fc0d7ade5977b5607d12068e45`
- **Current State**: `['T1590.002', 'T1591']` (Tactics: `['Reconnaissance']`)
- **Model Status**: `ok`

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 1 | `T1589.002` | None | 1.0000 | `transition_probability` | 1.00 | 1.00 | [E7] |

### Deterministic Explanation

> State [T1590.002, T1591] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1589.002 with estimated transition probability 1.0000 based on 1.00/1.00 transition weight across episodes [E7]. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.

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
      "Reconnaissance"
    ],
    "current_technique_set": [
      "T1590.002",
      "T1591"
    ],
    "episode_id": "E1",
    "event_index": 1,
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
  "record_id": "95d5f7d31cc45469cf8eecef4ca7608c116d1af301a274a27fa54f68d7adc0ca",
  "record_sha256": "730b7d3099277233a03c30b9338170d60fa466fc0d7ade5977b5607d12068e45",
  "schema_version": "1.0.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1590.002, T1591] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1589.002 with estimated transition probability 1.0000 based on 1.00/1.00 transition weight across episodes [E7]. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": null,
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
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
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 1.0,
        "score": 1.0,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      }
    ],
    "status": "ok",
    "tie_flags": {
      "tie_at_top1": false,
      "tie_at_top3_boundary": false,
      "tied_candidates": []
    }
  }
}
```

---

## Exemplar: 3. First Fallback (`E1-col-ful-K03`)

- **Record ID**: `5488ce56922c4d09707b0b3c944b1ce0209c0bc0e9c0d081e806c1f2c84ad14d`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `ec5bfeda049ea7a6356dc0b4df036554ad41c221af955ced8abf5f400db4d5f5`
- **Record SHA-256**: `c73411d81ed22408f2803d980f07789f7aed048f1c31c876f892d540a5f95929`
- **Current State**: `['T1595.002']` (Tactics: `['Reconnaissance']`)
- **Model Status**: `fallback`

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 1 | `T1105` | None | 0.0714 | `training_frequency_share` | 5.50 | 77.00 | [E2, E3, E4, E6] |
| 2 | `T1003.008` | None | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E3, E7] |
| 3 | `T1057` | None | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E7] |

### Deterministic Explanation

> State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.

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
      "Reconnaissance"
    ],
    "current_technique_set": [
      "T1595.002"
    ],
    "episode_id": "E1",
    "event_index": 3,
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
  "record_id": "5488ce56922c4d09707b0b3c944b1ce0209c0bc0e9c0d081e806c1f2c84ad14d",
  "record_sha256": "c73411d81ed22408f2803d980f07789f7aed048f1c31c876f892d540a5f95929",
  "schema_version": "1.0.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [
      {
        "candidate_id": "T1083",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.030303030303030304,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1078.003",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.0303030303030303,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1016",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1041",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      }
    ],
    "explanation": "State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": null,
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
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
        "candidate_name": null,
        "denominator": 77.0,
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
        "tactics": []
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "denominator": 77.0,
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E3",
          "E7"
        ],
        "supporting_episodes_count": 3,
        "tactics": []
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "denominator": 77.0,
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactics": []
      }
    ],
    "status": "fallback",
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

## Exemplar: 4. First Unseen State (`E1-col-ful-K03`)

- **Record ID**: `5488ce56922c4d09707b0b3c944b1ce0209c0bc0e9c0d081e806c1f2c84ad14d`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `ec5bfeda049ea7a6356dc0b4df036554ad41c221af955ced8abf5f400db4d5f5`
- **Record SHA-256**: `c73411d81ed22408f2803d980f07789f7aed048f1c31c876f892d540a5f95929`
- **Current State**: `['T1595.002']` (Tactics: `['Reconnaissance']`)
- **Model Status**: `fallback`

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 1 | `T1105` | None | 0.0714 | `training_frequency_share` | 5.50 | 77.00 | [E2, E3, E4, E6] |
| 2 | `T1003.008` | None | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E3, E7] |
| 3 | `T1057` | None | 0.0390 | `training_frequency_share` | 3.00 | 77.00 | [E2, E7] |

### Deterministic Explanation

> State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.

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
      "Reconnaissance"
    ],
    "current_technique_set": [
      "T1595.002"
    ],
    "episode_id": "E1",
    "event_index": 3,
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
  "record_id": "5488ce56922c4d09707b0b3c944b1ce0209c0bc0e9c0d081e806c1f2c84ad14d",
  "record_sha256": "c73411d81ed22408f2803d980f07789f7aed048f1c31c876f892d540a5f95929",
  "schema_version": "1.0.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [
      {
        "candidate_id": "T1083",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1059.004",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.030303030303030304,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1078.003",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.0303030303030303,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1016",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      },
      {
        "candidate_id": "T1041",
        "candidate_name": null,
        "denominator": 1.0,
        "numerator": 0.0,
        "score": 0.025974025974025976,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [],
        "supporting_episodes_count": 0,
        "tactics": []
      }
    ],
    "explanation": "State [T1595.002] was not observed in training episodes (E2, E3, E4, E5, E6, E7) (zero outgoing transitions observed). Model fell back to unconditional training frequency baseline. Top candidate is T1105 with training frequency share 0.0714. Note: this score is an unconditional empirical frequency share, not a conditional transition probability. Notice: Top-3 rank boundary is tied with alternative candidates: ['T1057', 'T1083']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": null,
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
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
        "candidate_name": null,
        "denominator": 77.0,
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
        "tactics": []
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "denominator": 77.0,
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E3",
          "E7"
        ],
        "supporting_episodes_count": 3,
        "tactics": []
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "denominator": 77.0,
        "numerator": 3.0,
        "score": 0.03896103896103896,
        "score_type": "training_frequency_share",
        "supporting_episode_ids": [
          "E2",
          "E7"
        ],
        "supporting_episodes_count": 2,
        "tactics": []
      }
    ],
    "status": "fallback",
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

## Exemplar: 5. First Tied Boundary (`E1-col-ful-K02`)

- **Record ID**: `56c46e2d20eea18796b0582da4a6ddaa8a7bb469f4ec4258ff26ffeee4d5eb76`
- **Episode**: E1
- **Prediction Level**: technique
- **Model SHA-256**: `76d8568da1f7b2d8faa73c822d6b81d32c23e657b341252f84219deb4ce64ea1`
- **Input Events SHA-256**: `fccbaf4fc2989e6e9c644aba313bdf28a556a509bf945c3c8d146ee8540257d4`
- **Record SHA-256**: `f018474cc48f616929b587f8b4e5a854e18f37a38b11bc7209e21f51ea718511`
- **Current State**: `['T1592.002', 'T1595']` (Tactics: `['Reconnaissance']`)
- **Model Status**: `ok`

### Ranked Top Candidates

| Rank | Candidate | Name | Score | Score Type | Numerator | Denominator | Supporting Episodes |
|:---:|:---|:---|:---:|:---|:---:|:---:|:---|
| 1 | `T1071.001` | None | 0.5000 | `transition_probability` | 0.50 | 0.50 | [E7] |
| 2 | `T1573.001` | None | 0.5000 | `transition_probability` | 0.50 | 0.50 | [E7] |

### Deterministic Explanation

> State [T1592.002, T1595] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1071.001 with estimated transition probability 0.5000 based on 0.50/0.50 transition weight across episodes [E7]. Notice: Top-1 boundary is tied among candidates: ['T1071.001', 'T1573.001']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.

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
      "Reconnaissance"
    ],
    "current_technique_set": [
      "T1592.002",
      "T1595"
    ],
    "episode_id": "E1",
    "event_index": 2,
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
  "record_id": "56c46e2d20eea18796b0582da4a6ddaa8a7bb469f4ec4258ff26ffeee4d5eb76",
  "record_sha256": "f018474cc48f616929b587f8b4e5a854e18f37a38b11bc7209e21f51ea718511",
  "schema_version": "1.0.0",
  "tactic_prediction": null,
  "technique_prediction": {
    "alternatives": [],
    "explanation": "State [T1592.002, T1595] recognized in training episodes (E2, E3, E4, E5, E6, E7). Top next-technique prediction is T1071.001 with estimated transition probability 0.5000 based on 0.50/0.50 transition weight across episodes [E7]. Notice: Top-1 boundary is tied among candidates: ['T1071.001', 'T1573.001']. Empirical Reliability Context: Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
    "frequency_baseline_candidates": [
      {
        "candidate_id": "T1105",
        "candidate_name": null,
        "score": 0.07142857142857142
      },
      {
        "candidate_id": "T1003.008",
        "candidate_name": null,
        "score": 0.03896103896103896
      },
      {
        "candidate_id": "T1057",
        "candidate_name": null,
        "score": 0.03896103896103896
      }
    ],
    "measured_reliability_banner": {
      "banner_text": "Technique Level (collapsed_full, N=95): Markov Hit@3 3.16% [1.08%, 8.88%] vs Frequency 16.84% [10.64%, 25.62%]; Coverage 64.21%. Markov does not outperform baseline.",
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
        "candidate_name": null,
        "denominator": 0.5,
        "numerator": 0.5,
        "score": 0.5,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      },
      {
        "candidate_id": "T1573.001",
        "candidate_name": null,
        "denominator": 0.5,
        "numerator": 0.5,
        "score": 0.5,
        "score_type": "transition_probability",
        "supporting_episode_ids": [
          "E7"
        ],
        "supporting_episodes_count": 1,
        "tactics": []
      }
    ],
    "status": "ok",
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

