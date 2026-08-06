from __future__ import annotations

from typing import Any, Dict, Optional
from src.models import NewsContextV2

class NewsIntelligencePanel:
    """
    Dashboard Panel presenting processed news analytics, critical alerts,
    upcoming macroeconomic calendar events, and sentiment distribution.
    """

    def __init__(self, news_context: Optional[NewsContextV2] = None) -> None:
        self.news_context = news_context

    def to_dict(self) -> Dict[str, Any]:
        """
        Structured representation of news intelligence metrics.
        """
        if not self.news_context:
            return {}

        nc = self.news_context
        stats = nc.statistics
        sumry = nc.market_summary

        # Calculate sentiment bias and panic triggers
        sentiment = stats.sentiment_score
        bias = "BULLISH" if sentiment >= 0.15 else "BEARISH" if sentiment <= -0.15 else "NEUTRAL"
        is_panic = sentiment <= -0.4

        return {
            "scanned_at": nc.scanned_at,
            "overall_sentiment": sentiment,
            "sentiment_bias": bias,
            "is_news_panic_active": is_panic,
            "timestamp": nc.scanned_at,
            "statistics": {
                "total_articles": stats.total_articles,
                "sentiment_score": stats.sentiment_score,
                "severity_distribution": stats.severity_distribution,
                "classification_distribution": stats.classification_distribution,
            },
            "summary": {
                "market_summary": sumry.market_summary,
                "key_takeaways": sumry.key_takeaways,
                "critical_alerts": sumry.critical_alerts,
            },
            "critical_events": [
                {
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "description": ev.description,
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                    "direction": ev.impact.expected_direction if ev.impact else "NEUTRAL",
                    "impact_score": ev.impact.impact_score if ev.impact else 0.0,
                }
                for ev in nc.critical_alerts
            ],
            "upcoming_events": [
                {
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "description": ev.description,
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                    "direction": ev.impact.expected_direction if ev.impact else "NEUTRAL",
                    "impact_score": ev.impact.impact_score if ev.impact else 0.0,
                }
                for ev in nc.upcoming_events
            ],
            "current_events": [
                {
                    "event_id": ev.event_id,
                    "title": ev.title,
                    "description": ev.description,
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                }
                for ev in nc.current_events
            ],
            "articles": [
                {
                    "article_id": art.article_id,
                    "title": art.title,
                    "headline": art.title,
                    "summary": art.content,
                    "source": art.source,
                    "published_at": art.published_at,
                    "entities": art.entities,
                    "classification": art.classification,
                    "severity": art.severity.value,
                    "expected_direction": art.impact.expected_direction if art.impact else "NEUTRAL",
                    "sentiment_score": art.impact.impact_score if art.impact else 0.0,
                    "impact_score": art.impact.impact_score if art.impact else 0.0,
                    "decay_multiplier": art.confidence_score,
                }
                for art in nc.articles
            ]
        }

    def render_cli(self) -> str:
        """
        Renders a beautifully formatted ASCII text card for terminal workstations.
        """
        if not self.news_context:
            return (
                "+- NEWS INTELLIGENCE PANEL ----------------------------------------------------+\n"
                "| No processed news context report available.                                  |\n"
                "+------------------------------------------------------------------------------+"
            )

        data = self.to_dict()
        stats = data["statistics"]
        summary = data["summary"]

        lines = []
        lines.append("+- NEWS INTELLIGENCE CONTEXT --------------------------------------------------+")
        lines.append(f"| SCANNED AT: {data['scanned_at']:<20} | SENTIMENT SCORE: {stats['sentiment_score']:+5.2f} (Articles: {stats['total_articles']:<2}) |")
        lines.append("|" + "-" * 78 + "|")
        
        # Severity Distribution
        sev = stats["severity_distribution"]
        lines.append(
            f"| Severity: CRITICAL: {sev.get('CRITICAL', 0):<2} | HIGH: {sev.get('HIGH', 0):<2} | MEDIUM: {sev.get('MEDIUM', 0):<2} | LOW: {sev.get('LOW', 0):<2}                       |"
        )
        lines.append("|" + "-" * 78 + "|")

        # Market Summary Paragraph (wrapped beautifully)
        raw_msg = summary["market_summary"]
        words = raw_msg.split()
        curr_line = []
        for word in words:
            if sum(len(w) for w in curr_line) + len(curr_line) + len(word) > 74:
                lines.append(f"| {' '.join(curr_line):<76} |")
                curr_line = [word]
            else:
                curr_line.append(word)
        if curr_line:
            lines.append(f"| {' '.join(curr_line):<76} |")

        # Key Takeaways
        if summary["key_takeaways"]:
            lines.append("|" + "-" * 78 + "|")
            lines.append("| KEY MARKET TAKEAWAYS:                                                        |")
            for tk in summary["key_takeaways"][:3]:
                # truncate if too long
                trunc = tk[:70] + "..." if len(tk) > 70 else tk
                lines.append(f"|   * {trunc:<72} |")

        # Critical Alerts Section
        if data["critical_events"]:
            lines.append("|" + "-" * 78 + "|")
            lines.append("| CRITICAL ALERTS:                                                             |")
            for ev in data["critical_events"][:3]:
                lines.append(
                    f"|   [CRITICAL] {ev['title'][:45]:<45} | Dir: {ev['direction']:<8} ({ev['impact_score']:+4.1f}) |"
                )

        # Upcoming Economic Calendar Events Section
        if data["upcoming_events"]:
            lines.append("|" + "-" * 78 + "|")
            lines.append("| UPCOMING MACROECONOMIC EVENTS:                                               |")
            for ev in data["upcoming_events"][:4]:
                lines.append(
                    f"|   * {ev['title'][:32]:<32} | {ev['event_type']:<15} | Scheduled: {ev['scheduled_time'][:16]:<16} |"
                )

        # Articles breakdown
        if data["articles"]:
            lines.append("|" + "-" * 78 + "|")
            lines.append("| RECENT ARTICLES:                                                             |")
            for art in data["articles"][:5]:
                entities_str = ", ".join(art["entities"][:2])
                lines.append(
                    f"|   * {art['title'][:40]:<40} | Src: {art['source'][:12]:<12} | Dir: {art['expected_direction']:<8} |"
                )

        lines.append("+------------------------------------------------------------------------------+")
        return "\n".join(lines)
