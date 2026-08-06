from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.models import (
    ExecutionStateReport,
    BrokerOrder,
    BrokerPosition,
    BrokerFunds,
    BrokerAccount,
    ExecutionRequest,
    ExecutionTimeline,
    ExecutionAudit,
)
from src.execution_engine.order_tracker import OrderTracker
from src.execution_engine.position_sync import PositionSynchronizer
from src.execution_engine.portfolio_sync import PortfolioSynchronizer
from src.execution_engine.timeline import TimelineGenerator

logger = logging.getLogger("ExecutionStateReportBuilder")


class ExecutionStateReportBuilder:
    """
    Orchestrates the individual tracking, synchronization, and calculation engines
    to compile a complete, immutable ExecutionStateReport.
    """

    @staticmethod
    def build(
        broker_orders: List[BrokerOrder],
        broker_positions: List[BrokerPosition],
        broker_funds: Optional[BrokerFunds] = None,
        broker_account: Optional[BrokerAccount] = None,
        execution_requests: Optional[List[ExecutionRequest]] = None,
        past_timelines: Optional[List[ExecutionTimeline]] = None,
        past_audits: Optional[List[ExecutionAudit]] = None,
    ) -> ExecutionStateReport:
        """
        Builds the complete state report statelessly.
        """
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        report_id = f"EXEC_STATE_{int(datetime.utcnow().timestamp())}"

        # 1. Track Order States and calculate order statistics
        orders_state = OrderTracker.track_orders(broker_orders, execution_requests)
        stats = OrderTracker.calculate_statistics(orders_state)

        # 2. Synchronize Positions
        position_context = PositionSynchronizer.synchronize(broker_positions)

        # 3. Synchronize Portfolio
        portfolio_context = PortfolioSynchronizer.synchronize(position_context, broker_funds)

        # 4. Generate/Update Order Timelines
        timelines = TimelineGenerator.generate_all_timelines(orders_state, past_timelines)

        # 5. Compile Audits list (preserves past history)
        audits = list(past_audits) if past_audits else []

        return ExecutionStateReport(
            report_id=report_id,
            timestamp=timestamp_str,
            orders=orders_state,
            positions=position_context,
            portfolio=portfolio_context,
            timelines=timelines,
            audits=audits,
            statistics=stats
        )
