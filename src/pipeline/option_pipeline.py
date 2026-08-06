from __future__ import annotations

from datetime import date
from typing import Dict, List, Tuple, Optional
import pandas as pd

from src.config_engine import Config
from src.utils import setup_logger, now_str
from src.data_engine import (
    get_equity_row,
    get_index_row,
    get_multi_timeframe_history,
)
from src.indicator_engine import (
    compute_timeframe_metrics,
    compute_price_levels,
    compute_relative_strength,
    summarize_multi_timeframe,
)
from src.options_engine import (
    nearest_expiry_for_symbol,
    nearest_expiry_for_nifty,
    get_dynamic_strike_step,
    candidate_strikes,
    filter_option_candidates,
    choose_best_option,
)
from src.risk_engine import make_rejection
from src.models import OptionSignal, TrendSnapshot, MarketRegime
from src.strategies.base import BaseStrategy
from src.data_engine.instruments import get_symbol_sector

logger = setup_logger("OptionPipeline")


class OptionPipeline:
    def __init__(self):
        pass

    def run_symbol(
        self,
        kite,
        instruments_df: pd.DataFrame,
        symbol: str,
        market_regime: MarketRegime,
        history_cache: dict,
        benchmark_history: pd.DataFrame,
        sector_vs_nifty_pct: float,
        scan_time: str,
        strategy: BaseStrategy,
        is_index: bool = False,
        forced_opt_type: Optional[str] = None,
    ) -> Tuple[Optional[OptionSignal], List[Any]]:
        """
        Executes the option pipeline for a single symbol or index.
        """
        rejections = []

        try:
            if is_index:
                index_row = get_index_row(instruments_df, "NIFTY 50" if symbol == "NIFTY" else symbol)
                token = int(index_row["instrument_token"])
            else:
                equity_row = get_equity_row(instruments_df, symbol)
                token = int(equity_row["instrument_token"])
        except Exception as exc:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="INSTRUMENT_LOOKUP",
                    reason="Metadata missing",
                    detail=str(exc),
                    market_bias=market_regime.overall_bias,
                )
            )
            return None, rejections

        # 1. Multi-timeframe History
        try:
            mtf_history = get_multi_timeframe_history(kite, token, history_cache)
        except Exception as exc:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="HISTORICAL_FETCH",
                    reason="Failed fetching MTF candles",
                    detail=str(exc),
                    market_bias=market_regime.overall_bias,
                )
            )
            return None, rejections

        # 2. Timeframe Metrics
        timeframe_metrics = {}
        for interval in ["day", "60minute", "15minute", "5minute"]:
            df_candles = mtf_history.get(interval)
            if df_candles is None or df_candles.empty or len(df_candles) < Config.VOL_AVG_PERIOD:
                rejections.append(
                    make_rejection(
                        scan_time=scan_time,
                        symbol=symbol,
                        stage="TIMEFRAME_ANALYSIS",
                        reason=f"Insufficient historical candles for interval {interval}",
                        detail=f"Candles count: {len(df_candles) if df_candles is not None else 0}",
                        market_bias=market_regime.overall_bias,
                    )
                )
                return None, rejections

            timeframe_metrics[interval] = compute_timeframe_metrics(
                df=df_candles,
                timeframe=interval,
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0 if is_index else Config.BREAKOUT_VOL_MULT_OPTIONS,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )

        five_min = timeframe_metrics["5minute"]
        spot_price = five_min.close

        # Filter: Spot price minimum (only for stocks, not index)
        if not is_index and spot_price < Config.MIN_STOCK_LTP:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="PRE_FILTER",
                    reason="Price below threshold",
                    detail=f"Spot price: {spot_price} vs min: {Config.MIN_STOCK_LTP}",
                    market_bias=market_regime.overall_bias,
                )
            )
            return None, rejections

        # Filter: Stock Volume (only for stocks, not index)
        if not is_index and five_min.last_volume < Config.MIN_STOCK_VOLUME_OPTIONS:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="PRE_FILTER",
                    reason="Insufficient volume",
                    detail=f"Current volume: {five_min.last_volume} vs min: {Config.MIN_STOCK_VOLUME_OPTIONS}",
                    market_bias=market_regime.overall_bias,
                )
            )
            return None, rejections

        # 3. Reference levels and Relative Strength
        price_levels = compute_price_levels(mtf_history["5minute"], mtf_history["day"])
        relative_strength = compute_relative_strength(
            stock_daily_df=mtf_history["day"],
            benchmark_daily_df=benchmark_history,
            sector_vs_nifty_pct=sector_vs_nifty_pct,
            lookback_bars=5,
        )

        # 4. Multi-Timeframe Alignment
        mtf_summary = summarize_multi_timeframe(
            timeframe_metrics=timeframe_metrics,
            price_levels=price_levels,
            relative_strength=relative_strength,
            market_regime_label=market_regime.regime_label,
        )

        opt_type = forced_opt_type
        if not opt_type:
            if mtf_summary.overall_trend == "BULLISH":
                opt_type = "CE"
            elif mtf_summary.overall_trend == "BEARISH":
                opt_type = "PE"

        if not opt_type:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="DIRECTIONAL_FILTER",
                    reason="No clean trend alignment",
                    detail=mtf_summary.rationale,
                    market_bias=market_regime.overall_bias,
                )
            )
            return None, rejections

        # 5. Expiry & Strikes
        expiry = nearest_expiry_for_nifty(instruments_df) if is_index else nearest_expiry_for_symbol(instruments_df, symbol)
        if not expiry:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="EXPIRY_SELECTION",
                    reason="No active expiries available",
                    detail="Filtered out illiquid or extremely near contract dates",
                    market_bias=market_regime.overall_bias,
                    trend=TrendSnapshot(symbol, spot_price, spot_price, five_min.ema_fast, five_min.ema_slow, five_min.rsi, five_min.atr, five_min.avg_volume, five_min.last_volume, five_min.volume_ratio, mtf_summary.overall_trend, five_min.trigger_buy_above, five_min.trigger_sell_below, mtf_summary.rationale),
                )
            )
            return None, rejections

        step = get_dynamic_strike_step(instruments_df, "NIFTY" if is_index else symbol, expiry)
        strikes = candidate_strikes(spot_price, step)

        options_df = filter_option_candidates(instruments_df, "NIFTY" if is_index else symbol, expiry, opt_type, strikes)
        if options_df.empty:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="STRIKE_SELECTION",
                    reason="No option contract rows found",
                    detail=f"Symbol: {symbol} expiry: {expiry} type: {opt_type}",
                    market_bias=market_regime.overall_bias,
                    trend=TrendSnapshot(symbol, spot_price, spot_price, five_min.ema_fast, five_min.ema_slow, five_min.rsi, five_min.atr, five_min.avg_volume, five_min.last_volume, five_min.volume_ratio, mtf_summary.overall_trend, five_min.trigger_buy_above, five_min.trigger_sell_below, mtf_summary.rationale),
                )
            )
            return None, rejections

        # 6. Best Option and Quotes
        best_opt, option_quote_time = choose_best_option(kite, options_df)
        if best_opt is None:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="OPTION_LIQUIDITY",
                    reason="Illiquid option chain or high cost",
                    detail=f"Tested {len(options_df)} strikes; spread/cost restrictions violated",
                    market_bias=market_regime.overall_bias,
                    trend=TrendSnapshot(symbol, spot_price, spot_price, five_min.ema_fast, five_min.ema_slow, five_min.rsi, five_min.atr, five_min.avg_volume, five_min.last_volume, five_min.volume_ratio, mtf_summary.overall_trend, five_min.trigger_buy_above, five_min.trigger_sell_below, mtf_summary.rationale),
                    candidate_count=len(options_df),
                )
            )
            return None, rejections

        # 7. Construct dataclass TrendSnapshot
        trend_snapshot = TrendSnapshot(
            symbol=symbol,
            spot=spot_price,
            close=spot_price,
            ema_fast=five_min.ema_fast,
            ema_slow=five_min.ema_slow,
            rsi=five_min.rsi,
            atr=five_min.atr,
            avg_volume=five_min.avg_volume,
            last_volume=five_min.last_volume,
            volume_ratio=five_min.volume_ratio,
            trend=mtf_summary.overall_trend,
            trigger_buy_above=five_min.trigger_buy_above,
            trigger_sell_below=five_min.trigger_sell_below,
            rationale=mtf_summary.rationale,
            structure=mtf_summary.structure.trend,
            higher_highs=mtf_summary.structure.higher_highs,
            higher_lows=mtf_summary.structure.higher_lows,
            lower_highs=mtf_summary.structure.lower_highs,
            lower_lows=mtf_summary.structure.lower_lows,
            daily_trend=mtf_summary.daily_trend,
            hourly_trend=mtf_summary.hourly_trend,
            fifteen_min_trend=mtf_summary.fifteen_min_trend,
            five_min_trend=mtf_summary.five_min_trend,
            timeframe_alignment_score=mtf_summary.timeframe_alignment_score,
            advanced_confidence_boost=mtf_summary.advanced_confidence_boost,
            price_level_score=mtf_summary.price_level_score,
            relative_strength_score=relative_strength.score,
            regime_score_adjustment=mtf_summary.regime_score,
            strategy_regime=market_regime.regime_label,
            intraday_vwap=price_levels.intraday_vwap,
            prev_day_high=price_levels.prev_day_high,
            prev_day_low=price_levels.prev_day_low,
            prev_day_close=price_levels.prev_day_close,
            weekly_high=price_levels.weekly_high,
            weekly_low=price_levels.weekly_low,
            stock_vs_nifty_return=relative_strength.stock_vs_nifty_pct,
            sector_vs_nifty_return=relative_strength.sector_vs_nifty_pct,
        )

        # 8. Strategy Pattern Signal Generation
        signal = strategy.generate_signal(
            trend_snapshot=trend_snapshot,
            market_regime=market_regime,
            asset_type="OPTION",
            option_row=best_opt,
            option_quote_time=option_quote_time,
            sector_strength=sector_vs_nifty_pct,
            sector="INDEX" if is_index else get_symbol_sector(symbol),
            scan_time=scan_time,
            forced_opt_type=forced_opt_type,
        )

        if signal is None:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="STRATEGY_GENERATION",
                    reason="Strategy generated empty signal",
                    detail=f"Overall trend: {trend_snapshot.trend}",
                    market_bias=market_regime.overall_bias,
                    trend=trend_snapshot,
                )
            )
            return None, rejections

        # Confidence verification
        min_conf = Config.MIN_CONFIDENCE_TO_SHOW_OPTIONS
        if signal.confidence < min_conf:
            rejections.append(
                make_rejection(
                    scan_time=scan_time,
                    symbol=symbol,
                    stage="CONFIDENCE_FILTER",
                    reason="Confidence below minimum",
                    detail=f"Confidence: {signal.confidence:.2f} vs min: {min_conf:.2f}",
                    market_bias=market_regime.overall_bias,
                    trend=trend_snapshot,
                    selected_option=best_opt["tradingsymbol"],
                )
            )
            return None, rejections

        return signal, rejections
