"""
tests/test_sprint_visual_assets.py

Sprint-specific tests for the visual asset and premium terminal enhancement sprint.

Tests cover:
- Removed membership badge
- Asset fallback system
- Missing-image handling  
- No fake market visualizations
- Zero-vs-unavailable semantics
- Mock/paper capability audit
- Component existence checks
"""
import subprocess
import os
import json
import re


STAGING_DIR = "/opt/ardhamind/staging"
FRONTEND_ASSETS_DIR = os.path.join(STAGING_DIR, "src/frontend/assets")
PUBLIC_ASSETS_DIR = os.path.join(STAGING_DIR, "public/assets")


# ─── 1. NIFTY 50 MEMBERSHIP BADGE REMOVAL ─────────────────────────────────────

class TestNiftyMembershipBadgeRemoved:
    """Verify the NIFTY 50 Official Membership badge was removed from the header."""

    def test_no_membership_badge_text(self):
        """No 'NIFTY 50 OFFICIAL MEMBERSHIP' text in WorkstationTopBar."""
        topbar_path = os.path.join(STAGING_DIR, "src/frontend/components/WorkstationTopBar.tsx")
        with open(topbar_path) as f:
            content = f.read()
        assert "NIFTY 50 OFFICIAL MEMBERSHIP" not in content, \
            "NIFTY 50 OFFICIAL MEMBERSHIP badge text still present in WorkstationTopBar"

    def test_no_shield_check_icon_in_topbar(self):
        """ShieldCheck icon no longer imported in WorkstationTopBar."""
        topbar_path = os.path.join(STAGING_DIR, "src/frontend/components/WorkstationTopBar.tsx")
        with open(topbar_path) as f:
            content = f.read()
        assert "ShieldCheck" not in content, \
            "ShieldCheck icon still imported in WorkstationTopBar (part of removed badge)"

    def test_no_membership_inspection_in_topbar(self):
        """openInspection for membership domain removed from WorkstationTopBar."""
        topbar_path = os.path.join(STAGING_DIR, "src/frontend/components/WorkstationTopBar.tsx")
        with open(topbar_path) as f:
            content = f.read()
        assert "openInspection" not in content, \
            "openInspection still referenced in WorkstationTopBar (used only for badge inspection)"

    def test_topbar_compiles(self):
        """WorkstationTopBar compiles without TS errors."""
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=STAGING_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, f"TypeScript compilation failed:\n{result.stdout}\n{result.stderr}"


# ─── 2. AUTHENTIC ASSET FILES ─────────────────────────────────────────────────

class TestAuthenticAssets:
    """Verify authentic market assets were downloaded and stored."""

    def test_asset_directory_exists(self):
        """Asset directory structure is created."""
        assert os.path.isdir(FRONTEND_ASSETS_DIR), f"Assets dir missing: {FRONTEND_ASSETS_DIR}"
        assert os.path.isdir(PUBLIC_ASSETS_DIR), f"Public assets dir missing: {PUBLIC_ASSETS_DIR}"

    def test_nasdaq_asset_downloaded(self):
        """NASDAQ SVG asset downloaded from Wikimedia Commons."""
        nasdaq_path = os.path.join(PUBLIC_ASSETS_DIR, "indices/nasdaq.svg")
        assert os.path.exists(nasdaq_path), "NASDAQ SVG asset not found"
        assert os.path.getsize(nasdaq_path) > 500, "NASDAQ SVG file is suspiciously small"

    def test_dow_jones_asset_downloaded(self):
        """Dow Jones SVG asset downloaded from Wikimedia Commons."""
        dj_path = os.path.join(PUBLIC_ASSETS_DIR, "indices/dow_jones.svg")
        assert os.path.exists(dj_path), "Dow Jones SVG asset not found"
        assert os.path.getsize(dj_path) > 200, "Dow Jones SVG file too small"

    def test_sp500_asset_downloaded(self):
        """S&P 500 SVG asset downloaded."""
        sp_path = os.path.join(PUBLIC_ASSETS_DIR, "indices/sp500.svg")
        assert os.path.exists(sp_path), "S&P 500 SVG asset not found"
        assert os.path.getsize(sp_path) > 500, "S&P 500 SVG too small"

    def test_nikkei_asset_downloaded(self):
        """Nikkei SVG asset downloaded."""
        nk_path = os.path.join(PUBLIC_ASSETS_DIR, "indices/nikkei.svg")
        assert os.path.exists(nk_path), "Nikkei SVG asset not found"

    def test_gold_commodity_asset_exists(self):
        """Gold photographic asset exists."""
        gold_path = os.path.join(PUBLIC_ASSETS_DIR, "commodities/gold.jpg")
        assert os.path.exists(gold_path), "Gold commodity asset not found"
        assert os.path.getsize(gold_path) > 1000, "Gold image file suspiciously small"

    def test_brent_commodity_asset_exists(self):
        """Brent crude photographic asset exists."""
        brent_path = os.path.join(PUBLIC_ASSETS_DIR, "commodities/brent_crude.jpg")
        assert os.path.exists(brent_path), "Brent crude asset not found"
        assert os.path.getsize(brent_path) > 1000, "Brent crude image suspiciously small"

    def test_manifest_exists(self):
        """Asset manifest documenting provenance exists."""
        manifest_path = os.path.join(FRONTEND_ASSETS_DIR, "MANIFEST.json")
        assert os.path.exists(manifest_path), "Asset MANIFEST.json not found"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert "assets" in manifest, "MANIFEST.json missing 'assets' array"

    def test_manifest_documents_sources(self):
        """Asset manifest documents source URLs."""
        manifest_path = os.path.join(FRONTEND_ASSETS_DIR, "MANIFEST.json")
        with open(manifest_path) as f:
            manifest = json.load(f)
        authenticated = [a for a in manifest["assets"] if a.get("status") == "downloaded"]
        assert len(authenticated) >= 5, \
            f"Only {len(authenticated)} authenticated assets — expected at least 5 from Wikimedia Commons"


# ─── 3. FALLBACK SYSTEM ───────────────────────────────────────────────────────

class TestAssetFallbackSystem:
    """Verify the fallback monogram system is implemented."""

    def test_instrument_monogram_component_exists(self):
        """InstrumentMonogram component exists in DataVisualizations."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        assert os.path.exists(viz_path), "DataVisualizations.tsx not found"
        with open(viz_path) as f:
            content = f.read()
        assert "InstrumentMonogram" in content, "InstrumentMonogram fallback component not found"

    def test_authentic_logo_fallback_to_monogram(self):
        """AuthenticMarketLogo falls back to InstrumentMonogram on error."""
        logo_path = os.path.join(STAGING_DIR, "src/frontend/components/ui/AuthenticMarketLogo.tsx")
        assert os.path.exists(logo_path), "AuthenticMarketLogo.tsx not found"
        with open(logo_path) as f:
            content = f.read()
        assert "InstrumentMonogram" in content, "Monogram fallback not referenced in AuthenticMarketLogo"
        assert "onError" in content, "onError handler (image load failure) not in AuthenticMarketLogo"
        assert "setFailed" in content, "Failed state not tracked for image fallback"

    def test_monogram_codes_defined(self):
        """Monogram codes defined for all key instruments."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        required_monograms = ["GN", "SPX", "NQ", "DJI", "N225", "HSI", "VIX", "BRN", "XAU", "10Y"]
        for mono in required_monograms:
            assert f'"{mono}"' in content, f"Monogram code '{mono}' not found in InstrumentMonogram"


# ─── 4. NO FAKE MARKET VISUALIZATIONS ────────────────────────────────────────

class TestNoFakeMarketData:
    """Verify no synthetic/fabricated market data in visualizations."""

    def test_no_random_in_visualization_components(self):
        """No Math.random() in visualization components."""
        viz_dir = os.path.join(STAGING_DIR, "src/frontend/components/visualizations")
        for fname in os.listdir(viz_dir):
            if fname.endswith(".tsx") or fname.endswith(".ts"):
                fpath = os.path.join(viz_dir, fname)
                with open(fpath) as f:
                    content = f.read()
                assert "Math.random()" not in content, \
                    f"Math.random() found in {fname} — may indicate fabricated market data"

    def test_no_fake_candles_in_visualizations(self):
        """No hard-coded fake candlestick data in visualization components."""
        viz_dir = os.path.join(STAGING_DIR, "src/frontend/components/visualizations")
        fake_patterns = [
            r'close:\s*\d{4,5}',  # Hard-coded close prices
            r'open:\s*\d{4,5}',   # Hard-coded open prices
        ]
        for fname in os.listdir(viz_dir):
            if fname.endswith(".tsx"):
                fpath = os.path.join(viz_dir, fname)
                with open(fpath) as f:
                    content = f.read()
                for pattern in fake_patterns:
                    matches = re.findall(pattern, content)
                    # Allow test fixtures but not inline fake data in component logic
                    # (max 2 matches for legitimate ATM strike examples etc.)
                    assert len(matches) < 3, \
                        f"Suspicious hard-coded prices in {fname}: {matches}"

    def test_data_visualizations_use_props_not_constants(self):
        """DataVisualizations components use props rather than hard-coded values."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        # Key viz functions should accept props (interface/type definitions)
        assert "MarketBreadthMeter" in content and "advances" in content, \
            "MarketBreadthMeter should accept 'advances' prop from canonical data"
        assert "DayRangeBar" in content and "current" in content, \
            "DayRangeBar should accept 'current' prop from canonical data"
        assert "VixGauge" in content and "value" in content, \
            "VixGauge should accept 'value' prop from canonical data"


# ─── 5. ZERO VS UNAVAILABLE SEMANTICS ────────────────────────────────────────

class TestZeroVsUnavailableSemantics:
    """Verify zero-vs-unavailable distinctions are properly implemented."""

    def test_global_cue_cards_not_observed_text(self):
        """GlobalCueCards uses NOT OBSERVED for null values, not 0 or Unavailable."""
        premarket_path = os.path.join(STAGING_DIR, "src/frontend/components/PreMarketPlannerWorkspace.tsx")
        with open(premarket_path) as f:
            content = f.read()
        assert "NOT OBSERVED" in content, \
            "PreMarketPlannerWorkspace should display NOT OBSERVED for unavailable cues"

    def test_compact_observation_state_exists(self):
        """CompactObservationState component exists to replace HISTORICAL CHART UNAVAILABLE."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        assert "CompactObservationState" in content, \
            "CompactObservationState not found — HISTORICAL CHART UNAVAILABLE not replaced"
        assert "Historical series" in content, \
            "Historical series message not in CompactObservationState"

    def test_metrics_uses_compact_observation_state(self):
        """MarketPulseWorkspace uses CompactObservationState instead of big empty box."""
        metrics_path = os.path.join(STAGING_DIR, "src/frontend/components/MarketPulseWorkspace.tsx")
        with open(metrics_path) as f:
            content = f.read()
        assert "CompactObservationState" in content, \
            "MarketPulseWorkspace still uses old HISTORICAL CHART UNAVAILABLE box"
        # Should NOT have the old big empty box
        assert "Historical chart unavailable" not in content, \
            "Old 'Historical chart unavailable' box still present — not replaced"


# ─── 6. MOCK/PAPER TRADING AUDIT ─────────────────────────────────────────────

class TestMockPaperTradingAudit:
    """Verify mock trading import removed from frontend components."""

    def test_no_mock_trade_journal_import_in_trading_journal(self):
        """TradingJournal no longer imports mockTradeJournal."""
        journal_path = os.path.join(STAGING_DIR, "src/frontend/components/TradingJournal.tsx")
        with open(journal_path) as f:
            content = f.read()
        assert "mockTradeJournal" not in content, \
            "mockTradeJournal still imported in TradingJournal — mock data import not removed"

    def test_no_mock_data_imports_in_production_ui_components(self):
        """No production UI components import from mockData services."""
        components_dir = os.path.join(STAGING_DIR, "src/frontend/components")
        violations = []
        for root, dirs, files in os.walk(components_dir):
            # Skip test directories
            dirs[:] = [d for d in dirs if not d.startswith("__")]
            for fname in files:
                if fname.endswith(".tsx") and not fname.startswith("test"):
                    fpath = os.path.join(root, fname)
                    with open(fpath) as f:
                        content = f.read()
                    if "from \"../services/mockData\"" in content or \
                       "from './mockData'" in content or \
                       "import.*mockData" in content:
                        violations.append(fpath)
        assert len(violations) == 0, \
            f"Production UI components still importing from mockData: {violations}"

    def test_mock_data_file_exists_for_tests(self):
        """mockData.ts still exists (needed for test fixtures, not UI components)."""
        mock_path = os.path.join(STAGING_DIR, "src/frontend/services/mockData.ts")
        assert os.path.exists(mock_path), \
            "mockData.ts was deleted — it should remain for test fixtures but not be imported by UI components"


# ─── 7. DATA VISUALIZATION COMPONENTS EXIST ──────────────────────────────────

class TestDataVisualizationComponents:
    """Verify all required visualization components were created."""

    def test_data_visualizations_file_exists(self):
        """DataVisualizations.tsx created with all required components."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        assert os.path.exists(viz_path), "DataVisualizations.tsx not created"

    def test_required_components_in_data_visualizations(self):
        """All sprint-required visualization components are present."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        required = [
            "MarketBreadthMeter",
            "DayRangeBar",
            "PriceLevelMap",
            "VixGauge",
            "InstitutionalFlowBars",
            "PerformanceBar",
            "GlobalSessionStrip",
            "CompactObservationState",
            "InstrumentMonogram",
        ]
        for component in required:
            assert component in content, f"Required component '{component}' not found in DataVisualizations.tsx"

    def test_nifty_workspace_uses_new_visualizations(self):
        """NiftyLiveWorkspace uses the new data visualization components."""
        nifty_path = os.path.join(STAGING_DIR, "src/frontend/components/NiftyLiveWorkspace.tsx")
        with open(nifty_path) as f:
            content = f.read()
        for component in ["PriceLevelMap", "DayRangeBar", "VixGauge", "MarketBreadthMeter", "InstitutionalFlowBars", "GlobalSessionStrip"]:
            assert component in content, f"NiftyLiveWorkspace missing {component}"

    def test_metrics_workspace_uses_new_visualizations(self):
        """MarketPulseWorkspace uses InstrumentVisual and CompactObservationState."""
        metrics_path = os.path.join(STAGING_DIR, "src/frontend/components/MarketPulseWorkspace.tsx")
        with open(metrics_path) as f:
            content = f.read()
        assert "InstrumentVisual" in content, "MarketPulseWorkspace not using InstrumentVisual"
        assert "CompactObservationState" in content, "MarketPulseWorkspace not using CompactObservationState"

    def test_options_workspace_has_visual_intelligence(self):
        """OptionsWorkspace has PCR gauge, ATM IV gauge, OI bars."""
        options_path = os.path.join(STAGING_DIR, "src/frontend/components/OptionsWorkspace.tsx")
        with open(options_path) as f:
            content = f.read()
        assert "PcrGauge" in content or "PCR" in content.upper(), "PCR gauge not in OptionsWorkspace"
        assert "AtmIvGauge" in content or "ATM IV" in content, "ATM IV visualization not in OptionsWorkspace"
        assert "OiConcentrationBars" in content or "OI Concentration" in content, "OI concentration bars not in OptionsWorkspace"

    def test_premarket_has_global_cue_cards(self):
        """PreMarketPlannerWorkspace has GlobalCueCards visual component."""
        premarket_path = os.path.join(STAGING_DIR, "src/frontend/components/PreMarketPlannerWorkspace.tsx")
        with open(premarket_path) as f:
            content = f.read()
        assert "GlobalCueCards" in content, "GlobalCueCards not found in PreMarketPlannerWorkspace"

    def test_performance_bars_in_movers(self):
        """NiftyLiveWorkspace Movers uses PerformanceBar."""
        nifty_path = os.path.join(STAGING_DIR, "src/frontend/components/NiftyLiveWorkspace.tsx")
        with open(nifty_path) as f:
            content = f.read()
        assert "PerformanceBar" in content, "PerformanceBar not found in NiftyLiveWorkspace Movers"


# ─── 8. GLOBAL SESSION STRIP ─────────────────────────────────────────────────

class TestGlobalSessionStrip:
    """Verify GlobalSessionStrip is implemented and not using fake geo data."""

    def test_global_session_strip_uses_known_exchanges(self):
        """GlobalSessionStrip uses real exchange names, not fabricated."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        real_markets = ["Tokyo", "Mumbai", "London", "New York", "Hong Kong"]
        for market in real_markets:
            assert market in content, f"Real market '{market}' not in GlobalSessionStrip"

    def test_global_session_uses_actual_time_calculation(self):
        """GlobalSessionStrip calculates open/closed from real UTC offsets."""
        viz_path = os.path.join(STAGING_DIR, "src/frontend/components/visualizations/DataVisualizations.tsx")
        with open(viz_path) as f:
            content = f.read()
        assert "utcOffset" in content or "UTC" in content, \
            "GlobalSessionStrip should use UTC offsets for time-accurate session status"
        assert "new Date()" in content or "Date.now()" in content, \
            "GlobalSessionStrip should use real current time, not hard-coded"


# ─── 9. TYPESCRIPT COMPILATION ────────────────────────────────────────────────

class TestTypeScriptCompilation:
    """Verify all changes compile cleanly."""

    def test_typescript_clean_compilation(self):
        """All modified files compile without TypeScript errors."""
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=STAGING_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, \
            f"TypeScript compilation has errors:\n{result.stdout}\n{result.stderr}"

    def test_vite_build_succeeds(self):
        """Vite production build completes successfully."""
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=STAGING_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, \
            f"Vite build failed:\n{result.stdout}\n{result.stderr}"


# ─── 10. PRODUCTION ISOLATION ─────────────────────────────────────────────────

class TestProductionIsolation:
    """Verify production environment is untouched."""

    def test_production_dir_not_modified(self):
        """No git changes in production directory."""
        prod_dir = "/opt/ArdhaMind"
        if not os.path.exists(prod_dir):
            return  # Production dir not present in this environment
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=prod_dir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode != 0 or result.stdout.strip() == "", \
            f"Production directory has uncommitted changes: {result.stdout}"

    def test_staging_branch_correct(self):
        """Staging is on ui/dashboard-restructure branch."""
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=STAGING_DIR,
            capture_output=True,
            text=True,
            timeout=10,
        )
        branch = result.stdout.strip()
        assert branch == "ui/dashboard-restructure", \
            f"Staging is on wrong branch: '{branch}' (expected 'ui/dashboard-restructure')"
