from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.broker.services.instrument_service import InstrumentService
from src.broker.services.kite_intelligence_service import KiteIntelligenceService, SECTOR_INDEX_NAMES
from src.broker.services.market_feed_service import MarketFeedService
from src.broker.services.subscription_manager import SubscriptionManager


def equity(symbol: str, token: int) -> dict:
    return {"exchange": "NSE", "segment": "NSE", "tradingsymbol": symbol,
            "name": symbol, "instrument_token": token}


def index(name: str, token: int) -> dict:
    return {"exchange": "NSE", "segment": "INDICES", "tradingsymbol": name,
            "name": name, "instrument_token": token}


def option(strike: float, kind: str, token: int, expiry: str = "2099-08-11") -> dict:
    return {"exchange": "NFO", "segment": "NFO-OPT", "name": "NIFTY",
            "tradingsymbol": f"NIFTY99AUG{int(strike)}{kind}", "instrument_token": token,
            "instrument_type": kind, "expiry": expiry, "strike": strike,
            "lot_size": 65, "tick_size": 0.05}


class Orchestrator:
    latest_ticks = {}


class FakeBroker:
    def __init__(self, quotes=None):
        self.quotes = quotes or {}
        self.subscribed = []
        self.unsubscribed = []

    def is_connected(self): return True
    def is_stream_connected(self): return True
    def get_quote(self, keys): return {key: self.quotes[key] for key in keys if key in self.quotes}
    def _get_orchestrator(self): return Orchestrator()
    def subscribe_stream(self, symbols): self.subscribed.extend(symbols)
    def unsubscribe_stream(self, symbols): self.unsubscribed.extend(symbols)


@pytest.fixture
def instrument_service(monkeypatch):
    service = InstrumentService.get_instance()
    original = list(service._instruments)
    monkeypatch.setattr(service, "load_instruments", lambda *args, **kwargs: True)
    yield service
    service._build_indexes(original)


def test_constituent_resolution_requires_verified_membership(instrument_service):
    instruments = [equity("AAA", 1), equity("BBB", 2)]
    result = KiteIntelligenceService.resolve_constituents(instruments, ["AAA", "MISSING"])
    assert result["resolved_count"] == 1
    assert result["members"][0]["instrument_token"] == 1
    assert result["members"][1]["resolution_status"] == "UNRESOLVED"
    unavailable = KiteIntelligenceService.resolve_constituents(instruments)
    assert unavailable["reason"] == "kite_instrument_dump_does_not_include_index_membership"


def test_breadth_computation_and_insufficient_coverage():
    members = {"members": [{"symbol": f"S{i}", "trading_symbol": f"S{i}",
                            "resolution_status": "RESOLVED"} for i in range(50)]}
    quotes = {f"NSE:S{i}": {"last_price": 101 if i < 30 else 99,
                              "ohlc": {"close": 100}, "timestamp": "2026-08-07T15:30:00+05:30"}
              for i in range(50)}
    observed_now = datetime(2026, 8, 7, 10, 5, tzinfo=timezone.utc)
    result = KiteIntelligenceService.compute_breadth(members, quotes, now=observed_now)
    assert result["status"] == "READY"
    assert (result["advances"], result["declines"]) == (30, 20)
    assert result["advance_decline_ratio"] == 1.5
    partial = KiteIntelligenceService.compute_breadth(members, dict(list(quotes.items())[:39]), now=observed_now)
    assert partial["status"] == "PARTIAL"
    assert partial["advances"] is None


def test_e4c_resolution_is_exact_equity_only_and_duplicate_safe(instrument_service):
    instruments = [
        {**equity("AAA", 1), "instrument_type": "EQ"},
        {**equity("DUP", 2), "instrument_type": "EQ"},
        {**equity("DUP", 3), "instrument_type": "EQ"},
        {**equity("NOT-EQ", 4), "instrument_type": "BE"},
    ]
    membership = [{"symbol": "NSE:AAA", "isin": "INE0001"}, {"symbol": "DUP"},
                  {"symbol": "NOT-EQ"}, {"symbol": "UNKNOWN"}]
    result = KiteIntelligenceService.resolve_constituents(instruments, membership)
    assert result["membership_source"] == "NSE_INDICES_VERIFIED_CANONICAL"
    assert result["membership_count"] == 4 and result["expected_count"] == 50
    assert result["resolved_count"] == 1
    assert result["members"][0]["isin"] == "INE0001"
    assert result["members"][1]["resolution_reason"] == "DUPLICATE_NSE_EQ_SYMBOL_MATCH"
    assert result["members"][2]["resolution_reason"] == "NO_EXACT_NSE_EQ_SYMBOL_MATCH"
    assert all(row["resolution_status"] == "UNRESOLVED" for row in result["members"][1:])


def test_e4c_closed_session_observations_breadth_and_movers_need_no_weights():
    members = {"members": [{"symbol": f"S{i}", "trading_symbol": f"S{i}",
                            "resolution_status": "RESOLVED"} for i in range(50)]}
    quotes = {}
    for i in range(50):
        last = 102 if i < 20 else 98 if i < 40 else 100
        quotes[f"NSE:S{i}"] = {"last_price": last, "ohlc": {"close": 100},
                                "timestamp": "2026-08-07T15:30:00+05:30"}
    result = KiteIntelligenceService.compute_breadth(members, quotes, market_closed=True)
    assert result["status"] == "READY"
    assert (result["advances"], result["declines"], result["unchanged"]) == (20, 20, 10)
    assert result["coverage"] == {"valid": 50, "expected": 50, "minimum": 40}
    assert result["freshness"] == result["observation_mode"] == "LAST_VALID_SESSION"
    assert [row["symbol"] for row in result["top_gainers"]] == [f"S{i}" for i in range(5)]
    assert [row["symbol"] for row in result["top_losers"]] == [f"S{i}" for i in range(20, 25)]
    assert all(row["source"] == "Kite Quote API" for row in result["observations"])


def test_e4c_missing_and_stale_quotes_are_not_zero_or_live():
    members = {"members": [{"symbol": "AAA", "trading_symbol": "AAA", "resolution_status": "RESOLVED"},
                           {"symbol": "BBB", "trading_symbol": "BBB", "resolution_status": "RESOLVED"}]}
    quotes = {"NSE:AAA": {"last_price": 101, "ohlc": {"close": 100},
                           "timestamp": "2026-08-07T15:30:00+05:30"}}
    result = KiteIntelligenceService.compute_breadth(
        members, quotes, now=datetime(2026, 8, 9, tzinfo=timezone.utc))
    assert result["status"] == "UNAVAILABLE"
    assert result["coverage"]["valid"] == 0
    assert result["observations"] == []


def test_e4c_market_extensions_joins_canonical_membership_to_quotes(instrument_service):
    rows = [{**equity(f"S{i}", i + 1), "instrument_type": "EQ"} for i in range(50)]
    instrument_service._build_indexes(rows)
    quotes = {f"NSE:S{i}": {"last_price": 101, "ohlc": {"close": 100},
                              "timestamp": "2026-08-07T15:30:00+05:30"} for i in range(50)}
    metadata = {"is_available": True, "weights_status": "LICENSE_REQUIRED",
                "constituents": [{"symbol": f"S{i}"} for i in range(50)]}
    result = KiteIntelligenceService.build_market_extensions(FakeBroker(quotes), True, metadata)
    assert result["constituent_instruments"]["resolved_count"] == 50
    assert result["breadth"]["coverage"]["valid"] == 50
    assert result["breadth"]["status"] == "READY"
    assert len(result["breadth"]["observations"]) == 50


def test_sector_index_resolution_and_quotes(instrument_service):
    instrument_service._build_indexes([index(name, 1000 + i) for i, name in enumerate(SECTOR_INDEX_NAMES)])
    quotes = {f"NSE:{name}": {"last_price": 102, "ohlc": {"close": 100},
                               "timestamp": "2026-08-07T15:30:00+05:30"}
              for name in SECTOR_INDEX_NAMES}
    result = KiteIntelligenceService.build_sector_snapshot(FakeBroker(quotes), market_closed=True)
    assert result["resolved_count"] == 10
    assert result["quote_count"] == 10
    assert all(row["observation_mode"] == "LAST_SESSION" for row in result["sectors"])
    assert result["sectors"][0]["change_pct"] == 2


def test_option_resolution_infers_actual_spacing_and_nearest_expiry(instrument_service):
    rows = []
    token = 2000
    for strike in range(50, 326, 25):
        rows.extend([option(strike, "CE", token), option(strike, "PE", token + 1)])
        token += 2
    instrument_service._build_indexes(rows)
    service = MarketFeedService()
    result = service.resolve_option_contracts(FakeBroker(), 157)
    assert result["expiry"] == "2099-08-11"
    assert result["atm_strike"] == 150
    assert result["strike_step"] == 25
    assert result["strikes"] == [50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300]
    assert len(result["contracts"]) == 22


def test_real_snapshot_pcr_max_pain_oi_comparison_and_no_fake_iv(instrument_service, tmp_path):
    rows = []
    token = 3000
    for strike in range(50, 326, 25):
        rows.extend([option(strike, "CE", token), option(strike, "PE", token + 1)])
        token += 2
    instrument_service._build_indexes(rows)
    quotes = {}
    for item in rows:
        key = f"NFO:{item['tradingsymbol']}"
        quotes[key] = {"last_price": 10, "ohlc": {"close": 9}, "oi": 100 if item["instrument_type"] == "CE" else 200,
                       "volume": 50, "depth": {"buy": [{"price": 9.9}], "sell": [{"price": 10.1}]},
                       "timestamp": "2026-08-07T15:30:00+05:30", "last_trade_time": "2026-08-07T15:29:00+05:30"}
    broker = FakeBroker(quotes)
    service = MarketFeedService()
    service.SNAPSHOT_PATH = tmp_path / "snapshot.json"
    first = service.build_option_chain_context(broker, 157, ["2099-08-11"])
    assert first["status"] == "READY"
    assert first["pcr"] == 2
    assert first["max_pain"] in first["pcr_provenance"]["strike_window"]
    assert first["oi_change"]["status"] == "BASELINE_CREATED"
    assert first["oi_change"]["provenance"] == "SESSION_BASELINE"
    assert first["iv_status"] == "UNAVAILABLE"
    assert all(row["callIv"] is None and row["putIv"] is None for row in first["strikes"])
    assert first["last_valid_snapshot"] == "AVAILABLE"

    for quote in quotes.values():
        quote["oi"] += 10
        quote["timestamp"] = "2026-08-07T15:31:00+05:30"
    second = service.build_option_chain_context(broker, 157, ["2099-08-11"])
    assert second["oi_change"]["status"] == "AVAILABLE"
    assert all(row["oi_change"] == 10 for row in second["contracts"])

    broker.quotes = {}
    closed = service.build_option_chain_context(broker, 157, ["2099-08-11"])
    assert closed["last_valid_snapshot"] == "AVAILABLE"
    assert closed["status"] == "MARKET_CLOSED"


def test_max_pain_rejects_incomplete_chain():
    assert MarketFeedService.calculate_max_pain([{"strike": 100, "option_type": "CE", "oi": 10}]) is None


def test_duplicate_websocket_token_prevention(instrument_service):
    instrument_service._build_indexes([index("ALIAS", 999)])
    adapter = type("Adapter", (), {"calls": [], "subscribe": lambda self, tokens: self.calls.append(tokens),
                                    "unsubscribe": lambda self, tokens: None})()
    manager = SubscriptionManager(adapter)
    monkey = instrument_service.lookup_index_instrument
    instrument_service.lookup_index_instrument = lambda symbol: index(symbol, 999)
    try:
        assert manager.subscribe(["ALIAS", "SECOND_ALIAS"]) == [999]
        assert manager.get_active_tokens() == [999]
        assert adapter.calls == [[999]]
    finally:
        instrument_service.lookup_index_instrument = monkey
