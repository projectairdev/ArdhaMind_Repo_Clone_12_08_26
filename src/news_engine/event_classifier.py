from __future__ import annotations

import re
from typing import Dict, Set

class EventClassifier:
    """
    Stateless classification engine assigning standard categories based on semantic keyword density.
    Categories:
    - Central Bank
    - Inflation
    - GDP
    - Corporate Earnings
    - Geopolitics
    - Regulation
    - Technology
    - Energy
    - Macro Economy
    - Global Markets
    """

    CLASSIFIER_RULES: Dict[str, Set[str]] = {
        "Central Bank": {
            "rbi", "fed", "federal reserve", "fomc", "ecb", "repo rate", "rate cut", "rate hike", "monetary policy",
            "hawkish", "dovish", "central bank", "interest rate", "interest rates", "policy rate", "mpc"
        },
        "Inflation": {
            "inflation", "cpi", "wpi", "consumer price", "prices rise", "pricing pressure", "cost of living"
        },
        "GDP": {
            "gdp", "gdp growth", "national output", "gva", "economic growth", "economic expansion"
        },
        "Corporate Earnings": {
            "q1", "q2", "q3", "q4", "net profit", "revenue", "earnings", "corporate earnings", "dividend",
            "ril results", "profit jumps", "profit falls", "profit surges", "operating margin", "balance sheet"
        },
        "Geopolitics": {
            "war", "missile", "drone", "strike", "attack", "conflict", "border", "ceasefire", "truce", "sanction",
            "geopolitical", "tariffs", "trade war", "military", "defense", "escalation", "de-escalation"
        },
        "Regulation": {
            "regulation", "sebi", "sec", "regulatory", "guideline", "rules", "policy change", "taxation",
            "gst", "capital gains tax", "compliance", "ban", "audit", "investigation"
        },
        "Technology": {
            "technology", "tech", "ai", "artificial intelligence", "semiconductor", "chip", "software",
            "cyber", "telecom", "jio", "5g", "cloud", "digitalization"
        },
        "Energy": {
            "energy", "crude", "oil", "brent", "wti", "refinery", "gas", "coal", "petroleum", "solar", "wind",
            "power grid", "power generation"
        },
        "Global Markets": {
            "global markets", "wall street", "nasdaq", "dow", "s&p 500", "nikkei", "hang seng", "ftse", "dax",
            "foreign cues", "global cues", "us market", "european markets", "fii", "foreign portfolio", "fpi"
        }
    }

    @classmethod
    def classify(cls, title: str, content: str = "") -> str:
        """
        Classifies an article/event based on pattern matching scores.
        Returns the category with highest match density, defaulting to "Macro Economy".
        """
        text = f"{title} {content}".lower()
        # Clean special chars to simplify word matches
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        
        scores: Dict[str, int] = {}
        for category, keywords in cls.CLASSIFIER_RULES.items():
            score = 0
            for kw in keywords:
                # Add score based on occurrences of keyword with word boundaries
                matches = re.findall(r'\b' + re.escape(kw) + r'\b', text)
                score += len(matches)
            if score > 0:
                scores[category] = score

        if not scores:
            # Fallback checks or default to "Macro Economy"
            if "economic" in text or "market" in text or "india" in text:
                return "Macro Economy"
            return "Macro Economy"

        # Return category with highest matching score
        sorted_cats = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return sorted_cats[0][0]
