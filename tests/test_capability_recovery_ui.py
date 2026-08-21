from pathlib import Path


ROOT = Path("src/frontend")


def source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_nifty_recovers_real_canonical_paths_without_fallback_values():
    code = source("components/NiftyLiveWorkspace.tsx")
    for path in ("breadth.top_gainers", "breadth.top_losers", 'dataset_type === "FII_CASH"',
                 'dataset_type === "DII_CASH"', "structural?.pivot_level?.price",
                 "news_intelligence?.overall_sentiment", "deterministic_risk?.risk_level"):
        assert path in code
    assert "12.66" not in code and "83.92" not in code and "78.40" not in code


def test_inspection_is_typed_contextual_and_deep_dive_is_conditional():
    code = source("context/MarketInspectionContext.tsx")
    for domain in ("market_context", "market_level", "institutional", "volatility", "breadth", "sector"):
        assert domain in code
    for detail in ("NIFTY relevance", "Market session", "Direction", "supportsDeepDive", "deepDiveEligible"):
        assert detail in code
    assert "historical_series" in code
    assert "{deepDiveEligible &&" in code
    assert 'aria-modal="true"' in code and "previousFocus" in code


def test_metrics_recovers_array_flows_and_sector_inspection():
    metrics = source("components/MarketPulseWorkspace.tsx")
    sectors = source("components/visualizations/SectorPerformanceChart.tsx")
    assert 'dataset_type === "FII_CASH"' in metrics
    assert 'dataset_type === "DII_CASH"' in metrics
    assert 'selected.kind === "institutional" ? "institutional"' in metrics
    assert 'domain: "sector"' in sectors and "openInspection" in sectors


def test_options_remains_continuous_and_exposes_validated_iv_snapshot():
    code = source("components/OptionsWorkspace.tsx")
    for label in ("NIFTY price & trend", "Options summary", "Option chain", "OI distribution",
                  "ATM IV", "CE / PE IV", "IV coverage"):
        assert label in code
    assert "activeTab" not in code and "sample" not in code.lower() and "mock" not in code.lower()
    assert "OptionChainLadder" in code and "OpenInterestHeatmap" in code


def test_existing_intelligence_journal_settings_and_phase3_boundary_remain_mounted():
    layout = source("layout/DashboardLayout.tsx")
    workspaces = source("components/PhaseOneWorkspaces.tsx")
    topbar = source("components/WorkstationTopBar.tsx")
    assert "<LiveAssistantWorkspace />" in layout
    assert "<NewsUpdatesWorkspace />" in layout
    assert "<SettingsWorkspace />" in layout
    assert "<IntradayAssistant />" in workspaces
    assert "<NewsIntelligence />" in workspaces
    assert "<SettingsDashboard />" in workspaces
    assert 'disabled title="Live Assistant — Phase 3, coming soon"' in topbar


def test_frontend_recovery_does_not_require_backend_contract_changes():
    inspection = source("context/MarketInspectionContext.tsx")
    assert "fetch(" not in inspection and "WebSocket" not in inspection
    assert "synthetic" not in inspection.lower() and "interpolat" not in inspection.lower()
