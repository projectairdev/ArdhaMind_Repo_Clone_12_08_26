# tests/test_news_responsive_ui.py
"""
Automated Responsive UI & Visual Closure Contract Tests for News & Updates Workspace.
Section 31 & 35 Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


# ── 1. LIVE NEWS HEADER & LAYOUT CONTRACTS ──

def test_live_news_title_cannot_truncate():
    code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "LIVE NEWS FEED" in code
    # Ensure LIVE NEWS FEED element does NOT have 'truncate' on its title span
    assert 'text-xs uppercase whitespace-nowrap shrink-0">LIVE NEWS FEED</span>' in code


def test_provider_health_appears_immediately_after_sector_impact():
    code = read_frontend("components/news/LiveNewsTab.tsx")
    market_pos = code.find('title="MARKET IMPACT SUMMARY"')
    sector_pos = code.find('title="SECTOR NEWS IMPACT"')
    provider_pos = code.find('title="PROVIDER &amp; SOURCE HEALTH"')

    assert market_pos != -1
    assert sector_pos != -1
    assert provider_pos != -1

    # Exact right rail order: Market Impact -> Sector Impact -> Provider Health
    assert market_pos < sector_pos < provider_pos


def test_duplicate_event_footer_removed_from_live_news_tab():
    code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "7G. NEXT EVENT FOOTER" not in code


# ── 2. DEAD SPACE & CATALYST CONTRACTS ──

def test_no_center_column_min_height_forcing_dead_space():
    code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "items-start" in code
    assert "min-h-[600px]" not in code
    assert "min-h-[500px]" not in code or "LEFT COLUMN" in code


def test_empty_regulatory_state_uses_compact_height():
    code = read_frontend("components/news/CatalystsTab.tsx")
    assert "No active regulatory or policy catalysts." in code
    assert "py-3" in code


def test_catalyst_columns_align_start():
    code = read_frontend("components/news/CatalystsTab.tsx")
    assert "items-start" in code


# ── 3. CALENDAR UPCOMING-FIRST CONTRACT ──

def test_calendar_groups_upcoming_before_completed():
    code = read_frontend("components/news/CalendarTab.tsx")
    upcoming_pos = code.find("UPCOMING EVENTS")
    completed_pos = code.find("COMPLETED EVENTS")
    assert upcoming_pos != -1
    assert completed_pos != -1
    assert upcoming_pos < completed_pos  # Upcoming first!
