from __future__ import annotations

from typing import List, Optional
from src.models import NewsContextV2
from src.news_engine import (
    BaseNewsProvider,
    GoogleNewsProvider,
    MacroCalendarProvider,
    ProviderManager,
    NewsContextBuilder,
)
from src.utils import setup_logger, now_str

logger = setup_logger("NewsPipeline")

class NewsPipeline:
    """
    Stateless, modular pipeline that orchestrates the ingestion and processing
    of financial news and macroeconomic events to produce an immutable NewsContextV2.
    """

    def __init__(self, providers: Optional[List[BaseNewsProvider]] = None) -> None:
        # Default to standard GoogleNews and MacroCalendar providers
        self.providers = providers if providers is not None else [
            GoogleNewsProvider(),
            MacroCalendarProvider(),
        ]

    def run(self, current_time: Optional[str] = None) -> NewsContextV2:
        logger.info("Initializing News Intelligence Evaluation Pipeline...")
        
        # Ingestion
        logger.info(f"Ingesting raw headlines and macro events from {len(self.providers)} providers...")
        raw_data = ProviderManager.fetch_all(self.providers)
        
        # Flatten all raw articles from various providers
        raw_articles = []
        raw_events = []
        for name, items in raw_data.items():
            if "Calendar" in name:
                raw_events.extend(items)
            else:
                raw_articles.extend(items)

        logger.info(f"Ingested {len(raw_articles)} raw articles and {len(raw_events)} raw scheduled events.")

        # Orchestrate context building
        scanned_at = current_time or now_str()
        news_context = NewsContextBuilder.build_context(
            raw_articles=raw_articles,
            raw_events=raw_events,
            current_time=scanned_at,
        )

        logger.info(
            f"News Intelligence Context built successfully: "
            f"Articles={news_context.statistics.total_articles}, "
            f"Upcoming Events={len(news_context.upcoming_events)}, "
            f"Critical Alerts={len(news_context.critical_alerts)}, "
            f"Sentiment Score={news_context.statistics.sentiment_score:+.2f}"
        )
        return news_context
