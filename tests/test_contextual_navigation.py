import os
import re
import subprocess
from pathlib import Path

STAGING_ROOT = Path("/opt/ardhamind/staging")
FRONTEND_ROOT = STAGING_ROOT / "src" / "frontend"


def test_navigation_context_file_exists_and_no_hash_side_effects():
    nav_ctx = FRONTEND_ROOT / "context" / "NavigationContext.tsx"
    assert nav_ctx.exists(), "NavigationContext.tsx must exist"
    content = nav_ctx.read_text(encoding="utf-8")
    assert "navigateTo" in content, "NavigationContext must export navigateTo"
    assert "activeHighlightId" in content, "NavigationContext must handle activeHighlightId"
    
    # P1 & P10: Ensure no hash mutations or history pushState with hash
    assert "pushState" not in content, "NavigationContext must not call history.pushState"
    assert "location.hash =" not in content, "NavigationContext must not assign location.hash"
    assert "#${" not in content, "NavigationContext must not build hash fragment string"

    # P3 & P11/P12: Ensure no popstate / hashchange listeners for navigation
    assert "addEventListener(\"popstate\"" not in content, "popstate listener must be removed"
    assert "addEventListener(\"hashchange\"" not in content, "hashchange listener must be removed"

    # P4: Ensure one-time replaceState legacy hash cleanup exists
    assert "history.replaceState" in content, "Legacy hash cleanup on mount must use history.replaceState"


def test_top_bar_navigation_integration():
    top_bar = FRONTEND_ROOT / "components" / "WorkstationTopBar.tsx"
    assert top_bar.exists(), "WorkstationTopBar.tsx must exist"
    content = top_bar.read_text(encoding="utf-8")
    assert "useNavigation" in content, "WorkstationTopBar must use useNavigation"
    assert "market-nifty-session-summary" in content, "Market status must link to market-nifty-session-summary"
    assert "settings-connections-broker" in content, "Broker status must link to settings-connections-broker"


def test_stable_target_section_ids_registry():
    expected_ids = [
        "settings-connections-broker",
        "settings-diagnostics-market-feed",
        "market-nifty-session-summary",
        "market-metrics-vix",
        "market-metrics-breadth",
        "market-metrics-institutional",
        "market-metrics-sector",
        "market-metrics-structural",
        "market-options-pcr",
        "market-options-max-pain",
        "market-options-oi-walls",
        "intelligence-ai-opportunities",
        "intelligence-now-decision-levels",
        "intelligence-next-day-outlook",
        "pre-market-briefing-command-center",
        "news-live-feed",
        "news-catalysts",
        "performance-history",
    ]

    all_ts_content = ""
    for path in FRONTEND_ROOT.glob("**/*.tsx"):
        all_ts_content += path.read_text(encoding="utf-8") + "\n"

    for target_id in expected_ids:
        assert target_id in all_ts_content, f"Stable target section ID '{target_id}' must exist in frontend code"


def test_no_internal_href_hash_links():
    # Scan all TSX components for internal href="#..." or href="/#..."
    hash_href_pattern = re.compile(r'href=["\']/?#[^"\']*["\']')
    found_violations = []

    for path in FRONTEND_ROOT.glob("**/*.tsx"):
        content = path.read_text(encoding="utf-8")
        matches = hash_href_pattern.findall(content)
        if matches:
            found_violations.append((path.name, matches))

    assert not found_violations, f"Found internal hash href links: {found_violations}"


def test_deep_navigation_targets_and_scroll_highlight_preserved():
    nav_ctx = FRONTEND_ROOT / "context" / "NavigationContext.tsx"
    content = nav_ctx.read_text(encoding="utf-8")
    
    assert "scrollIntoView" in content, "scrollToSection must call scrollIntoView"
    assert "setActiveHighlightId" in content, "navigateTo must trigger pulse highlight"
    assert "requestAnimationFrame" in content, "Cross-workspace navigation timing must use requestAnimationFrame"


def test_live_assistant_and_portfolio_untouched_exclusion():
    # Verify LiveAssistant and Portfolio components were not refactored or modified by navigation
    portfolio = FRONTEND_ROOT / "components" / "PortfolioWorkspace.tsx"
    assert portfolio.exists(), "PortfolioWorkspace.tsx must exist"
    p_content = portfolio.read_text(encoding="utf-8")
    assert "useNavigation" not in p_content, "PortfolioWorkspace must remain untouched (0 navigation refactorings)"

    live_ast = STAGING_ROOT / "src" / "intelligence_engine" / "live_assistant_engine.py"
    if live_ast.exists():
        la_content = live_ast.read_text(encoding="utf-8")
        assert "navigateTo" not in la_content, "Live assistant backend must remain untouched"


def test_canonical_state_not_mutated_by_navigation():
    # Verify navigation context only mutates view state and not canonical state
    nav_ctx = FRONTEND_ROOT / "context" / "NavigationContext.tsx"
    content = nav_ctx.read_text(encoding="utf-8")
    assert "workstationState" not in content, "NavigationContext must not mutate backend workstationState"
    assert "/api/" not in content, "NavigationContext must not trigger API calls for internal UI navigation"


def test_production_directory_untouched():
    res = subprocess.run(["git", "-C", "/opt/ArdhaMind", "status", "--porcelain"], capture_output=True, text=True)
    assert res.returncode == 0, "Production git status must succeed"
    assert res.stdout.strip() == "", f"Production directory /opt/ArdhaMind must be 100% clean, got: {res.stdout}"
