from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.broker.services.kite_intelligence_service import KiteIntelligenceService
from src.broker.services.market_feed_service import MarketFeedService
from src.models.macro_context import NiftyConstituentItem, NiftyConstituentMetadata
from src.news_engine.nifty_metadata_provider import NiftyMetadataProvider
from src.news_engine.specialized_data_provider import (
    GiftNiftyProvider,
    NiftyReconstitutionProvider,
    NiftyWeightsProvider,
    NseParticipantDerivativesProvider,
    RbiRiskFreeRateProvider,
)
from src.options_engine.chain_builder import OptionChainContract
from src.options_engine.iv import analyze_iv, black_scholes_price, solve_implied_volatility
from src.pipeline.macro_pipeline import MacroPipeline


HEADER = (
    "Client Type,Future Index Long,Future Index Short,Future Stock Long,Future Stock Short,"
    "Option Index Call Long,Option Index Call Short,Option Index Put Long,Option Index Put Short,"
    "Option Stock Call Long,Option Stock Call Short,Option Stock Put Long,Option Stock Put Short,"
    "Total Long Contracts,Total Short Contracts"
)


def _participant_csv(kind: str = "Open Interest") -> str:
    rows = []
    for offset, participant in enumerate(("Client", "DII", "FII", "Pro"), start=1):
        values = [offset * 100 + index for index in range(1, 13)]
        rows.append(",".join([participant, *map(str, values), str(sum(values[::2])), str(sum(values[1::2]))]))
    return "\n".join([
        f'"Participant wise {kind} (no. of contracts) in Equity Derivatives as on Aug 07, 2026"',
        HEADER,
        *rows,
    ])


OI_CSV = _participant_csv("Open Interest")
VOLUME_CSV = _participant_csv("Trading Volumes")
RBI_HTML = "<html><body>Government Securities Market 91 day T-bills : 5.2780%* # as on August 06, 2026 Capital Market</body></html>"
RECONSTITUTION_HTML = "<html>Nifty 50 Some text Semi-annually - Last working day of March and September</html>"


def _participant_provider(tmp_path: Path, reports=None) -> NseParticipantDerivativesProvider:
    return NseParticipantDerivativesProvider(
        cache_path=tmp_path / "participants.json",
        fixture_reports=reports or {"OPEN_INTEREST": OI_CSV, "VOLUME": VOLUME_CSV},
        today=date(2026, 8, 9),
    )


def _metadata() -> NiftyConstituentMetadata:
    return NiftyConstituentMetadata(
        metadata_version="nifty50-e4a-test",
        effective_from="",
        retrieved_at="2026-08-09T00:00:00Z",
        verified_source="NSE Indices Limited",
        source_attribution="Official NIFTY 50 constituent download",
        is_available=True,
        constituents=[NiftyConstituentItem("RELIANCE", "Reliance Industries Limited", "Energy")],
        weights_status="LICENSE_REQUIRED",
        weights_reason="OFFICIAL_NIFTY_WEIGHTS_LICENSE_REQUIRED",
        source_url="https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
        source_authority="PRIMARY",
        resolution_count=1,
        effective_snapshot_date="2026-08-09",
    )


def test_participant_oi_parser_returns_24_rows() -> None:
    parsed = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "https://official/oi.csv", "2026-08-09T00:00:00Z")
    assert len(parsed["records"]) == 24


def test_participant_volume_parser_returns_24_rows() -> None:
    parsed = NseParticipantDerivativesProvider.parse_report(VOLUME_CSV, "VOLUME", "https://official/vol.csv", "2026-08-09T00:00:00Z")
    assert len(parsed["records"]) == 24


def test_participant_parser_has_all_four_participant_types() -> None:
    parsed = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "u", "t")
    assert {row["participant_type"] for row in parsed["records"]} == {"CLIENT", "DII", "FII", "PRO"}


def test_participant_parser_has_all_six_instrument_categories() -> None:
    parsed = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "u", "t")
    assert len({row["instrument_category"] for row in parsed["records"]}) == 6


def test_participant_parser_preserves_contract_units() -> None:
    parsed = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "u", "t")
    assert all(row["unit"] == "CONTRACTS" for row in parsed["records"])


def test_participant_parser_preserves_trade_date_and_timestamp() -> None:
    row = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "u", "t")["records"][0]
    assert row["trade_date"] == row["record_timestamp"] == "2026-08-07"


def test_participant_net_position_is_long_minus_short() -> None:
    row = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "u", "t")["records"][0]
    assert row["net_position"] == row["long_contracts"] - row["short_contracts"]


def test_participant_total_row_is_not_a_canonical_participant() -> None:
    extra = OI_CSV + "\nTOTAL," + ",".join(["1"] * 14)
    parsed = NseParticipantDerivativesProvider.parse_report(extra, "OPEN_INTEREST", "u", "t")
    assert all(row["participant_type"] != "TOTAL" for row in parsed["records"])


def test_participant_records_are_primary_nse_clearing_data() -> None:
    row = NseParticipantDerivativesProvider.parse_report(OI_CSV, "OPEN_INTEREST", "https://official", "t")["records"][0]
    assert row["source"] == "NSE Clearing Limited" and row["source_authority"] == "PRIMARY"


def test_participant_snapshot_keeps_oi_and_volume_separate(tmp_path: Path) -> None:
    snapshot = _participant_provider(tmp_path).fetch_snapshot()
    assert snapshot["open_interest"]["dataset_type"] == "OPEN_INTEREST"
    assert snapshot["volume"]["dataset_type"] == "VOLUME"


def test_participant_snapshot_exposes_deterministic_positioning(tmp_path: Path) -> None:
    positioning = _participant_provider(tmp_path).fetch_snapshot()["positioning"]
    assert positioning["FII_INDEX_FUTURES"]["positioning"] in {"NET_LONG", "NET_SHORT", "BALANCED"}


def test_participant_oi_failure_does_not_erase_volume(tmp_path: Path) -> None:
    snapshot = _participant_provider(tmp_path, {"VOLUME": VOLUME_CSV}).fetch_snapshot()
    assert snapshot["open_interest"] is None
    assert len(snapshot["volume"]["records"]) == 24


def test_participant_last_valid_cache_restores_each_dataset(tmp_path: Path) -> None:
    cache = tmp_path / "participants.json"
    _participant_provider(tmp_path).fetch_snapshot()
    failed = NseParticipantDerivativesProvider(cache_path=cache, fixture_reports={}, today=date(2026, 8, 9)).fetch_snapshot()
    assert len(failed["records"]) == 48
    assert all(row["status"] == "DEGRADED" for row in failed["records"])


def test_participant_invalid_report_is_rejected() -> None:
    with pytest.raises(ValueError):
        NseParticipantDerivativesProvider.parse_report("not a report", "OPEN_INTEREST", "u", "t")


def test_participant_holiday_lookup_skips_weekends(tmp_path: Path) -> None:
    requested = []

    def fetch(url, **kwargs):
        requested.append(url)
        return OI_CSV.encode(), {"Content-Type": "text/csv"}, 200

    provider = NseParticipantDerivativesProvider(cache_path=tmp_path / "p.json", today=date(2026, 8, 9))
    with patch("src.news_engine.specialized_data_provider.safe_url_fetch", side_effect=fetch):
        parsed = provider._download_latest("OPEN_INTEREST")
    assert parsed["trade_date"] == "2026-08-07"
    assert requested == [NseParticipantDerivativesProvider.report_url("OPEN_INTEREST", date(2026, 8, 7))]


def test_rbi_rate_parser_returns_decimal_and_percent() -> None:
    record = RbiRiskFreeRateProvider.parse_current_rates(RBI_HTML, "2026-08-09T00:00:00Z")
    assert record["rate"] == pytest.approx(0.05278) and record["rate_pct"] == pytest.approx(5.278)


def test_rbi_rate_parser_preserves_primary_provenance() -> None:
    record = RbiRiskFreeRateProvider.parse_current_rates(RBI_HTML, "2026-08-09T00:00:00Z")
    assert record["source"] == "Reserve Bank of India" and record["observation_date"] == "2026-08-06"


def test_rbi_rate_rejects_missing_observation_date() -> None:
    with pytest.raises(ValueError):
        RbiRiskFreeRateProvider.parse_current_rates("91 day T-bills : 5.2%", "t")


def test_rbi_rate_freshness_rejects_old_cache() -> None:
    assert not RbiRiskFreeRateProvider._is_fresh({"observation_date": "2026-07-01"}, date(2026, 8, 9))


def test_iv_is_unavailable_without_verified_rate() -> None:
    result = solve_implied_volatility(100, 100, 100, 1, None, "CE")
    assert result.iv is None and result.reason == "MISSING_RISK_FREE_RATE"


def test_call_iv_solver_converges() -> None:
    premium = black_scholes_price(100, 100, 1, 0.05, 0.2, "CE")
    result = solve_implied_volatility(premium, 100, 100, 1, 0.05, "CE")
    assert result.solver_status == "CONVERGED" and result.iv == pytest.approx(20, abs=0.1)


def test_put_iv_solver_converges() -> None:
    premium = black_scholes_price(100, 100, 1, 0.05, 0.25, "PE")
    result = solve_implied_volatility(premium, 100, 100, 1, 0.05, "PE")
    assert result.solver_status == "CONVERGED" and result.iv == pytest.approx(25, abs=0.1)


def test_iv_solver_rejects_impossible_price() -> None:
    assert solve_implied_volatility(200, 100, 100, 1, 0.05, "CE").reason == "IMPOSSIBLE_OPTION_PRICE"


def test_iv_solver_rejects_expired_contract() -> None:
    assert solve_implied_volatility(5, 100, 100, 0, 0.05, "CE").solver_status == "EXPIRED"


def test_iv_solver_reports_nonconvergence() -> None:
    premium = black_scholes_price(100, 100, 1, 0.05, 0.2, "CE")
    result = solve_implied_volatility(premium, 100, 100, 1, 0.05, "CE", tolerance=1e-15, max_iterations=1)
    assert result.solver_status == "NON_CONVERGENCE" and result.iv is None


def test_chain_iv_analysis_requires_rate() -> None:
    contract = OptionChainContract("NIFTYCE", 100, "2026-08-11", "CE", 5, 4, 6, 2, 40, 1, 1, 0, "ATM", True)
    assert analyze_iv([contract], 100, 100, date(2026, 8, 11), date(2026, 8, 9)).status == "UNAVAILABLE"


def test_chain_iv_analysis_uses_real_premium() -> None:
    expiry = date(2026, 9, 8)
    t = (expiry - date(2026, 8, 9)).days / 365
    premium = black_scholes_price(100, 100, t, 0.05, 0.22, "CE")
    contract = OptionChainContract("NIFTYCE", 100, expiry.isoformat(), "CE", premium, 1, 2, 1, 40, 1, 1, 0, "ATM", True)
    result = analyze_iv([contract], 100, 100, expiry, date(2026, 8, 9), r=0.05)
    assert result.status == "AVAILABLE" and result.atm_iv == pytest.approx(22, abs=0.1)


def test_market_feed_iv_is_additive_to_pcr_and_max_pain() -> None:
    expiry = "2026-09-08"
    timestamp = "2026-08-09T10:00:00+05:30"
    t = MarketFeedService._iv_time_to_expiry(expiry, timestamp)
    assert t is not None
    rows = []
    for kind in ("CE", "PE"):
        premium = black_scholes_price(100, 100, t, 0.05, 0.2, kind)
        rows.append({"strike": 100.0, "option_type": kind, "ltp": premium, "oi": 10, "volume": 5})
    envelope = {"pcr": 1.0, "max_pain": 100.0}
    with patch.object(RbiRiskFreeRateProvider, "load_validated_rate", return_value={"status": "AVAILABLE", "rate": 0.05, "source": "Reserve Bank of India", "observation_date": "2026-08-06"}):
        envelope["iv"] = MarketFeedService._apply_implied_volatility(rows, 100, expiry, timestamp, 100)
    assert envelope["pcr"] == 1.0 and envelope["max_pain"] == 100.0 and envelope["iv"]["rows"] == 2
    assert envelope["iv"]["atm_average_iv"] == pytest.approx(20, abs=0.1)


def test_option_iv_rows_keep_rate_and_option_timestamps() -> None:
    expiry, timestamp = "2026-09-08", "2026-08-09T10:00:00+05:30"
    t = MarketFeedService._iv_time_to_expiry(expiry, timestamp)
    rows = [{"strike": 100.0, "option_type": "CE", "ltp": black_scholes_price(100, 100, t, 0.05, 0.2, "CE"), "oi": 1, "volume": 1}]
    with patch.object(RbiRiskFreeRateProvider, "load_validated_rate", return_value={"status": "AVAILABLE", "rate": 0.05, "source": "Reserve Bank of India", "observation_date": "2026-08-06"}):
        MarketFeedService._apply_implied_volatility(rows, 100, expiry, timestamp, 100)
    assert rows[0]["iv_input_timestamp"] == timestamp and rows[0]["rate_observation_date"] == "2026-08-06"


def test_reconstitution_parser_has_official_schedule() -> None:
    record = NiftyReconstitutionProvider.parse_schedule(RECONSTITUTION_HTML, "2026-08-09T00:00:00Z")
    assert record["review_frequency"] == "SEMI_ANNUAL" and record["announcement_date"] is None


def test_membership_snapshot_is_versioned_and_persisted(tmp_path: Path) -> None:
    csv_data = b"Company Name,Industry,Symbol,Series,ISIN Code\n" + b"\n".join(
        f"Company {i},Sector,SYM{i},EQ,INE{i:09d}".encode() for i in range(50)
    ) + b"\n"
    instruments = [{"tradingsymbol": f"SYM{i}", "exchange": "NSE", "instrument_type": "EQ", "instrument_token": i} for i in range(50)]
    snapshot_path = tmp_path / "membership.json"
    with patch("src.news_engine.nifty_metadata_provider.MEMBERSHIP_SNAPSHOT_PATH", snapshot_path), \
         patch("src.news_engine.nifty_metadata_provider.safe_url_fetch", return_value=(csv_data, {}, 200)), \
         patch("src.news_engine.nifty_metadata_provider.InstrumentCacheManager.load_cache", return_value=instruments):
        metadata = NiftyMetadataProvider().fetch_metadata()
    assert metadata.metadata_version.startswith("nifty50-") and metadata.effective_snapshot_date
    persisted = __import__("json").loads(snapshot_path.read_text(encoding="utf-8"))
    assert persisted[0]["metadata_version"] == metadata.metadata_version
    assert len(persisted[0]["constituents"]) == 50


def test_gift_provider_contract_starts_without_data_before_first_attempt() -> None:
    health = GiftNiftyProvider().get_health().to_dict()
    assert health["latest_fetch_status"] == "NOT_ATTEMPTED"
    assert health["serving_mode"] == "NO_DATA"


def test_weights_provider_is_license_gated_and_makes_no_request() -> None:
    health = NiftyWeightsProvider.get_health()
    assert health["status"] == "LICENSE_REQUIRED" and health["last_attempted_fetch"] is None


def test_specialized_data_reaches_macro_canonical_state(tmp_path: Path) -> None:
    pipeline = MacroPipeline(
        providers=[], metadata_provider=NiftyMetadataProvider(metadata_fixture=_metadata()),
        participant_provider=_participant_provider(tmp_path),
        risk_free_rate_provider=RbiRiskFreeRateProvider(tmp_path / "rate.json", RBI_HTML),
        reconstitution_provider=NiftyReconstitutionProvider(tmp_path / "reconstitution.json", RECONSTITUTION_HTML),
        cache_file=tmp_path / "macro.json",
    )
    result = pipeline.run("2026-08-09T00:00:00Z").to_dict()
    assert len(result["institutional_derivatives"]["records"]) == 48
    assert result["risk_free_rate"]["rate"] == pytest.approx(0.05278)
    assert result["constituent_metadata"]["reconstitution"]["status"] == "AVAILABLE"


def test_specialized_ingestion_has_zero_record_loss(tmp_path: Path) -> None:
    pipeline = MacroPipeline(
        providers=[], metadata_provider=NiftyMetadataProvider(metadata_fixture=_metadata()),
        participant_provider=_participant_provider(tmp_path),
        risk_free_rate_provider=RbiRiskFreeRateProvider(tmp_path / "rate.json", RBI_HTML),
        reconstitution_provider=NiftyReconstitutionProvider(tmp_path / "reconstitution.json", RECONSTITUTION_HTML),
        cache_file=tmp_path / "macro.json",
    )
    metrics = pipeline.run("2026-08-09T00:00:00Z").ingestion_metrics
    assert metrics["specialized_provider_records"] == metrics["specialized_canonical_records"]
    assert metrics["specialized_provider_to_canonical_data_loss"] == 0
    assert metrics["synthetic_macro_values"] == 0


class _VixInstrumentService:
    def load_instruments(self, broker) -> None:
        return None

    def lookup_index_instrument(self, name: str):
        return {"tradingsymbol": "INDIA VIX", "exchange": "NSE", "instrument_token": 264969} if name == "INDIA VIX" else None


class _VixBroker:
    def get_quote(self, keys):
        return {"NSE:INDIA VIX": {"last_price": 12.16, "ohlc": {"close": 12.0}, "timestamp": "2026-08-07T15:30:00+05:30"}}

    def get_historical_data(self, *args, **kwargs):
        return [{"date": "2026-08-07", "close": 12.16}]


def test_india_vix_requires_exact_kite_instrument_and_quote(tmp_path: Path) -> None:
    with patch("src.broker.services.kite_intelligence_service.InstrumentService.get_instance", return_value=_VixInstrumentService()):
        snapshot = KiteIntelligenceService.build_india_vix_snapshot(_VixBroker(), True, tmp_path / "vix.json", True)
    assert snapshot["value"] == 12.16 and snapshot["source_symbol"] == "NSE:INDIA VIX"


def test_india_vix_preserves_timestamp_change_and_history(tmp_path: Path) -> None:
    with patch("src.broker.services.kite_intelligence_service.InstrumentService.get_instance", return_value=_VixInstrumentService()):
        snapshot = KiteIntelligenceService.build_india_vix_snapshot(_VixBroker(), True, tmp_path / "vix.json", True)
    assert snapshot["observation_timestamp"] and snapshot["change_pct"] == pytest.approx(1.3333333)
    assert snapshot["historical_series"] == [{"date": "2026-08-07", "close": 12.16}]


@pytest.mark.parametrize("value,regime", [(11.99, "LOW"), (12.0, "NORMAL"), (18.0, "ELEVATED"), (25.0, "HIGH")])
def test_india_vix_regime_thresholds_are_explicit(tmp_path: Path, value: float, regime: str) -> None:
    broker = _VixBroker()
    broker.get_quote = lambda keys: {"NSE:INDIA VIX": {"last_price": value, "ohlc": {"close": value}, "timestamp": "2026-08-07T15:30:00+05:30"}}
    with patch("src.broker.services.kite_intelligence_service.InstrumentService.get_instance", return_value=_VixInstrumentService()):
        snapshot = KiteIntelligenceService.build_india_vix_snapshot(broker, True, tmp_path / f"vix-{regime}.json", True)
    assert snapshot["regime"] == regime and snapshot["regime_version"] == "INDIA_VIX_REGIME_V1"


def test_india_vix_failure_restores_only_a_real_last_valid_snapshot(tmp_path: Path) -> None:
    cache = tmp_path / "vix.json"
    with patch("src.broker.services.kite_intelligence_service.InstrumentService.get_instance", return_value=_VixInstrumentService()):
        KiteIntelligenceService.build_india_vix_snapshot(_VixBroker(), True, cache, True)
        failed = _VixBroker()
        failed.get_quote = lambda keys: {}
        restored = KiteIntelligenceService.build_india_vix_snapshot(failed, True, cache, True)
    assert restored["status"] == "DEGRADED" and restored["cache_restored"] is True and restored["value"] == 12.16
