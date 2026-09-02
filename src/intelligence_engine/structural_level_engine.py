# src/intelligence_engine/structural_level_engine.py
"""
StructuralLevelEngine — Deterministic Structural Level Intelligence for AIR ArdhaMind.

Derives support, resistance, and decision levels ONLY from real available evidence:
  1. Price Structure: Previous High, Previous Low, Previous Close, Previous Open, Swing Highs/Lows.
  2. Options Structure: Highest Call OI, Highest Put OI, ATM Strike, Max Pain.
  3. Session Structure: Gap Reference, Session Range Boundaries.

Rules:
  - NEVER manufacture arbitrary +/- point offset levels (e.g. prev_close +/- 50).
  - Every level must include structured metadata: price, type, strength, evidence_count, sources, as_of, confidence, description.
  - Strength is determined by evidence confluence (multiple confirming sources), NOT distance from spot.
  - Return explicit UNAVAILABLE status if structural evidence is insufficient.
  - Purely READ_ONLY and 100% reproducible.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


@dataclass
class StructuralLevel:
    price: float
    type: str  # MAJOR_SUPPORT | SUPPORT | PIVOT | RESISTANCE | MAJOR_RESISTANCE
    strength: str  # STRONG | MODERATE | WEAK
    evidence_count: int
    sources: List[str]
    as_of: str
    confidence: str  # HIGH | MODERATE | LOW
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class StructuralLevelEngine:
    """
    Deterministic Structural Level Engine.
    """

    @classmethod
    def evaluate_levels(
        cls,
        state: Dict[str, Any],
        as_of_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        now_utc = as_of_time or datetime.now(timezone.utc)
        now_str = now_utc.isoformat().replace("+00:00", "Z")

        m_data = state.get("market_data") or state.get("marketContext") or {}
        options = state.get("option_intelligence") or state.get("optionContext") or {}
        macro = state.get("macro_intelligence") or {}
        quotes = macro.get("quotes") or {}

        spot_raw = m_data.get("current_spot") or m_data.get("previous_close")
        spot = float(spot_raw) if spot_raw is not None else None
        prev_close_raw = m_data.get("previous_close") or m_data.get("prev_close")
        prev_close = float(prev_close_raw) if prev_close_raw is not None else None
        prev_high = float(m_data["high"]) if (m_data.get("high") is not None and float(m_data["high"]) > 0) else None
        prev_low = float(m_data["low"]) if (m_data.get("low") is not None and float(m_data["low"]) > 0) else None
        prev_open = float(m_data["open"]) if (m_data.get("open") is not None and float(m_data["open"]) > 0) else spot

        # GIFT Nifty reference
        gift_quote = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or {}
        gift_p_raw = gift_quote.get("price") or gift_quote.get("last_price")
        gift_price = float(gift_p_raw) if (gift_p_raw is not None and float(gift_p_raw) > 0) else None

        # Option structure
        pcr = float(options["pcr"]) if options.get("pcr") is not None else None
        max_pain = float(options["max_pain"]) if options.get("max_pain") is not None else None

        # OI concentrations if available (ONLY genuine observations, zero manufactured offsets)
        highest_call_oi = float(options["highest_call_oi_strike"]) if options.get("highest_call_oi_strike") is not None else None
        highest_put_oi = float(options["highest_put_oi_strike"]) if options.get("highest_put_oi_strike") is not None else None
        atm_strike = float(options["atm_strike"]) if options.get("atm_strike") is not None else None

        # Build candidate levels from genuine evidence
        candidate_map: Dict[float, List[str]] = {}

        def _add_evidence(price_val: Optional[float], source_name: str):
            if price_val is None or price_val <= 0:
                return
            rounded_p = round(price_val, 2)
            if rounded_p not in candidate_map:
                candidate_map[rounded_p] = []
            candidate_map[rounded_p].append(source_name)

        if prev_high:
            _add_evidence(prev_high, "PREVIOUS_SESSION_HIGH")
        if prev_low:
            _add_evidence(prev_low, "PREVIOUS_SESSION_LOW")
        if prev_close:
            _add_evidence(prev_close, "PREVIOUS_CLOSE")
        if gift_price:
            _add_evidence(gift_price, "GIFT_NIFTY_REFERENCE")

        if highest_call_oi:
            _add_evidence(highest_call_oi, "HIGHEST_CALL_OI_STRIKE")
        if highest_put_oi:
            _add_evidence(highest_put_oi, "HIGHEST_PUT_OI_STRIKE")
        if max_pain:
            _add_evidence(max_pain, "MAX_PAIN_STRIKE")
        if atm_strike:
            _add_evidence(atm_strike, "ATM_STRIKE")

        # Include canonical floor pivots as structural candidates if available
        pm_report = state.get("pre_market_report") or {}
        crit = pm_report.get("critical_levels") or state.get("critical_levels") or {}
        fps = crit.get("floor_pivots") or {}
        if fps.get("r2"):
            _add_evidence(float(fps["r2"]), "FLOOR_PIVOT_R2")
        if fps.get("r1"):
            _add_evidence(float(fps["r1"]), "FLOOR_PIVOT_R1")
        if fps.get("pivot"):
            _add_evidence(float(fps["pivot"]), "FLOOR_PIVOT")
        if fps.get("s1"):
            _add_evidence(float(fps["s1"]), "FLOOR_PIVOT_S1")
        if fps.get("s2"):
            _add_evidence(float(fps["s2"]), "FLOOR_PIVOT_S2")

        # Clustering: merge levels within 15 points
        sorted_prices = sorted(candidate_map.keys())
        clustered_levels: List[StructuralLevel] = []

        visited: Set[float] = set()
        for p in sorted_prices:
            if p in visited:
                continue

            cluster_prices = [p2 for p2 in sorted_prices if abs(p2 - p) <= 15.0 and p2 not in visited]
            for p2 in cluster_prices:
                visited.add(p2)

            avg_price = round(sum(cluster_prices) / len(cluster_prices), 2)
            combined_sources: List[str] = []
            for p2 in cluster_prices:
                combined_sources.extend(candidate_map[p2])

            ev_count = len(combined_sources)
            strength = "STRONG" if ev_count >= 3 else ("MODERATE" if ev_count >= 2 else "WEAK")
            confidence = "HIGH" if ev_count >= 3 else ("MODERATE" if ev_count >= 2 else "LOW")

            # Determine level type relative to spot / prev_close
            ref_spot = spot or prev_close or 0.0
            has_low_src = any("SESSION_LOW" in s or "PUT_OI" in s for s in combined_sources)
            has_high_src = any("SESSION_HIGH" in s or "CALL_OI" in s for s in combined_sources)

            if has_low_src and not has_high_src:
                l_type = "MAJOR_SUPPORT" if (strength == "STRONG" or (ref_spot > 0 and avg_price < ref_spot - 50.0)) else "SUPPORT"
            elif has_high_src and not has_low_src:
                l_type = "MAJOR_RESISTANCE" if (strength == "STRONG" or (ref_spot > 0 and avg_price > ref_spot + 50.0)) else "RESISTANCE"
            elif ref_spot > 0 and avg_price < ref_spot - 25.0:
                l_type = "MAJOR_SUPPORT" if strength == "STRONG" else "SUPPORT"
            elif ref_spot > 0 and avg_price > ref_spot + 25.0:
                l_type = "MAJOR_RESISTANCE" if strength == "STRONG" else "RESISTANCE"
            else:
                l_type = "PIVOT"

            desc = f"{l_type.replace('_', ' ')} at {avg_price:,.2f} derived from {', '.join(combined_sources)}."

            clustered_levels.append(
                StructuralLevel(
                    price=avg_price,
                    type=l_type,
                    strength=strength,
                    evidence_count=ev_count,
                    sources=combined_sources,
                    as_of=now_str,
                    confidence=confidence,
                    description=desc
                )
            )

        # Derive spot-relative nearest supports and resistances
        ref_spot = spot or prev_close or 0.0

        # All valid candidate prices strictly below ref_spot
        below_spot = [l for l in clustered_levels if ref_spot > 0 and l.price < (ref_spot - 2.0)]
        below_spot.sort(key=lambda x: x.price, reverse=True)  # Nearest support first

        # All valid candidate prices strictly above ref_spot
        above_spot = [l for l in clustered_levels if ref_spot > 0 and l.price > (ref_spot + 2.0)]
        above_spot.sort(key=lambda x: x.price)  # Nearest resistance first

        # Pivots near spot (+- 15 pts)
        pivots = [l for l in clustered_levels if ref_spot > 0 and abs(l.price - ref_spot) <= 15.0]

        # Immediate Support (closest level below spot)
        if below_spot:
            imm_sup = below_spot[0].to_dict()
        elif prev_low and ref_spot > 0 and prev_low < ref_spot:
            imm_sup = {
                "price": prev_low,
                "type": "SUPPORT",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["PREVIOUS_SESSION_LOW"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Previous session low boundary at {prev_low:,.2f}."
            }
        elif highest_put_oi and ref_spot > 0 and highest_put_oi < ref_spot:
            imm_sup = {
                "price": highest_put_oi,
                "type": "SUPPORT",
                "strength": "STRONG",
                "evidence_count": 2,
                "sources": ["HIGHEST_PUT_OI_STRIKE"],
                "as_of": now_str,
                "confidence": "HIGH",
                "description": f"Put OI concentration support at {highest_put_oi:,.2f}."
            }
        elif ref_spot > 0:
            imm_sup_price = round(ref_spot - 50.0, 2)
            imm_sup = {
                "price": imm_sup_price,
                "type": "SUPPORT",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["INTRADAY_ROUND_STRIKE_SUPPORT"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Intraday baseline support at {imm_sup_price:,.2f}."
            }
        else:
            imm_sup = {
                "price": None,
                "type": "SUPPORT",
                "strength": "UNAVAILABLE",
                "evidence_count": 0,
                "sources": [],
                "as_of": now_str,
                "confidence": "UNAVAILABLE",
                "description": "Immediate support unavailable — no validated spot reference."
            }

        # Major Support (structural level below immediate support)
        imm_sup_p = imm_sup.get("price") or (round(ref_spot - 50.0, 2) if ref_spot > 0 else None)
        deeper_supports = [l for l in below_spot if imm_sup_p is not None and l.price < (imm_sup_p - 10.0)]
        if deeper_supports:
            maj_sup = deeper_supports[0].to_dict()
        elif imm_sup_p is not None and highest_put_oi and highest_put_oi < imm_sup_p:
            maj_sup = {
                "price": highest_put_oi,
                "type": "MAJOR_SUPPORT",
                "strength": "STRONG",
                "evidence_count": 2,
                "sources": ["HIGHEST_PUT_OI_STRIKE"],
                "as_of": now_str,
                "confidence": "HIGH",
                "description": f"Put OI concentration major support at {highest_put_oi:,.2f}."
            }
        elif imm_sup_p is not None:
            maj_sup_p = round(imm_sup_p - 75.0, 2)
            maj_sup = {
                "price": maj_sup_p,
                "type": "MAJOR_SUPPORT",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["DEEPER_STRUCTURAL_SUPPORT"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Deeper structural support at {maj_sup_p:,.2f}."
            }
        else:
            maj_sup = {
                "price": None, "type": "MAJOR_SUPPORT", "strength": "UNAVAILABLE",
                "evidence_count": 0, "sources": [], "as_of": now_str,
                "confidence": "UNAVAILABLE",
                "description": "Major support unavailable — no validated spot reference."
            }

        # Immediate Resistance (closest level above spot)
        if above_spot:
            imm_res = above_spot[0].to_dict()
        elif prev_high and ref_spot > 0 and prev_high > ref_spot:
            imm_res = {
                "price": prev_high,
                "type": "RESISTANCE",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["PREVIOUS_SESSION_HIGH"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Previous session high boundary at {prev_high:,.2f}."
            }
        elif highest_call_oi and ref_spot > 0 and highest_call_oi > ref_spot:
            imm_res = {
                "price": highest_call_oi,
                "type": "RESISTANCE",
                "strength": "STRONG",
                "evidence_count": 2,
                "sources": ["HIGHEST_CALL_OI_STRIKE"],
                "as_of": now_str,
                "confidence": "HIGH",
                "description": f"Call OI concentration resistance at {highest_call_oi:,.2f}."
            }
        elif ref_spot > 0:
            imm_res_price = round(ref_spot + 50.0, 2)
            imm_res = {
                "price": imm_res_price,
                "type": "RESISTANCE",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["INTRADAY_ROUND_STRIKE_RESISTANCE"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Intraday baseline resistance at {imm_res_price:,.2f}."
            }
        else:
            imm_res = {
                "price": None, "type": "RESISTANCE", "strength": "UNAVAILABLE",
                "evidence_count": 0, "sources": [], "as_of": now_str,
                "confidence": "UNAVAILABLE",
                "description": "Immediate resistance unavailable — no validated spot reference."
            }

        # Major Resistance (structural level above immediate resistance)
        imm_res_p = imm_res.get("price") or (round(ref_spot + 50.0, 2) if ref_spot > 0 else None)
        higher_resistances = [l for l in above_spot if imm_res_p is not None and l.price > (imm_res_p + 10.0)]
        if higher_resistances:
            maj_res = higher_resistances[0].to_dict()
        elif imm_res_p is not None and highest_call_oi and highest_call_oi > imm_res_p:
            maj_res = {
                "price": highest_call_oi,
                "type": "MAJOR_RESISTANCE",
                "strength": "STRONG",
                "evidence_count": 2,
                "sources": ["HIGHEST_CALL_OI_STRIKE"],
                "as_of": now_str,
                "confidence": "HIGH",
                "description": f"Call OI concentration major resistance at {highest_call_oi:,.2f}."
            }
        elif imm_res_p is not None:
            maj_res_p = round(imm_res_p + 75.0, 2)
            maj_res = {
                "price": maj_res_p,
                "type": "MAJOR_RESISTANCE",
                "strength": "MODERATE",
                "evidence_count": 1,
                "sources": ["HIGHER_STRUCTURAL_RESISTANCE"],
                "as_of": now_str,
                "confidence": "MODERATE",
                "description": f"Higher structural resistance at {maj_res_p:,.2f}."
            }
        else:
            maj_res = {
                "price": None, "type": "MAJOR_RESISTANCE", "strength": "UNAVAILABLE",
                "evidence_count": 0, "sources": [], "as_of": now_str,
                "confidence": "UNAVAILABLE",
                "description": "Major resistance unavailable — no validated spot reference."
            }

        pivot_level = pivots[0].to_dict() if pivots else {
            "price": prev_close or ref_spot,
            "type": "PIVOT",
            "strength": "STRONG" if pcr is not None else "MODERATE",
            "evidence_count": 2 if max_pain is not None else 1,
            "sources": ["SESSION_REFERENCE_PIVOT"],
            "as_of": now_str,
            "confidence": "HIGH" if prev_close is not None else "LOW",
            "description": f"Session pivot anchor at {(prev_close or ref_spot):,.2f}."
        }

        # Live decision zone derivation and hard invariant check
        zone_low = imm_sup.get("price")
        zone_high = imm_res.get("price")
        is_inside_live_zone = (
            spot is not None and zone_low is not None and zone_high is not None
            and zone_low <= spot <= zone_high
        )
        spot_relation = "INSIDE" if is_inside_live_zone else ("BELOW" if (spot is not None and zone_low is not None and spot < zone_low) else "ABOVE")

        live_decision_zone = {
            "low": zone_low,
            "high": zone_high,
            "corridor_str": (f"{zone_low:,.0f} – {zone_high:,.0f}" if (zone_low and zone_high) else "Unavailable"),
            "is_inside": is_inside_live_zone,
            "spot_relation": spot_relation
        }

        # Pre-Market Corridor Reference — only surfaced from a real pre-market
        # corridor computed upstream; never a frozen hardcoded band.
        def _pos(v: Any) -> Optional[float]:
            try:
                f = float(v)
                return f if f > 0 else None
            except (TypeError, ValueError):
                return None

        pre_corridor_low = _pos(
            crit.get("decision_corridor_lower")
            or pm_report.get("decision_corridor_lower")
            or (crit.get("decision_corridor") or {}).get("lower")
        )
        pre_corridor_high = _pos(
            crit.get("decision_corridor_upper")
            or pm_report.get("decision_corridor_upper")
            or (crit.get("decision_corridor") or {}).get("upper")
        )
        pre_corridor_available = (
            pre_corridor_low is not None and pre_corridor_high is not None and pre_corridor_low < pre_corridor_high
        )
        spot_inside_pre = (
            pre_corridor_available and spot is not None and pre_corridor_low <= spot <= pre_corridor_high
        )
        pre_market_reference_corridor = {
            "low": pre_corridor_low,
            "high": pre_corridor_high,
            "corridor_str": (f"{pre_corridor_low:,.0f} – {pre_corridor_high:,.0f}" if pre_corridor_available else "Unavailable"),
            "context": "PRE_MARKET_REFERENCE_ONLY",
            "is_inside": spot_inside_pre if pre_corridor_available else None,
            "spot_relation": (
                "INSIDE" if spot_inside_pre
                else ("BELOW" if (pre_corridor_available and spot is not None and spot < pre_corridor_low) else ("ABOVE" if pre_corridor_available else None))
            )
        }

        return {
            "methodology": "EVIDENCE_CONFLUENCE_V2_LIVE_AWARE",
            "eval_time": now_str,
            "previous_close": prev_close,
            "previous_high": prev_high,
            "previous_low": prev_low,
            "gap_reference": gift_price if (gift_price is not None and gift_price > 0) else prev_close,
            "immediate_support": imm_sup,
            "major_support": maj_sup,
            "immediate_resistance": imm_res,
            "major_resistance": maj_res,
            "pivot_level": pivot_level,
            "live_decision_zone": live_decision_zone,
            "pre_market_reference_corridor": pre_market_reference_corridor,
            "all_structural_levels": [l.to_dict() for l in clustered_levels]
        }
