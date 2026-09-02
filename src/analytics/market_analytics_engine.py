from __future__ import annotations

from datetime import date, datetime, timezone
import logging
from typing import Optional, Sequence

from src.analytics.breadth.breadth_engine import MarketBreadthEngine
from src.analytics.breadth.models import ConstituentState, MarketBreadthContext
from src.analytics.options.models import OptionsConfirmationContext
from src.analytics.options.options_intelligence_engine import OptionsIntelligenceEngine
from src.analytics.price_structure.models import PriceStructureContext
from src.analytics.price_structure.price_structure_engine import PriceStructureEngine
from src.analytics.regime.market_regime_engine import MarketRegimeEngine
from src.analytics.regime.models import RegimeContext
from src.analytics.snapshot.analytics_snapshot import MarketAnalyticsSnapshot
from src.market_data.models.canonical_candle import CanonicalCandle
from src.market_data.models.canonical_option_chain import CanonicalOptionChainSnapshot
from src.market_data.models.quality_enums import DataQualityStatus, Timeframe
from src.market_data.services.candle_engine import CanonicalCandleEngine
from src.market_data.session.session_authority import CanonicalSessionAuthority
from src.market_data.state.live_market_state import LiveMarketState

logger = logging.getLogger(__name__)


class MarketAnalyticsEngine:
    """
    Deterministic provider-independent coordinator for all core market analytics.
    Constructs immutable MarketAnalyticsSnapshot directly from canonical state.
    """

    def __init__(
        self,
        live_market_state: LiveMarketState,
        candle_engine: CanonicalCandleEngine,
        session_authority: Optional[CanonicalSessionAuthority] = None,
    ) -> None:
        self.state_store = live_market_state
        self.candle_engine = candle_engine
        self.session_authority = session_authority or CanonicalSessionAuthority()

    def generate_snapshot(
        self,
        option_snapshot: Optional[CanonicalOptionChainSnapshot] = None,
        constituents: Optional[Sequence[ConstituentState]] = None,
        nifty_id: str = "IDX:NSE:NIFTY_50",
        vix_id: str = "IDX:NSE:INDIA_VIX",
    ) -> MarketAnalyticsSnapshot:
        """Computes and returns a comprehensive, immutable MarketAnalyticsSnapshot."""
        now_utc = datetime.now(timezone.utc)
        sess_ctx = self.session_authority.evaluate_session()
        sess_date = sess_ctx.active_trading_date or sess_ctx.completed_session_date

        nifty_state = self.state_store.get_instrument_state(nifty_id)
        vix_state = self.state_store.get_instrument_state(vix_id)
        vix_price = vix_state.last_price if vix_state else None

        candles_1m = self.candle_engine.get_candles(nifty_id, Timeframe.M1)

        # 1. Price Structure Analysis
        price_structure = PriceStructureEngine.analyze(
            instrument_state=nifty_state,
            intraday_candles_1m=candles_1m,
        )

        # 2. Market Breadth Analysis
        nifty_chg_pct = nifty_state.change_pct if nifty_state and nifty_state.change_pct is not None else 0.0
        breadth_ctx = MarketBreadthEngine.analyze(
            constituents=constituents or [],
            index_change_pct=nifty_chg_pct,
        )

        # 3. Options Intelligence Analysis
        options_ctx = OptionsIntelligenceEngine.analyze(option_snapshot)

        # 4. Market Regime Analysis
        regime_ctx = MarketRegimeEngine.classify_regime(
            price_structure=price_structure,
            breadth_context=breadth_ctx,
            options_context=options_ctx,
            vix_price=vix_price,
        )

        # Overall Quality Resolution
        overall_quality = DataQualityStatus.VALID
        if price_structure.quality == DataQualityStatus.UNAVAILABLE or nifty_state is None:
            overall_quality = DataQualityStatus.UNAVAILABLE
        elif breadth_ctx.quality == DataQualityStatus.DELAYED or options_ctx.quality == DataQualityStatus.UNAVAILABLE:
            overall_quality = DataQualityStatus.DELAYED

        return MarketAnalyticsSnapshot(
            session_date=sess_date,
            captured_at=now_utc,
            price_structure=price_structure,
            market_breadth=breadth_ctx,
            options_intelligence=options_ctx,
            market_regime=regime_ctx,
            vix_price=vix_price,
            state_revision=self.state_store.state_revision,
            quality=overall_quality,
        )
