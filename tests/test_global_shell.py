# tests/test_global_shell.py
"""
Automated Contract Tests for Global Shell & 3-Zone Top Navigation Bar.
Section 45 Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


# ── 1. THREE-ZONE TOP NAV GRID CONTRACTS ──

def test_top_bar_three_zone_grid_layout():
    code = read_frontend("components/WorkstationTopBar.tsx")
    assert "grid grid-cols-[auto_1fr_auto]" in code
    assert "justify-self-start" in code
    assert "justify-self-center" in code
    assert "justify-self-end" in code
    assert "h-[56px]" in code


def test_top_bar_brand_cluster_prominence():
    code = read_frontend("components/WorkstationTopBar.tsx")
    assert "ArdhaMindBrandMark size={24}" in code
    assert "text-[15px] font-bold" in code
    assert "STAGING" in code


def test_top_bar_market_closed_uses_non_error_amber_color():
    code = read_frontend("components/WorkstationTopBar.tsx")
    # Market closed must use amber (#E59700), NOT red (#E5484D)
    assert 'sessionBadge.isOpen ? "text-[#00C896]" : sessionBadge.isPreMarket ? "text-[#38BDF8]" : "text-[#E59700]"' in code


def test_top_bar_settings_and_assistant_buttons():
    code = read_frontend("components/WorkstationTopBar.tsx")
    assert "Live Assistant" in code
    assert "Settings" in code
    assert "settingsOpen" in code
    assert "border-[#38BDF8] bg-[#38BDF8]/15 text-[#38BDF8]" in code


# ── 2. FROZEN SIDEBAR & WORKSPACE CONTRACTS ──

def test_sidebar_remains_frozen_with_four_primary_workspaces():
    code = read_frontend("layout/DashboardLayout.tsx")
    assert "PRIMARY_MODULES = [" in code
    assert 'label: "MARKET"' in code
    assert 'label: "INTELLIGENCE"' in code
    assert 'label: "NEWS & UPDATES"' in code
    assert 'label: "PORTFOLIO"' in code
    assert 'label: "JOURNAL"' not in code


def test_no_overflow_shell_classes():
    code = read_frontend("layout/DashboardLayout.tsx")
    assert "min-w-0" in code
    assert "flex-1" in code
    assert "overflow-hidden" in code
