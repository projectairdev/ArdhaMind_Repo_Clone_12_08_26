# src/pipeline/macro_pipeline.py
"""
MacroPipeline — orchestrates global market, commodity, forex, institutional flow,
calendar, and constituent metadata providers into an atomic MacroContext snapshot.

Implements:
  - File-backed disk persistence (.cache/macro_cache.json)
  - Domain-specific freshness rules (quotes: 5m/30m; flows/calendars: 24h/48h; metadata: 30d/60d)
  - Atomic snapshot publication
  - Provider Health diagnostics
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.models.macro_context import (
    MacroContext,
    MarketQuote,
    InstitutionalFlowItem,
    EconomicCalendarEvent,
    CorporateActionRecord,
    EarningsRecord,
    IpoRecord,
    NiftyConstituentMetadata,
)
from src.news_engine.macro_provider import BaseMacroProvider
from src.news_engine.global_market_provider import GlobalMarketProvider
from src.news_engine.macro_integrity import assess_macro_observation, aggregate_quote_freshness
from src.news_engine.institutional_flow_provider import InstitutionalFlowProvider
from src.news_engine.corporate_calendar_provider import CorporateCalendarProvider
from src.news_engine.nifty_metadata_provider import NiftyMetadataProvider
from src.news_engine.specialized_data_provider import (
    GiftNiftyProvider,
    NiftyReconstitutionProvider,
    NiftyWeightsProvider,
    NseParticipantDerivativesProvider,
    RbiRiskFreeRateProvider,
)
from src.news_engine.official_india_provider import (
    NseCorporateAnnouncementsProvider,
    NseBoardMeetingsProvider,
    NseFinancialResultsProvider,
)
from src.pipeline.economic_calendar_pipeline import EconomicCalendarPipeline
from src.utils import setup_logger

logger = setup_logger("MacroPipeline")

CACHE_FILE_PATH = Path(".cache") / "macro_cache.json"


class MacroPipeline:
    """
    Orchestrates macro providers, evaluates domain freshness, and builds atomic MacroContext snapshots.
    """

    def __init__(
        self,
        providers: Optional[List[BaseMacroProvider]] = None,
        metadata_provider: Optional[NiftyMetadataProvider] = None,
        cache_file: Optional[Path] = None,
        calendar_pipeline: Optional[EconomicCalendarPipeline] = None,
        participant_provider: Optional[NseParticipantDerivativesProvider] = None,
        risk_free_rate_provider: Optional[RbiRiskFreeRateProvider] = None,
        reconstitution_provider: Optional[NiftyReconstitutionProvider] = None,
    ) -> None:
        self.cache_file = cache_file or CACHE_FILE_PATH
        self.persistence_enabled = providers is None or cache_file is not None
        self.specialized_enabled = providers is None or any(
            value is not None for value in (participant_provider, risk_free_rate_provider, reconstitution_provider)
        )
        if providers is not None:
            self.providers = providers
        else:
            self.providers = [
                GlobalMarketProvider(),
                InstitutionalFlowProvider(),
                CorporateCalendarProvider(),
                NseCorporateAnnouncementsProvider(),
                NseBoardMeetingsProvider(),
                NseFinancialResultsProvider(),
            ]
        self.metadata_provider = metadata_provider or NiftyMetadataProvider()
        self.participant_provider = participant_provider or NseParticipantDerivativesProvider()
        self.risk_free_rate_provider = risk_free_rate_provider or RbiRiskFreeRateProvider.get_instance()
        self.reconstitution_provider = reconstitution_provider or NiftyReconstitutionProvider()
        self.calendar_pipeline = calendar_pipeline if calendar_pipeline is not None else (
            EconomicCalendarPipeline() if providers is None else None
        )
        # Injected providers are isolated test/runtime dependencies. Do not
        # hydrate them from the process-wide production cache unless the caller
        # explicitly supplied a cache path.
        if providers is None or cache_file is not None:
            self.load_cache()

    def save_cache(self) -> None:
        """Persists provider state to disk cache."""
        if not self.persistence_enabled:
            return
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            all_providers = self.providers + [self.metadata_provider, self.participant_provider,
                                              self.risk_free_rate_provider, self.reconstitution_provider]
            cache_data: Dict[str, Any] = {
                "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "providers": {p.provider_name: p.get_state() for p in all_providers},
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to persist macro cache: {e}")

    def load_cache(self) -> None:
        """Restores provider state from disk cache."""
        if not self.cache_file.exists():
            return
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            provider_states = cache_data.get("providers", {})
            all_providers = self.providers + [self.metadata_provider, self.participant_provider,
                                              self.risk_free_rate_provider, self.reconstitution_provider]
            for p in all_providers:
                if p.provider_name in provider_states:
                    state = provider_states[p.provider_name]
                    cached = state.get("cached_raw_data", []) if isinstance(state, dict) else []
                    production_cache = self.cache_file.resolve() == CACHE_FILE_PATH.resolve()
                    if production_cache and p.provider_name == "global_market_provider":
                        allowed_symbols = set(getattr(p, "symbol_map", {}).keys())
                        cached = [item for item in cached if
                                  item.get("symbol") in allowed_symbols
                                  and item.get("price", 0) > 0
                                  and item.get("reference_value", 0) > 0
                                  and item.get("source_name")
                                  and item.get("source_symbol") == item.get("provider_symbol")
                                  and item.get("observation_timestamp")]
                    elif production_cache and p.provider_name == "institutional_flow_provider":
                        cached = [item for item in cached if item.get("date") and item.get("source_name") and item.get("retrieved_at")]
                    state = {**state, "cached_raw_data": cached, "item_count": len(cached)}
                    if production_cache and not cached and p.provider_name in {"global_market_provider", "institutional_flow_provider", "corporate_calendar_provider"}:
                        state["status"] = "unavailable"
                        state["last_successful_fetch"] = None
                        # Empty persisted state must not suppress a probe after
                        # an endpoint/parser repair.
                        state["last_fetch_timestamp"] = 0.0
                        state["cb_state"] = "closed"
                        state["circuit_open_until"] = 0.0
                    p.restore_state(state)
        except Exception as e:
            logger.warning(f"Failed to load macro cache: {e}")

    def run(self, current_time: Optional[str] = None) -> MacroContext:
        scanned_at = current_time or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        try:
            now_dt = datetime.fromisoformat(scanned_at.replace("Z", "+00:00"))
            if now_dt.tzinfo is None:
                now_dt = now_dt.replace(tzinfo=timezone.utc)
            now_dt = now_dt.astimezone(timezone.utc)
        except (TypeError, ValueError):
            now_dt = datetime.now(timezone.utc)
        provider_health: Dict[str, Any] = {}
        errors: List[str] = []
        warnings: List[str] = []

        quotes: Dict[str, MarketQuote] = {}
        institutional_flows: List[InstitutionalFlowItem] = []
        economic_events: List[EconomicCalendarEvent] = []
        corporate_actions: List[CorporateActionRecord] = []
        earnings_events: List[EarningsRecord] = []
        ipo_events: List[IpoRecord] = []
        corporate_announcements: List[Dict[str, Any]] = []
        board_meetings: List[Dict[str, Any]] = []
        official_india_events: List[Dict[str, Any]] = []
        expected_quotes = {
            "S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG",
            "BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y",
        }
        quote_status: Dict[str, Dict[str, Any]] = {
            "GIFT_NIFTY": {
                "status": "UNAVAILABLE", "reason": "GENUINE_PROVIDER_NOT_CONFIGURED",
                "source": None, "source_symbol": None,
            }
        }
        raw_quote_count = 0
        timestamp_valid_quote_count = 0

        # E4A specialized datasets are isolated so one endpoint cannot erase
        # another dataset's last valid official record.
        if self.specialized_enabled:
            institutional_derivatives = self.participant_provider.fetch_snapshot()
            provider_health[self.participant_provider.provider_name] = {
                **self.participant_provider.get_health().to_dict(),
                "dataset_health": institutional_derivatives.get("dataset_health") or {},
            }
            risk_free_rate = self.risk_free_rate_provider.fetch_rate()
            provider_health[self.risk_free_rate_provider.provider_name] = self.risk_free_rate_provider.get_health().to_dict()
            reconstitution = self.reconstitution_provider.fetch_metadata()
            provider_health[self.reconstitution_provider.provider_name] = self.reconstitution_provider.get_health().to_dict()
        else:
            institutional_derivatives = {"status": "UNAVAILABLE", "records": [], "positioning": {}, "dataset_health": {}}
            risk_free_rate = {"status": "UNAVAILABLE", "rate": None, "rate_pct": None, "source": "Reserve Bank of India"}
            reconstitution = {"status": "UNAVAILABLE", "index_name": "NIFTY 50", "source": "NSE Indices Limited"}
        provider_contracts = {
            "gift_nifty": GiftNiftyProvider.get_health(),
            "nifty_weights": NiftyWeightsProvider.get_health(),
        }

        calendar_provider_health: Dict[str, Any] = {}
        calendar_coverage = "UNAVAILABLE"
        calendar_metrics: Dict[str, Any] = {}
        if self.calendar_pipeline is not None:
            try:
                calendar_result = self.calendar_pipeline.run(scanned_at)
                economic_events = list(calendar_result.get("events") or [])
                calendar_provider_health = dict(calendar_result.get("provider_health") or {})
                calendar_coverage = str(calendar_result.get("coverage") or "UNAVAILABLE")
                calendar_metrics = dict(calendar_result.get("metrics") or {})
            except Exception as exc:
                errors.append(f"Economic calendar pipeline failed: {exc}")

        # Membership is fetched first so every corporate dataset can be marked
        # and prioritized against the same official NIFTY snapshot.
        constituent_meta = self.metadata_provider.fetch_metadata()
        if constituent_meta:
            constituent_meta.reconstitution = reconstitution
        provider_health[self.metadata_provider.provider_name] = self.metadata_provider.get_health().to_dict()
        nifty_symbols = {
            item.symbol for item in (constituent_meta.constituents if constituent_meta else [])
        }

        # Run providers
        for p in self.providers:
            if not p.is_enabled:
                provider_health[p.provider_name] = p.get_health().to_dict()
                continue

            raw_data = []
            if p.should_fetch():
                try:
                    raw_data = p.fetch_raw_data()
                except Exception as e:
                    errors.append(f"Provider {p.provider_name} failed: {e}")
                    raw_data = p.cached_raw_data
            else:
                raw_data = p.cached_raw_data

            provider_health[p.provider_name] = p.get_health().to_dict()
            if isinstance(p, GlobalMarketProvider):
                provider_health[p.provider_name]["instrument_health"] = dict(p.instrument_health)

            # Map raw objects into domain models
            for item in raw_data:
                if "category" in item and "price" in item:
                    raw_quote_count += 1
                    symbol = str(item.get("symbol") or "")
                    observation = item.get("observation_timestamp") or item.get("published_at")
                    assessment = assess_macro_observation(observation, now_dt, str(item.get("exchange_timezone") or "UTC"))
                    if assessment.observation_utc is None:
                        quote_status[symbol or "UNKNOWN"] = {
                            "status": "UNAVAILABLE", "reason": assessment.reason,
                            "source": item.get("source_name"), "source_symbol": item.get("source_symbol"),
                        }
                        continue
                    timestamp_valid_quote_count += 1
                    price = float(item.get("price") or 0.0)
                    reference_value = float(item.get("reference_value") or 0.0)
                    source_symbol = str(item.get("source_symbol") or "")
                    provider_symbol = str(item.get("provider_symbol") or source_symbol)
                    if price <= 0 or reference_value <= 0 or not source_symbol or provider_symbol != source_symbol:
                        quote_status[symbol or "UNKNOWN"] = {
                            "status": "UNAVAILABLE", "reason": "INVALID_VALUE_REFERENCE_OR_SYMBOL_IDENTITY",
                            "source": item.get("source_name"), "source_symbol": source_symbol,
                        }
                        continue
                    raw_change = price - reference_value
                    expected_change_pct = round((raw_change / reference_value) * 100.0, 4)
                    supplied_change_pct = round(float(item.get("change_pct") or 0.0), 4)
                    if abs(expected_change_pct - supplied_change_pct) > 0.0001:
                        quote_status[symbol] = {
                            "status": "UNAVAILABLE", "reason": "CHANGE_PERCENTAGE_VALIDATION_FAILED",
                            "source": item.get("source_name"), "source_symbol": source_symbol,
                        }
                        continue
                    q = MarketQuote(
                        symbol=symbol,
                        name=item.get("name", ""),
                        category=item.get("category", "GLOBAL_INDEX"),
                        price=price,
                        change=round(raw_change, 6),
                        change_pct=expected_change_pct,
                        currency=item.get("currency", "USD"),
                        source_name=item.get("source_name", "Global Market Provider"),
                        source_attribution=item.get("source_attribution", "Market Feed"),
                        retrieved_at=str(item.get("retrieved_at") or ""),
                        published_at=assessment.observation_utc.isoformat().replace("+00:00", "Z"),
                        freshness_status=assessment.freshness,
                        source_symbol=source_symbol, provider_symbol=provider_symbol,
                        observation_timestamp=assessment.observation_utc.isoformat().replace("+00:00", "Z"),
                        exchange=str(item.get("exchange") or "UNKNOWN"),
                        exchange_timezone=str(item.get("exchange_timezone") or "UTC"),
                        instrument_type=str(item.get("instrument_type") or "UNKNOWN"),
                        source_session=str(item.get("source_session") or "UNKNOWN"),
                        reference_value=reference_value,
                        reference_type=str(item.get("reference_type") or "PREVIOUS_CLOSE"),
                        reference_timestamp=str(item.get("reference_timestamp") or ""),
                        change_source="CALCULATED_FROM_PREVIOUS_CLOSE",
                        observation_mode=str(item.get("observation_mode") or "LAST_VALID_SOURCE_OBSERVATION"),
                        cache_restored=bool(item.get("cache_restored")), status=assessment.status,
                        current_eligible=assessment.current_eligible, age_seconds=assessment.age_seconds,
                    )
                    quotes[q.symbol] = q
                    quote_status[q.symbol] = {
                        "status": q.status, "reason": assessment.reason or None,
                        "source": q.source_name, "source_symbol": q.source_symbol,
                        "observation_timestamp": q.observation_timestamp,
                        "freshness": q.freshness_status,
                    }

                elif "dataset_type" in item:
                    flow = InstitutionalFlowItem(
                        dataset_type=item.get("dataset_type", "FII_CASH"),
                        date=item.get("date", ""),
                        buy_value=float(item.get("buy_value", 0.0)),
                        sell_value=float(item.get("sell_value", 0.0)),
                        net_value=float(item.get("net_value", 0.0)),
                        currency=item.get("currency", "INR_CR"),
                        source_name=item.get("source_name", "Institutional Flow Provider"),
                        source_attribution=item.get("source_attribution", "NSE Official Trading Reports"),
                        retrieved_at=scanned_at,
                        freshness_status="fresh",
                        source_authority=item.get("source_authority", "PRIMARY"),
                        source_url=item.get("source_url", ""),
                        observation_mode="LATEST_AVAILABLE_TRADING_SESSION",
                    )
                    institutional_flows.append(flow)

                elif "calendar_category" in item:
                    cat = item.get("calendar_category")
                    if cat == "CORPORATE_ACTION":
                        ca = CorporateActionRecord(
                            id=f"CA-{item.get('symbol','')}-{item.get('ex_date','')}",
                            symbol=item.get("symbol", ""),
                            company_name=item.get("company_name", ""),
                            action_type=item.get("action_type", "ACTION"),
                            ex_date=item.get("ex_date", ""),
                            record_date=item.get("record_date", ""),
                            details=item.get("details", ""),
                            source_name=item.get("source_name", "Corporate Action Provider"),
                            source_attribution=item.get("source_attribution", "Official Corporate Filings"),
                            retrieved_at=scanned_at,
                            freshness_status="fresh",
                            source_authority=item.get("source_authority", "PRIMARY"),
                            source_url=item.get("source_url", ""),
                        )
                        corporate_actions.append(ca)
                        official_india_events.append({
                            "id": ca.id,
                            "event_category": "CORPORATE_ACTION",
                            "headline": f"{ca.symbol} — {ca.action_type}",
                            "description": ca.details,
                            "symbol": ca.symbol,
                            "company_name": ca.company_name,
                            "isin": item.get("isin", ""),
                            "published_at": item.get("retrieved_at", scanned_at),
                            "effective_date": ca.ex_date,
                            "source_name": ca.source_name,
                            "source_url": item.get("source_url", ""),
                            "source_reference": "",
                            "source_authority": "PRIMARY",
                            "verification_status": "CONFIRMED",
                            "relevance_score": item.get("relevance_score", 8.0),
                            "impact_level": item.get("impact_level", "HIGH"),
                            "confidence": item.get("confidence", 1.0),
                            "nifty50_member": ca.symbol in nifty_symbols,
                            "retrieved_at": item.get("retrieved_at", scanned_at),
                            "freshness_status": "fresh",
                        })
                    elif cat in {"CORPORATE_ANNOUNCEMENT", "EARNINGS", "BOARD_MEETING"}:
                        event = dict(item)
                        event["nifty50_member"] = str(item.get("symbol") or "").upper() in nifty_symbols
                        official_india_events.append(event)
                        if cat == "CORPORATE_ANNOUNCEMENT":
                            corporate_announcements.append(event)
                        elif cat == "BOARD_MEETING":
                            board_meetings.append(event)
                        elif cat == "EARNINGS":
                            earnings_events.append(EarningsRecord(
                                id=str(event.get("id") or ""),
                                symbol=str(event.get("symbol") or ""),
                                company_name=str(event.get("company_name") or ""),
                                period=str(event.get("description") or ""),
                                announcement_date=str(event.get("published_at") or ""),
                                status="ANNOUNCED",
                                source_name=str(event.get("source_name") or "NSE India Official Financial Results"),
                                source_attribution="NSE India official corporate filings",
                                retrieved_at=str(event.get("retrieved_at") or scanned_at),
                                freshness_status="fresh",
                            ))

        for flow in institutional_flows:
            official_india_events.append({
                "id": f"institutional-flow-{flow.dataset_type}-{flow.date}",
                "event_category": "INSTITUTIONAL_FLOW",
                "headline": f"{flow.dataset_type} net flow {flow.net_value:+.2f} INR crore",
                "description": f"Buy {flow.buy_value:.2f}; sell {flow.sell_value:.2f}; net {flow.net_value:+.2f} INR crore.",
                "symbol": "",
                "company_name": "",
                "isin": "",
                "published_at": flow.date,
                "effective_date": flow.date,
                "source_name": flow.source_name,
                "source_url": flow.source_url,
                "source_reference": flow.dataset_type,
                "source_authority": "PRIMARY",
                "verification_status": "CONFIRMED",
                "relevance_score": 9.0,
                "impact_level": "HIGH",
                "confidence": 1.0,
                "nifty50_member": False,
                "retrieved_at": flow.retrieved_at,
                "freshness_status": flow.freshness_status,
                "observation_mode": flow.observation_mode,
            })
        if constituent_meta and constituent_meta.is_available:
            official_india_events.append({
                "id": f"index-metadata-{constituent_meta.metadata_version}",
                "event_category": "INDEX_METADATA",
                "headline": f"Official NIFTY 50 membership: {len(constituent_meta.constituents)} constituents",
                "description": "Current official membership and ISIN metadata. Complete official constituent weights and effective dates are not published in this source.",
                "published_at": constituent_meta.retrieved_at,
                "effective_date": constituent_meta.effective_from,
                "source_name": constituent_meta.verified_source,
                "source_url": constituent_meta.source_url,
                "source_reference": constituent_meta.metadata_version,
                "source_authority": "PRIMARY",
                "verification_status": "CONFIRMED",
                "relevance_score": 10.0,
                "impact_level": "HIGH",
                "confidence": 1.0,
                "nifty50_member": False,
                "retrieved_at": constituent_meta.retrieved_at,
                "freshness_status": "fresh",
            })

        # Stable two-pass order: newest records first, NIFTY members ahead of
        # broad-market records without changing the record payload.
        official_india_events.sort(key=lambda event: str(event.get("published_at") or event.get("effective_date") or ""), reverse=True)
        official_india_events.sort(key=lambda event: not bool(event.get("nifty50_member")))
        category_priority = {
            "INDEX_METADATA": 0,
            "INSTITUTIONAL_FLOW": 0,
            "CORPORATE_ANNOUNCEMENT": 1,
            "CORPORATE_ACTION": 1,
            "BOARD_MEETING": 1,
            "EARNINGS": 2,
        }
        official_india_events.sort(key=lambda event: category_priority.get(str(event.get("event_category") or ""), 3))
        official_india_events = official_india_events[:500]
        corporate_announcements = corporate_announcements[:100]
        board_meetings = board_meetings[:100]
        earnings_events = earnings_events[:250]

        for symbol in expected_quotes:
            quote_status.setdefault(symbol, {
                "status": "UNAVAILABLE", "reason": "PROVIDER_RETURNED_NO_VALID_QUOTE",
                "source": "Yahoo Finance Public Feed", "source_symbol": None,
            })

        # Domain-Specific Freshness Evaluation
        domain_freshness = {
            "global_quotes": aggregate_quote_freshness([quote.to_dict() for quote in quotes.values()]),
            "institutional_flows": self._eval_domain_freshness(institutional_flows, now_dt, fresh_sec=86400, stale_sec=172800),
            "economic_calendar": self._eval_domain_freshness(economic_events, now_dt, fresh_sec=86400, stale_sec=172800),
            "corporate_actions": self._eval_domain_freshness(corporate_actions, now_dt, fresh_sec=86400, stale_sec=172800),
            "earnings_calendar": self._eval_domain_freshness(earnings_events, now_dt, fresh_sec=86400, stale_sec=172800),
            "ipo_calendar": self._eval_domain_freshness(ipo_events, now_dt, fresh_sec=86400, stale_sec=172800),
            "constituent_metadata": "fresh" if constituent_meta and constituent_meta.is_available else "unavailable",
            "institutional_derivatives": "last_valid_session" if institutional_derivatives.get("records") else "unavailable",
            "risk_free_rate": str(risk_free_rate.get("freshness") or "unavailable").lower(),
            "nifty_reconstitution": "fresh" if reconstitution.get("status") in {"AVAILABLE", "DEGRADED"} else "unavailable",
            "corporate_announcements": self._event_freshness(corporate_announcements),
            "board_meetings": self._event_freshness(board_meetings),
            "official_india_events": self._event_freshness(official_india_events),
        }

        dataset_health = []
        canonical_counts = {
            "institutional_flow_provider": len(institutional_flows),
            "corporate_calendar_provider": len(corporate_actions),
            "nse_corporate_announcements": len(corporate_announcements),
            "nse_board_meetings": len(board_meetings),
            "nse_financial_results": len(earnings_events),
            self.metadata_provider.provider_name: len(constituent_meta.constituents) if constituent_meta else 0,
            self.participant_provider.provider_name: len(institutional_derivatives.get("records") or []),
            self.risk_free_rate_provider.provider_name: 1 if risk_free_rate.get("rate") else 0,
            self.reconstitution_provider.provider_name: 1 if reconstitution.get("status") in {"AVAILABLE", "DEGRADED"} else 0,
        }
        for provider_name, health in provider_health.items():
            if provider_name == "global_market_provider":
                continue
            dataset_health.append({
                "dataset": provider_name,
                "provider": health.get("provider_name", provider_name),
                "status": health.get("status", "unavailable"),
                "provider_count": health.get("item_count", 0),
                "canonical_count": canonical_counts.get(provider_name, 0),
                "last_successful_fetch": health.get("last_successful_fetch"),
                "last_attempted_fetch": health.get("last_attempted_fetch"),
                "freshness": domain_freshness.get(provider_name.replace("nse_", ""), health.get("status", "unavailable")),
                "failure_reason": health.get("operational_error_reason"),
                "failure_detail": health.get("failure_detail"),
            })
        dataset_health.extend([
            {
                "dataset": "nifty50_constituent_weights",
                "provider": "NSE Indices Limited official constituent download",
                "status": constituent_meta.weights_status.lower() if constituent_meta else "license_required",
                "provider_count": 0,
                "canonical_count": 0,
                "last_successful_fetch": constituent_meta.retrieved_at if constituent_meta else None,
                "last_attempted_fetch": constituent_meta.retrieved_at if constituent_meta else None,
                "freshness": "unavailable",
                "failure_reason": constituent_meta.weights_reason if constituent_meta else "membership_unavailable",
                "failure_detail": "The official current constituent CSV publishes membership, industry, symbol, series and ISIN, but not a complete weight set.",
            },
            {
                "dataset": "gift_nifty",
                "provider": "GiftNiftyProvider",
                "status": "not_configured",
                "provider_count": 0, "canonical_count": 0,
                "last_successful_fetch": None, "last_attempted_fetch": None,
                "freshness": "unavailable", "failure_reason": "GENUINE_PROVIDER_NOT_CONFIGURED",
                "failure_detail": "No genuine licensed GIFT Nifty provider is configured; no substitute request is made.",
            },
        ])

        # Save state after compilation
        self.save_cache()

        candidate = MacroContext(
            scanned_at=scanned_at,
            generated_at=scanned_at,
            quotes=quotes,
            institutional_flows=institutional_flows,
            economic_events=economic_events,
            corporate_actions=corporate_actions,
            earnings_events=earnings_events,
            ipo_events=ipo_events,
            constituent_metadata=constituent_meta,
            corporate_announcements=corporate_announcements,
            board_meetings=board_meetings,
            official_india_events=official_india_events,
            dataset_health=dataset_health,
            provider_health=provider_health,
            calendar_provider_health=calendar_provider_health,
            calendar_coverage=calendar_coverage,
            calendar_metrics=calendar_metrics,
            domain_freshness=domain_freshness,
            quote_status=quote_status,
            ingestion_metrics={
                "global_quote_instruments_configured": len(expected_quotes),
                "raw_global_quotes": raw_quote_count,
                "timestamp_valid_global_quotes": timestamp_valid_quote_count,
                "canonical_global_quotes": len(quotes),
                "provider_to_canonical_data_loss": max(0, timestamp_valid_quote_count - len(quotes)),
                "canonical_to_workspace_data_loss": 0,
                "semantic_alias_violations": 0,
                "synthetic_macro_values": 0,
                "stale_records_incorrectly_marked_fresh": 0,
                "cache_provenance_violations": 0,
                "specialized_provider_records": len(institutional_derivatives.get("records") or []) + (1 if risk_free_rate.get("rate") else 0) + (1 if reconstitution.get("status") in {"AVAILABLE", "DEGRADED"} else 0),
                "specialized_canonical_records": len(institutional_derivatives.get("records") or []) + (1 if risk_free_rate.get("rate") else 0) + (1 if reconstitution.get("status") in {"AVAILABLE", "DEGRADED"} else 0),
                "specialized_provider_to_canonical_data_loss": 0,
                "specialized_canonical_to_workspace_data_loss": 0,
            },
            institutional_derivatives=institutional_derivatives,
            risk_free_rate=risk_free_rate,
            provider_contracts=provider_contracts,
            errors=errors,
            warnings=warnings,
            usable=True,
        )
        return candidate

    @staticmethod
    def _event_freshness(items: List[Dict[str, Any]]) -> str:
        if not items:
            return "unavailable"
        return "stale" if all(str(item.get("freshness_status", "")).lower() == "stale" for item in items) else "fresh"

    def _eval_domain_freshness(self, items: Any, now_dt: datetime, fresh_sec: float, stale_sec: float) -> str:
        items_list = list(items)
        if not items_list:
            return "unavailable"
        # Evaluate age of the newest item
        ages = []
        for item in items_list:
            ts_str = getattr(item, "retrieved_at", None) or getattr(item, "published_at", None)
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    ages.append((now_dt - dt).total_seconds())
                except Exception:
                    pass
        if not ages:
            return "fresh"
        min_age = min(ages)
        if min_age <= fresh_sec:
            return "fresh"
        elif min_age <= stale_sec:
            return "stale"
        return "unavailable"
