"""Live Dashboard Screenshot Capture Script using Playwright in separate venv (Prompt 15 R4(d)).

Rules:
- Uses channel="chrome" (system installed Chrome).
- Never downloads browsers.
- Drives real app on port 8501 (spawned via ..\.venv\Scripts\python.exe).
- Saves reports/measurements/live_*.png and logs results.
- If it fails, logs the exact error and leaves static renders intact.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEASUREMENTS_DIR = REPO_ROOT / "reports" / "measurements"
LOG_PATH = MEASUREMENTS_DIR / "live_capture_log.txt"

APP_PY = REPO_ROOT / "src" / "c4" / "dashboard" / "prediction_app.py"
MAIN_PYTHON = REPO_ROOT.parent / ".venv" / "Scripts" / "python.exe"


def log(msg: str) -> None:
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def wait_for_server(port: int = 8501, timeout: float = 30.0) -> bool:
    url = f"http://localhost:{port}/_stcore/health"
    start = time.perf_counter()
    while time.perf_counter() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def run_live_capture() -> int:
    LOG_PATH.write_text(f"=== LIVE DASHBOARD CAPTURE LOG (Prompt 15 R4(d)) ===\n{time.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n", encoding="utf-8")
    log("[1] Starting Streamlit prediction app on port 8501...")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    cmd = [
        str(MAIN_PYTHON),
        "-m",
        "streamlit",
        "run",
        str(APP_PY),
        "--server.port",
        "8501",
        "--server.headless",
        "true",
    ]

    server_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log(f"    Streamlit PID: {server_proc.pid}")

    try:
        ready = wait_for_server(port=8501, timeout=30.0)
        if not ready:
            log("[-] Streamlit server failed to respond on http://localhost:8501/_stcore/health within 30s.")
            return 1

        log("[+] Streamlit server is healthy and responding.")

        log("[2] Launching Playwright with channel='chrome'...")
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)
            context = browser.new_context(viewport={"width": 1400, "height": 1100})
            page = context.new_page()

            log("    Navigating to http://localhost:8501...")
            page.goto("http://localhost:8501", timeout=30000)
            page.wait_for_load_state("networkidle")
            time.sleep(3.0)

            # Click tab "4. Next-Step Prediction (FR6-FR9)"
            log("    Selecting Tab 4: Next-Step Prediction...")
            import re
            tab4 = page.get_by_role("tab", name=re.compile(r"Next-Step Prediction"))
            if tab4.count() > 0:
                tab4.first.click()
                time.sleep(2.0)
            else:
                log("    Tab 4 not found by role; searching by text...")
                page.locator("text=Next-Step Prediction").first.click()
                time.sleep(2.0)

            samples_to_capture = [
                ("E1-col-ful-K01", MEASUREMENTS_DIR / "live_prediction_panel.png", "Standard active Markov transition"),
                ("E1-col-ful-K03", MEASUREMENTS_DIR / "live_unseen_state.png", "Frequency fallback on unseen state"),
                ("E1-col-ful-K02", MEASUREMENTS_DIR / "live_tied_case.png", "Tied rank case"),
                ("E1-tac-col-K01", MEASUREMENTS_DIR / "live_tactic_prediction.png", "Tactic-level prediction"),
            ]

            for sid, out_path, desc in samples_to_capture:
                log(f"[3] Selecting sample '{sid}' ({desc})...")
                # Find the sample selectbox input in Tab 4
                sb_input = page.locator("div[data-testid='stSelectbox']:has-text('Select Prediction Sample') input")
                if sb_input.count() > 0:
                    sb_input.first.click()
                    time.sleep(0.3)
                    sb_input.first.fill(sid)
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(2.5)
                    log(f"    Selected {sid} via input fill + Enter.")
                else:
                    log("    Sample selectbox input locator not found.")

                page.screenshot(path=str(out_path), full_page=True)
                log(f"    [OK] Captured live screenshot to {out_path.name} ({out_path.stat().st_size} bytes)")

            browser.close()
            log("\n[+] LIVE CAPTURE COMPLETED SUCCESSFULLY.")
            return 0

    except Exception as exc:
        log(f"\n[-] LIVE CAPTURE ENCOUNTERED ERROR: {type(exc).__name__}: {exc}")
        import traceback
        log(traceback.format_exc())
        log("Keeping static renders only as primary visual artifacts.")
        return 1
    finally:
        log("[4] Terminating Streamlit server process...")
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            server_proc.kill()
        log("    Streamlit server terminated cleanly.")


if __name__ == "__main__":
    code = run_live_capture()
    sys.exit(code)
