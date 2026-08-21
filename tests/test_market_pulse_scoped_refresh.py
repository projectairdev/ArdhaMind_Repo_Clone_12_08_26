"""Dashboard restructure contract for MARKET / METRICS."""
from pathlib import Path

COMP = Path("src/frontend/components/MarketPulseWorkspace.tsx").read_text(encoding="utf-8")


def test_metrics_uses_authoritative_master_sync_only():
    assert "await syncBroker(true)" in COMP
    assert "apiMacroRefresh" not in COMP and "apiNewsRefresh" not in COMP and "fetch(" not in COMP
    assert 'refreshState === "refreshing"' in COMP and '"Refreshing…"' in COMP and '"Updated"' in COMP


def test_metrics_is_master_detail_with_sector_access():
    assert "xl:grid-cols-[minmax(280px,35fr)_minmax(0,65fr)]" in COMP
    assert "InstrumentCard" in COMP and "Related Markets" in COMP and "CompactObservationState" in COMP
    assert "SectorPerformanceChart" in COMP


def test_expected_cross_asset_rows_remain_visible_when_missing():
    for key in ("GIFT_NIFTY", "S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG", "INDIA_VIX", "USD_INR", "DXY", "BRENT_CRUDE", "GOLD", "US_10Y", "IN_10Y"):
        assert f'"{key}"' in COMP
    assert '"Unavailable"' in COMP


def test_additional_canonical_quotes_and_flows_are_retained():
    assert "Object.keys(quotes)" in COMP and "additional" in COMP
    assert '"FII Flow"' in COMP and '"DII Flow"' in COMP


def test_metrics_contains_no_hardcoded_market_numbers():
    for fake in ("83.92", "102.50", "78.40", "2,450.00", "3.88%", "6.86%", "12.66"):
        assert fake not in COMP
