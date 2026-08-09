# src/news_engine/impact_assessor.py
from __future__ import annotations

import re
from typing import Any, Dict, List

NIFTY_CONSTITUENT_METADATA = {
    "metadata_version": "1.0.0",
    "effective_date": "2026-08-07",
    "constituents": {
        "RELIANCE": {"sector": "Energy", "weight": 0.098},
        "HDFCBANK": {"sector": "Banking", "weight": 0.115},
        "ICICIBANK": {"sector": "Banking", "weight": 0.078},
        "INFY": {"sector": "Technology", "weight": 0.052},
        "TCS": {"sector": "Technology", "weight": 0.041},
        "ITC": {"sector": "Consumer Goods", "weight": 0.045},
        "LT": {"sector": "Construction", "weight": 0.038},
        "SBIN": {"sector": "Banking", "weight": 0.032},
        "BHARTIARTL": {"sector": "Telecom", "weight": 0.030},
        "KOTAKBANK": {"sector": "Banking", "weight": 0.027},
    }
}


class NewsImpactAssessor:
    """
    Stateless relevance and impact assessor using deterministic versioned rules.
    """
    RULE_VERSION = "1.2.0"

    @classmethod
    def assess_impact(cls, headline: str, content: str, source_type: str, category: str) -> Dict[str, Any]:
        text = f"{headline} {content}".lower()

        # 1. Identify affected constituents and sectors using versioned NIFTY metadata
        affected_symbols = []
        affected_sectors = []
        highest_weight = 0.0

        for symbol, meta in NIFTY_CONSTITUENT_METADATA["constituents"].items():
            pattern = r'\b' + re.escape(symbol.lower()) + r'\b'
            if re.search(pattern, text):
                affected_symbols.append(symbol)
                if meta["sector"] not in affected_sectors:
                    affected_sectors.append(meta["sector"])
                highest_weight = max(highest_weight, meta.get("weight", 0.0))

        # 2. Determine relevance score (0.0 to 10.0 scale)
        relevance = 1.0
        relevance_reasons = []

        if affected_symbols:
            relevance += 4.0
            relevance_reasons.append(f"Direct NIFTY constituent mention: {', '.join(affected_symbols)}")
            if highest_weight > 0.05:
                relevance += 3.0
                relevance_reasons.append(f"High index weight component (>5%): weight {highest_weight:.1%}")

        if category in {"RBI", "SEBI", "Exchange Operations"}:
            relevance += 5.0
            relevance_reasons.append(f"High policy/regulatory significance category: {category}")

        if source_type == "official":
            relevance += 3.0
            relevance_reasons.append("Official regulatory source publication")

        category_weight = {
            "Government Policy": 3.5,
            "Macro": 3.0,
            "Global Markets": 3.0,
            "Geopolitics": 4.0,
            "Crude": 3.5,
            "Currency/Yields": 3.5,
            "Corporate": 3.0,
            "Earnings": 3.5,
            "Exchange Operations": 3.0,
        }.get(category, 0.0)
        if category_weight:
            relevance += category_weight
            relevance_reasons.append(f"NIFTY-sensitive category: {category}")

        relevance = min(10.0, relevance)

        # 3. Deterministic sentiment assessment (directions: positive, negative, mixed, uncertain, not_assessed)
        positive_keywords = {
            "jump", "surge", "growth", "cut", "cuts", "positive", "buying", "rally", "profit", "cools", "ease",
            "record high", "beat", "higher", "approval", "dividend", "bonus"
        }
        negative_keywords = {
            "fall", "drop", "slump", "down", "crash", "war", "missile", "drone", "tension", "sanction", "selling",
            "hike", "hikes", "sticky", "hot", "deficit", "selloff", "penalty", "loss", "losses", "investigation"
        }

        cleaned = re.sub(r"[^a-z\s]", " ", text)
        words = cleaned.split()

        pos_matches = [w for w in words if w in positive_keywords]
        neg_matches = [w for w in words if w in negative_keywords]

        # Context-aware modifiers for oil & inflation
        if "oil" in words or "crude" in words:
            if any(w in words for w in ["rise", "surge", "higher", "jump"]):
                neg_matches.append("oil_rise")
            if any(w in words for w in ["fall", "cool", "ease", "drop"]):
                pos_matches.append("oil_drop")

        if "inflation" in words:
            if any(w in words for w in ["rise", "surge", "higher", "sticky", "hot"]):
                neg_matches.append("inflation_rise")
            if any(w in words for w in ["cool", "ease", "drop", "softens"]):
                pos_matches.append("inflation_drop")

        total_matches = len(pos_matches) + len(neg_matches)

        direction = "uncertain"
        confidence = 0.5
        reasons = []

        if total_matches == 0:
            direction = "not_assessed"
            confidence = 0.0
            reasons.append("No explicit directional keywords found")
        elif len(pos_matches) > 0 and len(neg_matches) > 0:
            direction = "mixed"
            confidence = 0.4
            reasons.append(f"Mixed signals: positive ({', '.join(pos_matches)}) and negative ({', '.join(neg_matches)})")
        elif len(pos_matches) > 0:
            direction = "positive"
            confidence = 0.8 if len(pos_matches) >= 2 else 0.6
            reasons.append(f"Positive matches found: {', '.join(pos_matches)}")
        elif len(neg_matches) > 0:
            direction = "negative"
            confidence = 0.8 if len(neg_matches) >= 2 else 0.6
            reasons.append(f"Negative matches found: {', '.join(neg_matches)}")

        # 4. Strength classification based on relevance
        if relevance >= 8.0:
            impact_strength = "high"
        elif relevance >= 5.0:
            impact_strength = "medium"
        else:
            impact_strength = "low"

        # 5. Duration classification
        if category in {"RBI", "SEBI", "Macro", "Geopolitics"}:
            impact_duration = "weekly"
        elif category in {"Earnings", "Corporate"}:
            impact_duration = "daily"
        else:
            impact_duration = "intraday"

        return {
            "nifty_relevance_score": round(relevance, 2),
            "expected_direction": direction,
            "impact_strength": impact_strength,
            "impact_duration": impact_duration,
            "confidence": round(confidence, 2),
            "affected_symbols": affected_symbols,
            "affected_sectors": affected_sectors,
            "assessment_reasons": reasons + relevance_reasons,
            "rule_version": cls.RULE_VERSION,
        }
