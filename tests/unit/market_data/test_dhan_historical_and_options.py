from __future__ import annotations

from datetime import date, datetime, timezone
import inspect
import time
import pytest

from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot
from src.market_data.models.quality_enums import Exchange, InstrumentType, OptionType, Segment, Timeframe
from src.market_data.providers.dhan.dhan_historical_provider import DhanHistoricalProvider
from src.market_data.providers.dhan.dhan_option_chain_provider import DhanOptionChainProvider
from src.market_data.services.instrument_master_service import InstrumentMasterService


@pytest.fixture
def nifty_instrument():
    return CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
        provider_ids={"DHAN": "13"},
    )


def test_1_historical_charts_normalization(nifty_instrument: CanonicalInstrument):
    start = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 28, 9, 17, 0, tzinfo=timezone.utc)

    # Dhan column-based response
    payload = {
        "open": [24500.0, 24510.0, 24520.0],
        "high": [24520.0, 24530.0, 24540.0],
        "low": [24490.0, 24500.0, 24510.0],
        "close": [24510.0, 24520.0, 24535.0],
        "volume": [1000, 1200, 1500],
        "start_Time": [
            int(datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc).timestamp()),
            int(datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc).timestamp()),
            int(datetime(2026, 8, 28, 9, 17, 0, tzinfo=timezone.utc).timestamp()),
        ],
    }

    provider = DhanHistoricalProvider()
    candles = provider.normalize_historical_payload(nifty_instrument, Timeframe.M1, payload, start, end)

    assert len(candles) == 3
    assert candles[0].open == 24500.0
    assert candles[0].close == 24510.0
    assert candles[0].volume == 1000
    assert candles[0].start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)


def test_2_historical_deduplication_and_range_filtering(nifty_instrument: CanonicalInstrument):
    start = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)

    # Contains an out-of-range candle (9:14) and duplicate candle (9:15 duplicate)
    payload = {
        "open": [24480.0, 24500.0, 24500.0, 24510.0],
        "high": [24490.0, 24520.0, 24520.0, 24530.0],
        "low": [24470.0, 24490.0, 24490.0, 24500.0],
        "close": [24490.0, 24510.0, 24510.0, 24520.0],
        "volume": [800, 1000, 1000, 1200],
        "start_Time": [
            int(datetime(2026, 8, 28, 9, 14, 0, tzinfo=timezone.utc).timestamp()),  # out of range
            int(datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc).timestamp()),
            int(datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc).timestamp()),  # duplicate
            int(datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc).timestamp()),
        ],
    }

    provider = DhanHistoricalProvider()
    candles = provider.normalize_historical_payload(nifty_instrument, Timeframe.M1, payload, start, end)

    # Out of range 9:14 discarded; duplicate 9:15 merged -> remaining 2 candles (9:15 and 9:16)
    assert len(candles) == 2
    assert candles[0].start_timestamp == datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    assert candles[1].start_timestamp == datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)


def test_3_option_chain_normalization(nifty_instrument: CanonicalInstrument):
    provider = DhanOptionChainProvider()

    raw_oc = {
        "data": {
            "last_price": 24550.0,
            "oc": {
                "24500.0": {
                    "ce": {
                        "last_price": 120.0,
                        "oi": 50000,
                        "volume": 20000,
                        "iv": 13.5,
                        "delta": 0.55,
                        "bid": 119.5,
                        "ask": 120.5,
                    },
                    "pe": {
                        "last_price": 65.0,
                        "oi": 80000,
                        "volume": 35000,
                        "iv": 14.1,
                        "delta": -0.45,
                        "bid": 64.5,
                        "ask": 65.5,
                    },
                },
                "24600.0": {
                    "ce": {
                        "last_price": 70.0,
                        "oi": 60000,
                        "volume": 25000,
                        "bid": 69.5,
                        "ask": 70.5,
                    }
                }
            }
        }
    }

    chain = provider.normalize_option_chain_payload(nifty_instrument, "2026-09-03", raw_oc)

    assert isinstance(chain, CanonicalOptionChainSnapshot)
    assert chain.underlying_instrument_id == "IDX:NSE:NIFTY_50"
    assert chain.underlying_price == 24550.0
    assert len(chain.strikes) == 2

    strike_24500 = chain.strikes[0]
    assert strike_24500.strike == 24500.0
    assert strike_24500.call is not None
    assert strike_24500.call.last_price == 120.0
    assert strike_24500.call.delta == 0.55
    assert strike_24500.put is not None
    assert strike_24500.put.last_price == 65.0

    strike_24600 = chain.strikes[1]
    assert strike_24600.strike == 24600.0
    assert strike_24600.call is not None
    assert strike_24600.put is None


def test_4_option_chain_rate_limiting():
    provider = DhanOptionChainProvider(
        min_request_interval_seconds=0.05,
        transport_fetcher=lambda params: {"data": {"last_price": 24500.0, "oc": {}}},
    )
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )

    t0 = time.perf_counter()
    # 3 calls for same expiry with min interval 0.05s should take >= 0.09s
    provider.fetch_option_chain(nifty, "2026-09-03")
    provider.fetch_option_chain(nifty, "2026-09-03")
    provider.fetch_option_chain(nifty, "2026-09-03")
    elapsed = time.perf_counter() - t0

    assert elapsed >= 0.09
    assert provider.total_requests_count == 3
    assert provider.throttled_requests_count >= 2

    # Check metrics
    last_req = provider.get_last_request_at("NIFTY", "2026-09-03")
    assert last_req is not None
    next_allowed = provider.get_next_allowed_at("NIFTY", "2026-09-03")
    assert next_allowed >= last_req

    # Different expiry has independent timestamp
    last_other = provider.get_last_request_at("NIFTY", "2026-09-10")
    assert last_other is None


def test_5_default_throttle_constant():
    provider = DhanOptionChainProvider()
    assert provider.DEFAULT_ENDPOINT_THROTTLE_SECONDS == 3.0
    assert provider.min_request_interval_seconds == 3.0


def test_6_architectural_import_inspection():
    import src.market_data.providers.dhan.dhan_historical_provider as dhp_mod
    import src.market_data.providers.dhan.dhan_option_chain_provider as docp_mod
    for mod in (dhp_mod, docp_mod):
        source = inspect.getsource(mod)
        forbidden = ["kiteconnect", "src.broker", "src.frontend", "src.controlled_execution"]
        for f in forbidden:
            assert f"import {f}" not in source
            assert f"from {f}" not in source
