# src/news_engine/event_classifier.py
"""
Stateless classification engine assigning news/calendar categories based on canonical taxonomy.
"""
from __future__ import annotations

import re
from typing import Dict, Set, List


class EventClassifier:
    """
    Canonical News Taxonomy classifier for AIR ArdhaMind.
    Maps news items to deterministic primary categories without broad keyword false positives.
    """

    CLASSIFIER_RULES: Dict[str, Set[str]] = {
        "RBI_MONETARY": {
            "rbi", "reserve bank of india", "shaktikanta", "monetary policy committee",
            "repo rate", "reverse repo", "vrr auction", "lafs", "statutory liquidity ratio", "crr"
        },
        "SEBI_REGULATION": {
            "sebi", "sebi circular", "sebi norms", "insider trading", "mutual fund rules",
            "listing norms", "derivative risk disclosure", "algo trading norms"
        },
        "GOVERNMENT_POLICY": {
            "union budget", "finance ministry", "pib india", "gst collection", "capital gains tax",
            "customs duty", "plis scheme", "cabinet decision"
        },
        "INDIA_MACRO": {
            "india cpi", "india wpi", "india gdp", "mospi", "iip growth", "core sector",
            "india trade balance", "forex reserves india", "fiscal deficit india"
        },
        "FED_MONETARY": {
            "fed", "fomc", "powell", "federal reserve", "fed rate", "fomc minutes", "dot plot"
        },
        "US_MACRO": {
            "us cpi", "us ppi", "us nonfarm payrolls", "us jobless claims", "us gdp",
            "us retail sales", "us pce inflation"
        },
        "GLOBAL_MARKETS": {
            "wall street", "nasdaq", "dow jones", "s&p 500", "nikkei", "hang seng", "dax", "ftse"
        },
        "GEOPOLITICS": {
            "strait of hormuz", "opec+", "middle east tension", "sanctions", "trade war", "missile strike"
        },
        "COMMODITIES": {
            "brent crude", "wti crude", "crude oil", "gold prices", "silver prices", "lme copper"
        },
        "FX_RATES": {
            "usd inr", "dollar index", "rupee depreciation", "dxy", "forex intervention"
        },
        "BANKING_FINANCIALS": {
            "bank nifty", "hdfc bank", "icici bank", "sbi", "axis bank", "kotak bank",
            "npa", "net interest margin", "asset quality"
        },
        "IT_TECH": {
            "nifty it", "tcs", "infosys", "wipro", "hcltech", "tech mahindra", "us tech spending"
        },
        "AUTO": {
            "nifty auto", "tata motors", "maruti", "mahindra", "bajaj auto", "auto sales"
        },
        "ENERGY": {
            "reliance industries", "ongc", "bpcl", "ioc", "ntpc", "power grid", "refining margin"
        },
        "METALS": {
            "nifty metal", "tata steel", "jsw steel", "hindalco", "coal india", "iron ore"
        },
        "PHARMA": {
            "nifty pharma", "sun pharma", "dr reddy", "cipla", "usfda approval"
        },
        "FMCG": {
            "nifty fmcg", "hindustan unilever", "itc", "nestle", "volume growth"
        },
        "INFRA": {
            "larsen toubro", "infra order", "highway construction", "capital goods"
        },
        "REALTY": {
            "nifty realty", "dlf", "macrotech", "godrej properties", "housing sales"
        },
    }

    @classmethod
    def classify(cls, title: str, content: str = "") -> str:
        """
        Returns primary category from canonical taxonomy, defaulting to "OTHER_RELEVANT".
        """
        text = f"{title} {content}".lower()
        cleaned_text = re.sub(r"[^a-z0-9\s/]", " ", text)

        scores: Dict[str, int] = {}
        for category, keywords in cls.CLASSIFIER_RULES.items():
            score = 0
            for kw in keywords:
                pattern = r'\b' + re.escape(kw) + r'\b'
                matches = re.findall(pattern, cleaned_text)
                score += len(matches) * (3 if len(kw) > 5 else 1)
            if score > 0:
                scores[category] = score

        if not scores:
            return "OTHER_RELEVANT"

        sorted_cats = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return sorted_cats[0][0]
