from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def is_market_hours(ts: Optional[datetime] = None) -> bool:
    if ts is None:
        ts = datetime.now()
    if ts.weekday() >= 5:
        return False

    now_minutes = ts.hour * 60 + ts.minute
    # 09:15 to 15:30
    market_open = 9 * 60 + 15
    market_close = 15 * 60 + 30
    return market_open <= now_minutes <= market_close


def next_trading_day(start: Optional[date] = None) -> date:
    next_day = (start or date.today()) + timedelta(days=1)
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    return next_day
