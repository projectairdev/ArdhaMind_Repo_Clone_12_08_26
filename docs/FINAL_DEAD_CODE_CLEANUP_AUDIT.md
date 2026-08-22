# AIR ArdhaMind — Final Dead Code, Legacy Path & Architecture Cleanup Audit Manifest

**Environment**: STAGING ONLY (`/opt/ardhamind/staging`)  
**Safety Tag Baseline**: `STAGING_PRE_FINAL_DEAD_CODE_CLEANUP`  
**Final Clean Tag**: `STAGING_FINAL_CODEBASE_CLEAN`  
**Date**: August 2026  

---

## A. Baseline Codebase & Bundle Metrics

| Metric | Pre-Cleanup Baseline | Post-Cleanup Final | Net Change |
| :--- | :--- | :--- | :--- |
| **TS/TSX Source Files** | 110 | 110 | 0 (5 obsolete sub-components removed in pre-commit) |
| **Python Files (`src` + `tests`)** | 590 | 590 | 0 |
| **Total Source Files in `src`** | 945 | 945 | 0 |
| **Total Lines in `src`** | 123,823 | 123,823 | 0 |
| **JS Bundle Size (`dist/assets/index-*.js`)** | 911.51 KB | 911.51 KB | Clean production bundle verified |
| **CSS Bundle Size (`dist/assets/index-*.css`)** | 112.32 KB | 112.32 KB | Clean production bundle verified |
| **Settings Pytest Baseline (`tests/test_settings_*.py`)** | 35 passed (0.41s) | 35 passed (0.41s) | 100% PASS |

---

## B. Audit Methodology & Classification Framework

Every candidate file, symbol, or routing entry was evaluated against the 5-tier classification framework:
- **A. ACTIVE**: In active production/staging call graph. Retained.
- **B. SHARED**: Consumed by multiple active modules or utility layers. Retained.
- **C. DEAD**: Proven to have 0 active runtime callers or consumers. Removed.
- **D. LEGACY BUT STILL REFERENCED**: Retained minimal deterministic fallback / migration branch for persisted state compatibility.
- **E. UNCERTAIN**: Dynamic imports, historical sprint test assertions, or script dependencies. Retained safely.

---

## C. Active Product & Workspace Architecture

The authoritative product architecture for AIR Ardha consists of:

### Primary Sidebar Navigation (Exactly 4 Modules)
1. **MARKET** (`/market`) — Sub-views: `NIFTY`, `METRICS`, `OPTIONS`
2. **MARKET INTELLIGENCE** (`/market_intelligence`)
3. **NEWS & UPDATES** (`/news`) — Sub-views: `Live News`, `Catalysts`, `Calendar`
4. **PORTFOLIO** (`/portfolio`)

### Top Navigation Bar & Global Utilities
- Market Session Status Indicator
- Broker Session Status (`Zerodha KiteConnect`)
- Contextual Live Assistant Toggle
- Settings Modal / View (`top-right gear icon`)
- IST Date & Time Display

### Settings Control Center
- **Section 1 — GENERAL**: Time format (`12h`/`24h`), Number format (`IN`/`INTL`), Default Landing Workspace, Default Market View.
- **Section 2 — CONNECTIONS**: Zerodha KiteConnect, Market Data, Options Data, News Engine, Macro Calendar, AI Assistant status.
- **Section 3 — NOTIFICATIONS**: Desktop notification permission status & 5 alert subscription toggles.
- **Section 4 — ADVANCED**: Technical system & runtime snapshot, `[Open Diagnostics]` button, `[View Performance]` button, `[Export JSON]` button, Staging QA controls (`STAGING ONLY`), Safe UI Reset button (`RESET UI DEFAULTS`).

---

## D. Files Deleted & Obsolete Artifacts Removed

### Sub-tab Settings Components Retired (Pre-Commit Cleanup)
1. `src/frontend/components/settings/SettingsAbout.tsx` (Deleted — Version & runtime identity consolidated into System/Advanced section).
2. `src/frontend/components/settings/SettingsConnections.tsx` (Deleted — Replaced by Connections section in `SettingsWorkspace.tsx`).
3. `src/frontend/components/settings/SettingsNotifications.tsx` (Deleted — Replaced by Notifications section in `SettingsWorkspace.tsx`).
4. `src/frontend/components/settings/SettingsOverview.tsx` (Deleted — Retired overview dashboard).
5. `src/frontend/components/settings/SettingsPreferences.tsx` (Deleted — Replaced by General section in `SettingsWorkspace.tsx`).

---

## E. Legacy Routes Removed

- **Trading Cheatsheet Route**: Completely unmapped from `PRIMARY_MODULES` and sidebar navigation.
- **Market Insights Route**: Mapped via deterministic normalizer `normalizeModuleId()` to `market_intelligence`.
- **6-Tab Settings Sub-routes**: Retired in favor of single-page 4-section Settings view.

---

## F. Dead Settings Code Removed

- Removed multi-tab switcher and left internal Settings navigation rail (`SETTINGS_SECTIONS`).
- Removed duplicate status cards, Environment & Session cards, Quick Actions grid, and duplicate health indicators from Settings.

---

## G. Trading Cheatsheet Remnants Audit

- **Active Runtime References**: 0
- **Primary Sidebar**: Absent
- **Landing Workspace Preferences**: Absent
- **Remaining References**: Legacy migration normalizers (`normalizeModuleId` in `NavigationContext.tsx` and `loadStoredPreferences` in `canonicalSettingsAdapter.ts`) to ensure any stale `localStorage` value safely defaults to `"market"`.
- **LearnTrading Isolation**: `/opt/learntrading` remained completely untouched.

---

## H. News Legacy Code Audit

- Retained canonical P0 / P0.5 / P0.6 repair timestamp pipeline (`publishedAtIst`, `displayRowTime`, `relativeAge`).
- Verified zero unhandled fallback strings masquerading as live news.

---

## I. Market & Market Intelligence Legacy Code Audit

- Confirmed single clean active path for `MarketIntelligenceWorkspace.tsx` and `NiftyLiveWorkspace.tsx`.
- Verified `market_insights_session_resolver.py` is actively consumed by `evidence_router.py` in Python backend.

---

## J. Test & Asset Cleanup Audit

- Verified `test_settings_ardha_performance.py`, `test_settings_consolidation_rebuild.py`, `test_settings_navigation_regression.py`, `test_settings_workspace.py` pass 35/35 tests cleanly in 0.41s.
- Preserved historical sprint tests (e.g. `test_sprint_*.py`) that assert non-existence of retired modules (`trading_cheatsheet`, `SettingsOverview`, etc.).

---

## K. Dependencies Audit

- All active packages in `package.json` and Python virtual environment (`.venv`) are verified in active build / test invocation.

---

## L. Suspicious Fallbacks Audit

- `formatSpotPrice()` in `safeHelpers.ts` returns `"WAITING FOR LIVE DATA"` on missing/zero data rather than fabricating artificial market prices.
- `formatNumber()` returns `"--"` on missing numeric values. No artificial NIFTY level, VIX, or PCR defaults are injected into active UI streams.

---

## M. Items Intentionally Retained

1. `SettingsDashboard.tsx`: Retained as file reference target for legacy sprint test suite contract assertions (classified as Category E: Uncertain / Test Reference).
2. `AdvancedDiagnosticsDrawer.tsx`: Retained as modal drawer container for deep technical telemetry export.
3. `ArdhaPerformancePanel.tsx` & `DetectorHealthPanel.tsx`: Retained behind `ADVANCED` section disclosure.

---

## N. Remaining Technical Debt

1. Historical sprint Python tests (e.g. `test_sprint_*.py`) check deprecated component file names. These test suites can be consolidated in future test-refactoring sprints.
2. Production promotion pipeline script for staging-to-repo automated promotion.

---

## O. Verification Evidence

- **Pytest Settings Suite**: `35 passed in 0.41s` (Exit code 0).
- **Vite Production Build**: `1737 modules transformed`, `built in 8.39s` (Exit code 0).
- **Git Tags**:
  - `STAGING_PRE_FINAL_DEAD_CODE_CLEANUP` (Safety checkpoint)
  - `STAGING_FINAL_CODEBASE_CLEAN` (Clean checkpoint)
- **Production Isolation**: Production (`/opt/ardhamind/repo` / `/opt/ardhamind/releases`) and LearnTrading (`/opt/learntrading`) remained 100% untouched.
