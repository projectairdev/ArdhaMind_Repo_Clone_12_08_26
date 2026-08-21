from pathlib import Path


ROOT = Path("src/frontend")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_brand_and_verified_membership_live_in_header_not_sidebar():
    header = read("components/WorkstationTopBar.tsx")
    layout = read("layout/DashboardLayout.tsx")
    assert "ArdhaMind" in header and "NIFTY 50 OFFICIAL MEMBERSHIP" not in header
    sidebar = layout.split("<aside", 1)[1].split("</aside>", 1)[0]
    assert "ArdhaMind" not in sidebar


def test_membership_uses_canonical_payload_and_progressive_disclosure():
    inspection = read("context/MarketInspectionContext.tsx")
    assert "membership_count" in inspection and "resolved_count" in inspection
    assert "constituents" in inspection and "supportsDeepDive" in inspection


def test_nifty_uses_grouped_metric_cards_and_zero_is_not_presented_as_volume():
    nifty = read("components/NiftyLiveWorkspace.tsx")
    for label in ("Change (Pts)", "Change (%)", "Volume", "Value", "Advance / Decline", "Market Breadth", "India VIX"):
        assert f'label="{label}"' in nifty
    assert "MetricCard" in nifty
    assert "Number(marketContext?.volume ?? market.volume) > 0" in nifty


def test_metrics_is_interactive_master_detail_with_truthful_history():
    metrics = read("components/MarketPulseWorkspace.tsx")
    assert "InstrumentCard" in metrics and "selectedKey" in metrics
    assert "35fr" in metrics and "65fr" in metrics
    assert "Related Markets" in metrics
    assert "CompactObservationState" in metrics
    assert "CanonicalSparkline" in metrics
    assert "await syncBroker(true)" in metrics and "fetch(" not in metrics


def test_semantic_palette_and_premium_surface_are_not_blue_dominant():
    primitives = read("components/ui/WorkspacePrimitives.tsx")
    css = read("../index.css")
    assert "rounded-xl" in primitives and "shadow-[" in primitives
    assert "#090909" in css and "#161616" in css
    assert "emerald" in primitives and "rose" in primitives and "amber" in primitives
    assert "--air-info: #34d399" in css
