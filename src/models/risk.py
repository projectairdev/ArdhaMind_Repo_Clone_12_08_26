from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskParameters:
    max_capital_per_trade: float
    max_risk_per_trade: float
    min_stock_ltp: float
    min_stock_volume: int
    min_abs_pct_move: float


@dataclass
class RiskCalculationResult:
    suggested_entry: float
    stop_loss: float
    target: float
    quantity: int
    capital_required: float
    rupee_risk: float
    rupee_reward: float
    reward_risk_ratio: float


@dataclass
class RejectionRecord:
    scanned_at: str
    symbol: str
    stage: str
    reason: str
    detail: str
    market_bias: str
    trend: str = ""
    sector: str = ""
    rsi: float = 0.0
    volume_ratio: float = 0.0
    candidate_count: int = 0
    selected_option: str = ""
