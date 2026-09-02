from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pytest

from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_provenance import CanonicalProvenance, SourceType
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.completed_session_snapshot import (
    CompletedSessionSnapshot,
    FinalizationStage,
)
from src.market_data.models.quality_enums import (
    CandleQuality,
    DataQualityStatus,
    Timeframe,
)
from src.market_data.session.exchange_calendar import ExchangeCalendar
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.session.session_validator import SessionValidator

IST = ZoneInfo("Asia/Kolkata")


def test_1_wrong_session_tick_rejected():
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)
    validator = SessionValidator(authority)

    # Reference time: Friday 2026-08-28 10:00 AM IST (Active session is 2026-08-28)
    ref_time = datetime(2026, 8, 28, 10, 0, 0, tzinfo=IST)

    # Tick claiming session date 2026-08-27 (yesterday)
    stale_tick = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=ref_time - timedelta(days=1),
        received_at=ref_time,
        session_date=date(2026, 8, 27),
        last_price=24500.0,
    )

    res = validator.validate_tick(stale_tick, reference_time=ref_time)
    assert res.is_valid is False
    assert res.status == DataQualityStatus.SESSION_MISMATCH


def test_2_future_tick_rejected():
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)
    validator = SessionValidator(authority)

    ref_time = datetime(2026, 8, 28, 10, 0, 0, tzinfo=IST)
    # Tick with future timestamp (+1 hour)
    future_tick = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=ref_time + timedelta(hours=1),
        received_at=ref_time,
        session_date=date(2026, 8, 28),
        last_price=24500.0,
    )

    res = validator.validate_tick(future_tick, reference_time=ref_time)
    assert res.is_valid is False
    assert res.status == DataQualityStatus.REJECTED


def test_3_candle_on_non_trading_day_rejected():
    calendar = ExchangeCalendar()
    authority = CanonicalSessionAuthority(calendar)
    validator = SessionValidator(authority)

    ref_time = datetime(2026, 8, 29, 10, 0, 0, tzinfo=IST)  # Saturday

    # Candle claiming session date on Sunday 2026-08-23
    sunday_candle = CanonicalCandle(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        session_date=date(2026, 8, 23),  # Sunday
        timeframe=Timeframe.M1,
        start_timestamp=datetime(2026, 8, 23, 9, 15, 0, tzinfo=timezone.utc),
        end_timestamp=datetime(2026, 8, 23, 9, 16, 0, tzinfo=timezone.utc),
        open=24500.0,
        high=24510.0,
        low=24490.0,
        close=24505.0,
        quality=CandleQuality.VALID,
    )

    res = validator.validate_candle(sunday_candle, reference_time=ref_time)
    assert res.is_valid is False
    assert res.status == DataQualityStatus.SESSION_MISMATCH


def test_4_canonical_provenance_immutability_and_validation():
    now_utc = datetime.now(timezone.utc)
    prov = CanonicalProvenance(
        provider="DHAN",
        source_type=SourceType.WEBSOCKET,
        source_timestamp=now_utc,
        received_at=now_utc,
        session_date=date(2026, 8, 28),
        quality=DataQualityStatus.VALID,
    )

    assert prov.provider == "DHAN"
    assert prov.source_type == SourceType.WEBSOCKET
    assert prov.quality == DataQualityStatus.VALID

    # Reject naive timestamps
    with pytest.raises(ValueError):
        CanonicalProvenance(
            provider="DHAN",
            source_type=SourceType.WEBSOCKET,
            source_timestamp=datetime.now(),  # naive
            received_at=now_utc,
            session_date=date(2026, 8, 28),
        )


def test_5_completed_session_snapshot_staged_finalization():
    t_end = datetime(2026, 8, 28, 15, 30, 0, tzinfo=timezone.utc)
    snap = CompletedSessionSnapshot(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        session_date=date(2026, 8, 28),
        open=24500.0,
        high=24620.0,
        low=24480.0,
        close=24580.0,
        previous_close=24450.0,
        absolute_change=130.0,
        percent_change=0.53,
        range=140.0,
        final_candle_timestamp=t_end,
        quality=DataQualityStatus.VALID,
        finalization_stage=FinalizationStage.PRICE_FINAL,
    )

    assert snap.canonical_instrument_id == "IDX:NSE:NIFTY_50"
    assert snap.range == 140.0
    assert snap.finalization_stage == FinalizationStage.PRICE_FINAL

    # Invalid high < low rejected
    with pytest.raises(ValueError):
        CompletedSessionSnapshot(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            session_date=date(2026, 8, 28),
            open=24500.0,
            high=24400.0,  # Invalid
            low=24500.0,
            close=24500.0,
            previous_close=24450.0,
            absolute_change=50.0,
            percent_change=0.2,
            range=100.0,
            final_candle_timestamp=t_end,
        )
