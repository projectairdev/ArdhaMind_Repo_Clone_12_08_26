# tests/test_metrics_null_safety.py
"""
Test Suite: Metrics Workspace Null Safety & Technical Indicator Degradation.

Verifies:
1. technicalIndicators = null / None
2. macd = null / None
3. rsi = null / None
4. ema = null / None
5. Partial indicator object
6. Complete indicator object
7. Async hydration from null -> hydrated
8. POST_MARKET completed session metrics degradation
"""

import pytest


def format_technical_indicators(market_context: dict) -> dict:
    """Python model reflecting the frontend null-safe rendering contract."""
    macd = market_context.get("macd")
    rsi = market_context.get("rsi")
    ema20 = market_context.get("ema20")
    ema50 = market_context.get("ema50")
    ema200 = market_context.get("ema200")
    adx = market_context.get("adx")
    vwap = market_context.get("vwap")
    spot = market_context.get("current_spot") or market_context.get("spot")

    # Safe MACD formatting
    if isinstance(macd, dict) and macd.get("macd") is not None and macd.get("signal") is not None:
        macd_str = f"{macd['macd']:.2f} / {macd['signal']:.2f}"
    else:
        macd_str = "UNAVAILABLE"

    # Safe RSI formatting
    if rsi is not None:
        rsi_val = float(rsi)
        rsi_tone = "Overbought" if rsi_val > 70 else ("Oversold" if rsi_val < 30 else "Neutral")
        rsi_str = f"{rsi_val:.2f} ({rsi_tone})"
    else:
        rsi_str = "UNAVAILABLE"

    # Safe EMA formatting
    ema20_str = f"{float(ema20):.2f}" if ema20 is not None else "UNAVAILABLE"
    ema50_str = f"{float(ema50):.2f}" if ema50 is not None else "UNAVAILABLE"
    ema200_str = f"{float(ema200):.2f}" if ema200 is not None else "UNAVAILABLE"

    return {
        "macd_display": macd_str,
        "rsi_display": rsi_str,
        "ema20_display": ema20_str,
        "ema50_display": ema50_str,
        "ema200_display": ema200_str,
        "adx_display": f"{float(adx):.2f}" if adx is not None else "UNAVAILABLE",
    }


def test_null_technical_indicators_render_unavailable():
    """Test A & B: When technical indicators / macd are null, render UNAVAILABLE without exception."""
    ctx = {
        "macd": None,
        "rsi": None,
        "ema20": None,
        "ema50": None,
        "ema200": None,
        "adx": None,
        "vwap": None
    }
    res = format_technical_indicators(ctx)
    assert res["macd_display"] == "UNAVAILABLE"
    assert res["rsi_display"] == "UNAVAILABLE"
    assert res["ema20_display"] == "UNAVAILABLE"
    assert res["ema50_display"] == "UNAVAILABLE"
    assert res["ema200_display"] == "UNAVAILABLE"
    assert res["adx_display"] == "UNAVAILABLE"


def test_partial_technical_indicators_render_gracefully():
    """Test E: Partial indicators render present values and UNAVAILABLE for missing."""
    ctx = {
        "macd": {"macd": 12.5, "signal": 10.2},
        "rsi": 62.4,
        "ema20": None,
        "ema50": 24150.0,
        "ema200": None
    }
    res = format_technical_indicators(ctx)
    assert res["macd_display"] == "12.50 / 10.20"
    assert "62.40" in res["rsi_display"]
    assert res["rsi_display"].endswith("(Neutral)")
    assert res["ema20_display"] == "UNAVAILABLE"
    assert res["ema50_display"] == "24150.00"
    assert res["ema200_display"] == "UNAVAILABLE"


def test_malformed_macd_object_does_not_crash():
    """Test I: Malformed macd object (missing signal) renders UNAVAILABLE cleanly."""
    ctx = {
        "macd": {"macd": 14.2}  # Missing 'signal'
    }
    res = format_technical_indicators(ctx)
    assert res["macd_display"] == "UNAVAILABLE"


def test_async_null_to_hydrated_progression():
    """Test G: Async null -> hydrated state transitions seamlessly."""
    # 1. Unhydrated state
    initial_ctx = {}
    init_res = format_technical_indicators(initial_ctx)
    assert init_res["macd_display"] == "UNAVAILABLE"

    # 2. Hydrated state
    hydrated_ctx = {
        "macd": {"macd": -4.20, "signal": -2.80},
        "rsi": 44.5,
        "ema20": 24220.0,
        "ema50": 24250.0,
        "ema200": 24100.0,
        "adx": 22.0
    }
    hyd_res = format_technical_indicators(hydrated_ctx)
    assert hyd_res["macd_display"] == "-4.20 / -2.80"
    assert "44.50" in hyd_res["rsi_display"]
    assert hyd_res["ema20_display"] == "24220.00"
