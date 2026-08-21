# src/intelligence_engine/market_insights_session_resolver.py
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from src.utils import setup_logger

logger = setup_logger("MarketInsightsSessionResolver")

IST = timezone(timedelta(hours=5, minutes=30))


class MarketInsightsSession(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    PRE_OPEN = "PRE_OPEN"
    LIVE_MARKET = "LIVE_MARKET"
    PRE_CLOSE = "PRE_CLOSE"
    CLOSED_MARKET = "CLOSED_MARKET"


class MarketInsightsSessionResolver:
    """
    Authoritative Market Insights Session Resolver for ArdhaMind.
    
    Determines current session state based on IST time & trading calendar:
    - PRE_MARKET: 02:00:00 - 08:59:59 IST
    - PRE_OPEN: 09:00:00 - 09:14:59 IST
    - LIVE_MARKET: 09:15:00 - 15:24:59 IST
    - PRE_CLOSE: 15:25:00 - 15:29:59 IST
    - CLOSED_MARKET: 15:30:00 - 01:59:59 IST
    
    Trading Calendar Overrides:
    - Saturdays & Sundays -> CLOSED_MARKET (unless special session)
    - Exchange Holidays -> CLOSED_MARKET
    - Backend canonical state takes precedence
    """

    @classmethod
    def get_canonical_ist_now(cls, custom_datetime: Optional[datetime] = None) -> datetime:
        if custom_datetime is not None:
            if custom_datetime.tzinfo is None:
                return custom_datetime.replace(tzinfo=IST)
            return custom_datetime.astimezone(IST)
        return datetime.now(IST)

    @classmethod
    def resolve_session(
        cls,
        custom_datetime: Optional[datetime] = None,
        market_session_state: Optional[Dict[str, Any]] = None,
        is_trading_day_override: Optional[bool] = None,
    ) -> Dict[str, Any]:
        now_ist = cls.get_canonical_ist_now(custom_datetime)
        
        hour = now_ist.hour
        minute = now_ist.minute
        second = now_ist.second
        
        time_seconds = hour * 3600 + minute * 60 + second
        
        # Calendar & Day-of-week Check (0 = Monday, 6 = Sunday in Python)
        weekday = now_ist.weekday()
        is_weekend = weekday in (5, 6) # Sat, Sun
        
        m_session = market_session_state or {}
        m_status = str(m_session.get("status") or "").lower()
        is_holiday = m_status in ("holiday", "closed_holiday")
        
        if is_trading_day_override is not None:
            is_trading_day = is_trading_day_override
        else:
            # A day is a trading day if it is not a weekend and not an exchange holiday.
            # Exchange session status "closed" during non-market hours (15:30-09:15) does NOT make a weekday a non-trading day.
            is_trading_day = not is_weekend and not is_holiday

        # Non-trading day override
        if not is_trading_day:
            return {
                "session": MarketInsightsSession.CLOSED_MARKET.value,
                "session_label": "MARKET CLOSED INSIGHTS",
                "status_text": "NO TRADING SESSION TODAY",
                "is_trading_day": False,
                "ist_time_str": now_ist.strftime("%H:%M:%S IST"),
                "date_str": now_ist.strftime("%Y-%m-%d"),
                "opening_setup_ready": False,
            }

        # IST Time Window Resolution
        # 02:00:00 = 7200s, 08:59:59 = 32399s
        # 09:00:00 = 32400s, 09:14:59 = 33299s
        # 09:15:00 = 33300s, 15:24:59 = 55499s
        # 15:25:00 = 55500s, 15:29:59 = 55799s
        # 15:30:00 = 55800s
        if 7200 <= time_seconds < 32400:
            session = MarketInsightsSession.PRE_MARKET
            label = "PRE-MARKET INSIGHTS"
            status_text = "CANONICAL 08:50 SNAPSHOT" if time_seconds >= 31800 else "PREPARING MORNING BASELINE"
        elif 32400 <= time_seconds < 33300:
            session = MarketInsightsSession.PRE_OPEN
            label = "PRE-OPEN INSIGHTS"
            status_text = "OPENING SETUP READY" if time_seconds >= 32880 else "PRICE DISCOVERY"
        elif 33300 <= time_seconds < 55500:
            session = MarketInsightsSession.LIVE_MARKET
            label = "LIVE MARKET INSIGHTS"
            status_text = "MARKET OPEN"
        elif 55500 <= time_seconds < 55800:
            session = MarketInsightsSession.PRE_CLOSE
            label = "PRE-CLOSE INSIGHTS"
            status_text = "PREPARING TOMORROW"
        else:
            # 15:30:00 to 01:59:59 IST
            session = MarketInsightsSession.CLOSED_MARKET
            label = "MARKET CLOSED INSIGHTS"
            status_text = "SESSION COMPLETE"

        # 09:08 Opening Setup Readiness (32880s = 09:08:00 IST)
        has_pre_open_data = bool(m_session.get("has_pre_open_data", True))
        opening_setup_ready = (session == MarketInsightsSession.PRE_OPEN and time_seconds >= 32880 and has_pre_open_data)

        return {
            "session": session.value,
            "session_label": label,
            "status_text": status_text,
            "is_trading_day": True,
            "ist_time_str": now_ist.strftime("%H:%M:%S IST"),
            "date_str": now_ist.strftime("%Y-%m-%d"),
            "opening_setup_ready": opening_setup_ready,
        }
