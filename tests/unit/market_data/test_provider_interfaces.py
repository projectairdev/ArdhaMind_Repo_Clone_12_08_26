from __future__ import annotations
import inspect
import pytest
from datetime import datetime, timezone, date
from typing import Callable, Sequence, Dict, Any

from src.market_data.interfaces.market_data_provider import IMarketDataProvider
from src.market_data.interfaces.historical_data_provider import IHistoricalDataProvider
from src.market_data.interfaces.option_chain_provider import IOptionChainProvider
from src.market_data.models.canonical_instrument import CanonicalInstrument
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.quality_enums import Exchange, Segment, InstrumentType, Timeframe


FORBIDDEN_EXECUTION_KEYWORDS = [
    "order", "place_order", "cancel_order", "modify_order",
    "buy", "sell", "trade", "execute", "exit_position",
    "funds", "margin", "portfolio", "holdings", "positions"
]


def test_interfaces_contain_no_trading_methods():
    for iface in [IMarketDataProvider, IHistoricalDataProvider, IOptionChainProvider]:
        methods = [name.lower() for name, _ in inspect.getmembers(iface, predicate=inspect.isfunction)]
        for m in methods:
            for forbidden in FORBIDDEN_EXECUTION_KEYWORDS:
                assert forbidden not in m, f"Interface {iface.__name__} violates read-only invariant with method: '{m}'"


def test_imarket_data_provider_cannot_instantiate_directly():
    with pytest.raises(TypeError):
        IMarketDataProvider()


def test_ihistorical_data_provider_cannot_instantiate_directly():
    with pytest.raises(TypeError):
        IHistoricalDataProvider()


def test_ioption_chain_provider_cannot_instantiate_directly():
    with pytest.raises(TypeError):
        IOptionChainProvider()


class MockMarketDataProvider(IMarketDataProvider):
    def __init__(self):
        self._connected = False
        self._handler = None
        self._subscribed = []

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, instruments: Sequence[CanonicalInstrument]) -> bool:
        self._subscribed.extend(instruments)
        return True

    def unsubscribe(self, instruments: Sequence[CanonicalInstrument]) -> bool:
        self._subscribed = [i for i in self._subscribed if i not in instruments]
        return True

    def set_tick_handler(self, handler: Callable[[CanonicalTick], None]) -> None:
        self._handler = handler

    def provider_name(self) -> str:
        return "MOCK_DHAN"


class MockHistoricalDataProvider(IHistoricalDataProvider):
    def fetch_candles(
        self,
        instrument: CanonicalInstrument,
        timeframe: Timeframe | str,
        start: datetime,
        end: datetime,
    ) -> Sequence[CanonicalCandle]:
        return [
            CanonicalCandle(
                canonical_instrument_id=instrument.canonical_id,
                provider="MOCK_DHAN",
                session_date=start.date(),
                timeframe=timeframe,
                start_timestamp=start,
                end_timestamp=end,
                open=24500.0,
                high=24520.0,
                low=24490.0,
                close=24510.0,
            )
        ]

    def provider_name(self) -> str:
        return "MOCK_DHAN"


class MockOptionChainProvider(IOptionChainProvider):
    def get_available_expiries(self, underlying: CanonicalInstrument) -> Sequence[str]:
        return ["2026-09-03", "2026-09-10", "2026-09-24"]

    def fetch_option_chain(self, underlying: CanonicalInstrument, expiry: str) -> Any:
        from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot, CanonicalOptionStrike, CanonicalOptionLeg
        from src.market_data.models.quality_enums import OptionType
        strike_leg = CanonicalOptionLeg(
            canonical_instrument_id=f"OPT:NFO:NIFTY:{expiry}:24500:CE",
            strike=24500.0,
            option_type=OptionType.CE,
            last_price=120.0,
        )
        strike_item = CanonicalOptionStrike(strike=24500.0, call=strike_leg)
        return CanonicalOptionChainSnapshot(
            underlying_instrument_id=underlying.canonical_id,
            underlying_price=24500.0,
            expiry=expiry,
            session_date=date(2026, 8, 28),
            captured_at=datetime.now(timezone.utc),
            provider="MOCK_DHAN",
            strikes=[strike_item],
        )

    def provider_name(self) -> str:
        return "MOCK_DHAN"


def test_mock_implementations():
    nifty = CanonicalInstrument(
        canonical_id="IDX:NSE:NIFTY_50",
        symbol="NIFTY 50",
        exchange=Exchange.NSE,
        segment=Segment.INDEX,
        instrument_type=InstrumentType.INDEX,
    )

    # Market Data Provider
    mdp = MockMarketDataProvider()
    assert not mdp.is_connected()
    assert mdp.connect()
    assert mdp.is_connected()
    assert mdp.subscribe([nifty])
    assert len(mdp._subscribed) == 1
    assert mdp.provider_name() == "MOCK_DHAN"

    # Historical Provider
    hdp = MockHistoricalDataProvider()
    start = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 28, 9, 16, 0, tzinfo=timezone.utc)
    candles = hdp.fetch_candles(nifty, Timeframe.M1, start, end)
    assert len(candles) == 1
    assert candles[0].canonical_instrument_id == "IDX:NSE:NIFTY_50"

    # Option Chain Provider
    ocp = MockOptionChainProvider()
    expiries = ocp.get_available_expiries(nifty)
    assert len(expiries) == 3
    chain = ocp.fetch_option_chain(nifty, expiries[0])
    assert chain.expiry == "2026-09-03"
