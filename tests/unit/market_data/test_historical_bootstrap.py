from __future__ import annotations

import inspect
import json
import os
import shutil
import tempfile
from datetime import date, datetime, timezone
from typing import Sequence
import pytest

from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.quality_enums import (
    CandleQuality,
    Exchange,
    InstrumentType,
    Segment,
    Timeframe,
)
from src.market_data.services.historical_bootstrap_service import HistoricalBootstrapService


class MockHistoricalProvider(IHistoricalDataProvider):
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        s_date = start.date()
        t1 = datetime(s_date.year, s_date.month, s_date.day, 9, 15, 0, tzinfo=timezone.utc)
        t2 = datetime(s_date.year, s_date.month, s_date.day, 9, 16, 0, tzinfo=timezone.utc)
        return [
            CanonicalCandle(
                canonical_instrument_id=instrument.canonical_id,
                provider="MOCK_DHAN",
                session_date=s_date,
                timeframe=timeframe,
                start_timestamp=t1,
                end_timestamp=t2,
                open=24500.0,
                high=24520.0,
                low=24490.0,
                close=24510.0,
                volume=1000,
                oi=1200000,
                quality=CandleQuality.VALID,
            )
        ]

    def provider_name(self) -> str:
        return "MOCK_DHAN"


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="am_history_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_1_empty_directory_cold_start_and_fetch_missing(temp_dir: str):
    provider = MockHistoricalProvider()
    service = HistoricalBootstrapService(historical_provider=provider, storage_dir=temp_dir)

    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    s_date = date(2026, 8, 28)

    # 1. First bootstrap: fetches from provider and writes to disk
    results = service.bootstrap(instruments=[nifty], dates=[s_date], timeframes=[Timeframe.M1])
    key = f"IDX:NSE:NIFTY_50:1m:{s_date.isoformat()}"

    assert key in results
    assert len(results[key]) == 1
    assert results[key][0].open == 24500.0

    # Verify file was written to disk
    expected_file = os.path.join(temp_dir, "IDX_NSE_NIFTY_50", "1m", "2026-08-28.json")
    assert os.path.exists(expected_file)


def test_2_existing_validated_file_reused(temp_dir: str):
    provider = MockHistoricalProvider()
    service = HistoricalBootstrapService(historical_provider=provider, storage_dir=temp_dir)

    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    s_date = date(2026, 8, 28)

    # First fetch
    service.bootstrap(instruments=[nifty], dates=[s_date], timeframes=[Timeframe.M1])

    # Instantiate new service with provider=None (must load purely from disk)
    disk_only_service = HistoricalBootstrapService(historical_provider=None, storage_dir=temp_dir)
    loaded = disk_only_service.load_session_candles(nifty, s_date, Timeframe.M1)

    assert loaded is not None
    assert len(loaded) == 1
    assert loaded[0].close == 24510.0


def test_3_malformed_local_file_rejected(temp_dir: str):
    service = HistoricalBootstrapService(historical_provider=None, storage_dir=temp_dir)
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    s_date = date(2026, 8, 28)

    # Create corrupted JSON file on disk
    file_path = service._get_file_path(nifty.canonical_id, Timeframe.M1, s_date)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{ INVALID JSON CONTENT")

    loaded = service.load_session_candles(nifty, s_date, Timeframe.M1)
    assert loaded is None


def test_4_wrong_session_file_rejected(temp_dir: str):
    service = HistoricalBootstrapService(historical_provider=None, storage_dir=temp_dir)
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    s_date = date(2026, 8, 28)

    # Save payload with wrong internal session date
    file_path = service._get_file_path(nifty.canonical_id, Timeframe.M1, s_date)
    payload = {
        "canonical_instrument_id": nifty.canonical_id,
        "session_date": "2026-08-25",  # Mismatch
        "timeframe": "1m",
        "provider": "DHAN",
        "candles": [],
    }
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    loaded = service.load_session_candles(nifty, s_date, Timeframe.M1)
    assert loaded is None


def test_5_atomic_write(temp_dir: str):
    service = HistoricalBootstrapService(storage_dir=temp_dir)
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    s_date = date(2026, 8, 28)
    t1 = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)

    candle = CanonicalCandle(
        canonical_instrument_id=nifty.canonical_id,
        provider="DHAN",
        session_date=s_date,
        timeframe=Timeframe.M1,
        start_timestamp=t1,
        end_timestamp=t2,
        open=24500.0,
        high=24520.0,
        low=24490.0,
        close=24510.0,
    )

    service.save_session_candles(nifty, s_date, Timeframe.M1, "DHAN", [candle])

    # No leftover .tmp files
    dir_path = os.path.dirname(service._get_file_path(nifty.canonical_id, Timeframe.M1, s_date))
    files = os.listdir(dir_path)
    assert any(".tmp" in f for f in files) is False
    assert "2026-08-28.json" in files


def test_6_multiple_dates_and_timeframes(temp_dir: str):
    provider = MockHistoricalProvider()
    service = HistoricalBootstrapService(historical_provider=provider, storage_dir=temp_dir)

    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )
    dates = [date(2026, 8, 27), date(2026, 8, 28)]
    tfs = [Timeframe.M1, Timeframe.M5]

    results = service.bootstrap([nifty], dates=dates, timeframes=tfs)
    # Total 2 dates * 2 timeframes = 4 combinations
    assert len(results) == 4
    for key, c_list in results.items():
        assert len(c_list) == 1


def test_7_architectural_import_inspection():
    import src.market_data.services.historical_bootstrap_service as hbs_mod
    source = inspect.getsource(hbs_mod)
    forbidden = ["kiteconnect", "dhanhq", "src.broker", "src.frontend", "src.controlled_execution"]
    for f in forbidden:
        assert f"import {f}" not in source
        assert f"from {f}" not in source
