from __future__ import annotations

from typing import Any, Dict
from src.opportunity_engine.domain import DetectorInputRequirements, DetectorResult, Direction
from src.opportunity_engine.detectors.base import OpportunityDetector


class MomentumContinuationDetector(OpportunityDetector):
    detector_id = "momentum_continuation"
    detector_version = "1.0.0"
    input_requirements = DetectorInputRequirements(
        required_inputs=["current_spot"],
        optional_inputs=["vwap", "atr", "pcr", "advances", "declines"],
        max_freshness_seconds=30.0,
    )

    def evaluate(self, context: Dict[str, Any]) -> DetectorResult:
        satisfied, block_reason = self.check_input_requirements(context)
        if not satisfied:
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=False,
                direction=Direction.BULLISH,
                raw_score=0.0,
                blocked=True,
                blocking_reason=block_reason,
            )

        market = context.get("market_context") or {}
        options = context.get("option_context") or {}
        breadth = context.get("breadth") or {}

        spot = float(market.get("current_spot") or 0.0)
        vwap = float(market.get("vwap") or 0.0)
        atr = float(market.get("atr") or 100.0)
        trend_direction = str(market.get("trend_direction") or "NEUTRAL").upper()
        trend_strength = float(market.get("trend_strength") or 0.0)

        if trend_direction == "NEUTRAL":
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=False,
                direction=Direction.BULLISH,
                raw_score=0.0,
                blocking_reason="Requires directional trend for momentum continuation detection",
            )

        is_bullish = trend_direction == "BULLISH"
        direction = Direction.BULLISH if is_bullish else Direction.BEARISH
        dist_vwap = (spot - vwap) if vwap > 0 else 0.0

        if abs(dist_vwap) > (1.5 * atr):
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=False,
                direction=direction,
                raw_score=0.0,
                blocked=True,
                blocking_reason=f"Price ({spot:.1f}) is overextended from VWAP ({vwap:.1f}) by {abs(dist_vwap):.1f} pts (> 1.5x ATR). Chasing blocked.",
            )

        evidence = []
        conflicts = []
        score_components = []

        if trend_strength >= 60.0:
            score_components.append(30.0)
            evidence.append(f"Strong directional momentum strength ({trend_strength:.0f}%)")
        elif trend_strength >= 40.0:
            score_components.append(15.0)
            evidence.append(f"Moderate momentum strength ({trend_strength:.0f}%)")

        if is_bullish and dist_vwap > 0:
            score_components.append(25.0)
            evidence.append(f"Holding above VWAP (+{dist_vwap:.1f} pts) with room to expand")
        elif not is_bullish and dist_vwap < 0:
            score_components.append(25.0)
            evidence.append(f"Holding below VWAP ({dist_vwap:.1f} pts) with downside room")
        else:
            conflicts.append("Price on opposite side of VWAP relative to momentum direction")

        pcr = float(options.get("pcr") or 0.0)
        if is_bullish and pcr > 1.0:
            score_components.append(20.0)
            evidence.append(f"Strong call-side momentum backed by put writing (PCR {pcr:.2f})")
        elif not is_bullish and 0 < pcr < 0.8:
            score_components.append(20.0)
            evidence.append(f"Strong put-side momentum backed by call writing (PCR {pcr:.2f})")

        adv = float(breadth.get("advances") or 0)
        dec = float(breadth.get("declines") or 0)
        if is_bullish and adv >= dec * 1.5:
            score_components.append(25.0)
            evidence.append(f"Strong market breadth expansion ({int(adv)} advances vs {int(dec)} declines)")
        elif not is_bullish and dec >= adv * 1.5:
            score_components.append(25.0)
            evidence.append(f"Broad market selling pressure ({int(dec)} declines vs {int(adv)} advances)")

        total_score = min(100.0, sum(score_components))
        is_detected = total_score >= 60.0 and len(conflicts) == 0

        if is_bullish:
            entry_ref = spot
            sl = spot - (atr * 0.35)
            t1 = spot + (atr * 0.9)
            t2 = spot + (atr * 1.6)
        else:
            entry_ref = spot
            sl = spot + (atr * 0.35)
            t1 = spot - (atr * 0.9)
            t2 = spot - (atr * 1.6)

        return DetectorResult(
            detector_id=self.detector_id,
            detector_version=self.detector_version,
            detected=is_detected,
            direction=direction,
            raw_score=round(total_score, 1),
            evidence=evidence,
            conflicts=conflicts,
            suggested_levels={
                "entry_reference": round(entry_ref, 2),
                "entry_zone_low": round(spot - (atr * 0.1), 2),
                "entry_zone_high": round(spot + (atr * 0.1), 2),
                "invalidation_level": round(sl, 2),
                "target_reference": round(t1, 2),
                "target_zone_1": round(t1, 2),
                "target_zone_2": round(t2, 2),
            },
            validity_window_seconds=600,
        )
