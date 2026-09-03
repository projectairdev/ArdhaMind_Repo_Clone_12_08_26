from __future__ import annotations

from datetime import date, datetime, timedelta
import threading
from typing import FrozenSet, Iterable, List, Optional, Set


class ExchangeCalendar:
    """
    Authoritative Exchange Trading Calendar for NSE.
    Handles standard weekends, public holidays, special trading session overrides,
    and month/year boundaries.
    """

    # Built-in baseline NSE holidays for 2025-2026 (ISO date format YYYY-MM-DD)
    DEFAULT_NSE_HOLIDAYS: FrozenSet[date] = frozenset({
        # 2025 Sample / Standard NSE Holidays
        date(2025, 1, 26),  # Republic Day
        date(2025, 2, 26),  # Mahashivratri
        date(2025, 3, 14),  # Holi
        date(2025, 3, 31),  # Id-Ul-Fitr
        date(2025, 4, 10),  # Mahavir Jayanti
        date(2025, 4, 14),  # Dr. Baba Saheb Ambedkar Jayanti
        date(2025, 4, 18),  # Good Friday
        date(2025, 5, 1),   # Maharashtra Day
        date(2025, 8, 15),  # Independence Day
        date(2025, 8, 27),  # Ganesh Chaturthi
        date(2025, 10, 2),  # Mahatma Gandhi Jayanti
        date(2025, 10, 21), # Diwali Laxmi Pujan (Muhurat - override handled via special sessions)
        date(2025, 10, 22), # Diwali Balipratipada
        date(2025, 11, 5),  # Prakash Gurpurb Sri Guru Nanak Dev
        date(2025, 12, 25), # Christmas
        # 2026 NSE equity/derivatives trading holidays — weekday closures only.
        # Dates reconciled against the official 2026 exchange holiday circular.
        # (Aug 15 / Independence Day falls on a Saturday in 2026, so it is not a
        # trading-day closure and is intentionally absent.) Festival-name comments
        # for movable feasts are indicative; the date is authoritative.
        date(2026, 1, 26),  # Republic Day
        date(2026, 3, 3),   # Holi
        date(2026, 3, 26),  # NSE trading holiday (movable feast)
        date(2026, 3, 31),  # Id-Ul-Fitr (Ramzan Id)
        date(2026, 4, 3),   # Good Friday
        date(2026, 4, 14),  # Dr. Baba Saheb Ambedkar Jayanti
        date(2026, 5, 1),   # Maharashtra Day
        date(2026, 5, 28),  # Bakri Id (Id-ul-Zuha)
        date(2026, 6, 26),  # Muharram
        date(2026, 9, 14),  # Ganesh Chaturthi
        date(2026, 10, 2),  # Mahatma Gandhi Jayanti
        date(2026, 10, 20), # Dussehra (Vijaya Dashami)
        date(2026, 11, 10), # Diwali - Laxmi Pujan
        date(2026, 11, 24), # Guru Nanak Jayanti
        date(2026, 12, 25), # Christmas
    })

    def __init__(
        self,
        holidays: Optional[Iterable[date | str]] = None,
        special_trading_days: Optional[Iterable[date | str]] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._holidays: Set[date] = set(self.DEFAULT_NSE_HOLIDAYS)
        self._special_trading_days: Set[date] = set()

        if holidays is not None:
            self.add_holidays(holidays)

        if special_trading_days is not None:
            self.add_special_trading_days(special_trading_days)

    def _normalize_date(self, d: date | str | datetime) -> date:
        if isinstance(d, datetime):
            return d.date()
        elif isinstance(d, str):
            return datetime.strptime(d.strip()[:10], "%Y-%m-%d").date()
        elif isinstance(d, date):
            return d
        raise ValueError(f"Invalid date object: {d}")

    def add_holidays(self, holidays: Iterable[date | str]) -> None:
        with self._lock:
            for h in holidays:
                self._holidays.add(self._normalize_date(h))

    def remove_holiday(self, holiday: date | str) -> None:
        with self._lock:
            d = self._normalize_date(holiday)
            self._holidays.discard(d)

    def add_special_trading_days(self, days: Iterable[date | str]) -> None:
        """Adds special weekend/holiday trading sessions (e.g. Muhurat or Disaster Recovery tests)."""
        with self._lock:
            for s in days:
                self._special_trading_days.add(self._normalize_date(s))

    def is_trading_day(self, target_date: date | str | datetime) -> bool:
        """
        Determines if target_date is an active exchange trading day.
        A date is a trading day if:
          1. It is explicitly registered as a special trading day, OR
          2. It is Monday-Friday AND NOT an official holiday.
        """
        d = self._normalize_date(target_date)
        with self._lock:
            if d in self._special_trading_days:
                return True
            if d.weekday() >= 5:  # Saturday (5) or Sunday (6)
                return False
            if d in self._holidays:
                return False
            return True

    def get_previous_trading_date(self, reference_date: date | str | datetime) -> date:
        """
        Returns the closest previous trading date before reference_date.
        Never simply assumes reference_date - 1 day is valid.
        """
        d = self._normalize_date(reference_date)
        curr = d - timedelta(days=1)
        while not self.is_trading_day(curr):
            curr -= timedelta(days=1)
        return curr

    def get_next_trading_date(self, reference_date: date | str | datetime) -> date:
        """
        Returns the closest next trading date after reference_date.
        """
        d = self._normalize_date(reference_date)
        curr = d + timedelta(days=1)
        while not self.is_trading_day(curr):
            curr += timedelta(days=1)
        return curr

    def get_trading_days(
        self,
        start_date: date | str | datetime,
        end_date: date | str | datetime,
    ) -> List[date]:
        """Returns sorted list of trading dates between start_date and end_date (inclusive)."""
        start = self._normalize_date(start_date)
        end = self._normalize_date(end_date)
        if start > end:
            return []

        trading_days: List[date] = []
        curr = start
        while curr <= end:
            if self.is_trading_day(curr):
                trading_days.append(curr)
            curr += timedelta(days=1)
        return trading_days
