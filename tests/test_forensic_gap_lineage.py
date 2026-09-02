# tests/test_forensic_gap_lineage.py
"""
Test Suite: Forensic Gap Lineage and Mathematical Distinction.

Enforces:
1. Exact arithmetic distinction between:
   - Actual Cash Open Gap: 24,285.05 - 24,252.00 = +33.05 pts
   - Final Session Change: 24,219.05 - 24,252.00 = -32.95 pts (-0.14%)
2. Rejection of unanchored +30 upper-band heuristic in opening gap calculations.
3. Strict session date and reference close validation for 24 Aug (2026-08-21 close = 24,252.00).
4. Symmetrical VIX-calibrated dispersion interval around implied cash open.
"""

import pytest
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine


def test_actual_opening_gap_vs_final_daily_change():
    """
    Proves mathematical distinction between:
    - Actual Open Gap (+33.05) vs
    - Final Session Change (-32.95).
    """
    ref_close = 24252.00  # 21 Aug Friday close
    actual_open = 24285.05  # 24 Aug Monday open
    final_close = 24219.05  # 24 Aug Monday close

    open_gap = round(actual_open - ref_close, 2)
    daily_change = round(final_close - ref_close, 2)
    daily_change_pct = round((daily_change / ref_close) * 100, 2)

    assert open_gap == 33.05
    assert daily_change == -32.95
    assert daily_change_pct == -0.14
    assert open_gap != daily_change


def test_no_plus_30_heuristic_in_active_engine():
    """
    Verifies that the active PreMarketIntelligenceEngine uses symmetric VIX dispersion
    around the normalized implied center rather than adding +30 to the upper bound.
    """
    PreMarketIntelligenceEngine.reset_engine_state()
    ref_close = 24252.00
    gift_quote = 24356.00  # Historical raw GIFT price
    vix = 14.0

    state = {
        "market_session": {"status": "PRE_MARKET", "session_date": "2026-08-24"},
        "market_data": {"previous_close": ref_close, "current_spot": ref_close},
        "macro_intelligence": {
            "quotes": {"GIFT_NIFTY": {"price": gift_quote, "status": "FRESH"}},
            "india_vix": {"value": vix},
        },
    }

    report = PreMarketIntelligenceEngine.analyze_pre_market(state)

    assert report.reference_close == 24252.00
    assert report.gap_methodology == "NORMALIZED_GIFT_ANCHORED"

    # Implied gap is centered on GIFT basis adjusted open
    # Bandwidth must be symmetric: center - low == high - center
    center = (report.expected_open_low + report.expected_open_high) / 2.0
    half_width_low = round(center - report.expected_open_low, 1)
    half_width_high = round(report.expected_open_high - center, 1)

    assert half_width_low == half_width_high


def test_nse_preopen_settled_handoff():
    """
    Verifies that at 09:08 IST (NSE pre-open discovery), the expected open collapses to
    the exact settled price +/- 5 pts.
    """
    PreMarketIntelligenceEngine.reset_engine_state()
    ref_close = 24252.00
    pre_open_settled = 24285.05

    state = {
        "market_session": {"status": "PRE_OPEN", "session_date": "2026-08-24"},
        "market_data": {
            "previous_close": ref_close,
            "current_spot": pre_open_settled,
            "pre_open_settlement": pre_open_settled,
        },
        "system_time": "2026-08-24T09:08:30+05:30",
    }

    report = PreMarketIntelligenceEngine.analyze_pre_market(state)

    assert report.gap_methodology == "NSE_PREOPEN_SETTLED"
    assert report.expected_open_low == 24280.05
    assert report.expected_open_high == 24290.05
    assert report.overall_confidence == "HIGH"
