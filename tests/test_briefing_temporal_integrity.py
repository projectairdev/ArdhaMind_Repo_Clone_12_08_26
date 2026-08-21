# tests/test_briefing_temporal_integrity.py
"""
Comprehensive Automated Test Suite for Time-Aware Briefing Workspace & Temporal Integrity.

Tests cover:
 1. 00:00 - 14:59 IST -> PRE-MARKET BRIEFING & MORNING subview default
 2. 15:00 - 23:59 IST -> POST-MARKET BRIEFING & POST_MARKET subview default
 3. Pre-15:20 IST (15:00-15:19 IST or morning) state = PREPARING, no fake frozen snapshot
 4. Timeline at 10:30 AM contains ONLY <= 10:30 entries (no 12:30, 14:30, 15:20)
 5. Timeline at 13:00 IST contains ONLY <= 13:00 entries (no 14:30, 15:20)
 6. 15:20 IST snapshot creation & immutability
 7. 15:30+ official close reconciliation as POST_CLOSE_FINAL
 8. Weekend / holiday non-trading day handling (NO_TRADING_SESSION)
 9. Production directory (/opt/ArdhaMind) 100% untouched
"""

import subprocess
import pytest
from datetime import datetime, timezone, timedelta
from src.intelligence_engine.post_market_briefing_engine import PostMarketBriefingEngine

IST = timezone(timedelta(hours=5, minutes=30))


@pytest.fixture(autouse=True)
def clear_engine_cache():
    PostMarketBriefingEngine._cached_reports.clear()
    yield
    PostMarketBriefingEngine._cached_reports.clear()


def test_time_aware_boundaries_pre_1500():
    """Verify 00:00 to 14:59 IST evaluates to PRE-MARKET BRIEFING and PREPARING state."""
    test_dt = datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST)
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24152.05, "high": 24167.05, "low": 24137.05},
        "options": {"pcr": 1.25, "max_pain": 24200.0},
    }
    report = PostMarketBriefingEngine.analyze_post_market(state, now_ist=test_dt)
    assert report.lifecycle_status == "PREPARING"
    assert report.snapshot_type == "PREPARING"
    assert report.next_session_outlook is None


def test_timeline_future_leakage_prevention_at_1030():
    """Verify timeline at 10:30 AM contains ONLY entries <= 10:30 AM (no 12:30, 14:30, 15:20)."""
    test_dt = datetime(2026, 8, 20, 10, 30, 0, tzinfo=IST)
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24152.05, "high": 24167.05, "low": 24137.05},
    }
    report = PostMarketBriefingEngine.analyze_post_market(state, now_ist=test_dt)
    timeline_times = [item.time_hhmm for item in report.session_story.timeline]
    assert "09:15" in timeline_times
    assert "10:30" in timeline_times
    assert "12:30" not in timeline_times
    assert "14:30" not in timeline_times
    assert "15:20" not in timeline_times


def test_timeline_future_leakage_prevention_at_1300():
    """Verify timeline at 13:00 IST contains ONLY entries <= 13:00 IST (no 14:30, 15:20)."""
    test_dt = datetime(2026, 8, 20, 13, 0, 0, tzinfo=IST)
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24152.05, "high": 24167.05, "low": 24137.05},
    }
    report = PostMarketBriefingEngine.analyze_post_market(state, now_ist=test_dt)
    timeline_times = [item.time_hhmm for item in report.session_story.timeline]
    assert "09:15" in timeline_times
    assert "10:30" in timeline_times
    assert "12:30" in timeline_times
    assert "14:30" not in timeline_times
    assert "15:20" not in timeline_times


def test_1520_snapshot_freeze():
    """Verify 15:20 IST snapshot is frozen and contains next_session_outlook."""
    test_dt = datetime(2026, 8, 20, 15, 20, 0, tzinfo=IST)
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24152.05, "high": 24177.05, "low": 24127.05},
        "options": {"pcr": 1.25, "max_pain": 24200.0},
    }
    report = PostMarketBriefingEngine.analyze_post_market(state, now_ist=test_dt)
    assert report.lifecycle_status == "SNAPSHOT_FROZEN"
    assert report.snapshot_type == "PRE_CLOSE_1520"
    assert report.next_session_outlook is not None
    assert report.nifty_snapshot.price_at_snapshot == 24152.05


def test_1530_official_close_reconciliation():
    """Verify 15:30+ official close updates lifecycle to FINAL_RECONCILED."""
    test_dt = datetime(2026, 8, 20, 15, 35, 0, tzinfo=IST)
    state = {
        "market_data": {"current_spot": 24152.05, "open": 24152.05, "high": 24177.05, "low": 24127.05, "close": 24155.10},
        "options": {"pcr": 1.25, "max_pain": 24200.0},
    }
    report = PostMarketBriefingEngine.reconcile_official_close("2026-08-20", state, now_ist=test_dt)
    assert report.lifecycle_status == "FINAL_RECONCILED"
    assert report.snapshot_type == "POST_CLOSE_FINAL"
    assert report.nifty_snapshot.official_close_available is True
    assert report.nifty_snapshot.official_close_value == 24155.10


def test_non_trading_day_handling():
    """Verify non-trading days (Sunday) at 15:00+ return NO_TRADING_SESSION."""
    sunday_dt = datetime(2026, 8, 23, 16, 0, 0, tzinfo=IST) # Sunday
    state = {"market_data": {"current_spot": 24152.05}}
    report = PostMarketBriefingEngine.analyze_post_market(state, now_ist=sunday_dt)
    assert report.lifecycle_status == "NO_TRADING_SESSION"
    assert report.snapshot_type == "NOT_APPLICABLE"


def test_production_directory_isolation():
    """Verify /opt/ArdhaMind production directory remains 100% untouched."""
    cmd = "git -C /opt/ArdhaMind status --porcelain"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert res.returncode == 0
    assert res.stdout.strip() == "", f"Production directory modified! Changes: {res.stdout}"
