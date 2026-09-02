# src/intelligence_engine/entry_quality_engine.py
"""
EntryQualityEngine — Evaluates Entry Timing, Risk/Reward Geometry, and Chase Distance for AIR ArdhaMind.

Core Invariant:
  A strong option strike (high delta/liquidity) can still be a dangerous or untimely entry if price has
  extended too far from structural invalidation or confirmation conditions are pending.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EntryQualityEvaluation:
    entry_quality_score: float  # 0 to 100
    entry_quality_band: str  # EXCELLENT | GOOD | WAIT | POOR | DO_NOT_ENTER
    entry_reason: str
    
    # Geometry
    entry_reference_price: float
    invalidation_price: Optional[float]
    target_1: Optional[float]
    target_2: Optional[float]
    risk_points: Optional[float]
    reward_points: Optional[float]
    risk_reward_ratio: Optional[float]
    chase_distance_pts: float
    
    # Flags & Quality components
    component_scores: Dict[str, float]
    entry_blockers: List[str]
    is_chase: bool
    is_favorable_rr: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EntryQualityEngine:
    """
    Deterministic Entry Quality and Trade Geometry Evaluator.
    """

    @classmethod
    def evaluate_entry_quality(
        cls,
        spot: float,
        direction: str,  # CE | PE | BULLISH | BEARISH
        entry_trigger_price: Optional[float] = None,
        invalidation_price: Optional[float] = None,
        target_1: Optional[float] = None,
        target_2: Optional[float] = None,
        strike_spread_pct: float = 0.5,
        premium_risk: str = "LOW",
        is_confirmed: bool = True,
    ) -> EntryQualityEvaluation:
        if spot <= 0:
            return EntryQualityEvaluation(
                entry_quality_score=0.0,
                entry_quality_band="DO_NOT_ENTER",
                entry_reason="Invalid or missing underlying spot price.",
                entry_reference_price=0.0,
                invalidation_price=None,
                target_1=None,
                target_2=None,
                risk_points=None,
                reward_points=None,
                risk_reward_ratio=None,
                chase_distance_pts=0.0,
                component_scores={},
                entry_blockers=["Missing spot price"],
                is_chase=False,
                is_favorable_rr=False
            )

        is_pe = str(direction).upper() in ("PE", "BEARISH", "PUT")
        entry_ref = entry_trigger_price or spot

        # 1. Chase Distance (how far spot has drifted past optimal entry trigger)
        if is_pe:
            # For PE, if spot is below entry_trigger, it is drifting away (chasing downwards)
            chase_dist = round(max(0.0, entry_ref - spot), 1) if entry_trigger_price else 0.0
        else:
            # For CE, if spot is above entry_trigger, it is drifting away (chasing upwards)
            chase_dist = round(max(0.0, spot - entry_ref), 1) if entry_trigger_price else 0.0

        is_chase = chase_dist >= 25.0

        # 2. Risk & Reward Geometry
        risk_pts: Optional[float] = None
        reward_pts: Optional[float] = None
        rr_ratio: Optional[float] = None

        if invalidation_price and invalidation_price > 0:
            if is_pe:
                # Stop is above spot for PE
                risk_pts = round(max(5.0, invalidation_price - spot), 1)
            else:
                # Stop is below spot for CE
                risk_pts = round(max(5.0, spot - invalidation_price), 1)

        t1 = target_1 or (spot - 60.0 if is_pe else spot + 60.0)
        if is_pe:
            reward_pts = round(max(10.0, spot - t1), 1)
        else:
            reward_pts = round(max(10.0, t1 - spot), 1)

        if risk_pts and risk_pts > 0 and reward_pts and reward_pts > 0:
            rr_ratio = round(reward_pts / risk_pts, 2)

        is_favorable_rr = (rr_ratio is not None and rr_ratio >= 1.5)

        # 3. Component Scoring (0–100)
        comp_scores: Dict[str, float] = {}
        blockers: List[str] = []

        # A. Risk/Reward Score (Max 35)
        if rr_ratio is not None:
            if rr_ratio >= 2.0:
                comp_scores["risk_reward"] = 35.0
            elif rr_ratio >= 1.5:
                comp_scores["risk_reward"] = 28.0
            elif rr_ratio >= 1.0:
                comp_scores["risk_reward"] = 18.0
            else:
                comp_scores["risk_reward"] = 8.0
                blockers.append(f"Unfavorable Risk/Reward ratio (1:{rr_ratio:.2f} < 1:1.50)")
        else:
            comp_scores["risk_reward"] = 15.0

        # B. Chase & Distance Penalty (Max 25)
        if chase_dist <= 8.0:
            comp_scores["entry_proximity"] = 25.0
        elif chase_dist <= 18.0:
            comp_scores["entry_proximity"] = 18.0
        elif chase_dist <= 30.0:
            comp_scores["entry_proximity"] = 10.0
            blockers.append(f"Chasing price ({chase_dist:.0f} pts from optimal trigger)")
        else:
            comp_scores["entry_proximity"] = 0.0
            blockers.append(f"Severe price chase ({chase_dist:.0f} pts from structural trigger)")

        # C. Invalidation Proximity / Stop Distance (Max 20)
        if risk_pts is not None:
            if risk_pts <= 25.0:
                comp_scores["stop_tightness"] = 20.0
            elif risk_pts <= 45.0:
                comp_scores["stop_tightness"] = 15.0
            elif risk_pts <= 70.0:
                comp_scores["stop_tightness"] = 8.0
            else:
                comp_scores["stop_tightness"] = 0.0
                blockers.append(f"Invalidation stop is very wide ({risk_pts:.0f} NIFTY pts)")
        else:
            comp_scores["stop_tightness"] = 10.0

        # D. Confirmation Status (Max 10)
        if is_confirmed:
            comp_scores["confirmation"] = 10.0
        else:
            comp_scores["confirmation"] = 2.0
            blockers.append("Setup confirmation conditions pending")

        # E. Spread & Premium Friction (Max 10)
        if strike_spread_pct <= 0.5 and premium_risk != "EXTREME":
            comp_scores["execution_friction"] = 10.0
        elif strike_spread_pct <= 1.2:
            comp_scores["execution_friction"] = 6.0
        else:
            comp_scores["execution_friction"] = 2.0
            if strike_spread_pct > 1.5:
                blockers.append(f"Spread friction high ({strike_spread_pct:.1f}%)")

        total_score = round(sum(comp_scores.values()), 1)

        # Classification Band
        if not is_confirmed or chase_dist >= 35.0:
            entry_band = "WAIT"
            entry_reason = f"Entry condition pending or price extended (+{chase_dist:.0f} pts chase)."
        elif total_score >= 80.0 and is_favorable_rr:
            entry_band = "EXCELLENT"
            entry_reason = f"High-quality entry geometry (R:R 1:{rr_ratio or 2.0:.1f}, tight {risk_pts or 20:.0f} pt invalidation)."
        elif total_score >= 65.0 and (rr_ratio is None or rr_ratio >= 1.2):
            entry_band = "GOOD"
            entry_reason = f"Qualified entry with acceptable risk/reward (R:R 1:{rr_ratio or 1.5:.1f})."
        elif total_score >= 45.0:
            entry_band = "WAIT"
            entry_reason = "Suboptimal timing or moderate risk/reward; await pullback to trigger."
        elif total_score >= 30.0:
            entry_band = "POOR"
            entry_reason = "Poor risk/reward or wide stop distance."
        else:
            entry_band = "DO_NOT_ENTER"
            entry_reason = "Severe chase, extreme premium risk, or invalidation too distant."

        return EntryQualityEvaluation(
            entry_quality_score=total_score,
            entry_quality_band=entry_band,
            entry_reason=entry_reason,
            entry_reference_price=entry_ref,
            invalidation_price=invalidation_price,
            target_1=t1,
            target_2=target_2,
            risk_points=risk_pts,
            reward_points=reward_pts,
            risk_reward_ratio=rr_ratio,
            chase_distance_pts=chase_dist,
            component_scores=comp_scores,
            entry_blockers=blockers,
            is_chase=is_chase,
            is_favorable_rr=is_favorable_rr
        )
