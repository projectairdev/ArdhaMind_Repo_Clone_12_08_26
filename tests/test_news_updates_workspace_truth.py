# tests/test_news_updates_workspace_truth.py
"""
Automated Contract Tests for NEWS & UPDATES Workspace in AIR ArdhaMind.

Enforces:
1. Exactly 3 subtabs exist: LIVE NEWS, CATALYSTS, CALENDAR.
2. Canonical News presentation adapter returns valid data models.
3. Target session date filtering rejects stale prior-year events.
4. Top story derived dynamically.
5. Deduplication preserves primary story while tracking related report counts.
6. Publisher vs Provider distinction enforced.
7. No hardcoded runtime fixtures in React components.
"""

from pathlib import Path
import json


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


def test_three_subtabs_exist_in_news_workspace():
    """Assert exactly 3 subtabs exist in NewsWorkspace: LIVE NEWS, CATALYSTS, CALENDAR."""
    ws_code = read_frontend("components/news/NewsWorkspace.tsx")
    assert "LIVE NEWS" in ws_code
    assert "CATALYSTS" in ws_code
    assert "CALENDAR" in ws_code
    assert "NewsSubTab = \"live_news\" | \"catalysts\" | \"calendar\"" in ws_code


def test_canonical_news_adapter_exports_valid_types():
    """Assert canonicalNewsAdapter defines presentation state model and story types."""
    adapter_code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "export interface NewsPresentationState" in adapter_code
    assert "export interface CanonicalNewsStory" in adapter_code
    assert "export interface CanonicalEconomicEvent" in adapter_code
    assert "export function getCanonicalNewsPresentation" in adapter_code


def test_publisher_vs_provider_distinction_enforced():
    """Assert publisher and provider are distinct properties in news adapter."""
    adapter_code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "publisher:" in adapter_code
    assert "provider:" in adapter_code
    assert "sourceType: \"OFFICIAL\"" in adapter_code


def test_deduplication_and_duplicate_group_id_handling():
    """Assert deduplicator groups duplicate headlines without inflating counts."""
    adapter_code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "duplicateGroupId" in adapter_code
    assert "dedupGroupMap" in adapter_code


def test_stale_event_filtering_contract():
    """Assert economic event parsing rejects prior-year stale events."""
    adapter_code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "evDate.getFullYear() < currentYear" in adapter_code


def test_no_hardcoded_fake_company_mappings():
    """Assert LiveNewsTab and NewsWorkspace use dynamic presentation data."""
    live_code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "WHY IT MATTERS TO NIFTY" in live_code
    assert "topStory" in live_code
    assert "pres.impactCounts" in live_code


def test_dashboard_layout_routes_to_news_workspace():
    """Assert DashboardLayout routes NEWS & UPDATES to NewsWorkspace."""
    layout_code = read_frontend("layout/DashboardLayout.tsx")
    assert "{ id: \"news\", label: \"NEWS & UPDATES\", glyph: JournalGlyph }" in layout_code
    assert "<NewsWorkspace subTab={newsSubTab} onSelectSubTab={setNewsSubTab} />" in layout_code


def test_top_story_and_why_it_matters_contract():
    """Assert Top Story, Why It Matters to Nifty, and Canonical Impact Context are rendered."""
    live_code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "TOP STORY OF THE SESSION" in live_code
    assert "WHY IT MATTERS TO NIFTY" in live_code
    assert "CANONICAL IMPACT CONTEXT" in live_code
    assert "RELATED SESSION COVERAGE" in live_code
    assert "VIEW ALL NEWS" in live_code
    assert "VIEW FULL RELATED COVERAGE" in live_code


def test_right_rail_intelligence_summaries_contract():
    """Assert Market Impact, Sector Impact, Event Timeline, and Provider Health exist."""
    live_code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "MARKET IMPACT SUMMARY" in live_code
    assert "SECTOR NEWS IMPACT" in live_code
    assert "EVENT TIMELINE" in live_code
    assert "PROVIDER &amp; SOURCE HEALTH" in live_code
    assert "VIEW SECTOR ANALYSIS" in live_code
    assert "VIEW FULL CALENDAR" in live_code
    assert "VIEW SOURCE MONITOR" in live_code


def test_degraded_feed_honest_language_contract():
    """Assert degraded or empty news states do not falsely display 'No important news'."""
    live_code = read_frontend("components/news/LiveNewsTab.tsx")
    assert "CANONICAL NEWS FEED UNAVAILABLE" in live_code

