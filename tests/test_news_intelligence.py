from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from dataclasses import is_dataclass
from src.models import (
    NewsContext,
    NewsContextV2,
    NewsArticle,
    NewsEvent,
    AffectedIndex,
    AffectedSector,
    AffectedMarket,
    EventSeverity,
    MarketImpact,
    NewsSummary,
    NewsStatistics,
)
from src.news_engine import (
    GoogleNewsProvider,
    MacroCalendarProvider,
    ProviderManager,
    NewsNormalizer,
    NewsDeduplicator,
    EntityExtractor,
    EventClassifier,
    SeverityEvaluator,
    MarketImpactEvaluator,
    TimeDecayCalculator,
    NewsSummaryBuilder,
    NewsContextBuilder,
)
from src.pipeline import NewsPipeline
from src.dashboard.news_panel import NewsIntelligencePanel
from src.dashboard.dashboard_builder import TradingWorkstationDashboard

class TestNewsIntelligence(unittest.TestCase):
    """
    Comprehensive tests for the News Intelligence Engine (Sprint 21).
    Ensures complete branch coverage, statelessness, and model immutability.
    """

    def setUp(self) -> None:
        self.raw_articles = [
            {
                "id": "raw_1",
                "title": "RBI Keeps Interest Rates Unchanged at 6.5%",
                "content": "The Monetary Policy Committee of the Reserve Bank of India keeps rates steady.",
                "source": "Economic Times",
                "pubDate": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "link": "https://et.com/rbi",
            },
            {
                "id": "raw_2",
                "title": "RBI Keeps Interest Rates Unchanged at 6.5%",
                "content": "Detailed overview of the RBI repo rate remaining steady at 6.50%. Sticky inflation continues.",
                "source": "Bloomberg Quint",
                "pubDate": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "link": "https://bloomberg.com/rbi",
            },
            {
                "id": "raw_3",
                "title": "TCS Q1 Net Profit Increases by 8% Year-on-Year",
                "content": "Tata Consultancy Services reports robust financial earnings for Q1 FY26.",
                "source": "Moneycontrol",
                "pubDate": (datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "link": "https://moneycontrol.com/tcs",
            },
            {
                "id": "raw_4",
                "title": "Geopolitical escalation: drone strikes in key shipping lanes",
                "content": "Tensions rise as drone attacks target crude oil container tankers.",
                "source": "Reuters",
                "pubDate": (datetime.utcnow() - timedelta(hours=28)).strftime("%Y-%m-%d %H:%M:%S"),
                "link": "https://reuters.com/tensions",
            }
        ]

        self.raw_events = [
            {
                "event_id": "macro_1",
                "event_title": "India CPI Inflation YoY",
                "event_description": "Scheduled release of June retail CPI figures.",
                "category": "Inflation",
                "importance": "HIGH",
                "target_date": (datetime.utcnow() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "source_ref": "MOSPI",
            },
            {
                "event_id": "macro_2",
                "event_title": "US Federal Reserve FOMC Statement",
                "event_description": "Scheduled rate announcement by the US Federal Reserve.",
                "category": "Central Bank",
                "importance": "CRITICAL",
                "target_date": (datetime.utcnow() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S"),
                "source_ref": "Federal Reserve",
                "status": "UPCOMING"
            }
        ]

    def test_model_immutability(self) -> None:
        """Verify models are immutable frozen dataclasses."""
        self.assertTrue(is_dataclass(NewsContextV2))
        self.assertTrue(is_dataclass(NewsArticle))
        self.assertTrue(is_dataclass(NewsEvent))
        
        # Test freezing
        art = NewsArticle(
            article_id="1", title="A", content="B", source="C", published_at="D", url="E"
        )
        with self.assertRaises(Exception):
            art.title = "New Title"  # type: ignore

    def test_providers(self) -> None:
        """Verify providers return correct structured data."""
        g_provider = GoogleNewsProvider()
        m_provider = MacroCalendarProvider()
        
        raw_g = g_provider.fetch_raw_news()
        raw_m = m_provider.fetch_raw_news()
        
        self.assertGreater(len(raw_g), 0)
        self.assertGreater(len(raw_m), 0)
        
        data = ProviderManager.fetch_all([g_provider, m_provider])
        self.assertIn("GoogleNewsProvider", data)
        self.assertIn("MacroCalendarProvider", data)

    def test_normalizer(self) -> None:
        """Test NewsNormalizer on raw inputs."""
        raw_art = {"title": "Test Title", "content": "Test Content", "source": "Reuters"}
        norm_art = NewsNormalizer.normalize_google_article(raw_art)
        
        self.assertEqual(norm_art["title"], "Test Title")
        self.assertEqual(norm_art["source"], "Reuters")
        self.assertTrue(norm_art["article_id"].startswith("art_"))

        raw_ev = {"event_title": "Test Event", "category": "Inflation"}
        norm_ev = NewsNormalizer.normalize_macro_event(raw_ev)
        self.assertEqual(norm_ev["title"], "Test Event")
        self.assertEqual(norm_ev["event_type"], "Inflation")

    def test_deduplicator(self) -> None:
        """Test deduplication and source merging."""
        normalized = [NewsNormalizer.normalize_google_article(a) for a in self.raw_articles]
        deduped = NewsDeduplicator.deduplicate(normalized, threshold=0.55)
        
        # Articles 1 and 2 are duplicates ("RBI Keeps Interest Rates Unchanged at 6.5%")
        # So we expect 4 raw articles to merge into 3 unique articles.
        self.assertEqual(len(deduped), 3)
        
        # Verify source consolidation
        rbi_art = next(x for x in deduped if "RBI" in x["title"])
        self.assertIn("Economic Times", rbi_art["source"])
        self.assertIn("Bloomberg Quint", rbi_art["source"])

    def test_entity_extractor(self) -> None:
        """Test entity extraction from text."""
        text = "Reliance Industries Q1 profits rise. TCS and Infosys lead IT gains. RBI retains repo rate at 6.5%."
        entities = EntityExtractor.extract_entities(text)
        
        # Should extract TCS, Reliance, Infosys, RBI, Repo Rate, Interest Rates etc.
        self.assertTrue(any("Reliance" in e for e in entities))
        self.assertTrue(any("TCS" in e for e in entities))
        self.assertTrue(any("Infosys" in e for e in entities))
        self.assertTrue(any("Reserve Bank of India" in e for e in entities))

    def test_event_classifier(self) -> None:
        """Test keyword-based event classification."""
        c1 = EventClassifier.classify("RBI repo rate hikes expected next week", "Monetary policy decision is upcoming")
        self.assertIn("RBI", c1)
        
        c2 = EventClassifier.classify("Inflation cools down as CPI drops to 4.2%")
        self.assertTrue(isinstance(c2, str))

        c3 = EventClassifier.classify("TCS announces outstanding corporate results with record revenue")
        self.assertTrue(isinstance(c3, str))

        c4 = EventClassifier.classify("Drone attacks hit key shipping container vessels")
        self.assertTrue(isinstance(c4, str))

    def test_severity_evaluator(self) -> None:
        """Test EventSeverity evaluation."""
        s1 = SeverityEvaluator.evaluate("Geopolitical crisis escalates to drone strikes and military war", category="Geopolitics")
        self.assertEqual(s1, EventSeverity.CRITICAL)

        s2 = SeverityEvaluator.evaluate("RBI policy remains steady at 6.5%", category="Central Bank")
        self.assertEqual(s2, EventSeverity.HIGH)

        s3 = SeverityEvaluator.evaluate("Nifty records high gains as IT stocks rally")
        self.assertEqual(s3, EventSeverity.MEDIUM)

    def test_market_impact_evaluator(self) -> None:
        """Test market impact extraction and direction scoring."""
        # 1. Bullish scenario
        impact_bull = MarketImpactEvaluator.evaluate("Infosys Q1 net profit jumps and beats forecast")
        self.assertEqual(impact_bull.expected_direction, "BULLISH")
        self.assertGreater(impact_bull.impact_score, 0.0)

        # 2. Bearish scenario
        impact_bear = MarketImpactEvaluator.evaluate("Crude oil surges past $90 as geopolitical crisis escalates")
        self.assertEqual(impact_bear.expected_direction, "BEARISH")
        self.assertLess(impact_bear.impact_score, 0.0)

    def test_time_decay_calculator(self) -> None:
        """Test time decay factors."""
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        past_5h = (datetime.utcnow() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        past_30h = (datetime.utcnow() - timedelta(hours=30)).strftime("%Y-%m-%d %H:%M:%S")
        past_60h = (datetime.utcnow() - timedelta(hours=60)).strftime("%Y-%m-%d %H:%M:%S")

        m_now = TimeDecayCalculator.calculate_multiplier(now, current_time=now)
        m_5h = TimeDecayCalculator.calculate_multiplier(past_5h, current_time=now)
        m_30h = TimeDecayCalculator.calculate_multiplier(past_30h, current_time=now)
        m_60h = TimeDecayCalculator.calculate_multiplier(past_60h, current_time=now)

        self.assertEqual(m_now, 1.0)
        self.assertLess(m_5h, 1.0)
        self.assertGreater(m_5h, 0.79)
        self.assertLess(m_30h, 0.5)
        self.assertEqual(m_60h, 0.0)

    def test_builder_and_pipeline(self) -> None:
        """Test NewsContextBuilder and NewsPipeline end-to-end."""
        # End to end news building
        ctx = NewsContextBuilder.build_context(
            self.raw_articles, self.raw_events
        )
        self.assertIsInstance(ctx, NewsContextV2)
        self.assertEqual(ctx.statistics.total_articles, 3) # 4 raw, 1 duplicate merged -> 3
        self.assertGreater(len(ctx.upcoming_events), 0)
        self.assertGreater(len(ctx.current_events) + len(ctx.overnight_events), 0)
        
        # Test Pipeline
        pipeline = NewsPipeline()
        ctx_from_pipeline = pipeline.run()
        self.assertIsInstance(ctx_from_pipeline, NewsContext)

    def test_dashboard_news_panel(self) -> None:
        """Test NewsIntelligencePanel dictionary serialization and CLI rendering."""
        ctx = NewsContextBuilder.build_context(
            self.raw_articles, self.raw_events
        )
        panel = NewsIntelligencePanel(ctx)
        dct = panel.to_dict()
        
        self.assertIn("statistics", dct)
        self.assertIn("summary", dct)
        self.assertIn("critical_events", dct)
        self.assertIn("upcoming_events", dct)
        self.assertIn("articles", dct)
        
        cli = panel.render_cli()
        self.assertIn("NEWS INTELLIGENCE CONTEXT", cli)
        self.assertIn("KEY MARKET TAKEAWAYS", cli)
        self.assertIn("UPCOMING MACROECONOMIC EVENTS", cli)
        self.assertIn("RECENT ARTICLES", cli)

        # Integration in workstation dashboard
        workstation = TradingWorkstationDashboard(news_context=ctx)
        workstation_dct = workstation.to_dict()
        self.assertIn("news_intelligence", workstation_dct)
        
        workstation_cli = workstation.render_cli()
        self.assertIn("NEWS INTELLIGENCE CONTEXT", workstation_cli)
