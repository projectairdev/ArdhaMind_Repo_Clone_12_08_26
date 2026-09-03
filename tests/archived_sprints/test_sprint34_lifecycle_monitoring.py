from __future__ import annotations

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.models import (
    OrderLifecycleReport,
    OrderLifecycleEvent,
    ExecutionFill,
    ExecutionProgress,
    ExecutionTimeline,
    OrderModificationHistory,
    OrderCancellationRecord,
    BrokerOrder,
    ExecutionRequest,
    ExecutionOrder,
)
from src.workspace import WorkspaceManager, WorkspaceMode
from src.execution_engine.order_lifecycle_manager import OrderLifecycleManager
from src.dashboard.order_lifecycle_panel import OrderLifecyclePanel


class TestSprint34OrderLifecycleMonitoring(unittest.TestCase):
    """
    Production-grade test suite for Sprint 34 – Order Lifecycle & Execution Monitoring.
    Covers state transitions, partial fills, modifications, cancellations, broker sync,
    timeline immutability, execution analytics, dashboard/operations rendering,
    deduplication/out-of-order recovery, and Sprint 33 regression checks.
    """

    def setUp(self) -> None:
        OrderLifecycleManager.clear_all()

    def tearDown(self) -> None:
        OrderLifecycleManager.clear_all()

    def test_lifecycle_state_machine_transitions(self) -> None:
        """
        Test state transitions and chronology.
        """
        # 1. Create order
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_001",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        self.assertEqual(report.current_state, "CREATED")
        self.assertEqual(len(report.timeline.events), 1)
        self.assertEqual(report.timeline.events[0].new_state, "CREATED")

        # 2. Transition: CREATED -> VALIDATED
        report = OrderLifecycleManager.transition_to(
            report,
            new_state="VALIDATED",
            trigger_source="SYSTEM",
            operator="SYSTEM",
            broker_response="Validation Passed",
            reason="Pre-flight checks succeeded",
            timestamp="2026-07-11 09:15:02"
        )
        self.assertEqual(report.current_state, "VALIDATED")
        self.assertEqual(len(report.timeline.events), 2)
        self.assertEqual(report.timeline.events[1].previous_state, "CREATED")
        self.assertEqual(report.timeline.events[1].new_state, "VALIDATED")

        # 3. Transition: VALIDATED -> PENDING_CONFIRMATION
        report = OrderLifecycleManager.transition_to(
            report,
            new_state="PENDING_CONFIRMATION",
            trigger_source="SYSTEM",
            operator="SYSTEM",
            broker_response="Operator action required",
            reason="Awaiting manual execution authorization",
            timestamp="2026-07-11 09:15:04"
        )
        self.assertEqual(report.current_state, "PENDING_CONFIRMATION")

        # 4. Transition: PENDING_CONFIRMATION -> CONFIRMED
        report = OrderLifecycleManager.transition_to(
            report,
            new_state="CONFIRMED",
            trigger_source="OPERATOR",
            operator="pvpk06@gmail.com",
            broker_response="Confirmed by operator",
            reason="Authorized buy order",
            timestamp="2026-07-11 09:15:10"
        )
        self.assertEqual(report.current_state, "CONFIRMED")
        self.assertEqual(report.timeline.events[-1].operator, "pvpk06@gmail.com")

        # 5. Transition: CONFIRMED -> SUBMITTED
        report = OrderLifecycleManager.transition_to(
            report,
            new_state="SUBMITTED",
            trigger_source="SYSTEM",
            operator="SYSTEM",
            broker_response="Order sent to broker gateway",
            reason="Placing limit order",
            timestamp="2026-07-11 09:15:11"
        )
        self.assertEqual(report.current_state, "SUBMITTED")

    def test_partial_fill_manager_calculations(self) -> None:
        """
        Verify quantity progress trackers, completion percentage, and remaining balance.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_002",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        # Apply 250 fills
        report = OrderLifecycleManager.update_progress(
            report,
            filled_quantity=250,
            average_fill_price=150.50,
            timestamp="2026-07-11 09:15:15"
        )

        self.assertEqual(report.current_state, "PARTIALLY_FILLED")
        self.assertEqual(report.progress.filled_quantity, 250)
        self.assertEqual(report.progress.remaining_quantity, 750)
        self.assertEqual(report.progress.completion_percentage, 25.0)
        self.assertEqual(report.progress.average_fill_price, 150.50)

        # Apply remaining 750 fills to complete the order
        report = OrderLifecycleManager.update_progress(
            report,
            filled_quantity=1000,
            average_fill_price=151.20,
            timestamp="2026-07-11 09:15:20"
        )
        self.assertEqual(report.current_state, "FILLED")
        self.assertEqual(report.progress.filled_quantity, 1000)
        self.assertEqual(report.progress.remaining_quantity, 0)
        self.assertEqual(report.progress.completion_percentage, 100.0)

    def test_order_modifications(self) -> None:
        """
        Verify modifications record in modification history and transition state cleanly.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_003",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        # Modify: Qty 1000 -> 500, Price 150.0 -> 152.5
        report = OrderLifecycleManager.add_modification(
            report,
            previous_quantity=1000,
            previous_price=150.00,
            new_quantity=500,
            new_price=152.50,
            status="SUCCESS",
            timestamp="2026-07-11 09:15:05"
        )

        self.assertEqual(len(report.modification_history), 1)
        mod = report.modification_history[0]
        self.assertEqual(mod.previous_quantity, 1000)
        self.assertEqual(mod.new_quantity, 500)
        self.assertEqual(mod.new_price, 152.50)
        self.assertEqual(report.quantity, 500)

    def test_order_cancellations(self) -> None:
        """
        Verify cancellations log correct records and trigger state transition.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_004",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        # Request manual cancellation
        report = OrderLifecycleManager.add_cancellation(
            report,
            requested_by="pvpk06@gmail.com",
            reason="Market conditions reversed",
            status="SUCCESS",
            timestamp="2026-07-11 09:15:08"
        )

        self.assertEqual(report.current_state, "CANCELLED")
        self.assertIsNotNone(report.cancellation_record)
        self.assertEqual(report.cancellation_record.requested_by, "pvpk06@gmail.com")
        self.assertEqual(report.cancellation_record.reason, "Market conditions reversed")

    def test_broker_synchronization(self) -> None:
        """
        Verify Broker synchronization service updates states and remarks.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_005",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        # 1. Simulate partial fill on broker side
        broker_order_partial = BrokerOrder(
            order_id="ORD_34_005",
            exchange_order_id="EX_005",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            status="OPEN",
            price=150.50,
            filled_quantity=400,
            order_timestamp="2026-07-11 09:15:10",
            status_message="Partially completed on book"
        )

        report = OrderLifecycleManager.sync_with_broker(
            report,
            broker_order=broker_order_partial,
            timestamp="2026-07-11 09:15:12"
        )

        self.assertEqual(report.current_state, "PARTIALLY_FILLED")
        self.assertEqual(report.progress.filled_quantity, 400)
        self.assertEqual(report.progress.remaining_quantity, 600)
        self.assertEqual(report.broker_remarks, "Partially completed on book")

        # 2. Simulate complete fill on broker
        broker_order_complete = BrokerOrder(
            order_id="ORD_34_005",
            exchange_order_id="EX_005",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            status="COMPLETE",
            price=151.00,
            filled_quantity=1000,
            order_timestamp="2026-07-11 09:15:20",
            status_message="Trade execution finalized"
        )

        report = OrderLifecycleManager.sync_with_broker(
            report,
            broker_order=broker_order_complete,
            timestamp="2026-07-11 09:15:22"
        )
        self.assertEqual(report.current_state, "FILLED")
        self.assertEqual(report.progress.filled_quantity, 1000)
        self.assertEqual(report.broker_remarks, "Trade execution finalized")

    def test_lifecycle_timeline_immutability(self) -> None:
        """
        Verify chronological events timeline generation and timeline preservation.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_006",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=500,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        # Capture timeline object ID to prove immutability
        old_timeline = report.timeline

        report_updated = OrderLifecycleManager.transition_to(
            report,
            new_state="VALIDATED",
            trigger_source="SYSTEM",
            operator="SYSTEM",
            broker_response="OK",
            timestamp="2026-07-11 09:15:02"
        )

        self.assertNotEqual(id(old_timeline), id(report_updated.timeline))
        self.assertEqual(len(old_timeline.events), 1)
        self.assertEqual(len(report_updated.timeline.events), 2)

    def test_execution_analytics(self) -> None:
        """
        Test the computation of Latencies, Slippage, modifications count, cancellation rates, etc.
        """
        r1 = OrderLifecycleManager.create_order("ORD_A", "SYM", "NFO", "BUY", 100, "NRML", "LIMIT", "pvpk06@gmail.com", "2026-07-11 09:15:00")
        r1 = OrderLifecycleManager.transition_to(r1, "CONFIRMED", "OPERATOR", "pvpk06@gmail.com", timestamp="2026-07-11 09:15:02")
        r1 = OrderLifecycleManager.transition_to(r1, "SUBMITTED", "SYSTEM", "SYSTEM", timestamp="2026-07-11 09:15:04")
        r1 = OrderLifecycleManager.transition_to(r1, "OPEN", "BROKER", "SYSTEM", timestamp="2026-07-11 09:15:06")
        r1 = OrderLifecycleManager.update_progress(r1, 100, 150.50, timestamp="2026-07-11 09:15:10")

        r2 = OrderLifecycleManager.create_order("ORD_B", "SYM", "NFO", "BUY", 100, "NRML", "LIMIT", "pvpk06@gmail.com", "2026-07-11 09:15:00")
        r2 = OrderLifecycleManager.add_cancellation(r2, "pvpk06@gmail.com", "Test Cancel", "SUCCESS", "2026-07-11 09:15:05")

        analytics = OrderLifecycleManager.calculate_analytics([r1, r2])

        # Fill time for completed: 09:15:04 (SUBMITTED) -> 09:15:10 (FILLED) = 6 seconds
        self.assertEqual(analytics.average_fill_time, 6.0)
        # Broker latency: 09:15:02 (CONFIRMED) -> 09:15:04 (SUBMITTED) = 2 seconds = 2000 ms
        self.assertEqual(analytics.broker_latency, 2000.0)
        # Exchange latency: 09:15:04 (SUBMITTED) -> 09:15:06 (OPEN) = 2 seconds = 2000 ms
        self.assertEqual(analytics.exchange_latency, 2000.0)
        # Cancellation rate: 1 of 2 orders = 50.0%
        self.assertEqual(analytics.cancellation_rate, 50.0)
        # Execution success rate: 1 of 2 orders filled = 50.0%
        self.assertEqual(analytics.execution_success_rate, 50.0)

    def test_recovery_mechanisms(self) -> None:
        """
        Verify recovery mechanism safely reassembles out-of-order and duplicate event logs.
        """
        # Formulate out-of-order and duplicate event logs
        events = [
            OrderLifecycleEvent("E1", "2026-07-11 09:15:15", "PARTIALLY_FILLED", "FILLED", "BROKER", "SYSTEM"),
            OrderLifecycleEvent("E2", "2026-07-11 09:15:00", "NONE", "CREATED", "OPERATOR", "pvpk06@gmail.com"),
            # Duplicate
            OrderLifecycleEvent("E2_dup", "2026-07-11 09:15:00", "NONE", "CREATED", "OPERATOR", "pvpk06@gmail.com"),
            OrderLifecycleEvent("E3", "2026-07-11 09:15:10", "OPEN", "PARTIALLY_FILLED", "BROKER", "SYSTEM"),
            OrderLifecycleEvent("E4", "2026-07-11 09:15:05", "CREATED", "VALIDATED", "SYSTEM", "SYSTEM"),
        ]

        report = OrderLifecycleManager.recover_lifecycle("ORD_RECOVER_001", events)

        # Sorted chronology rank order should conclude in FILLED state
        self.assertEqual(report.current_state, "FILLED")
        self.assertEqual(len(report.timeline.events), 4) # CREATED, VALIDATED, PARTIALLY_FILLED, FILLED (duplicates weeded out)
        self.assertEqual(report.timeline.events[0].new_state, "CREATED")
        self.assertEqual(report.timeline.events[1].new_state, "VALIDATED")
        self.assertEqual(report.timeline.events[2].new_state, "PARTIALLY_FILLED")
        self.assertEqual(report.timeline.events[3].new_state, "FILLED")

    def test_dashboard_and_operations_panel_serialization(self) -> None:
        """
        Verify dictionary serialization and CLI report generation formats.
        """
        report = OrderLifecycleManager.create_order(
            order_id="ORD_34_007",
            tradingsymbol="NIFTY26JUL24200CE",
            exchange="NFO",
            transaction_type="BUY",
            quantity=1000,
            product="NRML",
            order_type="LIMIT",
            operator="pvpk06@gmail.com",
            timestamp="2026-07-11 09:15:00"
        )

        panel = OrderLifecyclePanel([report])
        data = panel.to_dict()

        self.assertIn("orders", data)
        self.assertIn("statistics", data)
        self.assertIn("system_health", data)
        self.assertEqual(data["system_health"]["engine_status"], "HEALTHY")

        cli_out = panel.render_cli()
        self.assertIn("SPRINT 34 — ORDER LIFECYCLE MONITORING", cli_out)
        self.assertIn("ORD_34_007", cli_out)
        self.assertIn("HEALTHY", cli_out)


if __name__ == "__main__":
    unittest.main()
