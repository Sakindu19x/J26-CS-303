# Component 2: Network Event Classification & Escalation Analysis (C2-network)

## Overview
Component 2 (C2) provides automated detection, prediction, and risk scoring from Windows host and network telemetry events:
- **Stage 1 (ATT&CK Technique Classification)**: A Random Forest model classifies events into MITRE ATT&CK technique IDs with prediction probabilities, top-3 candidates, and SHAP-based feature explanations.
- **Stage 2 (Next-Technique Prediction)**: A first-order Markov chain model predicts the top-3 most probable next attack techniques conditioned on observed technique sequences.
- **Stage 3 (Escalation Probability Analysis)**: Derives the probability that subsequent adversary actions escalate towards later MITRE ATT&CK tactics in the attack lifecycle.
- **C3 Interoperability & Handoff**: Serializes findings into standardized JSON and CSV handoff schemas (`c2_output.json`, `c2_output.csv`) consumed directly by Component 3 (CTI).

## Datasets
Datasets are external and not stored in this repository. Download them directly from their source repositories:
- **Windows-APT 2025**: [IEEE DataPort](https://dx.doi.org/10.21227/5g1d-2x47) / [GitHub Repository](https://github.com/d-g-e-o-r-g-e/Windows-APT-2025)
- **OTRF Security Datasets (Mordor)**: [OTRF Security Datasets GitHub](https://github.com/OTRF/Security-Datasets)

## Installation
Set up a Python virtual environment and install the required dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Pipeline
To execute the complete end-to-end pipeline and audit suite:
```bash
python run_all.py <dataset folder> <output folder>
```
*Note: `<dataset folder>` must contain `APT_C2_Detection_Dataset/` with `task_A_event_classification.csv` and `task_B_next_technique.csv`. `<output folder>` must not already exist.*
