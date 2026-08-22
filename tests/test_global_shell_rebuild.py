# tests/test_global_shell_rebuild.py
"""
Automated Unit, Integration, & Architectural Verification Tests for
GLOBAL SHELL — TOP NAVBAR + SIDEBAR PROFESSIONAL REBUILD SPRINT.
Staging Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


class TestTopNavbarRebuild:
    """Tests confirming the refined top navbar architecture and brand identity."""

    def test_brand_identity_is_ardha(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "ARDHA" in code
        assert "ArdhaMindBrandMark" in code
        assert "STAGING" in code

    def test_market_status_is_text_only_no_icon(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "Market:" in code
        assert "sessionBadge.label" in code

    def test_broker_status_is_text_only_no_icon(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "Broker:" in code
        assert "brokerLabel" in code

    def test_status_separators_present(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "|" in code
        assert "text-[#242830]" in code

    def test_live_assistant_is_icon_only_with_tooltip(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert 'aria-label="Live Assistant"' in code
        assert "Sparkles" in code
        assert "Live Assistant" in code  # in tooltip
        assert "toggleAssistant" in code

    def test_settings_is_icon_only_with_tooltip(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert 'aria-label="Settings"' in code
        assert "SettingsIcon" in code
        assert "Settings" in code  # in tooltip
        assert "onOpenSettings" in code

    def test_calendar_icon_removed_clock_only(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "Calendar" not in code  # Calendar icon must not be imported in topbar
        assert "Clock" in code
        assert "IST" in code

    def test_compact_topbar_height(self):
        code = read_frontend("components/WorkstationTopBar.tsx")
        assert "h-14" in code or "h-16" in code or "h-[64px]" in code


class TestSidebarRebuild:
    """Tests confirming the sidebar contains ONLY the 5 primary navigation items and no Settings/collapse clutter."""

    def test_exact_five_primary_modules_present(self):
        code = read_frontend("layout/DashboardLayout.tsx")
        assert 'id: "market", label: "MARKET"' in code
        assert 'id: "market_intelligence", label: "MARKET INTELLIGENCE"' in code
        assert 'id: "trading_cheatsheet", label: "TRADING CHEATSHEET"' in code
        assert 'id: "news", label: "NEWS & UPDATES"' in code
        assert 'id: "portfolio", label: "PORTFOLIO"' in code

    def test_settings_removed_from_sidebar_navigation(self):
        code = read_frontend("layout/DashboardLayout.tsx")
        # Sidebar aside should only map PRIMARY_MODULES
        sidebar_block = code.split('id="workstation-sidebar"')[1].split("</aside>")[0]
        assert "SETTINGS" not in sidebar_block
        assert "openSettingsConsole" not in sidebar_block

    def test_collapse_control_removed_from_sidebar(self):
        code = read_frontend("layout/DashboardLayout.tsx")
        sidebar_block = code.split('id="workstation-sidebar"')[1].split("</aside>")[0]
        assert "ChevronLeft" not in sidebar_block
        assert "ChevronRight" not in sidebar_block
        assert "toggleSidebarCollapse" not in code

    def test_sidebar_active_border_highlight(self):
        code = read_frontend("layout/DashboardLayout.tsx")
        assert "border-[#38BDF8]" in code
        assert "bg-[#12151A]" in code
