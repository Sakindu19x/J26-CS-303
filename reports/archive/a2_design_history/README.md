# A2 Design History Archive

These seven scratch scripts were used during the exploratory design phase of Planted-Structure Variant A2 (order-free / non-sequential baseline) prior to adopting the final pre-declared collapsed-sequence design.

## Important Notice
These scripts were **recovered verbatim from the agent conversation transcripts** (`conversation 5ab42197-3071-457f-b0f7-27258611f865`, transcript steps 352-376). They are preserved here purely for historical documentation, transparency, and auditability. They are **not** part of the verified production pipeline and are not executed during standard test or verification runs.

## Recovered Scripts
1. `test_a2_diff.py`: Evaluated LOEO with variant="collapsed" vs variant="raw" without applying `collapse_sequence()`.
2. `inspect_a2.py`: Diagnostic inspection of conditional transition probabilities for fold 1.
3. `test_a2_choices.py`: Compared `random.Random.choices` weighted sampling vs Bernoulli sampling.
4. `test_a2_proper.py`: Independent 8-episode generation per replicate across 20 seeds without collapsing.
5. `test_a2_dom.py`: Fixed dominant technique vs seed-rotating dominant technique.
6. `test_a2_collapsed.py`: Applied production `collapse_sequence()` to raw A2 sequences (resolved self-repeat artifact).
7. `test_all_gates.py`: Integration harness validating gates G1-G7 across A1, collapsed A2, A3, and negative control.
