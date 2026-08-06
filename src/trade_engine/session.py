from __future__ import annotations

import datetime
from typing import Optional, Set
from src.models.trade_context import SessionContext


def analyze_session(
    dt: Optional[datetime.datetime] = None,
    holidays: Optional[Set[datetime.date]] = None,
    half_days: Optional[Set[datetime.date]] = None,
) -> SessionContext:
    """
    Deterministic session analysis for NIFTY based on trading hours.
    """
    if dt is None:
        dt = datetime.datetime.now()

    time_str = dt.strftime("%H:%M:%S")
    date_val = dt.date()

    if holidays is None:
        # Default market holidays for 2026
        holidays = {
            datetime.date(2026, 1, 26),  # Republic Day
            datetime.date(2026, 3, 6),   # Holi (approx)
            datetime.date(2026, 4, 3),   # Good Friday
            datetime.date(2026, 5, 1),   # Maharashtra Day
            datetime.date(2026, 8, 15),  # Independence Day
            datetime.date(2026, 10, 2),  # Gandhi Jayanti
            datetime.date(2026, 12, 25), # Christmas
        }

    if half_days is None:
        half_days = {
            datetime.date(2026, 11, 8),  # Mock Muhurat Trading or similar half day
        }

    is_weekend = dt.weekday() >= 5
    is_holiday = date_val in holidays
    is_half_day = date_val in half_days

    if is_weekend:
        session_type = "WEEKEND"
        is_tradable = False
    elif is_holiday:
        session_type = "HOLIDAY"
        is_tradable = False
    else:
        hour = dt.hour
        minute = dt.minute
        now_minutes = hour * 60 + minute

        # Standard NIFTY trading hours: 09:15 to 15:30 IST
        market_open_mins = 9 * 60 + 15
        market_close_mins = 15 * 60 + 30

        if is_half_day:
            # Half-day hours are typically 09:15 to 11:30 IST
            half_day_close_mins = 11 * 60 + 30
            if market_open_mins <= now_minutes <= half_day_close_mins:
                session_type = "HALF_DAY"
                is_tradable = True
            else:
                session_type = "POST_MARKET"
                is_tradable = False
        else:
            if now_minutes < market_open_mins or now_minutes > market_close_mins:
                session_type = "POST_MARKET"
                is_tradable = False
            else:
                is_tradable = True
                if market_open_mins <= now_minutes < (9 * 60 + 30):
                    session_type = "MARKET_OPEN"
                elif (9 * 60 + 30) <= now_minutes < (11 * 60 + 30):
                    session_type = "MORNING"
                elif (11 * 60 + 30) <= now_minutes < (13 * 60 + 30):
                    session_type = "MID_SESSION"
                elif (13 * 60 + 30) <= now_minutes < (15 * 60):
                    session_type = "AFTERNOON"
                else:
                    session_type = "CLOSING_SESSION"

    return SessionContext(
        session_type=session_type,
        is_tradable_time=is_tradable,
        time_of_day=time_str,
        is_weekend=is_weekend,
        is_holiday=is_holiday,
        is_half_day=is_half_day,
    )
