from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest

from src.market_data.session.exchange_calendar import ExchangeCalendar
from src.market_data.session.session_authority import (
    CanonicalSessionAuthority,
    MarketPhase,
    SessionContext,
)

IST = ZoneInfo("Asia/Kolkata")


def test_1_friday_to_monday_transition():
    calendar = ExchangeCalendar()
    friday = date(2026, 8, 28)
    saturday = date(2026, 8, 29)
    sunday = date(2026, 8, 30)
    monday = date(2026, 8, 31)

    assert calendar.is_trading_day(friday) is True
    assert calendar.is_trading_day(saturday) is False
    assert calendar.is_trading_day(sunday) is False
    assert calendar.is_trading_day(monday) is True

    assert calendar.get_next_trading_date(friday) == monday
    assert calendar.get_previous_trading_date(monday) == friday


def test_2_saturday_completed_session_resolves_to_friday_not_thursday():
    """
    CRITICAL HISTORICAL DEFECT REGRESSION TEST:
    On Saturday after Friday close, completed_session_date MUST resolve to Friday, NOT Thursday.
    """
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)

    # Saturday morning 10:00 AM IST
    sat_morning = datetime(2026, 8, 29, 10, 0, 0, tzinfo=IST)
    ctx = authority.evaluate_session(sat_morning)

    assert ctx.is_trading_day is False
    assert ctx.market_phase == MarketPhase.MARKET_CLOSED
    assert ctx.active_trading_date is None
    # Must be Friday 2026-08-28, NOT Thursday 2026-08-27!
    assert ctx.completed_session_date == date(2026, 8, 28)
    assert ctx.previous_session_date == date(2026, 8, 27)
    assert ctx.next_trading_date == date(2026, 8, 31)


def test_3_holiday_monday_transition():
    calendar = ExchangeCalendar()
    # 2026-01-26 is Republic Day (Monday Holiday)
    fri = date(2026, 1, 23)
    sat = date(2026, 1, 24)
    sun = date(2026, 1, 25)
    mon_hol = date(2026, 1, 26)
    tue = date(2026, 1, 27)

    assert calendar.is_trading_day(mon_hol) is False
    assert calendar.get_next_trading_date(fri) == tue
    assert calendar.get_previous_trading_date(tue) == fri
    assert calendar.get_previous_trading_date(mon_hol) == fri


def test_4_month_and_year_boundary():
    calendar = ExchangeCalendar()
    # Year boundary: 2025-12-31 (Wed) -> 2026-01-01 (Thu)
    d_dec31 = date(2025, 12, 31)
    d_jan01 = date(2026, 1, 1)
    assert calendar.get_next_trading_date(d_dec31) == d_jan01
    assert calendar.get_previous_trading_date(d_jan01) == d_dec31


def test_5_special_session_override():
    calendar = ExchangeCalendar()
    # Special Saturday disaster recovery trading session
    sat_special = date(2026, 9, 12)
    assert calendar.is_trading_day(sat_special) is False

    calendar.add_special_trading_days([sat_special])
    assert calendar.is_trading_day(sat_special) is True
    assert calendar.get_next_trading_date(date(2026, 9, 11)) == sat_special


def test_6_market_phase_resolution_during_trading_day():
    authority = CanonicalSessionAuthority()
    fri = date(2026, 8, 28)

    # 1. Pre-market: 08:30 IST
    t_pre_mkt = datetime(2026, 8, 28, 8, 30, 0, tzinfo=IST)
    ctx1 = authority.evaluate_session(t_pre_mkt)
    assert ctx1.market_phase == MarketPhase.PRE_MARKET
    assert ctx1.active_trading_date == fri
    assert ctx1.completed_session_date == date(2026, 8, 27)

    # 2. Pre-open: 09:05 IST
    t_pre_open = datetime(2026, 8, 28, 9, 5, 0, tzinfo=IST)
    ctx2 = authority.evaluate_session(t_pre_open)
    assert ctx2.market_phase == MarketPhase.PRE_OPEN
    assert ctx2.active_trading_date == fri

    # 3. Continuous Trading: 10:30 IST
    t_open = datetime(2026, 8, 28, 10, 30, 0, tzinfo=IST)
    ctx3 = authority.evaluate_session(t_open)
    assert ctx3.market_phase == MarketPhase.MARKET_OPEN
    assert ctx3.active_trading_date == fri
    assert authority.is_session_active(t_open) is True

    # 4. Post-market: 15:45 IST
    t_post = datetime(2026, 8, 28, 15, 45, 0, tzinfo=IST)
    ctx4 = authority.evaluate_session(t_post)
    assert ctx4.market_phase == MarketPhase.POST_MARKET
    assert ctx4.completed_session_date == fri  # Today is now completed

    # 5. Night Closed: 19:00 IST
    t_night = datetime(2026, 8, 28, 19, 0, 0, tzinfo=IST)
    ctx5 = authority.evaluate_session(t_night)
    assert ctx5.market_phase == MarketPhase.MARKET_CLOSED
    assert ctx5.completed_session_date == fri
    assert ctx5.next_trading_date == date(2026, 8, 31)


def test_7_session_dates_agreement_invariant():
    """
    Ensures that calendar date, active trading date, and completed date
    maintain logical invariant relationships with zero discrepancy.
    """
    authority = CanonicalSessionAuthority()

    # Midday Friday 14:00 IST
    midday = datetime(2026, 8, 28, 14, 0, 0, tzinfo=IST)
    ctx = authority.evaluate_session(midday)

    assert ctx.calendar_date == date(2026, 8, 28)
    assert ctx.active_trading_date == date(2026, 8, 28)
    assert ctx.completed_session_date == date(2026, 8, 27)
    assert ctx.previous_session_date == date(2026, 8, 26)
    assert ctx.next_trading_date == date(2026, 8, 31)
