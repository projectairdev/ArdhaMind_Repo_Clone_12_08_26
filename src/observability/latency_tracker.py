from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class LatencyTelemetry:
    """Latency metrics across each stage of the canonical pipeline."""
    exchange_to_receive_ms: Optional[float]
    receive_to_state_ms: Optional[float]
    state_to_analytics_ms: Optional[float]
    analytics_to_decision_ms: Optional[float]
    decision_to_export_ms: Optional[float]
    total_pipeline_ms: Optional[float]


class LatencyTracker:
    """Computes stage-to-stage latency without synthesizing unavailable timestamps."""

    @staticmethod
    def measure_latency(
        exchange_ts: Optional[datetime],
        received_ts: Optional[datetime],
        state_applied_ts: Optional[datetime],
        analytics_ts: Optional[datetime],
        decision_ts: Optional[datetime],
        export_ts: Optional[datetime],
    ) -> LatencyTelemetry:
        def diff_ms(t_start: Optional[datetime], t_end: Optional[datetime]) -> Optional[float]:
            if t_start and t_end:
                return round(max(0.0, (t_end - t_start).total_seconds() * 1000.0), 2)
            return None

        e_to_r = diff_ms(exchange_ts, received_ts)
        r_to_s = diff_ms(received_ts, state_applied_ts)
        s_to_a = diff_ms(state_applied_ts, analytics_ts)
        a_to_d = diff_ms(analytics_ts, decision_ts)
        d_to_x = diff_ms(decision_ts, export_ts)
        total = diff_ms(exchange_ts or received_ts, export_ts or decision_ts)

        return LatencyTelemetry(
            exchange_to_receive_ms=e_to_r,
            receive_to_state_ms=r_to_s,
            state_to_analytics_ms=s_to_a,
            analytics_to_decision_ms=a_to_d,
            decision_to_export_ms=d_to_x,
            total_pipeline_ms=total,
        )
