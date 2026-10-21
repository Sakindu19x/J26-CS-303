# C2 -> C3 interface (schema_version 1.0)

C2 delivers one record per event, ordered by session and time. Files: `c2_output.csv` (flat) and `c2_output.json` (nested). Keys are identical in both.

| Field | Type | Meaning |
|---|---|---|
| schema_version | string | Format version, currently "1.0" |
| event_id | string | Source record id of the event |
| scenario_id, session_id | string | Attack scenario and session. The dataset has no host column; `host_or_session` repeats `session_id` |
| source_dataset | string | Windows-APT-2025 or OTRF |
| timestamp, sequence_position | string, int | Event time and its position in the session |
| detected_technique | string or empty | MITRE ATT&CK technique ID predicted by Stage 1. Composite IDs such as `T1059.003;T1574.001` are one class. Empty = event not flagged |
| tactics | string | ATT&CK tactic(s) of the detected technique (`;`-separated in CSV) |
| classification_probability | 0-1 | Stage 1 probability of the predicted technique |
| malicious_probability | 0-1 | Stage 1 probability that the event is malicious |
| observed_sequence | string | Up to the last 10 detected techniques in the session, ` > `-separated, ending with this event's technique |
| next_1..next_3, next_k_prob | string, 0-1 | Top-3 next techniques from the first-order Markov model with transition probabilities |
| escalation_probability | 0-1 | Probability that the next technique belongs to a later ATT&CK tactic |
| state_seen_in_training | bool | False = no transition history for this technique; the prediction fell back to overall frequency |
| explanation_top5 / explanation_top_features | text / list | The five Stage 1 features with the largest SHAP value for the predicted technique |

Rules for C3: an event that is not flagged has empty detection and prediction fields - treat it as "no detection", not as zero. Probabilities are model scores; their calibration was only checked on Windows-APT. OTRF predictions are unreliable (see report) - filter on `source_dataset` if needed. Do not use `scenario_id` as a model input.

Example record (JSON, sequence shortened):

```json
{
 "schema_version": "1.0",
 "event_id": "waSxuZMBXkk7zdQZ990U",
 "scenario_id": "APT2025-2024.12.12",
 "session_id": "APT2025-2024.12.12-Host",
 "host_or_session": "APT2025-2024.12.12-Host",
 "source_dataset": "Windows-APT-2025",
 "timestamp": "2024-12-12 07:06:28.593",
 "sequence_position": 1,
 "detection": {
  "technique_id": "T1087",
  "tactics": [
   "Discovery"
  ],
  "classification_probability": 0.9818,
  "malicious_probability": 1.0,
  "alternatives": [
   {
    "technique_id": "T1059.003;T1574.001",
    "probability": 0.012
   },
   {
    "technique_id": "T1087;T1059.001",
    "probability": 0.0047
   }
  ],
  "explanation_top_features": [
   {
    "feature": "image_is_syswow64",
    "shap_value": 0.12719
   },
   {
    "feature": "image_is_system32",
    "shap_value": 0.10454
   },
   {
    "feature": "is_system_user",
    "shap_value": 0.10304
   },
   {
    "feature": "parent_image_basename_cmd.exe",
    "shap_value": 0.07419
   },
   {
    "feature": "cmd_length",
    "shap_value": 0.07121
   }
  ]
 },
 "observed_sequence": [
  "T1087"
 ],
 "prediction": {
  "next_techniques": [
   {
    "technique_id": "T1201",
    "probability": 0.461,
    "training_transition_count": 1375
   },
   {
    "technique_id": "T1087.001",
    "probability": 0.3216,
    "training_transition_count": 959
   },
   {
    "technique_id": "T1069.001",
    "probability": 0.1374,
    "training_transition_count": 409
   }
  ],
  "escalation_probability": 0.0425,
  "state_seen_in_training": true,
  "state_training_total": 2974,
  "model": "first-order Markov",
  "alpha": 1.0
 }
}
```
