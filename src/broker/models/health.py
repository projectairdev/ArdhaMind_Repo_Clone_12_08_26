from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class BrokerHealth:
    broker_name: str
    connection_status: str             # "CONNECTED", "DISCONNECTED", "ERROR"
    trading_mode: str                  # "PAPER_TRADING", "LIVE_ZERODHA", etc.
    latency: float                     # latency in milliseconds
    authentication_state: str          # "AUTHENTICATED", "EXPIRED", "UNAUTHENTICATED"
    last_heartbeat: str                # timestamp string
    instrument_cache_status: str       # "VALID", "STALE", "MISSING"
    market_status: str                 # "OPEN", "CLOSED", "HOLIDAY"
    health_score: float                # 0.0 to 100.0
    last_error: Optional[str] = None
    
    # Extended metrics (Sprint 28)
    authentication_status: str = "UNAUTHENTICATED"  # "AUTHENTICATED", "EXPIRED", "UNAUTHENTICATED"
    session_age_hours: float = 0.0
    token_expiry: str = "N/A"
    last_login_time: str = "N/A"
    session_valid: bool = False
    broker_version: str = "KiteConnect v5.2"
    api_status: str = "ONLINE"

