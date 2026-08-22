# tests/test_trading_cheatsheet_workspace.py
"""
Targeted Unit & Regression Test Suite for Trading Cheatsheet:
BEGINNER / INTERMEDIATE / ADVANCED Experience Modes.

Validates:
  1. Experience level selector exists with BEGINNER default and local persistence.
  2. Single unified knowledge model with 3 presentation layers per concept.
  3. Semantic consistency across all 3 levels (e.g. VIX = magnitude in all modes).
  4. Beginner mode simplification: plain English, minimal jargon, friendly subtitles, grouped layout.
  5. Detail popover adaptation (4 fields in Beginner, 5 in Intermediate, 7 in Advanced).
  6. Multi-layer Scenario Explorer (4 controls in Beginner, 6 in Intermediate, 8 in Advanced).
  7. Deterministic canonical scenario taxonomy alignment across all modes.
  8. Conflict detection and trap detection across all modes.
  9. Absolute zero live-data dependency.
"""
import unittest
from pathlib import Path


class TestTradingCheatsheetAdaptiveWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_file = Path("src/frontend/features/trading-cheatsheet/data/tradingCheatsheet.ts")
        cls.component_file = Path("src/frontend/features/trading-cheatsheet/TradingCheatsheetWorkspace.tsx")
        cls.layout_file = Path("src/frontend/layout/DashboardLayout.tsx")

    def test_01_source_files_exist(self):
        """Knowledge base, component, and layout files must exist."""
        self.assertTrue(self.data_file.exists(), "tradingCheatsheet.ts data file must exist")
        self.assertTrue(self.component_file.exists(), "TradingCheatsheetWorkspace.tsx component must exist")
        self.assertTrue(self.layout_file.exists(), "DashboardLayout.tsx layout file must exist")

    def test_02_zero_live_data_dependency_invariant(self):
        """Trading Cheatsheet component and data must NOT import live market feeds or Kite broker state."""
        data_code = self.data_file.read_text(encoding="utf-8")
        comp_code = self.component_file.read_text(encoding="utf-8")

        forbidden_imports = [
            "useWorkstationState",
            "StreamingOrchestrator",
            "KiteTicker",
            "kite_intelligence_service",
            "KiteSession"
        ]
        for forbidden in forbidden_imports:
            self.assertNotIn(
                f"import {forbidden}",
                data_code,
                f"Data file must have 0 live market dependencies; found '{forbidden}'"
            )
            self.assertNotIn(
                f"import {forbidden}",
                comp_code,
                f"Component file must have 0 live market dependencies; found '{forbidden}'"
            )
            self.assertNotIn(
                forbidden,
                comp_code,
                f"Component file must have 0 live market dependencies; found '{forbidden}'"
            )

    def test_03_experience_level_selector_and_persistence(self):
        """Component must implement 3 experience levels with BEGINNER default and local persistence."""
        comp_code = self.component_file.read_text(encoding="utf-8")
        self.assertIn("BEGINNER", comp_code)
        self.assertIn("INTERMEDIATE", comp_code)
        self.assertIn("ADVANCED", comp_code)
        self.assertIn("trading_cheatsheet_experience_level", comp_code)
        self.assertIn('localStorage.getItem("trading_cheatsheet_experience_level")', comp_code)
        self.assertIn('return "BEGINNER"', comp_code)

    def test_04_unified_concept_model_with_three_layers(self):
        """UnifiedTradingConcept must provide beginner, intermediate, and advanced presentation fields."""
        data_code = self.data_file.read_text(encoding="utf-8")
        self.assertIn("export interface UnifiedTradingConcept", data_code)
        self.assertIn("beginner: BeginnerConceptPresentation", data_code)
        self.assertIn("intermediate: IntermediateConceptPresentation", data_code)
        self.assertIn("advanced: AdvancedConceptPresentation", data_code)
        self.assertIn("UNIFIED_CORE_METRICS", data_code)

    def test_05_india_vix_adaptation(self):
        """India VIX must adapt across Beginner, Intermediate, and Advanced without contradiction."""
        data_code = self.data_file.read_text(encoding="utf-8")
        # Beginner: "How nervous is the market?", magnitude not direction
        self.assertIn("How nervous is the market?", data_code)
        self.assertIn("VIX measures the SIZE of expected price swings", data_code)
        # Intermediate: annualized 30-day volatility expectation
        self.assertIn("annualized 30-day volatility expectation", data_code)
        # Advanced: Black-Scholes variance swap formula
        self.assertIn("variance swap formula", data_code)

    def test_06_market_breadth_adaptation(self):
        """Market Breadth must adapt across all 3 levels."""
        data_code = self.data_file.read_text(encoding="utf-8")
        self.assertIn("How many NIFTY stocks are participating?", data_code)
        self.assertIn("Advance/Decline ratio across the 50 constituent stocks", data_code)
        self.assertIn("unweighted advance-decline", data_code)

    def test_07_pcr_and_oi_adaptation(self):
        """PCR and Open Interest must adapt across all 3 levels."""
        data_code = self.data_file.read_text(encoding="utf-8")
        self.assertIn("Are traders positioned more in puts or calls?", data_code)
        self.assertIn("Are new positions being added or removed?", data_code)
        self.assertIn("UNIFIED_PRICE_OI_MATRIX", data_code)
        self.assertIn("beginnerLabel", data_code)
        self.assertIn("advancedMechanics", data_code)

    def test_08_detail_popover_structure_by_mode(self):
        """Popover detail must render 4 sections in Beginner, 5 in Intermediate, 7 in Advanced."""
        comp_code = self.component_file.read_text(encoding="utf-8")
        # Beginner popover
        self.assertIn("1. WHAT IS THIS?", comp_code)
        self.assertIn("2. WHY DOES IT MATTER?", comp_code)
        self.assertIn("3. SIMPLE EXAMPLE", comp_code)
        self.assertIn("4. REMEMBER THIS", comp_code)
        # Intermediate popover
        self.assertIn("2. HOW TRADERS INTERPRET IT", comp_code)
        self.assertIn("3. COMMON REFERENCE RANGES", comp_code)
        self.assertIn("4. CONFIRM WITH", comp_code)
        self.assertIn("5. COMMON MISTAKE", comp_code)
        # Advanced popover
        self.assertIn("DEFINITION", comp_code)
        self.assertIn("2. QUANTITATIVE MECHANICS", comp_code)
        self.assertIn("3. INTERPRETATION REGIMES", comp_code)
        self.assertIn("4. CONFLUENCE RULES", comp_code)
        self.assertIn("5. FAILURE CONDITIONS", comp_code)

    def test_09_scenario_explorer_inputs_by_mode(self):
        """Beginner explorer must have 4 controls, Intermediate 6, Advanced 8."""
        comp_code = self.component_file.read_text(encoding="utf-8")
        data_code = self.data_file.read_text(encoding="utf-8")
        self.assertIn("BeginnerScenarioInputState", data_code)
        self.assertIn("IntermediateScenarioInputState", data_code)
        self.assertIn("CanonicalScenarioInputState", data_code)
        self.assertIn("mapBeginnerToCanonical", data_code)
        self.assertIn("mapIntermediateToCanonical", data_code)
        self.assertIn("4 Simple Market Controls", comp_code)
        self.assertIn("6 Indicator Controls", comp_code)
        self.assertIn("8 Institutional Controls", comp_code)

    def test_10_canonical_scenario_taxonomy_mapping(self):
        """All explorer outputs must map to the same canonical taxonomy."""
        data_code = self.data_file.read_text(encoding="utf-8")
        taxonomies = [
            "BULLISH_CONTINUATION",
            "BEARISH_CONTINUATION",
            "RANGE_CHOP",
            "FALSE_BREAKOUT_RISK",
            "BEAR_TRAP_RISK",
            "MIXED_CONFLICTING"
        ]
        for t in taxonomies:
            self.assertIn(t, data_code)

    def test_11_conflict_detection_and_no_fake_probabilities(self):
        """Conflict detection must operate at all 3 experience levels without arbitrary percentages."""
        data_code = self.data_file.read_text(encoding="utf-8")
        self.assertIn("SCEN_CONFLICTING_SIGNALS", data_code)
        self.assertIn("MIXED / UNCLEAR SIGNALS", data_code)
        self.assertIn("MIXED / CONFLICTING SIGNALS", data_code)
        self.assertNotIn("Math.random()", data_code)


if __name__ == "__main__":
    unittest.main()
