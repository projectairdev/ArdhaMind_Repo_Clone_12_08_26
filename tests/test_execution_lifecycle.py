from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock

from src.models import (
    BrokerOrder,
    BrokerPosition,
    BrokerFunds,
    BrokerAccount,
    ExecutionRequest,
    ExecutionOrder,
    ExecutionReport,
    OrderState,
    LivePosition,
    PositionContext,
    PortfolioContext,
    ExecutionTimeline,
    ExecutionAudit,
    ExecutionStateReport,
)
from src.broker.services.portfolio.order_tracker import OrderTracker
from src.broker.services.portfolio.position_sync import PositionSynchronizer
from src.broker.services.portfolio.portfolio_sync import PortfolioSynchronizer
from src.broker.services.portfolio.mtm import MTMCalculator


class TestExecutionLifecycle(unittest.TestCase):
    """
    Comprehensive mocked unit tests for Portfolio Telemetry & Order Tracking.
    Verifies stateless normalization, position synchronization, portfolio aggregation, and MTM logic.
    """

    def test_order_tracker_lifecycle_mapping(self) -> None:
        """
        Verify OrderTracker status mapping across all states.
        """
        # Test exact helper mapping
        self.assertEqual(OrderTracker.map_broker_status("COMPLETE", 100, 100), "FILLED")
        self.assertEqual(OrderTracker.map_broker_status("REJECTED", 0, 100), "REJECTED")
        self.assertEqual(OrderTracker.map_broker_status("CANCELLED", 0, 100), "CANCELLED")
        self.assertEqual(OrderTracker.map_broker_status("OPEN", 0, 100), "PENDING")
        self.assertEqual(OrderTracker.map_broker_status("OPEN", 50, 100), "PARTIALLY_FILLED")
        self.assertEqual(OrderTracker.map_broker_status("TRIGGER PENDING", 0, 100), "PENDING")
        self.assertEqual(OrderTracker.map_broker_status("EXPIRED", 0, 100), "EXPIRED")
        self.assertEqual(OrderTracker.map_broker_status("SENT", 0, 100), "SUBMITTED")
        self.assertEqual(OrderTracker.map_broker_status("ACCEPTED", 0, 100), "ACCEPTED")

        # Test tracking from list of BrokerOrders
        broker_orders = [
            BrokerOrder(
                order_id="ORD_001",
                exchange_order_id="EXCH_001",
                tradingsymbol="NIFTY26NOV24200CE",
                exchange="NFO",
                transaction_type="BUY",
                quantity=100,
                product="MIS",
                order_type="LIMIT",
                status="COMPLETE",
                price=150.5,
                filled_quantity=100,
                order_timestamp="2026-11-09 10:00:00",
                status_message=""
            ),
            BrokerOrder(
                order_id="ORD_002",
                exchange_order_id="",
                tradingsymbol="NIFTY26NOV24150PE",
                exchange="NFO",
                transaction_type="SELL",
                quantity=100,
                product="MIS",
                order_type="LIMIT",
                status="OPEN",
                price=80.0,
                filled_quantity=40,
                order_timestamp="2026-11-09 10:05:00",
                status_message="Waiting in queue"
            )
        ]

        order_states = OrderTracker.track_orders(broker_orders)
        self.assertEqual(len(order_states), 2)
        
        o1 = order_states[0]
        self.assertEqual(o1.order_id, "ORD_001")
        self.assertEqual(o1.status, "FILLED")
        self.assertEqual(o1.pending_quantity, 0)
        self.assertEqual(o1.average_price, 150.5)

        o2 = order_states[1]
        self.assertEqual(o2.order_id, "ORD_002")
        self.assertEqual(o2.status, "PARTIALLY_FILLED")
        self.assertEqual(o2.pending_quantity, 60)
        self.assertEqual(o2.filled_quantity, 40)

        # Calculate Statistics
        stats = OrderTracker.calculate_statistics(order_states)
        self.assertEqual(stats.total_orders, 2)
        self.assertEqual(stats.filled_orders, 1)
        self.assertEqual(stats.fill_rate, 50.0)

    def test_position_synchronizer(self) -> None:
        """
        Verify PositionSynchronizer groups, calculates MTM, and splits PnL properly.
        """
        broker_positions = [
            # Open position
            BrokerPosition(
                tradingsymbol="NIFTY26NOV24200CE",
                exchange="NFO",
                product="MIS",
                quantity=50,
                average_price=100.0,
                last_price=120.0,
                pnl=1200.0,
                today_mtm=1000.0
            ),
            # Closed position
            BrokerPosition(
                tradingsymbol="NIFTY26NOV24150PE",
                exchange="NFO",
                product="MIS",
                quantity=0,
                average_price=80.0,
                last_price=90.0,
                pnl=-500.0,
                today_mtm=-500.0
            )
        ]

        ctx = PositionSynchronizer.synchronize(broker_positions)
        self.assertEqual(ctx.total_positions_count, 2)
        self.assertEqual(ctx.open_positions_count, 1)
        self.assertEqual(ctx.today_mtm, 500.0)

        p1 = ctx.positions[0]
        # unrealized = (120 - 100) * 50 = 1000
        # realized = 1200 - 1000 = 200
        self.assertEqual(p1.unrealized_pnl, 1000.0)
        self.assertEqual(p1.realized_pnl, 200.0)

        p2 = ctx.positions[1]
        self.assertEqual(p2.unrealized_pnl, 0.0)
        self.assertEqual(p2.realized_pnl, -500.0)

    def test_portfolio_synchronizer(self) -> None:
        """
        Verify portfolio segmentation into active vs closed and capital tracking.
        """
        positions = [
            LivePosition(
                tradingsymbol="SYM1", exchange="NFO", product="MIS", quantity=100,
                average_price=10.0, last_price=12.0, pnl=200.0, realized_pnl=0.0,
                unrealized_pnl=200.0, today_mtm=200.0
            ),
            LivePosition(
                tradingsymbol="SYM2", exchange="NFO", product="MIS", quantity=0,
                average_price=20.0, last_price=15.0, pnl=-500.0, realized_pnl=-500.0,
                unrealized_pnl=0.0, today_mtm=-500.0
            )
        ]
        pos_ctx = PositionContext(positions=positions, total_positions_count=2, open_positions_count=1, today_mtm=-300.0)
        
        funds = BrokerFunds(available_cash=10000.0, margins=8000.0, utilized_margin=2000.0, available_margin=6000.0)

        port_ctx = PortfolioSynchronizer.synchronize(pos_ctx, funds)
        self.assertEqual(len(port_ctx.active_positions), 1)
        self.assertEqual(len(port_ctx.closed_positions), 1)
        self.assertEqual(port_ctx.capital_utilized, 2000.0)
        self.assertEqual(port_ctx.available_capital, 6000.0)
        self.assertEqual(port_ctx.portfolio_mtm, 200.0)

    def test_mtm_calculator(self) -> None:
        """
        Verify MTM calculators and sensitivity projections.
        """
        positions = [
            LivePosition(
                tradingsymbol="SYM1", exchange="NFO", product="MIS", quantity=100,
                average_price=10.0, last_price=100.0, pnl=200.0, realized_pnl=0.0,
                unrealized_pnl=200.0, today_mtm=150.0
            ),
            LivePosition(
                tradingsymbol="SYM2", exchange="NFO", product="MIS", quantity=0,
                average_price=20.0, last_price=15.0, pnl=-500.0, realized_pnl=-500.0,
                unrealized_pnl=0.0, today_mtm=-500.0
            )
        ]

        total_mtm = MTMCalculator.calculate_total_mtm(positions)
        self.assertEqual(total_mtm, -350.0)

        # Projections
        # SYM1 has qty 100, last price 100. Shift is +2.0% -> price changes by +2.0. Delta = 100 * 100 * 0.02 = 200.0
        sensitivity = MTMCalculator.project_mtm_sensitivity(positions, {"SYM1": 2.0})
        self.assertEqual(sensitivity, 200.0)
