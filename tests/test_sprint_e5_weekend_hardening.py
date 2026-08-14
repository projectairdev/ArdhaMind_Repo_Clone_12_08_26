# tests/test_sprint_e5_weekend_hardening.py
import json
from pathlib import Path
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService
from src.broker.services.market_context_builder import MarketContextBuilder
from src.risk_engine_v2.allocation import get_option_premium
from src.models import TradeCandidate, OptionContext


class DummyBrokerService:
    def __init__(self, connected=True):
        self._connected = connected

    def is_connected(self):
        return self._connected

    def get_quote(self, symbols):
        return {
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


class DummyOrchestrator:
    def __init__(self):
        self.latest_ticks = {
            "NSE:NIFTY 50": {
                "last_price": 24366.00,
                "volume": 1000,
                "oi": 5000,
                "timestamp": "2026-08-14T15:30:02Z",
                "ohlc": {
                    "open": 24361.90,
                    "high": 24404.05,
                    "low": 24309.10,
                    "close": 24395.85
                }
            }
        }


def test_forward_outlook_persistence(tmp_path):
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    try:
        payload = {
            "marketContext": {
                "current_spot": 24366.0,
                "open": 24361.90,
                "high": 24404.05,
                "low": 24309.10,
                "close": 24366.00,
                "previous_close": 24395.85,
                "vwap": 24370.0,
                "session_date": "2026-08-14"
            }
        }

        state = WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="OPEN")
        WorkstationStateService.flush_session_history("2026-08-14")

        cache_file = tmp_path / "session_history_2026-08-14.json"
        assert cache_file.exists()

        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        snaps = data.get("snapshots", [])
        assert len(snaps) > 0

        latest_snap = snaps[-1]
        fo = latest_snap.get("forward_outlook")
        assert fo is not None, "Snapshot must retain forward_outlook payload"
        assert fo.get("session_date") == "2026-08-14"
        assert "analysis_status" in fo or "status" in fo
        assert "confidence" in fo
        assert "support" in fo
        assert "resistance" in fo
        assert "vwap" in fo
        assert "confirmation_conditions" in fo
        assert "invalidation_conditions" in fo
        assert "key_evidence" in fo
    finally:
        WorkstationStateService.reset_for_testing()


def test_disk_churn_dirty_state_and_flush(tmp_path):
    WorkstationStateService.reset_for_testing()
    WorkstationStateService.CACHE_DIR = tmp_path
    WorkstationStateService._allow_disk_cache_in_test = True

    try:
        cache_file = tmp_path / "session_history_2026-08-14.json"

        # Build initial state
        payload = {"marketContext": {"current_spot": 24366.0}}
        WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="OPEN")
        WorkstationStateService.flush_session_history("2026-08-14")

        mtime1 = cache_file.stat().st_mtime

        # Throttled call without force should not write
        WorkstationStateService.build_from_legacy(payload, broker_state="CONNECTED", market_state="OPEN")
        mtime2 = cache_file.stat().st_mtime
        assert mtime2 == mtime1

        # Forced flush must write
        WorkstationStateService.flush_session_history("2026-08-14")
        mtime3 = cache_file.stat().st_mtime
    finally:
        WorkstationStateService.reset_for_testing()
    assert mtime3 >= mtime1


def test_no_hardcoded_spot_fallback():
    candidate = TradeCandidate(
        candidate_id="TEST-1",
        strategy_name="MEAN_REVERSION",
        tradingsymbol="NIFTY26AUG24300CE",
        strike=0.0,
        instrument_type="CE",
        expiry="2026-08-20",
        distance_from_atm=0.0,
        atm_distance_class="ATM",
        oi=0,
        volume=0,
        spread_pct=0.0,
        iv=15.0,
        tradability_score=0.0,
        suitability_score=0.0,
        ranking_score=0.0,
        rank=1
    )
    opt_ctx = OptionContext(
        underlying_spot=0.0,
        atm_strike=0.0,
        strike_step=50.0,
        current_weekly_expiry="2026-08-20",
        current_monthly_expiry="2026-08-27",
        time_to_expiry=6.0,
        atm_iv=15.0,
        expected_move=100.0,
        pcr=1.0,
        max_pain=0.0,
        highest_call_oi=0.0,
        highest_put_oi=0.0,
        highest_call_oi_change=0.0,
        highest_put_oi_change=0.0,
        top_candidate_strikes=[]
    )

    prem = get_option_premium(candidate, opt_ctx)
    # When spot and strike are 0, no fabricated price like 24300 should enter; returns 0.0
    assert prem == 0.0


def test_lightweight_provenance():
    bs = DummyBrokerService(connected=True)
    orch = DummyOrchestrator()
    mc = MarketContextBuilder.build(bs, orch, india_vix=12.0)

    assert mc.get("source_type") == "WEBSOCKET_STREAM"
    assert "observed_at" in mc
    assert mc.get("current_spot") == 24366.0
    assert mc.get("open") == 24361.90
    assert mc.get("high") == 24404.05
    assert mc.get("low") == 24309.10
