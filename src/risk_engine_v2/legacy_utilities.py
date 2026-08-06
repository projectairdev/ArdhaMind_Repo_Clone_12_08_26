from __future__ import annotations

from typing import Optional
from src.configuration_engine.runtime import Config
from src.models import RejectionRecord, TrendSnapshot, RiskCalculationResult
from src.data_engine.instruments import get_symbol_sector


def get_position_size(
    entry_price: float,
    stop_price: float,
    max_capital: float = Config.MAX_CAPITAL_PER_TRADE_STOCKS,
    max_risk: float = Config.MAX_RISK_PER_TRADE_STOCKS,
) -> int:
    risk_per_share = abs(entry_price - stop_price)
    if entry_price <= 0 or risk_per_share <= 0:
        return 0

    qty_by_capital = int(max_capital // entry_price)
    qty_by_risk = int(max_risk // risk_per_share)
    return max(0, min(qty_by_capital, qty_by_risk))


def calculate_stock_risk(
    side: str,
    trigger_buy_above: float,
    trigger_sell_below: float,
    atr_val: float,
    max_capital: float = Config.MAX_CAPITAL_PER_TRADE_STOCKS,
    max_risk: float = Config.MAX_RISK_PER_TRADE_STOCKS,
    sl_atr_mult: float = Config.SL_ATR_MULT,
    target_atr_mult: float = Config.TARGET_ATR_MULT,
) -> RiskCalculationResult:
    suggested_entry = trigger_buy_above if side == "BUY" else trigger_sell_below
    if side == "BUY":
        stop_loss = suggested_entry - (atr_val * sl_atr_mult)
        target = suggested_entry + (atr_val * target_atr_mult)
    else:
        stop_loss = suggested_entry + (atr_val * sl_atr_mult)
        target = suggested_entry - (atr_val * target_atr_mult)

    qty = get_position_size(
        entry_price=suggested_entry,
        stop_price=stop_loss,
        max_capital=max_capital,
        max_risk=max_risk,
    )

    capital_required = suggested_entry * qty
    rupee_risk = abs(suggested_entry - stop_loss) * qty
    rupee_reward = abs(target - suggested_entry) * qty
    reward_risk_ratio = rupee_reward / rupee_risk if rupee_risk > 0 else 0.0

    return RiskCalculationResult(
        suggested_entry=round(suggested_entry, 2),
        stop_loss=round(stop_loss, 2),
        target=round(target, 2),
        quantity=qty,
        capital_required=round(capital_required, 2),
        rupee_risk=round(rupee_risk, 2),
        rupee_reward=round(rupee_reward, 2),
        reward_risk_ratio=round(reward_risk_ratio, 2),
    )


def calculate_option_risk(
    ask_price: float,
    lot_size: int,
    max_capital: float = Config.MAX_CAPITAL_PER_TRADE_OPTIONS,
    max_risk: float = Config.MAX_RISK_PER_TRADE_OPTIONS,
) -> RiskCalculationResult:
    suggested_entry_option = float(ask_price)
    risk_per_option = max_risk / lot_size

    stop_loss_option = max(0.1, suggested_entry_option - risk_per_option)
    target_option = suggested_entry_option + (risk_per_option * 1.5)

    capital_required = suggested_entry_option * lot_size
    rupee_reward = (target_option - suggested_entry_option) * lot_size
    reward_risk_ratio = rupee_reward / max_risk if max_risk > 0 else 0.0

    return RiskCalculationResult(
        suggested_entry=round(suggested_entry_option, 2),
        stop_loss=round(stop_loss_option, 2),
        target=round(target_option, 2),
        quantity=lot_size,
        capital_required=round(capital_required, 2),
        rupee_risk=round(max_risk, 2),
        rupee_reward=round(rupee_reward, 2),
        reward_risk_ratio=round(reward_risk_ratio, 2),
    )


def make_rejection(
    scan_time: str,
    symbol: str,
    stage: str,
    reason: str,
    detail: str,
    market_bias: str,
    trend: Optional[TrendSnapshot] = None,
    candidate_count: int = 0,
    selected_option: str = "",
) -> RejectionRecord:
    return RejectionRecord(
        scanned_at=scan_time,
        symbol=symbol,
        stage=stage,
        reason=reason,
        detail=detail,
        market_bias=market_bias,
        trend=trend.trend if trend is not None else "",
        sector=get_symbol_sector(symbol),
        rsi=round(trend.rsi, 2) if trend is not None else 0.0,
        volume_ratio=round(trend.volume_ratio, 2) if trend is not None else 0.0,
        candidate_count=candidate_count,
        selected_option=selected_option,
    )
