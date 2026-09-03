from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional, Tuple

from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot
from src.market_data.models.canonical_tick import CanonicalTick
from src.market_data.models.quality_enums import DataQualityStatus
from src.market_data.session.session_authority import (
    CanonicalSessionAuthority,
    MarketPhase,
    SessionContext,
)


@dataclass(frozen=True)
class SessionValidationResult:
    is_valid: bool
    status: DataQualityStatus
    reason: Optional[str] = None


class SessionValidator:
    """
    Validates incoming market data against CanonicalSessionAuthority.
    Prevents cross-session contamination and enforces strict trading-calendar invariants.
    """

    def __init__(self, session_authority: CanonicalSessionAuthority) -> None:
        self.session_authority = session_authority

    def validate_tick(
        self,
        tick: CanonicalTick,
        reference_time: Optional[datetime] = None,
    ) -> SessionValidationResult:
        """Validates incoming CanonicalTick against current session context."""
        ctx = self.session_authority.evaluate_session(reference_time)

        # 1. Check if tick timestamp is in the future
        now_ist = ctx.observed_at
        if tick.exchange_timestamp > now_ist + timedelta(seconds=60):
            return SessionValidationResult(
                is_valid=False,
                status=DataQualityStatus.REJECTED,
                reason=f"Tick exchange_timestamp {tick.exchange_timestamp} is in the future relative to {now_ist}",
            )

        # 2. Check session date alignment
        if ctx.market_phase in (MarketPhase.PRE_MARKET, MarketPhase.PRE_OPEN, MarketPhase.MARKET_OPEN, MarketPhase.POST_MARKET):
            expected_session = ctx.active_trading_date
            if tick.session_date != expected_session:
                return SessionValidationResult(
                    is_valid=False,
                    status=DataQualityStatus.SESSION_MISMATCH,
                    reason=f"Tick session_date {tick.session_date} does not match active session {expected_session}",
                )
        else:
            # Market is closed: ticks should match completed session date or upcoming date
            expected_session = ctx.completed_session_date
            if tick.session_date not in (expected_session, ctx.next_trading_date):
                return SessionValidationResult(
                    is_valid=False,
                    status=DataQualityStatus.SESSION_MISMATCH,
                    reason=f"Off-market tick session_date {tick.session_date} does not match completed session {expected_session}",
                )

        return SessionValidationResult(is_valid=True, status=DataQualityStatus.VALID)

    def validate_candle(
        self,
        candle: CanonicalCandle,
        reference_time: Optional[datetime] = None,
    ) -> SessionValidationResult:
        """Validates CanonicalCandle session date and timestamp bounds."""
        ctx = self.session_authority.evaluate_session(reference_time)

        if candle.session_date > ctx.calendar_date:
            return SessionValidationResult(
                is_valid=False,
                status=DataQualityStatus.REJECTED,
                reason=f"Candle session_date {candle.session_date} is in the future",
            )

        # If it's a closed past session, it must be on a known trading day
        if candle.session_date < ctx.calendar_date:
            if not self.session_authority.calendar.is_trading_day(candle.session_date):
                return SessionValidationResult(
                    is_valid=False,
                    status=DataQualityStatus.SESSION_MISMATCH,
                    reason=f"Candle session_date {candle.session_date} is not a valid exchange trading day",
                )

        return SessionValidationResult(is_valid=True, status=DataQualityStatus.VALID)

    def validate_option_chain(
        self,
        chain: CanonicalOptionChainSnapshot,
        reference_time: Optional[datetime] = None,
    ) -> SessionValidationResult:
        """Validates CanonicalOptionChainSnapshot session date."""
        ctx = self.session_authority.evaluate_session(reference_time)

        if chain.session_date > ctx.calendar_date:
            return SessionValidationResult(
                is_valid=False,
                status=DataQualityStatus.REJECTED,
                reason=f"Option chain session_date {chain.session_date} is in the future",
            )

        return SessionValidationResult(is_valid=True, status=DataQualityStatus.VALID)
