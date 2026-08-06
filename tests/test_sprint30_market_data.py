from __future__ import annotations
import os
import unittest
from datetime import datetime, timedelta, date
from unittest.mock import MagicMock, patch

from src.broker.services.instrument_service import InstrumentService
from src.broker.utils.cache_manager import InstrumentCacheManager
from src.broker.services.market_status_service import MarketStatusService, MarketStatusReport
from src.broker.utils.data_validation import MarketDataValidator, DataValidationItem
from src.broker.services.broker_service import BrokerService
from src.broker.models.quote import QuoteModel, LTPModel
from src.broker.models.candle import CandleModel

class TestSprint30MarketData(unittest.TestCase):
    """
    Comprehensive test suite validating the market data integration features from Sprint 30:
    1. Instrument Master and Cache Manager
    2. Market Status and Session/Holiday Service
    3. Data Validation (OHLC, timestamps, negative volume, invalid tokens)
    4. BrokerService high-level immutable wrappers
    """

    def setUp(self) -> None:
        # Clear the SQLite database between tests for isolation
        if os.path.exists("cache/instruments.db"):
            try:
                os.remove("cache/instruments.db")
            except Exception:
                pass

    def tearDown(self) -> None:
        if os.path.exists("cache/instruments.db"):
            try:
                os.remove("cache/instruments.db")
            except Exception:
                pass

    def test_instrument_cache_manager_save_and_load(self):
        """Verifies SQLite cache saving, loading, exists, age, and validation."""
        broker = "ZERODHA"
        instruments = [
            {
                "instrument_token": 256265,
                "exchange_token": 1001,
                "tradingsymbol": "NIFTY26JUL22000CE",
                "name": "NIFTY 50",
                "last_price": 0.0,
                "expiry": "2026-07-26",
                "strike": 22000.0,
                "tick_size": 0.05,
                "lot_size": 50,
                "instrument_type": "CE",
                "segment": "NFO-OPT",
                "exchange": "NFO"
            }
        ]

        # Initially, cache should not exist
        self.assertFalse(InstrumentCacheManager.cache_exists(broker))
        self.assertIsNone(InstrumentCacheManager.load_cache(broker))

        # Save to cache
        save_ok = InstrumentCacheManager.save_cache(broker, instruments)
        self.assertTrue(save_ok)

        # Cache should now exist
        self.assertTrue(InstrumentCacheManager.cache_exists(broker))

        # Load from cache
        loaded = InstrumentCacheManager.load_cache(broker)
        self.assertIsNotNone(loaded)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["tradingsymbol"], "NIFTY26JUL22000CE")
        self.assertEqual(loaded[0]["strike"], 22000.0)

        # Validate cache status (should be VALID)
        self.assertTrue(InstrumentCacheManager.cache_validation(broker))

        # Cache age should be very close to 0
        self.assertEqual(InstrumentCacheManager.cache_age(broker), 0.0)

        # Invalidate cache
        InstrumentCacheManager.invalidate_cache(broker)
        self.assertFalse(InstrumentCacheManager.cache_validation(broker))

    def test_instrument_service_lookups(self):
        """Verifies InstrumentService master synchronization and lookup functions."""
        mock_gateway = MagicMock()
        mock_gateway.get_instruments.return_value = [
            {
                "instrument_token": 256265,
                "exchange_token": 1001,
                "tradingsymbol": "NIFTY26JUL22000CE",
                "name": "NIFTY",
                "last_price": 0.0,
                "expiry": "2026-07-26",
                "strike": 22000.0,
                "tick_size": 0.05,
                "lot_size": 50,
                "instrument_type": "CE",
                "segment": "NFO-OPT",
                "exchange": "NFO"
            },
            {
                "instrument_token": 256001,
                "exchange_token": 1002,
                "tradingsymbol": "NIFTY 50",
                "name": "NIFTY 50",
                "last_price": 0.0,
                "expiry": None,
                "strike": 0.0,
                "tick_size": 0.0,
                "lot_size": 0,
                "instrument_type": "EQ",
                "segment": "NSE-INDICES",
                "exchange": "NSE"
            }
        ]

        # Create mock broker service
        mock_broker_service = MagicMock()
        mock_broker_service.get_instruments.return_value = mock_gateway.get_instruments.return_value
        mock_broker_service.trading_mode = None  # Use MOCK

        # Get service instance and load instruments
        inst_service = InstrumentService.get_instance()
        loaded_ok = inst_service.load_instruments(mock_broker_service, force_refresh=True)
        self.assertTrue(loaded_ok)

        # Query by token
        inst1 = inst_service.lookup_instrument_by_token(256265)
        self.assertIsNotNone(inst1)
        self.assertEqual(inst1["tradingsymbol"], "NIFTY26JUL22000CE")

        # Query by symbol
        inst2 = inst_service.lookup_instrument_by_symbol("NIFTY 50")
        self.assertIsNotNone(inst2)
        self.assertEqual(inst2["instrument_token"], 256001)

        # Option contract search
        opt = inst_service.lookup_option_type(
            name="NIFTY",
            expiry="2026-07-26",
            strike=22000.0,
            option_type="CE"
        )
        self.assertIsNotNone(opt)
        self.assertEqual(opt["instrument_token"], 256265)

    def test_market_status_service_calculations(self):
        """Verifies session calculations in Indian Standard Time (IST)."""
        service = MarketStatusService()

        # Test case 1: 2026-07-11 13:00:00 UTC -> Saturday -> Holiday
        sat_utc = datetime(2026, 7, 11, 13, 0, 0)
        report_sat = service.get_market_status(sat_utc)
        self.assertFalse(report_sat.is_trading_day)
        self.assertTrue(report_sat.is_holiday)
        self.assertEqual(report_sat.status, "HOLIDAY")

        # Test case 2: Monday 2026-07-13 04:30:00 UTC -> 10:00:00 IST -> OPEN
        mon_open_utc = datetime(2026, 7, 13, 4, 30, 0)
        report_mon_open = service.get_market_status(mon_open_utc)
        self.assertTrue(report_mon_open.is_trading_day)
        self.assertFalse(report_mon_open.is_holiday)
        self.assertEqual(report_mon_open.status, "OPEN")
        # 10:00:00 IST to 15:30:00 IST is 5.5 hours = 19800 seconds
        self.assertEqual(report_mon_open.remaining_seconds, 19800.0)

        # Test case 3: Monday 2026-07-13 03:35:00 UTC -> 09:05:00 IST -> PRE_OPEN
        mon_pre_utc = datetime(2026, 7, 13, 3, 35, 0)
        report_mon_pre = service.get_market_status(mon_pre_utc)
        self.assertEqual(report_mon_pre.status, "PRE_OPEN")
        # 09:05:00 IST to 09:15:00 IST is 10 mins = 600 seconds
        self.assertEqual(report_mon_pre.remaining_seconds, 600.0)

        # Test case 4: Monday 2026-07-13 10:15:00 UTC -> 15:45:00 IST -> POST_CLOSE
        mon_post_utc = datetime(2026, 7, 13, 10, 15, 0)
        report_mon_post = service.get_market_status(mon_post_utc)
        self.assertEqual(report_mon_post.status, "POST_CLOSE")
        # 15:45:00 IST to 16:00:00 IST is 15 mins = 900 seconds
        self.assertEqual(report_mon_post.remaining_seconds, 900.0)

    def test_market_data_validator_quotes(self):
        """Verifies that invalid quotes (prices, negative volume, incorrect OHLC) are flagged."""
        # Good quote
        good_quotes = {
            "NSE:RELIANCE": {
                "instrument_token": 738561,
                "last_price": 2450.5,
                "volume": 1200000,
                "ohlc": {
                    "open": 2430.0,
                    "high": 2465.0,
                    "low": 2425.0,
                    "close": 2445.0
                }
            }
        }
        report_good = MarketDataValidator.validate_quotes(good_quotes)
        self.assertTrue(report_good.is_valid)
        self.assertEqual(len(report_good.errors), 0)

        # Bad quote (OHLC inconsistency: Low > Close, Negative Volume, Non-positive Price)
        bad_quotes = {
            "NSE:INFY": {
                "instrument_token": 408065,
                "last_price": -1500.0,  # Negative last price
                "volume": -500,        # Negative volume
                "ohlc": {
                    "open": 1490.0,
                    "high": 1510.0,
                    "low": 1530.0,     # Low is greater than High and Open
                    "close": 1480.0
                }
            }
        }
        report_bad = MarketDataValidator.validate_quotes(bad_quotes)
        self.assertFalse(report_bad.is_valid)
        self.assertGreater(len(report_bad.errors), 0)
        
        err_types = [err.error_type for err in report_bad.errors]
        self.assertIn("INVALID_PRICE", err_types)
        self.assertIn("NEGATIVE_VOLUME", err_types)
        self.assertIn("OHLC_INCONSISTENCY", err_types)

    def test_market_data_validator_candles(self):
        """Verifies that historical candles (ordering, duplicate timestamps, missing blocks) are validated."""
        good_candles = [
            {"date": "2026-07-13 09:15:00", "open": 100.0, "high": 105.0, "low": 99.0, "close": 102.0, "volume": 1000},
            {"date": "2026-07-13 09:16:00", "open": 102.0, "high": 103.0, "low": 101.0, "close": 101.5, "volume": 500}
        ]
        report_good = MarketDataValidator.validate_historical_candles(good_candles, instrument_token=123)
        self.assertTrue(report_good.is_valid)

        # Bad candles (Duplicate timestamp and ordering violation)
        bad_candles = [
            {"date": "2026-07-13 09:15:00", "open": 100.0, "high": 105.0, "low": 99.0, "close": 102.0, "volume": 1000},
            {"date": "2026-07-13 09:15:00", "open": 102.0, "high": 103.0, "low": 101.0, "close": 101.5, "volume": 500}
        ]
        report_bad = MarketDataValidator.validate_historical_candles(bad_candles, instrument_token=123)
        self.assertFalse(report_bad.is_valid)
        err_types = [err.error_type for err in report_bad.errors]
        self.assertIn("DUPLICATE_CANDLE", err_types)

    def test_broker_service_immutable_wrappers(self):
        """Verifies BrokerService wrappers cleanly map raw broker returns to immutable models."""
        mock_gateway = MagicMock()
        mock_gateway.get_quote.return_value = {
            "NSE:SBIN": {
                "instrument_token": 779521,
                "last_price": 612.4,
                "volume": 2500000,
                "last_trade_time": "2026-07-13 15:29:55",
                "ohlc": {
                    "open": 605.0,
                    "high": 615.0,
                    "low": 602.0,
                    "close": 610.0
                }
            }
        }
        mock_gateway.get_ltp.return_value = {
            "NSE:SBIN": {
                "instrument_token": 779521,
                "last_price": 612.4
            }
        }
        mock_gateway.get_historical_data.return_value = [
            {"date": "2026-07-13 15:00:00", "open": 611.0, "high": 613.0, "low": 610.5, "close": 612.4, "volume": 15000}
        ]

        broker_service = BrokerService.get_instance()
        with patch.object(broker_service, "_gateway", mock_gateway):
            # Test get_quotes
            quotes = broker_service.get_quotes(["NSE:SBIN"])
            self.assertIn("NSE:SBIN", quotes)
            q_model = quotes["NSE:SBIN"]
            self.assertIsInstance(q_model, QuoteModel)
            self.assertEqual(q_model.symbol, "NSE:SBIN")
            self.assertEqual(q_model.last_price, 612.4)
            self.assertEqual(q_model.ohlc.high, 615.0)

            # Test get_ltp_models
            ltps = broker_service.get_ltp_models(["NSE:SBIN"])
            self.assertIn("NSE:SBIN", ltps)
            ltp_model = ltps["NSE:SBIN"]
            self.assertIsInstance(ltp_model, LTPModel)
            self.assertEqual(ltp_model.last_price, 612.4)

            # Test get_historical_candle_models
            candles = broker_service.get_historical_candle_models(779521, None, None, "15minute")
            self.assertEqual(len(candles), 1)
            c_model = candles[0]
            self.assertIsInstance(c_model, CandleModel)
            self.assertEqual(c_model.close, 612.4)
            self.assertEqual(c_model.volume, 15000)
