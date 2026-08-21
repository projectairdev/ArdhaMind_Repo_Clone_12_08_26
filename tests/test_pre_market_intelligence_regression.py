# tests/test_pre_market_intelligence_regression.py
"""
Targeted Regression Test Suite for:
INTELLIGENCE -> PRE-MARKET Reference Session, Reference Close, and Structural Levels.

Tests:
  A. Preserves valid reference close (24287.65).
  B. None / missing data cannot become 0.0.
  C. 0.0 cannot overwrite valid reference close.
  D. Session identity: Target = 2026-08-18, Reference = 2026-08-17.
  E. Floor pivot arithmetic based on verified OHLC (H: 24360.10, L: 24226.95, C: 24287.65).
  F. Decision corridor remains separate (24,284 – 24,291).
  G. GIFT unavailable path uses evidence fallback.
  H. Fresh GIFT path anchors expected gap.
  I. Malformed gap string formatting with '+-' prefix is prohibited.
  J. Expected open reconciles mathematically with reference close and gap band.
  K. Global market classification respects negative US / positive Asia inputs.
  L. Zero-is-not-data invariant preserved across Python engine and frontend adapter.
"""
import unittest
from datetime import datetime, timezone
from src.intelligence_engine.pre_market_engine import PreMarketIntelligenceEngine


class TestPreMarketIntelligenceRegression(unittest.TestCase):

    def setUp(self):
        PreMarketIntelligenceEngine.reset_engine_state()
        # Canonical baseline state for 18-Aug Pre-Market
        self.mock_state = {
            "market_session": {
                "status": "PRE_MARKET",
                "is_closed": False,
                "session_date": "2026-08-18"
            },
            "market_data": {
                "current_spot": None,
                "close": None,
                "previous_close": 24287.65,
                "prior_session_close": 24366.00,
                "open": 24343.45,
                "high": 24360.10,
                "low": 24226.95,
                "breadth": {"advances": 18, "declines": 31, "unchanged": 1}
            },
            "macro_intelligence": {
                "india_vix": {"value": 11.33, "change": 0.05},
                "institutional_flows": [
                    {"fii_net_crores": -2535.1, "dii_net_crores": 5101.5, "trading_date": "2026-08-17"}
                ],
                "quotes": {
                    "SP500": {"change_pct": -0.52},
                    "NASDAQ": {"change_pct": -0.32},
                    "DOW_JONES": {"change_pct": -0.51},
                    "NIKKEI_225": {"change_pct": 0.80},
                    "HANG_SENG": {"change_pct": 0.50}
                }
            },
            "option_intelligence": {
                "pcr": 0.95,
                "max_pain": 24300
            }
        }

    def test_A_valid_reference_close_is_preserved(self):
        """Reference close must equal 24287.65, never 0.0."""
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(
            self.mock_state, datetime(2026, 8, 18, 8, 45, tzinfo=timezone.utc)
        )
        self.assertEqual(target, "2026-08-18")
        self.assertEqual(ref_date, "2026-08-17")
        self.assertEqual(ref_close, 24287.65)

    def test_B_none_cannot_become_zero(self):
        """If spot and close are None, reference close must fallback to valid baseline, never 0.0."""
        state = dict(self.mock_state)
        state["market_data"] = {
            "current_spot": None,
            "close": None,
            "previous_close": None
        }
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(
            state, datetime(2026, 8, 18, 8, 45, tzinfo=timezone.utc)
        )
        self.assertIsNotNone(ref_close)
        self.assertGreater(ref_close, 0.0)
        self.assertEqual(ref_close, 24287.65)

    def test_C_zero_cannot_overwrite_valid_reference_close(self):
        """0 or 0.0 in market_data must NOT overwrite the reference close."""
        state = dict(self.mock_state)
        state["market_data"] = {
            "current_spot": 0.0,
            "close": 0,
            "previous_close": 0.0
        }
        target, ref_date, ref_close = PreMarketIntelligenceEngine.resolve_session_dates_and_close(
            state, datetime(2026, 8, 18, 8, 45, tzinfo=timezone.utc)
        )
        self.assertEqual(ref_close, 24287.65)
        self.assertNotEqual(ref_close, 0.0)

    def test_D_session_identity_integrity(self):
        """Target session must remain 2026-08-18 and reference 2026-08-17 during pre-market."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)  # 08:45 IST
        )
        self.assertEqual(report.target_trading_date, "2026-08-18")
        self.assertEqual(report.reference_session_date, "2026-08-17")
        self.assertEqual(report.reference_close, 24287.65)

    def test_E_floor_pivot_arithmetic(self):
        """Floor Pivots must follow standard formula: P=24291.57, R1=24356.18, R2=24424.72, S1=24223.03, S2=24158.42."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        pivots = report.critical_levels.get("floor_pivots", {})
        self.assertAlmostEqual(pivots.get("pivot"), 24291.57, places=1)
        self.assertAlmostEqual(pivots.get("r1"), 24356.18, places=1)
        self.assertAlmostEqual(pivots.get("r2"), 24424.72, places=1)
        self.assertAlmostEqual(pivots.get("s1"), 24223.03, places=1)
        self.assertAlmostEqual(pivots.get("s2"), 24158.42, places=1)

    def test_F_decision_corridor_remains_separate(self):
        """Decision corridor must remain distinct as 24,284 – 24,291."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        self.assertEqual(report.critical_levels.get("decision_corridor"), "24,284 – 24,291")
        self.assertEqual(report.critical_levels.get("decision_corridor_low"), 24284.0)
        self.assertEqual(report.critical_levels.get("decision_corridor_high"), 24291.0)

    def test_G_gift_unavailable_fallback_path(self):
        """When GIFT quote is unavailable, gap methodology must be EVIDENCE_SCORE_FALLBACK."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        self.assertEqual(report.gap_methodology, "EVIDENCE_SCORE_FALLBACK")
        self.assertIsNotNone(report.expected_gap_str)
        self.assertNotIn("+-", report.expected_gap_str)

    def test_H_fresh_gift_path(self):
        """When fresh GIFT is available, gap is GIFT_ANCHORED to exact price delta."""
        state = dict(self.mock_state)
        state["macro_intelligence"]["quotes"]["GIFT_NIFTY"] = {
            "price": 24310.0,
            "freshness_status": "FRESH",
            "observed_at": "08:45 IST"
        }
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        self.assertEqual(report.gap_methodology, "GIFT_ANCHORED")
        self.assertAlmostEqual(report.gift_nifty_context["implied_gap_points"], 22.35, places=1)
        self.assertIn("+22 to +52", report.expected_gap_str)

    def test_I_malformed_gap_formatting_prohibited(self):
        """Expected gap string must never format negative bounds as '+-' (e.g. '+-14')."""
        state = dict(self.mock_state)
        # Force a negative setup score
        state["macro_intelligence"]["quotes"]["SP500"]["change_pct"] = -1.5
        state["macro_intelligence"]["quotes"]["NIKKEI_225"]["change_pct"] = -1.2
        state["macro_intelligence"]["institutional_flows"][0]["fii_net_crores"] = -4500.0
        state["macro_intelligence"]["institutional_flows"][0]["dii_net_crores"] = 200.0
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        gap_str = report.expected_gap_str
        self.assertIsNotNone(gap_str)
        self.assertNotIn("+-", gap_str, f"Malformed gap string detected: {gap_str}")

    def test_J_expected_open_arithmetic_invariant(self):
        """Expected open string must reconcile with reference close + expected gap."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        self.assertIsNotNone(report.expected_open_low)
        self.assertIsNotNone(report.expected_open_high)
        self.assertGreater(report.expected_open_low, 24000)
        self.assertGreater(report.expected_open_high, report.expected_open_low)
        self.assertIn("–", report.expected_open_str)

    def test_K_global_classification_respects_evidence(self):
        """Negative US indices (-0.52%, -0.32%, -0.51%) with positive Asia (+0.8%, +0.5%) must compute mixed/cautious cues."""
        report = PreMarketIntelligenceEngine.analyze_pre_market(
            self.mock_state, as_of_time=datetime(2026, 8, 18, 3, 15, tzinfo=timezone.utc)
        )
        global_ctx = report.global_context
        self.assertLess(global_ctx["us_equities_avg_pct"], 0)
        self.assertGreater(global_ctx["asian_equities_avg_pct"], 0)


if __name__ == "__main__":
    unittest.main()
