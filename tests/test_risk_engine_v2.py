from __future__ import annotations

import unittest
from src.models import (
    TradeCandidate,
    OptionContext,
    CandidateConfidence,
    ConfidenceReport,
    TradePlan,
    SessionContext,
    ExpiryContext,
    ConfluenceContext,
    MarketReadiness,
    TradeContext,
    MarketContext,
    MarketScore,
    TrendScore,
    OptionScore,
    VolatilityScore,
    LiquidityScore,
    SessionScore,
    ExpiryScore,
    ConfluenceScore,
    RiskEngineConfig,
    CandidateRisk,
    RiskReport,
    CapitalAllocation,
    RiskWarning,
    ExposureSummary,
    PortfolioConstraint,
    RiskSummary,
)
from src.risk_engine_v2.allocation import (
    get_option_premium,
    get_option_lot_size,
    calculate_allocation,
    determine_risk_grade,
)
from src.risk_engine_v2.constraints import evaluate_candidate_constraints
from src.risk_engine_v2.exposure import calculate_portfolio_exposures
from src.risk_engine_v2.warnings import generate_portfolio_warnings
from src.risk_engine_v2.portfolio import apply_portfolio_level_limits
from src.risk_engine_v2.builder import RiskBuilder
from src.pipeline.risk_pipeline import RiskPipeline


class TestRiskEngineV2(unittest.TestCase):
    def setUp(self):
        # 1. Option Context Setup
        self.option_context = OptionContext(
            underlying_spot=24320.0,
            atm_strike=24300.0,
            strike_step=50.0,
            current_weekly_expiry="2026-10-29",
            current_monthly_expiry="2026-10-29",
            time_to_expiry=3.0,
            atm_iv=16.0,
            expected_move=350.0,
            pcr=1.2,
            max_pain=24300.0,
            highest_call_oi=100000.0,
            highest_put_oi=120000.0,
            highest_call_oi_change=1000.0,
            highest_put_oi_change=1200.0,
            support_strikes=[24200.0, 24100.0],
            resistance_strikes=[24400.0, 24500.0],
            liquidity_metrics={
                "overall_liquidity_score": 85.0,
                "average_spread_pct": 0.12,
            },
            option_chain_summary={
                "total_calls_oi": 500000.0,
                "total_puts_oi": 600000.0,
            },
            top_candidate_strikes=[
                {
                    "tradingsymbol": "NIFTY26OCT24300CE",
                    "strike": 24300.0,
                    "instrument_type": "CE",
                    "option_ltp": 120.0,
                    "lot_size": 50,
                },
                {
                    "tradingsymbol": "NIFTY26OCT24350CE",
                    "strike": 24350.0,
                    "instrument_type": "CE",
                    "option_ltp": 90.0,
                    "lot_size": 50,
                },
                {
                    "tradingsymbol": "BANKNIFTY26OCT52000CE",
                    "strike": 52000.0,
                    "instrument_type": "CE",
                    "option_ltp": 350.0,
                    "lot_size": 15,
                }
            ],
            market_option_bias="BULLISH"
        )

        # 2. Unified Trade Context Setup
        self.market_ctx = MarketContext(
            current_spot=24320.0,
            timestamp="2026-07-09 10:30:00",
            trading_session="MORNING",
            current_expiry="2026-10-29",
            market_regime="BULLISH",
            trend_direction="UP",
            trend_strength=75.0,
            support_levels=[24100.0, 24200.0],
            resistance_levels=[24500.0, 24600.0],
            vwap=24300.0,
            atr=150.0,
            india_vix=15.0,
            volatility_state="NORMAL"
        )
        self.session_ctx = SessionContext(
            session_type="MORNING",
            is_tradable_time=True,
            time_of_day="10:30:00",
            is_weekend=False,
            is_holiday=False,
            is_half_day=False,
        )
        self.expiry_ctx = ExpiryContext(
            expiry_date="2026-10-29",
            days_remaining=3,
            expiry_type="WEEKLY",
            is_expiry_day=False,
            is_expiry_eve=False,
            is_far_expiry=False,
            classification="WEEKLY_EXPIRY"
        )
        self.confluence_ctx = ConfluenceContext(
            trend_confluence=True,
            option_confluence=True,
            sr_alignment=True,
            volatility_alignment=True,
            liquidity_alignment=True,
            overall_confluence=True,
            description="Aligned trend structure"
        )
        self.readiness_ctx = MarketReadiness(
            is_market_ready=True,
            suitability_score=100.0,
            reasons=[],
            session_suitable=True,
            volatility_suitable=True,
            liquidity_suitable=True,
            trend_suitable=True,
        )
        self.trade_context = TradeContext(
            market=self.market_ctx,
            options=self.option_context,
            session=self.session_ctx,
            expiry=self.expiry_ctx,
            confluence=self.confluence_ctx,
            readiness=self.readiness_ctx,
            timestamp="2026-07-09 10:30:00"
        )

        # 3. Market Score Setup
        self.market_score = MarketScore(
            trend=TrendScore(80.0, 100.0, 80.0, 100.0, 100.0, 85.0),
            options=OptionScore(100.0, 100.0, 100.0, 100.0, 85.0, 100.0, 100.0, 95.0),
            volatility=VolatilityScore(100.0, 90.0, 85.0, 100.0, 100.0, 95.0),
            liquidity=LiquidityScore(100.0, 85.0, 100.0, 100.0, 95.0),
            session=SessionScore(100.0, 100.0, 100.0),
            expiry=ExpiryScore(100.0, 100.0, 100.0, 80.0),
            confluence=ConfluenceScore(100.0, 100.0, 100.0, 100.0, 100.0, 90.0),
            overall_score=88.0,
            letter_grade="A",
            classification="Favorable",
            timestamp="2026-07-09 10:30:00"
        )

        # 4. Standard Risk Configuration
        self.config = RiskEngineConfig(
            max_capital_per_trade=40000.0,
            max_portfolio_exposure=150000.0,
            max_daily_exposure=200000.0,
            max_concurrent_trades=3,
            min_confidence_threshold=50.0,
            risk_scaling_enabled=True,
            total_portfolio_value=500000.0,
        )

    def create_mock_candidate(self, cand_id, symbol, strategy, strike=24300.0, ranking_score=80.0):
        return TradeCandidate(
            candidate_id=cand_id,
            strategy_name=strategy,
            tradingsymbol=symbol,
            strike=strike,
            instrument_type="CE" if "CE" in symbol else "PE",
            expiry="2026-10-29",
            distance_from_atm=0.0 if strike == 24300.0 else abs(strike - 24300.0),
            atm_distance_class="ATM" if strike == 24300.0 else "OTHER",
            oi=50000,
            volume=10000,
            spread_pct=0.15,
            iv=16.5,
            tradability_score=85.0,
            suitability_score=90.0,
            ranking_score=ranking_score,
            rank=1,
            reasons=[],
            warnings=[],
        )

    def test_option_premium_and_lot_size(self):
        # Retrieve premium from top strikes
        candidate_1 = self.create_mock_candidate("MOMENTUM_NIFTY26OCT24300CE", "NIFTY26OCT24300CE", "MOMENTUM")
        premium_1 = get_option_premium(candidate_1, self.option_context)
        self.assertEqual(premium_1, 120.0)

        # Verify lot sizes
        lot_nifty = get_option_lot_size(candidate_1, self.option_context)
        self.assertEqual(lot_nifty, 50)

        candidate_bank = self.create_mock_candidate("BREAKOUT_BANKNIFTY26OCT52000CE", "BANKNIFTY26OCT52000CE", "BREAKOUT")
        lot_bank = get_option_lot_size(candidate_bank, self.option_context)
        self.assertEqual(lot_bank, 15)

        # Fallback premium estimation test
        fallback_candidate = self.create_mock_candidate("MOMENTUM_FINNIFTY26OCT21000CE", "FINNIFTY26OCT21000CE", "MOMENTUM", strike=21000.0)
        fallback_premium = get_option_premium(fallback_candidate, self.option_context)
        self.assertTrue(fallback_premium > 0)

    def test_capital_allocation(self):
        candidate = self.create_mock_candidate("MOMENTUM_NIFTY26OCT24300CE", "NIFTY26OCT24300CE", "MOMENTUM")
        
        # Scaling enabled, 80% confidence
        alloc_scaled = calculate_allocation(candidate, 80.0, self.option_context, self.config)
        # Scaled max capital = 40000 * 0.8 = 32000
        # Cost per lot = 120 * 50 = 6000
        # Lots = 32000 // 6000 = 5 lots
        # Capital = 5 * 6000 = 30000
        self.assertEqual(alloc_scaled.allocated_lots, 5)
        self.assertEqual(alloc_scaled.allocated_capital, 30000.0)
        self.assertEqual(alloc_scaled.risk_amount, 30000.0)
        self.assertEqual(alloc_scaled.utilization_pct, 6.0)

        # Scaling disabled
        no_scaling_config = RiskEngineConfig(risk_scaling_enabled=False)
        alloc_fixed = calculate_allocation(candidate, 80.0, self.option_context, no_scaling_config)
        # Max capital = 40000
        # Lots = 40000 // 6000 = 6 lots
        # Capital = 6 * 6000 = 36000
        self.assertEqual(alloc_fixed.allocated_lots, 6)
        self.assertEqual(alloc_fixed.allocated_capital, 36000.0)

    def test_constraint_handling(self):
        candidate = self.create_mock_candidate("MOMENTUM_NIFTY26OCT24300CE", "NIFTY26OCT24300CE", "MOMENTUM")
        
        # Confidence below minimum threshold
        constraints, approved = evaluate_candidate_constraints(
            candidate=candidate,
            confidence_score=40.0,
            allocated_capital=30000.0,
            config=self.config,
        )
        self.assertFalse(approved)
        self.assertTrue(any(c.constraint_type == "MIN_CONFIDENCE_THRESHOLD" and c.is_violated for c in constraints))

        # Approved candidate
        constraints, approved = evaluate_candidate_constraints(
            candidate=candidate,
            confidence_score=75.0,
            allocated_capital=30000.0,
            config=self.config,
        )
        self.assertTrue(approved)
        self.assertFalse(any(c.is_violated for c in constraints if c.constraint_type == "MIN_CONFIDENCE_THRESHOLD"))

    def test_portfolio_limits(self):
        # Create 5 approved candidates, max concurrent trades = 3
        candidates = []
        for i in range(5):
            cand = self.create_mock_candidate(
                f"STRAT_CAND_{i}",
                "NIFTY26OCT24300CE",
                "STRAT",
                ranking_score=90.0 - i,
            )
            # Allocate capital
            alloc = calculate_allocation(cand, 90.0 - i, self.option_context, self.config)
            # Initial CandidateRisk
            constraints, approved = evaluate_candidate_constraints(cand, 90.0 - i, alloc.allocated_capital, self.config)
            risk = CandidateRisk(
                candidate_id=cand.candidate_id,
                tradingsymbol=cand.tradingsymbol,
                strategy_name=cand.strategy_name,
                risk_grade="LOW_RISK",
                capital_allocation=alloc,
                warnings=[],
                constraints=constraints,
                is_approved=approved,
            )
            candidates.append(risk)

        # Verify concurrent limits prioritize higher ranked scores
        scores = [90.0 - i for i in range(5)]
        adjusted_risks = apply_portfolio_level_limits(candidates, scores, self.config)

        approved_count = sum(1 for r in adjusted_risks if r.is_approved)
        self.assertEqual(approved_count, 3)

        # Check that top 3 were approved and last 2 rejected due to max concurrent
        self.assertTrue(adjusted_risks[0].is_approved)
        self.assertTrue(adjusted_risks[1].is_approved)
        self.assertTrue(adjusted_risks[2].is_approved)
        self.assertFalse(adjusted_risks[3].is_approved)
        self.assertFalse(adjusted_risks[4].is_approved)

    def test_portfolio_exposure_aggregation_and_warnings(self):
        # Set up a list of candidate risks to test sector exposure warnings
        cand1 = self.create_mock_candidate("MOM_NIFTY", "NIFTY26OCT24300CE", "MOMENTUM")
        alloc1 = calculate_allocation(cand1, 85.0, self.option_context, self.config)
        risk1 = CandidateRisk(
            candidate_id=cand1.candidate_id,
            tradingsymbol=cand1.tradingsymbol,
            strategy_name=cand1.strategy_name,
            risk_grade="LOW_RISK",
            capital_allocation=alloc1,
            warnings=[],
            constraints=[],
            is_approved=True,
        )

        exposure = calculate_portfolio_exposures([risk1], self.config)
        self.assertEqual(exposure.total_capital_allocated, 30000.0)
        self.assertEqual(exposure.option_concentration_pct, 100.0)
        self.assertEqual(exposure.capital_concentration_pct, 100.0)

        # Verify warnings
        warnings = generate_portfolio_warnings(exposure, self.config)
        # High single trade concentration warning (>50%) should trigger
        self.assertTrue(any(w.warning_type == "CAPITAL_CONCENTRATION" for w in warnings))

    def test_risk_builder_and_pipeline(self):
        cand1 = self.create_mock_candidate("MOMENTUM_NIFTY26OCT24300CE", "NIFTY26OCT24300CE", "MOMENTUM")
        cand2 = self.create_mock_candidate("MOMENTUM_NIFTY26OCT24350CE", "NIFTY26OCT24350CE", "MOMENTUM", strike=24350.0)
        
        trade_plan = TradePlan(
            trade_plan_id="PLAN_MOCK_123",
            accepted_candidates=[cand1, cand2],
            rejected_candidates=[],
        )

        confidence_report = ConfidenceReport(
            report_id="CONF_MOCK_123",
            trade_plan_id="PLAN_MOCK_123",
            candidate_confidences=[
                CandidateConfidence(
                    candidate_id="MOMENTUM_NIFTY26OCT24300CE",
                    tradingsymbol="NIFTY26OCT24300CE",
                    strategy_name="MOMENTUM",
                    confidence_score=85.0,
                    raw_score=85.0,
                ),
                CandidateConfidence(
                    candidate_id="MOMENTUM_NIFTY26OCT24350CE",
                    tradingsymbol="NIFTY26OCT24350CE",
                    strategy_name="MOMENTUM",
                    confidence_score=70.0,
                    raw_score=70.0,
                )
            ]
        )

        # Test RiskBuilder
        report = RiskBuilder.build_risk_report(
            trade_plan=trade_plan,
            confidence_report=confidence_report,
            trade_context=self.trade_context,
            market_score=self.market_score,
            config=self.config,
        )

        self.assertEqual(report.confidence_report_id, "CONF_MOCK_123")
        self.assertTrue(len(report.candidate_risks) == 2)
        self.assertTrue(report.exposure_summary.total_capital_allocated > 0)
        self.assertTrue(len(report.summary.conclusions) > 0)

        # Test RiskPipeline
        pipeline = RiskPipeline()
        pipeline_report = pipeline.run(
            confidence_report=confidence_report,
            trade_plan=trade_plan,
            trade_context=self.trade_context,
            market_score=self.market_score,
            config=self.config,
        )
        self.assertEqual(pipeline_report.confidence_report_id, "CONF_MOCK_123")
