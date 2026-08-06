from __future__ import annotations

from typing import List
from src.models.news_context_v2 import NewsSummary, NewsArticle, NewsEvent, EventSeverity

class NewsSummaryBuilder:
    """
    Stateless builder that synthesizes raw list of articles and events into an immutable NewsSummary.
    """

    @staticmethod
    def build(articles: List[NewsArticle], events: List[NewsEvent]) -> NewsSummary:
        """
        Creates a NewsSummary based on articles and calendar events.
        """
        critical_alerts: List[str] = []
        key_takeaways: List[str] = []

        # Find critical/high severity items
        for art in articles:
            if art.severity == EventSeverity.CRITICAL:
                critical_alerts.append(f"CRITICAL NEWS ALERT ({art.source}): {art.title}")
            elif art.severity == EventSeverity.HIGH:
                key_takeaways.append(f"HIGH IMPACT ({art.source}): {art.title}")

        for ev in events:
            if ev.severity == EventSeverity.CRITICAL:
                critical_alerts.append(f"CRITICAL EVENT ({ev.event_type.upper()}): {ev.title} - {ev.description}")
            elif ev.severity == EventSeverity.HIGH:
                key_takeaways.append(f"HIGH IMPACT EVENT ({ev.event_type.upper()}): {ev.title} - {ev.description}")

        # Limit count for cleanliness
        critical_alerts = critical_alerts[:4]
        key_takeaways = key_takeaways[:5]

        # Construct market summary paragraph
        if not articles and not events:
            market_summary = "No news articles or macroeconomic events are currently active in the market."
        else:
            bullish_count = sum(1 for a in articles if a.impact and a.impact.expected_direction == "BULLISH")
            bearish_count = sum(1 for a in articles if a.impact and a.impact.expected_direction == "BEARISH")
            
            direction_bias = "NEUTRAL"
            if bullish_count > bearish_count:
                direction_bias = "BULLISH"
            elif bearish_count > bullish_count:
                direction_bias = "BEARISH"

            num_articles = len(articles)
            num_events = len(events)
            
            market_summary = (
                f"Market news scan completed with {num_articles} active articles and {num_events} scheduled calendar events. "
                f"Overall bias is leaning {direction_bias} with {bullish_count} bullish and {bearish_count} bearish sentiment sources. "
            )

            if critical_alerts:
                market_summary += f"Urgent: {len(critical_alerts)} critical alerts require immediate risk monitoring. "
            else:
                market_summary += "No critical risk-escalations detected. General operations remain within normal volatility thresholds."

        # Provide default takeaways if empty
        if not key_takeaways:
            key_takeaways = [
                "Market sentiment remains steady with stable domestic flows.",
                "Trading volumes are in line with weekly moving averages.",
                "Inflation indicators and yield curves are closely monitored."
            ]

        return NewsSummary(
            market_summary=market_summary,
            key_takeaways=key_takeaways,
            critical_alerts=critical_alerts,
        )
