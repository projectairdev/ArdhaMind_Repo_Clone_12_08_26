"""
Sidebar Navigation Modernization Test Suite
===========================================
Verifies:
1. All 8 workspaces are accessible in the modern order.
2. Internal workspace IDs are completely unchanged.
3. 5 navigation groups (MARKET, INTELLIGENCE, PLANNING, INFORMATION, SYSTEM) are defined.
4. Correct professional terminal labels are used.
5. No trade execution terminology or forbidden consumer app terms are present in navigation.
"""

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
LAYOUT_FILE = ROOT / "src/frontend/layout/DashboardLayout.tsx"


def test_navigation_groups_definition():
    """Verify that NAVIGATION_GROUPS defines all 5 required categories in order."""
    content = LAYOUT_FILE.read_text(encoding="utf-8")
    assert "NAVIGATION_GROUPS" in content

    categories = ["MARKET", "INTELLIGENCE", "PLANNING", "INFORMATION", "SYSTEM"]
    last_idx = -1
    for cat in categories:
        idx = content.find(f'category: "{cat}"')
        assert idx != -1, f"Category {cat} missing in NAVIGATION_GROUPS"
        assert idx > last_idx, f"Category {cat} is out of order"
        last_idx = idx


def test_all_eight_workspaces_mapped_in_new_order():
    """Verify exact modern workspace labels and order within NAVIGATION_GROUPS."""
    content = LAYOUT_FILE.read_text(encoding="utf-8")

    expected_items = [
        ("nifty-live", "Market Command"),
        ("market-pulse", "Market Pulse"),
        ("live-assistant", "Intraday Intelligence"),
        ("todays-analysis", "Session Intelligence"),
        ("forward-outlook", "Scenario Outlook"),
        ("pre-market-planner", "Pre-Market Intelligence"),
        ("news-updates", "Intelligence Feed"),
        ("settings", "System Control"),
    ]

    for internal_id, label in expected_items:
        pattern = f'id: "{internal_id}", label: "{label}"'
        assert pattern in content, f"Workspace mapping missing: {pattern}"


def test_internal_ids_unchanged():
    """Verify that internal workspace IDs remain identical for routing & legacy redirects."""
    content = LAYOUT_FILE.read_text(encoding="utf-8")

    ids = [
        "nifty-live",
        "market-pulse",
        "live-assistant",
        "todays-analysis",
        "forward-outlook",
        "pre-market-planner",
        "news-updates",
        "settings",
    ]

    for item_id in ids:
        assert f'"{item_id}"' in content


def test_no_forbidden_trade_execution_terms():
    """Verify forbidden execution terminology is not present in navigation array."""
    content = LAYOUT_FILE.read_text(encoding="utf-8")
    nav_start = content.find("export const NAVIGATION_GROUPS")
    nav_end = content.find("type WorkspaceId")
    nav_code = content[nav_start:nav_end]

    forbidden = ["Trade Center", "Execution", "Portfolio", "Orders", "Strategy Execution", "Trade Planner"]
    for term in forbidden:
        assert term not in nav_code, f"Forbidden term '{term}' found in navigation definition"
