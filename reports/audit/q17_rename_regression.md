# S2 Rename-Regression Incident & Prevention Report (T5)

> [!NOTE]
> Generated for Prompt 17 Part T5.
> Documents the root causes, affected modules, and automated gate mechanisms preventing rename regressions.

---

## 1. Executive Summary

During the Prompt 16 Part S2 reorganisation, root-level scripts in `scripts/*.py` were restructured into organized subsystems:
- `scripts/pipeline/`: Numbered end-to-end data processing stages (`s01_normalize_events.py` through `s20_build_overnight_summary.py`)
- `scripts/verify/`: Independent baseline and report verifiers (`verify_stage1_7ep.py`, `verify_e5_hit1_diagnostic.py`, `verify_viva_pack.py`, etc.)
- `scripts/audit/`: Audit tools, hash verifiers, and ledgers
- `scripts/dashboard/`: Streamlit dashboard and browser capture harnesses

While active runtime execution paths were updated, legacy fallback import constructs (`try: ... except ImportError: ...`) and lingering references pointing to root `scripts/` locations remained un-exercised during standard top-level runs but posed latent regression risks under alternate execution contexts and static analysis.

Part T5 implements an AST-level import integrity verifier (`scripts/audit/check_imports.py`) and incorporates it into the continuous regression gate suite (`tests/test_import_integrity.py`).

---

## 2. What the S2 Rename Broke

The AST parser identified four broken import references across three files:

| File | Line | Broken Import | Intended Target After S2 Rename |
|:---|:---:|:---|:---|
| `scripts/pipeline/s15_exploratory_tactic_conditioned.py` | 55 | `from scripts.run_tie_sensitivity_7ep import (...)` | `scripts/pipeline/s14_tie_sensitivity_7ep.py` |
| `tests/test_inference_7ep.py` | 212 | `from scripts.verify_e5_hit1_diagnostic import (...)` | `scripts/verify/verify_e5_hit1_diagnostic.py` |
| `tests/test_inference_7ep.py` | 221 | `from scripts.run_tie_sensitivity_7ep import (...)` | `scripts/pipeline/s14_tie_sensitivity_7ep.py` |
| `tests/test_viva_pack_sweep.py` | 15 | `from scripts.verify_viva_pack import (...)` | `scripts/verify/verify_viva_pack.py` |

### Failure Mechanism
In each case, authors had introduced defensive fallback imports:
```python
try:
    from scripts.verify.verify_viva_pack import verify_viva_pack
except ImportError:
    from scripts.verify_viva_pack import verify_viva_pack
```
Because `scripts/verify_viva_pack.py` had been permanently moved to `scripts/verify/verify_viva_pack.py`, the fallback branch was dead code pointing to a deleted file. If the primary import ever failed (e.g., due to an internal syntax error or circular dependency during module evaluation), the fallback would mask the true error and raise a secondary `ModuleNotFoundError: No module named 'scripts.verify_viva_pack'`. Furthermore, static analysis tools, linters, and AST parsers flagged these dangling imports as broken module dependencies.

---

## 3. What Now Prevents It

Three layers of defense now prevent any similar rename regression:

1. **AST-Based Import Integrity Verifier (`scripts/audit/check_imports.py`)**:
   - Parses the Abstract Syntax Tree (AST) of every Python file under `scripts/`, `src/`, and `tests/`.
   - Resolves all local `import` and `from ... import ...` statements (both absolute and relative) to physical files on disk.
   - Parses the target module's AST to verify that every imported function, class, or module-level variable actually exists within the target.
   - Detects dangling `try/except` fallbacks, obsolete module paths, and typos before any code is merged.

2. **Automated Regression Gate Integration (`tests/test_import_integrity.py`)**:
   - Invokes `check_all_imports()` as part of the primary `pytest` suite.
   - Any broken module reference or missing symbol causes immediate test failure, halting CI/CD and release pipelines.

3. **Codebase Clean-Up**:
   - Removed obsolete legacy fallback blocks across `s15_exploratory_tactic_conditioned.py`, `tests/test_inference_7ep.py`, and `tests/test_viva_pack_sweep.py`.
   - All modules now import directly from their canonical post-S2 subsystem paths.

---

## 4. Verification Output Summary

Execution of `scripts/audit/check_imports.py` (logged to `reports/audit/q17_T5_output.txt`):
- **Scanned Python Files**: 143
- **Checked Local Imports**: 172
- **Missing Modules**: 0
- **Missing Symbols**: 0
- **Gate Status**: **PASS**
