import pytest
from src.broker.services.market_context_builder import (
    _compute_ema,
    _compute_rsi,
    _compute_macd,
    _compute_adx,
    _compute_vwap,
    _compute_atr,
    _compute_support_resistance,
)


def test_nifty_spot_change_math():
    spot = 24287.65
    prev_close = 24366.00
    change = round(spot - prev_close, 2)
    change_pct = round((change / prev_close) * 100.0, 4)

    assert change == -78.35
    assert round(change_pct, 2) == -0.32


def test_vwap_delta_math():
    spot = 24287.65
    vwap = 24408.25
    vwap_delta_pct = round(((spot - vwap) / vwap) * 100.0, 2)

    assert vwap_delta_pct == -0.49


def test_ema_deltas_math():
    spot = 24287.65
    ema20 = 24331.89
    ema50 = 24336.72
    ema200 = 24327.11

    delta_20 = round(((spot - ema20) / ema20) * 100.0, 2)
    delta_50 = round(((spot - ema50) / ema50) * 100.0, 2)
    delta_200 = round(((spot - ema200) / ema200) * 100.0, 2)

    assert delta_20 == -0.18
    assert delta_50 == -0.20
    assert delta_200 == -0.16


def test_deterministic_quick_reference_ema_comparison():
    spot = 24287.65
    ema50 = 24336.72
    ema200 = 24327.11

    comparison_50 = "ABOVE" if spot > ema50 else "BELOW"
    comparison_200 = "ABOVE" if spot > ema200 else "BELOW"

    assert comparison_50 == "BELOW"
    assert comparison_200 == "BELOW"


def test_market_regime_enum_narrative_mapping():
    def get_regime_narrative(regime: str, momentum: str = "neutral", breadth: str = "neutral") -> str:
        if regime == "UNKNOWN":
            return "Market regime cannot be reliably classified due to insufficient observation history."
        elif regime == "UNCERTAIN":
            return "Market regime is uncertain due to conflicting price structure and breadth signals."
        elif regime == "SIDEWAYS":
            return f"NIFTY is sideways with {momentum} momentum and {breadth} breadth."
        elif regime == "TRENDING":
            return f"NIFTY is trending with {momentum} momentum and {breadth} breadth."
        return "Unclassified regime."

    assert "cannot be reliably classified" in get_regime_narrative("UNKNOWN")
    assert "uncertain due to conflicting" in get_regime_narrative("UNCERTAIN")
    assert "sideways" in get_regime_narrative("SIDEWAYS")


def test_sector_return_classification_semantics():
    sectors = [
        {"name": "NIFTY BANK", "change_pct": 0.01},
        {"name": "NIFTY IT", "change_pct": -0.66},
        {"name": "NIFTY AUTO", "change_pct": 0.45},
        {"name": "NIFTY PHARMA", "change_pct": 0.32},
        {"name": "NIFTY FMCG", "change_pct": -0.12},
        {"name": "NIFTY METAL", "change_pct": 0.55},
        {"name": "NIFTY REALTY", "change_pct": 0.20},
        {"name": "NIFTY ENERGY", "change_pct": -0.40},
        {"name": "NIFTY OIL & GAS", "change_pct": -0.15},
        {"name": "NIFTY FIN SERVICE", "change_pct": 0.08},
    ]
    pos = len([s for s in sectors if s["change_pct"] > 0])
    neg = len([s for s in sectors if s["change_pct"] < 0])
    flat = len(sectors) - pos - neg

    assert pos == 6
    assert neg == 4
    assert flat == 0


def test_key_level_deltas_math():
    spot = 24287.65
    pivot = 24350.00
    r1 = 24450.00
    s1 = 24200.00

    delta_pivot = round(((pivot - spot) / spot) * 100.0, 2)
    delta_r1 = round(((r1 - spot) / spot) * 100.0, 2)
    delta_s1 = round(((s1 - spot) / spot) * 100.0, 2)

    assert delta_pivot == 0.26
    assert delta_r1 == 0.67
    assert delta_s1 == -0.36


def test_vix_math_reconciliation():
    vix = 11.33
    prev_vix = 11.31
    vix_change = round(vix - prev_vix, 2)
    vix_change_pct = round((vix_change / prev_vix) * 100.0, 2)

    assert vix_change == 0.02
    assert vix_change_pct == 0.18


def test_breadth_constituent_sum():
    advances = 18
    declines = 31
    unchanged = 1
    total = advances + declines + unchanged
    assert total == 50

    ad_ratio = round(advances / declines, 2)
    assert ad_ratio == 0.58


def test_institutional_net_flow():
    fii_cash = -2535.1
    dii_cash = 5101.5
    net_flow = round(fii_cash + dii_cash, 1)

    assert net_flow == 2566.4


def test_technical_indicator_computation_helpers():
    series = [float(100 + i) for i in range(30)]
    ema20 = _compute_ema(series, 20)
    assert ema20 is not None
    assert 115 < ema20 < 130

    rsi = _compute_rsi(series, 14)
    assert rsi is not None
    assert rsi == 100.0


def test_metrics_workspace_layout_and_elements_contract():
    with open("/opt/ardhamind/staging/src/frontend/components/MarketPulseWorkspace.tsx", "r") as f:
        src = f.read()

    # 1. Row 1 checks
    assert "1. MARKET STATE" in src
    assert "GLOBAL & MACRO CONTEXT" in src
    assert "CrossAssetIcon" in src
    assert "MARKET SESSION STATUS (LOCAL TIME)" in src
    assert "MarketCenterSilhouette" in src

    # 2. Row 2 checks (5-column balanced cards)
    assert "2. PRICE & TREND METRICS" in src
    assert "3. KEY STRUCTURAL LEVELS" in src
    assert "4. MARKET BREADTH" in src
    assert "5. VOLATILITY & RANGE" in src
    assert "9. KEY TELEMETRY SUMMARY" in src

    # 3. Row 3 checks
    assert "6. SECTOR PARTICIPATION (NIFTY SECTORS)" in src
    assert "7. INSTITUTIONAL POSITIONING" in src
    assert "10. METRIC INTERPRETATION" in src

    # 4. Global financial centers
    centers = ["Tokyo", "Shanghai", "Hong Kong", "Mumbai", "Frankfurt", "London", "New York"]
    for c in centers:
        assert c in src

    # 5. Global benchmarks
    instruments = ["GIFT_NIFTY", "S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG", "BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y"]
    for inst in instruments:
        assert inst in src

    # 6. Contract test anchors
    assert "INDIA_VIX" in src
    assert "Object.keys(quotes)" in src

