# tests/test_sprint_d2_live_decision_intelligence.py
import pytest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService, validate_setup_geometry

class TestSprintD2LiveDecisionIntelligence:

    def setup_method(self):
        WorkstationStateService._snapshots_history = []
        WorkstationStateService._live_event_stream = []
        WorkstationStateService._sequence = 200
        if hasattr(WorkstationStateService, "_last_confirmation_trends"):
            WorkstationStateService._last_confirmation_trends = {}

    def _setup_5m_history(self, start_dt, spot_start=24500.0, adv_start=25, pcr_start=1.0, vix_start=12.0):
        for i in range(6):
            t = datetime.fromtimestamp(start_dt.timestamp() + i * 60, tz=timezone.utc)
            t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            WorkstationStateService.build_from_legacy({
                "marketContext": {
                    "timestamp": t_str,
                    "last_tick_time": t_str,
                    "current_spot": spot_start,
                    "breadth": {"advances": adv_start, "declines": 50 - adv_start, "coverage": 50},
                    "support_levels": [24428.0, 24435.0],
                    "resistance_levels": [24530.0, 24540.0]
                },
                "optionContext": {"pcr": pcr_start, "max_pain": spot_start, "timestamp": t_str},
                "macroIntelligence": {"india_vix": {"value": vix_start, "status": "AVAILABLE"}}
            }, market_state="MARKET_OPEN", now=t)

    # 1. Bearish entry/profit collision rejected
    def test_bearish_entry_profit_collision_rejected(self):
        bad_setup = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24450", "zone_low": 24449.0, "zone_high": 24456.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                    "zone_low": 24428.0, "zone_high": 24435.0, "zone": "24428.0–24435.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(bad_setup)
        assert valid is False
        assert "ENTRY_PROFIT_COLLISION" in issues

    # 2. Bullish entry/profit collision rejected
    def test_bullish_entry_profit_collision_rejected(self):
        bad_setup = {
            "direction": "BULLISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_res_1", "provenance_id": "dz_res_1",
                "zone_low": 24530.0, "zone_high": 24540.0, "display_range": "24530.0–24540.0"
            },
            "invalidation": {"zone": "24500", "zone_low": 24490.0, "zone_high": 24500.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_res_1", "provenance_id": "dz_res_1",
                    "zone_low": 24530.0, "zone_high": 24540.0, "zone": "24530.0–24540.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(bad_setup)
        assert valid is False
        assert "ENTRY_PROFIT_COLLISION" in issues

    # 3. Bearish profit must be below entry
    def test_bearish_profit_must_be_below_entry(self):
        wrong_side_setup = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24460", "zone_low": 24450.0, "zone_high": 24460.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_higher", "provenance_id": "dz_sup_higher",
                    "zone_low": 24450.0, "zone_high": 24460.0, "zone": "24450.0–24460.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(wrong_side_setup)
        assert valid is False
        assert "FIRST_PROFIT_REFERENCE_WRONG_SIDE" in issues

    # 4. Bullish profit must be above entry
    def test_bullish_profit_must_be_above_entry(self):
        wrong_side_setup = {
            "direction": "BULLISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_res_1", "provenance_id": "dz_res_1",
                "zone_low": 24530.0, "zone_high": 24540.0, "display_range": "24530.0–24540.0"
            },
            "invalidation": {"zone": "24500", "zone_low": 24490.0, "zone_high": 24500.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_res_lower", "provenance_id": "dz_res_lower",
                    "zone_low": 24450.0, "zone_high": 24460.0, "zone": "24450.0–24460.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(wrong_side_setup)
        assert valid is False
        assert "FIRST_PROFIT_REFERENCE_WRONG_SIDE" in issues

    # 5. Bearish invalidation must be above entry
    def test_bearish_invalidation_must_be_above_entry(self):
        wrong_inval = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24400", "zone_low": 24390.0, "zone_high": 24400.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_2", "provenance_id": "dz_sup_2",
                    "zone_low": 24350.0, "zone_high": 24360.0, "zone": "24350.0–24360.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(wrong_inval)
        assert valid is False
        assert "INVALIDATION_WRONG_SIDE" in issues

    # 6. Bullish invalidation must be below entry
    def test_bullish_invalidation_must_be_below_entry(self):
        wrong_inval = {
            "direction": "BULLISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_res_1", "provenance_id": "dz_res_1",
                "zone_low": 24530.0, "zone_high": 24540.0, "display_range": "24530.0–24540.0"
            },
            "invalidation": {"zone": "24600", "zone_low": 24590.0, "zone_high": 24600.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_res_2", "provenance_id": "dz_res_2",
                    "zone_low": 24580.0, "zone_high": 24590.0, "zone": "24580.0–24590.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(wrong_inval)
        assert valid is False
        assert "INVALIDATION_WRONG_SIDE" in issues

    # 7. Missing first profit reference prevents confirmed context
    def test_missing_first_profit_reference_prevents_confirmed_context(self):
        no_p1_setup = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24450", "zone_low": 24449.0, "zone_high": 24456.0},
            "profit_references": {
                "first_reference": {"available": False},
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(no_p1_setup)
        assert valid is False
        assert "FIRST_PROFIT_REFERENCE_UNAVAILABLE" in issues

    # 8. Missing invalidation prevents confirmed context
    def test_missing_invalidation_prevents_confirmed_context(self):
        no_inval = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_2", "provenance_id": "dz_sup_2",
                    "zone_low": 24350.0, "zone_high": 24360.0, "zone": "24350.0–24360.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(no_inval)
        assert valid is False
        assert "INVALIDATION_UNAVAILABLE" in issues

    # 9. Second profit reference optional
    def test_second_profit_reference_optional(self):
        single_profit = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24450", "zone_low": 24449.0, "zone_high": 24456.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_2", "provenance_id": "dz_sup_2",
                    "zone_low": 24350.0, "zone_high": 24360.0, "zone": "24350.0–24360.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(single_profit)
        assert valid is True
        assert len(issues) == 0

    # 10. Non-monotonic profit references rejected
    def test_non_monotonic_profit_references_rejected(self):
        non_mono = {
            "direction": "BEARISH",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24450", "zone_low": 24449.0, "zone_high": 24456.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_sup_2", "provenance_id": "dz_sup_2",
                    "zone_low": 24350.0, "zone_high": 24360.0, "zone": "24350.0–24360.0"
                },
                "second_reference": {
                    "available": True, "reference_id": "dz_sup_3", "provenance_id": "dz_sup_3",
                    "zone_low": 24390.0, "zone_high": 24400.0, "zone": "24390.0–24400.0"
                }
            }
        }
        valid, issues = validate_setup_geometry(non_mono)
        assert valid is False
        assert "NON_MONOTONIC_PROFIT_REFERENCES" in issues

    # 11. Canonical provenance preserved
    def test_canonical_provenance_preserved(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "current_spot": 24500.0,
                "support_levels": [24428.0, 24435.0],
                "resistance_levels": [24530.0, 24540.0]
            }
        }, market_state="MARKET_OPEN", now=t0)
        ld = state.live_assistant_temporal_state["live_decision"]
        sc = ld["setup_candidate"]

        assert "provenance" in sc["entry_reference"]
        assert "provenance_id" in sc["entry_reference"]
        assert "provenance" in sc["invalidation"]
        assert "provenance_id" in sc["invalidation"]
        assert "provenance" in sc["profit_references"]["first_reference"]
        assert "provenance_id" in sc["profit_references"]["first_reference"]

    # 12. No arbitrary target generated
    def test_no_arbitrary_target_generated(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "current_spot": 24500.0,
                "support_levels": [24428.0, 24435.0],
                "resistance_levels": [24530.0, 24540.0]
            }
        }, market_state="MARKET_OPEN", now=t0)
        ld = state.live_assistant_temporal_state["live_decision"]
        sc = ld["setup_candidate"]
        p1 = sc["profit_references"]["first_reference"]

        if p1.get("available"):
            assert p1["provenance"].startswith("canonical.")
            assert not any(k in str(p1).lower() for k in ("percent", "multiplier", "offset_pts"))

    # 13. Primary path / setup relationship exposed
    def test_primary_path_setup_relationship_exposed(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, market_state="MARKET_OPEN", now=t0)
        ld = state.live_assistant_temporal_state["live_decision"]
        sc = ld["setup_candidate"]

        assert "setup_relationship_to_primary_path" in sc
        assert sc["setup_relationship_to_primary_path"] in ("ALIGNED", "CONDITIONAL_ALTERNATE", "HEDGE_CONTEXT", "NOT_APPLICABLE")

    # 14. Bearish stable between-areas language
    def test_bearish_stable_between_areas_language(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24470.0, adv_start=15)
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        t1_str = t1.strftime("%Y-%m-%dT%H:%M:%SZ")
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t1_str, "last_tick_time": t1_str,
                "current_spot": 24470.0, "breadth": {"advances": 15, "declines": 35, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 0.75, "max_pain": 24500.0, "timestamp": t1_str}
        }, market_state="MARKET_OPEN", now=t1)

        ld = state.live_assistant_temporal_state["live_decision"]
        assert "Bearish background structure" in ld["current_read"] or "Downside pressure" in ld["current_read"]

    # 15. Bearish weakening support-test language
    def test_bearish_weakening_support_test_language(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0, adv_start=30)
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        t1_str = t1.strftime("%Y-%m-%dT%H:%M:%SZ")
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t1_str, "last_tick_time": t1_str,
                "current_spot": 24430.0, "breadth": {"advances": 12, "declines": 38, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 0.75, "max_pain": 24500.0, "timestamp": t1_str}
        }, market_state="MARKET_OPEN", now=t1)

        ld = state.live_assistant_temporal_state["live_decision"]
        assert "Bearish pressure with weakening momentum at support" in ld["current_read"] or "Downside pressure with weakening momentum" in ld["current_read"]

    # 16. Bullish improving breakout language
    def test_bullish_improving_breakout_language(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0, adv_start=20)
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        t1_str = t1.strftime("%Y-%m-%dT%H:%M:%SZ")
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t1_str, "last_tick_time": t1_str,
                "current_spot": 24550.0, "breadth": {"advances": 38, "declines": 12, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 1.20, "max_pain": 24500.0, "timestamp": t1_str}
        }, market_state="MARKET_OPEN", now=t1)

        ld = state.live_assistant_temporal_state["live_decision"]
        assert "Bullish pressure" in ld["current_read"] or "Upside pressure" in ld["current_read"]

    # 17. Mixed range language
    def test_mixed_range_language(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0)
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        t1_str = t1.strftime("%Y-%m-%dT%H:%M:%SZ")
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t1_str, "last_tick_time": t1_str,
                "current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 1.0, "max_pain": 24500.0, "timestamp": t1_str}
        }, market_state="MARKET_OPEN", now=t1)

        ld = state.live_assistant_temporal_state["live_decision"]
        assert "Mixed structure with range-bound price action." in ld["current_read"] or "Range-bound structure" in ld["current_read"]

    # 18. Range setup geometry
    def test_range_setup_geometry(self):
        range_setup = {
            "direction": "NEUTRAL",
            "entry_reference": {
                "available": True, "reference_id": "dz_sup_1", "provenance_id": "dz_sup_1",
                "zone_low": 24428.0, "zone_high": 24435.0, "display_range": "24428.0–24435.0"
            },
            "invalidation": {"zone": "24410", "zone_low": 24400.0, "zone_high": 24410.0},
            "profit_references": {
                "first_reference": {
                    "available": True, "reference_id": "dz_res_1", "provenance_id": "dz_res_1",
                    "zone_low": 24530.0, "zone_high": 24540.0, "zone": "24530.0–24540.0"
                },
                "second_reference": {"available": False}
            }
        }
        valid, issues = validate_setup_geometry(range_setup)
        assert valid is True
        assert len(issues) == 0

    # 19. D.1 09:30 replay fixed (entry != first_profit)
    def test_d1_0930_replay_fixed(self):
        base_t = datetime(2026, 8, 11, 3, 45, 0, tzinfo=timezone.utc)
        for i in range(15):
            t = datetime.fromtimestamp(base_t.timestamp() + i * 60, tz=timezone.utc)
            t_s = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            WorkstationStateService.build_from_legacy({
                "marketContext": {
                    "timestamp": t_s, "last_tick_time": t_s,
                    "current_spot": 24533.85, "breadth": {"advances": 25, "declines": 25, "coverage": 50},
                    "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
                }
            }, market_state="MARKET_OPEN", now=t)

        t_b = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        t_b_str = t_b.strftime("%Y-%m-%dT%H:%M:%SZ")
        state_b = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t_b_str, "last_tick_time": t_b_str,
                "current_spot": 24495.0, "breadth": {"advances": 16, "declines": 27, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 0.75, "max_pain": 24500.0, "timestamp": t_b_str}
        }, market_state="MARKET_OPEN", now=t_b)

        ld = state_b.live_assistant_temporal_state["live_decision"]
        sc = ld["setup_candidate"]
        e_ref = sc["entry_reference"]["display_range"]
        p1_ref = sc["profit_references"]["first_reference"].get("zone") or sc["profit_references"]["first_reference"].get("display_range")

        # ENTRY AND PROFIT MUST NOT BE IDENTICAL
        assert e_ref != p1_ref

    # 20. D.1 14:38 replay remains logically distinct
    def test_d1_1438_replay_remains_logically_distinct(self):
        base_t = datetime(2026, 8, 11, 9, 0, 0, tzinfo=timezone.utc)
        for i in range(10):
            t = datetime.fromtimestamp(base_t.timestamp() + i * 60, tz=timezone.utc)
            t_s = t.strftime("%Y-%m-%dT%H:%M:%SZ")
            WorkstationStateService.build_from_legacy({
                "marketContext": {
                    "timestamp": t_s, "last_tick_time": t_s,
                    "current_spot": 24442.0, "breadth": {"advances": 12, "declines": 38, "coverage": 50},
                    "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
                },
                "optionContext": {"pcr": 0.75, "max_pain": 24440.0, "timestamp": t_s},
                "macroIntelligence": {"india_vix": {"value": 11.91, "status": "AVAILABLE"}}
            }, market_state="MARKET_OPEN", now=t)

        t_d = datetime(2026, 8, 11, 9, 8, 0, tzinfo=timezone.utc)
        t_d_str = t_d.strftime("%Y-%m-%dT%H:%M:%SZ")
        state_d = WorkstationStateService.build_from_legacy({
            "marketContext": {
                "timestamp": t_d_str, "last_tick_time": t_d_str,
                "current_spot": 24442.5, "breadth": {"advances": 12, "declines": 38, "coverage": 50},
                "support_levels": [24428.0, 24435.0], "resistance_levels": [24530.0, 24540.0]
            },
            "optionContext": {"pcr": 0.75, "max_pain": 24440.0, "timestamp": t_d_str},
            "macroIntelligence": {"india_vix": {"value": 11.91, "status": "AVAILABLE"}}
        }, market_state="MARKET_OPEN", now=t_d)

        ld = state_d.live_assistant_temporal_state["live_decision"]
        assert ld["structural_bias"] == "BEARISH"
        assert ld["short_term_momentum"] in ("STABILIZING", "STABLE")
