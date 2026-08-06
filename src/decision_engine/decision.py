from __future__ import annotations

from typing import List, Union
from src.models import (
    OptionSignal,
    StockSignal,
    TradeRecommendation,
)


def compile_recommendations(
    symbol: str,
    asset_type: str,
    signals: List[Union[OptionSignal, StockSignal]],
    min_confidence: float,
) -> TradeRecommendation:
    """
    Processes a list of technical signals, sorts them, selects the primary high-confidence signal,
    and returns a TradeRecommendation.
    """
    valid_signals = [s for s in signals if s.confidence >= min_confidence]

    # Sort signals by:
    # 1. Confidence (descending)
    # 2. Reward-to-Risk ratio (descending)
    # 3. Capital required (ascending)
    sorted_signals = sorted(
        valid_signals,
        key=lambda s: (
            -s.confidence,
            -s.reward_risk_ratio,
            s.capital_required,
        ),
    )

    if sorted_signals:
        primary_signal = sorted_signals[0]
        watchlist_signals = sorted_signals[1:]
        action = "BUY" if getattr(primary_signal, "option_type", "CE") == "CE" or getattr(primary_signal, "side", "BUY") == "BUY" else "SELL_WATCHLIST"
        rationale = primary_signal.rationale
        confidence_score = primary_signal.confidence
    else:
        primary_signal = None
        watchlist_signals = sorted_signals
        action = "WATCHLIST"
        rationale = "No primary signal met the minimum confidence threshold."
        confidence_score = 0.0

    return TradeRecommendation(
        symbol=symbol,
        action=action,
        asset_type=asset_type,
        primary_signal=primary_signal,
        watchlist_signals=watchlist_signals,
        confidence_score=confidence_score,
        rationale=rationale,
    )
