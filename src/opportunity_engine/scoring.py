from __future__ import annotations

from typing import Any, Dict
from src.opportunity_engine.domain import DetectorResult


class OpportunityScorer:
    """
    Deterministic scoring system for NIFTY trading opportunities.
    Computes inspectable sub-scores and master scores (quality_score, confidence_score, priority_score).
    """

    scoring_version = "1.0.0"

    @classmethod
    def calculate_scores(
        cls,
        detector_result: DetectorResult,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        market = context.get("market_context") or {}
        options = context.get("option_context") or {}
        breadth = context.get("breadth") or {}
        news = context.get("news") or {}

        spot = float(market.get("current_spot") or 0.0)
        vwap = float(market.get("vwap") or 0.0)
        atr = float(market.get("atr") or 100.0)
        vix = float(market.get("india_vix") or 15.0)
        trend_strength = float(market.get("trend_strength") or 50.0)

        levels = detector_result.suggested_levels
        entry = float(levels.get("entry_reference") or spot)
        sl = float(levels.get("invalidation_level") or 0.0)
        t1 = float(levels.get("target_zone_1") or 0.0)

        risk = abs(entry - sl) if sl > 0 else (atr * 0.4)
        reward = abs(t1 - entry) if t1 > 0 else (atr * 0.8)
        rr_ratio = round(reward / risk, 2) if risk > 0 else 1.0

        setup_quality = round(float(detector_result.raw_score), 1)
        trend_alignment = min(100.0, round(trend_strength, 1))

        momentum_strength = min(
            100.0,
            round(
                (trend_strength * 0.6) + (20.0 if abs(spot - vwap) > 10 else 10.0),
                1,
            ),
        )

        structure_quality = (
            85.0
            if (
                market.get("support_levels") or market.get("resistance_levels")
            )
            else 60.0
        )

        pcr = float(options.get("pcr") or 1.0)
        if detector_result.direction == "BULLISH":
            options_confirmation = (
                90.0 if pcr >= 1.0 else (70.0 if pcr >= 0.85 else 40.0)
            )
        else:
            options_confirmation = (
                90.0 if pcr <= 0.85 else (70.0 if pcr <= 1.0 else 40.0)
            )

        adv = float(breadth.get("advances") or breadth.get("advance_count") or 0)
        dec = float(breadth.get("declines") or breadth.get("decline_count") or 0)
        if adv + dec > 0:
            raw_adv_pct = (adv / (adv + dec)) * 100.0
            if detector_result.direction == "BULLISH":
                breadth_confirmation = round(raw_adv_pct, 1)
            else:
                breadth_confirmation = round(100.0 - raw_adv_pct, 1)
        else:
            breadth_confirmation = 50.0

        if 12.0 <= vix <= 22.0:
            volatility_suitability = 90.0
        elif vix < 12.0:
            volatility_suitability = 70.0
        else:
            volatility_suitability = 50.0

        news_risk = (
            25.0
            if (
                news.get("high_impact_news")
                or news.get("market_moving_event")
            )
            else 0.0
        )
        macro_risk = 0.0

        data_quality = 95.0 if (spot > 0 and vwap > 0 and pcr > 0) else 65.0

        if rr_ratio >= 2.0:
            reward_risk_quality = 95.0
        elif rr_ratio >= 1.5:
            reward_risk_quality = 80.0
        elif rr_ratio >= 1.0:
            reward_risk_quality = 50.0
        else:
            reward_risk_quality = 20.0

        dist_vwap_atr = (abs(spot - vwap) / atr) if (vwap > 0 and atr > 0) else 0.0
        extension_penalty = round(min(40.0, max(0.0, (dist_vwap_atr - 1.0) * 40.0)), 1)
        conflict_penalty = min(50.0, float(len(detector_result.conflicts) * 15.0))

        raw_quality = (
            (setup_quality * 0.25)
            + (structure_quality * 0.20)
            + (trend_alignment * 0.15)
            + (options_confirmation * 0.15)
            + (breadth_confirmation * 0.15)
            + (reward_risk_quality * 0.10)
            - extension_penalty
            - conflict_penalty
        )
        quality_score = round(max(0.0, min(100.0, raw_quality)), 1)

        raw_confidence = (
            (setup_quality * 0.35)
            + (data_quality * 0.25)
            + (options_confirmation * 0.20)
            + (volatility_suitability * 0.20)
            - (news_risk * 0.5)
            - conflict_penalty
        )
        confidence_score = round(max(0.0, min(100.0, raw_confidence)), 1)

        raw_priority = (
            (quality_score * 0.45)
            + (confidence_score * 0.35)
            + (reward_risk_quality * 0.20)
        )
        priority_score = round(max(0.0, min(100.0, raw_priority)), 1)

        return {
            "quality_score": quality_score,
            "confidence_score": confidence_score,
            "priority_score": priority_score,
            "estimated_risk": round(risk, 2),
            "estimated_reward": round(reward, 2),
            "reward_risk_ratio": rr_ratio,
            "scoring_version": cls.scoring_version,
            "sub_scores": {
                "setup_quality": setup_quality,
                "trend_alignment": trend_alignment,
                "momentum_strength": momentum_strength,
                "structure_quality": structure_quality,
                "options_confirmation": options_confirmation,
                "breadth_confirmation": breadth_confirmation,
                "volatility_suitability": volatility_suitability,
                "news_risk": news_risk,
                "macro_risk": macro_risk,
                "data_quality": data_quality,
                "reward_risk_quality": reward_risk_quality,
                "extension_penalty": extension_penalty,
                "conflict_penalty": conflict_penalty,
            },
        }


calculate_opportunity_scores = OpportunityScorer.calculate_scores
