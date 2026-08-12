# tests/test_sprint_d3_ui_session_story.py
from pathlib import Path
import pytest

MARKET_STORY_PATH = Path("src/frontend/components/MarketStory.tsx")
WORKSTATION_STATE_PATH = Path("src/application/workstation_state_service.py")


def read_file(path: Path) -> str:
    assert path.exists(), f"File {path} does not exist"
    return path.read_text(encoding="utf-8")


def test_market_story_ui_session_timeline_rendering():
    code = read_file(MARKET_STORY_PATH)
    assert "Today’s Analysis — NIFTY 50 Session Timeline" in code
    assert "session_story" in code
    assert "session_summary" in code
    assert "KEY_EVENTS" in code
    assert "FULL 15M" in code
    assert "major_turning_points" in code
    assert "session_verdict" in code
    assert "live_feed_latency_truth" in code


def test_market_story_telemetry_gap_and_attribution_rendering():
    code = read_file(MARKET_STORY_PATH)
    assert "TELEMETRY_GAP" in code
    assert "POSSIBLE_CATALYST" in code
    assert "OBSERVATION" in code
    assert "Temporal proximity alone does not establish causality" in code


def test_workstation_state_service_session_story_methods():
    code = read_file(WORKSTATION_STATE_PATH)
    assert "_derive_session_story" in code
    assert "_derive_latency_diagnostics" in code
    assert "live_feed_latency_truth" in code
    assert "session_story" in code
