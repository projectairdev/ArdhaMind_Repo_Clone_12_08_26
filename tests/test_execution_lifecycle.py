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
from src.execution_engine.order_tracker import OrderTracker
from src.execution_engine.position_sync import PositionSynchronizer
from src.execution_engine.portfolio_sync import PortfolioSynchronizer
from src.execution_engine.mtm import MTMCalculator
from src.execution_engine.audit import ExecutionAuditLog
from src.execution_engine.timeline import TimelineGenerator
from src.execution_engine.builder import ExecutionStateReportBuilder
from src.dashboard.execution_panel import ExecutionPanel
from src.dashboard.dashboard_builder import TradingWorkstationDashboard


class TestExecutionLifecycle(unittest.TestCase):
    """
    Comprehensive mocked unit tests for Sprint 23 (Execution & Position Lifecycle Manager).
    Verifies all stateless engines, lifecycle transitions, synchronization, MTM logic, 
    timeline generation, audit integrity, and dashboard rendering.
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

    def test_timeline_generator(self) -> None:
        """
        Verify timeline events generation and persistence.
        """
        order = OrderState(
            order_id="ORD_101", tradingsymbol="RELIANCE", exchange="NSE",
            transaction_type="BUY", quantity=10, filled_quantity=0,
            pending_quantity=10, status="CREATED", average_price=0.0,
            trigger_price=0.0, product="MIS", order_type="LIMIT",
            status_message="Local created", timestamp="10:00:00"
        )

        timeline = TimelineGenerator.generate_timeline(order)
        self.assertEqual(len(timeline.events), 1)
        self.assertEqual(timeline.events[0]["status"], "CREATED")

        # Update status to PENDING
        order_pending = OrderState(
            order_id="ORD_101", tradingsymbol="RELIANCE", exchange="NSE",
            transaction_type="BUY", quantity=10, filled_quantity=0,
            pending_quantity=10, status="PENDING", average_price=0.0,
            trigger_price=0.0, product="MIS", order_type="LIMIT",
            status_message="Active in queue", timestamp="10:01:00"
        )
        updated_timeline = TimelineGenerator.generate_timeline(order_pending, timeline)
        self.assertEqual(len(updated_timeline.events), 3)  # CREATED, SUBMITTED, PENDING
        self.assertEqual(updated_timeline.events[2]["status"], "PENDING")

    def test_audit_logging(self) -> None:
        """
        Verify ExecutionAuditLog correctly records and structures audit details.
        """
        audit = ExecutionAuditLog.create_audit_record(
            action="TEST_ACTION",
            request_payload={"data": 123},
            response_payload={"result": "OK"},
            status="SUCCESS"
        )
        self.assertTrue(audit.audit_id.startswith("AUD_"))
        self.assertEqual(audit.action, "TEST_ACTION")
        self.assertEqual(audit.status, "SUCCESS")

        # Audit Execution Request/Report
        req = ExecutionRequest(
            request_id="REQ_001",
            decision_report_id="DEC_REP_123",
            timestamp="10:00:00",
            status="PENDING",
            orders=[
                ExecutionOrder(
                    candidate_id="CAND_1", tradingsymbol="SYM1", exchange="NSE",
                    transaction_type="BUY", quantity=100, price=50.0, product="MIS",
                    order_type="LIMIT", trigger_price=0.0
                )
            ]
        )
        rep = ExecutionReport(
            report_id="REP_001", timestamp="10:00:05", status="COMPLETED",
            broker_order_id="ORD_001", exchange_order_id="EX_001",
            accepted_orders=[req.orders[0]], rejected_orders=[], failure_reason="",
            request_id="REQ_001"
        )

        audit_record = ExecutionAuditLog.audit_execution_request(req, rep)
        self.assertEqual(audit_record.action, "ORDER_EXECUTION")
        self.assertEqual(audit_record.status, "SUCCESS")
        self.assertEqual(audit_record.request_payload["request_id"], "REQ_001")
        self.assertEqual(audit_record.response_payload["broker_order_id"], "ORD_001")

    def test_state_report_builder(self) -> None:
        """
        Verify end-to-end stateless report construction via ExecutionStateReportBuilder.
        """
        broker_orders = [
            BrokerOrder(
                order_id="ORD_1", exchange_order_id="EX1", tradingsymbol="SYM1",
                exchange="NSE", transaction_type="BUY", quantity=10, product="MIS",
                order_type="LIMIT", status="COMPLETE", price=100.0, filled_quantity=10,
                order_timestamp="10:00:00", status_message=""
            )
        ]
        broker_positions = [
            BrokerPosition(
                tradingsymbol="SYM1", exchange="NSE", product="MIS", quantity=10,
                average_price=100.0, last_price=105.0, pnl=50.0, today_mtm=50.0
            )
        ]
        funds = BrokerFunds(available_cash=10000.0, margins=8000.0, utilized_margin=2000.0, available_margin=8000.0)

        report = ExecutionStateReportBuilder.build(
            broker_orders=broker_orders,
            broker_positions=broker_positions,
            broker_funds=funds
        )

        self.assertEqual(len(report.orders), 1)
        self.assertEqual(report.statistics.total_orders, 1)
        self.assertEqual(report.positions.total_positions_count, 1)
        self.assertEqual(report.portfolio.portfolio_mtm, 50.0)
        self.assertEqual(len(report.timelines), 1)

    def test_dashboard_rendering(self) -> None:
        """
        Verify ExecutionPanel dict serialization and text/ASCII rendering functions.
        """
        live_pos = LivePosition(
            tradingsymbol="SYM1", exchange="NSE", product="MIS", quantity=10,
            average_price=100.0, last_price=105.0, pnl=50.0, realized_pnl=0.0,
            unrealized_pnl=50.0, today_mtm=50.0
        )
        pos_ctx = PositionContext(positions=[live_pos], total_positions_count=1, open_positions_count=1, today_mtm=50.0)
        port_ctx = PortfolioContext(active_positions=[live_pos], closed_positions=[], capital_utilized=2000.0, available_capital=8000.0, portfolio_mtm=50.0)
        
        order = OrderState(
            order_id="ORD_1", tradingsymbol="SYM1", exchange="NSE",
            transaction_type="BUY", quantity=10, filled_quantity=10,
            pending_quantity=0, status="FILLED", average_price=100.0,
            trigger_price=0.0, product="MIS", order_type="LIMIT",
            status_message="", timestamp="10:00:00"
        )
        
        timeline = ExecutionTimeline(order_id="ORD_1", tradingsymbol="SYM1", events=[{"timestamp": "10:00:00", "status": "FILLED", "details": "Filled"}])
        
        report = ExecutionStateReport(
            report_id="REP_TEST",
            timestamp="10:00:00",
            orders=[order],
            positions=pos_ctx,
            portfolio=port_ctx,
            timelines=[timeline],
            audits=[],
            statistics=OrderTracker.calculate_statistics([order])
        )

        panel = ExecutionPanel(report)
        dct = panel.to_dict()
        self.assertEqual(dct["statistics"]["total_orders"], 1)
        self.assertEqual(dct["portfolio"]["portfolio_mtm"], 50.0)
        self.assertEqual(len(dct["positions"]), 1)

        cli_out = panel.render_cli()
        self.assertIn("EXECUTION & POSITION LIFECYCLE PANEL", cli_out)
        self.assertIn("SYM1", cli_out)
        self.assertIn("Portfolio MTM : INR +50.00", cli_out)

        # Render integrated workspace dashboard
        dash = TradingWorkstationDashboard(execution_state=report)
        dash_dict = dash.to_dict()
        self.assertIn("execution", dash_dict)
        self.assertEqual(dash_dict["execution"]["portfolio"]["portfolio_mtm"], 50.0)

        dash_cli = dash.render_cli()
        self.assertIn("EXECUTION & POSITION LIFECYCLE PANEL", dash_cli)
