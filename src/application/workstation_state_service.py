from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from src.application.data_quality_service import DataQualityService
from src.configuration_engine.runtime import Config
from src.models.canonical_workstation_state import CanonicalWorkstationState, sanitize_read_only
from src.models.data_quality import FreshnessStatus, SectionStatus, ValueClassification
from src.models.decision_support import DecisionSupportReport
from src.news_engine.temporal_integrity import assess_publication_time, strict_publication_timestamp
from src.news_engine.macro_integrity import assess_macro_observation, aggregate_quote_freshness
from src.intelligence_engine import UnifiedNiftyIntelligenceBuilder


class WorkstationStateService:
    SCHEMA_VERSION = "2.0.0"
    _sequence = 0
    _lock = Lock()
    _runtime_id = str(uuid4())

    @classmethod
    def _next_sequence(cls) -> int:
        with cls._lock:
            cls._sequence += 1
            return cls._sequence

    @classmethod
    def build_from_legacy(cls, payload: dict[str, Any], *, broker_state: str = "DISCONNECTED",
                          market_state: str = "UNKNOWN", now: datetime | None = None) -> CanonicalWorkstationState:
        current = now or datetime.now(timezone.utc)
        generated = current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        market_closed = str(market_state).upper() in {"CLOSED", "MARKET_CLOSED", "POST_MARKET", "HOLIDAY", "TRADING_HOLIDAY"}
        expired = str(broker_state).upper() in {"SESSION_EXPIRED", "TOKEN_EXPIRED", "EXPIRED"}
        market = sanitize_read_only(payload.get("marketContext") or {})
        raw_candles = market.get("candles") or []
        valid_candles, candle_errors = DataQualityService.validate_candles(raw_candles)
        market["candles"] = valid_candles
        if candle_errors:
            market["candle_validation_warnings"] = candle_errors

        tech = sanitize_read_only(payload.get("technicalAnalysis") or {})
        if not tech.get("vwap") or tech.get("vwap") == 0:
            tech["vwap_status"] = "UNAVAILABLE"
            tech["vwap_reason"] = "Index spot data has no volume; VWAP requires volume-weighted ticks."
        if not tech.get("ema_20") or not tech.get("ema_50"):
            tech["ema_status"] = "UNAVAILABLE"
            tech["ema_reason"] = "Requires minimum 50 historical candles for calculation."
        if tech.get("trend_direction") in {None, "", "UNKNOWN"}:
            tech["trend_reason"] = "Insufficient validated historical candles to establish technical trend direction."
        payload["technicalAnalysis"] = tech
        payload["marketContext"] = market

        options = sanitize_read_only(payload.get("optionContext") or {})
        market_observed = cls._timestamp(market)
        option_observed = cls._timestamp(options)
        market_value = market.get("current_spot", market.get("price"))
        market_available = DataQualityService.is_valid_number(market_value, positive=True) and bool(market_observed) and not expired
        explicit_option_time = options.get("provider_timestamp") or options.get("snapshot_timestamp") or options.get("observed_at")
        option_available = bool(option_observed) and not expired
        if market_closed:
            option_available = bool(explicit_option_time) and bool(options.get("current_weekly_expiry") or options.get("expiry")) and not expired
        market_source = "kite_historical_api" if market_closed else "kite_market_feed"
        market_meta = DataQualityService.metadata("nifty_spot", market_source, market_observed,
            instrument="NIFTY 50", generated_at=current, market_closed=market_closed,
            available=market_available,
            classification=ValueClassification.LIVE, now=current)
        option_meta = DataQualityService.metadata("option_aggregate", "kite_option_chain", option_observed,
            instrument="NIFTY options", generated_at=current, market_closed=market_closed,
            available=option_available, classification=ValueClassification.CALCULATED, now=current)
        market_status = cls._section(market_meta.freshness_status)
        option_status = cls._section(option_meta.freshness_status)
        news = sanitize_read_only(payload.get("newsSentiment") or {})
        cls._apply_news_temporal_workspace(news, current, market_observed)
        news_has_items = bool(news.get("items") or news.get("top_headlines") or news.get("high_impact_items"))
        news_status = SectionStatus.READY if news_has_items and str(news.get("status", "")).upper() not in {"UNAVAILABLE", "ERROR"} else SectionStatus.UNAVAILABLE
        analytics_status = cls._dependent(market_status, [option_status, news_status])
        assistant_status = cls._dependent(market_status, [option_status])
        macro = sanitize_read_only(payload.get("macroIntelligence") or {})
        cls._apply_macro_workspace(macro, current, market_observed)
        # Released macro events and their E2 reporting remain separate records,
        # but clusters carry a deterministic canonical reference when country,
        # topic and release window agree.
        cls._link_released_economic_events(news, macro)
        payload = {**payload, "newsSentiment": news}
        official_news_events = []
        for item in news.get("items") or []:
            canonical_category = item.get("canonical_event_category")
            if canonical_category not in {"RBI", "SEBI", "GOVERNMENT_POLICY", "INDIA_MACRO"}:
                continue
            official_news_events.append({
                "id": item.get("id"),
                "event_category": canonical_category,
                "headline": item.get("headline"),
                "description": item.get("summary_snippet"),
                "published_at": item.get("published_at"),
                "source_name": item.get("source_name"),
                "source_url": item.get("original_url"),
                "source_reference": item.get("source_reference") or item.get("original_url"),
                "source_authority": item.get("source_authority") or "PRIMARY",
                "official_subcategory": item.get("official_subcategory"),
                "verification_status": str(item.get("verification_status") or "").upper(),
                "relevance_score": item.get("nifty_relevance_score"),
                "impact_level": str(item.get("impact_strength") or "").upper(),
                "confidence": item.get("confidence"),
                "retrieved_at": item.get("received_at"),
                "freshness_status": item.get("freshness_status"),
            })
        if official_news_events:
            macro = {**macro, "official_india_events": [
                *(macro.get("official_india_events") or []), *official_news_events
            ]}
        vix_context = sanitize_read_only(market.get("india_vix_context") or {})
        if vix_context.get("value") is not None and vix_context.get("observation_timestamp"):
            macro["india_vix"] = vix_context
        elif macro.get("india_vix") and macro["india_vix"].get("value") is not None:
            macro["india_vix"].setdefault("status", "AVAILABLE")
        else:
            macro["india_vix"] = {
                **vix_context, "status": "UNAVAILABLE", "value": None,
                "failure_reason": vix_context.get("failure_reason") or "NO_VALIDATED_INDIA_VIX_OBSERVATION",
            }
        specialized = macro.get("institutional_derivatives") or {}
        specialized_records = specialized.get("records") or []
        specialized_workspace = macro.setdefault("specialized_workspace", {})
        specialized_workspace.update({
            "participant_record_count": len(specialized_records),
            "participant_latest_session": (specialized.get("open_interest") or {}).get("trade_date"),
            "india_vix_available": macro["india_vix"].get("status") in {"AVAILABLE", "DEGRADED"},
            "risk_free_rate_available": (macro.get("risk_free_rate") or {}).get("status") in {"AVAILABLE", "DEGRADED"},
            "option_iv_rows": int(options.get("iv_rows") or 0),
            "canonical_to_workspace_data_loss": 0,
        })
        macro.setdefault("ingestion_metrics", {})["specialized_canonical_to_workspace_data_loss"] = 0
        macro_quotes = macro.get("quotes") or {}
        macro_workspace = macro.get("workspace_context") or {}
        usable_macro_keys = set(macro_workspace.get("current_context_quote_keys") or [])
        has_macro_cues = bool(usable_macro_keys)

        flow_context = []
        for flow in macro.get("institutional_flows") or []:
            dataset = str(flow.get("dataset_type") or "").upper()
            net = flow.get("net_value")
            if dataset not in {"FII_CASH", "DII_CASH"} or not DataQualityService.is_valid_number(net):
                continue
            flow_context.append({
                **flow,
                "context": f"{dataset.replace('_CASH', '')}_CASH_{'BUYING' if float(net) > 0 else 'SELLING' if float(net) < 0 else 'BALANCED'}",
            })
        macro["institutional_context"] = {
            "cash": flow_context,
            "derivatives": specialized.get("positioning") or {},
            "status": "AVAILABLE" if flow_context or specialized_records else "UNAVAILABLE",
            "prediction": None,
        }

        gift = macro_quotes.get("GIFT_NIFTY") or {}
        nifty_reference = (
            market.get("previous_close")
            or market.get("current_spot")
            or macro.get("nifty_previous_close")
            or options.get("underlying_spot")
            or (payload.get("eveningReport") or {}).get("market_summary", {}).get("spot_price")
        )
        gap_session_eligible = market_closed or str(market_state).upper() in {"PRE_OPEN", "PRE_MARKET"}
        gap_ready = (
            gap_session_eligible
            and
            "GIFT_NIFTY" in usable_macro_keys
            and DataQualityService.is_valid_number(gift.get("price"), positive=True)
            and DataQualityService.is_valid_number(nifty_reference, positive=True)
        )
        if gap_ready:
            gap_points = float(gift["price"]) - float(nifty_reference)
            gap_pct = gap_points / float(nifty_reference) * 100.0
            direction = "POSITIVE_GAP_INDICATION" if gap_pct > 0.15 else "NEGATIVE_GAP_INDICATION" if gap_pct < -0.15 else "FLAT_OPEN_INDICATION"
            magnitude = "LARGE" if abs(gap_pct) >= 1.0 else "MODERATE" if abs(gap_pct) >= 0.5 else "SMALL" if abs(gap_pct) > 0.15 else "FLAT"
            macro["opening_gap"] = {
                "status": "READY", "readiness": "READY", "nifty_reference_close": float(nifty_reference),
                "gift_nifty_reference": float(gift["price"]), "gap_points": round(gap_points, 4),
                "gap_pct": round(gap_pct, 4), "classification": direction, "magnitude": magnitude,
                "observation_timestamp": gift.get("observation_timestamp"), "age_seconds": gift.get("age_seconds"),
                "freshness": gift.get("freshness_status"), "source": gift.get("source_name"),
                "contract_expiry": gift.get("contract_expiry"),
                "provenance": "GIFT_NIFTY_FUTURE_MINUS_VALIDATED_NIFTY_REFERENCE_CLOSE",
                "disclaimer": "Opening indication only; not a predicted NIFTY opening price.",
            }
        else:
            macro["opening_gap"] = {
                "status": "UNAVAILABLE", "readiness": "BLOCKED", "nifty_reference_close": nifty_reference,
                "gift_nifty_reference": gift.get("price"), "gap_points": None, "gap_pct": None,
                "classification": None, "failure_reason": "SESSION_OR_ELIGIBLE_GIFT_NIFTY_OR_NIFTY_REFERENCE_UNAVAILABLE",
            }

        iv_values = [float(row["iv"]) for row in options.get("iv_skew") or [] if DataQualityService.is_valid_number(row.get("iv"), positive=True)]
        atm_ce, atm_pe = options.get("atm_ce_iv"), options.get("atm_pe_iv")
        options["volatility_context"] = {
            "status": "AVAILABLE" if iv_values and DataQualityService.is_valid_number(atm_ce, positive=True) and DataQualityService.is_valid_number(atm_pe, positive=True) else "UNAVAILABLE",
            "india_vix_regime": macro["india_vix"].get("regime"),
            "atm_ce_iv": atm_ce, "atm_pe_iv": atm_pe, "atm_average_iv": options.get("atm_iv"),
            "ce_pe_iv_difference": round(float(atm_ce) - float(atm_pe), 4) if DataQualityService.is_valid_number(atm_ce) and DataQualityService.is_valid_number(atm_pe) else None,
            "strike_iv_min": min(iv_values) if iv_values else None, "strike_iv_max": max(iv_values) if iv_values else None,
            "strike_iv_dispersion": round(max(iv_values) - min(iv_values), 4) if iv_values else None,
            "source": "Kite option chain; deterministic Black-Scholes convergence",
            "fallback_iv_used": False,
        }
        payload = {**payload, "optionContext": options}
        broker_account = sanitize_read_only(payload.get("brokerAccount") or {})

        core_market_ready = market_status in {SectionStatus.READY, SectionStatus.MARKET_CLOSED} and not expired
        overall_state = "NOT_READY" if expired or market_status == SectionStatus.BLOCKED else ("DEGRADED" if news_status != SectionStatus.READY or not has_macro_cues else "READY")

        premarket_inputs = {
            "gift_nifty": "READY" if "GIFT_NIFTY" in usable_macro_keys else "UNAVAILABLE",
            "global_indices": "READY" if usable_macro_keys & {"S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG"} else "UNAVAILABLE",
            "commodities_fx": "READY" if usable_macro_keys & {"BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y"} else "UNAVAILABLE",
            "fii_dii": "READY" if macro.get("institutional_flows") else "UNAVAILABLE",
            "derivative_positioning": "READY" if specialized_records else "UNAVAILABLE",
            "volatility": "READY" if macro["india_vix"].get("status") in {"AVAILABLE", "DEGRADED"} else "UNAVAILABLE",
            "calendars": "READY" if macro.get("corporate_actions") or macro.get("economic_events") else "UNAVAILABLE",
            "news": "READY" if news_status == SectionStatus.READY else "UNAVAILABLE",
        }
        ready_count = sum(value == "READY" for value in premarket_inputs.values())
        full_premarket = all(premarket_inputs[key] == "READY" for key in ("gift_nifty", "global_indices", "commodities_fx", "fii_dii", "news"))
        premarket_state = "READY" if full_premarket else "PARTIAL_READY" if ready_count >= 4 else "BLOCKED" if not market_available else "UNAVAILABLE"
        readiness = {
            "overall_state": overall_state,
            "core_market_feed_state": "READY" if core_market_ready else "UNAVAILABLE",
            "intelligence_providers_state": "READY" if news_status == SectionStatus.READY and has_macro_cues else "DEGRADED",
            "pre_market_850_readiness": {
                **premarket_inputs,
                "overall_state": premarket_state,
                "ready_inputs": sorted(key for key, value in premarket_inputs.items() if value == "READY"),
                "unavailable_inputs": sorted(key for key, value in premarket_inputs.items() if value == "UNAVAILABLE"),
                "blocked_inputs": [] if market_available else ["validated_nifty_reference"],
                "is_full_premarket_ready": full_premarket,
            },
            "nifty_live": cls._ready("NIFTY Live", market_status, cls._reasons(market_status)),
            "pre_market_planner": cls._ready("Pre-Market Planner", market_status,
                [] if market_status in {SectionStatus.READY, SectionStatus.MARKET_CLOSED} else ["validated market snapshot"]),
            "todays_analysis": cls._ready("Today's Analysis", analytics_status,
                cls._reasons(market_status, option_status, news_status)),
            "news_updates": cls._ready("NEWS & UPDATES", news_status,
                [] if news_status == SectionStatus.READY else ["real news provider"]),
            "live_assistant": cls._ready("Live Assistant", assistant_status,
                cls._reasons(market_status, option_status)),
            "settings": cls._ready("Settings", SectionStatus.READY, []),
        }
        unified = UnifiedNiftyIntelligenceBuilder.build(
            market=market, technical=sanitize_read_only(payload.get("technicalAnalysis") or {}),
            options=options, macro=macro, news=news, market_state=market_state,
            market_meta=market_meta.to_dict(), option_meta=option_meta.to_dict(), now=current,
        )
        for workspace_key in ("pre_market_planner", "todays_analysis", "live_assistant"):
            readiness[workspace_key]["unified_intelligence_mode"] = unified["mode"]
            readiness[workspace_key]["unified_intelligence_readiness"] = unified["readiness"]
        blockers = cls._reasons(market_status, option_status)
        support = DecisionSupportReport(
            market_interpretation="Validated analytical context" if not blockers else "Analytical context incomplete",
            current_scenario_status="market_closed" if market_closed else ("blocked" if blockers else "monitor"),
            required_confirmations=["validated NIFTY spot", "validated option aggregate"],
            missing_confirmations=blockers, blockers=blockers,
            warnings=["Live broker session requires reconnect"] if expired else [],
        )
        support_payload = {
            **support.to_dict(),
            "unified_intelligence_engine": unified["engine"],
            "session_mode": unified["mode"],
            "alignment": unified["alignment"],
            "confirming_signals": unified["confirming_signals"],
            "opposing_signals": unified["opposing_signals"],
            "unavailable_or_ineligible_signals": unified["unavailable_or_ineligible_signals"],
            "market_regime": unified["market_regime"],
            "key_levels": unified["key_levels"],
            "scenarios": unified["scenarios"],
            "invalidation_conditions": unified["invalidation_conditions"],
            "risk": unified["risk"], "confidence": unified["confidence"],
            "human_decision_required": True, "execution_authorized": False,
        }
        explanation_payload = {
            **sanitize_read_only(payload.get("explanationReport") or {}),
            "status": assistant_status.value, "engine": unified["engine"],
            "deterministic": True, "llm_dependency": False,
            "summary": unified["explanation"],
            "evidence": {name: signal["evidence"] for name, signal in unified["signals"].items()},
            "confirming_signals": unified["confirming_signals"],
            "opposing_signals": unified["opposing_signals"],
        }
        confidence_payload = {
            **sanitize_read_only(payload.get("confidenceReport") or {}),
            "unified_evidence_quality": unified["confidence"],
            "evidence_completeness": unified["evidence_completeness"],
            "agreement_state": unified["alignment"],
            "explainable": True,
        }
        risk_payload = {
            **sanitize_read_only(payload.get("riskReport") or {}),
            "unified_analytical_risk": unified["risk"],
            "event_risk": unified["signals"]["events"],
            "volatility_risk": unified["signals"]["volatility"],
            "data_quality_risk": unified["unavailable_or_ineligible_signals"],
            "position_sizing": None,
        }
        def section(name: str, status: SectionStatus, fallback: Any = None) -> dict[str, Any]:
            value = sanitize_read_only(payload.get(name) or fallback or {})
            if status == SectionStatus.UNAVAILABLE and name in {"marketContext", "optionContext"} and not (isinstance(value, dict) and (value.get("current_spot") or value.get("breadth"))):
                return {"status": status.value}
            if isinstance(value, dict):
                if name == "marketContext":
                    pc = value.get("previous_close") or nifty_reference
                    if pc and float(pc) > 0:
                        value["previous_close"] = float(pc)
                        sp = value.get("current_spot")
                        if sp and float(sp) > 0:
                            chg = round(float(sp) - float(pc), 2)
                            chg_pct = round(chg / float(pc) * 100.0, 4)
                            value.setdefault("spot_change", chg)
                            value.setdefault("spot_change_pct", chg_pct)
                            value.setdefault("change_points", chg)
                            value.setdefault("change_percent", chg_pct)
                return {**value, "status": status.value}
            return {"status": status.value, "value": value}
        return CanonicalWorkstationState(
            cls.SCHEMA_VERSION, cls._next_sequence(), generated, cls._runtime_id,
            {"status": "closed" if str(market_state).upper() == "MARKET_CLOSED" else str(market_state).lower(), "is_closed": market_closed},
            {"status": "degraded" if expired else "ready", "read_only": True},
            {"status": "session_expired" if expired else str(broker_state).lower(),
             "reconnect_required": expired,
             "session_valid": broker_account.get("session_valid") if broker_account else not expired,
             "last_authenticated_at": broker_account.get("last_authenticated_at") if broker_account else None,
             "last_profile_validation": broker_account.get("profile_validated_at") if broker_account else None,
             "last_successful_update": broker_account.get("profile_validated_at") if broker_account else market_observed,
             "redirect_url": getattr(Config, "KITE_REDIRECT_URL", "http://127.0.0.1:3000/api/broker/callback")},
            {"status": "market_closed" if market_closed else market_status.value, "source": market_source},
            section("marketContext", market_status), section("technicalAnalysis", market_status),
            section("optionContext", option_status), section("marketScore", market_status),
            section("opportunityContext", market_status), section("strategyEvaluation", assistant_status),
            sanitize_read_only(payload.get("tradeScenarios") or []),
            {**confidence_payload, "status": assistant_status.value}, {**risk_payload, "status": market_status.value},
            support_payload, explanation_payload,
            section("newsSentiment", news_status), broker_account or None, section("operationsReport", SectionStatus.READY),
            readiness, {"market_data": market_meta.to_dict(), "option_intelligence": option_meta.to_dict()},
            sanitize_read_only(payload.get("eveningReport") or {}),
            sanitize_read_only(payload.get("intradayReport") or {}),
            sanitize_read_only(payload.get("validationReport") or {}),
            sanitize_read_only(payload.get("optimizationReport") or {}),
            sanitize_read_only(payload.get("analyticsReport") or {}),
            macro,
            unified,
            warnings=support.warnings, errors=[],
        )

    @staticmethod
    def _timestamp(section: dict[str, Any]) -> Any:
        for key in ("provider_timestamp", "snapshot_timestamp", "observed_at", "observedAt", "last_tick_time", "timestamp", "lastUpdated", "generated_at", "generatedAt"):
            if section.get(key):
                return section[key]
        return None

    @staticmethod
    def _apply_news_temporal_workspace(news: dict[str, Any], now: datetime, market_observed: Any) -> None:
        """Re-evaluate time-dependent eligibility before canonical publication.

        This is a defensive second gate: persisted pipeline output cannot carry
        a previously-current flag forever across a restart or long-lived state.
        """
        explicit_close = strict_publication_timestamp(news.get("last_market_close_boundary"))
        boundary = strict_publication_timestamp(market_observed) or explicit_close
        current_items: list[dict[str, Any]] = []
        newly_historical: list[dict[str, Any]] = []
        for original in news.get("items") or []:
            item = dict(original)
            assessment = assess_publication_time(item.get("published_at"), now, explicit_close)
            item.update({
                "normalized_timestamp": assessment.published_at_utc.isoformat().replace("+00:00", "Z") if assessment.published_at_utc else "",
                "timestamp_validity": assessment.timestamp_validity,
                "timestamp_confidence": assessment.timestamp_confidence,
                "timestamp_source": assessment.timestamp_source,
                "temporal_class": assessment.temporal_class,
                "canonical_eligible": assessment.current_eligible,
                "workspace_eligible": assessment.current_eligible,
                "age_seconds": assessment.age_seconds,
                "age_minutes": round(assessment.age_seconds / 60, 2) if assessment.age_seconds is not None else None,
            })
            (current_items if assessment.current_eligible else newly_historical).append(item)

        current_ids = {str(item.get("id")) for item in current_items}
        news["items"] = current_items
        news["historical_items"] = [*(news.get("historical_items") or []), *newly_historical]
        for key in ("top_headlines", "high_impact_items"):
            news[key] = [item for item in news.get(key) or [] if str(item.get("id")) in current_ids]
        news["corporate_items"] = [item for item in news.get("corporate_items") or [] if str(item.get("id")) in current_ids]
        news["event_items"] = [item for item in news.get("event_items") or [] if str(item.get("id")) in current_ids]

        current_clusters = []
        expired_clusters = []
        for original in news.get("event_clusters") or []:
            cluster = dict(original)
            active_ids = [article_id for article_id in cluster.get("article_ids") or [] if str(article_id) in current_ids]
            cluster_time = cluster.get("latest_article_published_at") or cluster.get("last_updated")
            cluster_temporal = assess_publication_time(cluster_time, now, explicit_close)
            carried_current_count = int(cluster.get("current_article_count") or 0) if cluster_temporal.current_eligible else 0
            if cluster_temporal.current_eligible and "canonical_eligible" not in cluster:
                # Legacy canonical clusters predate the explicit count fields;
                # their own validated latest-publication timestamp is sufficient.
                carried_current_count = max(1, carried_current_count)
            active_count = max(len(active_ids), carried_current_count)
            cluster["current_article_count"] = active_count
            cluster["historical_article_count"] = max(0, int(cluster.get("article_count") or 0) - len(active_ids))
            cluster["canonical_eligible"] = bool(active_count)
            (current_clusters if active_count else expired_clusters).append(cluster)
        news["event_clusters"] = current_clusters
        news["historical_event_clusters"] = [*(news.get("historical_event_clusters") or []), *expired_clusters]

        since_close_ids: list[str] = []
        previous_session_ids: list[str] = []
        for item in current_items:
            observed = strict_publication_timestamp(item.get("published_at"))
            if boundary and observed and observed > boundary:
                since_close_ids.append(str(item.get("id")))
            elif boundary and observed:
                previous_session_ids.append(str(item.get("id")))
        since_close_clusters = [
            str(cluster.get("event_cluster_id")) for cluster in current_clusters
            if any(str(article_id) in set(since_close_ids) for article_id in cluster.get("article_ids") or [])
        ]
        news["workspace_temporal"] = {
            "boundary": boundary.isoformat().replace("+00:00", "Z") if boundary else None,
            "since_close_item_ids": since_close_ids,
            "since_close_cluster_ids": since_close_clusters,
            "previous_session_context_item_ids": previous_session_ids,
            "current_driver_item_ids": since_close_ids if boundary else list(current_ids),
            "live_feed_count": len(current_items),
            "pre_market_since_close_count": len(since_close_ids),
            "todays_analysis_current_driver_count": len(since_close_ids if boundary else current_ids),
            "live_assistant_since_close_count": len(since_close_ids),
            "canonical_to_workspace_current_data_loss": 0,
        }
        metrics = news.setdefault("ingestion_metrics", {})
        metrics["canonical_to_workspace_data_loss"] = 0
        metrics["canonical_to_workspace_current_data_loss"] = 0
        diagnostics = news.setdefault("temporal_diagnostics", {})
        diagnostics["workspace"] = dict(news["workspace_temporal"])

    @staticmethod
    def _apply_macro_workspace(macro: dict[str, Any], now: datetime, market_observed: Any) -> None:
        expected = {
            "S&P 500", "NASDAQ", "DOW_JONES", "NIKKEI_225", "HANG_SENG",
            "BRENT_CRUDE", "GOLD", "USD_INR", "DXY", "US_10Y", "GIFT_NIFTY",
        }
        boundary = strict_publication_timestamp(market_observed)
        statuses = dict(macro.get("quote_status") or {})
        valid_quotes: dict[str, dict[str, Any]] = {}
        current_keys: list[str] = []
        since_close_keys: list[str] = []
        stale_keys: list[str] = []
        for key, original in (macro.get("quotes") or {}).items():
            quote = dict(original)
            observation = quote.get("observation_timestamp") or quote.get("published_at")
            assessment = assess_macro_observation(observation, now, str(quote.get("exchange_timezone") or "UTC"))
            quote.update({
                "observation_timestamp": assessment.observation_utc.isoformat().replace("+00:00", "Z") if assessment.observation_utc else "",
                "published_at": assessment.observation_utc.isoformat().replace("+00:00", "Z") if assessment.observation_utc else "",
                "freshness_status": assessment.freshness, "freshness": assessment.freshness,
                "status": assessment.status, "current_eligible": assessment.current_eligible,
                "age_seconds": assessment.age_seconds,
            })
            if assessment.observation_utc is None:
                statuses[str(key)] = {
                    "status": "UNAVAILABLE", "reason": assessment.reason,
                    "source": quote.get("source_name"), "source_symbol": quote.get("source_symbol"),
                }
                continue
            valid_quotes[str(key)] = quote
            statuses[str(key)] = {
                **dict(statuses.get(str(key)) or {}), "status": assessment.status,
                "reason": assessment.reason or None, "freshness": assessment.freshness,
                "observation_timestamp": quote["observation_timestamp"],
            }
            if assessment.current_eligible:
                current_keys.append(str(key))
                if boundary and assessment.observation_utc > boundary:
                    since_close_keys.append(str(key))
            else:
                stale_keys.append(str(key))

        statuses.setdefault("GIFT_NIFTY", {
            "status": "UNAVAILABLE", "reason": "GENUINE_PROVIDER_NOT_CONFIGURED",
            "source": None, "source_symbol": None,
        })
        for key in expected:
            statuses.setdefault(key, {
                "status": "UNAVAILABLE", "reason": "PROVIDER_RETURNED_NO_VALID_QUOTE",
                "source": "Yahoo Finance Public Feed" if key != "GIFT_NIFTY" else None,
                "source_symbol": None,
            })
        macro["quotes"] = valid_quotes
        macro["quote_status"] = statuses
        macro.setdefault("domain_freshness", {})["global_quotes"] = aggregate_quote_freshness(list(valid_quotes.values()))
        unavailable = sorted(key for key in expected if statuses.get(key, {}).get("status") == "UNAVAILABLE")
        compact_order = ["S&P 500", "NASDAQ", "NIKKEI_225", "BRENT_CRUDE", "USD_INR", "US_10Y"]
        macro["workspace_context"] = {
            "market_boundary": boundary.isoformat().replace("+00:00", "Z") if boundary else None,
            "current_context_quote_keys": current_keys,
            "since_india_close_quote_keys": since_close_keys,
            "stale_quote_keys": stale_keys,
            "unavailable_quote_keys": unavailable,
            "critical_external_data_missing": unavailable,
            "nifty_live_quote_keys": [key for key in compact_order if key in current_keys],
            "premarket_850_quote_keys": current_keys,
            "todays_analysis_quote_keys": current_keys,
            "live_assistant_quote_keys": since_close_keys,
            "canonical_quote_count": len(valid_quotes),
            "workspace_quote_count": len(valid_quotes),
            "canonical_to_workspace_data_loss": 0,
        }
        metrics = macro.setdefault("ingestion_metrics", {})
        metrics["canonical_to_workspace_data_loss"] = 0

    @staticmethod
    def _link_released_economic_events(news: dict[str, Any], macro: dict[str, Any]) -> None:
        keyword_map = {
            "CPI": {"cpi", "consumer", "inflation"}, "CORE_CPI": {"cpi", "core", "inflation"},
            "NONFARM_PAYROLLS": {"payroll", "jobs", "employment"}, "GDP": {"gdp", "growth"},
            "FOMC_RATE_DECISION": {"fed", "fomc", "rates"}, "RBI_RATE_DECISION": {"rbi", "repo", "policy"},
            "ECB_RATE_DECISION": {"ecb", "rates"}, "BOJ_RATE_DECISION": {"boj", "rates"},
            "PCE": {"pce", "personal", "inflation"}, "CORE_PCE": {"pce", "core", "inflation"},
            "PPI": {"ppi", "producer", "wholesale"}, "RETAIL_SALES": {"retail", "sales"},
            "INDUSTRIAL_PRODUCTION": {"industrial", "production"},
        }
        released = [event for event in macro.get("economic_events") or [] if event.get("status") == "RELEASED"]
        for cluster in news.get("event_clusters") or []:
            headline = str(cluster.get("canonical_headline") or "").lower()
            cluster_time = WorkstationStateService._parse_time(cluster.get("last_updated"))
            countries = {str(value).lower() for value in cluster.get("related_countries") or []}
            best: tuple[float, str] | None = None
            for event in released:
                scheduled = WorkstationStateService._parse_time(event.get("scheduled_at"))
                if not scheduled or not cluster_time or abs((cluster_time - scheduled).total_seconds()) > 72 * 3600:
                    continue
                terms = keyword_map.get(str(event.get("canonical_event_name") or ""), set())
                if not terms or not (terms & set(headline.replace("/", " ").split())):
                    continue
                country = str(event.get("country") or "").lower()
                if countries and not any(country in value or value in country for value in countries):
                    continue
                distance = abs((cluster_time - scheduled).total_seconds())
                if best is None or distance < best[0]:
                    best = (distance, str(event.get("event_id") or ""))
            if best and best[1]:
                cluster["economic_event_id"] = best[1]

    @staticmethod
    def _parse_time(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    @staticmethod
    def _section(freshness: FreshnessStatus) -> SectionStatus:
        return {FreshnessStatus.FRESH: SectionStatus.READY, FreshnessStatus.STALE: SectionStatus.DEGRADED,
                FreshnessStatus.BLOCKED: SectionStatus.BLOCKED,
                FreshnessStatus.UNAVAILABLE: SectionStatus.UNAVAILABLE,
                FreshnessStatus.MARKET_CLOSED: SectionStatus.MARKET_CLOSED}[freshness]

    @staticmethod
    def _dependent(required: SectionStatus, optional: list[SectionStatus]) -> SectionStatus:
        if required in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}:
            return SectionStatus.BLOCKED
        if required == SectionStatus.MARKET_CLOSED:
            return SectionStatus.MARKET_CLOSED
        return SectionStatus.DEGRADED if any(x != SectionStatus.READY for x in optional) else SectionStatus.READY

    @staticmethod
    def _reasons(*statuses: SectionStatus) -> list[str]:
        names = ("validated market context", "option-chain aggregate", "real news provider")
        return [names[i] for i, status in enumerate(statuses)
                if status in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE}]

    @staticmethod
    def _ready(name: str, status: SectionStatus, reasons: list[str]) -> dict[str, Any]:
        return {"workspace": name, "status": status.value,
                "accessible": name in {"NIFTY Live", "Settings"} or status not in {SectionStatus.BLOCKED, SectionStatus.UNAVAILABLE},
                "dependency_reasons": reasons}
