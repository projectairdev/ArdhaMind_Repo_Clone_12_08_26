from __future__ import annotations

import pytest

from src.analytics.breadth.breadth_engine import MarketBreadthEngine
from src.analytics.breadth.models import (
    ConstituentState,
    DivergenceType,
    LeadershipBias,
)
from src.market_data.models.quality_enums import DataQualityStatus


def test_1_full_universe_breadth_calculation():
    constituents = []
    # 35 advances (+1.0%), 10 declines (-1.0%), 5 unchanged (0.0%)
    for i in range(35):
        constituents.append(ConstituentState(symbol=f"STOCK_UP_{i}", last_price=100.0, change_pct=1.0))
    for i in range(10):
        constituents.append(ConstituentState(symbol=f"STOCK_DN_{i}", last_price=100.0, change_pct=-1.0))
    for i in range(5):
        constituents.append(ConstituentState(symbol=f"STOCK_FLAT_{i}", last_price=100.0, change_pct=0.0))

    summary = MarketBreadthEngine.calculate_breadth(constituents, total_universe_count=50)

    assert summary.total_constituents == 50
    assert summary.observed_constituents == 50
    assert summary.advances == 35
    assert summary.declines == 10
    assert summary.unchanged == 5
    assert summary.advance_pct == 70.0
    assert summary.advance_decline_ratio == 3.5
    assert summary.weighted_breadth_score > 0.0
    assert summary.quality == DataQualityStatus.VALID


def test_2_partial_and_missing_universe_breadth():
    # Partial universe: 30 stocks out of 50 (60% coverage) -> DELAYED quality
    constituents_30 = [ConstituentState(f"STOCK_{i}", 100.0, 0.5) for i in range(30)]
    summary_partial = MarketBreadthEngine.calculate_breadth(constituents_30, total_universe_count=50)
    assert summary_partial.coverage_pct == 60.0
    assert summary_partial.quality == DataQualityStatus.DELAYED

    # Severely degraded universe: 10 stocks out of 50 (20% coverage) -> UNAVAILABLE quality
    constituents_10 = [ConstituentState(f"STOCK_{i}", 100.0, 0.5) for i in range(10)]
    summary_poor = MarketBreadthEngine.calculate_breadth(constituents_10, total_universe_count=50)
    assert summary_poor.coverage_pct == 20.0
    assert summary_poor.quality == DataQualityStatus.UNAVAILABLE


def test_3_breadth_divergence_detection():
    # 1. Bearish Divergence: Index up +0.50% but only 10/50 advancing (20%)
    constituents_bearish = [ConstituentState(f"STOCK_{i}", 100.0, 0.5 if i < 10 else -0.5) for i in range(50)]
    summary_bear = MarketBreadthEngine.calculate_breadth(constituents_bearish, total_universe_count=50)
    div_bear = MarketBreadthEngine.evaluate_divergence(summary_bear, index_change_pct=0.50)

    assert div_bear.divergence == DivergenceType.BEARISH_DIVERGENCE
    assert "Narrow Leadership" in div_bear.note

    # 2. Bullish Divergence: Index down -0.50% while 40/50 advancing (80%)
    constituents_bullish = [ConstituentState(f"STOCK_{i}", 100.0, 0.5 if i < 40 else -0.5) for i in range(50)]
    summary_bull = MarketBreadthEngine.calculate_breadth(constituents_bullish, total_universe_count=50)
    div_bull = MarketBreadthEngine.evaluate_divergence(summary_bull, index_change_pct=-0.50)

    assert div_bull.divergence == DivergenceType.BULLISH_DIVERGENCE
    assert "Broad Accumulation" in div_bull.note


def test_4_heavyweight_leadership():
    # HDFCBANK, RELIANCE, ICICIBANK up; INFY down
    constituents = [
        ConstituentState("HDFCBANK", 1600.0, 1.2),
        ConstituentState("RELIANCE", 2900.0, 1.5),
        ConstituentState("ICICIBANK", 1200.0, 0.8),
        ConstituentState("INFY", 1800.0, -0.4),
        ConstituentState("TCS", 4200.0, 0.5),
    ]

    hw_ctx = MarketBreadthEngine.evaluate_heavyweights(constituents)
    assert hw_ctx.advances == 4
    assert hw_ctx.declines == 1
    assert hw_ctx.leadership_bias == LeadershipBias.BULLISH
    assert hw_ctx.contribution_score > 0.3
