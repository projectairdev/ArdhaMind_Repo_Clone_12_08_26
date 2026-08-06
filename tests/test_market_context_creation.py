import unittest
import datetime
import pandas as pd
from src.models import MarketContext
from src.pipeline.market_intelligence_pipeline import MarketIntelligencePipeline


class MockKiteClient:
    """
    Mock Kite Connect API client returning realistic simulated data.
    """
    def quote(self, keys):
        return {
            "NSE:NIFTY 50": {
                "last_price": 24200.50,
                "volume": 2500000,
                "ohlc": {"open": 24100.0, "high": 24250.0, "low": 24080.0, "close": 24120.0},
            },
            "NSE:INDIA VIX": {
                "last_price": 13.50,
            }
        }

    def ltp(self, keys):
        return {
            "NSE:NIFTY 50": {
                "last_price": 24200.50,
            }
        }

    def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False, oi=False):
        dates = pd.date_range(start=from_date, end=to_date, periods=100)
        closes = [24000.0 + i * 2.0 for i in range(100)]
        highs = [c + 50.0 for c in closes]
        lows = [c - 50.0 for c in closes]
        return [
            {
                "date": d,
                "open": c - 10.0,
                "high": h,
                "low": l,
                "close": c,
                "volume": 50000,
            }
            for d, c, h, l in zip(dates, closes, highs, lows)
        ]


class TestMarketContextCreation(unittest.TestCase):
    def setUp(self):
        self.kite = MockKiteClient()
        
        # Build mock NIFTY index and option instruments dataframe
        today = datetime.date.today()
        self.exp = today + datetime.timedelta(days=(3 - today.weekday()) % 7)
        if self.exp == today:
            self.exp += datetime.timedelta(days=7)
            
        rows = [
            {
                "exchange": "NSE",
                "segment": "INDICES",
                "tradingsymbol": "NIFTY 50",
                "name": "NIFTY 50",
                "instrument_token": 256265,
                "expiry": pd.NaT,
                "strike": 0.0,
                "instrument_type": "EQ",
            },
            {
                "exchange": "NFO",
                "segment": "NFO-OPT",
                "tradingsymbol": f"NIFTY26{self.exp.strftime('%m%d')}24200CE",
                "name": "NIFTY",
                "instrument_token": 12345,
                "expiry": self.exp,
                "strike": 24200.0,
                "instrument_type": "CE",
            }
        ]
        self.instruments_df = pd.DataFrame(rows)

    def test_market_intelligence_pipeline_run(self):
        pipeline = MarketIntelligencePipeline()
        context = pipeline.run(self.kite, self.instruments_df)
        
        # Verify MarketContext type and fields
        self.assertIsInstance(context, MarketContext)
        self.assertEqual(context.current_spot, 24200.50)
        self.assertEqual(context.current_expiry, self.exp.strftime("%Y-%m-%d"))
        self.assertEqual(context.india_vix, 13.50)
        self.assertIsInstance(context.support_levels, list)
        self.assertIsInstance(context.resistance_levels, list)
        self.assertTrue(len(context.support_levels) > 0)
        self.assertTrue(len(context.resistance_levels) > 0)
        
        # Volatility & Trend fields
        self.assertIn(context.volatility_state, ["NORMAL", "HIGH", "LOW"])
        self.assertIn(context.market_regime, ["TRENDING", "RANGING", "BREAKOUT", "REVERSAL", "HIGH VOLATILITY", "LOW VOLATILITY"])
        self.assertEqual(context.trend_direction, "BULLISH")
        self.assertTrue(context.trend_strength > 0.0)


if __name__ == "__main__":
    unittest.main()
