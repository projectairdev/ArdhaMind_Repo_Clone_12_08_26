from __future__ import annotations

from src.news_engine.sentiment import (
    aggregate_market_news,
    score_market_headline,
    sentiment_from_score,
)
from src.news_engine.provider_manager import (
    BaseNewsProvider,
    GoogleNewsProvider,
    MacroCalendarProvider,
    ProviderManager,
)
from src.news_engine.normalizer import NewsNormalizer
from src.news_engine.deduplicator import NewsDeduplicator
from src.news_engine.entity_extractor import EntityExtractor
from src.news_engine.event_classifier import EventClassifier
from src.news_engine.severity import SeverityEvaluator
from src.news_engine.impact import MarketImpactEvaluator
from src.news_engine.time_decay import TimeDecayCalculator
from src.news_engine.summary_builder import NewsSummaryBuilder
from src.news_engine.builder import NewsContextBuilder
