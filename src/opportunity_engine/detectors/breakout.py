from __future__ import annotations

from typing import Any, Dict
from src.opportunity_engine.domain import DetectorInputRequirements, DetectorResult, Direction
from src.opportunity_engine.detectors.base import OpportunityDetector


class BreakoutDetector(OpportunityDetector):
    detector_id = "breakout"
    detector_version = "1.0.0"
    input_requirements = DetectorInputRequirements(
        required_inputs=["current_spot", "resistance_levels"],
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
        trend_strength = float(market.get("trend_strength") or 50.0)
        resistances = market.get("resistance_levels") or []

        key_resistance = min(resistances) if resistances else spot + 100.0
        buffer_pts = max(5.0, atr * 0.05)

        evidence = []
        conflicts = []
        score_components = []

        if spot >= (key_resistance + buffer_pts):
            score_components.append(30.0)
            evidence.append(f"Price ({spot:.1f}) broke key resistance ({key_resistance:.1f}) with valid buffer (+{buffer_pts:.1f} pts)")
        elif spot >= key_resistance:
            conflicts.append(f"Price ({spot:.1f}) touching resistance ({key_resistance:.1f}) without buffer confirmation")

        if not score_components:
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=False,
                direction=Direction.BULLISH,
                raw_score=0.0,
                blocking_reason=f"Price ({spot:.1f}) has not cleared key resistance ({key_resistance:.1f})",
            )

        if vwap > 0 and spot > vwap:
            score_components.append(15.0)
            evidence.append(f"Holding above VWAP ({vwap:.1f})")
        elif vwap > 0 and spot <= vwap:
            conflicts.append(f"Price below VWAP ({vwap:.1f}) during breakout attempt")

        if trend_direction == "BULLISH":
            score_components.append(20.0)
            evidence.append(f"Strong bullish trend alignment ({trend_strength:.0f}%)")
        elif trend_direction == "BEARISH":
            conflicts.append("Counter-trend breakout attempt against bearish trend")

        pcr = float(options.get("pcr") or 0.0)
        call_oi_change = float(options.get("highest_call_oi_change") or 0.0)
        put_oi_change = float(options.get("highest_put_oi_change") or 0.0)
        if pcr > 0.95:
            score_components.append(15.0)
            evidence.append(f"Bullish options PCR positioning ({pcr:.2f})")
        if put_oi_change > call_oi_change:
            score_components.append(10.0)
            evidence.append("Put writing exceeding call writing (OI support build-up)")

        adv = float(breadth.get("advances") or 0)
        dec = float(breadth.get("declines") or 0)
        if adv > dec and dec >= 0:
            score_components.append(10.0)
            evidence.append(f"Positive market breadth ({int(adv)} advances vs {int(dec)} declines)")
        elif dec > adv:
            conflicts.append("Divergent market breadth (declines leading)")

        total_score = min(100.0, sum(score_components))
        is_detected = total_score >= 50.0 and len(conflicts) <= 2

        entry_ref = spot
        entry_zone_low = spot - (atr * 0.1)
        entry_zone_high = spot + (atr * 0.1)
        sl = key_resistance - (atr * 0.3)
        t1 = spot + (atr * 0.8)
        t2 = spot + (atr * 1.5)

        return DetectorResult(
            detector_id=self.detector_id,
            detector_version=self.detector_version,
            detected=is_detected,
            direction=Direction.BULLISH,
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
                "key_resistance": round(key_resistance, 2),
            },
            validity_window_seconds=900,
        )
