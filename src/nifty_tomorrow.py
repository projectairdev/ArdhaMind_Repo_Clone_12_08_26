#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import pandas as pd

# Add src to python path if run as script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config_engine import Config
from src.utils import setup_logger, now_str
from src.utils.io_utils import export_json_file
from src.data_engine import (
    make_kite,
    load_instruments_df,
    get_index_row,
    get_multi_timeframe_history,
)
from src.pipeline import OptionPipeline
from src.strategies import get_strategy
from src.models import MarketRegime
from src.decision_engine import compile_recommendations
from src.ui import print_nifty_result

logger = setup_logger("NiftyTomorrow")


def scan_nifty_tomorrow(kite, instruments_df: pd.DataFrame) -> None:
    scan_time = now_str()
    logger.info("Initializing Nifty Trend & Option Scan...")

    try:
        index_row = get_index_row(instruments_df, "NIFTY 50")
        token = int(index_row["instrument_token"])
        benchmark_history = get_multi_timeframe_history(kite, token)["day"]
    except Exception as exc:
        logger.error(f"Failed looking up NIFTY 50 index token or fetching daily history: {exc}")
        return

    # Fetch spot price to determine baseline
    try:
        nifty_candles = get_multi_timeframe_history(kite, token)
        spot_price = float(nifty_candles["5minute"].iloc[-1]["close"])
    except Exception as exc:
        logger.error(f"Failed loading Nifty spot price: {exc}")
        return

    # Build local market regime for nifty scanner
    regime = MarketRegime(
        scanned_at=scan_time,
        nifty_trend="SIDEWAYS",
        banknifty_trend="SIDEWAYS",
        overall_bias="SIDEWAYS",
        regime_score=0.0,
        regime_label="SIDEWAYS",
        volatility_score=0.0,
        market_breadth=0.0,
        strong_sectors=[],
        weak_sectors=[],
        sector_scores={},
        rationale="Nifty single-index scanning session.",
    )

    pipeline = OptionPipeline()
    strategy = get_strategy("BreakoutTrendStrategy")
    option_signals = []

    # Check CE and PE options
    for opt_type in ["CE", "PE"]:
        sig, _ = pipeline.run_symbol(
            kite=kite,
            instruments_df=instruments_df,
            symbol="NIFTY",
            market_regime=regime,
            history_cache={},
            benchmark_history=benchmark_history,
            sector_vs_nifty_pct=0.0,
            scan_time=scan_time,
            strategy=strategy,
            is_index=True,
            forced_opt_type=opt_type,
        )
        if sig is not None:
            option_signals.append(sig)

    # Use Decision Engine to compile recommendations
    recommendation = compile_recommendations(
        symbol="NIFTY",
        asset_type="OPTION",
        signals=option_signals,
        min_confidence=Config.MIN_CONFIDENCE_TO_SHOW_OPTIONS,
    )

    print_nifty_result(recommendation, "=== NIFTY DIRECTIONAL OPTION FINDER ===")

    # Export Nifty report to file
    nifty_report_path = os.path.join("scanner_output", "nifty_tomorrow.json")
    export_json_file(
        {
            "scanned_at": scan_time,
            "nifty_spot": spot_price,
            "nifty_trend": recommendation.primary_signal.trend if recommendation.primary_signal else "SIDEWAYS",
            "confidence_score": recommendation.confidence_score,
            "action": recommendation.action,
            "rationale": recommendation.rationale,
            "primary_signal": recommendation.primary_signal.__dict__ if recommendation.primary_signal else None,
            "watchlist": [s.__dict__ for s in recommendation.watchlist_signals],
        },
        nifty_report_path,
    )
    logger.info(f"Nifty scanning report exported to {nifty_report_path}")


def main() -> None:
    try:
        kite = make_kite()
        instruments_df = load_instruments_df(kite)
        scan_nifty_tomorrow(kite, instruments_df)
    except Exception as exc:
        logger.exception(f"Fatal error running Nifty Tomorrow scan: {exc}")


if __name__ == "__main__":
    main()
