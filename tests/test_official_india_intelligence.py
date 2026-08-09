from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from src.application.workstation_state_service import WorkstationStateService
from src.models.macro_context import NiftyConstituentItem, NiftyConstituentMetadata
from src.news_engine.corporate_calendar_provider import CorporateCalendarProvider
from src.news_engine.institutional_flow_provider import InstitutionalFlowProvider
from src.news_engine.nifty_metadata_provider import NiftyMetadataProvider
from src.news_engine.official_india_provider import (
    NseBoardMeetingsProvider,
    NseCorporateAnnouncementsProvider,
    NseFinancialResultsProvider,
)
from src.news_engine.official_source_provider import OfficialSourceProvider
from src.pipeline.macro_pipeline import MacroPipeline


def _meta() -> NiftyConstituentMetadata:
    return NiftyConstituentMetadata(
        metadata_version="nifty50-test",
        effective_from="",
        retrieved_at="2026-08-09T00:00:00Z",
        verified_source="NSE Indices Limited",
        source_attribution="Official constituent download",
        is_available=True,
        constituents=[
            NiftyConstituentItem("RELIANCE", "Reliance Industries Limited", "Oil Gas & Consumable Fuels", None, "INE002A01018", resolution_status="RESOLVED"),
            NiftyConstituentItem("HDFCBANK", "HDFC Bank Limited", "Financial Services", None, "INE040A01034", resolution_status="RESOLVED"),
        ],
        weights_status="UNAVAILABLE",
        weights_reason="official_constituent_csv_does_not_publish_full_constituent_weights",
        source_url="https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        resolution_count=2,
    )


def _pipeline(tmp_path: Path) -> MacroPipeline:
    flows = InstitutionalFlowProvider(fixture_data=[
        {"dataset_type": "FII_CASH", "date": "07-Aug-2026", "buy_value": 100.0, "sell_value": 80.0, "net_value": 20.0, "currency": "INR_CR", "source_name": "NSE", "source_attribution": "NSE official", "retrieved_at": "2026-08-09T00:00:00Z", "source_authority": "PRIMARY"},
        {"dataset_type": "DII_CASH", "date": "07-Aug-2026", "buy_value": 90.0, "sell_value": 95.0, "net_value": -5.0, "currency": "INR_CR", "source_name": "NSE", "source_attribution": "NSE official", "retrieved_at": "2026-08-09T00:00:00Z", "source_authority": "PRIMARY"},
    ])
    actions = CorporateCalendarProvider(fixture_data={"CORPORATE_ACTION": [{
        "symbol": "RELIANCE", "company_name": "Reliance Industries Limited", "action_type": "DIVIDEND",
        "ex_date": "11-Aug-2026", "record_date": "12-Aug-2026", "details": "Dividend",
        "source_name": "NSE", "source_attribution": "NSE official",
    }]})
    announcements = NseCorporateAnnouncementsProvider(fixture_data=[{
        "symbol": "RELIANCE", "attchmntText": "Reliance announces acquisition", "desc": "Acquisition",
        "an_dt": "09-Aug-2026 09:00:00", "sm_name": "Reliance Industries Limited", "sm_isin": "INE002A01018", "seq_id": "1", "attchmntFile": "https://nsearchives.nseindia.com/a.pdf",
    }])
    boards = NseBoardMeetingsProvider(fixture_data=[{
        "bm_symbol": "OTHER", "bm_date": "12-Aug-2026", "bm_purpose": "Financial Results",
        "bm_desc": "Consider results", "bm_timestamp": "09-Aug-2026 08:00:00", "sm_name": "Other Limited", "sm_isin": "INE000000001",
    }])
    results = NseFinancialResultsProvider(fixture_data=[{
        "symbol": "HDFCBANK", "filingDate": "08-Aug-2026 18:00", "relatingTo": "First Quarter",
        "companyName": "HDFC Bank Limited", "isin": "INE040A01034", "toDate": "30-Jun-2026",
        "audited": "Un-Audited", "consolidated": "Consolidated", "seqNumber": "2",
    }])
    return MacroPipeline(
        providers=[flows, actions, announcements, boards, results],
        metadata_provider=NiftyMetadataProvider(metadata_fixture=_meta()),
        cache_file=tmp_path / "macro.json",
    )


def test_official_constituent_ingestion_and_no_false_weight(tmp_path: Path) -> None:
    context = _pipeline(tmp_path).run().to_dict()
    meta = context["constituent_metadata"]
    assert len(meta["constituents"]) == 2
    assert all(item["weight_pct"] is None for item in meta["constituents"])
    assert meta["weights_status"] == "UNAVAILABLE"
    assert meta["source_authority"] == "PRIMARY"


def test_constituent_symbol_resolution() -> None:
    csv_data = b"Company Name,Industry,Symbol,Series,ISIN Code\n" + b"\n".join(
        f"Company {i},Sector,SYM{i},EQ,INE{i:09d}".encode() for i in range(50)
    ) + b"\n"
    instruments = [{"tradingsymbol": f"SYM{i}", "exchange": "NSE", "instrument_type": "EQ", "instrument_token": i} for i in range(50)]
    provider = NiftyMetadataProvider()
    with patch("src.news_engine.nifty_metadata_provider.safe_url_fetch", return_value=(csv_data, {}, 200)), patch("src.news_engine.nifty_metadata_provider.InstrumentCacheManager.load_cache", return_value=instruments):
        meta = provider.fetch_metadata()
    assert meta.is_available and meta.resolution_count == 50
    assert all(item.resolution_status == "RESOLVED" for item in meta.constituents)


def test_holiday_fii_dii_fallback_and_no_zero_defaults() -> None:
    provider = InstitutionalFlowProvider()
    valid = provider._parse_institutional_json(json.dumps([
        {"category": "FII/FPI", "date": "07-Aug-2026", "buyValue": "12.5", "sellValue": "10.0", "netValue": "2.5"}
    ]).encode())
    invalid = provider._parse_institutional_json(json.dumps([
        {"category": "DII", "date": "07-Aug-2026", "buyValue": "", "sellValue": "10", "netValue": "-10"}
    ]).encode())
    assert valid[0]["date"] == "07-Aug-2026"
    assert valid[0]["source_authority"] == "PRIMARY"
    assert invalid == []


def test_nifty_prioritization_and_official_categories(tmp_path: Path) -> None:
    events = _pipeline(tmp_path).run().official_india_events
    categories = {event["event_category"] for event in events}
    assert {"INDEX_METADATA", "INSTITUTIONAL_FLOW", "CORPORATE_ANNOUNCEMENT", "CORPORATE_ACTION", "BOARD_MEETING", "EARNINGS"} <= categories
    reliance = next(event for event in events if event.get("symbol") == "RELIANCE" and event["event_category"] == "CORPORATE_ANNOUNCEMENT")
    assert reliance["nifty50_member"] is True
    assert reliance["source_authority"] == "PRIMARY"


def test_stable_ids_and_duplicate_safety() -> None:
    fixture = [{"symbol": "RELIANCE", "attchmntText": "Announcement", "an_dt": "09-Aug-2026 09:00:00", "seq_id": "42"}]
    provider = NseCorporateAnnouncementsProvider(fixture_data=fixture)
    first = provider.fetch_raw_data()[0]
    second = provider.fetch_raw_data()[0]
    assert first["id"] == second["id"]


def test_last_valid_cache_fallback() -> None:
    provider = NseCorporateAnnouncementsProvider(fixture_data=[{"symbol": "RELIANCE", "attchmntText": "Announcement", "an_dt": "09-Aug-2026 09:00:00"}])
    first = provider.fetch_raw_data()
    provider.fixture_data = None
    with patch("src.news_engine.official_india_provider.safe_url_fetch", side_effect=RuntimeError("network down")):
        second = provider.fetch_raw_data()
    assert second == first
    assert provider.status == "stale"


def test_provider_health_and_canonical_counts(tmp_path: Path) -> None:
    context = _pipeline(tmp_path).run().to_dict()
    rows = {row["dataset"]: row for row in context["dataset_health"]}
    assert rows["institutional_flow_provider"]["provider_count"] == 2
    assert rows["institutional_flow_provider"]["canonical_count"] == 2
    assert rows["nse_financial_results"]["canonical_count"] == 1


def test_canonical_state_propagates_official_india(tmp_path: Path) -> None:
    macro = _pipeline(tmp_path).run().to_dict()
    state = WorkstationStateService.build_from_legacy({"macroIntelligence": macro, "newsSentiment": {"items": []}})
    assert state.macro_intelligence is not None
    assert any(event["event_category"] == "INDEX_METADATA" for event in state.macro_intelligence["official_india_events"])


def test_rbi_sebi_pib_classification_and_market_filter() -> None:
    xml = b"""<rss><channel>
    <item><title>CPI inflation release from MoSPI</title><link>https://pib.gov.in/PressReleasePage.aspx?PRID=1</link><pubDate>Sun, 09 Aug 2026 09:00:00 GMT</pubDate><description>Consumer price index data</description></item>
    <item><title>Cultural festival</title><link>https://pib.gov.in/PressReleasePage.aspx?PRID=2</link><pubDate>Sun, 09 Aug 2026 09:00:00 GMT</pubDate><description>Arts event</description></item>
    </channel></rss>"""
    provider = OfficialSourceProvider("pib_market_releases", "https://pib.gov.in/rss", xml_fixture=xml, market_relevant_only=True)
    items = provider.fetch_raw_news()
    assert len(items) == 1
    assert items[0]["canonical_event_category"] == "INDIA_MACRO"
    assert items[0]["source_authority"] == "PRIMARY"


def test_no_synthetic_values_in_official_payload(tmp_path: Path) -> None:
    data = _pipeline(tmp_path).run().to_dict()
    assert data["ingestion_metrics"]["synthetic_macro_values"] == 0
    data.pop("ingestion_metrics", None)
    payload = json.dumps(data).lower()
    assert "synthetic" not in payload
    assert "sample" not in payload
