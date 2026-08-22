"""
src/intelligence_engine/decision_summary_composer.py

Thin, deterministic composer for the Market Intelligence Trader Decision Summary Layer.
Distills canonical Unified Nifty Intelligence, Opportunity Engine, Confidence, Risk,
and Data Quality into a compact, trader-facing decision object without creating any
new analytical pipelines or modifying existing calculations.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class DecisionLiquidityPolicy:
    """Configurable policy for evaluating option strike liquidity."""
    policy_version: str = "1.0.0"
    max_spread_bps: float = 250.0
    min_volume: int = 1000
    min_open_interest: int = 25000
    min_depth_quantity: int = 50

    def evaluate_liquidity(self, option_data: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Evaluates contract depth and returns (Grade, Reasons)."""
        if not option_data:
            return "UNAVAILABLE", ["No option chain data"]

        reasons = []
        spread_bps = option_data.get("bid_ask_spread_bps")
        volume = option_data.get("volume", 0) or 0
        oi = option_data.get("oi", 0) or 0

        if spread_bps is None and volume == 0 and oi == 0:
            return "UNAVAILABLE", ["Insufficient depth metrics"]

        is_spread_ok = (spread_bps is not None and spread_bps <= self.max_spread_bps)
        is_vol_ok = volume >= self.min_volume
        is_oi_ok = oi >= self.min_open_interest

        if not is_spread_ok and spread_bps is not None:
            reasons.append(f"Spread {spread_bps:.0f} bps exceeds policy limit {self.max_spread_bps:.0f} bps")
        if not is_vol_ok:
            reasons.append(f"Volume {volume} below minimum {self.min_volume}")
        if not is_oi_ok:
            reasons.append(f"OI {oi} below minimum {self.min_open_interest}")

        if is_spread_ok and is_vol_ok and is_oi_ok:
            return "EXCELLENT" if (spread_bps is not None and spread_bps <= 100.0) else "GOOD", []
        elif is_spread_ok or is_oi_ok:
            return "FAIR", reasons
        else:
            return "POOR", reasons


@dataclass
class FieldStatus:
    """Typed container preserving field value alongside its distinct availability state."""
    value: Any = None
    status: str = "AVAILABLE"  # AVAILABLE | NOT_QUALIFIED | STALE | UNAVAILABLE | WAITING | DEGRADED

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "status": self.status}


@dataclass
class MarketDecisionSummary:
    """Typed DTO representing the Trader Decision Summary Layer."""
    decision_id: str
    as_of: str
    session_date: str
    session_phase: str  # MORNING_PLAN | LIVE_GUIDE | TOMORROW_PLAN | MARKET_CLOSED

    bias: FieldStatus
    setup: FieldStatus
    strike: FieldStatus
    entry_condition: FieldStatus
    confidence: FieldStatus
    liquidity: FieldStatus
    data_quality: FieldStatus
    risk: FieldStatus
    status: str  # WAITING | WATCH | QUALIFYING | READY_FOR_APPROVAL | BLOCKED | INVALIDATED | EXPIRED | UNAVAILABLE | MARKET_CLOSED

    invalidation: Optional[str] = None
    supporting_evidence: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "as_of": self.as_of,
            "session_date": self.session_date,
            "session_phase": self.session_phase,
            "bias": self.bias.to_dict(),
            "setup": self.setup.to_dict(),
            "strike": self.strike.to_dict(),
            "entry_condition": self.entry_condition.to_dict(),
            "confidence": self.confidence.to_dict(),
            "liquidity": self.liquidity.to_dict(),
            "data_quality": self.data_quality.to_dict(),
            "risk": self.risk.to_dict(),
            "status": self.status,
            "invalidation": self.invalidation,
            "supporting_evidence": list(self.supporting_evidence),
            "blocking_reasons": list(self.blocking_reasons),
            "provenance": dict(self.provenance)
        }


class MarketDecisionSummaryComposer:
    """
    Deterministic composer that builds MarketDecisionSummary from existing canonical objects.
    """

    @classmethod
    def compose(
        cls,
        context: Dict[str, Any],
        liquidity_policy: Optional[DecisionLiquidityPolicy] = None
    ) -> MarketDecisionSummary:
        policy = liquidity_policy or DecisionLiquidityPolicy()
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # 1. Extract context components
        market_ctx = context.get("market_context") or {}
        option_ctx = context.get("option_context") or {}
        breadth = context.get("breadth") or {}
        unified_intel = context.get("unified_intelligence") or {}
        opp_list = context.get("opportunities") or []
        opp_intel = opp_list[0] if (opp_list and isinstance(opp_list, list)) else {}
        session_date = str(context.get("session_date") or datetime.now().strftime("%Y-%m-%d"))
        market_state = str(context.get("market_state") or "LIVE").upper()
        market_closed = context.get("market_closed") is True or market_state in ("CLOSED", "MARKET_CLOSED", "POST_CLOSE", "HOLIDAY", "WEEKEND")
        freshness_state = str(context.get("freshness_state") or "FRESH").upper()
        broker_auth_state = str(context.get("broker_auth_state") or "DISCONNECTED").upper()
        active_subtab = str(context.get("active_subtab") or ("LIVE_GUIDE" if not market_closed else "TOMORROW_PLAN")).upper()

        blocking_reasons: List[str] = []
        supporting_evidence: List[str] = []

        # 2. Derive BIAS
        raw_bias = unified_intel.get("market_bias") or unified_intel.get("preferred_bias") or market_ctx.get("trend")
        if raw_bias and str(raw_bias).upper() in ("BULLISH", "BEARISH", "NEUTRAL", "MIXED"):
            bias_val = str(raw_bias).upper()
            bias_field = FieldStatus(value=bias_val, status="AVAILABLE")
        else:
            bias_field = FieldStatus(value=None, status="UNAVAILABLE")

        # 3. Derive SETUP
        raw_setup = opp_intel.get("strategy_name") or opp_intel.get("name")
        if not raw_setup and unified_intel.get("morning_plan"):
            raw_setup = (unified_intel.get("morning_plan") or {}).get("primary_scenario_name")

        if raw_setup and str(raw_setup).strip():
            setup_name = str(raw_setup).strip().upper()
            setup_field = FieldStatus(value=setup_name, status="AVAILABLE")
        else:
            setup_field = FieldStatus(value="NO_VALID_SETUP", status="NOT_QUALIFIED")
            if not market_closed:
                blocking_reasons.append("NO_VALID_SETUP")

        # 4. Derive STRIKE & LIQUIDITY
        target_contract = opp_intel.get("contract") or {}
        strike_sym = target_contract.get("symbol") or opp_intel.get("target_strike")
        opt_status = str(option_ctx.get("status") or "AVAILABLE").upper()
        is_opt_stale = opt_status in ("STALE", "UNAVAILABLE", "DISCONNECTED") or freshness_state == "STALE"

        if market_closed:
            strike_field = FieldStatus(value=None, status="REQUIRES_LIVE_OPTIONS")
            liquidity_field = FieldStatus(value="UNAVAILABLE", status="UNAVAILABLE")
        elif is_opt_stale:
            strike_field = FieldStatus(value=None, status="WAITING_FOR_OPTIONS_CONFIRMATION")
            liquidity_field = FieldStatus(value="UNAVAILABLE", status="STALE")
            blocking_reasons.append("OPTIONS_FEED_STALE")
        elif strike_sym:
            strike_field = FieldStatus(value=str(strike_sym), status="AVAILABLE")
            liq_grade, liq_reasons = policy.evaluate_liquidity(target_contract)
            liquidity_field = FieldStatus(value=liq_grade, status="AVAILABLE" if liq_grade != "UNAVAILABLE" else "UNAVAILABLE")
            if liq_grade in ("POOR", "UNAVAILABLE"):
                blocking_reasons.append("LIQUIDITY_POOR")
        else:
            strike_field = FieldStatus(value=None, status="NOT_QUALIFIED")
            liquidity_field = FieldStatus(value="UNAVAILABLE", status="NOT_QUALIFIED")
            if not market_closed and setup_field.status == "AVAILABLE":
                blocking_reasons.append("STRIKE_NOT_QUALIFIED")

        # 5. Derive ENTRY CONDITION & INVALIDATION
        entry_raw = opp_intel.get("entry_trigger_statement") or opp_intel.get("trigger_statement")
        invalidation_raw = opp_intel.get("invalidation_statement") or opp_intel.get("invalidation_level")
        if not invalidation_raw and unified_intel.get("decision_zones"):
            invalidation_raw = (unified_intel.get("decision_zones") or {}).get("invalidation")

        if entry_raw:
            entry_dict = {
                "primary_trigger": str(entry_raw),
                "confirmation_conditions": opp_intel.get("confirmation_conditions") or [],
                "invalidation_condition": str(invalidation_raw or "Structural breach"),
                "formatted_statement": str(entry_raw)
            }
            entry_field = FieldStatus(value=entry_dict, status="AVAILABLE")
        else:
            entry_field = FieldStatus(value=None, status="WAITING_FOR_TRIGGER")

        # 6. Derive CONFIDENCE
        scores = opp_intel.get("scores") or {}
        conf_val = scores.get("confidence_score") or opp_intel.get("confidence")
        if conf_val is not None and isinstance(conf_val, (int, float)):
            conf_int = int(round(float(conf_val)))
            conf_field = FieldStatus(value=conf_int, status="DEGRADED" if freshness_state == "STALE" else "AVAILABLE")
        else:
            conf_field = FieldStatus(value=None, status="UNAVAILABLE")

        # 7. Derive DATA QUALITY
        dq_status = context.get("data_quality_status") or ("HIGH" if freshness_state == "FRESH" else "DEGRADED")
        data_quality_field = FieldStatus(value=str(dq_status).upper(), status="AVAILABLE")

        # 8. Derive RISK
        risk_val = context.get("overall_risk") or opp_intel.get("risk_grade") or "MODERATE"
        risk_field = FieldStatus(value=str(risk_val).upper(), status="AVAILABLE")

        # 9. Build Supporting Evidence Chips (Max 3-5)
        spot_val = float(market_ctx.get("current_spot") or market_ctx.get("spot") or 0.0)
        vwap_val = float(market_ctx.get("vwap") or 0.0)
        if spot_val > 0 and vwap_val > 0:
            if spot_val >= vwap_val:
                supporting_evidence.append(f"Above VWAP ({vwap_val:.1f})")
            else:
                supporting_evidence.append(f"Below VWAP ({vwap_val:.1f})")

        adv = breadth.get("advances")
        dec = breadth.get("declines")
        if adv is not None and dec is not None:
            supporting_evidence.append(f"Breadth {adv}A / {dec}D")

        put_wall = option_ctx.get("put_wall")
        call_wall = option_ctx.get("call_wall")
        if bias_field.value == "BULLISH" and put_wall:
            supporting_evidence.append(f"Put Wall Support ({put_wall})")
        elif bias_field.value == "BEARISH" and call_wall:
            supporting_evidence.append(f"Call Wall Resistance ({call_wall})")

        vix_val = market_ctx.get("india_vix") or market_ctx.get("vix")
        if vix_val and isinstance(vix_val, (int, float)):
            supporting_evidence.append(f"India VIX {vix_val:.2f}")

        # 10. Evaluate STATUS State Machine & Mandatory Safety Contract
        # Check feed freshness blocking reasons
        if freshness_state == "STALE":
            blocking_reasons.append("MARKET_FEED_STALE")
        if breadth.get("status") == "UNAVAILABLE" or (adv is None and dec is None and not market_closed):
            blocking_reasons.append("BREADTH_INSUFFICIENT_COVERAGE")
        if context.get("reconciliation_status") == "PENDING":
            blocking_reasons.append("RECONCILIATION_PENDING")

        # Mandatory Correction #2: Broker Auth separation
        broker_auth_ok = (broker_auth_state in ("AUTHENTICATED", "CONNECTED_VERIFIED"))
        if not broker_auth_ok and not market_closed:
            blocking_reasons.append("BROKER_AUTH_REQUIRED")

        # Status determination
        if market_closed:
            final_status = "MARKET_CLOSED"
        elif active_subtab == "MORNING_PLAN":
            final_status = "WATCH"
        elif active_subtab == "TOMORROW_PLAN":
            final_status = "MARKET_CLOSED"
        elif freshness_state == "STALE" or is_opt_stale:
            final_status = "BLOCKED"
        elif setup_field.status != "AVAILABLE":
            final_status = "WAITING"
        elif strike_field.status != "AVAILABLE" or liquidity_field.value in ("POOR", "UNAVAILABLE"):
            final_status = "QUALIFYING"
        elif invalidation_raw is None:
            final_status = "QUALIFYING"
            blocking_reasons.append("MISSING_INVALIDATION")
        elif not broker_auth_ok:
            # All analytical gates pass, but broker auth is required for execution approval
            final_status = "QUALIFYING"
        elif opp_intel.get("status") == "INVALIDATED":
            final_status = "INVALIDATED"
        else:
            # All 8 safety gates passed!
            final_status = "READY_FOR_APPROVAL"

        # 11. Mandatory Correction #3: Stable Deterministic Decision Identity
        # Use opportunity_id if available, or hash (session_date, setup, direction, strike, trigger_zone_bin)
        opp_id = opp_intel.get("opportunity_id") or opp_intel.get("id")
        if opp_id:
            decision_id = f"DEC-{opp_id}"
        else:
            # Deterministic binning: 50-point price bin to prevent tick churn
            trigger_bin = int(round(spot_val / 50.0) * 50) if spot_val > 0 else 0
            hash_input = f"{session_date}:{setup_field.value}:{bias_field.value}:{strike_field.value}:{trigger_bin}"
            hash_digest = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:12]
            decision_id = f"DEC-{session_date.replace('-', '')}-{hash_digest}"

        provenance = {
            "canonical_sequence": context.get("sequence", 0),
            "runtime_id": context.get("runtime_id", "ardha-staging"),
            "opportunity_id": opp_id,
            "strategy_id": opp_intel.get("strategy_id"),
            "liquidity_policy_version": policy.policy_version,
            "evidence_sources": ["UnifiedNiftyIntelligence", "OpportunityRegistry", "OptionChain", "DataQualityService"],
            "freshness_summary": {
                "spot_freshness": "FRESH" if freshness_state == "FRESH" else "STALE",
                "options_freshness": "FRESH" if not is_opt_stale else "STALE",
                "breadth_coverage": f"{adv or 0}A / {dec or 0}D"
            }
        }

        return MarketDecisionSummary(
            decision_id=decision_id,
            as_of=now_utc,
            session_date=session_date,
            session_phase=active_subtab,
            bias=bias_field,
            setup=setup_field,
            strike=strike_field,
            entry_condition=entry_field,
            confidence=conf_field,
            liquidity=liquidity_field,
            data_quality=data_quality_field,
            risk=risk_field,
            status=final_status,
            invalidation=str(invalidation_raw) if invalidation_raw else None,
            supporting_evidence=supporting_evidence[:5],
            blocking_reasons=list(dict.fromkeys(blocking_reasons)),
            provenance=provenance
        )
