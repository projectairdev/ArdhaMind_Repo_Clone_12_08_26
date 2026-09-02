from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class CutoverStatus(str, Enum):
    NOT_READY = "NOT_READY"
    READY_FOR_LIVE_VALIDATION = "READY_FOR_LIVE_VALIDATION"
    READY_FOR_CUTOVER = "READY_FOR_CUTOVER"


@dataclass(frozen=True)
class EnhancedCutoverReport:
    """Comprehensive readiness evaluation across market data, analytics, decision, and reliability."""
    status: CutoverStatus
    evaluated_at: datetime
    gate_results: Dict[str, bool]
    passed_gates_count: int
    total_gates_count: int
    readiness_percentage: float
    blocking_reasons: List[str]
    live_dhan_proof_verified: bool


class EnhancedCutoverEvaluator:
    """Evaluates full system cutover readiness."""

    @staticmethod
    def evaluate(
        gate_inputs: Dict[str, Any],
        live_dhan_proof_verified: bool = False,
    ) -> EnhancedCutoverReport:
        now_utc = datetime.now(timezone.utc)
        gates: Dict[str, bool] = {}
        blockers: List[str] = []

        # 13 Core Foundation Gates
        gates["dhan_auth_verified"] = bool(gate_inputs.get("dhan_auth_verified", False))
        gates["websocket_connected"] = bool(gate_inputs.get("websocket_connected", False))
        gates["subscriptions_active"] = bool(gate_inputs.get("active_subscriptions_count", 0) >= gate_inputs.get("desired_subscriptions_count", 2))
        gates["nifty_ticks_observed"] = bool(gate_inputs.get("nifty_ticks_observed_count", 0) > 0)
        gates["feed_health_operational"] = gate_inputs.get("feed_health_status") in ("HEALTHY", "RECOVERING")
        gates["session_authority_valid"] = bool(gate_inputs.get("session_authority_valid", False))
        gates["session_integrity_verified"] = not bool(gate_inputs.get("has_session_mismatch", False))
        gates["candle_engine_progressing"] = bool(gate_inputs.get("candles_count", 0) > 0)
        gates["reconciliation_functioning"] = bool(gate_inputs.get("reconciliation_functioning", False))
        gates["historical_bootstrap_functioning"] = bool(gate_inputs.get("historical_bootstrap_functioning", False))
        gates["option_chain_functioning"] = bool(gate_inputs.get("option_chain_functioning", False))
        gates["shadow_comparison_matching"] = gate_inputs.get("shadow_comparison_status") in ("MATCH", "CANONICAL_NEWER")
        gates["zero_fabrication_confirmed"] = (gate_inputs.get("fabricated_values_count", 0) == 0)

        # Wave 7 Engineering Assurance Gates
        gates["replay_reproducibility_verified"] = bool(gate_inputs.get("replay_reproducible", True))
        gates["observability_operational"] = bool(gate_inputs.get("observability_healthy", True))
        gates["frontend_export_contract_verified"] = bool(gate_inputs.get("export_contract_valid", True))
        gates["fail_safe_policies_active"] = bool(gate_inputs.get("failsafe_active", True))

        for gname, passed in gates.items():
            if not passed:
                blockers.append(f"Gate failed: {gname}")

        passed_cnt = sum(1 for p in gates.values() if p)
        total_cnt = len(gates)
        pct = round((passed_cnt / total_cnt) * 100.0, 1)

        # Cutover state resolution
        if not live_dhan_proof_verified:
            status = CutoverStatus.READY_FOR_LIVE_VALIDATION
            blockers.append("Live Dhan market-hours proof is pending (execute validate_live_dhan during open session)")
        elif passed_cnt == total_cnt:
            status = CutoverStatus.READY_FOR_CUTOVER
        else:
            status = CutoverStatus.NOT_READY

        return EnhancedCutoverReport(
            status=status,
            evaluated_at=now_utc,
            gate_results=gates,
            passed_gates_count=passed_cnt,
            total_gates_count=total_cnt,
            readiness_percentage=pct,
            blocking_reasons=blockers,
            live_dhan_proof_verified=live_dhan_proof_verified,
        )
