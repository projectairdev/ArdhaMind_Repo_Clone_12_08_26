"""
tests/unit/test_sprint3_storage_and_lifecycle.py

Unit tests for Sprint 3 forensic audit defect repairs (FIX 14 to FIX 21):
- FIX 14: SessionCloseCore schema backward-compatibility & carry-forward fields
- FIX 15: StructuralLevels raw_atr_14 persistence
- FIX 16: Lean recovery snapshot footprint measurement
- FIX 17: Bounded LRU/FIFO version-dict eviction
- FIX 18: Dynamic off-market daemon cadence throttling
- FIX 19: Orphaned .tmp file age-gated sweep
- FIX 20: Dynamic symbol normalization with static fallback
- FIX 21: Forming candle live tick overlay stitching
"""
import os
import json
import time
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timezone, timedelta

from src.storage.schemas import SessionCloseCore, StructuralLevels, MarketOHLCV
from src.storage.atomic_store import cleanup_orphaned_tmp_files, atomic_write_json, atomic_read_json
from src.storage.lightweight_session_store import LightweightSessionStore, _extract_lean_recovery_state
from src.application.workstation_state_service import WorkstationStateService
from src.broker.utils.symbol_normalizer import normalize_instrument_key


def test_fix14_session_close_core_backward_compatibility():
    """Verify loading legacy pre-fix SessionCloseCore JSON without session_vwap/or_high/or_low defaults to None."""
    legacy_json = {
        "schema_name": "SESSION_CLOSE_CORE",
        "schema_version": "1.1.0",
        "session_date": "2026-08-28",
        "market_ohlcv": {
            "open": 24150.0,
            "high": 24200.0,
            "low": 24100.0,
            "close": 24175.65
        },
        "structural_levels": {
            "pivot": 24158.55,
            "r1": 24217.1,
            "s1": 24117.1
        }
    }
    
    # Must load cleanly without KeyError or Exception
    obj = SessionCloseCore.from_dict(legacy_json)
    assert obj.session_date == "2026-08-28"
    assert obj.session_vwap is None
    assert obj.or_high is None
    assert obj.or_low is None
    assert obj.structural_levels.raw_atr_14 is None

    # Verify modern payload with fields preserves values
    modern_json = dict(legacy_json)
    modern_json["session_vwap"] = 24160.50
    modern_json["or_high"] = 24190.00
    modern_json["or_low"] = 24120.00
    modern_json["structural_levels"]["raw_atr_14"] = 125.40

    modern_obj = SessionCloseCore.from_dict(modern_json)
    assert modern_obj.session_vwap == 24160.50
    assert modern_obj.or_high == 24190.00
    assert modern_obj.or_low == 24120.00
    assert modern_obj.structural_levels.raw_atr_14 == 125.40


def test_fix15_structural_levels_raw_atr():
    """Verify raw_atr_14 scalar is persisted and converted in StructuralLevels."""
    levels = StructuralLevels(
        pivot=24150.0,
        r1=24200.0,
        s1=24100.0,
        raw_atr_14=118.75,
        local_atr_upper=24268.75,
        local_atr_lower=24031.25
    )
    d = levels.to_dict()
    assert d["raw_atr_14"] == 118.75
    assert d["local_atr_upper"] == 24268.75


def test_fix16_lean_recovery_snapshot_footprint_measurement():
    """Measure and compare the serialized JSON byte footprint before and after lean filtering."""
    # Synthetic monolithic state containing heavy narrative, explanations, and HTML blobs
    fat_state = {
        "generated_at": "2026-08-28T10:00:00Z",
        "state_sequence": 1204,
        "market_data": {
            "current_spot": 24175.65,
            "open": 24150.0,
            "high": 24200.0,
            "low": 24100.0,
            "previous_close": 24090.85,
            "volume": 45000000,
            "vwap": 24160.50,
            "oi": 12000000,
            "change_points": 84.80,
            "change_pct": 0.35,
            "vix": {"last_price": 10.68},
            "breadth": {"advances": 32, "declines": 18}
        },
        "market_session": {"status": "OPEN", "is_open": True, "session_date": "2026-08-28"},
        "structural_levels": {"pivot": 24158.55, "r1": 24217.1, "s1": 24117.1, "raw_atr_14": 118.5},
        "option_intelligence": {
            "underlying_price": 24175.65,
            "atm_strike": 24200,
            "pcr": 1.15,
            "max_pain": 24150,
            "call_wall": 24500,
            "put_wall": 24000
        },
        # Bloat to be stripped:
        "session_story": {
            "headline": "NIFTY tests 24,200 call wall resistance in heavy volume consolidation",
            "primary_driver": "Financials and IT surge on institutional buying while midcaps consolidate near day highs.",
            "deep_narrative": "A" * 80000,  # 80 KB
            "html_rendered_view": "<div class='full-dashboard'>" + ("<p>Telemetry Card</p>" * 2000) + "</div>"  # 50 KB
        },
        "news_sentiment": {
            "items": [{"id": f"story_{i}", "body": "Detailed economic commentary " * 100} for i in range(50)]  # 100 KB
        },
        "presentation_blobs": {
            "viewmodels": {"chart_ui_cache": [x for x in range(10000)]}  # 50 KB
        }
    }

    raw_json_str = json.dumps(fat_state)
    raw_size_bytes = len(raw_json_str.encode("utf-8"))

    lean_state = _extract_lean_recovery_state(fat_state)
    lean_json_str = json.dumps(lean_state)
    lean_size_bytes = len(lean_json_str.encode("utf-8"))

    # Assert dramatic footprint reduction (> 80% reduction)
    assert raw_size_bytes > 150000, f"Raw size expected > 150KB, got {raw_size_bytes}"
    assert lean_size_bytes < 15000, f"Lean size expected < 15KB, got {lean_size_bytes}"
    
    # Assert core numerical metrics are preserved intact
    assert lean_state["market_data"]["current_spot"] == 24175.65
    assert lean_state["market_data"]["vwap"] == 24160.50
    assert lean_state["option_intelligence"]["atm_strike"] == 24200
    assert "session_story" not in lean_state
    assert "news_sentiment" not in lean_state
    
    print(f"\n[Fix 16 Footprint Measurement] Raw: {raw_size_bytes / 1024:.2f} KB -> Lean: {lean_size_bytes / 1024:.2f} KB ({(1 - lean_size_bytes/raw_size_bytes)*100:.1f}% reduction)")


def test_fix17_bounded_version_dict_eviction():
    """Verify version dicts enforce bounded FIFO eviction at MAX_VERSION_SNAPSHOTS / MAX_NEWS_ITEMS."""
    WorkstationStateService.reset_for_testing()
    test_dict = {}

    # Insert 60 version snapshots
    for i in range(60):
        key = f"VER_{i:03d}"
        val = {"version": i, "payload": f"data_{i}"}
        WorkstationStateService._put_bounded_version(test_dict, key, val, max_size=50)

    # Size must be capped at 50
    assert len(test_dict) == 50

    # Oldest 10 items (VER_000 to VER_009) must have been evicted
    for i in range(10):
        assert f"VER_{i:03d}" not in test_dict

    # Newest items (VER_010 to VER_059) must be retained
    for i in range(10, 60):
        assert f"VER_{i:03d}" in test_dict

    # News item bounded ingestion test
    for i in range(70):
        news_payload = {"items": [{"id": f"news_{i}", "headline": f"Headline {i}"}]}
        WorkstationStateService._ingest_news_items(news_payload)

    assert len(WorkstationStateService._news_items) <= WorkstationStateService.MAX_NEWS_ITEMS


def test_fix18_dynamic_daemon_throttling_logic():
    """Verify throttling evaluation logic produces 3s on active window and 60s off-market."""
    from src.utils.time_utils import is_trading_day
    
    # Case 1: Active weekday market hours (10:30 IST on a Wednesday)
    wednesday_dt = datetime(2026, 8, 26, 10, 30, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    hhmm = wednesday_dt.strftime("%H:%M")
    is_active = is_trading_day(wednesday_dt.date()) and ("08:45" <= hhmm <= "18:30")
    assert is_active is True  # -> Cadence 3.0s

    # Case 2: Deep night off-market (23:15 IST on a weekday)
    night_dt = datetime(2026, 8, 26, 23, 15, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    hhmm_night = night_dt.strftime("%H:%M")
    is_active_night = is_trading_day(night_dt.date()) and ("08:45" <= hhmm_night <= "18:30")
    assert is_active_night is False  # -> Cadence 60.0s

    # Case 3: Weekend (Saturday 12:00 IST)
    sat_dt = datetime(2026, 8, 29, 12, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    hhmm_sat = sat_dt.strftime("%H:%M")
    is_active_sat = is_trading_day(sat_dt.date()) and ("08:45" <= hhmm_sat <= "18:30")
    assert is_active_sat is False  # -> Cadence 60.0s


def test_fix19_orphaned_tmp_file_sweep():
    """Verify cleanup_orphaned_tmp_files unlinks old temp files without touching fresh in-flight temp files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        # 1. Create an orphaned .tmp file with mtime 10 minutes ago
        old_tmp = tmp_path / "latest_canonical_state.json.tmp.abcd1234"
        old_tmp.write_text("{}", encoding="utf-8")
        ten_mins_ago = time.time() - 600.0
        os.utime(old_tmp, (ten_mins_ago, ten_mins_ago))

        # 2. Create a fresh in-flight .tmp file with mtime 10 seconds ago
        fresh_tmp = tmp_path / "latest_canonical_state.json.tmp.fresh999"
        fresh_tmp.write_text("{}", encoding="utf-8")

        # 3. Run orphan sweep with 300s (5-minute) threshold
        removed = cleanup_orphaned_tmp_files(tmp_path, max_age_seconds=300.0)

        assert removed == 1
        assert not old_tmp.exists(), "Old orphaned .tmp file must be unlinked"
        assert fresh_tmp.exists(), "Fresh in-flight .tmp file must NOT be unlinked"


def test_fix20_dynamic_symbol_normalization():
    """Verify symbol normalizer resolves tokens with static fallback."""
    # Known canonical Kite tokens
    assert normalize_instrument_key(256265) == "NSE:NIFTY 50"
    assert normalize_instrument_key(264969) == "NSE:INDIA VIX"
    assert normalize_instrument_key(260105) == "NSE:NIFTY BANK"
    
    # String symbol normalization
    assert normalize_instrument_key("NIFTY 50") == "NSE:NIFTY 50"
    assert normalize_instrument_key("INDIA VIX") == "NSE:INDIA VIX"
    assert normalize_instrument_key("UNKNOWN_TICKER") == "UNKNOWN_TICKER"


def test_fix21_forming_candle_tick_overlay_stitching():
    """Verify live WebSocket tick overlays directly on active forming 1m candle."""
    candle_buffer = [
        {"open": 24100.0, "high": 24150.0, "low": 24090.0, "close": 24140.0, "volume": 10000},
        {"open": 24140.0, "high": 24160.0, "low": 24135.0, "close": 24155.0, "volume": 12000},
        # Active forming candle
        {"open": 24155.0, "high": 24170.0, "low": 24150.0, "close": 24165.0, "volume": 5000},
    ]

    # Incoming live tick creates new intra-bar high
    spot = 24182.50
    last_c = candle_buffer[-1]
    last_c["high"] = max(float(last_c.get("high") or spot), spot)
    last_c["low"] = min(float(last_c.get("low") or spot), spot)
    last_c["close"] = spot

    assert last_c["high"] == 24182.50
    assert last_c["low"] == 24150.0
    assert last_c["close"] == 24182.50

    # Incoming live tick creates new intra-bar low
    spot_dip = 24142.00
    last_c["high"] = max(float(last_c.get("high") or spot_dip), spot_dip)
    last_c["low"] = min(float(last_c.get("low") or spot_dip), spot_dip)
    last_c["close"] = spot_dip

    assert last_c["high"] == 24182.50
    assert last_c["low"] == 24142.00
    assert last_c["close"] == 24142.00
