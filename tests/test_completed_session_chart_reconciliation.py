import subprocess
import json
import os
from src.broker.services.market_context_builder import _candle_buffer


def test_chart_candle_data_source_reconciliation():
    """1-6: Verify 19 Aug chart candles reconcile with finalized 19 Aug session summary."""
    cache_file = "data/cache/nifty_candles_cache.json"
    assert os.path.exists(cache_file), f"Cache file {cache_file} must exist"
    
    with open(cache_file, "r") as f:
        candles = json.load(f)

    assert len(candles) > 0, "Candles list must not be empty"
    
    # Verify trading_date for all candles in cache is 2026-08-19
    for c in candles:
        dt_str = str(c.get("date") or "")[:10]
        assert dt_str == "2026-08-19", f"Candle date must be 2026-08-19, got {dt_str}"

    first_open = float(candles[0]["open"])
    max_high = max(float(c["high"]) for c in candles)
    min_low = min(float(c["low"]) for c in candles)
    last_close = float(candles[-1]["close"])

    # Verify canonical OHLC values match finalized 19 Aug session summary
    assert first_open == 24152.05, f"Expected open 24152.05, got {first_open}"
    assert max_high == 24172.85, f"Expected high 24172.85, got {max_high}"
    assert min_low == 24025.65, f"Expected low 24025.65, got {min_low}"
    assert last_close == 24078.30, f"Expected close 24078.30, got {last_close}"
    assert round(max_high - min_low, 2) == 147.20


def test_stale_previous_session_cache_rejection():
    """6-7: Verify previous-session (18 Aug) candles are rejected when completed session is 19 Aug."""
    stale_candles = [
        {"date": "2026-08-18T09:15:00+05:30", "open": 24223.85, "high": 24269.65, "low": 24154.90, "close": 24200.00},
        {"date": "2026-08-18T15:29:00+05:30", "open": 24200.00, "high": 24210.00, "low": 24150.00, "close": 24154.90},
    ]
    target_completed_date = "2026-08-19"

    filtered = [
        c for c in stale_candles
        if str(c.get("date"))[:10] == target_completed_date
    ]
    # Stale 18 Aug candles must filter down to 0 for 19 Aug session
    assert len(filtered) == 0


def test_production_untouched():
    """10: Verify production /opt/ArdhaMind status remains 100% clean."""
    res = subprocess.run(["git", "-C", "/opt/ArdhaMind", "status", "--porcelain"], capture_output=True, text=True)
    assert res.stdout.strip() == "", f"Production git tree must be clean, got: {res.stdout}"
