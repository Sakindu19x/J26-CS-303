"""test_dashboard_q8.py

Pytest suite for Prompt 14 Q8 Dashboard deliverables:
- scripts/run_dashboard.ps1 launcher specification
- docs/demo_script.md launch documentation
- reports/measurements/dashboard_capture_log.txt
- High-fidelity static renders (*_static_render.png)
- AppTest automated verification
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_run_dashboard_ps1_spec():
    """Verify run_dashboard.ps1 exists and defines both prediction and timeline apps."""
    ps1_path = REPO_ROOT / "scripts" / "dashboard" / "run_dashboard.ps1"
    if not ps1_path.is_file():
        ps1_path = REPO_ROOT / "scripts" / "run_dashboard.ps1"
    assert ps1_path.is_file(), f"Missing launcher at {ps1_path}"
    content = ps1_path.read_text(encoding="utf-8")
    assert "PYTHONPATH" in content
    assert "src\\c4\\dashboard\\prediction_app.py" in content or "src/c4/dashboard/prediction_app.py" in content
    assert "src\\c4\\dashboard\\app.py" in content or "src/c4/dashboard/app.py" in content
    assert "8501" in content
    assert "8502" in content


def test_demo_script_launch_and_render_docs():
    """Verify demo_script.md contains How to Launch and static render designations."""
    demo_path = REPO_ROOT / "docs" / "demo_script.md"
    assert demo_path.is_file()
    content = demo_path.read_text(encoding="utf-8")
    assert "How to Launch" in content
    assert "run_dashboard.ps1 -App prediction" in content
    assert "run_dashboard.ps1 -App timeline" in content
    assert "static renders" in content.lower()
    assert "dashboard_prediction_panel_static_render.png" in content
    assert "dashboard_unseen_state_static_render.png" in content
    assert "dashboard_tied_case_static_render.png" in content
    assert "dashboard_tactic_prediction_static_render.png" in content


def test_dashboard_capture_log_content():
    """Verify dashboard_capture_log.txt documents live server start and capture method."""
    log_path = REPO_ROOT / "reports" / "measurements" / "dashboard_capture_log.txt"
    assert log_path.is_file()
    content = log_path.read_text(encoding="utf-8")
    assert "Server Launch Command" in content
    assert "Health Check Passed" in content
    assert "LIVE CAPTURE LIMITATION DETECTED" in content
    assert "AppTest" in content
    assert "Statistical Support Caution" in content
    assert "Candidate Tactics" in content
    assert "Boundary Tie Status" in content


def test_static_renders_exist_and_valid():
    """Verify that all 4 static render files exist, have substantial size, and valid PNG headers."""
    render_files = [
        "dashboard_prediction_panel_static_render.png",
        "dashboard_unseen_state_static_render.png",
        "dashboard_tied_case_static_render.png",
        "dashboard_tactic_prediction_static_render.png",
    ]
    png_magic = b"\x89PNG\r\n\x1a\n"

    for r_name in render_files:
        r_path = REPO_ROOT / "reports" / "measurements" / r_name
        assert r_path.is_file(), f"Missing render {r_name}"
        data = r_path.read_bytes()
        assert data[:8] == png_magic, f"{r_name} does not have valid PNG header"
        assert len(data) > 50_000, f"{r_name} size ({len(data)} bytes) is too small"


def test_apptest_prediction_app_renders_cleanly():
    """Verify prediction_app renders cleanly via streamlit AppTest."""
    from streamlit.testing.v1 import AppTest

    app_path = REPO_ROOT / "src" / "c4" / "dashboard" / "prediction_app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30)
    at.run()
    assert not at.exception, f"AppTest raised exception: {at.exception}"
