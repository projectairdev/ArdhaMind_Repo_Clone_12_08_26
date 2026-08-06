import unittest
import datetime
import pandas as pd
from src.data_engine.instruments import InstrumentManager


class TestExpirySelection(unittest.TestCase):
    def setUp(self):
        # Setup a mock instruments dataframe
        today = datetime.date.today()
        # Create some weekly and monthly expiries
        # e.g., 3 consecutive Thursdays
        self.exp1 = today + datetime.timedelta(days=(3 - today.weekday()) % 7)  # Nearest Thursday
        if self.exp1 == today:
            self.exp1 += datetime.timedelta(days=7)
        self.exp2 = self.exp1 + datetime.timedelta(days=7)
        self.exp3 = self.exp2 + datetime.timedelta(days=7)
        
        # Build mock NIFTY options instruments
        rows = []
        for exp in [self.exp1, self.exp2, self.exp3]:
            for strike in [24000.0, 24100.0, 24200.0]:
                for opt_type in ["CE", "PE"]:
                    rows.append({
                        "exchange": "NFO",
                        "segment": "NFO-OPT",
                        "name": "NIFTY",
                        "expiry": exp,
                        "strike": strike,
                        "instrument_type": opt_type,
                        "tradingsymbol": f"NIFTY26{exp.strftime('%m%d')}{int(strike)}{opt_type}",
                    })
        self.instruments_df = pd.DataFrame(rows)

    def test_get_option_expiries(self):
        expiries = InstrumentManager.get_option_expiries(self.instruments_df, "NIFTY")
        self.assertEqual(len(expiries), 3)
        self.assertEqual(expiries[0], self.exp1)

    def test_resolve_nearest_expiry(self):
        nearest = InstrumentManager.resolve_nearest_expiry(self.instruments_df, "NIFTY")
        self.assertEqual(nearest, self.exp1)

    def test_resolve_weekly_vs_monthly_expiry(self):
        # By our definition, the last expiry in a given calendar month is the monthly one,
        # and other expiries in that month are weekly.
        # Let's use future dates (e.g. October 2026) to prevent today's filters from removing any expiries.
        expiries = [
            datetime.date(2026, 10, 1),  # Weekly
            datetime.date(2026, 10, 8),  # Weekly
            datetime.date(2026, 10, 15), # Weekly
            datetime.date(2026, 10, 22), # Weekly
            datetime.date(2026, 10, 29), # Monthly (last Thursday of October 2026)
        ]
        mock_rows = []
        for exp in expiries:
            mock_rows.append({
                "exchange": "NFO",
                "name": "NIFTY",
                "expiry": exp,
                "strike": 24000.0,
                "instrument_type": "CE",
                "tradingsymbol": "MOCK",
            })
        df = pd.DataFrame(mock_rows)
        
        nearest_weekly = InstrumentManager.resolve_weekly_expiry(df, "NIFTY")
        # Nearest weekly is 2026-10-01 (since it is not the max of October)
        self.assertEqual(nearest_weekly, datetime.date(2026, 10, 1))
        
        nearest_monthly = InstrumentManager.resolve_monthly_expiry(df, "NIFTY")
        # Nearest monthly is the last expiry of October -> 2026-10-29
        self.assertEqual(nearest_monthly, datetime.date(2026, 10, 29))


    def test_resolve_atm_strike(self):
        # Strikes available: [24000.0, 24100.0, 24200.0]
        # Spot: 24080 -> ATM should be 24100.0
        atm = InstrumentManager.resolve_atm_strike(self.instruments_df, "NIFTY", 24080.0)
        self.assertEqual(atm, 24100.0)

        # Spot: 24010 -> ATM should be 24000.0
        atm2 = InstrumentManager.resolve_atm_strike(self.instruments_df, "NIFTY", 24010.0)
        self.assertEqual(atm2, 24000.0)

    def test_resolve_strike_step(self):
        # Strikes: [24000.0, 24100.0, 24200.0] -> Difference 100.0
        step = InstrumentManager.resolve_strike_step(self.instruments_df, "NIFTY")
        self.assertEqual(step, 100.0)


if __name__ == "__main__":
    unittest.main()
