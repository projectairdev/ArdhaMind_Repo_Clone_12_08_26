from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.application.workstation_state_service import WorkstationStateService
from src.models.macro_context import NiftyConstituentMetadata
from src.news_engine.global_market_provider import GlobalMarketProvider
from src.news_engine.macro_integrity import assess_macro_observation
from src.news_engine.nifty_metadata_provider import NiftyMetadataProvider
from src.pipeline.macro_pipeline import MacroPipeline


NOW = datetime(2026, 8, 9, 6, 0, tzinfo=timezone.utc)
OBSERVED = datetime(2026, 8, 7, 20, 50, tzinfo=timezone.utc)


def _metadata() -> NiftyMetadataProvider:
    return NiftyMetadataProvider(metadata_fixture=NiftyConstituentMetadata(
        metadata_version="UNAVAILABLE", effective_from="", retrieved_at=NOW.isoformat(),
        verified_source="NSE Indices Limited", source_attribution="official test boundary",
        is_available=False, constituents=[], weights_status="UNAVAILABLE",
        weights_reason="not_in_e3_scope", effective_date_status="UNAVAILABLE",
    ))


def _raw(symbol: str = "S&P 500", source_symbol: str = "^GSPC", price: float = 110.0,
         reference: float = 100.0, observed: datetime = OBSERVED, **overrides: object) -> dict:
    item = {
        "symbol": symbol, "name": symbol, "category": "GLOBAL_INDEX", "price": price,
        "change": price - reference,
        "change_pct": round(((price - reference) / reference) * 100.0, 4),
        "currency": "USD", "source_name": "Yahoo Finance Public Feed",
        "source_attribution": "Yahoo Finance chart API", "source_symbol": source_symbol,
        "provider_symbol": source_symbol, "exchange": "SNP",
        "exchange_timezone": "America/New_York", "instrument_type": "INDEX",
        "source_session": "UNKNOWN",
        "observation_timestamp": observed.isoformat().replace("+00:00", "Z"),
        "published_at": observed.isoformat().replace("+00:00", "Z"),
        "retrieved_at": NOW.isoformat().replace("+00:00", "Z"),
        "reference_value": reference, "reference_type": "PREVIOUS_CLOSE",
        "reference_timestamp": "", "change_source": "CALCULATED_FROM_PREVIOUS_CLOSE",
        "observation_mode": "LAST_VALID_SOURCE_OBSERVATION", "cache_restored": False,
    }
    item.update(overrides)
    return item


def _context(items: list[dict], now: datetime = NOW):
    provider = GlobalMarketProvider(fixture_data=items)
    return MacroPipeline(providers=[provider], metadata_provider=_metadata()).run(
        now.isoformat().replace("+00:00", "Z")
    )


def _workspace(ctx, now: datetime = NOW):
    payload = {
        "marketContext": {"current_spot": 24500.0, "observed_at": "2026-08-07T10:00:00Z"},
        "optionContext": {"expiry": "2026-08-11", "snapshot_timestamp": "2026-08-07T10:00:00Z"},
        "newsSentiment": {"status": "ready", "items": [{"id": "n", "published_at": "2026-08-09T05:30:00Z"}]},
        "macroIntelligence": ctx.to_dict(),
    }
    return WorkstationStateService.build_from_legacy(
        payload, broker_state="CONNECTED", market_state="HOLIDAY", now=now
    ).to_dict()


def test_01_provider_symbol_identity_map_is_exact() -> None:
    assert {value[0] for value in GlobalMarketProvider().symbol_map.values()} == {
        "^GSPC", "^IXIC", "^DJI", "^N225", "^HSI", "BZ=F", "GC=F",
        "USDINR=X", "DX-Y.NYB", "^TNX",
    }


def test_02_no_nsei_to_gift_alias_in_production_paths() -> None:
    paths = [Path("src/news_engine"), Path("src/pipeline"), Path("src/application"), Path("src/frontend")]
    text = "\n".join(file.read_text(encoding="utf-8", errors="ignore") for path in paths for file in path.rglob("*") if file.is_file())
    assert "^NSEI" not in text


def test_03_missing_gift_provider_is_explicitly_unavailable() -> None:
    data = _context([_raw()]).to_dict()
    assert "GIFT_NIFTY" not in data["quotes"]
    assert data["quote_status"]["GIFT_NIFTY"] == {
        "status": "UNAVAILABLE", "reason": "GENUINE_PROVIDER_NOT_CONFIGURED",
        "source": None, "source_symbol": None,
    }


def test_04_observation_timestamp_survives_normalization() -> None:
    quote = _context([_raw()]).to_dict()["quotes"]["S&P 500"]
    assert quote["observation_timestamp"] == "2026-08-07T20:50:00Z"
    assert quote["retrieved_at"] == "2026-08-09T06:00:00Z"


def test_05_cache_restore_preserves_observation_timestamp(tmp_path: Path) -> None:
    cache = tmp_path / "macro.json"
    first = GlobalMarketProvider(fixture_data=[_raw()])
    MacroPipeline(providers=[first], metadata_provider=_metadata(), cache_file=cache).run(NOW.isoformat())
    restored = GlobalMarketProvider(refresh_interval=3600)
    ctx = MacroPipeline(providers=[restored], metadata_provider=_metadata(), cache_file=cache).run(NOW.isoformat())
    assert ctx.to_dict()["quotes"]["S&P 500"]["observation_timestamp"] == "2026-08-07T20:50:00Z"


def test_06_cache_restore_cannot_turn_stale_into_fresh(tmp_path: Path) -> None:
    cache = tmp_path / "macro.json"
    first = GlobalMarketProvider(fixture_data=[_raw()])
    MacroPipeline(providers=[first], metadata_provider=_metadata(), cache_file=cache).run(NOW.isoformat())
    restored = GlobalMarketProvider(refresh_interval=3600)
    later = NOW + timedelta(days=5)
    ctx = MacroPipeline(providers=[restored], metadata_provider=_metadata(), cache_file=cache).run(later.isoformat())
    quote = ctx.to_dict()["quotes"]["S&P 500"]
    assert quote["freshness_status"] == "stale"
    assert quote["current_eligible"] is False


def test_07_percentage_change_is_recalculated_from_reference() -> None:
    quote = _context([_raw(price=103.0, reference=100.0)]).to_dict()["quotes"]["S&P 500"]
    assert quote["change"] == 3.0
    assert quote["change_pct"] == 3.0
    assert quote["change_source"] == "CALCULATED_FROM_PREVIOUS_CLOSE"


def test_08_provider_failure_isolated_per_symbol() -> None:
    provider = GlobalMarketProvider()
    epoch = int(OBSERVED.timestamp())
    def fetch(url: str, **_: object):
        if "%5EHSI" in url or "^HSI" in url:
            raise ConnectionError("Hang Seng unavailable")
        requested = url.split("/chart/")[1].split("?")[0]
        payload = {"chart": {"result": [{"meta": {
            "symbol": requested, "regularMarketPrice": 110, "chartPreviousClose": 100,
            "regularMarketTime": epoch, "currency": "USD", "exchangeTimezoneName": "UTC",
        }}]}}
        return json.dumps(payload).encode(), {}, 200
    with patch("src.news_engine.global_market_provider.safe_url_fetch", side_effect=fetch):
        rows = provider.fetch_raw_data()
    assert len(rows) == 9
    assert provider.instrument_health["HANG_SENG"]["status"] == "UNAVAILABLE"
    assert provider.status == "degraded"


def test_09_missing_symbol_does_not_remove_healthy_quotes() -> None:
    ctx = _context([_raw(), _raw("NASDAQ", "^IXIC", 105, 100)])
    data = ctx.to_dict()
    assert set(data["quotes"]) == {"S&P 500", "NASDAQ"}
    assert data["quote_status"]["HANG_SENG"]["status"] == "UNAVAILABLE"


def test_10_canonical_macro_serialization_has_required_provenance() -> None:
    quote = _context([_raw()]).to_dict()["quotes"]["S&P 500"]
    required = {"symbol", "display_name", "value", "change", "change_pct", "unit", "source",
                "observation_timestamp", "freshness", "status", "reference_value", "current_eligible"}
    assert required <= set(quote)


def test_11_global_telemetry_is_owned_by_market_pulse() -> None:
    state = _workspace(_context([_raw(), _raw("NASDAQ", "^IXIC")]))
    assert state["macro_intelligence"]["workspace_context"]["nifty_live_quote_keys"] == ["S&P 500", "NASDAQ"]
    nifty = Path("src/frontend/components/NiftyLiveWorkspace.tsx").read_text(encoding="utf-8")
    pulse = Path("src/frontend/components/MarketPulseWorkspace.tsx").read_text(encoding="utf-8")
    assert "GlobalMarketsDashboard" not in nifty
    assert "GLOBAL CUES" in pulse and "MACRO &amp; CROSS-ASSET" in pulse


def test_12_evening_outlook_consumes_only_since_close_macro_keys() -> None:
    source = Path("src/frontend/components/PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    assert "since_india_close_quote_keys" in source
    assert "sinceCloseQuotes" in source


def test_13_850_briefing_exposes_full_global_cues_widget() -> None:
    source = Path("src/frontend/components/PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    assert 'data-premarket-panel="briefing-850"' in source
    assert "<GlobalCuesWidget" in source


def test_14_opening_checklist_is_readiness_not_duplicate_dashboard() -> None:
    source = Path("src/frontend/components/PreMarketPlannerWorkspace.tsx").read_text(encoding="utf-8")
    panel = source.split('data-premarket-panel="opening-checklist"', 1)[1]
    assert "Missing Critical Data" in panel
    assert "GlobalCuesWidget" not in panel


def test_15_todays_analysis_consumes_contextual_macro_keys() -> None:
    source = Path("src/frontend/components/PhaseOneWorkspaces.tsx").read_text(encoding="utf-8")
    active_source = Path("src/frontend/components/MarketStory.tsx").read_text(encoding="utf-8")
    assert "todays_analysis_quote_keys" in source and "todays_analysis_quote_keys" in active_source
    assert "do not establish causality" in active_source


def test_16_live_assistant_does_not_use_stale_quotes_as_confirmation() -> None:
    source = Path("src/frontend/components/PhaseOneWorkspaces.tsx").read_text(encoding="utf-8")
    assert "live_assistant_quote_keys" in source
    assert "No global-market observation newer" in source


def test_17_no_synthetic_macro_values_or_gift_substitution() -> None:
    provider_source = Path("src/news_engine/global_market_provider.py").read_text(encoding="utf-8")
    pipeline_source = Path("src/pipeline/macro_pipeline.py").read_text(encoding="utf-8")
    assert "random.uniform" not in provider_source
    assert "GIFT_NIFTY" not in provider_source
    assert "synthetic_macro_values\": 0" in pipeline_source


def test_18_provider_to_canonical_loss_is_zero_for_valid_quotes() -> None:
    metrics = _context([_raw(), _raw("NASDAQ", "^IXIC")]).to_dict()["ingestion_metrics"]
    assert metrics["raw_global_quotes"] == 2
    assert metrics["canonical_global_quotes"] == 2
    assert metrics["provider_to_canonical_data_loss"] == 0


def test_19_canonical_to_workspace_loss_is_zero() -> None:
    state = _workspace(_context([_raw(), _raw("NASDAQ", "^IXIC")]))
    macro = state["macro_intelligence"]
    assert macro["workspace_context"]["canonical_quote_count"] == 2
    assert macro["workspace_context"]["workspace_quote_count"] == 2
    assert macro["ingestion_metrics"]["canonical_to_workspace_data_loss"] == 0


def test_20_restart_cache_preserves_full_provenance(tmp_path: Path) -> None:
    cache = tmp_path / "macro.json"
    first = GlobalMarketProvider(fixture_data=[_raw(cache_restored=False)])
    original = MacroPipeline(providers=[first], metadata_provider=_metadata(), cache_file=cache).run(NOW.isoformat()).to_dict()["quotes"]["S&P 500"]
    restored_provider = GlobalMarketProvider(refresh_interval=3600)
    restored = MacroPipeline(providers=[restored_provider], metadata_provider=_metadata(), cache_file=cache).run(NOW.isoformat()).to_dict()["quotes"]["S&P 500"]
    for key in ("source", "source_symbol", "provider_symbol", "value", "reference_value", "observation_timestamp", "change_pct"):
        assert restored[key] == original[key]


def test_21_timezone_naive_observation_is_unavailable() -> None:
    assessment = assess_macro_observation("2026-08-09T05:00:00", NOW, "UTC")
    assert assessment.status == "UNAVAILABLE"
    assert assessment.current_eligible is False


def test_22_provider_symbol_mismatch_is_rejected() -> None:
    data = _context([_raw(provider_symbol="^IXIC")]).to_dict()
    assert "S&P 500" not in data["quotes"]
    assert data["quote_status"]["S&P 500"]["reason"] == "INVALID_VALUE_REFERENCE_OR_SYMBOL_IDENTITY"


def test_23_fabricated_reference_is_rejected() -> None:
    data = _context([_raw(reference_value=0.0)]).to_dict()
    assert "S&P 500" not in data["quotes"]


def test_24_fetch_time_does_not_replace_observation_time() -> None:
    data = _context([_raw()]).to_dict()["quotes"]["S&P 500"]
    assert data["observation_timestamp"] != data["retrieved_at"]
    assert data["published_at"] == data["observation_timestamp"]
