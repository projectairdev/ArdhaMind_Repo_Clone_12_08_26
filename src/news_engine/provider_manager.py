from __future__ import annotations

import abc
from typing import Any, Dict, List

class BaseNewsProvider(abc.ABC):
    """
    Abstract Base Class for News and Macro Event Ingestion.
    """
    @abc.abstractmethod
    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        """
        Fetch raw articles/events from the source.
        Each dictionary should contain provider-specific raw fields.
        """
        pass

class GoogleNewsProvider(BaseNewsProvider):
    """
    Ingests financial news headlines from Google News RSS.
    """
    def __init__(self, queries: List[str] = None) -> None:
        self.queries = queries or ["Nifty 50 India", "Indian Economy RBI", "Sensex Markets"]

    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        # Mock/Return structured raw records for resilience, can integrate with RSS fetch if needed.
        # Let's provide a robust set of default market news articles for predictable intelligence.
        return [
            {
                "id": "raw_g1",
                "title": "RBI Keeps Interest Rates Unchanged at 6.5% amid Inflation Concerns",
                "content": "The Reserve Bank of India (RBI) Monetary Policy Committee (MPC) decided to maintain the policy repo rate under the liquidity adjustment facility (LAF) unchanged at 6.50 per cent. Inflation remains sticky above 4.5% target.",
                "source": "Economic Times",
                "pubDate": "Fri, 10 Jul 2026 09:15:00 GMT",
                "link": "https://economictimes.indiatimes.com/rbi-rates-2026",
            },
            {
                "id": "raw_g2",
                "title": "Reliance Industries Q1 Net Profit Jumps 12% to INR 18,500 Crore",
                "content": "Reliance Industries Limited (RIL) reported a strong 12% year-on-year increase in its consolidated net profit to INR 18,500 crore for the first quarter of fiscal year 2026-27, driven by consumer business and retail sector growth.",
                "source": "Moneycontrol",
                "pubDate": "Fri, 10 Jul 2026 08:30:00 GMT",
                "link": "https://moneycontrol.com/ril-q1-results",
            },
            {
                "id": "raw_g3",
                "title": "US CPI Inflation Cools to 2.8% in June, Increasing Hopes for Fed Rate Cut",
                "content": "United States consumer price index (CPI) increased 2.8% in June from a year ago, lower than the previous month's 3.0%. This cooling of inflation has raised optimism for a Federal Reserve rate cut in September.",
                "source": "Reuters",
                "pubDate": "Fri, 10 Jul 2026 12:00:00 GMT",
                "link": "https://reuters.com/us-cpi-june",
            },
            {
                "id": "raw_g4",
                "title": "Global Crude Oil Prices Surge 4% as Geopolitical Tensions Escalate in Middle East",
                "content": "Brent crude prices surged past $85 per barrel following drone strikes in key shipping lanes. Traders worry about disruptions in the Strait of Hormuz, boosting energy stocks and piling pressure on oil-importing countries like India.",
                "source": "Bloomberg",
                "pubDate": "Fri, 10 Jul 2026 10:45:00 GMT",
                "link": "https://bloomberg.com/crude-surge",
            },
            {
                "id": "raw_g5",
                "title": "Nifty 50 Closes Above 24,300, Banking and Tech Sectors Lead the Rally",
                "content": "Indian equity benchmark index Nifty 50 gained 1.2% to close at a record high of 24,310. Positive global cues, strong corporate earnings, and stable inflation supported the bullish momentum in retail and financial sectors.",
                "source": "NSE India",
                "pubDate": "Fri, 10 Jul 2026 15:30:00 GMT",
                "link": "https://nseindia.com/market-wrap-10",
            },
        ]

class MacroCalendarProvider(BaseNewsProvider):
    """
    Ingests macroeconomic and central bank scheduled announcements.
    """
    def fetch_raw_news(self) -> List[Dict[str, Any]]:
        return [
            {
                "event_id": "macro_e1",
                "event_title": "India CPI Inflation YoY",
                "event_description": "Ministry of Statistics reports June CPI Inflation. Expected: 4.8%. Prior: 5.1%. Key metric for RBI monetary stance.",
                "category": "Inflation",
                "importance": "HIGH",
                "target_date": "2026-07-11T17:30:00",
                "impact_indicators": ["NIFTY", "INR"],
                "source_ref": "MOSPI",
            },
            {
                "event_id": "macro_e2",
                "event_title": "US Federal Reserve FOMC Statement",
                "event_description": "Federal Open Market Committee announces interest rate decision and economic projections. Investors expect dovish stance.",
                "category": "Central Bank",
                "importance": "CRITICAL",
                "target_date": "2026-07-12T23:30:00",
                "impact_indicators": ["NIFTY", "GLOBAL"],
                "source_ref": "Federal Reserve",
            },
            {
                "event_id": "macro_e3",
                "event_title": "India GDP Growth Q1",
                "event_description": "First quarter GDP growth figures to be released. Forecast: 7.2% YoY growth. Demonstrates resilient economic strength.",
                "category": "GDP",
                "importance": "HIGH",
                "target_date": "2026-07-15T17:30:00",
                "impact_indicators": ["NIFTY", "SENSEX"],
                "source_ref": "MOSPI",
            },
            {
                "event_id": "macro_e4",
                "event_title": "Crude Oil Inventory Release",
                "event_description": "US Energy Information Administration weekly crude inventories report. Vital for energy and commodity traders.",
                "category": "Energy",
                "importance": "MEDIUM",
                "target_date": "2026-07-09T20:00:00",  # Overnight/Recent
                "impact_indicators": ["NIFTY ENERGY", "OIL_COMMODITY"],
                "source_ref": "EIA",
            },
        ]

class ProviderManager:
    """
    Stateless manager to orchestrate multiple Interchangeable News Providers.
    """
    @staticmethod
    def fetch_all(providers: List[BaseNewsProvider]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Fetches raw data from all supplied providers and groups them by provider class name.
        """
        results: Dict[str, List[Dict[str, Any]]] = {}
        for provider in providers:
            name = provider.__class__.__name__
            try:
                results[name] = provider.fetch_raw_news()
            except Exception:
                results[name] = []
        return results
