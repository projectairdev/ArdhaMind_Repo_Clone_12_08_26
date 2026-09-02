from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GateStatus:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class CutoverReadinessReport:
    """
    Authoritative evaluation of whether the new canonical pipeline is ready for production cutover.
    CANONICAL_READY_FOR_CUTOVER is True if and only if ALL 13 gates pass.
    """
    is_ready: bool
    gates: Dict[str, GateStatus]
    failing_gates: List[str]
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CutoverGateEvaluator:
    """
    Evaluates 13 strict invariants before allowing production cutover to Dhan canonical market data.
    """

    REQUIRED_GATES = [
        "1_dhan_auth_verified",
        "2_websocket_connected",
        "3_desired_subscriptions_active",
        "4_real_nifty_ticks_observed",
        "5_feed_healthy",
        "6_session_authority_correct",
        "7_no_session_mismatch",
        "8_candles_updating",
        "9_rest_reconciliation_functioning",
        "10_historical_bootstrap_functioning",
        "11_option_chain_functioning",
        "12_shadow_comparison_acceptable",
        "13_zero_fabricated_fallback_values",
    ]

    def evaluate_gates(self, gate_inputs: Dict[str, Any]) -> CutoverReadinessReport:
        gate_statuses: Dict[str, GateStatus] = {}
        failing: List[str] = []

        # 1. Dhan Auth
        g1_pass = bool(gate_inputs.get("dhan_auth_verified", False))
        gate_statuses["1_dhan_auth_verified"] = GateStatus("1_dhan_auth_verified", g1_pass, "Dhan credentials authenticated" if g1_pass else "Dhan authentication not verified")
        if not g1_pass: failing.append("1_dhan_auth_verified")

        # 2. WebSocket Connected
        g2_pass = bool(gate_inputs.get("websocket_connected", False))
        gate_statuses["2_websocket_connected"] = GateStatus("2_websocket_connected", g2_pass, "WebSocket connected" if g2_pass else "WebSocket disconnected")
        if not g2_pass: failing.append("2_websocket_connected")

        # 3. Subscriptions Active
        desired_cnt = gate_inputs.get("desired_subscriptions_count", 0)
        active_cnt = gate_inputs.get("active_subscriptions_count", 0)
        g3_pass = desired_cnt > 0 and active_cnt >= desired_cnt
        gate_statuses["3_desired_subscriptions_active"] = GateStatus("3_desired_subscriptions_active", g3_pass, f"Active: {active_cnt}/{desired_cnt}" if g3_pass else f"Subscriptions missing: {active_cnt}/{desired_cnt}")
        if not g3_pass: failing.append("3_desired_subscriptions_active")

        # 4. Real NIFTY ticks observed
        ticks_obs = gate_inputs.get("nifty_ticks_observed_count", 0)
        g4_pass = ticks_obs > 0
        gate_statuses["4_real_nifty_ticks_observed"] = GateStatus("4_real_nifty_ticks_observed", g4_pass, f"Observed {ticks_obs} live ticks" if g4_pass else "Zero live ticks observed")
        if not g4_pass: failing.append("4_real_nifty_ticks_observed")

        # 5. Feed Healthy
        feed_health = gate_inputs.get("feed_health_status", "")
        g5_pass = str(feed_health).upper() == "HEALTHY"
        gate_statuses["5_feed_healthy"] = GateStatus("5_feed_healthy", g5_pass, f"Status: {feed_health}" if g5_pass else f"Feed not healthy: {feed_health}")
        if not g5_pass: failing.append("5_feed_healthy")

        # 6. Session Authority Correct
        g6_pass = bool(gate_inputs.get("session_authority_valid", False))
        gate_statuses["6_session_authority_correct"] = GateStatus("6_session_authority_correct", g6_pass, "Session authority valid" if g6_pass else "Session authority invalid")
        if not g6_pass: failing.append("6_session_authority_correct")

        # 7. No Session Mismatch
        sess_mismatch = bool(gate_inputs.get("has_session_mismatch", False))
        g7_pass = not sess_mismatch
        gate_statuses["7_no_session_mismatch"] = GateStatus("7_no_session_mismatch", g7_pass, "No session mismatch" if g7_pass else "Session mismatch detected")
        if not g7_pass: failing.append("7_no_session_mismatch")

        # 8. Candles Updating
        candles_cnt = gate_inputs.get("candles_count", 0)
        g8_pass = candles_cnt > 0
        gate_statuses["8_candles_updating"] = GateStatus("8_candles_updating", g8_pass, f"Candles active: {candles_cnt}" if g8_pass else "No candles updating")
        if not g8_pass: failing.append("8_candles_updating")

        # 9. REST Reconciliation Functioning
        g9_pass = bool(gate_inputs.get("reconciliation_functioning", False))
        gate_statuses["9_rest_reconciliation_functioning"] = GateStatus("9_rest_reconciliation_functioning", g9_pass, "Reconciliation active" if g9_pass else "Reconciliation not active")
        if not g9_pass: failing.append("9_rest_reconciliation_functioning")

        # 10. Historical Bootstrap Functioning
        g10_pass = bool(gate_inputs.get("historical_bootstrap_functioning", False))
        gate_statuses["10_historical_bootstrap_functioning"] = GateStatus("10_historical_bootstrap_functioning", g10_pass, "Historical bootstrap verified" if g10_pass else "Bootstrap unverified")
        if not g10_pass: failing.append("10_historical_bootstrap_functioning")

        # 11. Option Chain Functioning
        g11_pass = bool(gate_inputs.get("option_chain_functioning", False))
        gate_statuses["11_option_chain_functioning"] = GateStatus("11_option_chain_functioning", g11_pass, "Option chain verified" if g11_pass else "Option chain unverified")
        if not g11_pass: failing.append("11_option_chain_functioning")

        # 12. Shadow Comparison Acceptable
        shadow_stat = gate_inputs.get("shadow_comparison_status", "")
        g12_pass = str(shadow_stat).upper() in ("MATCH", "WITHIN_TOLERANCE", "ACCEPTABLE")
        gate_statuses["12_shadow_comparison_acceptable"] = GateStatus("12_shadow_comparison_acceptable", g12_pass, f"Comparison status: {shadow_stat}" if g12_pass else f"Comparison unacceptable: {shadow_stat}")
        if not g12_pass: failing.append("12_shadow_comparison_acceptable")

        # 13. Zero Fabricated Fallback Values
        fab_count = gate_inputs.get("fabricated_values_count", 0)
        g13_pass = fab_count == 0
        gate_statuses["13_zero_fabricated_fallback_values"] = GateStatus("13_zero_fabricated_fallback_values", g13_pass, "Zero fabricated values" if g13_pass else f"Detected {fab_count} fabricated values")
        if not g13_pass: failing.append("13_zero_fabricated_fallback_values")

        is_all_ready = len(failing) == 0

        return CutoverReadinessReport(
            is_ready=is_all_ready,
            gates=gate_statuses,
            failing_gates=failing,
            evaluated_at=datetime.now(timezone.utc),
        )
