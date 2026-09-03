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
        # 2026 NSE equity/derivatives trading holidays — weekday closures only.
        # Kept in sync with src/market_data/session/exchange_calendar.py and
        # src/broker/services/market_status_service.py. Movable-feast names are
        # indicative; the date is authoritative. (Aug 15 falls on a Saturday in
        # 2026 and is not a trading-day closure.)
        holidays = {
            datetime.date(2026, 1, 26),  # Republic Day
            datetime.date(2026, 3, 3),   # Holi
            datetime.date(2026, 3, 26),  # NSE trading holiday (movable feast)
            datetime.date(2026, 3, 31),  # Id-Ul-Fitr (Ramzan Id)
            datetime.date(2026, 4, 3),   # Good Friday
            datetime.date(2026, 4, 14),  # Dr. Baba Saheb Ambedkar Jayanti
            datetime.date(2026, 5, 1),   # Maharashtra Day
            datetime.date(2026, 5, 28),  # Bakri Id (Id-ul-Zuha)
            datetime.date(2026, 6, 26),  # Muharram
            datetime.date(2026, 9, 14),  # Ganesh Chaturthi
            datetime.date(2026, 10, 2),  # Mahatma Gandhi Jayanti
            datetime.date(2026, 10, 20), # Dussehra (Vijaya Dashami)
            datetime.date(2026, 11, 10), # Diwali - Laxmi Pujan
            datetime.date(2026, 11, 24), # Guru Nanak Jayanti
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
