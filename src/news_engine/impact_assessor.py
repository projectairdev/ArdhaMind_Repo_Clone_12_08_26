# src/news_engine/impact_assessor.py
"""
Stateless relevance and impact assessor using deterministic versioned rules for AIR ArdhaMind.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

NIFTY_CONSTITUENT_METADATA = {
    "metadata_version": "2.0.0",
    "effective_date": "2026-08-17",
    "constituents": {
        "RELIANCE": {"name": "Reliance Industries", "sector": "ENERGY", "weight": 0.098, "aliases": ["reliance industries", "ril"]},
        "HDFCBANK": {"name": "HDFC Bank", "sector": "BANKING", "weight": 0.115, "aliases": ["hdfc bank", "hdfcbank"]},
        "ICICIBANK": {"name": "ICICI Bank", "sector": "BANKING", "weight": 0.078, "aliases": ["icici bank", "icicibank"]},
        "INFY": {"name": "Infosys", "sector": "IT", "weight": 0.052, "aliases": ["infosys", "infy"]},
        "TCS": {"name": "Tata Consultancy Services", "sector": "IT", "weight": 0.041, "aliases": ["tata consultancy services", "tcs"]},
        "ITC": {"name": "ITC Limited", "sector": "FMCG", "weight": 0.045, "aliases": ["itc limited", "itc ltd"]},
        "LT": {"name": "Larsen & Toubro", "sector": "INFRA", "weight": 0.038, "aliases": ["larsen & toubro", "l&t"]},
        "SBIN": {"name": "State Bank of India", "sector": "BANKING", "weight": 0.032, "aliases": ["state bank of india", "sbin", "sbi"]},
        "BHARTIARTL": {"name": "Bharti Airtel", "sector": "TELECOM", "weight": 0.030, "aliases": ["bharti airtel", "airtel"]},
        "KOTAKBANK": {"name": "Kotak Mahindra Bank", "sector": "BANKING", "weight": 0.027, "aliases": ["kotak mahindra bank", "kotak bank"]},
    }
}


class NewsImpactAssessor:
    """
    Stateless relevance and impact assessor using token-boundary entity matching and canonical taxonomy.
    """
    RULE_VERSION = "2.0.0"

    @classmethod
    def assess_impact(cls, headline: str, content: str, source_type: str, category: str) -> Dict[str, Any]:
        text = f"{headline} {content}".lower()

        # 1. Boundary-safe entity matching against NIFTY constituents
        affected_symbols: List[str] = []
        affected_sectors: List[str] = []
        highest_weight = 0.0

        for symbol, meta in NIFTY_CONSTITUENT_METADATA["constituents"].items():
            matched = False
            for alias in [symbol.lower()] + meta.get("aliases", []):
                pattern = r'(?<![a-z0-9])' + re.escape(alias) + r'(?![a-z0-9])'
                if re.search(pattern, text):
                    matched = True
                    break
            if matched:
                affected_symbols.append(symbol)
                if meta["sector"] not in affected_sectors:
                    affected_sectors.append(meta["sector"])
                highest_weight = max(highest_weight, meta.get("weight", 0.0))

        if not affected_sectors:
            if category in {"RBI_MONETARY", "BANKING_FINANCIALS"}:
                affected_sectors = ["BANKING"]
            elif category in {"FED_MONETARY", "US_MACRO", "IT_TECH"}:
                affected_sectors = ["IT"]
            elif category in {"COMMODITIES", "ENERGY"}:
                affected_sectors = ["ENERGY"]
            else:
                affected_sectors = ["BROAD_MARKET"]

        # 2. Determine relevance score (0.0 to 100.0 scale)
        relevance = 20.0
        relevance_reasons = []

        if affected_symbols:
            relevance += 40.0
            relevance_reasons.append(f"Direct NIFTY constituent mention: {', '.join(affected_symbols)}")
            if highest_weight > 0.05:
                relevance += 30.0
                relevance_reasons.append(f"High index weight component (>5%): weight {highest_weight:.1%}")

        if category in {"RBI_MONETARY", "SEBI_REGULATION", "FED_MONETARY"}:
            relevance += 40.0
            relevance_reasons.append(f"High policy/regulatory significance category: {category}")

        if source_type == "official" or source_type == "OFFICIAL":
            relevance += 20.0
            relevance_reasons.append("Official regulatory source publication")

        category_weight = {
            "GOVERNMENT_POLICY": 25.0,
            "INDIA_MACRO": 30.0,
            "GLOBAL_MARKETS": 25.0,
            "GEOPOLITICS": 35.0,
            "COMMODITIES": 30.0,
            "FX_RATES": 25.0,
            "CORPORATE_NIFTY": 30.0,
        }.get(category, 0.0)

        if category_weight:
            relevance += category_weight
            relevance_reasons.append(f"NIFTY-sensitive category: {category}")

        relevance = min(100.0, relevance)

        # 3. Deterministic sentiment & direction assessment
        positive_keywords = {
            "jump", "surge", "growth", "cut", "cuts", "positive", "buying", "rally", "profit", "cools", "ease",
            "record high", "beat", "higher", "approval", "dividend", "bonus", "injection", "easing"
        }
        negative_keywords = {
            "fall", "drop", "slump", "down", "crash", "war", "missile", "drone", "tension", "sanction", "selling",
            "hike", "hikes", "sticky", "hot", "deficit", "selloff", "penalty", "loss", "losses", "investigation",
            "risk", "concerns", "intensify", "spikes"
        }

        cleaned = re.sub(r"[^a-z\s]", " ", text)
        words = cleaned.split()

        pos_matches = [w for w in words if w in positive_keywords]
        neg_matches = [w for w in words if w in negative_keywords]

        if "oil" in words or "crude" in words or "brent" in words:
            if any(w in words for w in ["rise", "rises", "surge", "surges", "higher", "jump", "jumps", "risk", "concerns"]):
                neg_matches.append("oil_rise")
                if "jump" in pos_matches: pos_matches.remove("jump")
                if "jumps" in pos_matches: pos_matches.remove("jumps")

        if "inflation" in words:
            if any(w in words for w in ["rise", "surge", "higher", "sticky", "hot", "concerns", "intensify"]):
                neg_matches.append("inflation_rise")
                if "jump" in pos_matches: pos_matches.remove("jump")
                if "jumps" in pos_matches: pos_matches.remove("jumps")

        total_matches = len(pos_matches) + len(neg_matches)

        if total_matches == 0:
            direction = "UNCLEAR"
            confidence = 0.0
            reasons = ["No explicit directional keywords found"]
        elif len(pos_matches) > 0 and len(neg_matches) > 0:
            direction = "MIXED"
            confidence = 0.4
            reasons = [f"Mixed signals: positive ({', '.join(pos_matches)}) and negative ({', '.join(neg_matches)})"]
        elif len(pos_matches) > 0:
            direction = "POSITIVE"
            confidence = 0.8 if len(pos_matches) >= 2 else 0.6
            reasons = [f"Positive matches found: {', '.join(pos_matches)}"]
        elif len(neg_matches) > 0:
            direction = "NEGATIVE"
            confidence = 0.8 if len(neg_matches) >= 2 else 0.6
            reasons = [f"Negative matches found: {', '.join(neg_matches)}"]
        else:
            direction = "UNCLEAR"
            confidence = 0.0
            reasons = ["Direction unclassified"]

        if relevance >= 75.0:
            impact_strength = "HIGH"
        elif relevance >= 45.0:
            impact_strength = "MEDIUM"
        else:
            impact_strength = "LOW"

        if category in {"RBI_MONETARY", "SEBI_REGULATION", "INDIA_MACRO", "GEOPOLITICS"}:
            impact_duration = "MULTI-DAY"
        elif category in {"CORPORATE_NIFTY", "BANKING_FINANCIALS", "IT_TECH"}:
            impact_duration = "1-3 DAYS"
        else:
            impact_duration = "INTRADAY"

        return {
            "nifty_relevance_score": round(relevance / 100.0, 2),
            "nifty_relevance_raw": round(relevance, 1),
            "expected_direction": direction,
            "impact_strength": impact_strength,
            "impact_duration": impact_duration,
            "confidence": round(confidence, 2),
            "affected_symbols": affected_symbols,
            "affected_sectors": [s for s in affected_sectors if s != "NIFTY 50"],
            "assessment_reasons": reasons + relevance_reasons,
            "rule_version": cls.RULE_VERSION,
        }
