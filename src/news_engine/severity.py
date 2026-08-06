from __future__ import annotations

import re
from typing import Dict, List, Set
from src.models.news_context_v2 import EventSeverity

class SeverityEvaluator:
    """
    Stateless severity evaluator mapping articles/events to standard severity bands:
    LOW, MEDIUM, HIGH, CRITICAL using keyword rules.
    """

    CRITICAL_KEYWORDS: Set[str] = {
        "war", "missile", "drone strike", "nuclear", "ceasefire", "crash", "black swan", "default", "rate hike",
        "rate cut", "interest rate decision", "fomc announcement", "rbi repo rate", "geopolitical crisis"
    }

    HIGH_KEYWORDS: Set[str] = {
        "inflation", "cpi YoY", "gdp growth", "gdp falls", "net profit jumps", "net profit falls", "surge",
        "spike", "tensions", "sanctions", "regulatory clampdown", "investigation", "sebi penalty", "fii selloff"
    }

    MEDIUM_KEYWORDS: Set[str] = {
        "q1 profit", "earnings", "forecast", "projection", "acquisition", "expansion", "crude oil", "brent",
        "unemployment", "pmi", "iip", "corporate results", "dividend"
    }

    @classmethod
    def evaluate(cls, title: str, content: str = "", category: str = "Macro Economy", source_importance: str = "MEDIUM") -> EventSeverity:
        """
        Determines the severity of the article/event based on keyword analysis.
        Allows setting high/critical bounds based on macroeconomic importance.
        """
        text = f"{title} {content}".lower()
        cleaned = re.sub(r"[^a-z0-9\s]", " ", text)

        # 1. Critical matches
        for kw in cls.CRITICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.CRITICAL

        # If provider/source specifically flagged as CRITICAL
        if source_importance == "CRITICAL":
            return EventSeverity.CRITICAL

        # 2. High matches
        for kw in cls.HIGH_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.HIGH

        if source_importance == "HIGH":
            return EventSeverity.HIGH

        # Category matches
        if category in {"Central Bank", "Geopolitics"}:
            return EventSeverity.HIGH

        # 3. Medium matches
        for kw in cls.MEDIUM_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.MEDIUM

        if source_importance == "MEDIUM":
            return EventSeverity.MEDIUM

        return EventSeverity.LOW
class SeverityEvaluator:
    """
    Stateless severity evaluator mapping articles/events to standard severity bands:
    LOW, MEDIUM, HIGH, CRITICAL using keyword rules.
    """

    CRITICAL_KEYWORDS: Set[str] = {
        "war", "missile", "drone strike", "nuclear", "ceasefire", "crash", "black swan", "default", "rate hike",
        "rate cut", "interest rate decision", "fomc announcement", "rbi repo rate", "geopolitical crisis"
    }

    HIGH_KEYWORDS: Set[str] = {
        "inflation", "cpi YoY", "gdp growth", "gdp falls", "net profit jumps", "net profit falls", "surge",
        "spike", "tensions", "sanctions", "regulatory clampdown", "investigation", "sebi penalty", "fii selloff"
    }

    MEDIUM_KEYWORDS: Set[str] = {
        "q1 profit", "earnings", "forecast", "projection", "acquisition", "expansion", "crude oil", "brent",
        "unemployment", "pmi", "iip", "corporate results", "dividend"
    }

    @classmethod
    def evaluate(cls, title: str, content: str = "", category: str = "Macro Economy", source_importance: str = "MEDIUM") -> EventSeverity:
        """
        Determines the severity of the article/event based on keyword analysis.
        Allows setting high/critical bounds based on macroeconomic importance.
        """
        text = f"{title} {content}".lower()
        cleaned = re.sub(r"[^a-z0-9\s]", " ", text)

        # 1. Critical matches
        for kw in cls.CRITICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.CRITICAL

        # If provider/source specifically flagged as CRITICAL
        if source_importance == "CRITICAL":
            return EventSeverity.CRITICAL

        # 2. High matches
        for kw in cls.HIGH_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.HIGH

        if source_importance == "HIGH":
            return EventSeverity.HIGH

        # Category matches
        if category in {"Central Bank", "Geopolitics"}:
            return EventSeverity.HIGH

        # 3. Medium matches
        for kw in cls.MEDIUM_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', cleaned) or kw in text:
                return EventSeverity.MEDIUM

        if source_importance == "MEDIUM":
            return EventSeverity.MEDIUM

        return EventSeverity.LOW
