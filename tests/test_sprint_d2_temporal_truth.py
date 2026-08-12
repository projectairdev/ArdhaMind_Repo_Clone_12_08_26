# tests/test_sprint_d2_temporal_truth.py
import pytest
from datetime import datetime, timezone
from src.broker.services.market_status_service import MarketStatusService
from src.application.workstation_state_service import WorkstationStateService

class TestSprintD2TemporalTruth:

    def setup_method(self):
        WorkstationStateService._snapshots_history = []
        WorkstationStateService._sequence = 100

    def test_authoritative_session_transitions(self):
        ms = MarketStatusService.get_instance()
        
        # 08:30 IST (UTC 03:00) -> CLOSED
        dt_0830 = datetime(2026, 8, 11, 3, 0, 0, tzinfo=timezone.utc)
        rep_0830 = ms.get_market_status(dt_0830)
        assert rep_0830.status == "CLOSED"

        # 09:00 IST (UTC 03:30) -> PRE_OPEN
        dt_0900 = datetime(2026, 8, 11, 3, 30, 0, tzinfo=timezone.utc)
        rep_0900 = ms.get_market_status(dt_0900)
        assert rep_0900.status == "PRE_OPEN"

        # 09:14 IST (UTC 03:44) -> PRE_OPEN
        dt_0914 = datetime(2026, 8, 11, 3, 44, 0, tzinfo=timezone.utc)
        rep_0914 = ms.get_market_status(dt_0914)
        assert rep_0914.status == "PRE_OPEN"

        # 09:16 IST (UTC 03:46) -> OPEN
        dt_0916 = datetime(2026, 8, 11, 3, 46, 0, tzinfo=timezone.utc)
        rep_0916 = ms.get_market_status(dt_0916)
        assert rep_0916.status == "OPEN"

    def test_08xx_closed_session_phase(self):
        dt_0830 = datetime(2026, 8, 11, 3, 0, 0, tzinfo=timezone.utc)
        payload = {"marketContext": {"current_spot": 24500.0}}
        state = WorkstationStateService.build_from_legacy(payload, now=dt_0830)
        
        last_snap = WorkstationStateService._snapshots_history[-1]
        assert last_snap["market_session_phase"] == "CLOSED"
        assert last_snap["continuous_session_open"] is False

    def test_0900_pre_open_session_phase(self):
        dt_0900 = datetime(2026, 8, 11, 3, 30, 0, tzinfo=timezone.utc)
        payload = {"marketContext": {"current_spot": 24580.0}}
        state = WorkstationStateService.build_from_legacy(payload, now=dt_0900)
        
        last_snap = WorkstationStateService._snapshots_history[-1]
        assert last_snap["market_session_phase"] == "PRE_OPEN"
        assert last_snap["continuous_session_open"] is False

    def test_0914_pre_open_session_phase(self):
        dt_0914 = datetime(2026, 8, 11, 3, 44, 0, tzinfo=timezone.utc)
        payload = {"marketContext": {"current_spot": 24585.0}}
        state = WorkstationStateService.build_from_legacy(payload, now=dt_0914)
        
        last_snap = WorkstationStateService._snapshots_history[-1]
        assert last_snap["market_session_phase"] == "PRE_OPEN"
        assert last_snap["continuous_session_open"] is False

    def test_first_market_open_transition(self):
        dt_0915 = datetime(2026, 8, 11, 3, 45, 23, tzinfo=timezone.utc)
        payload = {"marketContext": {"current_spot": 24533.85}}
        state = WorkstationStateService.build_from_legacy(payload, now=dt_0915)
        
        last_snap = WorkstationStateService._snapshots_history[-1]
        assert last_snap["market_session_phase"] == "MARKET_OPEN"
        assert last_snap["continuous_session_open"] is True

    def test_since_open_baseline_selection(self):
        # 08:45 CLOSED
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24500.0}},
            now=datetime(2026, 8, 11, 3, 15, 0, tzinfo=timezone.utc)
        )
        # 09:00 PRE_OPEN
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24580.0}},
            now=datetime(2026, 8, 11, 3, 30, 0, tzinfo=timezone.utc)
        )
        # 09:15:23 FIRST MARKET_OPEN (Baseline = 24533.85)
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24533.85}},
            now=datetime(2026, 8, 11, 3, 45, 23, tzinfo=timezone.utc)
        )
        # 09:20:00 SUBSEQUENT MARKET_OPEN (Spot = 24510.75)
        state_0920 = WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24510.75}},
            now=datetime(2026, 8, 11, 3, 50, 0, tzinfo=timezone.utc)
        )

        temporal = state_0920.live_assistant_temporal_state
        so = next(c for c in temporal["comparisons"] if c["requested_window"] == "SINCE OPEN")
        
        assert so["available"] is True
        assert so["diff_spot"] == round(24510.75 - 24533.85, 2)

    def test_cross_session_baseline_exclusion(self):
        # Yesterday MARKET_OPEN (2026-08-10 09:15 IST / UTC 03:45)
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24100.0}},
            now=datetime(2026, 8, 10, 3, 45, 0, tzinfo=timezone.utc)
        )
        # Today PRE_OPEN (2026-08-11 09:00 IST / UTC 03:30)
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24580.0}},
            now=datetime(2026, 8, 11, 3, 30, 0, tzinfo=timezone.utc)
        )
        # Today First MARKET_OPEN (2026-08-11 09:15 IST / UTC 03:45) -> Baseline spot = 24533.85
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24533.85}},
            now=datetime(2026, 8, 11, 3, 45, 0, tzinfo=timezone.utc)
        )
        # Today Subsequent MARKET_OPEN (2026-08-11 09:20 IST / UTC 03:50) -> Spot = 24510.00
        state_today = WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24510.00}},
            now=datetime(2026, 8, 11, 3, 50, 0, tzinfo=timezone.utc)
        )

        temporal = state_today.live_assistant_temporal_state
        so = next(c for c in temporal["comparisons"] if c["requested_window"] == "SINCE OPEN")
        assert so["available"] is True
        # Diff must be calculated relative to today's open (24533.85), NOT yesterday's open (24100.0)
        assert so["diff_spot"] == round(24510.00 - 24533.85, 2)
        assert so["from_timestamp"].startswith("2026-08-11T03:45:00")

    def test_pre_open_exclusion(self):
        # Multiple PRE_OPEN snapshots
        for mins in [0, 5, 10, 14]:
            t = datetime(2026, 8, 11, 3, 30 + mins, 0, tzinfo=timezone.utc)
            state = WorkstationStateService.build_from_legacy(
                {"marketContext": {"current_spot": 24580.0 + mins}},
                now=t
            )
            so = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "SINCE OPEN")
            # None of the PRE_OPEN snapshots can serve as SINCE_OPEN baseline
            assert so["available"] is False
            assert so["status"] == "INSUFFICIENT_HISTORY"

    def test_host_gap_detection(self):
        # 14:00 snapshot
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24500.0}},
            now=datetime(2026, 8, 11, 8, 30, 0, tzinfo=timezone.utc)
        )
        # 14:14 snapshot (14 min host sleep gap)
        WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24510.0}},
            now=datetime(2026, 8, 11, 8, 44, 0, tzinfo=timezone.utc)
        )
        # 14:15 snapshot (1 min after 14:14)
        state_1415 = WorkstationStateService.build_from_legacy(
            {"marketContext": {"current_spot": 24512.0}},
            now=datetime(2026, 8, 11, 8, 45, 0, tzinfo=timezone.utc)
        )

        temporal = state_1415.live_assistant_temporal_state
        c15 = next(c for c in temporal["comparisons"] if c["requested_window"] == "15 MIN")
        
        assert c15["available"] is False
        assert c15["continuity_valid"] is False
        assert c15["status"] == "TELEMETRY_GAP"
        assert c15["largest_gap_seconds"] == 840.0

    def test_1m_continuity(self):
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 4, 1, 0, tzinfo=timezone.utc)
        state_1m = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=t1)

        c1m = next(c for c in state_1m.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "1 MIN")
        assert c1m["available"] is True
        assert c1m["continuity_valid"] is True

    def test_5m_continuity(self):
        base_t = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        for i in range(6):
            t = datetime.fromtimestamp(base_t.timestamp() + i * 60, tz=timezone.utc)
            state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0 + i}}, now=t)

        c5m = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "5 MIN")
        assert c5m["available"] is True
        assert c5m["continuity_valid"] is True

    def test_15m_continuity(self):
        t0 = datetime(2026, 8, 11, 8, 30, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 8, 44, 0, tzinfo=timezone.utc) # 14m gap
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0}}, now=t1)
        t2 = datetime(2026, 8, 11, 8, 45, 0, tzinfo=timezone.utc)
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24515.0}}, now=t2)

        c15m = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "15 MIN")
        assert c15m["available"] is False
        assert c15m["continuity_valid"] is False
        assert c15m["status"] == "TELEMETRY_GAP"

    def test_post_gap_1m_recovery(self):
        base_t = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=base_t)
        # Gap of 10 minutes
        post_gap_t = datetime(2026, 8, 11, 4, 10, 0, tzinfo=timezone.utc)
        state_immediate = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=post_gap_t)
        c1m_imm = next(c for c in state_immediate.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "1 MIN")
        assert c1m_imm["available"] is False

        # Accumulate 60 seconds continuous post-gap
        rec_t = datetime(2026, 8, 11, 4, 11, 0, tzinfo=timezone.utc)
        state_rec = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0}}, now=rec_t)
        c1m_rec = next(c for c in state_rec.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "1 MIN")
        assert c1m_rec["available"] is True
        assert c1m_rec["continuity_valid"] is True

    def test_post_gap_5m_recovery(self):
        base_t = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=base_t)
        # Gap of 10 minutes
        gap_t = datetime(2026, 8, 11, 4, 10, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=gap_t)
        
        # 3 minutes post-gap (continuous 1m steps 04:11, 04:12, 04:13) -> 5M still unavailable
        for i in [1, 2, 3]:
            t_3m = datetime(2026, 8, 11, 4, 10 + i, 0, tzinfo=timezone.utc)
            state_3m = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0 + i}}, now=t_3m)
        c5m_3m = next(c for c in state_3m.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "5 MIN")
        assert c5m_3m["available"] is False

        # Monotonic progression to 04:15 (5m continuous post-gap from 04:10)
        for i in [4, 5]:
            t_sub = datetime(2026, 8, 11, 4, 10 + i, 0, tzinfo=timezone.utc)
            state_rec = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0 + i}}, now=t_sub)
        
        c5m_rec = next(c for c in state_rec.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "5 MIN")
        assert c5m_rec["available"] is True
        assert c5m_rec["continuity_valid"] is True

    def test_post_gap_15m_recovery(self):
        base_t = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=base_t)
        # Gap of 20 minutes
        gap_t = datetime(2026, 8, 11, 4, 20, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=gap_t)
        
        # 10 minutes post gap -> 15M still unavailable
        for i in range(1, 11):
            t_sub = datetime(2026, 8, 11, 4, 20 + i, 0, tzinfo=timezone.utc)
            state_mid = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0 + i}}, now=t_sub)
        c15_mid = next(c for c in state_mid.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "15 MIN")
        assert c15_mid["available"] is False

        # 15 minutes continuous post gap -> 15M recovers
        for i in range(11, 16):
            t_sub = datetime(2026, 8, 11, 4, 20 + i, 0, tzinfo=timezone.utc)
            state_rec = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0 + i}}, now=t_sub)
        c15_rec = next(c for c in state_rec.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "15 MIN")
        assert c15_rec["available"] is True
        assert c15_rec["continuity_valid"] is True

    def test_internal_gap_rejection(self):
        # Spans 15m (14:00 to 14:15), but contains a 5m internal gap (14:05 to 14:10)
        t0 = datetime(2026, 8, 11, 8, 30, 0, tzinfo=timezone.utc) # 14:00 IST
        t5 = datetime(2026, 8, 11, 8, 35, 0, tzinfo=timezone.utc) # 14:05 IST
        t10 = datetime(2026, 8, 11, 8, 40, 0, tzinfo=timezone.utc) # 14:10 IST (5m gap > 120s)
        t15 = datetime(2026, 8, 11, 8, 45, 0, tzinfo=timezone.utc) # 14:15 IST

        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24505.0}}, now=t5)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24510.0}}, now=t10)
        state_15 = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24515.0}}, now=t15)

        c15 = next(c for c in state_15.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "15 MIN")
        assert c15["available"] is False
        assert c15["continuity_valid"] is False
        assert c15["status"] == "TELEMETRY_GAP"

    def test_no_interpolation(self):
        # Verify engine creates zero synthetic / interpolated snapshots
        WorkstationStateService._snapshots_history = []
        t0 = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t0)
        t1 = datetime(2026, 8, 11, 4, 30, 0, tzinfo=timezone.utc) # 30 min gap
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24550.0}}, now=t1)

        # Snapshots history length must be EXACTLY 2 (no synthetic intermediate entries)
        assert len(WorkstationStateService._snapshots_history) == 2
        assert WorkstationStateService._snapshots_history[0]["spot"] == 24500.0
        assert WorkstationStateService._snapshots_history[1]["spot"] == 24550.0

    def test_since_open_gap_metadata(self):
        t_open = datetime(2026, 8, 11, 3, 45, 0, tzinfo=timezone.utc)
        WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24500.0}}, now=t_open)
        t_gap = datetime(2026, 8, 11, 4, 15, 0, tzinfo=timezone.utc) # 30m gap
        state = WorkstationStateService.build_from_legacy({"marketContext": {"current_spot": 24520.0}}, now=t_gap)

        so = next(c for c in state.live_assistant_temporal_state["comparisons"] if c["requested_window"] == "SINCE OPEN")
        assert so["available"] is True
        assert so["contains_telemetry_gap"] is True
        assert so["gap_count"] == 1
        assert so["largest_gap_seconds"] == 1800.0
        assert so["continuity_valid"] is False

    def test_heavyweights_unavailable_when_quotes_absent(self):
        dt = datetime(2026, 8, 11, 4, 0, 0, tzinfo=timezone.utc)
        payload = {"marketContext": {"current_spot": 24500.0, "breadth": {"advances": 10, "declines": 40}}, "macroIntelligence": {"quotes": {}}}
        state = WorkstationStateService.build_from_legacy(payload, now=dt)

        hw_fam = next(f for f in state.live_assistant_temporal_state["confirmation_families"] if f["family"] == "HEAVYWEIGHTS")
        assert hw_fam["status"] == "UNAVAILABLE"
        assert hw_fam["bias"] == "UNAVAILABLE"
