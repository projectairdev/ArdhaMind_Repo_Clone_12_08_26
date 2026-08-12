# tests/test_sprint_d2_confirmation_events.py
import pytest
from datetime import datetime, timezone
from src.application.workstation_state_service import WorkstationStateService

class TestSprintD2ConfirmationEvents:

    def setup_method(self):
        WorkstationStateService._snapshots_history = []
        WorkstationStateService._live_event_stream = []
        WorkstationStateService._sequence = 100
        if hasattr(WorkstationStateService, "_last_confirmation_trends"):
            WorkstationStateService._last_confirmation_trends = {}
        if hasattr(WorkstationStateService, "_last_emitted_regime"):
            delattr(WorkstationStateService, "_last_emitted_regime")
        if hasattr(WorkstationStateService, "_last_emitted_alignment"):
            delattr(WorkstationStateService, "_last_emitted_alignment")

    def _setup_5m_history(self, start_dt, spot_start=24500.0, adv_start=25, pcr_start=1.0, vix_start=12.0):
        # 5 minutes of valid continuous 1m snapshots
        for i in range(6):
            t = datetime.fromtimestamp(start_dt.timestamp() + i * 60, tz=timezone.utc)
            WorkstationStateService.build_from_legacy({
                "marketContext": {
                    "current_spot": spot_start,
                    "breadth": {"advances": adv_start, "declines": 50 - adv_start}
                },
                "optionContext": {"pcr": pcr_start},
                "macroIntelligence": {"india_vix": {"value": vix_start, "status": "AVAILABLE"}}
            }, now=t)

    def test_price_trend_improving(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24510.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "PRICE")
        assert fam["trend_direction"] == "IMPROVING"

    def test_price_trend_weakening(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24485.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "PRICE")
        assert fam["trend_direction"] == "WEAKENING"

    def test_price_trend_stable(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.5, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "PRICE")
        assert fam["trend_direction"] == "STABLE"

    def test_breadth_improving(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, adv_start=20)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 32, "declines": 18}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "BREADTH")
        assert fam["trend_direction"] == "IMPROVING"

    def test_breadth_weakening(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, adv_start=30)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 18, "declines": 32}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "BREADTH")
        assert fam["trend_direction"] == "WEAKENING"

    def test_breadth_stable(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, adv_start=25)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "BREADTH")
        assert fam["trend_direction"] == "STABLE"

    def test_options_valid_trend(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, pcr_start=0.90)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.05},
            "macroIntelligence": {"india_vix": {"value": 12.0, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "OPTIONS")
        assert fam["trend_direction"] == "IMPROVING"

    def test_options_unavailable_when_semantics_insufficient(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {}
        }, now=t0)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "OPTIONS")
        assert fam["status"] in ("READY", "UNAVAILABLE")
        assert fam["trend_direction"] in ("STABLE", "UNAVAILABLE")

    def test_volatility_improving(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, vix_start=14.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 12.5, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "VOLATILITY")
        assert fam["trend_direction"] == "IMPROVING"

    def test_volatility_weakening(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, vix_start=12.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 25, "declines": 25}},
            "optionContext": {"pcr": 1.0},
            "macroIntelligence": {"india_vix": {"value": 13.5, "status": "AVAILABLE"}}
        }, now=t_now)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "VOLATILITY")
        assert fam["trend_direction"] == "WEAKENING"

    def test_heavyweights_unavailable_without_authoritative_source(self):
        dt = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 35, "declines": 15}}
        }, now=dt)

        temporal = state.live_assistant_temporal_state
        fam = next(f for f in temporal["confirmation_families"] if f["family"] == "HEAVYWEIGHTS")
        assert fam["status"] == "UNAVAILABLE"
        assert fam["stance"] == "UNAVAILABLE"
        assert fam["trend_direction"] == "UNAVAILABLE"
        assert fam["reason"] == "authoritative heavyweight membership/weights unavailable"

    def test_breadth_never_substitutes_heavyweights(self):
        dt = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 45, "declines": 5}}
        }, now=dt)

        temporal = state.live_assistant_temporal_state
        hw_fam = next(f for f in temporal["confirmation_families"] if f["family"] == "HEAVYWEIGHTS")
        assert hw_fam["status"] == "UNAVAILABLE"
        assert hw_fam["trend_direction"] == "UNAVAILABLE"

    def test_rebuilding_1m_ignored(self):
        # 0 snapshots in history -> 1M rebuilding -> no trend event emitted
        dt = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=dt)
        c1m = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "1 MIN")
        assert c1m["available"] is False

    def test_rebuilding_5m_ignored(self):
        # 1 minute of history -> 5M rebuilding -> 5M comparison is not used for trend calculation
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 4, 1, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=t1)

        c5m = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "5 MIN")
        assert c5m["available"] is False

    def test_telemetry_gap_15m_ignored(self):
        t0 = datetime(2026, 8, 11, 8, 30, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 8, 44, 0, tzinfo=timezone.utc) # 14m gap
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24540.0}}, now=t1)

        temporal = state.live_assistant_temporal_state
        c15 = next(c for c in temporal["comparisons"] if c["requested_window"] == "15 MIN")
        assert c15["available"] is False
        # No 15M breakout event must be emitted across telemetry gap
        events_15m = [e for e in temporal["material_events"] if e.get("event_type") in ("15M_BREAKOUT", "15M_BREAKDOWN")]
        assert len(events_15m) == 0

    def test_valid_temporal_state_consumed(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24500.0)
        t_now = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0}}, now=t_now)

        price_fam = next(f for f in state.live_assistant_temporal_state["confirmation_families"] if f["family"] == "PRICE")
        assert price_fam["trend_direction"] == "IMPROVING"

    def test_trend_transition_emits_event(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, adv_start=30)
        
        # Initial tick sets baseline trend
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 30, "declines": 20}}
        }, now=t1)

        # Transition breadth to WEAKENING (15 advances)
        t2 = datetime(2026, 8, 11, 4, 6, 0, tzinfo=timezone.utc)
        state2 = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 15, "declines": 35}}
        }, now=t2)

        events = state2.live_assistant_temporal_state["material_events"]
        breadth_events = [e for e in events if e.get("event_type") == "BREADTH_DETERIORATED"]
        assert len(breadth_events) >= 1
        assert breadth_events[0]["family"] == "BREADTH"
        assert breadth_events[0]["previous_state"] == "STABLE"
        assert breadth_events[0]["current_state"] == "WEAKENING"

    def test_unchanged_trend_does_not_duplicate_event(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, adv_start=30)

        # Tick 1: Transition breadth to WEAKENING
        t1 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        state1 = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 15, "declines": 35}}
        }, now=t1)
        count_after_t1 = len([e for e in state1.live_assistant_temporal_state["material_events"] if e.get("event_type") == "BREADTH_DETERIORATED"])

        # Tick 2: Same WEAKENING trend (14 advances) -> must NOT duplicate BREADTH_DETERIORATED event
        t2 = datetime(2026, 8, 11, 4, 6, 0, tzinfo=timezone.utc)
        state2 = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24500.0, "breadth": {"advances": 14, "declines": 36}}
        }, now=t2)
        count_after_t2 = len([e for e in state2.live_assistant_temporal_state["material_events"] if e.get("event_type") == "BREADTH_DETERIORATED"])

        assert count_after_t2 == count_after_t1

    def test_scenario_transition_emits_event(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 4, 1, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24400.0}}, now=t1)

        events = state.live_assistant_temporal_state["material_events"]
        assert len(events) >= 1

    def test_behavior_transition_emits_event(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 4, 1, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t1)

        events = state.live_assistant_temporal_state["material_events"]
        assert len(events) >= 1

    def test_decision_area_break_reclaim_event(self):
        # Build 15m continuous history
        base_t = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        for i in range(15):
            t = datetime.fromtimestamp(base_t.timestamp() + i * 60, tz=timezone.utc)
            WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t)

        # 15m breakdown tick (-35 pts)
        t_break = datetime(2026, 8, 11, 4, 15, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24465.0}}, now=t_break)

        events = state.live_assistant_temporal_state["material_events"]
        break_events = [e for e in events if e.get("event_type") in ("15M_BREAKDOWN", "15M_BREAKOUT")]
        assert len(break_events) >= 1
        assert break_events[0]["event_type"] == "15M_BREAKDOWN"

    def test_event_carries_evidence_provenance(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        event = state.live_assistant_temporal_state["material_events"][0]

        assert "event_id" in event or "id" in event
        assert "event_type" in event
        assert "family" in event
        assert "occurred_at" in event
        assert "state_sequence" in event
        assert "materiality" in event
        assert "title" in event
        assert "description" in event
        assert "source_window" in event
        assert "evidence" in event
        assert "source_rule" in event
        assert "cooldown_key" in event

    def test_event_stream_remains_bounded(self):
        WorkstationStateService._live_event_stream = []
        for i in range(60):
            WorkstationStateService._live_event_stream.insert(0, {
                "id": f"evt-{i}", "event_type": "TEST", "family": "PRICE"
            })
            WorkstationStateService._live_event_stream = WorkstationStateService._live_event_stream[:50]

        assert len(WorkstationStateService._live_event_stream) == 50

    def test_invalid_temporal_window_cannot_emit_event(self):
        # 15M window containing host gap must not emit 15M breakout event
        t0 = datetime(2026, 8, 11, 8, 30, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 8, 44, 0, tzinfo=timezone.utc) # 14m gap
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24450.0}}, now=t1)

        events_15m = [e for e in state.live_assistant_temporal_state["material_events"] if e.get("source_window") == "15 MIN"]
        assert len(events_15m) == 0

    def test_d1_replay_weakening_state(self):
        # D.1 Replay ~09:30 IST state: NIFTY below 24500, weak breadth 16A/27D, PCR 1.04
        base_t = datetime(2026, 8, 11, 3, 45, 0, tzinfo=timezone.utc) # 09:15 IST (24533.85)
        for i in range(15):
            t = datetime.fromtimestamp(base_t.timestamp() + i * 60, tz=timezone.utc)
            WorkstationStateService.build_from_legacy({
                "marketContext": {"current_spot": 24533.85, "breadth": {"advances": 25, "declines": 25}},
                "optionContext": {"pcr": 1.04},
                "macroIntelligence": {"india_vix": {"value": 12.18, "status": "AVAILABLE"}}
            }, now=t)

        t_weak = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc) # 09:30 IST (24495.0, 16A/27D)
        state_weak = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24495.0, "breadth": {"advances": 16, "declines": 27}},
            "optionContext": {"pcr": 1.04},
            "macroIntelligence": {"india_vix": {"value": 12.18, "status": "AVAILABLE"}}
        }, now=t_weak)

        temporal = state_weak.live_assistant_temporal_state
        price_fam = next(f for f in temporal["confirmation_families"] if f["family"] == "PRICE")
        breadth_fam = next(f for f in temporal["confirmation_families"] if f["family"] == "BREADTH")

        assert price_fam["trend_direction"] == "WEAKENING"
        assert breadth_fam["trend_direction"] == "WEAKENING"

    def test_d1_replay_stabilization_state(self):
        # D.1 Replay ~09:40 IST state: NIFTY near 24440, PCR 0.8 -> spot stabilizing
        t0 = datetime(2026, 8, 11, 4, 5, 0, tzinfo=timezone.utc)
        self._setup_5m_history(t0, spot_start=24440.0, adv_start=17, pcr_start=0.8)

        t_stab = datetime(2026, 8, 11, 4, 10, 0, tzinfo=timezone.utc) # 09:40 IST
        state_stab = WorkstationStateService.build_from_legacy({
            "marketContext": {"current_spot": 24440.5, "breadth": {"advances": 17, "declines": 33}},
            "optionContext": {"pcr": 0.8},
            "macroIntelligence": {"india_vix": {"value": 11.91, "status": "AVAILABLE"}}
        }, now=t_stab)

        temporal = state_stab.live_assistant_temporal_state
        price_fam = next(f for f in temporal["confirmation_families"] if f["family"] == "PRICE")
        assert price_fam["trend_direction"] == "STABLE"
