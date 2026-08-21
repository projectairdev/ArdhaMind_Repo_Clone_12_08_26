from __future__ import annotations

from typing import Any, Dict
from src.opportunity_engine.domain import DetectorInputRequirements, DetectorResult, Direction
from src.opportunity_engine.detectors.base import OpportunityDetector


class PullbackDetector(OpportunityDetector):
    detector_id = "pullback"
    detector_version = "1.0.0"
    input_requirements = DetectorInputRequirements(
        required_inputs=["current_spot"],
        optional_inputs=["vwap", "atr", "pcr", "support_levels", "resistance_levels"],
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

        spot = float(market.get("current_spot") or 0.0)
        vwap = float(market.get("vwap") or 0.0)
        atr = float(market.get("atr") or 100.0)
        trend_direction = str(market.get("trend_direction") or "NEUTRAL").upper()
        trend_strength = float(market.get("trend_strength") or 0.0)
        supports = market.get("support_levels") or []
        resistances = market.get("resistance_levels") or []

        if trend_direction == "NEUTRAL" or trend_strength < 40.0:
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=False,
                direction=Direction.BULLISH if trend_direction == "BULLISH" else Direction.BEARISH,
                raw_score=0.0,
                blocking_reason="Requires established trend (strength >= 40%) for pullback evaluation",
            )

        evidence = []
        conflicts = []
        score_components = []

        is_bullish = trend_direction == "BULLISH"
        direction = Direction.BULLISH if is_bullish else Direction.BEARISH

        if is_bullish:
            key_sup = max([s for s in supports if s < spot], default=vwap or spot - 80.0)
            dist_vwap = abs(spot - vwap) if vwap > 0 else 0.0

            if 0 < dist_vwap <= (atr * 0.5):
                score_components.append(35.0)
                evidence.append(f"Controlled pullback near VWAP ({vwap:.1f}) within {dist_vwap:.1f} pts")
            elif dist_vwap > (atr * 1.2):
                conflicts.append("Price overextended or deep pullback warning (trend deterioration risk)")

            if spot >= key_sup:
                score_components.append(25.0)
                evidence.append(f"Holding above validated support level ({key_sup:.1f})")
            else:
                conflicts.append(f"Price violated key support ({key_sup:.1f}) — potential reversal")

            score_components.append(min(20.0, trend_strength * 0.25))
            evidence.append(f"Established bullish primary trend ({trend_strength:.0f}%)")

            pcr = float(options.get("pcr") or 0.0)
            if pcr >= 0.90:
                score_components.append(20.0)
                evidence.append(f"Options PCR ({pcr:.2f}) supports pullback continuation")

            entry_ref = spot
            entry_zone_low = spot - (atr * 0.1)
            entry_zone_high = spot + (atr * 0.1)
            sl = key_sup - (atr * 0.25)
            t1 = spot + (atr * 0.7)
            t2 = spot + (atr * 1.2)

        else:
            key_res = min([r for r in resistances if r > spot], default=vwap or spot + 80.0)
            dist_vwap = abs(spot - vwap) if vwap > 0 else 0.0

            if 0 < dist_vwap <= (atr * 0.5):
                score_components.append(35.0)
                evidence.append(f"Controlled bounce into VWAP resistance ({vwap:.1f}) within {dist_vwap:.1f} pts")
            elif dist_vwap > (atr * 1.2):
                conflicts.append("Deep bounce warning — trend deterioration risk")

            if spot <= key_res:
                score_components.append(25.0)
                evidence.append(f"Rejection below resistance level ({key_res:.1f})")
            else:
                conflicts.append(f"Price violated resistance ({key_res:.1f}) — potential bullish reversal")

            score_components.append(min(20.0, trend_strength * 0.25))
            evidence.append(f"Established bearish primary trend ({trend_strength:.0f}%)")

            pcr = float(options.get("pcr") or 0.0)
            if 0 < pcr <= 0.85:
                score_components.append(20.0)
                evidence.append(f"Options PCR ({pcr:.2f}) supports bearish bounce short")

            entry_ref = spot
            entry_zone_low = spot - (atr * 0.1)
            entry_zone_high = spot + (atr * 0.1)
            sl = key_res + (atr * 0.25)
            t1 = spot - (atr * 0.7)
            t2 = spot - (atr * 1.2)

        total_score = min(100.0, sum(score_components))
        is_detected = total_score >= 55.0 and len(conflicts) == 0

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
                "entry_zone_low": round(entry_zone_low, 2),
                "entry_zone_high": round(entry_zone_high, 2),
                "invalidation_level": round(sl, 2),
                "target_reference": round(t1, 2),
                "target_zone_1": round(t1, 2),
                "target_zone_2": round(t2, 2),
            },
            validity_window_seconds=900,
        )
