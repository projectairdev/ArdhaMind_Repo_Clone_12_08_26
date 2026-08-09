from __future__ import annotations

from datetime import datetime, timezone

from src.application.workstation_state_service import WorkstationStateService
from src.news_engine.specialized_data_provider import GiftNiftyProvider
from src.pipeline.macro_pipeline import MacroPipeline


GIFT_PAYLOAD = {
    "data": [
        {"INSTRUMENTTYPE": "FUTIDX", "SYMBOL": "NIFTY", "EXPIRYDATE": "25-Aug-2026",
         "LASTPRICE": "24721.00", "DAYCHANGE": "79.50", "DAYCHANGE_1": 79.5,
         "PERCHANGE": ".32", "CONTRACTSTRADED": 45227,
         "TIMESTMP": "08-Aug-2026 02:44:54", "TOKEN_NMBR": 1348},
        # The official endpoint can repeat the same contract row; identity de-duplication is mandatory.
        {"INSTRUMENTTYPE": "FUTIDX", "SYMBOL": "NIFTY", "EXPIRYDATE": "25-Aug-2026",
         "LASTPRICE": "24721.00", "DAYCHANGE": "79.50", "DAYCHANGE_1": 79.5,
         "PERCHANGE": ".32", "CONTRACTSTRADED": 45227,
         "TIMESTMP": "08-Aug-2026 02:44:54", "TOKEN_NMBR": 1348},
        {"INSTRUMENTTYPE": "FUTIDX", "SYMBOL": "NIFTY", "EXPIRYDATE": "29-Sep-2026",
         "LASTPRICE": "24806", "DAYCHANGE_1": 48, "CONTRACTSTRADED": 44,
         "TIMESTMP": "07-Aug-2026 19:26:01", "TOKEN_NMBR": 1215},
    ]
}


def _gift_provider(tmp_path):
    return GiftNiftyProvider(
        cache_path=tmp_path / "gift.json", fixture_payload=GIFT_PAYLOAD,
        fixture_status={"marketstatus": "Session 2 Market Closed - As On Aug 08, 2026 01:30"},
    )


def test_official_gift_snapshot_has_exact_futures_identity_and_reference(tmp_path):
    provider = _gift_provider(tmp_path)
    row = provider.fetch_raw_data()[0]
    assert row["source_name"] == "NSE International Exchange"
    assert row["source_symbol"] == row["provider_symbol"] == "NSEIX:NIFTY"
    assert row["instrument_type"] == "INDEX_FUTURE"
    assert row["contract_expiry"] == "2026-08-25"
    assert row["price"] == 24721.0 and row["reference_value"] == 24641.5
    assert row["observation_timestamp"].endswith("+05:30")


def test_gift_snapshot_reaches_canonical_without_continuous_contract_fabrication(tmp_path):
    provider = _gift_provider(tmp_path)
    context = MacroPipeline(providers=[], gift_provider=provider, cache_file=tmp_path / "macro.json").run(
        "2026-08-09T06:00:00Z").to_dict()
    quote = context["quotes"]["GIFT_NIFTY"]
    assert quote["status"] == "AVAILABLE" and quote["freshness"] == "last_valid_session"
    assert quote["contract_expiry"] == "2026-08-25"
    assert quote["observation_mode"] == "OFFICIAL_NEAR_MONTH_FUTURE_SNAPSHOT"
    assert context["provider_contracts"]["gift_nifty"]["latest_fetch_status"] == "SUCCESS"


def test_opening_gap_and_partial_readiness_are_separate_canonical_contracts(tmp_path):
    provider = _gift_provider(tmp_path)
    macro = MacroPipeline(providers=[], gift_provider=provider, cache_file=tmp_path / "macro.json").run(
        "2026-08-09T06:00:00Z").to_dict()
    payload = {
        "marketContext": {"current_spot": 24570.65, "timestamp": "2026-08-07T15:30:00+05:30"},
        "optionContext": {}, "newsSentiment": {"status": "unavailable", "items": []},
        "macroIntelligence": macro,
    }
    state = WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="HOLIDAY",
        now=datetime(2026, 8, 9, 6, tzinfo=timezone.utc),
    ).to_dict()
    gap = state["macro_intelligence"]["opening_gap"]
    assert gap["status"] == "READY" and gap["classification"] == "POSITIVE_GAP_INDICATION"
    assert gap["gap_points"] == 150.35
    assert "opening indication only" in gap["disclaimer"].lower()
    readiness = state["workspace_readiness"]["pre_market_850_readiness"]
    assert readiness["gift_nifty"] == "READY"
    assert readiness["overall_state"] != "READY"


def test_provider_health_distinguishes_failed_attempt_from_last_valid_serving(tmp_path):
    provider = _gift_provider(tmp_path)
    assert provider.fetch_raw_data()
    provider.fixture_payload = {"data": []}
    restored = provider.fetch_raw_data()
    health = provider.get_health().to_dict()
    assert restored and restored[0]["cache_restored"] is True
    assert health["latest_fetch_status"] == "FAILED"
    assert health["serving_mode"] == "LAST_VALID_DATA"
    assert health["data_status"] == "DEGRADED"


def test_opening_gap_is_not_recomputed_from_live_intraday_spot(tmp_path):
    provider = _gift_provider(tmp_path)
    macro = MacroPipeline(providers=[], gift_provider=provider, cache_file=tmp_path / "macro.json").run(
        "2026-08-09T06:00:00Z").to_dict()
    state = WorkstationStateService.build_from_legacy({
        "marketContext": {"current_spot": 24900, "timestamp": "2026-08-09T06:00:00Z"},
        "newsSentiment": {"status": "unavailable", "items": []}, "macroIntelligence": macro,
    }, broker_state="CONNECTED", market_state="MARKET_OPEN",
       now=datetime(2026, 8, 9, 6, tzinfo=timezone.utc)).to_dict()
    assert state["macro_intelligence"]["opening_gap"]["status"] == "UNAVAILABLE"


def test_financial_results_are_not_published_as_upcoming_earnings(tmp_path):
    context = MacroPipeline(providers=[], cache_file=tmp_path / "macro.json").run(
        "2026-08-09T06:00:00Z").to_dict()
    assert context["earnings_events"] == []
    assert context["domain_freshness"]["earnings_calendar"] == "unavailable"
