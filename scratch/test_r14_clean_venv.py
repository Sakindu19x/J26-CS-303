"""Test R14: Create a fresh temporary virtual environment, follow README instructions literally, run pipeline and pytest."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

temp_venv = Path("C:/Users/Lenovo/AppData/Local/Temp/c4_test_venv")
if temp_venv.exists():
    shutil.rmtree(temp_venv, ignore_errors=True)

print(f"Creating fresh venv at {temp_venv}...")
res = subprocess.run([sys.executable, "-m", "venv", str(temp_venv)], capture_output=True, text=True)
if res.returncode != 0:
    print(f"Failed to create venv: {res.stderr}")
    sys.exit(1)

py_bin = temp_venv / "Scripts" / "python.exe"
pip_bin = temp_venv / "Scripts" / "pip.exe"
pytest_bin = temp_venv / "Scripts" / "pytest.exe"

print(f"Python binary: {py_bin}")
assert py_bin.is_file(), f"Missing {py_bin}"

# 1. Install requirements.txt
print("\n--- Step 1: pip install -r requirements.txt ---")
res = subprocess.run([str(pip_bin), "install", "-r", "requirements.txt"], capture_output=True, text=True)
print(f"Exit code: {res.returncode}")
if res.returncode != 0:
    print(res.stderr)
    sys.exit(1)
else:
    print("requirements.txt installed successfully.")

# 2. Install editable package
print("\n--- Step 2: pip install -e . ---")
res = subprocess.run([str(pip_bin), "install", "-e", "."], capture_output=True, text=True)
print(f"Exit code: {res.returncode}")
if res.returncode != 0:
    print(res.stderr)
    sys.exit(1)
else:
    print("c4 package installed in editable mode successfully.")

# 3. Install pytest
print("\n--- Step 3: pip install pytest ---")
res = subprocess.run([str(pip_bin), "install", "pytest"], capture_output=True, text=True)
print(f"Exit code: {res.returncode}")
if res.returncode != 0:
    print(res.stderr)
    sys.exit(1)
else:
    print("pytest installed successfully.")

# 4. Run pipeline scripts in order
for script in [
    "scripts/run_normalization.py",
    "scripts/run_timeline_pipeline.py",
    "scripts/run_samples_and_stats.py",
]:
    print(f"\n--- Running: {script} ---")
    res = subprocess.run([str(py_bin), script], capture_output=True, text=True)
    print(f"Exit code: {res.returncode}")
    print(res.stdout.strip())
    if res.returncode != 0:
        print("STDERR:", res.stderr)
        sys.exit(1)

# 5. Run pytest -v
print("\n--- Step 5: pytest -v ---")
res = subprocess.run([str(pytest_bin), "-v"], capture_output=True, text=True)
print(f"Exit code: {res.returncode}")
print(res.stdout)
if res.returncode != 0:
    print("STDERR:", res.stderr)
    sys.exit(1)

print("\nSUCCESS: All README instructions executed cleanly in fresh virtual environment!")
