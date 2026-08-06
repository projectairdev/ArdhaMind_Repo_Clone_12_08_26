from __future__ import annotations

import datetime
import unittest
from unittest.mock import MagicMock
import pandas as pd

from src.models.option_context import OptionContext
from src.options_engine.chain_builder import build_option_chain, OptionChainContract
from src.options_engine.oi_analysis import analyze_oi, OIAnalysisResult
from src.options_engine.max_pain import calculate_max_pain, MaxPainResult
from src.options_engine.liquidity import analyze_liquidity, LiquiditySummary
from src.options_engine.iv import analyze_iv, IVAnalysisResult, black_scholes_price, calculate_implied_volatility
from src.options_engine.strike_ranker import rank_strikes, RankedStrike
from src.pipeline.option_intelligence_pipeline import OptionIntelligencePipeline


class TestOptionIntelligence(unittest.TestCase):
    def setUp(self):
        # 1. Setup mock spot and expiry
        self.spot_price = 24320.0
        self.today = datetime.date(2026, 10, 1)
        self.expiry_date = datetime.date(2026, 10, 29)  # Last Thursday of Oct 2026
        
        # 2. Setup mock instruments DataFrame
        mock_instruments = []
        self.strikes = [24100.0, 24150.0, 24200.0, 24250.0, 24300.0, 24350.0, 24400.0, 24450.0, 24500.0]
        
        for strike in self.strikes:
            for opt_type in ["CE", "PE"]:
                symbol = f"NIFTY26OCT{int(strike)}{opt_type}"
                mock_instruments.append({
                    "exchange": "NFO",
                    "segment": "NFO",
                    "name": "NIFTY",
                    "tradingsymbol": symbol,
                    "strike": strike,
                    "expiry": self.expiry_date,
                    "instrument_type": opt_type,
                    "lot_size": 75,
                    "instrument_token": hash(symbol) & 0xffffffff
                })
        
        self.instruments_df = pd.DataFrame(mock_instruments)
        
        # 3. Setup mock Kite quotes map
        # Under normal conditions:
        # CE premiums decrease as strikes go up.
        # PE premiums increase as strikes go up.
        # Let's mock realistic values to make calculations pass.
        self.mock_quotes = {}
        for strike in self.strikes:
            # Call details
            ce_symbol = f"NIFTY26OCT{int(strike)}CE"
            ce_ltp = max(5.0, 300.0 - (strike - 24100.0) * 0.8)
            ce_close = ce_ltp * 0.95  # Positive price change (Long Build-up / Short Covering)
            ce_oi = int((25000 - abs(strike - 24300.0) * 50))
            ce_oi_chg = int(ce_oi * 0.1)
            
            self.mock_quotes[f"NFO:{ce_symbol}"] = {
                "last_price": ce_ltp,
                "ohlc": {"close": ce_close},
                "depth": {
                    "buy": [{"price": ce_ltp - 0.1, "quantity": 100}],
                    "sell": [{"price": ce_ltp + 0.1, "quantity": 100}]
                },
                "volume": 20000,
                "oi": ce_oi,
                "oi_change": ce_oi_chg
            }
            
            # Put details
            pe_symbol = f"NIFTY26OCT{int(strike)}PE"
            pe_ltp = max(5.0, 10.0 + (strike - 24100.0) * 0.8)
            pe_close = pe_ltp * 1.05  # Negative price change (Short Build-up / Long Unwinding)
            pe_oi = int((20000 - abs(strike - 24300.0) * 40))
            pe_oi_chg = int(pe_oi * 0.1)
            
            self.mock_quotes[f"NFO:{pe_symbol}"] = {
                "last_price": pe_ltp,
                "ohlc": {"close": pe_close},
                "depth": {
                    "buy": [{"price": pe_ltp - 0.1, "quantity": 100}],
                    "sell": [{"price": pe_ltp + 0.1, "quantity": 100}]
                },
                "volume": 15000,
                "oi": pe_oi,
                "oi_change": pe_oi_chg
            }
            
        # 4. Setup mock Kite connection
        self.mock_kite = MagicMock()
        self.mock_kite.quote.return_value = self.mock_quotes

    def test_chain_builder(self):
        """Verify fetching, normalization, ATM, ITM/OTM, and liquid contract identification."""
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        # Verify normalization and count
        self.assertGreater(len(chain), 0)
        self.assertEqual(len(chain), len(self.strikes) * 2)
        
        # Verify specific contract ATM/ITM/OTM
        # Spot is 24320, strike step is 50, so ATM is 24300
        for c in chain:
            self.assertEqual(c.expiry, "2026-10-29")
            if c.strike == 24300.0:
                self.assertEqual(c.itm_otm, "ATM")
            elif c.instrument_type == "CE":
                if c.strike < 24300.0:
                    self.assertEqual(c.itm_otm, "ITM")
                else:
                    self.assertEqual(c.itm_otm, "OTM")
            elif c.instrument_type == "PE":
                if c.strike > 24300.0:
                    self.assertEqual(c.itm_otm, "ITM")
                else:
                    self.assertEqual(c.itm_otm, "OTM")

    def test_oi_calculations(self):
        """Verify PCR (Put-Call Ratio), Build-ups, and concentrations."""
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        oi_res = analyze_oi(chain)
        
        # Verify PCR OI is Put OI / Call OI
        total_calls_oi = sum(c.oi for c in chain if c.instrument_type == "CE")
        total_puts_oi = sum(c.oi for c in chain if c.instrument_type == "PE")
        expected_pcr = total_puts_oi / total_calls_oi
        self.assertAlmostEqual(oi_res.pcr_oi, expected_pcr, places=3)
        
        # Verify PCR Volume is Put Volume / Call Volume
        total_calls_vol = sum(c.volume for c in chain if c.instrument_type == "CE")
        total_puts_vol = sum(c.volume for c in chain if c.instrument_type == "PE")
        expected_pcr_vol = total_puts_vol / total_calls_vol
        self.assertAlmostEqual(oi_res.pcr_volume, expected_pcr_vol, places=3)
        
        # Verify highest CE / PE OI strikes
        self.assertEqual(oi_res.highest_ce_oi_strike, 24300.0)
        self.assertEqual(oi_res.highest_pe_oi_strike, 24300.0)

    def test_max_pain(self):
        """Verify Option Max Pain strike and pin zone calculations."""
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        max_pain_res = calculate_max_pain(chain)
        
        # Ensure max pain strike is one of our strikes
        self.assertIn(max_pain_res.max_pain_strike, self.strikes)
        self.assertGreater(len(max_pain_res.pain_distribution), 0)
        self.assertIn(max_pain_res.max_pain_strike, max_pain_res.expected_pin_zone)

    def test_liquidity_analysis(self):
        """Verify Spread, volume, and OI scoring plus suitabilities."""
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        liq_summary = analyze_liquidity(chain, atm_strike=24300.0, strike_step=50.0)
        
        self.assertGreaterEqual(liq_summary.overall_liquidity_score, 0.0)
        self.assertLessEqual(liq_summary.overall_liquidity_score, 100.0)
        self.assertGreater(len(liq_summary.contract_metrics), 0)
        
        # Check individual metrics
        first_metric = liq_summary.contract_metrics[0]
        self.assertGreaterEqual(first_metric.volume_score, 0.0)
        self.assertGreaterEqual(first_metric.oi_score, 0.0)
        self.assertGreaterEqual(first_metric.liquidity_score, 0.0)
        self.assertGreaterEqual(first_metric.tradability_score, 0.0)

    def test_implied_volatility(self):
        """Verify Black-Scholes pricing, ATM IV, and Expected Move calculations."""
        # 1. Test standard Black-Scholes price
        # S=100, K=100, T=1, r=0.05, sigma=0.2 (20% IV)
        call_price = black_scholes_price(S=100.0, K=100.0, T=1.0, r=0.05, sigma=0.2, option_type="CE")
        self.assertGreater(call_price, 0.0)
        
        # 2. Test Implied Volatility calculation from premium
        calculated_iv = calculate_implied_volatility(price=call_price, S=100.0, K=100.0, T=1.0, r=0.05, option_type="CE")
        self.assertAlmostEqual(calculated_iv, 20.0, delta=0.5)

        # 3. Test chain-wide IV analysis
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        iv_res = analyze_iv(chain, self.spot_price, atm_strike=24300.0, expiry_date=self.expiry_date, today_date=self.today)
        self.assertGreater(iv_res.atm_iv, 0.0)
        self.assertGreater(iv_res.expected_move, 0.0)
        self.assertIn(iv_res.iv_classification, ["LOW", "NORMAL", "HIGH", "EXTREME"])

    def test_strike_ranking(self):
        """Verify RankStrike objects and proper multi-factor sorting."""
        chain = build_option_chain(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            symbol="NIFTY",
            expiry=self.expiry_date,
            spot_price=self.spot_price
        )
        
        liq_res = analyze_liquidity(chain, atm_strike=24300.0, strike_step=50.0)
        iv_res = analyze_iv(chain, self.spot_price, atm_strike=24300.0, expiry_date=self.expiry_date, today_date=self.today)
        
        ranked = rank_strikes(chain, liq_res, iv_res, atm_strike=24300.0)
        
        self.assertGreater(len(ranked), 0)
        # Verify sorting is descending by score
        scores = [r.ranking_score for r in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        # Verify rank field incrementing
        ranks = [r.rank for r in ranked]
        self.assertEqual(ranks, list(range(1, len(ranked) + 1)))

    def test_pipeline_assembly(self):
        """Verify OptionIntelligencePipeline runs successfully and outputs a valid immutable OptionContext."""
        pipeline = OptionIntelligencePipeline()
        
        opt_ctx = pipeline.run(
            kite=self.mock_kite,
            instruments_df=self.instruments_df,
            spot_price=self.spot_price,
            expiry_date=self.expiry_date
        )
        
        self.assertIsInstance(opt_ctx, OptionContext)
        self.assertEqual(opt_ctx.underlying_spot, self.spot_price)
        self.assertEqual(opt_ctx.atm_strike, 24300.0)
        self.assertEqual(opt_ctx.strike_step, 50.0)
        self.assertGreater(opt_ctx.atm_iv, 0.0)
        self.assertGreater(opt_ctx.expected_move, 0.0)
        self.assertGreater(opt_ctx.max_pain, 0.0)
        self.assertIn(opt_ctx.market_option_bias, ["BULLISH", "BEARISH", "NEUTRAL"])
        self.assertEqual(opt_ctx.schema_version, "1.0")
        self.assertEqual(opt_ctx.pipeline_version, "1.0")
        self.assertIsNotNone(opt_ctx.timestamp)
