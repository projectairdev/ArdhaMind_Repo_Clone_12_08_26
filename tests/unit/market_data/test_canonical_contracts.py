from __future__ import annotations
import pytest
from datetime import date, datetime, timezone
from dataclasses import FrozenInstanceError

from src.market_data.models.quality_enums import (
    DataQualityStatus,
    CandleQuality,
    Exchange,
    Segment,
    InstrumentType,
    OptionType,
    Timeframe,
)
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.data_provenance import DataProvenance


def test_valid_nifty_instrument():
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=50,
        tick_size=0.05,
        provider_ids={"kite_token": 256265, "dhan_security_id": "13"},
    )
    assert nifty.canonical_id == "IDX:NSE:NIFTY_50"
    assert nifty.symbol == "NIFTY 50"
    assert nifty.exchange == Exchange.NSE
    assert nifty.segment == Segment.INDEX
    assert nifty.instrument_type == InstrumentType.INDEX
    assert nifty.provider_ids["kite_token"] == 256265
    assert nifty.provider_ids["dhan_security_id"] == "13"

    # Test immutability
    with pytest.raises(FrozenInstanceError):
        nifty.symbol = "MODIFIED"


def test_valid_vix_instrument():
    vix = CanonicalInstrument(
        canonical_id="IDX:NSE:INDIA_VIX",
        symbol="INDIA VIX",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        lot_size=1,
        tick_size=0.01,
        provider_ids={"kite_token": 264969},
    )
    assert vix.canonical_id == "IDX:NSE:INDIA_VIX"
    assert vix.symbol == "INDIA VIX"


def test_valid_option_instrument():
    opt = CanonicalInstrument(
        canonical_id="OPT:NFO:NIFTY:2026-09-03:CE:24500",
        symbol="NIFTY2690324500CE",
        exchange=Exchange.NFO,
        segment=Segment.OPTIONS,
        instrument_type=InstrumentType.CE,
        expiry=date(2026, 9, 3),
        strike=24500.0,
        option_type=OptionType.CE,
        lot_size=50,
        tick_size=0.05,
        provider_ids={"kite_token": 123456},
    )
    assert opt.canonical_id == "OPT:NFO:NIFTY:2026-09-03:CE:24500"
    assert opt.expiry == date(2026, 9, 3)
    assert opt.strike == 24500.0
    assert opt.option_type == OptionType.CE


def test_invalid_option_missing_expiry():
    with pytest.raises(ValueError, match="requires 'expiry'"):
        CanonicalInstrument(
            canonical_id="OPT:NFO:NIFTY:CE:24500",
            symbol="NIFTY24500CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            strike=24500.0,
            option_type=OptionType.CE,
        )


def test_invalid_option_missing_strike():
    with pytest.raises(ValueError, match="requires a positive numeric 'strike'"):
        CanonicalInstrument(
            canonical_id="OPT:NFO:NIFTY:2026-09-03:CE",
            symbol="NIFTY24500CE",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type=InstrumentType.CE,
            expiry=date(2026, 9, 3),
            option_type=OptionType.CE,
        )


def test_invalid_option_missing_option_type():
    with pytest.raises(ValueError, match="requires 'option_type'"):
        CanonicalInstrument(
            canonical_id="OPT:NFO:NIFTY:2026-09-03:24500",
            symbol="NIFTY24500",
            exchange=Exchange.NFO,
            segment=Segment.OPTIONS,
            instrument_type="OPTIONS",
            expiry=date(2026, 9, 3),
            strike=24500.0,
        )


def test_canonical_tick_valid():
    ts = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)
    recv_ts = datetime(2026, 8, 28, 9, 15, 30, 50000, tzinfo=timezone.utc)
    sess_date = date(2026, 8, 28)

    tick = CanonicalTick(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        exchange_timestamp=ts,
        received_at=recv_ts,
        session_date=sess_date,
        last_price=24510.50,
        open=24480.00,
        high=24520.00,
        low=24470.00,
        previous_close=24450.00,
        volume=150000,
        oi=12500000,
        bid=24510.45,
        ask=24510.55,
        internal_sequence=1,
    )
    assert tick.last_price == 24510.50
    assert tick.exchange_timestamp.tzinfo is not None
    assert tick.session_date == sess_date

    # Immutability
    with pytest.raises(FrozenInstanceError):
        tick.last_price = 24600.0


def test_canonical_tick_rejects_zero_or_negative_price():
    ts = datetime.now(timezone.utc)
    sess_date = date.today()

    with pytest.raises(ValueError, match="last_price' must be a positive number"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess_date,
            last_price=0.0,
        )

    with pytest.raises(ValueError, match="last_price' must be a positive number"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess_date,
            last_price=-10.5,
        )


def test_canonical_tick_rejects_naive_timestamp():
    naive_ts = datetime(2026, 8, 28, 9, 15, 30)  # No tzinfo
    with pytest.raises(ValueError, match="timezone-aware"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=naive_ts,
            received_at=datetime.now(timezone.utc),
            session_date=date.today(),
            last_price=24500.0,
        )


def test_canonical_tick_rejects_invalid_bid_ask():
    ts = datetime.now(timezone.utc)
    sess_date = date.today()

    # Negative bid
    with pytest.raises(ValueError, match="bid' cannot be negative"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess_date,
            last_price=24500.0,
            bid=-5.0,
        )

    # Ask less than bid
    with pytest.raises(ValueError, match="cannot be less than 'bid'"):
        CanonicalTick(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            exchange_timestamp=ts,
            received_at=ts,
            session_date=sess_date,
            last_price=24500.0,
            bid=24510.0,
            ask=24505.0,
        )


def test_canonical_candle_valid():
    start_ts = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    end_ts = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    sess_date = date(2026, 8, 28)

    candle = CanonicalCandle(
        canonical_instrument_id="IDX:NSE:NIFTY_50",
        provider="DHAN",
        session_date=sess_date,
        timeframe=Timeframe.M1,
        start_timestamp=start_ts,
        end_timestamp=end_ts,
        open=24500.0,
        high=24525.0,
        low=24495.0,
        close=24520.0,
        volume=5000,
        oi=1200000,
        quality=CandleQuality.VALID,
    )
    assert candle.open == 24500.0
    assert candle.high == 24525.0
    assert candle.low == 24495.0
    assert candle.close == 24520.0
    assert candle.quality == CandleQuality.VALID


def test_canonical_candle_ohlc_invariants():
    start_ts = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    end_ts = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    sess_date = date(2026, 8, 28)

    # High lower than Open
    with pytest.raises(ValueError, match="OHLC invariant violation"):
        CanonicalCandle(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            session_date=sess_date,
            timeframe=Timeframe.M1,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            open=24530.0,  # Open > High
            high=24520.0,
            low=24490.0,
            close=24500.0,
        )

    # Low higher than Close
    with pytest.raises(ValueError, match="OHLC invariant violation"):
        CanonicalCandle(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            session_date=sess_date,
            timeframe=Timeframe.M1,
            start_timestamp=start_ts,
            end_timestamp=end_ts,
            open=24510.0,
            high=24520.0,
            low=24505.0,  # Low > Close
            close=24500.0,
        )


def test_canonical_candle_invalid_timestamps():
    t1 = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    sess_date = date(2026, 8, 28)

    # start >= end
    with pytest.raises(ValueError, match="must be strictly before"):
        CanonicalCandle(
            canonical_instrument_id="IDX:NSE:NIFTY_50",
            provider="DHAN",
            session_date=sess_date,
            timeframe=Timeframe.M1,
            start_timestamp=t1,  # 9:16 >= 9:15
            end_timestamp=t2,
            open=24500.0,
            high=24510.0,
            low=24490.0,
            close=24505.0,
        )


def test_canonical_candle_quality_values():
    # Only VALID, BACKFILLED, MISSING are permitted
    assert CandleQuality.VALID.value == "VALID"
    assert CandleQuality.BACKFILLED.value == "BACKFILLED"
    assert CandleQuality.MISSING.value == "MISSING"

    # INTERPOLATED must not exist in CandleQuality
    with pytest.raises(AttributeError):
        _ = CandleQuality.INTERPOLATED


def test_data_provenance():
    prov = DataProvenance(
        provider="DHAN",
        source_timestamp=datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc),
        received_at=datetime(2026, 8, 28, 9, 15, 30, 20000, tzinfo=timezone.utc),
        session_date=date(2026, 8, 28),
        source_type="WEBSOCKET_TICK",
        request_id="REQ-12345",
    )
    assert prov.provider == "DHAN"
    assert prov.session_date == date(2026, 8, 28)
