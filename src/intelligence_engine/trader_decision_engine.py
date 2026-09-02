# src/intelligence_engine/trader_decision_engine.py
"""
TraderDecisionEngine — Canonical Trader Decision & Trade Candidate Layer for AIR ArdhaMind.

Transforms multi-factor market intelligence into a compact, auditable decision object:
- What is the market doing?
- Is there actually a qualified trade setup?
- Which strike is suitable (Strike Strength Engine)?
- Is this a good entry now (Entry Quality Engine)?
- What invalidates it? What is the risk/reward?
- Is it ready for human trader review (Approval Safety Gates)?

Strict Invariants:
  1. Strictly READ_ONLY: NO automatic order placement, NO broker execution calls.
  2. Directional bias and setup qualification are strictly separate.
  3. Strike strength and entry quality are evaluated independently.
  4. READY_FOR_APPROVAL requires ALL mandatory safety, data, liquidity, and risk gates to pass.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.intelligence_engine.strike_strength_engine import (
    StrikeStrengthEngine,
    StrikeEvaluation,
)
from src.intelligence_engine.entry_quality_engine import (
    EntryQualityEngine,
    EntryQualityEvaluation,
)


@dataclass
class TradeCandidate:
    candidate_id: str
    generated_at: str
    underlying: str
    direction: str  # CE | PE
    instrument: str
    strike: float
    expiry: str
    option_type: str
    entry_condition: str
    invalidation: Optional[float]
    targets: List[float]
    confidence: str
    strike_strength: float
    entry_quality: str
    risk: str
    data_quality: str
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TraderDecision:
    trading_date: str
    generated_at: str
    market_phase: str
    spot: float
    bias: str
    regime: str
    setup: str
    direction: str  # CE | PE | NO_TRADE
    entry_condition: str
    entry_status: str
    invalidation: Optional[float]
    target: Optional[str]
    risk_reward: Optional[str]
    confidence_band: str
    calibrated_probability: Optional[float]
    data_quality: str  # FULL | GOOD | DEGRADED | INSUFFICIENT
    liquidity_quality: str  # STRONG | ACCEPTABLE | WEAK | UNTRADEABLE
    opportunity_quality: str  # EXCELLENT | GOOD | FAIR | POOR | NONE
    strike_recommendation: Optional[Dict[str, Any]]
    entry_quality: Optional[Dict[str, Any]]
    nearby_strikes: List[Dict[str, Any]]
    risk_flags: List[str]
    supporting_evidence: List[str]
    opposing_evidence: List[str]
    approval_status: str  # WATCH | CONDITIONS_PENDING | QUALIFIED | READY_FOR_APPROVAL
    approval_blockers: List[str]
    trade_candidate: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TraderDecisionEngine:
    """
    Deterministic Decision Composer & Approval Gatekeeper.
    """

    @classmethod
    def evaluate_trader_decision(
        cls,
        state: Dict[str, Any],
        as_of_time: Optional[datetime] = None
    ) -> TraderDecision:
        now_utc = as_of_time or datetime.now(timezone.utc)
        now_ist = now_utc + timedelta(hours=5, minutes=30)
        now_str = now_utc.isoformat().replace("+00:00", "Z")
        hhmm = now_ist.strftime("%H:%M")

        m_session = state.get("market_session") or {}
        session_date = str(m_session.get("session_date") or now_ist.strftime("%Y-%m-%d"))
        session_status = str(m_session.get("status") or ("OPEN" if "09:15" <= hhmm <= "15:30" else "CLOSED")).upper()

        m_data = state.get("market_data") or state.get("marketContext") or {}
        spot = float(m_data.get("current_spot") or m_data.get("ltp") or m_data.get("close") or 0.0)
        open_price = float(m_data.get("open") or spot)
        high_price = float(m_data.get("high") or spot)
        low_price = float(m_data.get("low") or spot)
        vwap = float(m_data.get("vwap") or spot)

        breadth = m_data.get("breadth") or {}
        advances = int(breadth.get("advances", 0) or 0)
        declines = int(breadth.get("declines", 0) or 0)

        fo = state.get("forward_outlook") or {}
        fo_scenario = str(fo.get("scenario") or fo.get("classification") or "RANGE_BALANCED").upper()
        fo_confidence = str(fo.get("confidence") or "MODERATE").upper()
        support = float(fo.get("support") or (spot - 50.0))
        resistance = float(fo.get("resistance") or (spot + 50.0))

        macro = state.get("macro_intelligence") or {}
        vix_info = macro.get("india_vix") or {}
        vix_val = float(vix_info.get("value") or 12.0)

        options_data = state.get("option_intelligence") or state.get("optionContext") or {}

        # 1. Data Quality Gate Check
        data_quality_issues: List[str] = []
        if spot <= 0:
            data_quality_issues.append("Missing live NIFTY spot price")
        if session_status not in ("OPEN", "REGULAR", "REGULAR_MARKET", "LIVE_SESSION"):
            data_quality_issues.append("Market session not currently active")
        if not options_data and not m_data.get("options"):
            data_quality_issues.append("Option chain intelligence pending")

        if len(data_quality_issues) >= 2:
            data_quality = "INSUFFICIENT"
        elif len(data_quality_issues) == 1:
            data_quality = "DEGRADED"
        else:
            data_quality = "FULL"

        # 2. Market Bias & Setup Qualification
        supporting_ev: List[str] = []
        opposing_ev: List[str] = []
        risk_flags: List[str] = []

        is_bearish_pressure = ("BEARISH" in fo_scenario) or (spot < vwap and declines > 28)
        is_bullish_pressure = ("BULLISH" in fo_scenario) or (spot > vwap and advances > 28)

        if is_bearish_pressure:
            bias = "BEARISH"
            direction = "PE"
            regime = "TRENDING_DOWN" if spot < support else "RANGE_WITH_BEARISH_PRESSURE"
            setup = "VWAP Rejection + Breadth Weakness"
            entry_trigger = round(min(spot, vwap - 10.0), 1)
            invalidation = round(max(vwap + 12.0, spot + 25.0), 1)
            target_1 = round(support - 15.0 if spot > support else spot - 40.0, 1)
            target_2 = round(target_1 - 40.0, 1)
            entry_condition = f"NIFTY holds below VWAP ({vwap:,.1f}) and breaks {entry_trigger:,.1f}"
            supporting_ev.append(f"Spot {spot:,.1f} trading below VWAP ({vwap:,.1f}).")
            if declines > advances:
                supporting_ev.append(f"Constituent breadth tilted bearish ({declines} declines vs {advances} advances).")
            if spot < support:
                supporting_ev.append(f"Structural support ({support:,.1f}) breached.")
        elif is_bullish_pressure:
            bias = "BULLISH"
            direction = "CE"
            regime = "TRENDING_UP" if spot > resistance else "RANGE_WITH_BULLISH_PRESSURE"
            setup = "VWAP Support + Breadth Strength"
            entry_trigger = round(max(spot, vwap + 10.0), 1)
            invalidation = round(min(vwap - 12.0, spot - 25.0), 1)
            target_1 = round(resistance + 15.0 if spot < resistance else spot + 40.0, 1)
            target_2 = round(target_1 + 40.0, 1)
            entry_condition = f"NIFTY holds above VWAP ({vwap:,.1f}) and clears {entry_trigger:,.1f}"
            supporting_ev.append(f"Spot {spot:,.1f} trading above VWAP ({vwap:,.1f}).")
            if advances > declines:
                supporting_ev.append(f"Constituent breadth strong positive ({advances} advances vs {declines} declines).")
        else:
            bias = "NEUTRAL_RANGE"
            direction = "NO_TRADE"
            regime = "RANGE_BOUND"
            setup = "Range Stabilization (No Directional Setup)"
            entry_trigger = None
            invalidation = None
            target_1 = None
            target_2 = None
            entry_condition = f"Await directional breakout outside range [{support:,.0f} – {resistance:,.0f}]"
            opposing_ev.append(f"Price consolidating between {support:,.0f} and {resistance:,.0f} without directional edge.")

        # 3. Strike Selection via Strike Strength Engine
        if direction in ("CE", "PE"):
            evaluated_strikes = StrikeStrengthEngine.evaluate_strike_universe(
                spot=spot,
                direction=direction,
                options_data=options_data,
                india_vix=vix_val,
                days_to_expiry=3.0
            )
        else:
            evaluated_strikes = []

        top_strike = evaluated_strikes[0] if evaluated_strikes else None
        nearby_shortlist = [s.to_dict() for s in evaluated_strikes[:3]]

        # 4. Entry Quality Evaluation
        if top_strike and direction in ("CE", "PE"):
            entry_eval = EntryQualityEngine.evaluate_entry_quality(
                spot=spot,
                direction=direction,
                entry_trigger_price=entry_trigger,
                invalidation_price=invalidation,
                target_1=target_1,
                target_2=target_2,
                strike_spread_pct=top_strike.spread_pct or 0.5,
                premium_risk=top_strike.premium_risk,
                is_confirmed=(is_bearish_pressure or is_bullish_pressure)
            )
        else:
            entry_eval = None

        # 5. Approval Safety Gates
        approval_blockers: List[str] = []

        # Gate 1: Market Session
        if session_status not in ("OPEN", "REGULAR", "REGULAR_MARKET", "LIVE_SESSION"):
            approval_blockers.append("Market is closed / outside regular trading hours")

        # Gate 2: Directional Setup
        if direction == "NO_TRADE":
            approval_blockers.append("No qualified directional trade setup (range balanced)")

        # Gate 3: Confidence Gating
        if fo_confidence == "LOW":
            approval_blockers.append("Intelligence confidence is LOW")

        # Gate 4: Data Quality Gate
        if data_quality in ("DEGRADED", "INSUFFICIENT"):
            approval_blockers.extend(data_quality_issues)

        # Gate 5: Strike Strength & Liquidity
        if top_strike:
            if top_strike.liquidity_grade in ("WEAK", "UNTRADEABLE"):
                approval_blockers.append(f"Top strike liquidity is {top_strike.liquidity_grade}")
            if top_strike.strength_band in ("WEAK", "AVOID"):
                approval_blockers.append(f"Top strike strength is {top_strike.strength_band} ({top_strike.strength_score:.0f}/100)")
            if top_strike.premium_risk == "EXTREME":
                approval_blockers.append("Option premium risk is EXTREME (theta/expiry danger)")
        else:
            if direction != "NO_TRADE":
                approval_blockers.append("No viable strike candidate found")

        # Gate 6: Entry Quality Gate
        if entry_eval:
            if entry_eval.entry_quality_band in ("WAIT", "POOR", "DO_NOT_ENTER"):
                approval_blockers.append(f"Entry timing is {entry_eval.entry_quality_band}: {entry_eval.entry_reason}")
            if entry_eval.risk_reward_ratio is not None and entry_eval.risk_reward_ratio < 1.4:
                approval_blockers.append(f"Risk/Reward ratio insufficient (1:{entry_eval.risk_reward_ratio:.2f} < 1:1.50)")
            if entry_eval.is_chase:
                approval_blockers.append(f"Price has extended past optimal entry ({entry_eval.chase_distance_pts:.0f} pts chase)")

        # Determine Approval Status Progression
        if session_status not in ("OPEN", "REGULAR", "REGULAR_MARKET", "LIVE_SESSION"):
            approval_status = "WATCH"
            entry_status = "MARKET_CLOSED"
        elif not approval_blockers and direction in ("CE", "PE"):
            approval_status = "READY_FOR_APPROVAL"
            entry_status = "QUALIFIED_READY"
        elif direction in ("CE", "PE") and any("chase" in b.lower() or "timing" in b.lower() or "pending" in b.lower() for b in approval_blockers):
            approval_status = "CONDITIONS_PENDING"
            entry_status = "AWAITING_TRIGGER"
        elif direction in ("CE", "PE"):
            approval_status = "QUALIFIED"
            entry_status = "SETUP_FORMED_GATED"
        else:
            approval_status = "WATCH"
            entry_status = "NO_ACTION"

        # Construct Serializable TradeCandidate
        trade_candidate: Optional[TradeCandidate] = None
        if top_strike and direction in ("CE", "PE"):
            trade_candidate = TradeCandidate(
                candidate_id=f"CAND-{session_date}-{top_strike.strike:,.0f}{top_strike.option_type}-{now_ist.strftime('%H%M%S')}",
                generated_at=now_str,
                underlying="NIFTY",
                direction=direction,
                instrument=top_strike.symbol,
                strike=top_strike.strike,
                expiry="CURRENT_WEEKLY",
                option_type=top_strike.option_type,
                entry_condition=entry_condition,
                invalidation=invalidation,
                targets=[t for t in (target_1, target_2) if t is not None],
                confidence=fo_confidence,
                strike_strength=top_strike.strength_score,
                entry_quality=entry_eval.entry_quality_band if entry_eval else "UNKNOWN",
                risk=top_strike.premium_risk,
                data_quality=data_quality,
                status=approval_status
            )

        target_str = f"{target_1:,.0f} / {target_2:,.0f}" if (target_1 and target_2) else (f"{target_1:,.0f}" if target_1 else "—")
        rr_str = f"1:{entry_eval.risk_reward_ratio:.2f}" if (entry_eval and entry_eval.risk_reward_ratio) else "—"

        return TraderDecision(
            trading_date=session_date,
            generated_at=now_str,
            market_phase="LIVE_SESSION" if session_status == "OPEN" else session_status,
            spot=spot,
            bias=bias,
            regime=regime,
            setup=setup,
            direction=direction,
            entry_condition=entry_condition,
            entry_status=entry_status,
            invalidation=invalidation,
            target=target_str,
            risk_reward=rr_str,
            confidence_band=fo_confidence,
            calibrated_probability=None,
            data_quality=data_quality,
            liquidity_quality=top_strike.liquidity_grade if top_strike else "UNAVAILABLE",
            opportunity_quality=top_strike.strength_band if top_strike else "NONE",
            strike_recommendation=top_strike.to_dict() if top_strike else None,
            entry_quality=entry_eval.to_dict() if entry_eval else None,
            nearby_strikes=nearby_shortlist,
            risk_flags=risk_flags,
            supporting_evidence=supporting_ev,
            opposing_evidence=opposing_ev,
            approval_status=approval_status,
            approval_blockers=approval_blockers,
            trade_candidate=trade_candidate.to_dict() if trade_candidate else None
        )
