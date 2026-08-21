from __future__ import annotations

from typing import Any, Dict
from src.opportunity_engine.domain import DetectorInputRequirements, DetectorResult, Direction
from src.opportunity_engine.detectors.base import OpportunityDetector


class ReversalDetector(OpportunityDetector):
    detector_id = "reversal"
    detector_version = "1.0.0"
    input_requirements = DetectorInputRequirements(
        required_inputs=["current_spot"],
        optional_inputs=["vwap", "atr", "india_vix", "pcr", "advances", "declines"],
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
        vix = float(market.get("india_vix") or 15.0)
        trend_direction = str(market.get("trend_direction") or "NEUTRAL").upper()
        supports = market.get("support_levels") or []
        resistances = market.get("resistance_levels") or []

        evidence_bullish = []
        evidence_bearish = []
        conflicts_bullish = []
        conflicts_bearish = []
        score_bullish = []
        score_bearish = []

        if supports:
            nearest_sup = max(supports)
            if abs(spot - nearest_sup) <= (atr * 0.25):
                score_bullish.append(30.0)
                evidence_bullish.append(f"Sharp rejection & support defense at {nearest_sup:.1f}")

        if resistances:
            nearest_res = min(resistances)
            if abs(spot - nearest_res) <= (atr * 0.25):
                score_bearish.append(30.0)
                evidence_bearish.append(f"Exhaustion & resistance rejection at {nearest_res:.1f}")

        if trend_direction == "BEARISH" and vwap > 0 and spot > vwap:
            score_bullish.append(25.0)
            evidence_bullish.append(f"Reclaimed VWAP ({vwap:.1f}) after bearish move (failed breakdown)")
        elif trend_direction == "BULLISH" and vwap > 0 and spot < vwap:
            score_bearish.append(25.0)
            evidence_bearish.append(f"Lost VWAP ({vwap:.1f}) after bullish move (failed breakout)")

        adv = float(breadth.get("advances") or 0)
        dec = float(breadth.get("declines") or 0)
        if trend_direction == "BEARISH" and adv > dec:
            score_bullish.append(20.0)
            evidence_bullish.append(f"Bullish breadth divergence ({int(adv)} advances despite bearish trend)")
        elif trend_direction == "BULLISH" and dec > adv:
            score_bearish.append(20.0)
            evidence_bearish.append(f"Bearish breadth divergence ({int(dec)} declines despite bullish trend)")

        pcr = float(options.get("pcr") or 0.0)
        call_oi_change = float(options.get("highest_call_oi_change") or 0.0)
        put_oi_change = float(options.get("highest_put_oi_change") or 0.0)
        if pcr > 1.2 and put_oi_change > call_oi_change:
            score_bullish.append(25.0)
            evidence_bullish.append(f"Heavy put writing ({pcr:.2f} PCR) signalling bottoming reversal")
        elif 0 < pcr < 0.75 and call_oi_change > put_oi_change:
            score_bearish.append(25.0)
            evidence_bearish.append(f"Heavy call writing ({pcr:.2f} PCR) signalling topping reversal")

        if vix > 20.0:
            evidence_bullish.append("Elevated VIX indicates capitulation risk/reversal opportunity")
            evidence_bearish.append("Elevated VIX indicates high volatility reversal risk")

        total_bullish = min(100.0, sum(score_bullish))
        total_bearish = min(100.0, sum(score_bearish))

        is_bullish_reversal = total_bullish >= 65.0 and len(evidence_bullish) >= 3
        is_bearish_reversal = total_bearish >= 65.0 and len(evidence_bearish) >= 3

        if is_bullish_reversal and total_bullish >= total_bearish:
            entry_ref = spot
            sl = spot - (atr * 0.4)
            t1 = spot + (atr * 1.0)
            t2 = spot + (atr * 1.8)
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=True,
                direction=Direction.BULLISH,
                raw_score=round(total_bullish, 1),
                evidence=evidence_bullish,
                conflicts=conflicts_bullish,
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
        elif is_bearish_reversal:
            entry_ref = spot
            sl = spot + (atr * 0.4)
            t1 = spot - (atr * 1.0)
            t2 = spot - (atr * 1.8)
            return DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detected=True,
                direction=Direction.BEARISH,
                raw_score=round(total_bearish, 1),
                evidence=evidence_bearish,
                conflicts=conflicts_bearish,
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

        return DetectorResult(
            detector_id=self.detector_id,
            detector_version=self.detector_version,
            detected=False,
            direction=Direction.BULLISH,
            raw_score=max(round(total_bullish, 1), round(total_bearish, 1)),
            blocking_reason="Strict multi-factor agreement (score >= 65, evidence >= 3) not met for reversal",
        )
