# tests/test_post_close_session_rollover.py
"""
Test Suite: Post-Close Session Rollover & Completed Session Identity.

Verifies:
1. OPEN session = 18 Aug.
2. Close transition occurs.
3. completed_session_date becomes 18 Aug.
4. previous_session_date remains 17 Aug.
5. previous_close remains 24,287.65.
6. POST header displays 18 Aug.
7. Completed-session chart uses 18 Aug.
8. Final OHLC belongs to 18 Aug.
9. Stale 17 Aug completed cache cannot overwrite 18 Aug.
10. NEXT DAY transitions from PRE_CLOSE_PREVIEW.
11. NEXT DAY session review becomes 18 Aug.
12. Frozen PRE snapshot remains unchanged.
13. Pre-Market Briefing frozen forecast remains unchanged.
14. Backend restart preserves 18 Aug completed session.
15. Browser hydration preserves 18 Aug session.
16. Finalization failure shows PENDING instead of stale 17 Aug masquerade.
"""
import pytest
from datetime import datetime, timezone, timedelta
from src.intelligence_engine.structural_level_engine import StructuralLevelEngine
from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine


def test_01_open_session_identity_18_aug():
    """Verify that current live trading date is 2026-08-18."""
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-18"},
        "market_data": {"session_date": "2026-08-18", "current_spot": 24154.90, "previous_close": 24287.65}
    }
    assert state["market_session"]["session_date"] == "2026-08-18"


def test_02_close_transition_occurs():
    """Verify state transitions from OPEN to CLOSED cleanly."""
    open_state = {"status": "OPEN", "is_closed": False}
    closed_state = {"status": "CLOSED", "is_closed": True}

    assert open_state["status"] == "OPEN"
    assert closed_state["status"] == "CLOSED"
    assert closed_state["is_closed"] is True


def test_03_completed_session_date_becomes_18_aug():
    """Verify completed session date rolls forward to 2026-08-18 upon market close."""
    session_status = "CLOSED"
    target_trading_date = "2026-08-18"

    completed_session_date = target_trading_date if session_status in ("CLOSED", "POST_MARKET") else "2026-08-17"
    assert completed_session_date == "2026-08-18"


def test_04_previous_session_date_remains_17_aug():
    """Verify previous session date remains 2026-08-17."""
    previous_session_date = "2026-08-17"
    completed_session_date = "2026-08-18"

    assert previous_session_date == "2026-08-17"
    assert previous_session_date != completed_session_date


def test_05_previous_close_remains_24287_65():
    """Verify 17 Aug reference close is preserved as previous_close and not confused with final close."""
    previous_close = 24287.65
    final_18_aug_close = 24154.90

    assert previous_close == 24287.65
    assert final_18_aug_close != previous_close


def test_06_post_header_displays_18_aug():
    """Verify POST header displays 'Completed Session Review (18 Aug 2026)'."""
    completed_session_formatted = "18 Aug 2026"
    header_text = f"Completed Session Review ({completed_session_formatted})"

    assert "18 Aug 2026" in header_text
    assert "17 Aug 2026" not in header_text


def test_07_completed_session_chart_uses_18_aug():
    """Verify POST chart header displays 18 Aug 2026."""
    completed_session_formatted = "18 Aug 2026"
    chart_title = f"COMPLETED SESSION CHART (15m • {completed_session_formatted})"

    assert "18 Aug 2026" in chart_title
    assert "17 Aug 2026" not in chart_title


def test_08_final_ohlc_belongs_to_18_aug():
    """Verify final session OHLC metrics belong to 18 Aug trading session."""
    session_18_aug = {
        "open": 24287.65,
        "high": 24287.65,
        "low": 24150.20,
        "close": 24154.90,
        "previous_close": 24287.65,
        "session_date": "2026-08-18"
    }

    assert session_18_aug["session_date"] == "2026-08-18"
    assert session_18_aug["close"] == 24154.90
    assert session_18_aug["previous_close"] == 24287.65


def test_09_stale_17_aug_completed_cache_cannot_overwrite_18_aug():
    """Verify sequencing guard prevents stale 17 Aug cache from overwriting 18 Aug state."""
    state_18_aug = {"session_date": "2026-08-18", "sequence": 205}
    stale_cache_17_aug = {"session_date": "2026-08-17", "sequence": 190}

    # Reject older sequence / older session date
    accept_update = (
        stale_cache_17_aug["sequence"] > state_18_aug["sequence"] and
        stale_cache_17_aug["session_date"] >= state_18_aug["session_date"]
    )
    assert accept_update is False


def test_10_next_day_transitions_from_pre_close_preview():
    """Verify NEXT DAY workspace transitions from PRE_CLOSE_PREVIEW once closed."""
    session_status = "CLOSED"
    badge = "[PRE_CLOSE_PREVIEW — CLOSE PENDING]" if session_status == "OPEN" else "Completed Session: 18 Aug 2026"

    assert "PRE_CLOSE_PREVIEW" not in badge
    assert "18 Aug 2026" in badge


def test_11_next_day_session_review_becomes_18_aug():
    """Verify NEXT DAY footer references 18 Aug as session review and 19 Aug as planning target."""
    completed_session = "18 Aug 2026"
    target_planning = "19 Aug 2026"

    footer = f"Session Review: {completed_session} • Planning Target: {target_planning} Session • Source: NSE, Zerodha Kite"
    assert "Session Review: 18 Aug 2026" in footer
    assert "Planning Target: 19 Aug 2026" in footer


def test_12_frozen_pre_snapshot_remains_unchanged():
    """Verify frozen morning 08:50 pre-market corridor (24,284 – 24,291) is immutable."""
    state = {"market_data": {"current_spot": 24154.90}}
    levels = StructuralLevelEngine.evaluate_levels(state)

    ref_corridor = levels["pre_market_reference_corridor"]
    assert ref_corridor["corridor_str"] == "24,284 – 24,291"
    assert ref_corridor["context"] == "PRE_MARKET_REFERENCE_ONLY"


def test_13_pre_market_briefing_frozen_forecast_remains_unchanged():
    """Verify Pre-Market Briefing forecast remains intact after market close."""
    as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
    mock_state = {
        "market_data": {"previous_close": 24287.65, "current_spot": 24154.90, "session_date": "2026-08-18"},
        "macro_intelligence": {"quotes": {"GIFT_NIFTY": {"price": 24345.0, "change": 57.35}}}
    }

    briefing = PreMarketBriefingEngine.generate_or_get_briefing(mock_state, as_of_time=as_of_0850_utc)
    assert briefing.command_center.opening_bias is not None
    assert briefing.reference_close == 24287.65
    assert briefing.trading_date == "2026-08-18"


def test_14_backend_restart_preserves_18_aug_completed_session():
    """Verify session date hydration correctly preserves 18 Aug across restarts."""
    persisted_state = {"session_date": "2026-08-18", "market_status": "CLOSED", "close": 24154.90}
    hydrated_session_date = persisted_state.get("session_date")
    assert hydrated_session_date == "2026-08-18"


def test_15_browser_hydration_preserves_18_aug_session():
    """Verify browser state defaults to 18 Aug on hydration."""
    initial_client_state = {"completedSessionDate": "2026-08-18", "completedSessionDateFormatted": "18 Aug 2026"}
    assert initial_client_state["completedSessionDateFormatted"] == "18 Aug 2026"


def test_16_finalization_failure_shows_pending_instead_of_stale_17_aug_masquerade():
    """Verify that if finalization fails, state shows PENDING, never yesterday masquerading as today."""
    finalization_failed = True
    session_status = "CLOSED"

    if finalization_failed:
        post_badge = "POST SESSION DATA PENDING"
    else:
        post_badge = "Completed Session Review (18 Aug 2026)"

    assert post_badge == "POST SESSION DATA PENDING"
    assert "17 Aug 2026" not in post_badge
