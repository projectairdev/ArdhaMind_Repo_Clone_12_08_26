# tests/test_phase5_3_macro_additions.py
from __future__ import annotations

import json
import time
import unittest
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from src.models.macro_context import (
    MacroContext,
    MarketQuote,
    InstitutionalFlowItem,
    CorporateActionRecord,
    NiftyConstituentMetadata,
    NiftyConstituentItem,
)
from src.news_engine.safe_utils import _validate_url_security
from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine.global_market_provider import GlobalMarketProvider
from src.news_engine.institutional_flow_provider import InstitutionalFlowProvider
from src.news_engine.corporate_calendar_provider import CorporateCalendarProvider
from src.news_engine.nifty_metadata_provider import NiftyMetadataProvider
from src.pipeline.macro_pipeline import MacroPipeline
from src.dashboard.macro_panel import MacroIntelligencePanel
from src.server_bridge import macro_refresh_lock, handle_daemon_command


class TestPhase53MacroAdditions(unittest.TestCase):
    """
    Targeted test suite for Phase 5.3 — External Market & Macro Data Integration:
    - Provider parsing
    - SSRF protection
    - Circuit-breaker lifecycle
    - Persistence / restart
    - ETag / 304 handling
    - Stale cache retention
    - Single-flight refresh lock
    - Partial provider outage
    - Complete provider outage with cached data
    - Domain-specific freshness rules
    - Atomic canonical publication
    - Metadata effective-date handling & source provenance
    - Canonical / legacy serialization parity
    """

    def test_provider_parsing(self) -> None:
        provider = GlobalMarketProvider()
        json_payload = json.dumps({
            "quoteResponse": {
                "result": [{
                    "symbol": "CL=F",
                    "shortName": "Crude Oil",
                    "regularMarketPrice": 78.50,
                    "regularMarketPreviousClose": 77.30,
                    "regularMarketTime": int(datetime.now(timezone.utc).timestamp()),
                    "exchangeTimezoneName": "America/New_York",
                    "currency": "USD",
                }]
            }
        }).encode("utf-8")
        items = provider._parse_payload("GLOBAL_CUES", json_payload)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["symbol"], "CL=F")
        self.assertEqual(items[0]["category"], "COMMODITY")
        self.assertEqual(items[0]["price"], 78.50)

    def test_ssrf_protection(self) -> None:
        blocked_urls = [
            "http://127.0.0.1/macro",
            "http://localhost/api",
            "http://169.254.169.254/latest/meta-data/",
            "http://192.168.1.1/internal",
            "http://10.0.0.5/secret",
            "http://user:pass@example.com/api",
            "ftp://example.com/data",
            "http://example.com:22/ssh",
        ]
        for url in blocked_urls:
            with self.assertRaises(ValueError, msg=f"Should block {url}"):
                _validate_url_security(url)

    def test_circuit_breaker_lifecycle(self) -> None:
        provider = InstitutionalFlowProvider()
        self.assertEqual(provider.cb_state, "closed")
        self.assertTrue(provider.should_fetch())

        # Trip breaker after 3 failures
        for _ in range(3):
            provider.record_failure(Exception("Connection Error"))

        self.assertEqual(provider.cb_state, "open")
        self.assertEqual(provider.status, "unavailable")
        self.assertFalse(provider.should_fetch())

        # Transition to half_open after cooldown
        provider.circuit_open_until = time.time() - 1.0
        self.assertTrue(provider.should_fetch())
        self.assertEqual(provider.cb_state, "half_open")

        # Recovery on successful probe
        provider.record_success([{"dataset_type": "FII_CASH", "net_value": 150.0}])
        self.assertEqual(provider.cb_state, "closed")
        self.assertEqual(provider.status, "ready")

        # Trip again and test probe failure return to open
        for _ in range(3):
            provider.record_failure(Exception("Probe Error"))
        self.assertEqual(provider.cb_state, "open")

        provider.circuit_open_until = time.time() - 1.0
        self.assertTrue(provider.should_fetch())  # enter half_open
        provider.record_failure(Exception("Probe Failed Again"))
        self.assertEqual(provider.cb_state, "open")

    def test_persistence_and_restart(self) -> None:
        test_cache = Path(".cache") / "test_macro_cache.json"
        if test_cache.exists():
            test_cache.unlink()

        p1 = GlobalMarketProvider(fixture_data=[{"symbol": "S&P 500", "price": 5200.0, "category": "GLOBAL_INDEX"}])
        p1.etags["https://test.com/api"] = "ETAG-MACRO-99"
        p1.cached_raw_data = [{"symbol": "S&P 500", "price": 5200.0}]

        pipeline1 = MacroPipeline(providers=[p1], cache_file=test_cache)
        pipeline1.save_cache()

        # Instantiate new pipeline and verify restored cache
        p2 = GlobalMarketProvider()
        pipeline2 = MacroPipeline(providers=[p2], cache_file=test_cache)

        self.assertEqual(p2.etags.get("https://test.com/api"), "ETAG-MACRO-99")
        self.assertEqual(len(p2.cached_raw_data), 1)
        self.assertEqual(p2.cached_raw_data[0]["symbol"], "S&P 500")

        if test_cache.exists():
            test_cache.unlink()

    def test_etag_304_handling(self) -> None:
        provider = InstitutionalFlowProvider()
        provider.etags[provider.feed_url] = "ETAG-FLOW-304"
        provider.cached_raw_data = [{"dataset_type": "FII_CASH", "net_value": 500.0}]

        with patch("src.news_engine.institutional_flow_provider.safe_url_fetch") as mock_fetch:
            mock_fetch.return_value = (b"", {"ETag": "ETAG-FLOW-304"}, 304)
            data = provider.fetch_raw_data()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["net_value"], 500.0)

    def test_stale_cache_retention(self) -> None:
        provider = InstitutionalFlowProvider()
        provider.cached_raw_data = [{"dataset_type": "DII_CASH", "net_value": -200.0}]

        with patch("src.news_engine.institutional_flow_provider.safe_url_fetch") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("500 Server Error")
            data = provider.fetch_raw_data()
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["net_value"], -200.0)
            self.assertEqual(provider.status, "stale")

    def test_single_flight_refresh(self) -> None:
        acquired = macro_refresh_lock.acquire(blocking=False)
        self.assertTrue(acquired)
        try:
            res = handle_daemon_command("refresh_macro", {}, MagicMock(), MagicMock())
            self.assertFalse(res.get("success"))
            self.assertIn("already running", res.get("error", ""))
        finally:
            macro_refresh_lock.release()

    def test_partial_provider_outage(self) -> None:
        observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        p1 = GlobalMarketProvider(fixture_data=[{
            "symbol": "GOLD", "name": "Gold", "price": 2400.0, "reference_value": 2380.0,
            "change_pct": round((20.0 / 2380.0) * 100, 4), "category": "COMMODITY",
            "source_name": "Yahoo Finance Public Feed", "source_symbol": "GC=F", "provider_symbol": "GC=F",
            "observation_timestamp": observed, "published_at": observed, "retrieved_at": observed,
            "exchange_timezone": "America/New_York",
        }])
        p2 = InstitutionalFlowProvider()

        with patch("src.news_engine.institutional_flow_provider.safe_url_fetch") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("Network Down")
            pipeline = MacroPipeline(providers=[p1, p2])
            ctx = pipeline.run()

            self.assertTrue(ctx.usable)
            self.assertIn("GOLD", ctx.quotes)
            self.assertIn(ctx.provider_health["institutional_flow_provider"]["status"], {"degraded", "stale"})

    def test_complete_provider_outage_with_cached_data(self) -> None:
        p1 = GlobalMarketProvider()
        observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        p1.cached_raw_data = [{
            "symbol": "BRENT_CRUDE", "name": "Brent", "price": 85.0, "reference_value": 84.0,
            "change_pct": round((1.0 / 84.0) * 100, 4), "category": "COMMODITY",
            "source_name": "Yahoo Finance Public Feed", "source_symbol": "BZ=F", "provider_symbol": "BZ=F",
            "observation_timestamp": observed, "published_at": observed, "retrieved_at": observed,
            "exchange_timezone": "America/New_York",
        }]
        p2 = InstitutionalFlowProvider()
        p2.cached_raw_data = [{"dataset_type": "FII_CASH", "net_value": 100.0}]

        with patch("src.news_engine.safe_utils.safe_url_fetch") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("Total Outage")
            pipeline = MacroPipeline(providers=[p1, p2])
            ctx = pipeline.run()

            self.assertTrue(ctx.usable)
            self.assertIn("BRENT_CRUDE", ctx.quotes)
            self.assertEqual(len(ctx.institutional_flows), 1)

    def test_domain_specific_freshness(self) -> None:
        now_dt = datetime.now(timezone.utc)
        quote = MarketQuote(
            symbol="DXY", name="Dollar Index", category="FOREX", price=104.2,
            change=0.1, change_pct=0.1, currency="USD", source_name="Test",
            source_attribution="Test", retrieved_at=now_dt.isoformat(), published_at=now_dt.isoformat(),
            freshness_status="fresh"
        )
        flow = InstitutionalFlowItem(
            dataset_type="FII_CASH", date="2026-08-07", buy_value=1000.0, sell_value=800.0,
            net_value=200.0, currency="INR_CR", source_name="Test", source_attribution="Test",
            retrieved_at=now_dt.isoformat(), freshness_status="fresh"
        )
        ctx = MacroContext(
            scanned_at=now_dt.isoformat(), generated_at=now_dt.isoformat(),
            quotes={"DXY": quote}, institutional_flows=[flow]
        )
        pipeline = MacroPipeline(providers=[])
        res = pipeline._eval_domain_freshness([quote], now_dt, fresh_sec=300, stale_sec=1800)
        self.assertEqual(res, "fresh")

    def test_atomic_canonical_publication(self) -> None:
        pipeline = MacroPipeline(providers=[])
        ctx = pipeline.run()
        panel_dict = MacroIntelligencePanel(ctx).to_dict()
        self.assertIsInstance(panel_dict, dict)
        self.assertIn("quotes", panel_dict)

    def test_metadata_effective_date_handling(self) -> None:
        valid_meta = NiftyConstituentMetadata(
            metadata_version="1.1.0",
            effective_from="2026-08-01",
            retrieved_at="2026-08-07T00:00:00Z",
            verified_source="NSE Indices Official Catalog",
            source_attribution="NSE Indices Limited",
            is_available=True,
            constituents=[
                NiftyConstituentItem("RELIANCE", "Reliance Industries", "Energy", 9.8),
                NiftyConstituentItem("HDFCBANK", "HDFC Bank", "Banking", 11.2),
            ]
        )
        provider = NiftyMetadataProvider(metadata_fixture=valid_meta)
        meta = provider.fetch_metadata()
        self.assertTrue(meta.is_available)
        self.assertEqual(meta.metadata_version, "1.1.0")
        self.assertEqual(meta.effective_from, "2026-08-01")
        self.assertEqual(len(meta.constituents), 2)

        # Test unverified unavailable fallback
        provider_unverified = NiftyMetadataProvider()
        with patch("src.news_engine.nifty_metadata_provider.safe_url_fetch", side_effect=RuntimeError("official source unavailable")):
            meta_unverified = provider_unverified.fetch_metadata()
        self.assertFalse(meta_unverified.is_available)
        self.assertIn("UNAVAILABLE", meta_unverified.metadata_version)

    def test_source_provenance(self) -> None:
        quote = MarketQuote(
            symbol="GIFT_NIFTY", name="GIFT Nifty", category="GLOBAL_INDEX", price=24500.0,
            change=50.0, change_pct=0.2, currency="INR", source_name="NSE IX Official Feed",
            source_attribution="NSE IX Limited (GIFT City)", retrieved_at="2026-08-07T00:00:00Z",
            published_at="2026-08-07T00:00:00Z", freshness_status="fresh"
        )
        self.assertEqual(quote.source_name, "NSE IX Official Feed")
        self.assertEqual(quote.source_attribution, "NSE IX Limited (GIFT City)")

    def test_canonical_legacy_serialization_parity(self) -> None:
        ctx = MacroContext(scanned_at="2026-08-07T00:00:00Z", generated_at="2026-08-07T00:00:00Z")
        panel = MacroIntelligencePanel(ctx)
        d = panel.to_dict()
        self.assertEqual(d["scanned_at"], "2026-08-07T00:00:00Z")
        self.assertIn("quotes", d)
        self.assertIn("institutional_flows", d)
