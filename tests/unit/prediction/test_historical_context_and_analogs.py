from __future__ import annotations

from datetime import date, datetime, timezone
import pytest

from src.market_data.models.completed_session_snapshot import CompletedSessionSnapshot
from src.market_data.models.quality_enums import DataQualityStatus
from src.prediction.history.historical_context_engine import HistoricalContextEngine
from src.prediction.history.similar_session_finder import SimilarSessionFinder


def _make_historical_series() -> list[CompletedSessionSnapshot]:
    t_end = datetime(2026, 8, 28, 15, 30, 0, tzinfo=timezone.utc)
    snaps = []
    # 10 historical sessions from Aug 1 to Aug 14
    for i in range(1, 15):
        if i in (2, 3, 9, 10):  # Skip weekend dates
            continue
        d = date(2026, 8, i)
        snaps.append(
            CompletedSessionSnapshot(
                canonical_instrument_id="IDX:NSE:NIFTY_50",
                session_date=d,
                open=24000.0 + i * 20.0,
                high=24150.0 + i * 20.0,
                low=23980.0 + i * 20.0,
                close=24100.0 + i * 20.0,
                previous_close=24000.0 + (i - 1) * 20.0,
                absolute_change=100.0,
                percent_change=0.42,
                range=170.0,
                final_candle_timestamp=t_end,
                quality=DataQualityStatus.VALID,
            )
        )
    return snaps


def test_1_rolling_metrics_calculation():
    snaps = _make_historical_series()
    as_of = date(2026, 8, 20)

    roll_ctx = HistoricalContextEngine.compute_rolling_metrics(snaps, as_of_session_date=as_of)
    assert roll_ctx.sample_count == 10
    assert roll_ctx.rolling_5_avg_range == 170.0
    assert roll_ctx.rolling_20_avg_range == 170.0


def test_2_strict_lookahead_bias_prevention():
    """
    Ensures sessions on or after target session date are strictly excluded.
    """
    snaps = _make_historical_series()
    # As of Aug 7, only sessions before Aug 7 should be included
    as_of = date(2026, 8, 7)
    roll_ctx = HistoricalContextEngine.compute_rolling_metrics(snaps, as_of_session_date=as_of)

    # In our series, Aug 1, 4, 5, 6 are strictly before Aug 7 (4 sessions)
    assert roll_ctx.sample_count == 4


def test_3_similar_session_finder():
    snaps = _make_historical_series()
    as_of = date(2026, 8, 20)

    analogs = SimilarSessionFinder.find_analogs(
        historical_snapshots=snaps,
        as_of_session_date=as_of,
        current_regime="TREND_UP",
        current_range_estimate=170.0,
        limit=3,
    )

    assert len(analogs) == 3
    assert analogs[0].similarity_score >= 0.90
    assert analogs[0].observed_range_pts == 170.0
