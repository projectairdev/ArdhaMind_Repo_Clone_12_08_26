from __future__ import annotations

from typing import Dict, List, Tuple, Any
import pandas as pd

from src.config_engine import Config
from src.utils import setup_logger, now_str
from src.data_engine import (
    get_index_row,
    get_multi_timeframe_history,
    build_market_snapshot,
)
from src.indicator_engine import (
    compute_timeframe_metrics,
    detect_market_regime,
)
from src.models import MarketRegime

logger = setup_logger("MarketPipeline")


class MarketPipeline:
    def __init__(self):
        pass

    def run(self, kite, instruments_df: pd.DataFrame) -> Tuple[MarketRegime, pd.DataFrame, List[Dict[str, Any]]]:
        """
        Runs the full market analysis workflow:
        1. Analyzes NIFTY and BankNIFTY macro indices.
        2. Fetches and processes the overall market snapshot.
        3. Computes sector scores, breadth, and detects market regime.
        """
        scan_time = now_str()
        nifty_trend = "SIDEWAYS"
        banknifty_trend = "SIDEWAYS"

        # 1. Macro Index Trends
        try:
            nifty_row = get_index_row(instruments_df, "NIFTY 50")
            banknifty_row = get_index_row(instruments_df, "NIFTY BANK")

            nifty_candles = get_multi_timeframe_history(kite, int(nifty_row["instrument_token"]))["day"]
            banknifty_candles = get_multi_timeframe_history(kite, int(banknifty_row["instrument_token"]))["day"]

            nifty_m = compute_timeframe_metrics(
                df=nifty_candles,
                timeframe="day",
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )
            banknifty_m = compute_timeframe_metrics(
                df=banknifty_candles,
                timeframe="day",
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )
            nifty_trend = nifty_m.trend
            banknifty_trend = banknifty_m.trend
        except Exception as exc:
            logger.warning(f"Failed loading Nifty/BankNifty macro indices: {exc}")

        # 2. Build Universe Snapshot and compute Sectors
        snapshot_df = build_market_snapshot(kite, instruments_df)
        if snapshot_df.empty:
            logger.error("Empty market snapshot in pipeline.")
            # Return empty skeleton
            empty_regime = MarketRegime(
                scanned_at=scan_time,
                nifty_trend="SIDEWAYS",
                banknifty_trend="SIDEWAYS",
                overall_bias="SIDEWAYS",
                regime_score=0.0,
                regime_label="SIDEWAYS",
                market_breadth=0.5,
                strong_sectors=[],
                weak_sectors=[],
                sector_scores={},
                rationale="Fallback empty regime.",
            )
            return empty_regime, pd.DataFrame(), []

        # Sector calculation
        sector_gp = snapshot_df.groupby("sector")
        sector_summary_list = []
        sector_scores_map = {}

        for sector_name, group in sector_gp:
            avg_pct = float(group["pct_change"].mean())
            pos_count = int((group["pct_change"] > 0).sum())
            total_count = len(group)
            breadth = (pos_count / total_count) if total_count > 0 else 0.5
            sector_score = (avg_pct * 4.0) + ((breadth - 0.5) * 12.0)

            sector_summary_list.append(
                {
                    "sector": sector_name,
                    "avg_pct_change": round(avg_pct, 2),
                    "breadth": round(breadth, 2),
                    "sector_score": round(sector_score, 2),
                }
            )
            sector_scores_map[sector_name] = sector_score

        sector_summary_sorted = sorted(sector_summary_list, key=lambda s: s["sector_score"], reverse=True)
        strong_sectors = [s["sector"] for s in sector_summary_sorted if s["sector_score"] >= 2.0]
        weak_sectors = [s["sector"] for s in sector_summary_sorted if s["sector_score"] <= -2.0]

        # Overall Market Breadth
        pos_universe = int((snapshot_df["pct_change"] > 0).sum())
        market_breadth = round(pos_universe / len(snapshot_df), 2) if len(snapshot_df) > 0 else 0.5

        # Benchmark history for relative strength
        benchmark_history = None
        nifty_day_m = None
        try:
            nifty_row = get_index_row(instruments_df, "NIFTY 50")
            benchmark_history = get_multi_timeframe_history(kite, int(nifty_row["instrument_token"]))["day"]
            nifty_day_m = compute_timeframe_metrics(
                df=benchmark_history,
                timeframe="day",
                ema_fast_span=Config.EMA_FAST,
                ema_slow_span=Config.EMA_SLOW,
                rsi_period=Config.RSI_PERIOD,
                atr_period=Config.ATR_PERIOD,
                vol_avg_period=Config.VOL_AVG_PERIOD,
                breakout_vol_mult=1.0,
                entry_buffer_atr=Config.ENTRY_BUFFER_ATR,
            )
        except Exception:
            pass

        regime_timeframe_metrics = {"day": nifty_day_m} if nifty_day_m else {}
        regime = detect_market_regime(
            timeframe_metrics=regime_timeframe_metrics,
            market_breadth=market_breadth,
            snapshot_score=0.0,
            benchmark_return_pct=0.0,
        )

        regime.scanned_at = scan_time
        regime.nifty_trend = nifty_trend
        regime.banknifty_trend = banknifty_trend
        regime.strong_sectors = strong_sectors[:4]
        regime.weak_sectors = weak_sectors[:4]
        regime.sector_scores = sector_scores_map

        return regime, snapshot_df, sector_summary_sorted
