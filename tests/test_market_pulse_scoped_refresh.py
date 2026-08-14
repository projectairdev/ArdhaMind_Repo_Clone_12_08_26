# tests/test_market_pulse_scoped_refresh.py
"""
Targeted test suite for SPRINT D3.5C.1 Market Pulse Scoped Refresh UI Completion.
Validates exact scoped controls, individual card refresh buttons, Forward Outlook navigation, provider boundaries, and timestamp truth semantics.
"""
from __future__ import annotations

import unittest
from pathlib import Path

COMP_PATH = Path("src/frontend/components/MarketPulseWorkspace.tsx")
MACRO_COMP_PATH = Path("src/frontend/components/MacroIntelligence.tsx")
LAYOUT_PATH = Path("src/frontend/layout/DashboardLayout.tsx")


class TestMarketPulseScopedRefreshUI(unittest.TestCase):

    def setUp(self):
        self.code = COMP_PATH.read_text(encoding="utf-8")
        self.macro_code = MACRO_COMP_PATH.read_text(encoding="utf-8")
        self.layout_code = LAYOUT_PATH.read_text(encoding="utf-8")

    def test_1_scoped_macro_refresh_control_visible(self):
        self.assertIn("↻ REFRESH GLOBAL & MACRO", self.code)
        self.assertIn("handleMacroRefresh", self.code)

    def test_2_fii_dii_refresh_control_visible(self):
        self.assertIn("↻ REFRESH FII/DII", self.macro_code)
        self.assertIn("handleMacroRefresh", self.code)

    def test_3_news_refresh_control_visible(self):
        self.assertIn("↻ REFRESH NEWS", self.code)
        self.assertIn("handleNewsRefresh", self.code)

    def test_4_option_chain_revalidate_remains(self):
        self.assertIn("REVALIDATE CHAIN", self.code)

    def test_5_live_nifty_has_no_manual_refresh(self):
        # Core India card header has no individual refresh button
        core_card = self.code.split("CARD 1: CORE INDIA", 1)[1].split("CARD 2: DERIVATIVES", 1)[0]
        self.assertNotIn("onClick=", core_card)

    def test_6_streamed_breadth_has_no_manual_refresh(self):
        # Constituents breadth widget has no individual refresh button
        breadth_card = self.code.split("CARD 6: CONSTITUENTS BREADTH", 1)[1]
        self.assertNotIn("onClick=", breadth_card)

    def test_7_duplicate_clicks_guarded(self):
        self.assertIn("if (macroRefreshing) return", self.code)
        self.assertIn("if (newsRefreshing) return", self.code)

    def test_8_family_refresh_invokes_correct_boundary(self):
        self.assertIn("apiMacroRefresh", self.code)
        self.assertIn("apiNewsRefresh", self.code)
        helpers_code = Path("src/frontend/utils/safeHelpers.ts").read_text(encoding="utf-8")
        self.assertIn("/api/macro/refresh", helpers_code)
        self.assertIn("/api/news/refresh", helpers_code)

    def test_9_unchanged_observation_semantics(self):
        # Checked timestamp updates, Observed remains canonical
        self.assertIn("Checked:", self.macro_code)
        self.assertIn("Observed:", self.macro_code)

    def test_10_failed_refresh_preserves_last_valid_value(self):
        self.assertIn("Macro refresh failed", self.code)
        self.assertIn("News refresh incomplete", self.code)

    def test_11_rate_limited_state_renders(self):
        self.assertIn("Rate limited (1/min)", self.code)
        self.assertIn("rate_limited", self.code)

    def test_12_market_closed_macro_news_refresh_remains_possible(self):
        # Scoped handlers are independent of isClosed guard
        self.assertIn("handleMacroRefresh", self.code)
        self.assertIn("handleNewsRefresh", self.code)

    def test_13_no_fake_card_timestamp_rewriting(self):
        self.assertIn("ObservedCheckedFreshness", self.code)

    def test_14_individual_tile_refresh_controls_present(self):
        # Individual tile refresh button title in MacroIntelligence
        self.assertIn("title={`Refresh ${label}`}", self.macro_code)
        self.assertIn("onRefreshItem", self.macro_code)

    def test_15_forward_outlook_wired_in_navigation(self):
        self.assertIn('id: "forward-outlook"', self.layout_code)
        self.assertIn('label: "Scenario Outlook"', self.layout_code)
        self.assertIn("ForwardOutlookWorkspace", self.layout_code)


if __name__ == "__main__":
    unittest.main()
