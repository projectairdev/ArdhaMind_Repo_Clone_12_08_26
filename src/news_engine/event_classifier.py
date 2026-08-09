# src/news_engine/event_classifier.py
from __future__ import annotations

import re
from typing import Dict, Set


class EventClassifier:
    """
    Stateless classification engine assigning news/calendar categories based on keyword match density.
    """

    CLASSIFIER_RULES: Dict[str, Set[str]] = {
        "RBI": {
            "rbi", "reserve bank", "shaktikanta", "monetary policy", "repo rate", "rate cut", "rate hike", "lafs"
        },
        "SEBI": {
            "sebi", "capital market", "regulation", "insider trading", "mutual fund rules", "listing norms"
        },
        "Exchange Operations": {
            "nse", "bse", "stock exchange", "circuit limit", "trading halt", "exchange circular",
            "broker outage", "zerodha down", "kite downtime", "clearing corporation", "settlement cycle"
        },
        "Government Policy": {
            "government", "budget", "finance ministry", "pib", "gst", "capital gains tax", "tariff", "policy change"
        },
        "Macro": {
            "cpi", "wpi", "inflation", "gdp", "gva", "industrial production", "iip", "unemployment", "trade deficit"
        },
        "Global Markets": {
            "fed", "fomc", "wall street", "nasdaq", "dow jones", "s&p 500", "nikkei", "global market", "fii flow"
        },
        "Geopolitics": {
            "geopolitical", "war", "missile", "drone strike", "drone", "attack", "attacks", "conflict", "sanction", "tariffs", "escalation"
        },
        "Crude": {
            "crude", "oil", "brent", "wti", "gold", "silver", "commodity", "crude prices"
        },
        "Currency/Yields": {
            "rupee", "inr", "usd", "forex", "treasury yield", "bond yield", "sovereign bond"
        },
        "Earnings": {
            "earnings", "quarterly", "profit jumps", "profit falls", "net profit", "revenue", "q1", "q2", "q3", "q4"
        },
        "Corporate": {
            "dividend", "bonus share", "stock split", "merger", "acquisition", "board meeting", "buyback",
            "corporate filing", "exchange filing", "expansion", "new order", "reliance results", "tcs deal"
        }
    }

    @classmethod
    def classify(cls, title: str, content: str = "") -> str:
        """
        Returns the category with highest match density, defaulting to "Other".
        """
        text = f"{title} {content}".lower()
        text = re.sub(r"[^a-z0-9\s/]", " ", text)

        scores: Dict[str, int] = {}
        for category, keywords in cls.CLASSIFIER_RULES.items():
            score = 0
            for kw in keywords:
                matches = re.findall(r'\b' + re.escape(kw) + r'\b', text)
                score += len(matches)
            if score > 0:
                scores[category] = score

        if not scores:
            return "Other"

        sorted_cats = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return sorted_cats[0][0]
