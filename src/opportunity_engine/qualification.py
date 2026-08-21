from __future__ import annotations

from typing import Any, Dict, List, Tuple
from src.opportunity_engine.domain import DetectorResult, OpportunityStatus
from src.opportunity_engine.config import DEFAULT_OPPORTUNITY_CONFIG, OpportunityConfig


class QualificationEngine:
    """
    Evaluates raw detections against market session, data freshness, coverage,
    structural validity, configurable risk-reward thresholds, and signal conflicts.
    Strictly distinguishes QUALIFIED (valid structure) vs TRADE_READY (actionable now).
    Assigns BLOCKED for temporary data/provider/session degradation instead of REJECTED.
    """

    qualification_version = "1.0.0"

    @classmethod
    def qualify_opportunity(
        cls,
        detector_result: DetectorResult,
        scores: Dict[str, Any],
        context: Dict[str, Any],
        config: OpportunityConfig = DEFAULT_OPPORTUNITY_CONFIG,
    ) -> Tuple[OpportunityStatus, str, List[str]]:
        market = context.get("market_context") or {}
        freshness = str(context.get("freshness_state") or "FRESH").upper()
        market_state = str(context.get("market_state") or "LIVE").upper()
        is_closed = context.get("market_closed") is True or market_state in (
            "CLOSED",
            "MARKET_CLOSED",
            "HOLIDAY",
            "WEEKEND",
        )

        blocking_reasons = []

        # 1. Temporary Detector Blocked / Data Stale -> BLOCKED (not REJECTED)
        if detector_result.blocked:
            reason = detector_result.blocking_reason or "Detector input requirements not satisfied"
            return (
                OpportunityStatus.BLOCKED,
                f"DETECTOR_BLOCKED: {reason}",
                [reason],
            )

        if freshness == "STALE":
            return (
                OpportunityStatus.BLOCKED,
                "MARKET_DATA_STALE: Price or option feeds are stale or disconnected.",
                ["Market data feeds are stale"],
            )

        if is_closed:
            return (
                OpportunityStatus.BLOCKED,
                "MARKET_CLOSED: Live opportunity scanning is paused.",
                ["Market session is closed"],
            )

        # 2. Minimum Data Coverage
        spot = float(market.get("current_spot") or 0.0)
        if spot <= 0:
            return (
                OpportunityStatus.BLOCKED,
                "INSUFFICIENT_DATA: Missing NIFTY spot price.",
                ["Missing valid NIFTY spot price"],
            )

        # 3. Detector Detection Check
        if not detector_result.detected:
            reason = detector_result.blocking_reason or "Detector threshold conditions not met"
            return (
                OpportunityStatus.REJECTED,
                f"DETECTOR_REJECTED: {reason}",
                [reason],
            )

        # 4. Configurable Per-Setup Risk / Reward Threshold Check
        setup_type = detector_result.detector_id.upper()
        min_rr = config.get_min_rr(setup_type)
        rr_ratio = float(scores.get("reward_risk_ratio") or 0.0)

        if rr_ratio < min_rr:
            blocking_reasons.append(
                f"Reward/Risk ratio ({rr_ratio:.2f}) below required minimum {min_rr:.2f} for {setup_type}"
            )

        # 5. Quality & Confidence Score Thresholds
        quality = float(scores.get("quality_score") or 0.0)
        confidence = float(scores.get("confidence_score") or 0.0)

        if quality < config.watching_min_quality:
            return (
                OpportunityStatus.REJECTED,
                f"REJECTED: Quality score ({quality:.1f}) below minimum watching threshold ({config.watching_min_quality:.0f})",
                [f"Quality score below {config.watching_min_quality:.0f}"],
            )

        # 6. Contradictory Signals / Heavy Conflicts
        conflicts = detector_result.conflicts
        if len(conflicts) >= 3:
            blocking_reasons.append(f"Excessive contradictory signals ({len(conflicts)} items)")

        # ── STATUS CLASSIFICATION ──
        # TRADE_READY = Structurally valid AND actionable now (no blockers, high quality & confidence)
        if (
            not blocking_reasons
            and quality >= config.trade_ready_min_quality
            and confidence >= config.trade_ready_min_confidence
            and rr_ratio >= min_rr
        ):
            return (
                OpportunityStatus.TRADE_READY,
                "TRADE_READY: Structurally valid and actionable now.",
                [],
            )

        # QUALIFIED = Structurally valid setup, but may have minor blockers or slightly lower conviction
        elif (
            not blocking_reasons
            and quality >= config.qualified_min_quality
            and confidence >= config.qualified_min_confidence
        ):
            return (
                OpportunityStatus.QUALIFIED,
                "QUALIFIED: Structurally valid setup meeting baseline evidence rules.",
                [],
            )

        # WATCHING = Promising setup under observation with soft blockers
        elif quality >= config.watching_min_quality:
            return (
                OpportunityStatus.WATCHING,
                f"WATCHING: Candidate under observation ({'; '.join(blocking_reasons)})",
                blocking_reasons,
            )

        else:
            return (
                OpportunityStatus.REJECTED,
                f"REJECTED: {'; '.join(blocking_reasons or ['Low conviction'])}",
                blocking_reasons or ["Low conviction score"],
            )


qualify_opportunity = QualificationEngine.qualify_opportunity
