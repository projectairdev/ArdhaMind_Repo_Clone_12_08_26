from pathlib import Path


ROOT = Path("src")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_visual_tokens_and_tabular_numbers_are_global():
    css = read("index.css")
    assert all(token in css for token in ("--air-bg", "--air-surface", "--air-line", "--air-positive", "--air-negative"))
    assert "font-variant-numeric: tabular-nums" in css


def test_reduced_motion_policy_is_explicit():
    css = read("index.css")
    assert "prefers-reduced-motion: reduce" in css
    assert "animation-duration: .01ms" in css


def test_flash_only_compares_genuine_numeric_updates():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "value !== previous.current" in text
    assert 'value > previous.current ? "air-flash-up" : "air-flash-down"' in text
    assert "setInterval" not in text


def test_market_closed_top_bar_indicator_is_static():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert "statusDot(!isClosedSession, isClosedSession)" in text
    assert 'active && !staticState ? "motion-safe:animate-pulse"' in text


def test_global_refresh_reuses_existing_canonical_sync():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert "await syncBroker(true)" in text
    assert "fetch(" not in text
    assert "if (syncing || refreshing) return" in text


def test_refresh_toasts_cover_started_completed_and_failed():
    text = read("frontend/components/WorkstationTopBar.tsx")
    for message in ("Checking canonical stream", "Canonical stream current", "Refresh failed"):
        assert message in text
    assert 'role="status"' in text


def test_notification_center_uses_current_canonical_states_and_deduplicated_ids():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert "news_intelligence?.provider_health" in text
    assert "macro_intelligence?.provider_health" in text
    assert 'id: "provider-summary"' in text and 'key={alert.id}' in text
    assert "fake" not in text.lower()


def test_notification_drawer_is_accessible_and_bounded():
    text = read("frontend/components/WorkstationTopBar.tsx")
    assert 'role="dialog"' in text and 'aria-label="Operational notifications"' in text
    assert "backdrop-blur-xl" in text and "max-h-80" in text


def test_sidebar_retains_six_workspaces_and_accessible_active_state():
    text = read("frontend/layout/DashboardLayout.tsx")
    assert text.count('{ id: "') == 6
    assert 'aria-current={active===item.id?"page":undefined}' in text
    assert "Decision intelligence only. Execution and order management are unavailable." not in text


def test_nifty_metrics_and_movers_use_dense_responsive_grids():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5" in text
    assert "Top constituent movers" in text and "Gainers" in text and "Losers" in text
    assert "sortedGainers" in text and "sortedLosers" in text and "rows.map" in text and "change_pct" in text


def test_no_mover_sparkline_without_real_series():
    text = read("frontend/components/NiftyLiveWorkspace.tsx")
    assert "sparkline" not in text.lower()
    assert "Math.random" not in text and "fake" not in text.lower()


def test_sector_rows_are_dense_and_last_session_metadata_is_preserved():
    text = read("frontend/components/visualizations/SectorPerformanceChart.tsx")
    assert "observation_mode" in text
    assert "grid-cols-[minmax(7rem,1fr)_5rem_5rem]" in text
    assert "h-1" in text


def test_premarket_risk_stream_has_operational_columns():
    text = read("frontend/components/PreMarketPlannerWorkspace.tsx")
    for heading in ("SEVERITY", "CATEGORY", "DEVELOPMENT", "TRANSMISSION", "TIME"):
        assert heading in text
    assert "overnightClusters" in text


def test_news_feed_uses_dense_rows_and_progressive_disclosure():
    text = read("frontend/components/NewsIntelligence.tsx")
    assert "why_it_matters" in text and "View details" in text
    assert "border-b border-[var(--air-line)] px-4 py-3" in text
    assert "published_at" in text and "source_name" in text


def test_c5_changes_are_presentation_only():
    changed_surfaces = [
        "index.css", "frontend/components/WorkstationTopBar.tsx",
        "frontend/layout/DashboardLayout.tsx", "frontend/components/NiftyLiveWorkspace.tsx",
        "frontend/components/NewsIntelligence.tsx", "frontend/components/PreMarketPlannerWorkspace.tsx",
    ]
    combined = "\n".join(read(path) for path in changed_surfaces)
    assert "UNIFIED_NIFTY_INTELLIGENCE_V1" not in combined
    assert "synthetic" not in combined.lower()
    assert "Math.random" not in combined
