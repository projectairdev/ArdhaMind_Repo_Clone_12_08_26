"""
src/intelligence_engine/decision_summary_composer.py

Thin, deterministic composer for the Market Intelligence Trader Decision Summary Layer.
Distills canonical Unified Nifty Intelligence, Opportunity Engine, Confidence, Risk,
Strike Strength, and Entry Quality into a compact, trader-facing decision object without
creating any new analytical pipelines or modifying existing calculations.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from src.intelligence_engine.trader_decision_engine import (
    TraderDecisionEngine,
    TraderDecision,
    TradeCandidate,
)
from src.intelligence_engine.strike_strength_engine import StrikeStrengthEngine
from src.intelligence_engine.entry_quality_engine import EntryQualityEngine


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
    status: str  # WAITING | WATCH | QUALIFYING | CONDITIONS_PENDING | QUALIFIED | READY_FOR_APPROVAL | BLOCKED | INVALIDATED | EXPIRED | UNAVAILABLE | MARKET_CLOSED

    invalidation: Optional[str] = None
    target: Optional[str] = None
    risk_reward: Optional[str] = None
    strike_strength: Optional[Dict[str, Any]] = None
    entry_quality: Optional[Dict[str, Any]] = None
    nearby_strikes: List[Dict[str, Any]] = field(default_factory=list)
    trade_candidate: Optional[Dict[str, Any]] = None
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
            "target": self.target,
            "risk_reward": self.risk_reward,
            "strike_strength": self.strike_strength,
            "entry_quality": self.entry_quality,
            "nearby_strikes": self.nearby_strikes,
            "trade_candidate": self.trade_candidate,
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

        # 1. Delegate core logic to TraderDecisionEngine
        trader_dec = TraderDecisionEngine.evaluate_trader_decision(context)

        # 2. Extract context components
        market_ctx = context.get("market_context") or {}
        option_ctx = context.get("option_context") or {}
        breadth = context.get("breadth") or {}
        unified_intel = context.get("unified_intelligence") or {}
        session_date = str(context.get("session_date") or trader_dec.trading_date)
        market_state = str(context.get("market_state") or "LIVE").upper()
        market_closed = context.get("market_closed") is True or market_state in ("CLOSED", "MARKET_CLOSED", "POST_CLOSE", "HOLIDAY", "WEEKEND")
        freshness_state = str(context.get("freshness_state") or "FRESH").upper()
        active_subtab = str(context.get("active_subtab") or ("LIVE_GUIDE" if not market_closed else "TOMORROW_PLAN")).upper()

        # 3. Derive FieldStatus representations
        bias_field = FieldStatus(value=trader_dec.bias, status="AVAILABLE" if trader_dec.bias != "UNAVAILABLE" else "UNAVAILABLE")
        setup_field = FieldStatus(value=trader_dec.setup, status="AVAILABLE" if trader_dec.direction != "NO_TRADE" else "NOT_QUALIFIED")

        top_strike = trader_dec.strike_recommendation
        if market_closed:
            strike_field = FieldStatus(value=None, status="REQUIRES_LIVE_OPTIONS")
            liquidity_field = FieldStatus(value="UNAVAILABLE", status="UNAVAILABLE")
        elif top_strike:
            strike_field = FieldStatus(value=top_strike.get("symbol"), status="AVAILABLE")
            liquidity_field = FieldStatus(value=trader_dec.liquidity_quality, status="AVAILABLE")
        else:
            strike_field = FieldStatus(value=None, status="NOT_QUALIFIED")
            liquidity_field = FieldStatus(value="UNAVAILABLE", status="NOT_QUALIFIED")

        entry_field = FieldStatus(
            value={
                "primary_trigger": trader_dec.entry_condition,
                "confirmation_conditions": trader_dec.supporting_evidence,
                "invalidation_condition": str(trader_dec.invalidation) if trader_dec.invalidation else "Structural breach",
                "formatted_statement": trader_dec.entry_condition
            },
            status="AVAILABLE" if trader_dec.direction != "NO_TRADE" else "WAITING"
        )

        conf_field = FieldStatus(
            value=int(round(float(unified_intel.get("conviction", 60)))) if isinstance(unified_intel.get("conviction"), (int, float)) else (75 if trader_dec.confidence_band == "HIGH" else (60 if trader_dec.confidence_band == "MODERATE" else 35)),
            status="AVAILABLE"
        )

        data_quality_field = FieldStatus(value=trader_dec.data_quality, status="AVAILABLE")
        risk_field = FieldStatus(value=top_strike.get("premium_risk") if top_strike else "MODERATE", status="AVAILABLE")

        decision_id = f"DEC-{session_date.replace('-', '')}-{hashlib.sha256((session_date + trader_dec.setup + str(trader_dec.spot)).encode('utf-8')).hexdigest()[:10]}"

        provenance = {
            "canonical_sequence": context.get("sequence", 0),
            "runtime_id": context.get("runtime_id", "ardha-staging"),
            "liquidity_policy_version": policy.policy_version,
            "evidence_sources": ["TraderDecisionEngine", "StrikeStrengthEngine", "EntryQualityEngine", "UnifiedNiftyIntelligence"],
            "freshness_summary": {
                "spot_freshness": "FRESH" if freshness_state == "FRESH" else "STALE",
                "options_freshness": "FRESH" if not market_closed else "STALE",
                "breadth_coverage": f"{breadth.get('advances', 0)}A / {breadth.get('declines', 0)}D"
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
            status=trader_dec.approval_status if not market_closed else "MARKET_CLOSED",
            invalidation=f"NIFTY {'reclaims' if trader_dec.direction == 'PE' else 'breaks'} {trader_dec.invalidation:,.1f}" if trader_dec.invalidation else None,
            target=trader_dec.target,
            risk_reward=trader_dec.risk_reward,
            strike_strength=top_strike,
            entry_quality=trader_dec.entry_quality,
            nearby_strikes=trader_dec.nearby_strikes,
            trade_candidate=trader_dec.trade_candidate,
            supporting_evidence=trader_dec.supporting_evidence[:5],
            blocking_reasons=trader_dec.approval_blockers,
            provenance=provenance
        )
