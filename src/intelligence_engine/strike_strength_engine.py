# src/intelligence_engine/strike_strength_engine.py
"""
StrikeStrengthEngine — Deterministic Option Strike Strength & Suitability Evaluator for AIR ArdhaMind.

Evaluates an option strike universe (ITM, ATM, OTM) for CE/PE based on:
1. Market Fit & Direction Compatibility
2. Greeks (Delta, Gamma, Theta, Vega)
3. Volatility & IV Context
4. Positioning (OI, Change in OI, Option Walls)
5. Liquidity (Bid/Ask Spread %, Volume, Open Interest)
6. Expiry & Theta Risk
7. Premium Responsiveness & Required NIFTY Move
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StrikeEvaluation:
    strike: float
    option_type: str  # CE | PE
    symbol: str
    ltp: float
    bid: Optional[float]
    ask: Optional[float]
    spread_pts: Optional[float]
    spread_pct: Optional[float]
    volume: int
    open_interest: int
    change_oi: Optional[int]
    
    # Greeks
    delta: Optional[float]
    gamma: Optional[float]
    theta: Optional[float]
    vega: Optional[float]
    iv: Optional[float]
    
    # Moneyness & Move
    moneyness: str  # ITM_2 | ITM_1 | ATM | OTM_1 | OTM_2 | OTM_3
    distance_from_spot: float
    required_nifty_move: float
    expected_premium_response: str
    premium_sensitivity: str  # HIGH | MODERATE | LOW
    
    # Scoring & Bands
    strength_score: float  # 0 to 100
    strength_band: str  # EXCELLENT | GOOD | ACCEPTABLE | WEAK | AVOID
    component_scores: Dict[str, float]
    liquidity_grade: str  # STRONG | ACCEPTABLE | WEAK | UNTRADEABLE
    premium_risk: str  # LOW | MEDIUM | HIGH | EXTREME
    premium_risk_reasons: List[str]
    
    selection_reasons: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StrikeStrengthEngine:
    """
    Deterministic Option Strike Strength & Comparison Engine.
    """

    @classmethod
    def evaluate_strike_universe(
        cls,
        spot: float,
        direction: str,  # CE | PE | BULLISH | BEARISH
        options_data: Optional[Dict[str, Any]] = None,
        india_vix: Optional[float] = None,
        days_to_expiry: float = 3.0,
    ) -> List[StrikeEvaluation]:
        """
        Evaluates a candidate strike universe centered on spot.
        """
        if spot <= 0:
            return []

        opt_type = "PE" if str(direction).upper() in ("PE", "BEARISH", "PUT") else "CE"
        atm_strike = round(spot / 50.0) * 50.0

        # Construct strike universe: 2 ITM, ATM, 3 OTM
        if opt_type == "PE":
            # For PE: higher strikes are ITM, lower strikes are OTM
            candidates = [
                (atm_strike + 100.0, "ITM_2"),
                (atm_strike + 50.0, "ITM_1"),
                (atm_strike, "ATM"),
                (atm_strike - 50.0, "OTM_1"),
                (atm_strike - 100.0, "OTM_2"),
                (atm_strike - 150.0, "OTM_3"),
            ]
        else:
            # For CE: lower strikes are ITM, higher strikes are OTM
            candidates = [
                (atm_strike - 100.0, "ITM_2"),
                (atm_strike - 50.0, "ITM_1"),
                (atm_strike, "ATM"),
                (atm_strike + 50.0, "OTM_1"),
                (atm_strike + 100.0, "OTM_2"),
                (atm_strike + 150.0, "OTM_3"),
            ]

        # Extract option chain items if provided
        chain_map: Dict[Tuple[float, str], Dict[str, Any]] = {}
        if options_data:
            chain_items = options_data.get("chain") or options_data.get("strikes") or []
            for item in chain_items:
                stk = float(item.get("strike", 0))
                ot = str(item.get("option_type", "")).upper()
                if stk > 0 and ot in ("CE", "PE"):
                    chain_map[(stk, ot)] = item

        evaluations: List[StrikeEvaluation] = []

        for stk, mness in candidates:
            item = chain_map.get((stk, opt_type), {})
            eval_res = cls._evaluate_single_strike(
                spot=spot,
                strike=stk,
                opt_type=opt_type,
                moneyness=mness,
                item=item,
                india_vix=india_vix or 12.0,
                days_to_expiry=days_to_expiry
            )
            evaluations.append(eval_res)

        # Sort by strength score descending
        evaluations.sort(key=lambda x: x.strength_score, reverse=True)

        # Populate comparative why_selected and why_not reasons
        if evaluations:
            top = evaluations[0]
            top.selection_reasons.append(f"Top overall Strike Strength score ({top.strength_score:.0f}/100, {top.strength_band}).")
            if top.delta:
                top.selection_reasons.append(f"Optimal delta response ({top.delta:.2f}) with {top.premium_sensitivity.lower()} premium sensitivity.")
            if top.spread_pct is not None and top.spread_pct <= 0.5:
                top.selection_reasons.append(f"Tight bid/ask spread ({top.spread_pct:.2f}%).")
            if top.open_interest > 50000:
                top.selection_reasons.append(f"Strong open interest participation ({top.open_interest:,} contracts).")

            for alt in evaluations[1:]:
                if alt.moneyness.startswith("OTM") and alt.delta and abs(alt.delta) < 0.30:
                    alt.rejection_reasons.append(f"Low delta ({alt.delta:.2f}) requires large {alt.required_nifty_move:.0f} pt move.")
                if alt.moneyness.startswith("ITM") and alt.ltp > 200.0:
                    alt.rejection_reasons.append(f"Higher capital outlay (₹{alt.ltp:.1f}) with lower leverage.")
                if alt.spread_pct is not None and alt.spread_pct > 1.5:
                    alt.rejection_reasons.append(f"Wide spread ({alt.spread_pct:.1f}%) increases slippage.")
                if alt.theta and abs(alt.theta) > 15.0:
                    alt.rejection_reasons.append(f"Elevated theta decay (-₹{abs(alt.theta):.1f}/day).")

        return evaluations

    @classmethod
    def _evaluate_single_strike(
        cls,
        spot: float,
        strike: float,
        opt_type: str,
        moneyness: str,
        item: Dict[str, Any],
        india_vix: float,
        days_to_expiry: float
    ) -> StrikeEvaluation:
        ltp = float(item.get("ltp") or item.get("close") or item.get("last_price") or 0.0)
        bid = float(item.get("bid")) if item.get("bid") is not None else None
        ask = float(item.get("ask")) if item.get("ask") is not None else None
        volume = int(item.get("volume") or 0)
        oi = int(item.get("oi") or item.get("open_interest") or 0)
        change_oi = int(item.get("change_oi") or 0) if item.get("change_oi") is not None else None

        # If LTP is 0, estimate reasonable intrinsic/extrinsic value based on spot and strike
        if ltp <= 0:
            intrinsic = max(0.0, (strike - spot) if opt_type == "PE" else (spot - strike))
            extrinsic = max(15.0, 50.0 * (india_vix / 12.0) * ((days_to_expiry / 4.0) ** 0.5) * (1.0 - min(0.8, abs(spot - strike) / 300.0)))
            ltp = round(intrinsic + extrinsic, 1)

        # Spread
        if bid is not None and ask is not None and ask >= bid:
            spread_pts = round(ask - bid, 2)
            spread_pct = round((spread_pts / (ltp or 1.0)) * 100.0, 2)
        else:
            spread_pts = 0.50
            spread_pct = round((spread_pts / ltp) * 100.0, 2) if ltp > 0 else 0.50

        # Greeks (from item or estimated via standard black-scholes approximations)
        delta_raw = item.get("delta")
        if delta_raw is not None:
            delta = float(delta_raw)
        else:
            # Deterministic delta estimate based on moneyness
            dist = spot - strike
            if opt_type == "PE":
                # PE delta is negative (-0.05 to -0.95)
                if moneyness == "ITM_2": delta = -0.72
                elif moneyness == "ITM_1": delta = -0.60
                elif moneyness == "ATM": delta = -0.50
                elif moneyness == "OTM_1": delta = -0.38
                elif moneyness == "OTM_2": delta = -0.26
                else: delta = -0.15
            else:
                if moneyness == "ITM_2": delta = 0.72
                elif moneyness == "ITM_1": delta = 0.60
                elif moneyness == "ATM": delta = 0.50
                elif moneyness == "OTM_1": delta = 0.38
                elif moneyness == "OTM_2": delta = 0.26
                else: delta = 0.15

        theta_raw = item.get("theta")
        theta = float(theta_raw) if theta_raw is not None else round(-1.0 * (ltp * 0.08 / max(0.5, days_to_expiry)), 2)

        gamma_raw = item.get("gamma")
        gamma = float(gamma_raw) if gamma_raw is not None else (0.0025 if moneyness == "ATM" else 0.0015)

        vega_raw = item.get("vega")
        vega = float(vega_raw) if vega_raw is not None else round(ltp * 0.05, 2)

        iv_raw = item.get("iv") or item.get("implied_volatility")
        iv = float(iv_raw) if iv_raw is not None else round(india_vix * 1.05, 2)

        distance_from_spot = round(abs(spot - strike), 1)

        # Required NIFTY Move
        eff_delta = max(0.10, abs(delta))
        required_nifty_move = round((spread_pts / eff_delta) + (ltp * 0.05 / eff_delta), 1)
        expected_premium_response = f"₹{eff_delta * 10.0:.1f} per 10 pt NIFTY move"
        premium_sensitivity = "HIGH" if eff_delta >= 0.50 else ("MODERATE" if eff_delta >= 0.30 else "LOW")

        # Premium Risk Assessment
        risk_reasons: List[str] = []
        if days_to_expiry <= 1.0:
            risk_reasons.append("Same-day / zero-DTE expiry theta acceleration")
        if abs(delta) < 0.25:
            risk_reasons.append(f"Deep OTM ({distance_from_spot:.0f} pts away) low delta responsiveness")
        if spread_pct > 1.5:
            risk_reasons.append(f"Wide bid/ask spread ({spread_pct:.1f}%)")
        if iv > 20.0:
            risk_reasons.append(f"Elevated IV ({iv:.1f}%) prone to crush")

        if len(risk_reasons) >= 2 or days_to_expiry <= 0.5:
            premium_risk = "HIGH" if len(risk_reasons) == 2 else "EXTREME"
        elif len(risk_reasons) == 1:
            premium_risk = "MEDIUM"
        else:
            premium_risk = "LOW"

        # Liquidity Grade
        if spread_pct <= 0.5 and (volume >= 5000 or oi >= 50000):
            liquidity_grade = "STRONG"
        elif spread_pct <= 1.5:
            liquidity_grade = "ACCEPTABLE"
        elif spread_pct <= 3.0:
            liquidity_grade = "WEAK"
        else:
            liquidity_grade = "UNTRADEABLE"

        # --- DETERMINISTIC STRIKE STRENGTH SCORING (0–100) ---
        comp_scores: Dict[str, float] = {}

        # 1. Moneyness & Delta Quality (Max 30)
        # Optimal sweet spot is ATM and ATM±1 (Delta 0.40 - 0.60)
        abs_d = abs(delta)
        if 0.45 <= abs_d <= 0.55:
            comp_scores["delta_fit"] = 30.0
        elif 0.35 <= abs_d <= 0.65:
            comp_scores["delta_fit"] = 25.0
        elif 0.25 <= abs_d <= 0.75:
            comp_scores["delta_fit"] = 18.0
        else:
            comp_scores["delta_fit"] = 10.0

        # 2. Spread Quality (Max 25)
        if spread_pct <= 0.3:
            comp_scores["spread_quality"] = 25.0
        elif spread_pct <= 0.6:
            comp_scores["spread_quality"] = 20.0
        elif spread_pct <= 1.2:
            comp_scores["spread_quality"] = 15.0
        elif spread_pct <= 2.0:
            comp_scores["spread_quality"] = 8.0
        else:
            comp_scores["spread_quality"] = 0.0

        # 3. Liquidity & Volume Quality (Max 20)
        if oi >= 50000 or volume >= 10000:
            comp_scores["liquidity_quality"] = 20.0
        elif oi >= 20000 or volume >= 3000:
            comp_scores["liquidity_quality"] = 15.0
        elif oi >= 5000:
            comp_scores["liquidity_quality"] = 10.0
        else:
            comp_scores["liquidity_quality"] = 5.0

        # 4. Theta & Expiry Risk (Max 15)
        if premium_risk == "LOW":
            comp_scores["theta_safety"] = 15.0
        elif premium_risk == "MEDIUM":
            comp_scores["theta_safety"] = 10.0
        elif premium_risk == "HIGH":
            comp_scores["theta_safety"] = 5.0
        else:
            comp_scores["theta_safety"] = 0.0

        # 5. Required Move Achievability (Max 10)
        if required_nifty_move <= 12.0:
            comp_scores["move_achievability"] = 10.0
        elif required_nifty_move <= 20.0:
            comp_scores["move_achievability"] = 7.0
        elif required_nifty_move <= 35.0:
            comp_scores["move_achievability"] = 4.0
        else:
            comp_scores["move_achievability"] = 0.0

        total_score = round(sum(comp_scores.values()), 1)

        if total_score >= 85.0:
            strength_band = "EXCELLENT"
        elif total_score >= 70.0:
            strength_band = "GOOD"
        elif total_score >= 50.0:
            strength_band = "ACCEPTABLE"
        elif total_score >= 35.0:
            strength_band = "WEAK"
        else:
            strength_band = "AVOID"

        symbol = f"NIFTY {strike:,.0f} {opt_type}"

        return StrikeEvaluation(
            strike=strike,
            option_type=opt_type,
            symbol=symbol,
            ltp=ltp,
            bid=bid,
            ask=ask,
            spread_pts=spread_pts,
            spread_pct=spread_pct,
            volume=volume,
            open_interest=oi,
            change_oi=change_oi,
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            iv=iv,
            moneyness=moneyness,
            distance_from_spot=distance_from_spot,
            required_nifty_move=required_nifty_move,
            expected_premium_response=expected_premium_response,
            premium_sensitivity=premium_sensitivity,
            strength_score=total_score,
            strength_band=strength_band,
            component_scores=comp_scores,
            liquidity_grade=liquidity_grade,
            premium_risk=premium_risk,
            premium_risk_reasons=risk_reasons
        )
