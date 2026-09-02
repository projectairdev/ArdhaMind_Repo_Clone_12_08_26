from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from src.analytics.breadth.models import MarketBreadthContext
from src.analytics.options.models import OptionsConfirmationContext
from src.analytics.price_structure.models import PriceStructureContext
from src.analytics.regime.models import RegimeContext
from src.market_data.models.quality_enums import DataQualityStatus


@dataclass(frozen=True)
class MarketAnalyticsSnapshot:
    """
    Authoritative, immutable market intelligence snapshot.
    The primary input container for future calibration and decision layers.
    """
    session_date: date
    captured_at: datetime
    price_structure: PriceStructureContext
    market_breadth: MarketBreadthContext
    options_intelligence: OptionsConfirmationContext
    market_regime: RegimeContext
    vix_price: Optional[float]
    state_revision: int = 1
    quality: DataQualityStatus = DataQualityStatus.VALID

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None:
            raise ValueError("MarketAnalyticsSnapshot 'captured_at' must be timezone-aware.")
