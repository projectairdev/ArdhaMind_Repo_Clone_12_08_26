# src/intelligence_engine/position_sizing_engine.py
"""
PositionSizingEngine — Deterministic Option Position Sizing & Risk Policy Engine for AIR ArdhaMind.

Calculates contract quantities and capital exposure based on:
1. Available account balance / trading capital (never fabricated)
2. Configured risk per trade percentage (e.g. 1.0%)
3. Underlying stop/invalidation distance and option delta
4. Lot size (25 contracts per NIFTY lot)
5. Max capital allocation and daily risk limits
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RiskPolicyConfig:
    max_risk_per_trade_pct: float = 1.0  # Max 1% of account equity per trade
    max_capital_allocation_pct: float = 10.0  # Max 10% capital in single position
    max_daily_risk_pct: float = 3.0  # Max 3% daily cumulative loss
    max_concurrent_positions: int = 2
    min_risk_reward: float = 1.5
    max_spread_pct: float = 1.5
    max_chase_pts: float = 25.0
    lot_size: int = 25  # NIFTY lot size

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PositionSizeResult:
    capital_base: Optional[float]
    risk_budget: Optional[float]
    risk_per_unit: Optional[float]
    raw_quantity: Optional[float]
    rounded_lots: Optional[int]
    final_quantity: Optional[int]
    estimated_premium_outlay: Optional[float]
    estimated_max_loss: Optional[float]
    position_size_status: str  # SIZED | POSITION_SIZE_UNAVAILABLE | EXCEEDS_RISK_LIMIT | INSUFFICIENT_FUNDS
    risk_blockers: List[str] = field(default_factory=list)
    policy_applied: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PositionSizingEngine:
    """
    Deterministic Option Position Sizer and Safety Gatekeeper.
    """

    @classmethod
    def calculate_position_size(
        cls,
        account_capital: Optional[float],
        option_ltp: float,
        spot: float,
        invalidation_price: Optional[float],
        delta: Optional[float] = None,
        policy: Optional[RiskPolicyConfig] = None,
        daily_loss_accumulated: float = 0.0,
        active_positions_count: int = 0
    ) -> PositionSizeResult:
        cfg = policy or RiskPolicyConfig()
        blockers: List[str] = []

        # 1. Capital Availability Check (Never fabricate balance)
        if account_capital is None or account_capital <= 0:
            return PositionSizeResult(
                capital_base=None,
                risk_budget=None,
                risk_per_unit=None,
                raw_quantity=None,
                rounded_lots=None,
                final_quantity=None,
                estimated_premium_outlay=None,
                estimated_max_loss=None,
                position_size_status="POSITION_SIZE_UNAVAILABLE",
                risk_blockers=["Account capital unavailable from broker"],
                policy_applied=cfg.to_dict()
            )

        if option_ltp <= 0 or spot <= 0:
            return PositionSizeResult(
                capital_base=account_capital,
                risk_budget=None,
                risk_per_unit=None,
                raw_quantity=None,
                rounded_lots=None,
                final_quantity=None,
                estimated_premium_outlay=None,
                estimated_max_loss=None,
                position_size_status="POSITION_SIZE_UNAVAILABLE",
                risk_blockers=["Invalid option premium or underlying spot price"],
                policy_applied=cfg.to_dict()
            )

        # 2. Portfolio & Daily Loss Policy Limits
        if active_positions_count >= cfg.max_concurrent_positions:
            blockers.append(f"Max concurrent positions ({cfg.max_concurrent_positions}) reached")

        max_daily_loss_rupees = account_capital * (cfg.max_daily_risk_pct / 100.0)
        if daily_loss_accumulated >= max_daily_loss_rupees:
            blockers.append(f"Daily loss limit (₹{max_daily_loss_rupees:,.0f}, {cfg.max_daily_risk_pct}%) breached")

        # 3. Risk Budget Calculation
        risk_budget = round(account_capital * (cfg.max_risk_per_trade_pct / 100.0), 2)
        max_capital_allocation = round(account_capital * (cfg.max_capital_allocation_pct / 100.0), 2)

        # 4. Risk per Option Unit (based on delta and stop distance)
        eff_delta = max(0.20, abs(delta)) if delta is not None else 0.50
        if invalidation_price and invalidation_price > 0:
            stop_dist_underlying = abs(spot - invalidation_price)
            # Estimated option stop distance
            estimated_option_stop = stop_dist_underlying * eff_delta
            risk_per_unit = round(min(option_ltp, max(5.0, estimated_option_stop)), 2)
        else:
            # Conservative default: assume full option premium is at risk
            risk_per_unit = round(option_ltp * 0.50, 2)
            blockers.append("No explicit invalidation price provided; using conservative risk estimate")

        # 5. Raw Quantity & Lot Rounding
        raw_qty = risk_budget / risk_per_unit
        lots_by_risk = math.floor(raw_qty / cfg.lot_size)

        # Also constrain by Max Capital Allocation (outlay <= max_capital_allocation)
        lots_by_capital = math.floor(max_capital_allocation / (option_ltp * cfg.lot_size))

        rounded_lots = min(lots_by_risk, lots_by_capital)

        if rounded_lots <= 0:
            # Check if 1 minimum lot exceeds risk budget or capital allocation
            min_lot_outlay = cfg.lot_size * option_ltp
            min_lot_risk = cfg.lot_size * risk_per_unit
            if min_lot_risk > risk_budget * 1.25 or min_lot_outlay > max_capital_allocation * 1.25:
                blockers.append(f"Minimum 1 lot (₹{min_lot_outlay:,.0f} outlay, ₹{min_lot_risk:,.0f} risk) exceeds risk budget (₹{risk_budget:,.0f})")
                return PositionSizeResult(
                    capital_base=account_capital,
                    risk_budget=risk_budget,
                    risk_per_unit=risk_per_unit,
                    raw_quantity=raw_qty,
                    rounded_lots=0,
                    final_quantity=0,
                    estimated_premium_outlay=0.0,
                    estimated_max_loss=0.0,
                    position_size_status="EXCEEDS_RISK_LIMIT",
                    risk_blockers=blockers,
                    policy_applied=cfg.to_dict()
                )
            else:
                # Allow 1 single minimum lot if within 25% tolerance
                rounded_lots = 1

        final_quantity = rounded_lots * cfg.lot_size
        estimated_outlay = round(final_quantity * option_ltp, 2)
        estimated_max_loss = round(final_quantity * risk_per_unit, 2)

        # Funds availability check
        if estimated_outlay > account_capital:
            blockers.append(f"Insufficient funds (Required: ₹{estimated_outlay:,.0f}, Available: ₹{account_capital:,.0f})")
            status = "INSUFFICIENT_FUNDS"
        elif blockers:
            status = "EXCEEDS_RISK_LIMIT"
        else:
            status = "SIZED"

        return PositionSizeResult(
            capital_base=account_capital,
            risk_budget=risk_budget,
            risk_per_unit=risk_per_unit,
            raw_quantity=round(raw_qty, 1),
            rounded_lots=rounded_lots,
            final_quantity=final_quantity,
            estimated_premium_outlay=estimated_outlay,
            estimated_max_loss=estimated_max_loss,
            position_size_status=status,
            risk_blockers=blockers,
            policy_applied=cfg.to_dict()
        )
