"""Current dashboard presentation contracts."""
from pathlib import Path

ROOT = Path("src/frontend/components")
NIFTY = (ROOT / "NiftyLiveWorkspace.tsx").read_text(encoding="utf-8")
METRICS = (ROOT / "MarketPulseWorkspace.tsx").read_text(encoding="utf-8")
OPTIONS = (ROOT / "OptionsWorkspace.tsx").read_text(encoding="utf-8")


def test_nifty_is_continuous_and_structured():
    assert "setActiveTab" not in NIFTY and 'data-testid="nifty-live-tabs"' not in NIFTY
    for label in ("NIFTY 50", 'label="High"', 'label="Low"', 'label="Volume"', 'label="Value"', 'title="Key levels"', 'title="Market context"', 'title="Top gainers"', 'title="Top losers"'):
        assert label in NIFTY
    assert "<NiftyCandlestickChart" in NIFTY and "<SectorPerformanceChart" in NIFTY


def test_metrics_uses_master_refresh_without_direct_provider_calls():
    assert "await syncBroker(true)" in METRICS
    assert 'refreshState === "refreshing"' in METRICS
    for forbidden in ("fetch(", "axios.", "WebSocket(", "apiMacroRefresh", "apiNewsRefresh"):
        assert forbidden not in METRICS


def test_metrics_is_master_detail_workspace():
    assert "xl:grid-cols-[minmax(280px,35fr)_minmax(0,65fr)]" in METRICS
    for label in ("InstrumentCard", "Related Markets", "CompactObservationState", "SectorPerformanceChart"):
        assert label in METRICS


def test_options_has_no_presentation_tabs():
    assert "activeTab" not in OPTIONS and "setActiveTab" not in OPTIONS
    for retired in ("Unified Chain & Heatmap", "Option Chain Ladder", "OI Distribution Heatmap"):
        assert retired not in OPTIONS
    assert OPTIONS.index("<OptionChainLadder") < OPTIONS.index("<OpenInterestHeatmap")


def test_presentation_has_no_fabricated_market_constants():
    combined = NIFTY + METRICS + OPTIONS
    for fake in ("83.92", "102.50", "78.40", "2,450.00", "3.88%", "6.86%", "12.66"):
        assert fake not in combined
