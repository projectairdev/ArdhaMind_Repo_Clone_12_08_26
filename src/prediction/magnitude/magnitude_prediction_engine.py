from __future__ import annotations

from typing import Optional

from src.analytics.price_structure.models import ATRContext, CompressionContext
from src.prediction.models.prediction_models import MagnitudeDistribution


class MagnitudePredictionEngine:
    """
    Deterministic magnitude prediction engine.
    Computes move magnitude distribution strictly from volatility and range context,
    preventing overprediction when direction signals are strong but volatility is subdued.
    """

    @staticmethod
    def infer_magnitude(
        atr_context: ATRContext,
        compression_context: CompressionContext,
        vix_price: Optional[float] = None,
        base_historical_range: float = 120.0,
    ) -> MagnitudeDistribution:
        """Computes discrete magnitude bucket probabilities and expected move."""
        atr = atr_context.atr_value if atr_context.atr_value > 0 else 80.0
        vix = vix_price if (vix_price and vix_price > 0) else 13.5

        # Normalization factor relative to baseline ATR (100 pts) and VIX (14.0)
        vol_scalar = (atr / 100.0) * (vix / 14.0)
        if compression_context.is_compressing:
            vol_scalar *= 0.75  # Squeeze dampens immediate expected magnitude

        vol_scalar = max(0.4, min(2.5, vol_scalar))

        # Baseline probability weights:
        # Typical NIFTY intraday range distribution
        if vol_scalar < 0.70:  # Low volatility / compression
            p0 = 0.45
            p1 = 0.35
            p2 = 0.12
            p3 = 0.05
            p4 = 0.03
            exp_mag = round(45.0 * vol_scalar, 1)
            med_mag = 40.0
            lower_band = 25.0
            upper_band = 75.0
        elif vol_scalar > 1.30:  # High volatility / expansion
            p0 = 0.10
            p1 = 0.20
            p2 = 0.30
            p3 = 0.25
            p4 = 0.15
            exp_mag = round(135.0 * vol_scalar, 1)
            med_mag = 125.0
            lower_band = 80.0
            upper_band = 220.0
        else:  # Normal volatility
            p0 = 0.20
            p1 = 0.40
            p2 = 0.25
            p3 = 0.10
            p4 = 0.05
            exp_mag = round(85.0 * vol_scalar, 1)
            med_mag = 80.0
            lower_band = 50.0
            upper_band = 140.0

        # Enforce exact 1.00 sum
        total_p = p0 + p1 + p2 + p3 + p4
        p0 = round(p0 / total_p, 2)
        p1 = round(p1 / total_p, 2)
        p2 = round(p2 / total_p, 2)
        p3 = round(p3 / total_p, 2)
        p4 = round(1.0 - (p0 + p1 + p2 + p3), 2)

        return MagnitudeDistribution(
            p_0_50=p0,
            p_50_100=p1,
            p_100_150=p2,
            p_150_200=p3,
            p_200_plus=p4,
            expected_magnitude=exp_mag,
            median_magnitude=med_mag,
            lower_band_pts=lower_band,
            upper_band_pts=upper_band,
        )
