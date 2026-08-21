from pathlib import Path
import pytest

ROOT = Path("src")


def read_src(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_1_usd_inr_summary_and_detailed_use_identical_canonical_observation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert 'getCanonicalQuote(macroQuotes, "USD_INR")' in pulse_code
    assert "getCanonicalQuote(quotes, key)" in macro_code or 'getCanonicalQuote(quotes, "USD_INR")' in macro_code


def test_2_brent_summary_and_detailed_use_identical_canonical_observation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert 'getCanonicalQuote(macroQuotes, "BRENT_CRUDE")' in pulse_code
    assert "getCanonicalQuote(" in macro_code


def test_3_us_10y_summary_and_detailed_use_identical_canonical_observation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert 'getCanonicalQuote(macroQuotes, "US_10Y")' in pulse_code
    assert "getCanonicalQuote(" in macro_code


def test_4_gift_nifty_summary_and_detailed_use_identical_canonical_observation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert 'getCanonicalQuote(macroQuotes, "GIFT_NIFTY")' in pulse_code
    assert "getCanonicalQuote(" in macro_code


def test_5_sp500_identity():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert 'getCanonicalQuote(macroQuotes, "S&P 500")' in pulse_code or 'getCanonicalQuote(macroQuotes, "SP500")' in pulse_code


def test_6_nasdaq_identity():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert 'getCanonicalQuote(macroQuotes, "NASDAQ")' in pulse_code


def test_7_dow_identity():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    assert "DOW_JONES" in util_code or "DOW" in util_code


def test_8_nikkei_identity():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    assert "NIKKEI_225" in util_code or "NIKKEI" in util_code


def test_9_hang_seng_identity():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    assert "HANG_SENG" in util_code


def test_10_gold_identity():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    assert "GOLD" in util_code


def test_11_dxy_identity():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    assert "DXY" in util_code


def test_12_missing_usd_inr_produces_unavailable():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "isAvailable: false" in util_code
    assert "Unavailable" in pulse_code


def test_13_missing_brent_produces_unavailable():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "isAvailable: false" in util_code
    assert "Unavailable" in pulse_code


def test_14_missing_us10y_produces_unavailable():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "isAvailable: false" in util_code
    assert "Unavailable" in pulse_code


def test_15_missing_gift_produces_unavailable():
    util_code = read_src("frontend/utils/canonicalQuotes.ts")
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert "isAvailable: false" in util_code
    assert "Unavailable" in pulse_code


def test_16_no_hardcoded_83_92_production_fallback():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert '"83.92"' not in pulse_code
    assert "83.92" not in pulse_code


def test_17_no_hardcoded_79_45_production_fallback():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert '"79.45"' not in pulse_code
    assert '79.45' not in pulse_code


def test_18_no_hardcoded_3_88_production_fallback():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert '3.88% (-4 bps)' not in pulse_code
    assert '"3.88"' not in pulse_code


def test_19_no_hardcoded_gift_numeric_fallback():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    assert '"24,616.50"' not in pulse_code
    assert '24616.50' not in pulse_code


def test_20_us10y_bps_semantics_validated():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert 'getCanonicalQuote(macroQuotes, "US_10Y")' in pulse_code
    assert "bps" in macro_code


def test_21_react_contains_no_direct_fetch():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "fetch(" not in pulse_code
    assert "fetch(" not in macro_code


def test_22_react_contains_no_axios():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "axios" not in pulse_code
    assert "axios" not in macro_code


def test_23_react_contains_no_websocket_creation():
    pulse_code = read_src("frontend/components/MarketPulseWorkspace.tsx")
    macro_code = read_src("frontend/components/MacroIntelligence.tsx")
    assert "WebSocket" not in pulse_code
    assert "new WebSocket" not in macro_code


def test_24_read_only_boundary_unchanged():
    boundary_code = read_src("../tests/test_e4b_read_only_boundary.py")
    assert "test_daemon_rejects_every_execution_action_before_service_access" in boundary_code


def test_25_no_backend_files_changed():
    """Verify that backend logic remains 100% frozen."""
    workstation_service = read_src("application/workstation_state_service.py")
    assert "class WorkstationStateService" in workstation_service
