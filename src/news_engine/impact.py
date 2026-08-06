from __future__ import annotations

import re
from typing import List, Tuple, Optional
from src.models.news_context_v2 import (
    AffectedIndex,
    AffectedSector,
    AffectedMarket,
    MarketImpact,
    EventSeverity,
)

class MarketImpactEvaluator:
    """
    Stateless evaluator assessing expected direction, time horizon,
    affected indices, affected sectors, and market scopes.
    """

    SECTORS_KEYWORDS = {
        "Banking": ["bank", "rbi", "lending", "credit", "hdfc", "icici", "sbi", "nbfc", "finance", "financials"],
        "Technology": ["tech", "it", "infosys", "tcs", "software", "ai", "semiconductor", "digital", "infy"],
        "Energy": ["crude", "oil", "brent", "wti", "energy", "petroleum", "gas", "refinery", "reliance", "ril"],
        "Consumer Goods": ["retail", "consumer", "reliance retail", "fmcg", "jio", "telecom", "automobile", "auto"],
    }

    INDICES_KEYWORDS = {
        "Nifty 50": ["nifty", "nifty 50", "sensex", "indian market"],
        "Bank Nifty": ["bank nifty", "banknifty", "banking sector"],
        "Nasdaq": ["nasdaq", "tech heavy", "us tech"],
        "S&P 500": ["s&p 500", "sp500", "wall street"],
    }

    MARKETS_KEYWORDS = {
        "INDIA": ["india", "indian", "rbi", "nse", "bse", "rupee", "inr"],
        "GLOBAL": ["us", "usa", "fed", "federal reserve", "global", "europe", "china", "geopolitical"],
    }

    @staticmethod
    def _evaluate_sentiment(text: str) -> Tuple[str, float]:
        """
        Calculates simple rule-based sentiment direction and score (-1.0 to 1.0).
        """
        bullish_words = {
            "jump", "jumps", "rise", "rises", "surge", "surges", "growth", "grow", "cool", "cools", "easing",
            "supportive", "positive", "buying", "inflow", "record high", "beat", "upbeat", "rally", "gain", "gains",
            "dovish", "accommodative", "cut", "cuts", "profit", "profits", "higher"
        }
        bearish_words = {
            "fall", "falls", "drop", "drops", "slump", "slumps", "down", "crash", "war", "missile", "drone strike",
            "attack", "tension", "tensions", "escalation", "sanction", "sanctions", "selling", "outflow", "hawkish",
            "hike", "hikes", "sticky", "hot", "inflation", "high interest", "rate hike", "deficit", "selloff",
            "investigation", "penalty", "loss", "losses"
        }

        cleaned = re.sub(r"[^a-z\s]", " ", text.lower())
        words = cleaned.split()

        bull_count = sum(1 for w in words if w in bullish_words)
        bear_count = sum(1 for w in words if w in bearish_words)

        # Context-aware modifiers for oil & inflation
        # If oil is rising -> negative for Indian economy
        if "oil" in words or "crude" in words:
            if any(w in text for w in ["rise", "surge", "jump", "higher", "spike"]):
                bear_count += 2
            if any(w in text for w in ["fall", "cool", "ease", "lower", "drop"]):
                bull_count += 2

        # If inflation is rising/hot -> negative for equity
        if "inflation" in words:
            if any(w in text for w in ["rise", "surge", "higher", "spike", "hot", "sticky"]):
                bear_count += 2
            if any(w in text for w in ["cool", "ease", "lower", "drop", "softens"]):
                bull_count += 2

        if bull_count > bear_count:
            score = min(1.0, 0.2 + (bull_count - bear_count) * 0.15)
            return "BULLISH", round(score, 2)
        elif bear_count > bull_count:
            score = max(-1.0, -0.2 - (bear_count - bull_count) * 0.15)
            return "BEARISH", round(score, 2)
        else:
            return "NEUTRAL", 0.0

    @classmethod
    def evaluate(cls, title: str, content: str = "", category: str = "Macro Economy", severity: EventSeverity = EventSeverity.LOW) -> MarketImpact:
        """
        Builds the immutable MarketImpact object by scanning textual content and mapping affected entities.
        """
        combined_text = f"{title} {content}".lower()
        direction, score = cls._evaluate_sentiment(combined_text)

        # Time horizon selection
        if category in {"Central Bank", "GDP", "Geopolitics"} or severity in {EventSeverity.CRITICAL, EventSeverity.HIGH}:
            time_horizon = "WEEKLY"
        elif category in {"Inflation", "Corporate Earnings"}:
            time_horizon = "DAILY"
        else:
            time_horizon = "INTRADAY"

        # Affected Indices
        affected_indices: List[AffectedIndex] = []
        for index_name, kw_list in cls.INDICES_KEYWORDS.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in kw_list):
                affected_indices.append(
                    AffectedIndex(
                        index_name=index_name,
                        impact_direction=direction,
                        impact_score=score,
                    )
                )

        # Affected Sectors
        affected_sectors: List[AffectedSector] = []
        for sector_name, kw_list in cls.SECTORS_KEYWORDS.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in kw_list):
                affected_sectors.append(
                    AffectedSector(
                        sector_name=sector_name,
                        impact_direction=direction,
                        impact_score=score,
                    )
                )

        # Affected Markets
        affected_markets: List[AffectedMarket] = []
        for market_name, kw_list in cls.MARKETS_KEYWORDS.items():
            if any(re.search(r'\b' + re.escape(kw) + r'\b', combined_text) for kw in kw_list):
                affected_markets.append(
                    AffectedMarket(
                        market_name=market_name,
                        impact_direction=direction,
                        impact_score=score,
                    )
                )

        # Default fallback to India/Nifty 50 if empty
        if not affected_markets:
            affected_markets.append(AffectedMarket(market_name="INDIA", impact_direction=direction, impact_score=score))
        if not affected_indices:
            affected_indices.append(AffectedIndex(index_name="Nifty 50", impact_direction=direction, impact_score=score))

        # Description construction
        desc = (
            f"Expected {direction} ({score:+.2f}) impact over {time_horizon} horizon. "
            f"Primary sectors: {', '.join(s.sector_name for s in affected_sectors) if affected_sectors else 'General Market'}."
        )

        return MarketImpact(
            expected_direction=direction,
            time_horizon=time_horizon,
            market_impact_description=desc,
            impact_score=score,
            affected_indices=affected_indices,
            affected_sectors=affected_sectors,
            affected_markets=affected_markets,
        )
