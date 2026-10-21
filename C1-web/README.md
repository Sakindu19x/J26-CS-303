# Component 1: Adaptive Web Attack Detection & Correlation Model

Weerasinghe W.G.O.N · IT23378148 · Group J26-CS-303

Multi-label web attack detection (One-vs-Rest Logistic Regression, 13 CAPEC labels, SR-BH 2020) plus contextual correlation of the detected attacks.

## Folders

| Folder / file | What it is | Safe to move? |
| --- | --- | --- |
| `Dataset/` | Raw dataset `data_capec_multilabel.csv`; `processed/` = train/test splits (`.joblib`); `processed/readable/` = CSV samples to open in Excel | ❌ code reads it |
| `src/` | Detection code: `config.py` (all paths and settings), `data_preparation.py`, `model_pipeline.py`, `dataset_exploration.py` | ❌ |
| `notebooks/` | 01 exploration → 02 cleaning/split → 03 model → 04 live demo | ❌ |
| `models/` | Trained model + preprocessor (`.joblib`) used by every demo | ❌ |
| `results/` | Metrics CSVs and the PP1 → PP2 hand-off file `correlation_input.csv` | ❌ |
| `docs/` | Markdown summaries, design notes, proposal text | ❌ scripts write here |
| `Demo outputs/` | CSVs saved by notebook 04 | ❌ notebook 04 writes here |
| `log_parser/` | Apache/Nginx log parser (tested, **not connected to the model yet**) | ❌ |
| `PP2 - Starter/` | Correlation stage (events, similarity functions, tests; PP2 work) | ❌ |
| `References/` | Proposal docs, PP1 docs, research papers (+ highlighted copies) | ✅ |
| `References/Study Guides/` | Word/PDF study material: notebook walkthrough, demo script & answers, viva guide | ✅ |
| `demo/` | `demo_app.py` = main demo: `python -m streamlit run demo/demo_app.py` · `demo_app_full.py` = old, larger demo (backup) · `run_test_row.py` = terminal demo: `python demo/run_test_row.py 443732` | ❌ paths are set for this folder |

Hidden folders (created automatically, safe to ignore): `.claude` (Claude Code settings for starting the demo), `.pytest_cache` and `__pycache__` (Python caches; they come back whenever tests or code run).

Run everything from this `RA 1` folder.
