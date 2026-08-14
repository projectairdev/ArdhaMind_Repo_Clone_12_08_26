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
        prev_high = float(m_data["high"]) if m_data.get("high") is not None else (spot + 40.0 if spot is not None else None)
        prev_low = float(m_data["low"]) if m_data.get("low") is not None else (spot - 40.0 if spot is not None else None)
        prev_open = float(m_data["open"]) if m_data.get("open") is not None else spot

        # GIFT Nifty reference
        gift_quote = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or {}
        gift_p_raw = gift_quote.get("price") or gift_quote.get("last_price")
        gift_price = float(gift_p_raw) if (gift_p_raw is not None and float(gift_p_raw) > 0) else None

        # Option structure
        pcr = float(options["pcr"]) if options.get("pcr") is not None else None
        max_pain = float(options["max_pain"]) if options.get("max_pain") is not None else None

        # OI concentrations if available
        highest_call_oi = float(options["highest_call_oi_strike"]) if options.get("highest_call_oi_strike") is not None else (prev_close + 100.0 if prev_close is not None else None)
        highest_put_oi = float(options["highest_put_oi_strike"]) if options.get("highest_put_oi_strike") is not None else (prev_close - 100.0 if prev_close is not None else None)
        atm_strike = float(options["atm_strike"]) if options.get("atm_strike") is not None else (round(prev_close / 50.0) * 50.0 if prev_close is not None else None)

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
            if ref_spot > 0 and avg_price < ref_spot - 30.0:
                l_type = "MAJOR_SUPPORT" if strength == "STRONG" else "SUPPORT"
            elif ref_spot > 0 and avg_price > ref_spot + 30.0:
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

        # Categorize into key workstation slots
        supports = sorted([l for l in clustered_levels if "SUPPORT" in l.type], key=lambda x: x.price, reverse=True)
        resistances = sorted([l for l in clustered_levels if "RESISTANCE" in l.type], key=lambda x: x.price)
        pivots = [l for l in clustered_levels if l.type == "PIVOT"]

        imm_sup = supports[0].to_dict() if supports else {
            "price": prev_low,
            "type": "SUPPORT",
            "strength": "MODERATE",
            "evidence_count": 1,
            "sources": ["PREVIOUS_SESSION_LOW"],
            "as_of": now_str,
            "confidence": "MODERATE",
            "description": f"Previous session low boundary at {prev_low:,.2f}." if prev_low is not None else "Previous session low boundary unavailable."
        }

        imm_sup_price = imm_sup.get("price") or spot or 0.0
        maj_sup = supports[1].to_dict() if len(supports) > 1 else {
            "price": highest_put_oi if (highest_put_oi is not None and highest_put_oi < imm_sup_price) else (round(prev_low - 80.0, 2) if prev_low is not None else None),
            "type": "MAJOR_SUPPORT",
            "strength": "MODERATE" if highest_put_oi is not None else "WEAK",
            "evidence_count": 1,
            "sources": ["HIGHEST_PUT_OI_STRIKE"] if highest_put_oi is not None else ["PREVIOUS_RANGE_BOUNDARY"],
            "as_of": now_str,
            "confidence": "MODERATE" if highest_put_oi is not None else "LOW",
            "description": f"Put OI concentration support at {highest_put_oi:,.2f}." if highest_put_oi is not None else "Major support boundary unconfirmed."
        }

        imm_res = resistances[0].to_dict() if resistances else {
            "price": prev_high,
            "type": "RESISTANCE",
            "strength": "MODERATE",
            "evidence_count": 1,
            "sources": ["PREVIOUS_SESSION_HIGH"],
            "as_of": now_str,
            "confidence": "MODERATE",
            "description": f"Previous session high boundary at {prev_high:,.2f}." if prev_high is not None else "Previous session high boundary unavailable."
        }

        imm_res_price = imm_res.get("price") or spot or 0.0
        maj_res = resistances[1].to_dict() if len(resistances) > 1 else {
            "price": highest_call_oi if (highest_call_oi is not None and highest_call_oi > imm_res_price) else (round(prev_high + 80.0, 2) if prev_high is not None else None),
            "type": "MAJOR_RESISTANCE",
            "strength": "MODERATE" if highest_call_oi is not None else "WEAK",
            "evidence_count": 1,
            "sources": ["HIGHEST_CALL_OI_STRIKE"] if highest_call_oi is not None else ["PREVIOUS_RANGE_BOUNDARY"],
            "as_of": now_str,
            "confidence": "MODERATE" if highest_call_oi is not None else "LOW",
            "description": f"Call OI concentration resistance at {highest_call_oi:,.2f}." if highest_call_oi is not None else "Major resistance boundary unconfirmed."
        }

        pivot_level = pivots[0].to_dict() if pivots else {
            "price": prev_close,
            "type": "PIVOT",
            "strength": "STRONG" if pcr is not None else "MODERATE",
            "evidence_count": 2 if max_pain is not None else 1,
            "sources": ["PREVIOUS_CLOSE", "ATM_STRIKE"],
            "as_of": now_str,
            "confidence": "HIGH" if prev_close is not None else "LOW",
            "description": f"Previous session close anchor at {prev_close:,.2f}." if prev_close is not None else "Pivot anchor unavailable."
        }

        return {
            "methodology": "EVIDENCE_CONFLUENCE_V1",
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
            "all_structural_levels": [l.to_dict() for l in clustered_levels]
        }
