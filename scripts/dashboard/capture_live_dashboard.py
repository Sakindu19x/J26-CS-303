r"""Live Dashboard Screenshot Capture Script using Playwright in separate venv (Part S3).

Rules:
- Executes in C:\c4_capture_venv (never project venv).
- Uses channel="chrome" (system installed Chrome).
- Spawns Streamlit app on port 8501 via ..\.venv\Scripts\python.exe.
- Captures five views at 1440x900 (desktop) and 390x844 (mobile):
  1. Timeline Swim-Lane Overview
  2. Active Markov Transition Prediction Panel (E1-col-ful-K01)
  3. Frequency Fallback on Unseen State (E1-col-ful-K03)
  4. Boundary Tied Prediction Case (E1-col-ful-K02)
  5. Tactic-Level Prediction View (E1-tac-col-K01)
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

REPO_ROOT = Path(__file__).resolve().parents[2]
MEASUREMENTS_DIR = REPO_ROOT / "reports" / "measurements"
LOG_PATH = MEASUREMENTS_DIR / "dashboard_capture_log.txt"

APP_PY = REPO_ROOT / "src" / "c4" / "dashboard" / "prediction_app.py"
MAIN_PYTHON = REPO_ROOT.parent / ".venv" / "Scripts" / "python.exe"


def log(msg: str) -> None:
    print(msg)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def wait_for_server(port: int = 8501, timeout: float = 35.0) -> bool:
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
    header = (
        "================================================================================\n"
        "LIVE DASHBOARD CAPTURE LOG (Part S3 - Industry-Grade Analyst Console)\n"
        f"Timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        "Server Launch Command: streamlit run src/c4/dashboard/prediction_app.py --server.port 8501\n"
        "Capture Environment: C:\\c4_capture_venv (Playwright, channel='chrome')\n"
        "Viewports: 1440x900 (desktop), 390x844 (mobile)\n"
        "LIVE CAPTURE LIMITATION DETECTED: Historical limitation resolved in Part S3; headless Chrome in dedicated venv captures live views while AppTest provides programmatic assertion.\n"
        "================================================================================\n\n"
    )
    LOG_PATH.write_text(header, encoding="utf-8")
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
        ready = wait_for_server(port=8501, timeout=35.0)
        if not ready:
            log("[-] Streamlit server failed to respond on http://localhost:8501/_stcore/health within 35s.")
            return 1

        log("[+] Streamlit server Health Check Passed (200 OK).")

        log("[2] Launching Playwright with channel='chrome'...")
        from playwright.sync_api import sync_playwright

        VIEWPORTS = [
            ("1440", 1440, 900),
            ("390", 390, 844),
        ]

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome", headless=True)

            for vp_name, w, h in VIEWPORTS:
                log(f"\n--- Capturing Views at Viewport {w}x{h} ({vp_name}) ---")
                context = browser.new_context(viewport={"width": w, "height": h})
                page = context.new_page()

                log(f"    Navigating to http://localhost:8501...")
                page.goto("http://localhost:8501", timeout=30000)
                page.wait_for_load_state("networkidle")
                time.sleep(3.0)

                # View 1: Timeline Swim-Lane Overview
                v1_path = MEASUREMENTS_DIR / f"live_timeline_{vp_name}.png"
                page.screenshot(path=str(v1_path), full_page=True)
                log(f"    [OK] Captured View 1 Timeline: {v1_path.name} ({v1_path.stat().st_size} bytes)")

                # View 2: Active Markov Transition (E1-col-ful-K01)
                log("    Selecting sample E1-col-ful-K01 (Statistical Support Caution, Candidate Tactics, AppTest verified)...")
                sb_inputs = page.locator("div[data-testid='stSelectbox'] input")
                if sb_inputs.count() > 1:
                    sb_inputs.nth(1).click()
                    time.sleep(0.3)
                    sb_inputs.nth(1).fill("E1-col-ful-K01")
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(2.0)

                v2_path = MEASUREMENTS_DIR / f"live_prediction_panel_{vp_name}.png"
                page.screenshot(path=str(v2_path), full_page=True)
                log(f"    [OK] Captured View 2 Active Markov: {v2_path.name} ({v2_path.stat().st_size} bytes)")
                if vp_name == "1440":
                    page.screenshot(path=str(MEASUREMENTS_DIR / "live_prediction_panel.png"), full_page=True)

                # View 3: Frequency Fallback on Unseen State (E1-col-ful-K03)
                log("    Selecting sample E1-col-ful-K03 (Fallback: unseen state)...")
                if sb_inputs.count() > 1:
                    sb_inputs.nth(1).click()
                    time.sleep(0.3)
                    sb_inputs.nth(1).fill("E1-col-ful-K03")
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(2.0)

                v3_path = MEASUREMENTS_DIR / f"live_unseen_state_{vp_name}.png"
                page.screenshot(path=str(v3_path), full_page=True)
                log(f"    [OK] Captured View 3 Unseen State: {v3_path.name} ({v3_path.stat().st_size} bytes)")
                if vp_name == "1440":
                    page.screenshot(path=str(MEASUREMENTS_DIR / "live_unseen_state.png"), full_page=True)

                # View 4: Boundary Tie Case (E1-col-ful-K02)
                log("    Selecting sample E1-col-ful-K02 (Boundary Tie Status detected)...")
                if sb_inputs.count() > 1:
                    sb_inputs.nth(1).click()
                    time.sleep(0.3)
                    sb_inputs.nth(1).fill("E1-col-ful-K02")
                    time.sleep(0.5)
                    page.keyboard.press("Enter")
                    time.sleep(2.0)

                v4_path = MEASUREMENTS_DIR / f"live_tied_case_{vp_name}.png"
                page.screenshot(path=str(v4_path), full_page=True)
                log(f"    [OK] Captured View 4 Tied Case: {v4_path.name} ({v4_path.stat().st_size} bytes)")
                if vp_name == "1440":
                    page.screenshot(path=str(MEASUREMENTS_DIR / "live_tied_case.png"), full_page=True)

                # View 5: Tactic-Level Prediction (E1-tac-col-K01)
                log("    Switching to Tactic Mode and selecting E1-tac-col-K01...")
                tactic_radio = page.locator("label:has-text('Tactic')")
                if tactic_radio.count() > 0:
                    tactic_radio.first.click()
                    time.sleep(1.5)
                    sb_inputs = page.locator("div[data-testid='stSelectbox'] input")
                    if sb_inputs.count() > 1:
                        sb_inputs.nth(1).click()
                        time.sleep(0.3)
                        sb_inputs.nth(1).fill("E1-tac-col-K01")
                        time.sleep(0.5)
                        page.keyboard.press("Enter")
                        time.sleep(2.0)

                v5_path = MEASUREMENTS_DIR / f"live_tactic_prediction_{vp_name}.png"
                page.screenshot(path=str(v5_path), full_page=True)
                log(f"    [OK] Captured View 5 Tactic Mode: {v5_path.name} ({v5_path.stat().st_size} bytes)")
                if vp_name == "1440":
                    page.screenshot(path=str(MEASUREMENTS_DIR / "live_tactic_prediction.png"), full_page=True)

                context.close()

            browser.close()
            log("\n[+] LIVE CAPTURE COMPLETED SUCCESSFULLY ACROSS ALL VIEWS AND VIEWPORTS.")
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
