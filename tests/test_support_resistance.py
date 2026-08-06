import unittest
import pandas as pd
import numpy as np
from src.indicator_engine.support_resistance import (
    calculate_swing_highs,
    calculate_swing_lows,
    calculate_prev_day_high,
    calculate_prev_day_low,
    calculate_weekly_high,
    calculate_weekly_low,
    calculate_dynamic_support,
    calculate_dynamic_resistance,
)


class TestSupportResistance(unittest.TestCase):
    def setUp(self):
        # Create a mock daily candles dataframe
        dates = pd.date_range(start="2026-06-01", periods=10, freq="D")
        highs = [105, 107, 104, 103, 106, 108, 105, 102, 104, 106]
        lows = [95, 96, 93, 92, 94, 95, 91, 90, 92, 94]
        closes = [100, 101, 98, 97, 102, 103, 99, 95, 98, 101]
        volumes = [1000] * 10
        self.df = pd.DataFrame({
            "date": dates,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes
        })

    def test_swing_highs(self):
        # Highs: [105, 107, 104, 103, 106, 108, 105, 102, 104, 106]
        # index 1 (107) is greater than 105 (left=1) and 104 (right=1)
        # index 5 (108) is greater than 106 (left=1) and 105 (right=1)
        swings = calculate_swing_highs(self.df, left=1, right=1)
        self.assertIn(107.0, swings)
        self.assertIn(108.0, swings)

    def test_swing_lows(self):
        # Lows: [95, 96, 93, 92, 94, 95, 91, 90, 92, 94]
        # index 3 (92) is less than 93 (left=1) and 94 (right=1)
        # index 7 (90) is less than 91 (left=1) and 92 (right=1)
        swings = calculate_swing_lows(self.df, left=1, right=1)
        self.assertIn(92.0, swings)
        self.assertIn(90.0, swings)

    def test_prev_day_high_low(self):
        # Last row high is 106, low is 94
        # Second to last row high is 104, low is 92
        pdh = calculate_prev_day_high(self.df, include_last=False)
        pdl = calculate_prev_day_low(self.df, include_last=False)
        self.assertEqual(pdh, 104.0)
        self.assertEqual(pdl, 92.0)

        pdh_last = calculate_prev_day_high(self.df, include_last=True)
        pdl_last = calculate_prev_day_low(self.df, include_last=True)
        self.assertEqual(pdh_last, 106.0)
        self.assertEqual(pdl_last, 94.0)

    def test_weekly_high_low(self):
        # Last 5 rows: highs [108, 105, 102, 104, 106] -> max 108
        # Last 5 rows: lows [95, 91, 90, 92, 94] -> min 90
        wh = calculate_weekly_high(self.df, lookback_bars=5)
        wl = calculate_weekly_low(self.df, lookback_bars=5)
        self.assertEqual(wh, 108.0)
        self.assertEqual(wl, 90.0)

    def test_dynamic_levels(self):
        # Simply ensure the functions execute and return valid floats
        dyn_s = calculate_dynamic_support(self.df, ema_period=5, atr_period=5)
        dyn_r = calculate_dynamic_resistance(self.df, ema_period=5, atr_period=5)
        self.assertIsInstance(dyn_s, float)
        self.assertIsInstance(dyn_r, float)
        self.assertTrue(dyn_r > dyn_s)


if __name__ == "__main__":
    unittest.main()
