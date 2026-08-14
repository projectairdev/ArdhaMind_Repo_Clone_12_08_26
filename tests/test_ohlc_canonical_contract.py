# tests/test_ohlc_canonical_contract.py
import json
from pathlib import Path
from src.broker.services.market_context_builder import MarketContextBuilder
from src.application.workstation_state_service import WorkstationStateService
from src.intelligence_engine.today_analysis_engine import TodayAnalysisEngine


class DummyBrokerService:
    def __init__(self, connected=True, quote_data=None):
        self._connected = connected
        self._quote = quote_data or {
            "NSE:NIFTY 50": {
                "last_price": 24366.00,
                "ohlc": {
                    "open": 24361.90,
                    "high": 24404.05,
                    "low": 24309.10,
                    "close": 24395.85
                }
            }
        }

    def is_connected(self):
        return self._connected

    def get_quote(self, symbols):
        return self._quote


class DummyOrchestrator:
    def __init__(self):
        self.latest_ticks = {
            "NSE:NIFTY 50": {
                "last_price": 24366.00,
                "volume": 0,
                "oi": 0,
                "timestamp": "2026-08-14T15:30:02Z"
            }
        }


def test_market_context_builder_extracts_ohlc_and_provenance():
    bs = DummyBrokerService(connected=True)
    orch = DummyOrchestrator()
    mc = MarketContextBuilder.build(bs, orch, india_vix=11.26)

    assert mc.get("current_spot") == 24366.00
    assert mc.get("open") == 24361.90
    assert mc.get("high") == 24404.05
    assert mc.get("low") == 24309.10
    assert mc.get("previous_close") == 24395.85
    assert mc.get("source_type") in ("WEBSOCKET_STREAM", "REST_POLL")


def test_14_aug_session_ohlc_reconstruction_from_history():
    hist_file = Path("data/cache/session_history_2026-08-14.json")
    if not hist_file.exists() or len(json.loads(hist_file.read_text()).get("snapshots", [])) == 0:
        hist_file = Path("data/cache/session_history_2026-08-13.json")
    assert hist_file.exists(), "Reference session file must exist"

    with open(hist_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    snaps = data.get("snapshots", [])
    assert len(snaps) > 0

    state = {
        "market_session": {"status": "CLOSED", "session_date": data.get("session_date", "2026-08-13"), "is_closed": True},
        "market_data": {"current_spot": 24395.85, "session_date": data.get("session_date", "2026-08-13"), "previous_close": 24395.85}
    }

    report = TodayAnalysisEngine.analyze(state, snaps)
    stats = report.session_statistics

    assert stats.get("close") is not None


def test_no_silent_fallback_to_spot_when_ohlc_missing():
    # State with no open/high/low and no snapshot history
    state = {
        "market_session": {"status": "OPEN", "session_date": "2026-08-14", "is_closed": False},
        "market_data": {"current_spot": 24366.0, "session_date": "2026-08-14"}
    }

    report = TodayAnalysisEngine.analyze(state, snapshot_history=[])
    stats = report.session_statistics

    # Missing OHLC values must remain None / unavailable, not silently become spot
    assert stats.get("open") is None
    assert stats.get("high") is None
    assert stats.get("low") is None
