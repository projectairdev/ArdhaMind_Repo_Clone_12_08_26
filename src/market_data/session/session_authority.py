from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from enum import Enum
import threading
from typing import Optional
from zoneinfo import ZoneInfo

from src.market_data.session.exchange_calendar import ExchangeCalendar

IST_TZ = ZoneInfo("Asia/Kolkata")


class MarketPhase(str, Enum):
    PRE_MARKET = "PRE_MARKET"        # 00:00 - 09:00 IST on trading days
    PRE_OPEN = "PRE_OPEN"            # 09:00 - 09:15 IST
    MARKET_OPEN = "MARKET_OPEN"      # 09:15 - 15:30 IST (Regular continuous trading)
    POST_MARKET = "POST_MARKET"      # 15:30 - 16:00 IST (Closing settlement / staging)
    MARKET_CLOSED = "MARKET_CLOSED"  # 16:00 - 24:00 IST, weekends, and holidays


@dataclass(frozen=True)
class SessionContext:
    """Immutable snapshot of the canonical session state at a specific observation time."""
    calendar_date: date
    is_trading_day: bool
    market_phase: MarketPhase
    active_trading_date: Optional[date]
    completed_session_date: date
    previous_session_date: date
    next_trading_date: date
    session_open_time: time
    session_close_time: time
    observed_at: datetime


class CanonicalSessionAuthority:
    """
    Single authoritative provider-independent session and trading date engine for Ardha.
    Computes market phases, active session dates, and completed session dates strictly in IST.
    """

    DEFAULT_PRE_OPEN_TIME: time = time(9, 0)
    DEFAULT_SESSION_OPEN_TIME: time = time(9, 15)
    DEFAULT_SESSION_CLOSE_TIME: time = time(15, 30)
    DEFAULT_POST_MARKET_END_TIME: time = time(16, 0)

    def __init__(
        self,
        exchange_calendar: Optional[ExchangeCalendar] = None,
        session_open_time: time = DEFAULT_SESSION_OPEN_TIME,
        session_close_time: time = DEFAULT_SESSION_CLOSE_TIME,
    ) -> None:
        self.calendar = exchange_calendar or ExchangeCalendar()
        self.session_open_time = session_open_time
        self.session_close_time = session_close_time
        self._lock = threading.RLock()

    def get_ist_now(self, override_time: Optional[datetime] = None) -> datetime:
        """Returns current time in Asia/Kolkata timezone."""
        if override_time is not None:
            if override_time.tzinfo is None:
                return override_time.replace(tzinfo=timezone.utc).astimezone(IST_TZ)
            return override_time.astimezone(IST_TZ)
        return datetime.now(IST_TZ)

    def evaluate_session(self, current_time: Optional[datetime] = None) -> SessionContext:
        """
        Evaluates the authoritative market phase, active trading date,
        and completed session date for the given timestamp (or current IST wall-clock).
        """
        now_ist = self.get_ist_now(current_time)
        cal_date = now_ist.date()
        t = now_ist.time()

        is_trading = self.calendar.is_trading_day(cal_date)

        if not is_trading:
            phase = MarketPhase.MARKET_CLOSED
            active_date = None
            # On a non-trading day (e.g. Saturday or holiday), completed session is the last valid trading day
            completed_date = self.calendar.get_previous_trading_date(cal_date)
            prev_date = self.calendar.get_previous_trading_date(completed_date)
            next_date = self.calendar.get_next_trading_date(cal_date)
        else:
            if t < self.DEFAULT_PRE_OPEN_TIME:
                phase = MarketPhase.PRE_MARKET
                active_date = cal_date
                completed_date = self.calendar.get_previous_trading_date(cal_date)
                prev_date = self.calendar.get_previous_trading_date(completed_date)
                next_date = cal_date
            elif t < self.session_open_time:
                phase = MarketPhase.PRE_OPEN
                active_date = cal_date
                completed_date = self.calendar.get_previous_trading_date(cal_date)
                prev_date = self.calendar.get_previous_trading_date(completed_date)
                next_date = cal_date
            elif t <= self.session_close_time:
                phase = MarketPhase.MARKET_OPEN
                active_date = cal_date
                completed_date = self.calendar.get_previous_trading_date(cal_date)
                prev_date = self.calendar.get_previous_trading_date(completed_date)
                next_date = self.calendar.get_next_trading_date(cal_date)
            elif t <= self.DEFAULT_POST_MARKET_END_TIME:
                phase = MarketPhase.POST_MARKET
                active_date = cal_date
                # Post-market: trading is completed for today
                completed_date = cal_date
                prev_date = self.calendar.get_previous_trading_date(cal_date)
                next_date = self.calendar.get_next_trading_date(cal_date)
            else:
                phase = MarketPhase.MARKET_CLOSED
                active_date = None
                # Night: session completed today
                completed_date = cal_date
                prev_date = self.calendar.get_previous_trading_date(cal_date)
                next_date = self.calendar.get_next_trading_date(cal_date)

        return SessionContext(
            calendar_date=cal_date,
            is_trading_day=is_trading,
            market_phase=phase,
            active_trading_date=active_date,
            completed_session_date=completed_date,
            previous_session_date=prev_date,
            next_trading_date=next_date,
            session_open_time=self.session_open_time,
            session_close_time=self.session_close_time,
            observed_at=now_ist,
        )

    def is_session_active(self, current_time: Optional[datetime] = None) -> bool:
        """Returns True if the market is currently in active continuous trading (09:15-15:30 IST)."""
        ctx = self.evaluate_session(current_time)
        return ctx.market_phase == MarketPhase.MARKET_OPEN
