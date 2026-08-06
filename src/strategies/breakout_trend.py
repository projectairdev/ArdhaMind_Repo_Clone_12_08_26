from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional
import pandas as pd

from src.config_engine import Config
from src.models import (
    OptionSignal,
    StockSignal,
    TrendSnapshot,
    MarketRegime,
    TradeSignal,
)
from src.strategies.base import BaseStrategy
from src.strategies.loader import register_strategy
from src.confidence_engine import calc_stock_confidence, calc_confidence
from src.risk_engine import calculate_stock_risk, calculate_option_risk


class BreakoutTrendStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="BreakoutTrendStrategy",
            description="Swing high/low breakout trend-following strategy with volume and indicators confirmation",
        )

    def generate_signal(
        self,
        trend_snapshot: TrendSnapshot,
        market_regime: MarketRegime,
        asset_type: str = "STOCK",
        **kwargs: Any,
    ) -> TradeSignal | None:
        scan_time = kwargs.get("scan_time", "")

        if asset_type == "STOCK":
            side = ""
            if trend_snapshot.trend == "BULLISH":
                side = "BUY"
            elif trend_snapshot.trend == "BEARISH":
                side = "SELL"

            if not side:
                return None

            confidence = calc_stock_confidence(
                trend=trend_snapshot,
                market_regime=market_regime,
            )

            # Risk calculations
            risk_result = calculate_stock_risk(
                side=side,
                trigger_buy_above=trend_snapshot.trigger_buy_above,
                trigger_sell_below=trend_snapshot.trigger_sell_below,
                atr_val=trend_snapshot.atr,
            )

            if risk_result.quantity <= 0:
                return None

            dist_abs = abs(trend_snapshot.close - risk_result.suggested_entry)
            dist_pct = (dist_abs / trend_snapshot.close) * 100.0 if trend_snapshot.close > 0 else 0.0

            return StockSignal(
                scanned_at=scan_time,
                quote_time=scan_time,
                market_bias=market_regime.overall_bias,
                setup_type="EMA_BREAKOUT" if trend_snapshot.volume_ratio >= Config.BREAKOUT_VOL_MULT_STOCKS else "EMA_PULLBACK",
                confidence=confidence,
                symbol=trend_snapshot.symbol,
                side=side,
                spot_price=trend_snapshot.close,
                trigger_price=risk_result.suggested_entry,
                trigger_distance_abs=round(dist_abs, 2),
                trigger_distance_pct=round(dist_pct, 2),
                trend=trend_snapshot.trend,
                quantity=risk_result.quantity,
                capital_required=risk_result.capital_required,
                rupee_risk=risk_result.rupee_risk,
                rupee_reward=risk_result.rupee_reward,
                reward_risk_ratio=risk_result.reward_risk_ratio,
                suggested_entry=risk_result.suggested_entry,
                stop_loss=risk_result.stop_loss,
                target=risk_result.target,
                exit_rule="Exit stock if stop loss hit, target reached, or trend changes on hourly chart",
                rationale=trend_snapshot.rationale,
                strategy_regime=market_regime.regime_label,
                daily_trend=trend_snapshot.daily_trend,
                hourly_trend=trend_snapshot.hourly_trend,
                fifteen_min_trend=trend_snapshot.fifteen_min_trend,
                five_min_trend=trend_snapshot.five_min_trend,
                timeframe_alignment_score=trend_snapshot.timeframe_alignment_score,
                structure=trend_snapshot.structure,
                intraday_vwap=trend_snapshot.intraday_vwap,
                prev_day_high=trend_snapshot.prev_day_high,
                prev_day_low=trend_snapshot.prev_day_low,
                prev_day_close=trend_snapshot.prev_day_close,
                weekly_high=trend_snapshot.weekly_high,
                weekly_low=trend_snapshot.weekly_low,
                stock_vs_nifty_return=trend_snapshot.stock_vs_nifty_return,
                sector_vs_nifty_return=trend_snapshot.sector_vs_nifty_return,
            )

        elif asset_type == "OPTION":
            option_row = kwargs.get("option_row")
            option_quote_time = kwargs.get("option_quote_time", scan_time)
            sector_strength = kwargs.get("sector_strength", 0.0)
            sector = kwargs.get("sector", "INDEX")

            if option_row is None:
                return None

            opt_type = kwargs.get("forced_opt_type")
            if not opt_type:
                if trend_snapshot.trend == "BULLISH":
                    opt_type = "CE"
                elif trend_snapshot.trend == "BEARISH":
                    opt_type = "PE"

            if not opt_type:
                return None

            confidence = calc_confidence(
                trend=trend_snapshot,
                market_regime=market_regime,
                opt_type=opt_type,
                option_row=option_row,
            )

            # Option risk calculation
            risk_result = calculate_option_risk(
                ask_price=float(option_row["ask_price"]),
                lot_size=int(option_row["lot_size"]),
            )

            trigger_underlying = (
                trend_snapshot.trigger_buy_above if opt_type == "CE" else trend_snapshot.trigger_sell_below
            )
            dist_abs = abs(trend_snapshot.close - trigger_underlying)
            dist_pct = (dist_abs / trend_snapshot.close) * 100.0 if trend_snapshot.close > 0 else 0.0

            return OptionSignal(
                scanned_at=scan_time,
                option_quote_time=option_quote_time,
                underlying_quote_time=scan_time,
                market_bias=market_regime.overall_bias,
                setup_type="EMA_BREAKOUT" if trend_snapshot.volume_ratio >= Config.BREAKOUT_VOL_MULT_OPTIONS else "EMA_PULLBACK",
                confidence=confidence,
                underlying=trend_snapshot.symbol,
                underlying_spot=trend_snapshot.close,
                underlying_trigger=round(trigger_underlying, 2),
                trigger_distance_abs=round(dist_abs, 2),
                trigger_distance_pct=round(dist_pct, 2),
                trend=trend_snapshot.trend,
                sector=sector,
                sector_strength=sector_strength,
                option_symbol=option_row["tradingsymbol"],
                option_type=opt_type,
                strike=float(option_row["strike"]),
                expiry=str(option_row["expiry"]),
                days_to_expiry=(option_row["expiry"] - date.today()).days if isinstance(option_row["expiry"], (date, pd.Timestamp)) else 0,
                option_ltp=float(option_row["option_ltp"]),
                option_volume=int(option_row["option_volume"]),
                option_oi=int(option_row["option_oi"]),
                bid_price=float(option_row["bid_price"]),
                ask_price=float(option_row["ask_price"]),
                spread_pct=float(option_row["spread_pct"]),
                option_quality_score=float(option_row["option_quality_score"]),
                lot_size=risk_result.quantity,
                capital_required=risk_result.capital_required,
                rupee_risk=risk_result.rupee_risk,
                rupee_reward=risk_result.rupee_reward,
                reward_risk_ratio=risk_result.reward_risk_ratio,
                entry_when_underlying=(
                    f"Enter {opt_type} option when NSE:{trend_snapshot.symbol} crosses {trigger_underlying:.2f}"
                ),
                suggested_entry_option=risk_result.suggested_entry,
                stop_loss_option=risk_result.stop_loss,
                target_option=risk_result.target,
                exit_rule="Exit option if stop loss hit, target reached, or trend changes on hourly chart",
                rationale=trend_snapshot.rationale,
                strategy_regime=market_regime.regime_label,
                daily_trend=trend_snapshot.daily_trend,
                hourly_trend=trend_snapshot.hourly_trend,
                fifteen_min_trend=trend_snapshot.fifteen_min_trend,
                five_min_trend=trend_snapshot.five_min_trend,
                timeframe_alignment_score=trend_snapshot.timeframe_alignment_score,
                structure=trend_snapshot.structure,
                intraday_vwap=trend_snapshot.intraday_vwap,
                prev_day_high=trend_snapshot.prev_day_high,
                prev_day_low=trend_snapshot.prev_day_low,
                prev_day_close=trend_snapshot.prev_day_close,
                weekly_high=trend_snapshot.weekly_high,
                weekly_low=trend_snapshot.weekly_low,
                stock_vs_nifty_return=trend_snapshot.stock_vs_nifty_return,
                sector_vs_nifty_return=trend_snapshot.sector_vs_nifty_return,
            )
        return None


# Register Strategy globally on module load
register_strategy("BreakoutTrendStrategy", BreakoutTrendStrategy())
