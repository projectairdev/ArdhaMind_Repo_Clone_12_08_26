# tests/test_pre_market_briefing_workspace.py
"""
Targeted Test Suite for Pre-Market Briefing Workspace.

Validates:
  1. 08:50 AM IST generation and immutable freeze.
  2. Strict evidence cutoff and future-data leakage protection.
  3. Disk persistence and restart survival.
  4. Complete 22-section domain model integrity.
  5. Post-market validation (Forecast vs Reality) with objective accuracy scoring.
  6. Historical briefing archive.
  7. Provider failure handling without fake fallbacks.
  8. Staging developer preview controls.
"""
import json
import os
import unittest
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from src.intelligence_engine.pre_market_briefing_engine import PreMarketBriefingEngine
from src.models.pre_market_briefing import PreMarketBriefingReport


class TestPreMarketBriefingWorkspace(unittest.TestCase):

    def setUp(self):
        PreMarketBriefingEngine._cached_briefings.clear()
        storage_dir = PreMarketBriefingEngine.get_storage_dir()
        test_file = storage_dir / "PMB_2026-08-18.json"
        if test_file.exists():
            try:
                test_file.unlink()
            except Exception:
                pass
        self.mock_canonical_state = {
            "runtime_id": "test-runtime-daemon-101",
            "state_sequence": 450,
            "market_session": {
                "status": "CLOSED",
                "is_closed": True,
                "session_date": "2026-08-17"
            },
            "market_data": {
                "current_spot": 24287.65,
                "close": 24287.65,
                "open": 24343.45,
                "high": 24360.10,
                "low": 24226.95,
                "previous_close": 24366.0,
                "spot_change": -78.35,
                "spot_change_pct": -0.3216
            },
            "option_intelligence": {
                "current_weekly_expiry": "2026-08-18",
                "atm_strike": 24300,
                "pcr": 1.22,
                "volume_pcr": 1.34,
                "max_pain": 24350,
                "highest_call_oi_strike": 24500,
                "highest_put_oi_strike": 24300,
                "atm_iv": 11.41
            },
            "macro_intelligence": {
                "quotes": {
                    "GIFT_NIFTY": {"price": 24296.0, "change": -79.0, "change_pct": -0.32},
                    "INDIA_VIX": {"price": 11.33, "change": 0.02, "change_pct": 0.18},
                    "S&P 500": {"price": 7745.06, "change": -40.7, "change_pct": -0.52},
                    "NASDAQ": {"price": 26644.91, "change": -84.25, "change_pct": -0.32},
                    "DOW_JONES": {"price": 53459.78, "change": -272.63, "change_pct": -0.51},
                    "NIKKEI_225": {"price": 69220.25, "change": 506.45, "change_pct": 0.74},
                    "HANG_SENG": {"price": 25453.23, "change": 336.38, "change_pct": 1.34},
                    "BRENT_CRUDE": {"price": 91.12, "change": 0.25, "change_pct": 0.28},
                    "GOLD": {"price": 4480.50, "change": 6.80, "change_pct": 0.15},
                    "USD_INR": {"price": 95.592, "change": 0.0, "change_pct": 0.0},
                    "DXY": {"price": 99.539, "change": -0.098, "change_pct": -0.10},
                    "US_10Y": {"price": 4.724, "change": 0.028, "change_pct": 0.60}
                },
                "institutional_flows": [
                    {"dataset_type": "FII_CASH", "net_value": -2535.1, "buy_value": 11546.16, "sell_value": 14081.26, "date": "17-Aug-2026"},
                    {"dataset_type": "DII_CASH", "net_value": 5101.46, "buy_value": 16654.08, "sell_value": 11552.62, "date": "17-Aug-2026"}
                ]
            },
            "news_intelligence": {
                "items": [
                    {"id": "n1", "headline": "Global Market Update", "source_name": "Reuters", "published_at": "2026-08-18T02:30:00Z", "nifty_relevance_score": 8.5, "impact_strength": "HIGH", "expected_direction": "NEUTRAL"},
                    {"id": "n2", "headline": "RBI Liquidity Measure", "source_name": "Economic Times", "published_at": "2026-08-18T03:10:00Z", "nifty_relevance_score": 7.9, "impact_strength": "MEDIUM", "expected_direction": "POSITIVE"}
                ]
            }
        }

    def test_01_briefing_generation_and_0850_freeze(self):
        """Briefing generated at/after 08:50 IST must be FROZEN and immutable."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)  # 08:50 IST
        briefing = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )
        self.assertEqual(briefing.trading_date, "2026-08-18")
        self.assertEqual(briefing.reference_session_date, "2026-08-17")
        self.assertEqual(briefing.status, "FROZEN")
        self.assertEqual(briefing.command_center.opening_bias, "NEUTRAL / MIXED")
        self.assertEqual(briefing.command_center.expected_open_str, "24,296 – 24,326")
        self.assertEqual(briefing.command_center.nifty_reference_close, 24287.65)
        self.assertEqual(briefing.command_center.gift_nifty_price, 24296.0)

    def test_02_evidence_cutoff_and_no_future_leakage(self):
        """Later market changes (e.g. at 09:10 IST) must NEVER alter the frozen 08:50 briefing."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        original_briefing = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )

        # Injected 09:10 IST mutated state
        mutated_state = json.loads(json.dumps(self.mock_canonical_state))
        mutated_state["macro_intelligence"]["quotes"]["GIFT_NIFTY"]["price"] = 24500.0  # Big jump at 09:10
        mutated_state["news_intelligence"]["items"].insert(0, {
            "id": "leak-news", "headline": "9:10 AM BREAKING NEWS", "published_at": "2026-08-18T03:40:00Z"
        })

        as_of_0910_utc = datetime(2026, 8, 18, 3, 40, 0, tzinfo=timezone.utc)
        second_call = PreMarketBriefingEngine.generate_or_get_briefing(
            mutated_state,
            as_of_time=as_of_0910_utc,
            force_regenerate=False
        )

        # Frozen values MUST NOT CHANGE
        self.assertEqual(second_call.command_center.gift_nifty_price, 24296.0)
        self.assertEqual(second_call.command_center.expected_open_str, "24,296 – 24,326")
        self.assertEqual(second_call.report_id, original_briefing.report_id)

    def test_03_persistence_and_restart_survival(self):
        """Briefing persisted to disk must reload identically after engine cache flush."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        original = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )
        report_id = original.report_id

        # Flush in-memory cache to simulate full daemon restart
        PreMarketBriefingEngine._cached_briefings.clear()

        reloaded = PreMarketBriefingEngine.load_persisted_briefing("2026-08-18")
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.report_id, report_id)
        self.assertEqual(reloaded.command_center.expected_open_str, "24,296 – 24,326")
        self.assertEqual(reloaded.command_center.opening_bias, "NEUTRAL / MIXED")

    def test_04_all_twenty_two_sections_integrity(self):
        """All 22 reference sections must be populated with non-null canonical evidence."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        b = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )

        # Section checks
        self.assertGreater(len(b.traffic_lights), 5)
        self.assertEqual(len(b.global_snapshot), 11)
        self.assertIn("us_equities_avg", b.global_cue_interpretation)
        self.assertEqual(b.gift_dashboard["price"], 24296.0)
        self.assertAlmostEqual(b.price_structure["r1"], 24356.0, delta=1.0)
        self.assertAlmostEqual(b.price_structure["s1"], 24223.0, delta=1.0)
        # Decision corridor is now computed from floor pivots (pivot ± 5), not a
        # date-pinned hardcoded 24,284 literal.
        self.assertAlmostEqual(
            b.price_structure["decision_corridor_lower"],
            b.price_structure["pivot_floor"] - 5.0,
            delta=1.0,
        )
        self.assertEqual(b.options_intelligence["pcr_oi"], 1.22)
        self.assertEqual(b.options_intelligence["max_pain"], 24350.0)
        self.assertEqual(b.institutional_positioning["fii_net"], -2535.1)
        self.assertEqual(b.institutional_positioning["dii_net"], 5101.46)
        self.assertEqual(b.volatility_and_risk["vix"], 11.33)
        self.assertEqual(b.breadth_carry["advances"], 18)
        self.assertEqual(b.breadth_carry["declines"], 31)
        self.assertEqual(len(b.sector_scoreboard), 10)
        self.assertGreaterEqual(len(b.heavyweights), 10)
        self.assertGreaterEqual(len(b.stocks_to_watch), 4)
        self.assertGreaterEqual(len(b.news_highlights), 2)
        self.assertGreaterEqual(len(b.event_calendar), 3)
        self.assertEqual(len(b.opening_scenarios), 3)
        self.assertEqual(len(b.trade_playbook), 3)
        self.assertIsNotNone(b.one_page_trade_card.best_action_at_open)
        self.assertIn("methodology_version", b.provenance)

    def test_05_staging_preview_does_not_mutate_canonical_status_or_persist(self):
        """Staging preview must populate validation_preview without mutating canonical report status or on-disk state."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        briefing = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )
        self.assertEqual(briefing.status, "FROZEN")
        self.assertEqual(briefing.post_market_validation.validation_status, "PENDING")

        # Run preview validation
        previewed = PreMarketBriefingEngine.validate_briefing(
            briefing,
            self.mock_canonical_state,
            is_preview=True
        )

        # Canonical status MUST remain FROZEN
        self.assertEqual(previewed.status, "FROZEN")
        self.assertEqual(previewed.post_market_validation.validation_status, "PENDING")

        # Preview state MUST be populated under preview structure
        self.assertIsNotNone(previewed.validation_preview)
        self.assertTrue(previewed.validation_preview["is_preview"])
        self.assertEqual(previewed.validation_preview["preview_mode"], "STAGING_HISTORICAL_SIMULATION")
        self.assertGreater(previewed.validation_preview["preview_accuracy_score_pct"], 80.0)
        self.assertIn("STAGING PREVIEW", previewed.validation_preview["notice"])

        # Disk reload MUST still reflect canonical FROZEN status, not VALIDATED
        reloaded = PreMarketBriefingEngine.load_persisted_briefing("2026-08-18")
        self.assertIsNotNone(reloaded)
        self.assertEqual(reloaded.status, "FROZEN")
        self.assertEqual(reloaded.post_market_validation.validation_status, "PENDING")

    def test_06_real_validation_hard_guard(self):
        """Genuine validation must fail-closed on future/ongoing sessions and only activate on completed sessions."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        briefing = PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )

        # Calling with is_preview=False on future/ongoing target session (before 15:30 IST on 2026-08-18)
        # must still be treated as preview simulation by hard guard
        simulated = PreMarketBriefingEngine.validate_briefing(briefing, self.mock_canonical_state, is_preview=False, now_time=as_of_0850_utc)
        self.assertNotEqual(simulated.status, "VALIDATED")
        self.assertIsNotNone(simulated.validation_preview)

    def test_07_completed_session_genuine_validation(self):
        """Past completed session with is_preview=False can genuinely validate and persist."""
        past_state = dict(self.mock_canonical_state)
        # Generate a past session briefing for 2026-08-17
        past_briefing = PreMarketBriefingEngine._build_canonical_briefing(
            state=past_state,
            target_date="2026-08-17",
            ref_date="2026-08-16",
            ref_close=24366.0,
            now_ist=datetime(2026, 8, 17, 8, 50, 0),
            now_str="2026-08-17T03:20:00Z",
            evidence_cutoff_at="2026-08-17T03:20:00Z",
            status="FROZEN",
            generated_late=False
        )

        validated = PreMarketBriefingEngine.validate_briefing(past_briefing, past_state, is_preview=False)
        self.assertEqual(validated.status, "VALIDATED")
        self.assertEqual(validated.post_market_validation.validation_status, "VALIDATED")
        self.assertGreater(validated.post_market_validation.overall_accuracy_score_pct, 80.0)

    def test_08_historical_archive_listing(self):
        """Historical list must provide session summary records."""
        as_of_0850_utc = datetime(2026, 8, 18, 3, 20, 0, tzinfo=timezone.utc)
        PreMarketBriefingEngine.generate_or_get_briefing(
            self.mock_canonical_state,
            as_of_time=as_of_0850_utc
        )
        history = PreMarketBriefingEngine.list_history()
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertIn("trading_date", history[0])
        self.assertIn("opening_bias", history[0])

    def test_09_provider_failure_truthful_fallback(self):
        """When macro feeds fail, values must show null/unavailable without fake zero or hardcoded fallbacks."""
        empty_state = {
            "market_session": {"status": "CLOSED", "session_date": "2026-08-17"},
            "market_data": {"close": 24287.65}
        }
        b = PreMarketBriefingEngine._build_canonical_briefing(
            state=empty_state,
            target_date="2026-08-18",
            ref_date="2026-08-17",
            ref_close=24287.65,
            now_ist=datetime(2026, 8, 18, 8, 50, 0),
            now_str="2026-08-18T03:20:00Z",
            evidence_cutoff_at="2026-08-18T03:20:00Z",
            status="FROZEN",
            generated_late=False
        )
        self.assertEqual(b.command_center.opening_bias, "NEUTRAL / MIXED")
        self.assertEqual(b.reference_close, 24287.65)
        self.assertIsNone(b.command_center.gift_nifty_price)
        self.assertEqual(b.command_center.gap_methodology, "EVIDENCE_SCORE_FALLBACK")
        self.assertEqual(b.command_center.gift_freshness, "UNAVAILABLE")

    def test_10_fresh_gift_gap_and_expected_open_arithmetic(self):
        """Fresh GIFT Nifty must strictly reconcile arithmetic across all UI locations."""
        b = PreMarketBriefingEngine._build_canonical_briefing(
            state=self.mock_canonical_state,
            target_date="2026-08-18",
            ref_date="2026-08-17",
            ref_close=24287.65,
            now_ist=datetime(2026, 8, 18, 8, 50, 0),
            now_str="2026-08-18T03:20:00Z",
            evidence_cutoff_at="2026-08-18T03:20:00Z",
            status="FROZEN",
            generated_late=False
        )
        ref_close = 24287.65
        gift_val = 24296.0

        # Command Center checks
        self.assertEqual(b.command_center.nifty_reference_close, ref_close)
        self.assertEqual(b.command_center.gift_nifty_price, gift_val)
        self.assertEqual(b.command_center.implied_gap_points, 8.35)
        self.assertEqual(b.command_center.gap_methodology, "GIFT_ANCHORED")
        self.assertEqual(b.command_center.expected_gap_str, "+8 to +38")
        self.assertEqual(b.command_center.expected_open_str, "24,296 – 24,326")

        # Arithmetic invariant: ref_close + gap_low == open_low, ref_close + gap_high == open_high
        self.assertEqual(b.command_center.expected_open_low, 24296.00)
        self.assertEqual(b.command_center.expected_open_high, 24326.00)
        self.assertAlmostEqual(ref_close + 8.35, b.command_center.expected_open_low, delta=0.5)
        self.assertAlmostEqual(ref_close + 38.35, b.command_center.expected_open_high, delta=0.5)

        # Cross-section consistency checks
        # 1. Why Summary
        self.assertIn("24,296", b.command_center.overall_summary_why[0])
        self.assertIn(f"{b.command_center.implied_gap_points:+.1f} points", b.command_center.overall_summary_why[0])

        # 2. Traffic Lights
        gift_tl = next(t for t in b.traffic_lights if t.category == "GIFT_NIFTY")
        self.assertEqual(gift_tl.status, "GREEN")
        self.assertIn("24,296", gift_tl.reason)
        self.assertIn(f"{b.command_center.implied_gap_points:+.1f} pts", gift_tl.reason)

        # 3. Global Snapshot
        gift_gs = next(g for g in b.global_snapshot if g.symbol == "GIFT_NIFTY")
        self.assertEqual(gift_gs.price, 24296.0)
        self.assertEqual(gift_gs.freshness, "FRESH")
        self.assertEqual(gift_gs.directional_implication, "POSITIVE")

        # 4. GIFT Dashboard
        self.assertEqual(b.gift_dashboard["price"], 24296.0)
        self.assertEqual(b.gift_dashboard["implied_gap_points"], 8.35)
        self.assertEqual(b.gift_dashboard["expected_open_zone"], "24,296 – 24,326")

        # 5. One Page Trade Card
        self.assertEqual(b.one_page_trade_card.expected_open, "24,296 – 24,326")
        self.assertEqual(b.one_page_trade_card.expected_gap, "+8 to +38")

    def test_11_last_valid_gift_freshness_exposure(self):
        """LAST_VALID GIFT Nifty must expose its freshness status and timestamp across all sections."""
        lv_state = json.loads(json.dumps(self.mock_canonical_state))
        lv_state["macro_intelligence"]["quotes"]["GIFT_NIFTY"] = {
            "price": 24296.0,
            "change": -79.0,
            "change_pct": -0.32,
            "freshness_status": "LAST_VALID",
            "observed_at": "02:30 IST"
        }
        b = PreMarketBriefingEngine._build_canonical_briefing(
            state=lv_state,
            target_date="2026-08-18",
            ref_date="2026-08-17",
            ref_close=24287.65,
            now_ist=datetime(2026, 8, 18, 8, 50, 0),
            now_str="2026-08-18T03:20:00Z",
            evidence_cutoff_at="2026-08-18T03:20:00Z",
            status="FROZEN",
            generated_late=False
        )
        self.assertEqual(b.command_center.gift_freshness, "LAST_VALID")
        self.assertEqual(b.command_center.gift_observed_at, "02:30 IST")
        self.assertIn("LAST_VALID", b.command_center.overall_summary_why[0])

        gift_gs = next(g for g in b.global_snapshot if g.symbol == "GIFT_NIFTY")
        self.assertEqual(gift_gs.freshness, "LAST_VALID")
        self.assertEqual(gift_gs.observed_at, "02:30 IST")

    def test_12_unavailable_gift_fallback_and_consistency(self):
        """Unavailable GIFT Nifty must consistently trigger fallback methodology without fake values."""
        no_gift_state = json.loads(json.dumps(self.mock_canonical_state))
        no_gift_state["macro_intelligence"]["quotes"].pop("GIFT_NIFTY", None)

        b = PreMarketBriefingEngine._build_canonical_briefing(
            state=no_gift_state,
            target_date="2026-08-18",
            ref_date="2026-08-17",
            ref_close=24287.65,
            now_ist=datetime(2026, 8, 18, 8, 50, 0),
            now_str="2026-08-18T03:20:00Z",
            evidence_cutoff_at="2026-08-18T03:20:00Z",
            status="FROZEN",
            generated_late=False
        )
        self.assertIsNone(b.command_center.gift_nifty_price)
        self.assertIsNone(b.command_center.implied_gap_points)
        self.assertEqual(b.command_center.gap_methodology, "EVIDENCE_SCORE_FALLBACK")
        self.assertEqual(b.command_center.gift_freshness, "UNAVAILABLE")

        # Why summary must state fallback
        self.assertIn("unavailable/pending", b.command_center.overall_summary_why[0])
        self.assertIn("evidence score fallback", b.command_center.overall_summary_why[0])

        # Traffic light must be AMBER and state pending
        gift_tl = next(t for t in b.traffic_lights if t.category == "GIFT_NIFTY")
        self.assertEqual(gift_tl.status, "AMBER")
        self.assertIn("unavailable/pending", gift_tl.reason)

        # Global snapshot must show None / UNAVAILABLE
        gift_gs = next(g for g in b.global_snapshot if g.symbol == "GIFT_NIFTY")
        self.assertIsNone(gift_gs.price)
        self.assertEqual(gift_gs.session_status, "UNAVAILABLE")
        self.assertEqual(gift_gs.freshness, "UNAVAILABLE")

        # Expected open arithmetic still holds with fallback gap
        self.assertEqual(b.command_center.expected_gap_str, "+4 to +24")
        self.assertEqual(b.command_center.expected_open_str, "24,291 – 24,311")
        self.assertAlmostEqual(24287.65 + 3.5, b.command_center.expected_open_low, delta=0.5)
        self.assertAlmostEqual(24287.65 + 23.5, b.command_center.expected_open_high, delta=0.5)


if __name__ == "__main__":
    unittest.main()
