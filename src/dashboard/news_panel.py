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
        if hasattr(nc, "payload"):
            payload = nc.payload
            items_list = nc.items
        else:
            payload = {
                "section_status": "ready" if nc.usable else "unavailable",
                "items": [],
                "top_headlines": [],
                "high_impact_items": [],
                "corporate_items": [],
                "event_items": [],
                "provider_health": getattr(nc, "provider_health", {}),
                "freshness": "unavailable",
                "warnings": [],
                "errors": [],
                "generated_at": nc.scanned_at,
            }
            # Map legacy articles to items
            items_list = []
            for art in getattr(nc, "articles", []):
                # Fake matching item fields
                class NewsItemCompat:
                    def __init__(self, a):
                        self.id = a.article_id
                        self.headline = a.title
                        self.summary_snippet = a.content
                        self.source_name = a.source
                        self.published_at = a.published_at
                        self.affected_symbols = a.entities
                        self.affected_sectors = []
                        self.category = a.classification
                        self.impact_strength = a.severity.value.lower()
                        self.expected_direction = a.impact.expected_direction.lower() if a.impact else "uncertain"
                        self.nifty_relevance_score = a.impact.impact_score if a.impact else 1.0
                        self.confidence = a.confidence_score
                items_list.append(NewsItemCompat(art))

        total_articles = len(items_list)
        severity_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        classification_distribution: Dict[str, int] = {}
        total_sentiment = 0.0

        for item in items_list:
            classification_distribution[item.category] = classification_distribution.get(item.category, 0) + 1
            if item.impact_strength == "high":
                severity_distribution["HIGH"] += 1
            elif item.impact_strength == "medium":
                severity_distribution["MEDIUM"] += 1
            else:
                severity_distribution["LOW"] += 1

            val = 1 if item.expected_direction == "positive" else -1 if item.expected_direction == "negative" else 0
            total_sentiment += item.nifty_relevance_score * val

        sentiment_score = round(total_sentiment / total_articles, 2) if total_articles else 0.0
        bias = "BULLISH" if sentiment_score >= 0.15 else "BEARISH" if sentiment_score <= -0.15 else "NEUTRAL"
        is_panic = sentiment_score <= -0.4

        from src.news_engine.normalizer import clean_html_text

        # Sanitize all items in payload if present
        if isinstance(payload.get("items"), list):
            for it in payload["items"]:
                if isinstance(it, dict):
                    it["headline"] = clean_html_text(it.get("headline", ""), max_length=200)
                    it["summary_snippet"] = clean_html_text(it.get("summary_snippet", ""), max_length=500)
                    if "summary" in it:
                        it["summary"] = clean_html_text(it.get("summary", ""), max_length=500)
                    if "description" in it:
                        it["description"] = clean_html_text(it.get("description", ""), max_length=500)

        legacy = {
            "scanned_at": nc.scanned_at,
            "overall_sentiment": sentiment_score,
            "sentiment_bias": bias,
            "is_news_panic_active": is_panic,
            "timestamp": nc.scanned_at,
            "statistics": {
                "total_articles": total_articles,
                "sentiment_score": sentiment_score,
                "severity_distribution": severity_distribution,
                "classification_distribution": classification_distribution,
            },
            "summary": {
                "market_summary": clean_html_text(nc.market_summary.market_summary if hasattr(nc, "market_summary") else "Unified financial news and macroeconomic calendar updates.", max_length=500),
                "key_takeaways": nc.market_summary.key_takeaways if hasattr(nc, "market_summary") else [],
                "critical_alerts": nc.market_summary.critical_alerts if hasattr(nc, "market_summary") else [],
            },
            "critical_events": [
                {
                    "event_id": ev.event_id,
                    "title": clean_html_text(ev.title, max_length=200),
                    "description": clean_html_text(ev.description, max_length=500),
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                    "direction": ev.impact.expected_direction if ev.impact else "NEUTRAL",
                    "impact_score": ev.impact.impact_score if ev.impact else 0.0,
                }
                for ev in getattr(nc, "critical_alerts", [])
            ],
            "upcoming_events": [
                {
                    "event_id": ev.event_id,
                    "title": clean_html_text(ev.title, max_length=200),
                    "description": clean_html_text(ev.description, max_length=500),
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                    "direction": ev.impact.expected_direction if ev.impact else "NEUTRAL",
                    "impact_score": ev.impact.impact_score if ev.impact else 0.0,
                }
                for ev in getattr(nc, "upcoming_events", [])
            ],
            "current_events": [
                {
                    "event_id": ev.event_id,
                    "title": clean_html_text(ev.title, max_length=200),
                    "description": clean_html_text(ev.description, max_length=500),
                    "event_type": ev.event_type,
                    "severity": ev.severity.value,
                    "scheduled_time": ev.scheduled_time,
                }
                for ev in getattr(nc, "current_events", [])
            ],
            "articles": [
                {
                    "article_id": item.id,
                    "title": clean_html_text(item.headline, max_length=200),
                    "headline": clean_html_text(item.headline, max_length=200),
                    "summary": clean_html_text(item.summary_snippet, max_length=500),
                    "source": clean_html_text(item.source_name, max_length=100),
                    "published_at": item.published_at,
                    "entities": item.affected_symbols + item.affected_sectors,
                    "classification": item.category,
                    "severity": "HIGH" if item.impact_strength == "high" else "MEDIUM" if item.impact_strength == "medium" else "LOW",
                    "expected_direction": item.expected_direction.upper(),
                    "sentiment_score": item.nifty_relevance_score,
                    "impact_score": item.nifty_relevance_score,
                    "decay_multiplier": item.confidence,
                }
                for item in items_list
            ]
        }
        return {**payload, **legacy}

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
