from __future__ import annotations

from datetime import datetime, timezone
import pytest

from src.decision.models.decision_models import DecisionState
from src.market_data.models.quality_enums import DataQualityStatus
from src.observability.failsafe_policy import FailSafePolicy
from src.observability.frontend_export_contract import (
    CanonicalFrontendEnvelope,
    FrontendConvergenceHandler,
)
from src.observability.incident_snapshot import IncidentSnapshotBuilder
from src.observability.latency_tracker import LatencyTracker
from src.observability.pipeline_health import PipelineHealthEvaluator, PipelineHealthStatus
from src.observability.runtime_metrics import RuntimeMetricsCollector
from src.observability.structured_logger import StructuredLogger


def test_1_runtime_metrics_and_health_evaluator():
    metrics = RuntimeMetricsCollector()
    metrics.record_tick_accepted()
    metrics.record_tick_rejected(reason="OUT_OF_ORDER")
    snap = metrics.get_snapshot()

    assert snap["live_state"]["accepted"] == 1
    assert snap["live_state"]["out_of_order"] == 1

    health = PipelineHealthEvaluator.evaluate(
        is_running=True,
        socket_connected=True,
        feed_status="HEALTHY",
        session_valid=True,
        event_bus_overflow=False,
        candles_count=10,
        analytics_quality=DataQualityStatus.VALID,
    )
    assert health.overall_status == PipelineHealthStatus.HEALTHY


def test_2_latency_tracking_telemetry():
    t0 = datetime(2026, 8, 28, 9, 15, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 8, 28, 9, 15, 0, 50000, tzinfo=timezone.utc)   # +50ms
    t2 = datetime(2026, 8, 28, 9, 15, 0, 70000, tzinfo=timezone.utc)   # +20ms
    t3 = datetime(2026, 8, 28, 9, 15, 0, 90000, tzinfo=timezone.utc)   # +20ms
    t4 = datetime(2026, 8, 28, 9, 15, 0, 100000, tzinfo=timezone.utc)  # +10ms
    t5 = datetime(2026, 8, 28, 9, 15, 0, 110000, tzinfo=timezone.utc)  # +10ms

    lat = LatencyTracker.measure_latency(t0, t1, t2, t3, t4, t5)
    assert lat.exchange_to_receive_ms == 50.0
    assert lat.receive_to_state_ms == 20.0
    assert lat.state_to_analytics_ms == 20.0
    assert lat.total_pipeline_ms == 110.0


def test_3_incident_snapshot_secret_redaction():
    inc = IncidentSnapshotBuilder.capture(
        incident_type="AUTH_FAILURE",
        error_message="Invalid token",
        pipeline_status="DEGRADED",
        session_data={"session_date": "2026-08-28"},
        provider_diag={"dhan_access_token": "SUPER_SECRET_TOKEN_123", "client_id": "DHAN123"},
        feed_health_data={"status": "STALE"},
        live_state_data={"price": 24500.0},
        analytics_quality_str="VALID",
        decision_state_str="BLOCKED",
    )

    data = inc.to_dict()
    # Ensure sensitive fields are recursively redacted
    assert data["provider_diagnostics"]["dhan_access_token"] == "[REDACTED]"
    assert data["provider_diagnostics"]["client_id"] == "DHAN123"


def test_4_failsafe_policy_and_last_known_value():
    t_obs = datetime(2026, 8, 28, 9, 15, 0, tzinfo=timezone.utc)
    t_curr_fresh = datetime(2026, 8, 28, 9, 15, 1, tzinfo=timezone.utc)
    t_curr_stale = datetime(2026, 8, 28, 9, 15, 30, tzinfo=timezone.utc)

    # Fresh value
    fresh_rec = FailSafePolicy.format_last_known_value("IDX:NSE:NIFTY_50", 24500.0, t_obs, t_curr_fresh)
    assert fresh_rec.is_stale is False
    assert "LIVE" in fresh_rec.display_label

    # Stale value
    stale_rec = FailSafePolicy.format_last_known_value("IDX:NSE:NIFTY_50", 24500.0, t_obs, t_curr_stale)
    assert stale_rec.is_stale is True
    assert "STALE" in stale_rec.display_label


def test_5_frontend_convergence_across_server_restarts():
    handler = FrontendConvergenceHandler()
    t_now = datetime.now(timezone.utc)

    env1 = CanonicalFrontendEnvelope("runtime_A", 10, t_now, {}, {}, {}, {}, {}, {}, {}, "VALID")
    accept1, _ = handler.evaluate_incoming_envelope(env1)
    assert accept1 is True

    # Same runtime, higher revision -> Accept
    env2 = CanonicalFrontendEnvelope("runtime_A", 11, t_now, {}, {}, {}, {}, {}, {}, {}, "VALID")
    accept2, _ = handler.evaluate_incoming_envelope(env2)
    assert accept2 is True

    # Same runtime, stale lower revision -> Reject
    env_stale = CanonicalFrontendEnvelope("runtime_A", 9, t_now, {}, {}, {}, {}, {}, {}, {}, "VALID")
    accept_stale, _ = handler.evaluate_incoming_envelope(env_stale)
    assert accept_stale is False

    # Server restarted (runtime_B, lower revision = 1) -> Must accept immediately without sequence locking!
    env_restart = CanonicalFrontendEnvelope("runtime_B", 1, t_now, {}, {}, {}, {}, {}, {}, {}, "VALID")
    accept_restart, reason_restart = handler.evaluate_incoming_envelope(env_restart)
    assert accept_restart is True
    assert "ACCEPTED_NEW_RUNTIME_INSTANCE" in reason_restart
