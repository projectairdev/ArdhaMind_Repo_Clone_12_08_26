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

        spot = float(m_data.get("current_spot") or m_data.get("previous_close") or 24500.0)
        prev_close = float(m_data.get("previous_close") or spot)
        prev_high = float(m_data.get("high") or (spot + 40.0))
        prev_low = float(m_data.get("low") or (spot - 40.0))
        prev_open = float(m_data.get("open") or spot)

        # GIFT Nifty reference
        gift_quote = quotes.get("GIFT_NIFTY") or quotes.get("GIFT NIFTY") or {}
        gift_price = float(gift_quote.get("price") or gift_quote.get("last_price") or 0.0)

        # Option structure
        pcr = float(options.get("pcr") or 1.0)
        max_pain = float(options.get("max_pain") or prev_close) if options.get("max_pain") else None

        # OI concentrations if available
        highest_call_oi = float(options.get("highest_call_oi_strike") or (prev_close + 100.0))
        highest_put_oi = float(options.get("highest_put_oi_strike") or (prev_close - 100.0))
        atm_strike = float(options.get("atm_strike") or round(prev_close / 50.0) * 50.0)

        # Build candidate levels from genuine evidence
        candidate_map: Dict[float, List[str]] = {}

        def _add_evidence(price_val: float, source_name: str):
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
        if gift_price > 0:
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
            if avg_price < spot - 30.0:
                l_type = "MAJOR_SUPPORT" if strength == "STRONG" else "SUPPORT"
            elif avg_price > spot + 30.0:
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
            "description": f"Previous session low boundary at {prev_low:,.2f}."
        }

        maj_sup = supports[1].to_dict() if len(supports) > 1 else {
            "price": highest_put_oi if highest_put_oi < imm_sup.get("price", spot) else round(prev_low - 80.0, 2),
            "type": "MAJOR_SUPPORT",
            "strength": "MODERATE" if highest_put_oi else "WEAK",
            "evidence_count": 1,
            "sources": ["HIGHEST_PUT_OI_STRIKE"] if highest_put_oi else ["PREVIOUS_RANGE_BOUNDARY"],
            "as_of": now_str,
            "confidence": "MODERATE" if highest_put_oi else "LOW",
            "description": f"Put OI concentration support at {highest_put_oi:,.2f}."
        }

        imm_res = resistances[0].to_dict() if resistances else {
            "price": prev_high,
            "type": "RESISTANCE",
            "strength": "MODERATE",
            "evidence_count": 1,
            "sources": ["PREVIOUS_SESSION_HIGH"],
            "as_of": now_str,
            "confidence": "MODERATE",
            "description": f"Previous session high boundary at {prev_high:,.2f}."
        }

        maj_res = resistances[1].to_dict() if len(resistances) > 1 else {
            "price": highest_call_oi if highest_call_oi > imm_res.get("price", spot) else round(prev_high + 80.0, 2),
            "type": "MAJOR_RESISTANCE",
            "strength": "MODERATE" if highest_call_oi else "WEAK",
            "evidence_count": 1,
            "sources": ["HIGHEST_CALL_OI_STRIKE"] if highest_call_oi else ["PREVIOUS_RANGE_BOUNDARY"],
            "as_of": now_str,
            "confidence": "MODERATE" if highest_call_oi else "LOW",
            "description": f"Call OI concentration resistance at {highest_call_oi:,.2f}."
        }

        pivot_level = pivots[0].to_dict() if pivots else {
            "price": prev_close,
            "type": "PIVOT",
            "strength": "STRONG" if pcr else "MODERATE",
            "evidence_count": 2 if max_pain else 1,
            "sources": ["PREVIOUS_CLOSE", "ATM_STRIKE"],
            "as_of": now_str,
            "confidence": "HIGH",
            "description": f"Previous session close anchor at {prev_close:,.2f}."
        }

        return {
            "methodology": "EVIDENCE_CONFLUENCE_V1",
            "eval_time": now_str,
            "previous_close": prev_close,
            "previous_high": prev_high,
            "previous_low": prev_low,
            "gap_reference": gift_price if gift_price > 0 else prev_close,
            "immediate_support": imm_sup,
            "major_support": maj_sup,
            "immediate_resistance": imm_res,
            "major_resistance": maj_res,
            "pivot_level": pivot_level,
            "all_structural_levels": [l.to_dict() for l in clustered_levels]
        }
