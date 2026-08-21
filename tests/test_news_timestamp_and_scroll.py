# tests/test_news_timestamp_and_scroll.py
"""
Automated Contract Tests for Live News Timestamp Normalization & Bounded Scroll Layout.
Section 23 Quality Gates for AIR ArdhaMind.
"""

from pathlib import Path
import pytest


def read_frontend(rel_path: str) -> str:
    full_path = Path(__file__).parent.parent / "src" / "frontend" / rel_path
    return full_path.read_text(encoding="utf-8")


# ── 1. TIMESTAMP FORMATTING & UTILITY CONTRACTS ──

def test_news_temporal_utils_file_contract():
    code = read_frontend("utils/newsTemporalUtils.ts")
    assert "export function formatNewsTimestamp" in code
    assert "Today ·" in code
    assert "Yesterday ·" in code
    assert "Time unavailable" in code
    assert "Asia/Kolkata" in code


def test_adapter_preserves_row_and_top_story_timestamps():
    code = read_frontend("utils/canonicalNewsAdapter.ts")
    assert "formatNewsTimestamp" in code
    assert "displayRowTime" in code
    assert "displayTopStoryTime" in code


# ── 2. COMPONENT SCROLL & VISIBILITY CONTRACTS ──

def test_live_news_tab_scroll_and_sticky_contract():
    code = read_frontend("components/news/LiveNewsTab.tsx")
    
    # Left feed bounded scroll list
    assert "overflow-y-auto" in code
    assert "feedListRef" in code
    assert "scrollTop = 0" in code  # Filter resets scroll position to top

    # Header and Filters stay outside scroll container (shrink-0)
    assert "shrink-0" in code

    # Adaptive responsive grid column layout
    assert "lg:grid-cols-" in code
    assert "xl:grid-cols-" in code
    assert "items-start" in code
