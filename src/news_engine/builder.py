from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.news_context_v2 import (
    NewsContext as NewsContextV2,
    NewsArticle,
    NewsEvent,
    EventSeverity,
    NewsStatistics,
    NewsSummary,
)
from src.news_engine.normalizer import NewsNormalizer
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.entity_extractor import EntityExtractor
from src.news_engine.event_classifier import EventClassifier
from src.news_engine.severity import SeverityEvaluator
from src.news_engine.impact import MarketImpactEvaluator
from src.news_engine.time_decay import TimeDecayCalculator
from src.news_engine.summary_builder import NewsSummaryBuilder
from src.utils import now_str

class NewsContextBuilder:
    """
    Stateless main builder orchestrating the entire News Intelligence pipeline to output an immutable NewsContext.
    """

    @classmethod
    def build_context(
        cls,
        raw_articles: List[Dict[str, Any]],
        raw_events: List[Dict[str, Any]],
        current_time: Optional[str] = None,
    ) -> NewsContextV2:
        """
        Runs full processing on raw articles and macro calendar events to build the final NewsContext report.
        """
        scanned_at = current_time or now_str()

        # Step 1: Normalize & Deduplicate Articles
        normalized_articles = [NewsNormalizer.normalize_google_article(art) for art in raw_articles]
        unique_raw_articles = NewsDeduplicator.deduplicate(normalized_articles)

        # Step 2: Enrich Articles (Entities, Classification, Severity, Impact, Decay)
        articles: List[NewsArticle] = []
        severity_dist: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        class_dist: Dict[str, int] = {}
        total_sentiment = 0.0

        for r_art in unique_raw_articles:
            title = r_art["title"]
            content = r_art["content"]

            # Extraction & Classification
            entities = EntityExtractor.extract_entities(f"{title} {content}")
            category = EventClassifier.classify(title, content)
            severity = SeverityEvaluator.evaluate(title, content, category=category)
            
            # Market Impact
            impact = MarketImpactEvaluator.evaluate(title, content, category=category, severity=severity)
            
            # Decay factor adjustment on impact score
            decay_multiplier = TimeDecayCalculator.calculate_multiplier(r_art["published_at"], current_time=scanned_at)
            decayed_score = round(impact.impact_score * decay_multiplier, 2)
            
            # Build the article
            news_art = NewsArticle(
                article_id=r_art["article_id"],
                title=title,
                content=content,
                source=r_art["source"],
                published_at=r_art["published_at"],
                url=r_art["url"],
                entities=entities,
                classification=category,
                severity=severity,
                impact=impact,
                confidence_score=decay_multiplier,  # map confidence to decay multiplier
            )
            articles.append(news_art)

            # Record stats
            severity_dist[severity.value] = severity_dist.get(severity.value, 0) + 1
            class_dist[category] = class_dist.get(category, 0) + 1
            total_sentiment += decayed_score

        # Step 3: Normalize and process Calendar Events
        events: List[NewsEvent] = []
        for r_ev in raw_events:
            norm_ev = NewsNormalizer.normalize_macro_event(r_ev)
            title = norm_ev["title"]
            description = norm_ev["description"]
            
            # Enrich calendar events
            category = norm_ev["event_type"]
            importance = r_ev.get("importance") or "MEDIUM"
            severity = SeverityEvaluator.evaluate(title, description, category=category, source_importance=importance)
            impact = MarketImpactEvaluator.evaluate(title, description, category=category, severity=severity)

            # Determine Status (CURRENT, UPCOMING, OVERNIGHT) based on target date vs scanned_at
            status = r_ev.get("status")
            if not status:
                try:
                    target_dt = TimeDecayCalculator.parse_time(norm_ev["scheduled_time"])
                    now_dt = TimeDecayCalculator.parse_time(scanned_at)
                    delta_hours = (target_dt - now_dt).total_seconds() / 3600.0
                    if delta_hours < 0:
                        # Event happened in past
                        if abs(delta_hours) <= 12.0:
                            status = "OVERNIGHT"
                        else:
                            status = "CURRENT"
                    else:
                        status = "UPCOMING"
                except Exception:
                    status = "CURRENT"

            news_ev = NewsEvent(
                event_id=norm_ev["event_id"],
                title=title,
                description=description,
                event_type=category,
                severity=severity,
                status=status,
                scheduled_time=norm_ev["scheduled_time"],
                impact=impact,
                sources=norm_ev["sources"],
            )
            events.append(news_ev)

        # Step 4: Group Events by Status
        current_events: List[NewsEvent] = []
        upcoming_events: List[NewsEvent] = []
        overnight_events: List[NewsEvent] = []
        critical_alerts: List[NewsEvent] = []

        for ev in events:
            if ev.severity == EventSeverity.CRITICAL:
                critical_alerts.append(ev)
            
            if ev.status == "UPCOMING":
                upcoming_events.append(ev)
            elif ev.status == "OVERNIGHT":
                overnight_events.append(ev)
            else:
                current_events.append(ev)

        # Step 5: Synthesize Summary
        summary = NewsSummaryBuilder.build(articles, events)

        # Step 6: Statistics
        avg_sentiment = round(total_sentiment / len(articles), 2) if articles else 0.0
        stats = NewsStatistics(
            total_articles=len(articles),
            severity_distribution=severity_dist,
            classification_distribution=class_dist,
            sentiment_score=avg_sentiment,
        )

        return NewsContextV2(
            scanned_at=scanned_at,
            current_events=current_events,
            upcoming_events=upcoming_events,
            critical_alerts=critical_alerts,
            overnight_events=overnight_events,
            market_summary=summary,
            statistics=stats,
            articles=articles,
        )
