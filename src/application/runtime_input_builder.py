from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from src.application.data_quality_service import DataQualityService
from src.application.runtime_inputs import RuntimeInput, RuntimeSnapshot
from src.models.data_quality import FreshnessStatus, QualityStatus, ValueClassification


class RuntimeInputBuilder:
    """Converts one daemon refresh into validated, timestamped immutable inputs."""

    @classmethod
    def from_daemon(cls, market: dict[str, Any] | None, options: dict[str, Any] | None, *,
                    market_state: str, broker_state: str, news: dict[str, Any] | None = None,
                    account: dict[str, Any] | None = None, generated_at: datetime | None = None) -> RuntimeSnapshot:
        now = generated_at or datetime.now(timezone.utc)
        stamp = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        closed = market_state.upper() in {"CLOSED", "POST_MARKET", "HOLIDAY"}
        expired = broker_state.upper() in {"EXPIRED", "TOKEN_EXPIRED", "SESSION_EXPIRED"}
        market = market or {}
        options = options or {}
        mt = cls._timestamp(market)
        ot = cls._timestamp(options)
        market_fresh, _ = DataQualityService.classify("nifty_spot", mt, now=now,
                                                       market_closed=closed, available=bool(market) and not expired)
        option_fresh, _ = DataQualityService.classify("option_aggregate", ot, now=now,
                                                       market_closed=closed, available=bool(options) and not expired)
        market_errors = cls._market_errors(market)
        option_errors = cls._option_errors(options, market)
        def value(source, instrument, observed, freshness, payload, errors=None, classification=ValueClassification.LIVE):
            quality = QualityStatus.INVALID if errors else (QualityStatus.VALID if payload else QualityStatus.UNVERIFIED)
            if freshness == FreshnessStatus.MARKET_CLOSED:
                classification = ValueClassification.HISTORICAL
            if not payload:
                classification = ValueClassification.UNAVAILABLE
            return RuntimeInput(source, instrument, observed, stamp, freshness, quality,
                                classification, payload or None, errors=errors or [])
        unavailable = RuntimeInput("not_integrated", "N/A", None, stamp, FreshnessStatus.UNAVAILABLE,
                                   QualityStatus.UNVERIFIED, ValueClassification.UNAVAILABLE, None)
        return RuntimeSnapshot(
            str(uuid4()), stamp,
            value("market_clock", "NSE", stamp, FreshnessStatus.MARKET_CLOSED if closed else FreshnessStatus.FRESH,
                  {"state": market_state}),
            value("kite_session", "ZERODHA", stamp, FreshnessStatus.BLOCKED if expired else FreshnessStatus.FRESH,
                  {"state": broker_state, "reconnect_required": expired}),
            value("kite_market_feed", "NIFTY 50", mt, market_fresh, market, market_errors),
            unavailable,
            value("kite_market_feed", "INDIA VIX", mt, market_fresh,
                  market.get("india_vix") if market.get("india_vix") is not None else None),
            unavailable,
            value("kite_option_chain", "NIFTY options", ot, option_fresh, options, option_errors,
                  ValueClassification.CALCULATED),
            value("instrument_master", "NIFTY options", ot, option_fresh,
                  {"expiry": options.get("current_weekly_expiry") or options.get("expiry")}
                  if options.get("current_weekly_expiry") or options.get("expiry") else None),
            value("news_provider", "market_news", cls._timestamp(news or {}),
                  FreshnessStatus.FRESH if news else FreshnessStatus.UNAVAILABLE, news),
            value("kite_account", "account", stamp, FreshnessStatus.FRESH, account)
            if account else None,
        )

    @staticmethod
    def _timestamp(value: dict[str, Any]) -> str | None:
        return next((value.get(k) for k in ("observed_at", "observedAt", "timestamp", "lastUpdated") if value.get(k)), None)

    @staticmethod
    def _market_errors(market: dict[str, Any]) -> list[str]:
        spot = market.get("current_spot", market.get("price"))
        return [] if DataQualityService.is_valid_number(spot, positive=True) else ["invalid or missing NIFTY spot"]

    @staticmethod
    def _option_errors(options: dict[str, Any], market: dict[str, Any]) -> list[str]:
        if not options:
            return []
        errors = []
        spot = options.get("underlying_spot")
        market_spot = market.get("current_spot", market.get("price"))
        if not DataQualityService.is_valid_number(spot, positive=True): errors.append("invalid option underlying spot")
        if market_spot and spot and abs(float(spot) - float(market_spot)) > max(5, float(market_spot) * .005):
            errors.append("option underlying inconsistent with market spot")
        if not options.get("current_weekly_expiry") and not options.get("expiry"):
            errors.append("missing option expiry")
        return errors
