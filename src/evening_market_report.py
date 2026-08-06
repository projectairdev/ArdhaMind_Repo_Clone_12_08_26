#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import pandas as pd
from typing import Dict, List, Any

# Add src to python path if run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_engine import Config
from src.utils import setup_logger, now_str
from src.utils.io_utils import export_json_file
from src.data_engine import (
    make_kite,
    load_instruments_df,
    get_multi_timeframe_history,
)
from src.indicator_engine import (
    compute_timeframe_metrics,
    compute_price_levels,
    compute_relative_strength,
)
from src.pipeline import MarketPipeline
from src.ui import print_evening_market_report

logger = setup_logger("EveningMarketReport")


class MonitorRow:
    def __init__(
        self,
        symbol: str,
        pct_change: float,
        trend: str,
        rsi: float,
        volume_ratio: float,
        sector: str,
        sector_strength: float,
        buy_trigger: float,
        sell_trigger: float,
        setup_score: float,
    ):
        self.symbol = symbol
        self.pct_change = pct_change
        self.trend = trend
        self.rsi = rsi
        self.volume_ratio = volume_ratio
        self.sector = sector
        self.sector_strength = sector_strength
        self.buy_trigger = buy_trigger
        self.sell_trigger = sell_trigger
        self.setup_score = setup_score


def generate_evening_report(kite, instruments_df: pd.DataFrame) -> None:
    scan_time = now_str()
    logger.info("Generating Evening Market Wrap Report...")

    # 1-3. Run MarketPipeline to get macro indicators, market breadth, regime, and sectors
    pipeline = MarketPipeline()
    regime, snapshot_df, sector_summary_sorted = pipeline.run(kite, instruments_df)

    if snapshot_df.empty:
        logger.error("Empty market snapshot. Cannot generate report.")
        return

    sector_scores_map = regime.sector_scores

    # 4. Filter and process all symbols into Watch lists
    monitor_lists: Dict[str, List[MonitorRow]] = {
        "bullish_continuation": [],
        "bearish_continuation": [],
        "near_breakout": [],
        "near_breakdown": [],
        "reversal_watch": [],
    }

    # Limit scan count to save rate limit, or scan whole snapshot up to top N
    scan_symbols = snapshot_df.sort_values("volume", ascending=False)["symbol"].head(Config.SCAN_TOP_N_OPTIONS).tolist()

    history_cache = {}
    benchmark_history = None
    try:
        nifty_row = instruments_df[
            (instruments_df["exchange"] == "NSE")
            & (instruments_df["segment"] == "INDICES")
            & (instruments_df["tradingsymbol"] == "NIFTY 50")
        ].iloc[0]
        benchmark_history = get_multi_timeframe_history(kite, int(nifty_row["instrument_token"]))["day"]
    except Exception:
        pass

    for symbol in scan_symbols:
        try:
            eq_row = instruments_df[
                (instruments_df["exchange"] == "NSE")
                & (instruments_df["segment"] == "NSE")
                & (instruments_df["tradingsymbol"] == symbol)
            ].iloc[0]
            token = int(eq_row["instrument_token"])

            mtf_history = get_multi_timeframe_history(kite, token, history_cache)
            daily_candles = mtf_history["day"]
            five_candles = mtf_history["5minute"]

            if daily_candles.empty or len(daily_candles) < Config.VOL_AVG_PERIOD:
                continue

            day_m = compute_timeframe_metrics(
                df=daily_candles,
                timeframe="day",
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )
            five_m = compute_timeframe_metrics(
                df=five_candles,
                timeframe="5minute",
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )

            spot = five_m.close
            price_levels = compute_price_levels(five_candles, daily_candles)
            relative_strength = compute_relative_strength(
                stock_daily_df=daily_candles,
                benchmark_daily_df=benchmark_history,
                sector_vs_nifty_pct=sector_scores_map.get(day_m.timeframe, 0.0),
            )

            # Buy/sell trigger values
            buy_trigger = price_levels.prev_day_high
            sell_trigger = price_levels.prev_day_low

            # Setup Score calculation
            vol_score = min(2.5, five_m.volume_ratio * 1.0)
            rs_score = min(2.5, max(0.0, relative_strength.score * 20.0))
            setup_score = vol_score + rs_score

            row_item = MonitorRow(
                symbol=symbol,
                pct_change=float(snapshot_df[snapshot_df["symbol"] == symbol]["pct_change"].values[0]),
                trend=day_m.trend,
                rsi=five_m.rsi,
                volume_ratio=five_m.volume_ratio,
                sector=day_m.timeframe,  # placeholder
                sector_strength=sector_scores_map.get(day_m.timeframe, 0.0),
                buy_trigger=buy_trigger,
                sell_trigger=sell_trigger,
                setup_score=round(setup_score, 2),
            )

            # Bullish Continuation
            if day_m.trend == "BULLISH" and five_m.trend == "BULLISH" and five_m.rsi >= 52:
                monitor_lists["bullish_continuation"].append(row_item)

            # Bearish Continuation
            if day_m.trend == "BEARISH" and five_m.trend == "BEARISH" and five_m.rsi <= 48:
                monitor_lists["bearish_continuation"].append(row_item)

            # Near Breakout (within 1.5% of Daily or Weekly High)
            dist_to_pdh = (price_levels.prev_day_high - spot) / spot
            if 0 < dist_to_pdh <= 0.015:
                monitor_lists["near_breakout"].append(row_item)

            # Near Breakdown (within 1.5% of Daily or Weekly Low)
            dist_to_pdl = (spot - price_levels.prev_day_low) / spot
            if 0 < dist_to_pdl <= 0.015:
                monitor_lists["near_breakdown"].append(row_item)

            # Reversal Watch (RSI extreme)
            if five_m.rsi <= 30 or five_m.rsi >= 70:
                monitor_lists["reversal_watch"].append(row_item)

        except Exception as exc:
            logger.debug(f"Symbol scan failed for {symbol}: {exc}")

    # Sort all lists by setup_score descending
    for key in monitor_lists:
        monitor_lists[key] = sorted(monitor_lists[key], key=lambda r: r.setup_score, reverse=True)

    # 5. Print results
    print_evening_market_report(
        market_regime=regime,
        snapshot_df=snapshot_df,
        sector_summary=sector_summary_sorted,
        monitor_lists=monitor_lists,
        report_list_size=6,
    )

    # 6. Export results
    report_data = {
        "scanned_at": scan_time,
        "overall_bias": regime.overall_bias,
        "regime_label": regime.regime_label,
        "market_breadth": regime.market_breadth,
        "nifty_trend": regime.nifty_trend,
        "banknifty_trend": regime.banknifty_trend,
        "sectors": sector_summary_sorted,
        "monitor_lists": {
            key: [
                {
                    "symbol": r.symbol,
                    "pct_change": r.pct_change,
                    "trend": r.trend,
                    "rsi": r.rsi,
                    "volume_ratio": r.volume_ratio,
                    "setup_score": r.setup_score,
                }
                for r in rows
            ]
            for key, rows in monitor_lists.items()
        },
    }

    filepath = os.path.join("scanner_output", "evening_market_report.json")
    export_json_file(report_data, filepath)
    logger.info(f"Report exported to: {filepath}")


def main() -> None:
    try:
        kite = make_kite()
        instruments_df = load_instruments_df(kite)
        generate_evening_report(kite, instruments_df)
    except Exception as exc:
        logger.exception(f"Fatal error generating Evening Market Report: {exc}")


if __name__ == "__main__":
    main()
