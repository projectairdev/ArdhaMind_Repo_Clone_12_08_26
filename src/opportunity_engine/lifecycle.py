from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from src.opportunity_engine.models import (
    CanonicalOpportunity,
    DetectorResult,
    OpportunityStatus,
    LifecycleTransition,
)


def generate_dedup_key(setup_type: str, direction: str, underlying: str, strike: Optional[int]) -> str:
    strike_str = str(strike) if strike else "SPOT"
    return f"{underlying}_{setup_type}_{direction}_{strike_str}".replace(" ", "_").upper()


def build_canonical_opportunity(
    detector_result: DetectorResult,
    quality_score: int,
    confidence_score: int,
    priority_score: int,
    score_breakdown_dict: dict[str, float],
    status: OpportunityStatus,
    status_reason: str,
    blocking_reasons: list[str],
    context: dict[str, Any],
    runtime_id: str = "rt-prod-1",
    state_sequence: int = 1,
    existing: Optional[CanonicalOpportunity] = None,
) -> CanonicalOpportunity:
    now_iso = datetime.now(timezone.utc).isoformat()
    market = context.get("market", {})
    options = context.get("options", {})
    news = context.get("news", {})
    macro = context.get("macro", {})
    session = context.get("session", {})

    spot = float(market.get("current_spot", 0.0) or 0.0)
    levels = detector_result.suggested_levels

    entry_ref = float(levels.get("entry_reference", spot))
    entry_low = float(levels.get("entry_zone_low", entry_ref - 10.0))
    entry_high = float(levels.get("entry_zone_high", entry_ref + 10.0))
    sl = float(levels.get("invalidation_level", entry_ref - 30.0))
    t1 = float(levels.get("target_zone_1", entry_ref + 50.0))
    t2 = float(levels.get("target_zone_2", entry_ref + 80.0))

    risk = abs(entry_ref - sl)
    reward = abs(t1 - entry_ref)
    rr_ratio = round(reward / max(1.0, risk), 2)

    strike = detector_result.provisional_strike or int(round(spot / 50.0) * 50)
    opt_type = detector_result.option_type or ("CE" if detector_result.direction == "BULLISH" else "PE")
    inst_family = f"NIFTY 23 MAY {strike} {opt_type}"

    dedup_key = generate_dedup_key(detector_result.setup_type, detector_result.direction, "NIFTY 50", strike)

    if existing:
        opp_id = existing.opportunity_id
        created_at = existing.created_at
        first_detected_at = existing.first_detected_at
        history = list(existing.lifecycle_history)
        if existing.status != status.value:
            history.append(
                LifecycleTransition(
                    timestamp=now_iso,
                    previous_status=existing.status,
                    new_status=status.value,
                    reason=status_reason,
                    state_sequence=state_sequence,
                ).to_dict()
            )
    else:
        opp_id = f"OPP-{dedup_key}-{str(uuid.uuid4())[:8]}"
        created_at = now_iso
        first_detected_at = now_iso
        history = [
            LifecycleTransition(
                timestamp=now_iso,
                previous_status="NONE",
                new_status=status.value,
                reason=status_reason,
                state_sequence=state_sequence,
            ).to_dict()
        ]

    explanation_tokens = [
        f"Setup: {detector_result.setup_type}",
        f"Direction: {detector_result.direction}",
        f"Priority Score: {priority_score}/100",
        f"R:R: 1:{rr_ratio}",
    ] + detector_result.evidence[:2]

    opp = CanonicalOpportunity(
        opportunity_id=opp_id,
        runtime_id=runtime_id,
        state_sequence=state_sequence,
        created_at=created_at,
        updated_at=now_iso,
        first_detected_at=first_detected_at,
        last_detected_at=now_iso,
        setup_type=detector_result.setup_type,
        direction=detector_result.direction,
        underlying="NIFTY 50",
        instrument_family=inst_family,
        market_session=str(session.get("session_type", "LIVE")).upper(),
        market_state="OPEN" if not session.get("is_closed") else "CLOSED",
        freshness_state=str(market.get("freshness_status", "FRESH")).upper(),
        status=status.value,
        status_reason=status_reason,
        entry_reference=entry_ref,
        entry_zone_low=entry_low,
        entry_zone_high=entry_high,
        invalidation_level=sl,
        target_reference=t1,
        target_zone_1=t1,
        target_zone_2=t2,
        estimated_reward=round(reward, 1),
        estimated_risk=round(risk, 1),
        reward_risk_ratio=rr_ratio,
        confidence_score=confidence_score,
        quality_score=quality_score,
        priority_score=priority_score,
        detector_scores={
            "raw_detector_score": detector_result.raw_score,
            "breakdown": score_breakdown_dict,
        },
        confirmation_signals=detector_result.evidence,
        conflicting_signals=detector_result.conflicts,
        market_context_snapshot={
            "spot": spot,
            "vwap": market.get("vwap"),
            "vix": market.get("india_vix"),
            "trend": market.get("trend_direction"),
            "atr": market.get("atr"),
        },
        options_context_snapshot={
            "pcr": options.get("pcr"),
            "max_pain": options.get("max_pain"),
            "atm_iv": options.get("atm_iv"),
        },
        news_context_snapshot={
            "high_impact_count": len(news.get("high_impact", [])) if isinstance(news, dict) else 0,
        },
        macro_context_snapshot={
            "gift_nifty": macro.get("quotes", {}).get("GIFT_NIFTY", {}).get("price") if isinstance(macro, dict) else None,
        },
        expiry_at="",
        invalidated_at=now_iso if status == OpportunityStatus.INVALIDATED else None,
        source_detector=detector_result.detector_id,
        detector_version=detector_result.detector_version,
        explanation_tokens=explanation_tokens,
        explanation_fields={
            "why_detected": detector_result.evidence,
            "conflicts": detector_result.conflicts,
        },
        data_quality={
            "status": market.get("freshness_status", "FRESH"),
            "coverage": "FULL",
        },
        blocking_reasons=blocking_reasons,
        lifecycle_history=history,
    )

    return opp
