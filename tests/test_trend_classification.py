import unittest
import pandas as pd
from src.indicator_engine.trend_strength import analyze_trend
from src.indicator_engine.volatility_state import calculate_volatility_state, VolatilitySnapshot
from src.indicator_engine.market_regime import classify_market_regime


class TestTrendAndRegime(unittest.TestCase):
    def setUp(self):
        # Create mock daily candles dataframe
        dates = pd.date_range(start="2026-06-01", periods=100, freq="D")
        
        # 1. Bullish stacking trend
        closes_bullish = [100.0 + i * 1.5 for i in range(100)]
        highs_bullish = [c + 2.0 for c in closes_bullish]
        lows_bullish = [c - 2.0 for c in closes_bullish]
        self.df_bullish = pd.DataFrame({
            "date": dates,
            "high": highs_bullish,
            "low": lows_bullish,
            "close": closes_bullish,
            "volume": [1000 + i * 10 for i in range(100)]
        })

        # 2. Sideways trend
        closes_sideways = [100.0 for _ in range(100)]
        highs_sideways = [c + 1.0 for c in closes_sideways]
        lows_sideways = [c - 1.0 for c in closes_sideways]
        self.df_sideways = pd.DataFrame({
            "date": dates,
            "high": highs_sideways,
            "low": lows_sideways,
            "close": closes_sideways,
            "volume": [1000] * 100
        })

    def test_trend_bullish(self):
        snapshot = analyze_trend(self.df_bullish, "NIFTY")
        self.assertEqual(snapshot.trend, "BULLISH")
        self.assertTrue(snapshot.trend_strength_score > 50.0)
        self.assertEqual(snapshot.ema_alignment, "BULLISH")

    def test_trend_sideways(self):
        snapshot = analyze_trend(self.df_sideways, "NIFTY")
        self.assertEqual(snapshot.trend, "SIDEWAYS")
        self.assertEqual(snapshot.ema_alignment, "MIXED")

    def test_regime_classification(self):
        # Create TrendSnapshot and VolatilitySnapshot to classify regimes
        dates = pd.date_range(start="2026-06-01", periods=50, freq="D")
        closes = [100.0] * 50
        df = pd.DataFrame({
            "date": dates,
            "high": [c + 1.0 for c in closes],
            "low": [c - 1.0 for c in closes],
            "close": closes,
            "volume": [1000] * 50
        })
        
        trend_snapshot = analyze_trend(df, "NIFTY")
        vol_snapshot = calculate_volatility_state(df)
        
        # Default state with flat data should be RANGING or LOW VOLATILITY
        regime = classify_market_regime(trend_snapshot, vol_snapshot)
        self.assertIn(regime, ["RANGING", "LOW VOLATILITY"])


if __name__ == "__main__":
    unittest.main()
