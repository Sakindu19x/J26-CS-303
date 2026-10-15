# Component 4 Forensic Next-Step Prediction: 10-Step Demonstration Script

> [!NOTE]
> This demonstration script guides an investigator, evaluator, or viva examiner through the end-to-end
> capabilities of the Component 4 Next-Step Attack Prediction Dashboard (FR6, FR7, FR9, NFR4, NFR6).

---

### Step 1: Launch the Prototype Dashboard
- Open a terminal in the repository root and start the dashboard interface:
  ```powershell
  ..\.venv\Scripts\streamlit.exe run src/c4/dashboard/prediction_app.py
  ```
- Verify the browser opens to the interactive C4 Investigation Dashboard.

### Step 2: Select an Episode Boundary
- In the sidebar episode selector, select **Episode 1 (E1 - Scenario 1 Sudo PAM)**.
- Note that all 19 chronological timeline events for E1 load instantly without cross-episode contamination (FR2).

### Step 3: Inspect the Chronological Forensic Timeline
- Review the main timeline panel. Confirm events display timestamp, host, MITRE ATT&CK techniques, and tactics.
- Observe that labeled attack actions and unlabeled system events are clearly delineated.

### Step 4: Focus on an Attack Step (Position Selector)
- Select sample position `E1-col-ful-K01` (Event step 1: `T1590.002`, `T1591` - Reconnaissance).
- Verify the **Next-Step Prediction Panel** updates dynamically for this exact state.

### Step 5: Examine Ranked Top-3 Candidate Predictions
- Locate the "Ranked Top-k Next-Step Candidates" table.
- Verify the top predicted technique (e.g. `T1589.002`) displays an estimated conditional transition probability with its official MITRE technique name and tactic category.

### Step 6: Verify Empirical Evidence Basis (FR5)
- Inspect the evidence columns for the top candidate.
- Confirm the display of the exact numerator and denominator transition counts (`numerator / denominator`) and the list of supporting training episodes.

### Step 7: Review Alternative Candidates and Tie Notices (FR6)
- Expand the **Alternative Candidates (Ranks 4+)** sub-panel.
- Confirm the presence of alternative candidates with their respective probability scores and the tie notice indicator ("No boundary ties" or "Tied boundary").

### Step 8: Inspect Upstream C3 Interface Fields (FR8)
- Review the **Component 3 Telemetry Context** section.
- Verify that C3 attributes (threat score, investigation priority, asset criticality, CTI confidence, freshness, IoC) are rendered explicitly as `"not provided by dataset"` for historical CAM-LDS events.

### Step 9: Evaluate the Empirical Reliability Banner (FR7)
- Locate the **Empirical Reliability Banner** at the base of the prediction panel.
- Confirm the display of pre-registered empirical benchmark figures: Markov vs Frequency Hit@3 alongside Wilson 95% confidence intervals and coverage percentage.

### Step 10: Review Cryptographic Provenance and Schema Validation (NFR2, NFR3, NFR6)
- Check the **Audit Metadata & Cryptographic Hashes** section.
- Confirm display of `record_id`, `model_file_sha256`, `input_events_sha256`, and `record_sha256`.
- Verify the green badge: `Schema Validation: 100% PASS (c4_prediction_record.schema.json)`.
