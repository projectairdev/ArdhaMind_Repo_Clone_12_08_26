from __future__ import annotations

import re
from typing import List, Set

class EntityExtractor:
    """
    Stateless entity recognition engine.
    Scans text for financial entities including Companies, Countries, Indices,
    Currencies, Commodities, Central Banks, and Economic Indicators.
    """

    COMPANIES = {
        "reliance": "Reliance Industries",
        "ril": "Reliance Industries",
        "tata": "Tata Group",
        "tcs": "TCS",
        "infosys": "Infosys",
        "infy": "Infosys",
        "hdfc": "HDFC Bank",
        "icici": "ICICI Bank",
        "reliance retail": "Reliance Retail",
        "reliance jio": "Jio",
        "apple": "Apple Inc.",
        "microsoft": "Microsoft Corp",
    }

    COUNTRIES = {
        "india": "India",
        "indian": "India",
        "us": "USA",
        "usa": "USA",
        "united states": "USA",
        "china": "China",
        "chinese": "China",
        "iran": "Iran",
        "russia": "Russia",
        "german": "Germany",
        "germany": "Germany",
        "uk": "United Kingdom",
        "japan": "Japan",
    }

    INDICES = {
        "nifty": "Nifty 50",
        "nifty 50": "Nifty 50",
        "sensex": "Sensex",
        "bank nifty": "Bank Nifty",
        "banknifty": "Bank Nifty",
        "nasdaq": "Nasdaq",
        "dow jones": "Dow Jones",
        "s&p 500": "S&P 500",
        "nifty energy": "Nifty Energy",
    }

    CURRENCIES = {
        "inr": "INR",
        "rupee": "INR",
        "rupees": "INR",
        "usd": "USD",
        "dollar": "USD",
        "dollars": "USD",
        "eur": "EUR",
        "euro": "EUR",
        "gbp": "GBP",
        "pound": "GBP",
    }

    COMMODITIES = {
        "crude": "Crude Oil",
        "oil": "Crude Oil",
        "brent": "Brent Crude",
        "wti": "WTI Crude",
        "gold": "Gold",
        "silver": "Silver",
        "gas": "Natural Gas",
    }

    CENTRAL_BANKS = {
        "rbi": "Reserve Bank of India",
        "reserve bank of india": "Reserve Bank of India",
        "fed": "Federal Reserve",
        "federal reserve": "Federal Reserve",
        "fomc": "Federal Reserve",
        "ecb": "European Central Bank",
    }

    ECONOMIC_INDICATORS = {
        "cpi": "CPI Inflation",
        "inflation": "Inflation",
        "gdp": "GDP Growth",
        "pmi": "PMI Index",
        "iip": "Industrial Production",
        "unemployment": "Unemployment Rate",
        "interest rate": "Interest Rates",
        "repo rate": "Repo Rate",
    }

    @classmethod
    def extract_entities(cls, text: str) -> List[str]:
        """
        Scans title and content to identify unique mapped entities.
        """
        if not text:
            return []

        found: Set[str] = set()
        cleaned = re.sub(r"[^a-zA-Z0-9&\s]", " ", text).lower()
        words = set(cleaned.split())

        # Substring/word matching for multi-word or exact-word expressions
        def check_presence(pattern_dict, category):
            for pattern, mapped_val in pattern_dict.items():
                # Word-boundary matching
                if re.search(r'\b' + re.escape(pattern) + r'\b', cleaned):
                    found.add(f"{mapped_val} ({category})")

        check_presence(cls.COMPANIES, "Company")
        check_presence(cls.COUNTRIES, "Country")
        check_presence(cls.INDICES, "Index")
        check_presence(cls.CURRENCIES, "Currency")
        check_presence(cls.COMMODITIES, "Commodity")
        check_presence(cls.CENTRAL_BANKS, "Central Bank")
        check_presence(cls.ECONOMIC_INDICATORS, "Economic Indicator")

        return sorted(list(found))
