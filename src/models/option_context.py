from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class OptionContext:
    underlying_spot: float
    atm_strike: float
    strike_step: float
    current_weekly_expiry: str
    current_monthly_expiry: str
    time_to_expiry: float  # time to expiry in days or fraction of years
    calendar_dte: int = 0
    trading_dte: int = 0
    dte_basis: str = "CALENDAR_DAYS"
    atm_iv: float = 0.0
    expected_move: float = 0.0
    pcr: float = 1.0
    max_pain: float = 0.0
    highest_call_oi: float = 0.0
    highest_put_oi: float = 0.0
    highest_call_oi_change: float = 0.0
    highest_put_oi_change: float = 0.0
    support_strikes: List[float] = field(default_factory=list)
    resistance_strikes: List[float] = field(default_factory=list)
    liquidity_metrics: Dict[str, Any] = field(default_factory=dict)
    option_chain_summary: Dict[str, Any] = field(default_factory=dict)
    top_candidate_strikes: List[Dict[str, Any]] = field(default_factory=list)
    market_option_bias: str = "NEUTRAL"
    next_weekly_expiry: str = ""
    next_monthly_expiry: str = ""
    far_expiry: str = ""
    all_expiries: List[str] = field(default_factory=list)
    timestamp: str = ""
    schema_version: str = "1.0"
    pipeline_version: str = "1.0"
