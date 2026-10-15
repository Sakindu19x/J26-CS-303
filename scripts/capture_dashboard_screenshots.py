"""Capture headless browser screenshots of Dashboard Prediction Panels (P7)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from c4.dashboard.prediction_panel import (
    load_prediction_records_by_sample,
    render_prediction_panel_html,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MEASUREMENTS_DIR = REPO_ROOT / "reports" / "measurements"
SCRATCH_DIR = REPO_ROOT / "scratch"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def main() -> None:
    MEASUREMENTS_DIR.mkdir(parents=True, exist_ok=True)
    SCRATCH_DIR.mkdir(parents=True, exist_ok=True)

    records = load_prediction_records_by_sample()

    # Find representative samples
    first_hit = None
    first_unseen = None
    first_fallback = None
    first_tied = None
    first_tactic = None

    for sid, rec in records.items():
        ptype = rec["prediction_type"]
        p_obj = rec["technique_prediction"] if ptype == "technique" else rec["tactic_prediction"]
        status = p_obj["status"]
        tie_flags = p_obj.get("tie_flags", {})

        if ptype == "technique" and status == "ok" and first_hit is None:
            first_hit = rec
        if status == "unseen_state" and first_unseen is None:
            first_unseen = rec
        if status == "fallback" and first_fallback is None:
            first_fallback = rec
        if (tie_flags.get("tie_at_top1") or tie_flags.get("tie_at_top3_boundary")) and first_tied is None:
            first_tied = rec
        if ptype == "tactic" and first_tactic is None:
            first_tactic = rec

    targets = {
        "dashboard_prediction_panel.png": first_hit,
        "dashboard_unseen_state.png": first_unseen or first_fallback,
        "dashboard_tied_case.png": first_tied,
        "dashboard_tactic_prediction.png": first_tactic,
    }

    print("--- Capturing Dashboard Prediction Panel Screenshots ---")
    for filename, rec in targets.items():
        if rec is None:
            print(f"Skipping {filename}: no matching record found")
            continue

        sample_id = rec["input"]["sample_id"]
        html_content = render_prediction_panel_html(rec)
        temp_html_path = SCRATCH_DIR / f"{sample_id}.html"
        temp_html_path.write_text(html_content, encoding="utf-8")

        out_png_path = MEASUREMENTS_DIR / filename
        cmd = f'cmd.exe /c "\"{CHROME_PATH}\" --headless --disable-gpu --screenshot=\"{out_png_path}\" --window-size=1280,960 \"{temp_html_path.resolve()}\""'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)

        if out_png_path.is_file():
            size_kb = out_png_path.stat().st_size / 1024
            print(f"Captured {filename} ({sample_id}): {size_kb:.1f} KB")
        else:
            print(f"Failed to capture {filename}: returncode {res.returncode}, stderr: {res.stderr.strip()}")


if __name__ == "__main__":
    main()
