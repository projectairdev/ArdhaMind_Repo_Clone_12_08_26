import pytest
from pathlib import Path
from src.storage.lightweight_session_store import LightweightSessionStore

def test_mid_session_restart_recovery_restores_all_vital_fields(tmp_path: Path):
    """
    Simulates a mid-session crash and restart.
    Verifies that the lean recovery snapshot (~1 KB) restores spot, OHLC, VWAP,
    breadth, structural levels, and option context with 100% data fidelity.
    """
    store = LightweightSessionStore(tmp_path)
    
    # 1. State before crash at 11:30 IST
    pre_crash_state = {
        "market_data": {
            "current_spot": 24862.45,
            "open": 24810.00,
            "high": 24895.30,
            "low": 24790.15,
            "previous_close": 24780.00,
            "volume": 45200000,
            "vwap": 24845.80,
            "oi": 12850000,
            "change_points": 82.45,
            "change_pct": 0.33,
            "observed_at": "2026-08-28T06:00:00Z",
            "last_tick_time": "2026-08-28T06:00:00Z",
            "feed_health": "HEALTHY",
            "source_type": "WEBSOCKET_STREAM",
            "vix": 13.42,
            "breadth": {"advances": 32, "declines": 17, "unchanged": 1, "coverage": 50}
        },
        "market_session": {
            "phase": "LIVE",
            "is_open": True,
            "trading_date": "2026-08-28"
        },
        "structural_levels": {
            "pivot": 24800.0,
            "r1": 24900.0,
            "s1": 24700.0,
            "raw_atr_14": 118.5
        },
        "option_intelligence": {
            "underlying_price": 24862.45,
            "atm_strike": 24850,
            "pcr": 1.18,
            "pcr_volume": 1.05,
            "max_pain": 24800,
            "call_wall": 25000,
            "put_wall": 24500,
            "atm_iv": 13.85,
            "total_call_oi": 5200000,
            "total_put_oi": 6136000
        },
        "data_quality": {
            "status": "VALID",
            "freshness": "REALTIME"
        }
    }
    
    # 2. Persist recovery state
    persisted = store.persist_recovery_state(
        state=pre_crash_state,
        runtime_id="rt-crash-test-01",
        state_sequence=1420,
        session_date="2026-08-28",
        market_session_phase="LIVE"
    )
    assert persisted is True
    
    # Verify file footprint on disk
    snap_file = tmp_path / "cache" / "latest_canonical_state.json"
    assert snap_file.exists()
    snap_size_bytes = snap_file.stat().st_size
    assert snap_size_bytes < 2000, f"Snapshot size {snap_size_bytes} exceeds lean limit (target < 12 KB)"
    
    # 3. Simulate process reboot and reload state
    rebooted_store = LightweightSessionStore(tmp_path)
    recovery_snap = rebooted_store.load_recovery_state()
    
    assert recovery_snap is not None
    assert recovery_snap.runtime_id == "rt-crash-test-01"
    assert recovery_snap.state_sequence == 1420
    assert recovery_snap.session_date == "2026-08-28"
    assert recovery_snap.market_session_phase == "LIVE"
    
    restored = recovery_snap.state
    # Check Spot & OHLC & VWAP
    assert restored["market_data"]["current_spot"] == 24862.45
    assert restored["market_data"]["open"] == 24810.00
    assert restored["market_data"]["high"] == 24895.30
    assert restored["market_data"]["low"] == 24790.15
    assert restored["market_data"]["previous_close"] == 24780.00
    assert restored["market_data"]["vwap"] == 24845.80
    assert restored["market_data"]["vix"] == 13.42
    
    # Check Breadth
    assert restored["market_data"]["breadth"]["advances"] == 32
    assert restored["market_data"]["breadth"]["declines"] == 17
    
    # Check Structural Levels
    assert restored["structural_levels"]["pivot"] == 24800.0
    assert restored["structural_levels"]["raw_atr_14"] == 118.5
    
    # Check Option Context
    assert restored["option_intelligence"]["atm_strike"] == 24850
    assert restored["option_intelligence"]["pcr"] == 1.18
    assert restored["option_intelligence"]["max_pain"] == 24800
    assert restored["option_intelligence"]["call_wall"] == 25000
    assert restored["option_intelligence"]["put_wall"] == 24500
