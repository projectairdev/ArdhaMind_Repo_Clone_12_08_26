from __future__ import annotations

from src.models.market_context import MarketContext
from src.models.option_context import OptionContext
from src.models.trade_context import (
    TradeContext,
    SessionContext,
    ExpiryContext,
    MarketReadiness,
    ConfluenceContext,
)
from src.utils import now_str


class TradeContextBuilder:
    """
    Builder orchestrating the creation of the final immutable TradeContext.
    """

    @staticmethod
    def build(
        market: MarketContext,
        options: OptionContext,
        session: SessionContext,
        expiry: ExpiryContext,
        confluence: ConfluenceContext,
        readiness: MarketReadiness,
        schema_version: str = "1.0",
        pipeline_version: str = "1.0",
    ) -> TradeContext:
        """
        Assembles all sub-contexts into a single, immutable, fully-typed TradeContext.
        """
        return TradeContext(
            market=market,
            options=options,
            session=session,
            expiry=expiry,
            confluence=confluence,
            readiness=readiness,
            timestamp=now_str(),
            schema_version=schema_version,
            pipeline_version=pipeline_version,
        )
