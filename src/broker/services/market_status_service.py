from __future__ import annotations
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, time as dt_time
from typing import Optional, List

logger = logging.getLogger("MarketStatusService")

# NSE equity/derivatives trading holidays for 2026 — weekday closures only.
# Reconciled against the official 2026 exchange holiday circular and kept in sync
# with src/market_data/session/exchange_calendar.py::DEFAULT_NSE_HOLIDAYS.
# (Aug 15 / Independence Day is a Saturday in 2026, so it is not a trading-day
# closure and is intentionally absent.) Movable-feast names are indicative.
HOLIDAYS_2026 = {
    "2026-01-26",  # Republic Day
    "2026-03-03",  # Holi
    "2026-03-26",  # NSE trading holiday (movable feast)
    "2026-03-31",  # Id-Ul-Fitr (Ramzan Id)
    "2026-04-03",  # Good Friday
    "2026-04-14",  # Dr. Baba Saheb Ambedkar Jayanti
    "2026-05-01",  # Maharashtra Day
    "2026-05-28",  # Bakri Id (Id-ul-Zuha)
    "2026-06-26",  # Muharram
    "2026-09-14",  # Ganesh Chaturthi
    "2026-10-02",  # Mahatma Gandhi Jayanti
    "2026-10-20",  # Dussehra (Vijaya Dashami)
    "2026-11-10",  # Diwali - Laxmi Pujan
    "2026-11-24",  # Guru Nanak Jayanti
    "2026-12-25",  # Christmas
}

@dataclass(frozen=True)
class MarketStatusReport:
    status: str  # "OPEN", "CLOSED", "PRE_OPEN", "POST_CLOSE"
    is_trading_day: bool
    is_holiday: bool
    remaining_seconds: float
    next_session_start: str
    next_session_date: str = ""
    timezone: str = "Asia/Kolkata"
    current_time_ist: str = ""
    calendar_verified: bool = True

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "is_trading_day": self.is_trading_day,
            "is_holiday": self.is_holiday,
            "remaining_seconds": self.remaining_seconds,
            "next_session_start": self.next_session_start,
            "next_session_date": self.next_session_date,
            "timezone": self.timezone,
            "current_time_ist": self.current_time_ist,
            "calendar_verified": self.calendar_verified
        }

class MarketStatusService:
    """
    Determines Indian stock exchange (NSE/NFO) market status, timezone handling, trading sessions,
    holidays, remaining session time, and next session start.
    """
    _instance: Optional[MarketStatusService] = None

    @classmethod
    def get_instance(cls) -> MarketStatusService:
        if cls._instance is None:
            cls._instance = MarketStatusService()
        return cls._instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MarketStatusService, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def get_ist_time(current_utc: Optional[datetime] = None) -> datetime:
        """Converts UTC or Local time to Asia/Kolkata (IST: UTC + 5 hours 30 mins) time."""
        if current_utc is None:
            current_utc = datetime.utcnow()
        elif current_utc.tzinfo is not None:
            current_utc = current_utc.astimezone(timezone.utc).replace(tzinfo=None)
        # Explicitly calculate IST offset (UTC + 5:30)
        ist_offset = timedelta(hours=5, minutes=30)
        return current_utc + ist_offset

    def is_holiday(self, date_val: datetime) -> bool:
        """Checks if a given date is a weekend or an exchange holiday."""
        # Weekend Check
        if date_val.weekday() in (5, 6):  # Saturday=5, Sunday=6
            return True
        # Holiday Check
        date_str = date_val.strftime("%Y-%m-%d")
        return date_str in HOLIDAYS_2026

    def get_market_status(self, current_utc: Optional[datetime] = None) -> MarketStatusReport:
        """
        Determines current market status, remaining session time, and details about the next session.
        """
        ist_now = self.get_ist_time(current_utc)
        current_time_ist_str = ist_now.strftime("%Y-%m-%d %H:%M:%S")
        is_h = self.is_holiday(ist_now)
        is_trading = not is_h

        # Session Boundary Times (IST)
        pre_market_start = dt_time(8, 45, 0)
        pre_open_start = dt_time(9, 0, 0)
        pre_open_end = dt_time(9, 15, 0)
        market_start = dt_time(9, 15, 0)
        market_end = dt_time(15, 30, 0)
        post_close_end = dt_time(16, 0, 0)

        now_time = ist_now.time()
        date_str = ist_now.strftime("%Y-%m-%d")

        # Special Sessions in 2026 (e.g. disaster recovery Saturday sessions)
        special_sessions = {
            "2026-05-02": (dt_time(9, 15, 0), dt_time(10, 0, 0)),
        }

        status = "CLOSED"
        remaining_seconds = 0.0

        if date_str in special_sessions:
            start_t, end_t = special_sessions[date_str]
            if start_t <= now_time < end_t:
                status = "SPECIAL_SESSION"
                target = datetime.combine(ist_now.date(), end_t)
                remaining_seconds = (target - ist_now).total_seconds()
            else:
                status = "CLOSED"
        elif is_h:
            status = "HOLIDAY"
        else:
            if now_time < pre_market_start:
                status = "EARLY_IDLE"
                target = datetime.combine(ist_now.date(), pre_market_start)
                remaining_seconds = (target - ist_now).total_seconds()
            elif pre_market_start <= now_time < pre_open_start:
                status = "PRE_MARKET"
                target = datetime.combine(ist_now.date(), pre_open_start)
                remaining_seconds = (target - ist_now).total_seconds()
            elif pre_open_start <= now_time < pre_open_end:
                status = "PRE_OPEN"
                target = datetime.combine(ist_now.date(), pre_open_end)
                remaining_seconds = (target - ist_now).total_seconds()
            elif market_start <= now_time < market_end:
                status = "OPEN"
                target = datetime.combine(ist_now.date(), market_end)
                remaining_seconds = (target - ist_now).total_seconds()
            elif market_end <= now_time < post_close_end:
                status = "POST_CLOSE"
                target = datetime.combine(ist_now.date(), post_close_end)
                remaining_seconds = (target - ist_now).total_seconds()
            else:
                status = "CLOSED"

        # Calculate Next Session Start
        next_session_dt = ist_now
        while True:
            # Move to next day first or stay if pre-market today
            if next_session_dt == ist_now:
                if is_trading and now_time < pre_open_start:
                    next_session_dt = datetime.combine(ist_now.date(), market_start)
                    break
                else:
                    next_session_dt = next_session_dt + timedelta(days=1)
            else:
                next_session_dt = next_session_dt + timedelta(days=1)

            if not self.is_holiday(next_session_dt):
                next_session_dt = datetime.combine(next_session_dt.date(), market_start)
                break

        next_session_start_str = next_session_dt.strftime("%Y-%m-%d %H:%M:%S")
        next_session_date_str = next_session_dt.strftime("%Y-%m-%d")

        return MarketStatusReport(
            status=status,
            is_trading_day=is_trading,
            is_holiday=is_h,
            remaining_seconds=remaining_seconds,
            next_session_start=next_session_start_str,
            next_session_date=next_session_date_str,
            current_time_ist=current_time_ist_str,
            calendar_verified=next_session_dt.year <= 2026
        )
