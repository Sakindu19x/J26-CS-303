"""scripts/audit/check_imports.py

AST-based import integrity verifier (Prompt 17 Part T5).
Parses every Python file under scripts/, src/, and tests/.
Verifies that:
1. Every imported local module/package resolves to a real file on disk.
2. Every imported function, class, or symbol exists in the target module.
Exits 0 if all clean; exits 1 if any broken or dangling import is detected.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

SEARCH_ROOTS = [
    REPO_ROOT,
    REPO_ROOT / "src",
    REPO_ROOT / "scripts",
    REPO_ROOT / "tests",
]

LOCAL_PREFIXES = ("c4", "src", "scripts", "tests")


def find_local_module_file(mod_name: str, current_file: Path) -> Path | None:
    parts = mod_name.split(".")
    # 1. Check relative to current file's directory
    cand = current_file.parent / (os.sep.join(parts) + ".py")
    if cand.is_file():
        return cand
    cand = current_file.parent / os.sep.join(parts) / "__init__.py"
    if cand.is_file():
        return cand

    # 2. Check in search roots
    for root in SEARCH_ROOTS:
        cand = root / (os.sep.join(parts) + ".py")
        if cand.is_file():
            return cand
        cand = root / os.sep.join(parts) / "__init__.py"
        if cand.is_file():
            return cand

    return None


def get_module_symbols(mod_path: Path) -> set[str]:
    try:
        content = mod_path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(mod_path))
    except Exception:
        return set()

    symbols = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            symbols.add(elt.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            symbols.add(node.target.id)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                symbols.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                symbols.add(alias.asname or alias.name)

    return symbols


def is_local_import(mod_name: str | None, level: int, current_file: Path) -> bool:
    if level > 0:
        return True
    if not mod_name:
        return False
    first = mod_name.split(".")[0]
    if first in LOCAL_PREFIXES:
        return True
    # If it resolves to a local file in any search root, treat as local
    return find_local_module_file(mod_name, current_file) is not None


def check_all_imports() -> int:
    print("=" * 80)
    print("RUNNING AST RENAME-REGRESSION IMPORT INTEGRITY CHECK (T5)")
    print("=" * 80)

    py_files = sorted(
        list(REPO_ROOT.glob("scripts/**/*.py"))
        + list(REPO_ROOT.glob("src/**/*.py"))
        + list(REPO_ROOT.glob("tests/**/*.py"))
    )

    total_files = len(py_files)
    total_imports = 0
    missing_modules: list[tuple[str, str, int]] = []
    missing_symbols: list[tuple[str, str, str, str, int]] = []

    for pf in py_files:
        try:
            tree = ast.parse(pf.read_text(encoding="utf-8"), filename=str(pf))
        except Exception as exc:
            missing_modules.append((str(pf.relative_to(REPO_ROOT)), f"SyntaxError: {exc}", 1))
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name
                    if is_local_import(mod, 0, pf):
                        total_imports += 1
                        mf = find_local_module_file(mod, pf)
                        if not mf:
                            missing_modules.append((str(pf.relative_to(REPO_ROOT)), mod, getattr(node, "lineno", 0)))

            elif isinstance(node, ast.ImportFrom):
                mod = node.module
                level = node.level
                if is_local_import(mod, level, pf):
                    total_imports += 1
                    # Resolve relative module name if level > 0
                    if level > 0:
                        rel_parts = pf.relative_to(REPO_ROOT).parent.parts
                        if level <= len(rel_parts):
                            base_parts = rel_parts[: len(rel_parts) - level + 1]
                            resolved_mod = ".".join(base_parts + (tuple(mod.split(".")) if mod else ()))
                        else:
                            resolved_mod = mod or ""
                    else:
                        resolved_mod = mod or ""

                    mf = find_local_module_file(resolved_mod, pf)
                    if not mf:
                        missing_modules.append((str(pf.relative_to(REPO_ROOT)), resolved_mod, getattr(node, "lineno", 0)))
                    else:
                        syms = get_module_symbols(mf)
                        for alias in node.names:
                            sym = alias.name
                            if sym == "*":
                                continue
                            # Check if sym is a submodule in the package directory
                            sub_mod = mf.parent / f"{sym}.py" if mf.name == "__init__.py" else None
                            sub_dir = mf.parent / sym / "__init__.py" if mf.name == "__init__.py" else None
                            if sym not in syms and not (sub_mod and sub_mod.is_file()) and not (sub_dir and sub_dir.is_file()):
                                missing_symbols.append((
                                    str(pf.relative_to(REPO_ROOT)),
                                    resolved_mod,
                                    sym,
                                    str(mf.relative_to(REPO_ROOT)),
                                    getattr(node, "lineno", 0),
                                ))

    print(f"Scanned Python Files : {total_files}")
    print(f"Checked Local Imports: {total_imports}")
    print(f"Missing Modules      : {len(missing_modules)}")
    print(f"Missing Symbols      : {len(missing_symbols)}")

    if missing_modules or missing_symbols:
        print("\n[FAIL] Broken local imports detected:")
        for f, mod, lineno in missing_modules:
            print(f"  - {f}:{lineno}: Missing module `{mod}`")
        for f, mod, sym, target, lineno in missing_symbols:
            print(f"  - {f}:{lineno}: Symbol `{sym}` not found in `{mod}` ({target})")
        print("\n" + "=" * 80)
        print("GATE STATUS: FAIL")
        print("=" * 80)
        return 1

    print("\n[PASS] All local imports and symbols verified clean.")
    print("=" * 80)
    print("GATE STATUS: PASS")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(check_all_imports())
