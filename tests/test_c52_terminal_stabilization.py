from pathlib import Path


ROOT = Path("src/frontend")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_nifty_summary_is_compact_overview_only_and_not_generic():
    nifty = read("components/NiftyLiveWorkspace.tsx")
    views = read("components/UnifiedIntelligencePanel.tsx")
    for label in ('label="High"', 'label="Low"', 'label="Volume"', 'label="Value"', 'title="Key levels"', 'title="Market context"', 'title="Top gainers"', 'title="Top losers"'):
        assert label in nifty
    assert 'data-intelligence-view="compact-command-center"' in views
    assert "SESSION INTELLIGENCE" in views


def test_premarket_is_next_session_specific_without_session_review():
    pre = read("components/PreMarketPlannerWorkspace.tsx")
    views = read("components/UnifiedIntelligencePanel.tsx")
    assert "<PreMarketIntelligenceView" in pre
    assert 'data-intelligence-view="next-session-setup"' in views
    for label in ("Tomorrow's Market Setup", "GIFT Nifty", "Breadth", "Options", "Volatility", "News & Event Risk"):
        assert label in views


def test_analysis_alone_has_full_synthesis_and_dynamic_session_heading():
    views = read("components/UnifiedIntelligencePanel.tsx")
    assert 'data-intelligence-view="full-session-synthesis"' in views
    for heading in ("PRE-MARKET CONTEXT", "LIVE SESSION ANALYSIS", "SESSION REVIEW", "LAST SESSION / NEXT SESSION CONTEXT"):
        assert heading in views
    assert "analysisSessionHeading(session)" in views
    assert 'timeZone: "Asia/Kolkata"' in views and '["Sat", "Sun"]' in views


def test_live_assistant_is_an_explanation_console_not_generic_dashboard():
    views = read("components/UnifiedIntelligencePanel.tsx")
    assert "Understand ArdhaMind's View" in views
    for question in ("Current Market State", "Why?", "What Supports This View?", "What Goes Against It?", "What is the Risk?", "What Changed?", "What Data is Missing?"):
        assert question in views


def test_all_purpose_views_consume_one_canonical_field_without_frontend_reasoning():
    views = read("components/UnifiedIntelligencePanel.tsx")
    assert views.count("canonicalState?.unified_intelligence") == 1
    assert all(name in views for name in ("NiftyIntelligenceStrip", "PreMarketIntelligenceView", "TodaysAnalysisSynthesis", "LiveAssistantExplanationView"))
    assert "fetch(" not in views and "new WebSocket" not in views and "score =" not in views.lower()


def test_top_bar_separates_session_and_feed_without_duplicate_settings():
    top = read("components/WorkstationTopBar.tsx")
    assert "Market:" in top and "Broker:" in top
    assert "Live Assistant" in top and "Settings" in top
    assert "Notifications" not in top


def test_refresh_is_single_path_guarded_and_truthful():
    metrics = read("components/MarketPulseWorkspace.tsx")
    assert "await syncBroker(true)" in metrics and "fetch(" not in metrics
    assert "refreshing || loading" in metrics


def test_toasts_are_deduplicated_transient_and_not_render_loop_driven():
    top = read("components/WorkstationTopBar.tsx")
    assert "toast" not in top.lower()
    assert "setTimeout" not in top


def test_notifications_have_severity_timestamp_and_stable_keys():
    top = read("components/WorkstationTopBar.tsx")
    assert "Notifications" not in top and "Bell" not in top


def test_settings_provider_health_is_bounded_and_keyboard_scrollable():
    settings = read("components/SettingsDashboard.tsx")
    assert "data-provider-health-scroll" in settings
    assert "max-h-[28rem]" in settings and "overflow-y-auto" in settings
    assert 'tabIndex={0}' in settings and 'aria-label="Scrollable news and macro provider health"' in settings


def test_sidebar_remains_clean_and_settings_is_single_primary_path():
    layout = read("layout/DashboardLayout.tsx")
    assert "PRIMARY_MODULES" in layout and "settingsOpen ?" in layout
    assert "Decision intelligence only. Execution and order management are unavailable." not in layout


def test_option_chain_is_semantic_scrollable_and_structurally_valid():
    chain = read("components/visualizations/OptionChainLadder.tsx")
    assert 'aria-label="Scrollable NIFTY option chain"' in chain and 'tabIndex={0}' in chain
    assert "min-w-[52rem]" in chain
    assert all(label in chain for label in ("CALL OI", "STRIKE", "PUT OI"))
    assert chain.count("<table") == chain.count("</table>") == 1


def test_news_degradation_is_compact_and_event_filters_are_grouped():
    news = read("components/NewsIntelligence.tsx")
    assert "<details" in news and "Partial provider coverage" in news
    assert 'aria-label="Event date window"' in news
    assert 'aria-label="Event region and relevance filters"' in news
    assert '["TODAY", "TOMORROW", "THIS WEEK", "ALL"]' in news


def test_internal_engine_identifier_is_not_visible_text():
    views = read("components/UnifiedIntelligencePanel.tsx")
    assert "UNIFIED_NIFTY_INTELLIGENCE_V1" not in views
    assert "Engine:" not in views
    assert "data-intelligence-engine={intelligence.engine}" in views


def test_distinct_unavailable_semantics_remain_supported():
    presentation = read("components/intelligence/CanonicalPresentation.tsx")
    settings = read("components/SettingsDashboard.tsx")
    specialized = read("components/SpecializedIntelligence.tsx")
    assert "UNAVAILABLE" in presentation
    assert "Not configured" in settings and "LICENSE_REQUIRED" in specialized


def test_global_motion_accessibility_and_scrollbars_remain_controlled():
    css = Path("src/index.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion: reduce" in css
    assert "scrollbar-width: thin" in css
    assert "focus-visible" in css


def test_no_synthetic_chart_or_duplicate_fetch_is_added():
    paths = ("components/UnifiedIntelligencePanel.tsx", "components/NiftyLiveWorkspace.tsx", "components/PreMarketPlannerWorkspace.tsx")
    combined = "\n".join(read(path) for path in paths)
    assert "Math.random" not in combined and "sparkline" not in combined.lower()
    assert "fetch(" not in combined and "new WebSocket" not in combined
